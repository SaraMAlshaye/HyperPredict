"""Parser tests: malformed lines and invalid measurements must never become values."""
import json

import pytest

from iot.sensor_protocol import parse_line


def reading(**overrides):
    msg = {"v": 1, "type": "reading", "hr_bpm": 72, "hr_valid": 1,
           "spo2_pct": 97, "spo2_valid": 1, "finger": 1, "uptime_ms": 1000}
    msg.update(overrides)
    return json.dumps(msg)


def test_valid_reading():
    r = parse_line(reading()).reading
    assert r.heart_rate_bpm == 72 and r.spo2_percent == 97
    assert r.finger_detected and r.device_uptime_ms == 1000 and not r.warnings


def test_bytes_input_and_trailing_newline():
    r = parse_line((reading() + "\r\n").encode()).reading
    assert r.heart_rate_bpm == 72


@pytest.mark.parametrize("line, fragment", [
    ("not json at all", "not JSON"),
    ("{broken", "not JSON"),
    ("[1, 2, 3]", "not an object"),
    ('{"v": 2, "type": "reading"}', "unsupported protocol"),
    ('{"type": "reading"}', "unsupported protocol"),
    ('{"v": 1, "type": "mystery"}', "unknown message type"),
    (reading(finger="yes"), "'finger'"),
    (reading(finger=None), "'finger'"),
    ('{"v": 1, "type": "status"}', "status message"),
    ("x" * 600, "too long"),
])
def test_malformed_lines_are_rejected(line, fragment):
    result = parse_line(line)
    assert result.reading is None and result.error and fragment in result.error


def test_invalid_utf8_is_rejected():
    result = parse_line(b"\xff\xfe\x00garbage")
    assert result.reading is None and "UTF-8" in result.error


@pytest.mark.parametrize("line", ["", "   ", "\n", b"\r\n"])
def test_blank_lines_are_ignored(line):
    result = parse_line(line)
    assert result.ignored and result.reading is None and result.error is None


@pytest.mark.parametrize("overrides, hr, spo2", [
    ({"hr_bpm": 10}, None, 97),                    # implausibly low heart rate
    ({"hr_bpm": 300}, None, 97),                   # implausibly high heart rate
    ({"spo2_pct": 55}, 72, None),                  # below reliable SpO2 range
    ({"spo2_pct": 104}, 72, None),                 # impossible SpO2
    ({"hr_valid": 0, "hr_bpm": -999}, None, 97),   # device says estimate is invalid
    ({"spo2_valid": 0, "spo2_pct": -999}, 72, None),
    ({"hr_bpm": "72"}, None, 97),                  # string, not a number
    ({"hr_bpm": True}, None, 97),                  # bool is not a number
    ({"spo2_pct": None}, 72, None),
])
def test_invalid_measurements_become_none(overrides, hr, spo2):
    result = parse_line(reading(**overrides))
    r = result.reading
    assert r.heart_rate_bpm == hr and r.spo2_percent == spo2
    assert r.warnings


def test_nan_and_infinity_are_rejected():
    # json.loads accepts NaN/Infinity literals; they must not become values.
    r = parse_line('{"v":1,"type":"reading","hr_bpm":NaN,"hr_valid":1,'
                   '"spo2_pct":Infinity,"spo2_valid":1,"finger":1}').reading
    assert r.heart_rate_bpm is None and r.spo2_percent is None


def test_no_finger_discards_numbers():
    r = parse_line(reading(finger=0, hr_bpm=72, spo2_pct=97)).reading
    assert r.heart_rate_bpm is None and r.spo2_percent is None
    assert not r.finger_detected and "no finger detected" in r.warnings


def test_device_status_message():
    result = parse_line('{"v":1,"type":"status","msg":"sensor_not_found"}')
    assert result.device_status.message == "sensor_not_found" and result.reading is None
