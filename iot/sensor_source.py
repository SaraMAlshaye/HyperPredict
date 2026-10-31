"""Connection layer between a USB-serial sensor device and the app.

- NoDeviceSource: the default. It always reports "no device configured" and never
  returns readings. The app works fully in this state.
- SerialSensorSource: opens a serial port (needs `pip install pyserial`), reads JSON
  lines in a background thread, and exposes the latest *real* reading plus a status.

Nothing here generates readings. If no valid data has arrived, there is no reading.
Status values are computed from what was actually received and when.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import threading
import time

from iot.sensor_protocol import ParseResult, SensorReading, parse_line

DEFAULT_BAUDRATE = 115200
STALE_AFTER_S = 5.0          # no valid reading for this long -> "stale"
CONNECT_TIMEOUT_S = 10.0     # port open but nothing valid yet -> "no data"


class SensorStatus(Enum):
    NOT_CONFIGURED = "No device configured"
    UNAVAILABLE = "Cannot connect"
    WAITING = "Connected, waiting for data"
    NO_DATA = "Connected, but no valid data received"
    LIVE = "Receiving readings"
    STALE = "Readings stopped"
    DEVICE_ERROR = "Device reported an error"
    DISCONNECTED = "Disconnected"

    @property
    def is_live(self) -> bool:
        return self is SensorStatus.LIVE


@dataclass(frozen=True)
class SensorSnapshot:
    status: SensorStatus
    detail: str
    reading: SensorReading | None         # latest valid reading, if any was ever received
    last_message_at: datetime | None      # any line, valid or not
    last_error: str | None
    port: str | None = None


class NoDeviceSource:
    """Used when no hardware is configured. Never produces readings."""

    port = None

    def snapshot(self) -> SensorSnapshot:
        return SensorSnapshot(SensorStatus.NOT_CONFIGURED,
                              "Hardware not connected. Enter a serial port to connect.",
                              None, None, None)

    def close(self) -> None:
        pass


def _default_serial_factory(port: str, baudrate: int):
    try:
        import serial  # pyserial, optional dependency
    except ImportError as exc:
        raise RuntimeError("pyserial is not installed (pip install pyserial)") from exc
    return serial.Serial(port, baudrate=baudrate, timeout=1)


class SerialSensorSource:
    """Reads the JSON-lines protocol from a serial port.

    `serial_factory(port, baudrate)` must return an object with readline() and
    close(); tests pass a fake. `clock` returns seconds (time.monotonic by default).
    """

    def __init__(self, port: str, baudrate: int = DEFAULT_BAUDRATE, serial_factory=None,
                 clock=time.monotonic, stale_after_s: float = STALE_AFTER_S,
                 connect_timeout_s: float = CONNECT_TIMEOUT_S):
        self.port = port
        self.baudrate = baudrate
        self._factory = serial_factory or _default_serial_factory
        self._clock = clock
        self._stale_after = stale_after_s
        self._connect_timeout = connect_timeout_s
        self._lock = threading.Lock()
        self._conn = None
        self._thread = None
        self._stop = threading.Event()
        self._opened_at = None
        self._open_error = None
        self._disconnected = None
        self._reading = None
        self._reading_clock = None
        self._last_message_at = None
        self._last_error = None
        self._device_status = None

    # -- connection -------------------------------------------------------------
    def open(self) -> bool:
        """Try to open the port. Returns False (with a reason) instead of raising."""
        try:
            conn = self._factory(self.port, self.baudrate)
        except Exception as exc:  # missing pyserial, wrong port, permission, unplugged
            with self._lock:
                self._open_error = str(exc) or exc.__class__.__name__
            return False
        with self._lock:
            self._conn, self._opened_at, self._open_error = conn, self._clock(), None
        return True

    def start(self) -> bool:
        """Open the port and start the background reader thread."""
        if not self.open():
            return False
        self._thread = threading.Thread(target=self._run, name="sensor-reader", daemon=True)
        self._thread.start()
        return True

    def _run(self) -> None:
        while not self._stop.is_set() and self.poll_once():
            pass

    def poll_once(self) -> bool:
        """Read and handle one line. Returns False once the connection is lost."""
        with self._lock:
            conn = self._conn
        if conn is None:
            return False
        try:
            line = conn.readline()  # returns b"" on timeout
        except Exception as exc:    # cable pulled, port closed, driver error
            self._mark_disconnected(f"read failed: {exc}")
            return False
        if line:
            self.handle_line(line)
        return True

    def handle_line(self, line) -> ParseResult:
        result = parse_line(line, datetime.now(timezone.utc))
        if result.ignored:
            return result
        with self._lock:
            self._last_message_at = datetime.now(timezone.utc)
            if result.error:
                self._last_error = result.error
            elif result.device_status:
                self._device_status = result.device_status
            elif result.reading:
                # Always keep the newest reading, even if its values are None, so the
                # app never keeps showing older numbers the device no longer stands by.
                self._last_error = None
                self._device_status = None
                self._reading, self._reading_clock = result.reading, self._clock()
        return result

    def _mark_disconnected(self, reason: str) -> None:
        with self._lock:
            self._disconnected = reason
            conn, self._conn = self._conn, None
        try:
            if conn is not None:
                conn.close()
        except Exception:
            pass

    def close(self) -> None:
        self._stop.set()
        self._mark_disconnected("closed by user")
        if self._thread is not None:
            self._thread.join(timeout=2)

    # -- status -----------------------------------------------------------------
    def snapshot(self) -> SensorSnapshot:
        with self._lock:
            now = self._clock()
            args = (self._reading, self._last_message_at, self._last_error, self.port)
            if self._open_error:
                return SensorSnapshot(SensorStatus.UNAVAILABLE, self._open_error, None, None,
                                      self._open_error, self.port)
            if self._disconnected:
                return SensorSnapshot(SensorStatus.DISCONNECTED, self._disconnected, *args)
            if self._conn is None:
                return SensorSnapshot(SensorStatus.NOT_CONFIGURED, "Port not opened.", *args)
            if self._device_status:
                return SensorSnapshot(SensorStatus.DEVICE_ERROR, self._device_status.message,
                                      *args)
            if self._reading is None:
                waited = now - self._opened_at
                if waited < self._connect_timeout:
                    return SensorSnapshot(SensorStatus.WAITING, "Port open.", *args)
                detail = self._last_error or "No messages received from the device."
                return SensorSnapshot(SensorStatus.NO_DATA, detail, *args)
            age = now - self._reading_clock
            if age > self._stale_after:
                return SensorSnapshot(SensorStatus.STALE,
                                      f"Last valid reading {age:.0f} s ago.", *args)
            detail = "Place a finger on the sensor." if not self._reading.finger_detected \
                else "; ".join(self._reading.warnings) or "OK"
            return SensorSnapshot(SensorStatus.LIVE, detail, *args)
