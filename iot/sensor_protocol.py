"""Message format between the microcontroller and the app, and a strict parser.

Transport: USB serial, 115200 baud, one JSON object per line (UTF-8, "\\n" ending).
The same JSON can later be sent over HTTP/Wi-Fi without changing this parser.

Reading message (sent about once per second by the firmware):
    {"v": 1, "type": "reading", "hr_bpm": 72, "hr_valid": 1,
     "spo2_pct": 97, "spo2_valid": 1, "finger": 1, "uptime_ms": 123456}

Status message (e.g. the sensor chip was not found on the I2C bus):
    {"v": 1, "type": "status", "msg": "sensor_not_found"}

The parser never invents values: anything missing, malformed, flagged invalid by the
device, or physiologically implausible becomes None plus a warning or an error.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import math

PROTOCOL_VERSION = 1
HR_RANGE = (30, 220)      # beats/min, same plausibility bounds as the training data
SPO2_RANGE = (70, 100)    # percent; below 70 the MAX30102 algorithm is not reliable
MAX_LINE_LENGTH = 512     # longer lines are treated as garbage


@dataclass(frozen=True)
class SensorReading:
    heart_rate_bpm: float | None      # None = no valid estimate in this message
    spo2_percent: float | None
    finger_detected: bool
    device_uptime_ms: int | None
    received_at: datetime             # time the app received it (device has no clock)
    warnings: tuple[str, ...] = ()

    @property
    def has_values(self) -> bool:
        return self.heart_rate_bpm is not None or self.spo2_percent is not None


@dataclass(frozen=True)
class DeviceStatus:
    message: str
    received_at: datetime


@dataclass(frozen=True)
class ParseResult:
    reading: SensorReading | None = None
    device_status: DeviceStatus | None = None
    error: str | None = None          # set when the line was rejected
    ignored: bool = False             # blank line / keep-alive
    warnings: tuple[str, ...] = field(default_factory=tuple)


def _number(value):
    """Return a finite float, or None for anything else (bools are not numbers here)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    value = float(value)
    return value if math.isfinite(value) else None


def _flag(value) -> bool | None:
    if value in (True, 1):
        return True
    if value in (False, 0):
        return False
    return None


def _checked(name, raw, valid_flag, bounds, warnings):
    if valid_flag is False:
        warnings.append(f"device marked {name} as not valid")
        return None
    value = _number(raw)
    if value is None:
        warnings.append(f"{name} missing or not a number")
        return None
    low, high = bounds
    if not low <= value <= high:
        warnings.append(f"{name} {value:g} outside plausible range {low}-{high}")
        return None
    return value


def parse_line(line, received_at: datetime | None = None) -> ParseResult:
    """Parse one line (bytes or str) from the device into a ParseResult."""
    received_at = received_at or datetime.now(timezone.utc)
    if isinstance(line, bytes):
        try:
            line = line.decode("utf-8")
        except UnicodeDecodeError:
            return ParseResult(error="malformed: not valid UTF-8 text")
    line = line.strip()
    if not line:
        return ParseResult(ignored=True)
    if len(line) > MAX_LINE_LENGTH:
        return ParseResult(error="malformed: line too long")
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return ParseResult(error=f"malformed: not JSON ({line[:40]!r})")
    if not isinstance(data, dict):
        return ParseResult(error="malformed: JSON is not an object")
    if data.get("v") != PROTOCOL_VERSION:
        return ParseResult(error=f"unsupported protocol version {data.get('v')!r}")

    kind = data.get("type")
    if kind == "status":
        msg = data.get("msg")
        if not isinstance(msg, str) or not msg:
            return ParseResult(error="malformed: status message without text")
        return ParseResult(device_status=DeviceStatus(msg[:100], received_at))
    if kind != "reading":
        return ParseResult(error=f"unknown message type {kind!r}")

    finger = _flag(data.get("finger"))
    if finger is None:
        return ParseResult(error="malformed: 'finger' must be 0 or 1")
    uptime = data.get("uptime_ms")
    uptime = int(uptime) if _number(uptime) is not None and uptime >= 0 else None

    warnings: list[str] = []
    if not finger:
        # No finger on the sensor: any numbers the device sent are meaningless.
        hr = spo2 = None
        warnings.append("no finger detected")
    else:
        hr = _checked("heart rate", data.get("hr_bpm"), _flag(data.get("hr_valid")),
                      HR_RANGE, warnings)
        spo2 = _checked("SpO2", data.get("spo2_pct"), _flag(data.get("spo2_valid")),
                        SPO2_RANGE, warnings)
    reading = SensorReading(hr, spo2, finger, uptime, received_at, tuple(warnings))
    return ParseResult(reading=reading, warnings=tuple(warnings))
