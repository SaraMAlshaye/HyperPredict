"""Connection-state tests using a fake serial port (no hardware needed)."""
import json

from iot.display import NO_VALUE, format_snapshot
from iot.sensor_source import NoDeviceSource, SensorStatus, SerialSensorSource


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


class FakeSerial:
    """readline() returns queued lines, then b"" (timeout); can simulate unplugging."""

    def __init__(self, lines=()):
        self.lines = list(lines)
        self.unplugged = False
        self.closed = False

    def readline(self):
        if self.unplugged:
            raise OSError("device disconnected")
        return self.lines.pop(0) if self.lines else b""

    def close(self):
        self.closed = True


def line(**overrides):
    msg = {"v": 1, "type": "reading", "hr_bpm": 70, "hr_valid": 1,
           "spo2_pct": 98, "spo2_valid": 1, "finger": 1, "uptime_ms": 5}
    msg.update(overrides)
    return (json.dumps(msg) + "\n").encode()


def make_source(fake=None, clock=None):
    fake = fake or FakeSerial()
    clock = clock or FakeClock()
    src = SerialSensorSource("FAKE0", serial_factory=lambda port, baud: fake, clock=clock)
    return src, fake, clock


def test_no_device_source_never_has_readings():
    snap = NoDeviceSource().snapshot()
    assert snap.status is SensorStatus.NOT_CONFIGURED and snap.reading is None
    view = format_snapshot(snap)
    assert view["connection"].startswith("Disconnected")
    assert view["heart_rate"] == NO_VALUE and view["spo2"] == NO_VALUE
    assert view["timestamp"] == "No reading received"


def test_missing_device_reports_unavailable():
    def missing(port, baud):
        raise OSError("could not open port 'COM99': FileNotFoundError")
    src = SerialSensorSource("COM99", serial_factory=missing)
    assert src.start() is False
    snap = src.snapshot()
    assert snap.status is SensorStatus.UNAVAILABLE and "COM99" in snap.detail
    assert snap.reading is None
    assert format_snapshot(snap)["connection"].startswith("Disconnected")


def test_missing_pyserial_reports_unavailable(monkeypatch):
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "serial":
            raise ImportError("No module named 'serial'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    src = SerialSensorSource("COM3")  # default factory tries to import pyserial
    assert src.open() is False
    snap = src.snapshot()
    assert snap.status is SensorStatus.UNAVAILABLE and "pyserial" in snap.detail


def test_waiting_then_no_data_when_device_silent():
    src, fake, clock = make_source()
    assert src.open()
    src.poll_once()
    assert src.snapshot().status is SensorStatus.WAITING
    clock.t = 11  # past the connect timeout, still nothing received
    snap = src.snapshot()
    assert snap.status is SensorStatus.NO_DATA and snap.reading is None


def test_valid_reading_goes_live():
    src, fake, clock = make_source(FakeSerial([line()]))
    src.open()
    src.poll_once()
    snap = src.snapshot()
    assert snap.status is SensorStatus.LIVE
    assert snap.reading.heart_rate_bpm == 70 and snap.reading.spo2_percent == 98
    view = format_snapshot(snap)
    assert view["heart_rate"] == "70" and view["spo2"] == "98" and view["values_are_live"]
    assert "ago" in view["timestamp"]


def test_malformed_lines_do_not_create_readings():
    src, fake, clock = make_source(FakeSerial([b"garbage\n", b"{bad json\n", b"\xff\n"]))
    src.open()
    for _ in range(3):
        src.poll_once()
    clock.t = 11
    snap = src.snapshot()
    assert snap.reading is None and snap.status is SensorStatus.NO_DATA
    assert snap.last_error


def test_invalid_measurement_replaces_previous_values():
    src, fake, clock = make_source(FakeSerial([line(), line(hr_bpm=400, spo2_pct=20)]))
    src.open()
    src.poll_once()
    src.poll_once()
    snap = src.snapshot()
    view = format_snapshot(snap)
    # The old 70/98 must not keep showing once the device sends invalid values.
    assert view["heart_rate"] == NO_VALUE and view["spo2"] == NO_VALUE
    assert "outside plausible range" in snap.detail


def test_readings_go_stale():
    src, fake, clock = make_source(FakeSerial([line()]))
    src.open()
    src.poll_once()
    clock.t = 6  # more than 5 s since the last valid reading
    snap = src.snapshot()
    assert snap.status is SensorStatus.STALE and not format_snapshot(snap)["values_are_live"]


def test_unplugged_device_reports_disconnected():
    fake = FakeSerial([line()])
    src, _, clock = make_source(fake)
    src.open()
    src.poll_once()
    fake.unplugged = True
    assert src.poll_once() is False
    snap = src.snapshot()
    assert snap.status is SensorStatus.DISCONNECTED and fake.closed
    assert format_snapshot(snap)["connection"].startswith("Disconnected")


def test_device_error_status():
    src, fake, clock = make_source(
        FakeSerial([b'{"v":1,"type":"status","msg":"sensor_not_found"}\n']))
    src.open()
    src.poll_once()
    snap = src.snapshot()
    assert snap.status is SensorStatus.DEVICE_ERROR and snap.reading is None
    assert "sensor_not_found" in snap.detail


def test_no_finger_is_live_but_has_no_values():
    src, fake, clock = make_source(FakeSerial([line(finger=0)]))
    src.open()
    src.poll_once()
    snap = src.snapshot()
    view = format_snapshot(snap)
    assert snap.status is SensorStatus.LIVE and "finger" in snap.detail.lower()
    assert view["heart_rate"] == NO_VALUE and view["spo2"] == NO_VALUE


def test_background_thread_and_close():
    fake = FakeSerial([line()])
    src, _, _ = make_source(fake)
    assert src.start()
    src.close()
    assert fake.closed and src.snapshot().status is SensorStatus.DISCONNECTED
