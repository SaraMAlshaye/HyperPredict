"""Turn a SensorSnapshot into display text. Kept separate from Streamlit so it is testable.

Rule: a value is shown only if the device actually sent a valid one. Otherwise "—".
"""
from datetime import datetime, timezone

from iot.sensor_source import SensorSnapshot, SensorStatus

NO_VALUE = "—"
LEVELS = {  # how the app colours the status line
    SensorStatus.LIVE: "ok",
    SensorStatus.WAITING: "info",
    SensorStatus.STALE: "warn",
    SensorStatus.NO_DATA: "warn",
    SensorStatus.DEVICE_ERROR: "error",
    SensorStatus.UNAVAILABLE: "error",
    SensorStatus.DISCONNECTED: "error",
    SensorStatus.NOT_CONFIGURED: "off",
}


def format_snapshot(snap: SensorSnapshot, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    r = snap.reading
    connected = snap.status in (SensorStatus.LIVE, SensorStatus.WAITING, SensorStatus.STALE,
                                SensorStatus.NO_DATA, SensorStatus.DEVICE_ERROR)
    hr = f"{r.heart_rate_bpm:.0f}" if r and r.heart_rate_bpm is not None else NO_VALUE
    spo2 = f"{r.spo2_percent:.0f}" if r and r.spo2_percent is not None else NO_VALUE
    if r is None:
        timestamp = "No reading received"
    else:
        local = r.received_at.astimezone()
        age = (now - r.received_at).total_seconds()
        timestamp = f"{local:%Y-%m-%d %H:%M:%S} ({age:.0f} s ago)"
    port = f" on {snap.port}" if snap.port else ""
    return {
        "connection": ("Connected" if connected else "Disconnected") + port,
        "status": snap.status.value,
        "level": LEVELS[snap.status],
        "detail": snap.detail,
        "heart_rate": hr,
        "spo2": spo2,
        "timestamp": timestamp,
        "values_are_live": snap.status is SensorStatus.LIVE,
        "last_error": snap.last_error,
    }
