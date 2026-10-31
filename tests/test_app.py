"""Run the Streamlit app headlessly: it must work with no hardware and fake nothing."""
from pathlib import Path

import pytest

from machine_learning.features import MODEL_PATH

APP = str(Path(__file__).resolve().parents[1] / "app" / "app.py")
pytestmark = pytest.mark.skipif(not MODEL_PATH.exists(),
                                reason="model not trained (python -m machine_learning.train)")


@pytest.fixture
def app(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.delenv("HYPERPREDICT_SERIAL_PORT", raising=False)
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception, at.exception
    return at


def all_text(at):
    parts = [e.value for e in at.info] + [e.value for e in at.error] + \
            [e.value for e in at.warning] + [e.value for e in at.success] + \
            [c.value for c in at.caption] + [m.value for m in at.markdown]
    return "\n".join(str(p) for p in parts)


def test_runs_without_device_and_shows_disconnected(app):
    text = all_text(app)
    assert "Device: Disconnected" in text and "No device configured" in text
    metrics = {m.label: m.value for m in app.metric}
    assert metrics["Heart rate (BPM)"] == "—" and metrics["SpO₂ (%)"] == "—"
    assert "No reading received" in text
    assert "Not a medical device" in "\n".join(w.value for w in app.warning)


def test_income_field_removed(app):
    labels = [n.label for n in app.number_input]
    assert not any("income" in label.lower() for label in labels)
    assert len(labels) == 3
    assert labels[0].startswith("Age") and labels[1].startswith("Body mass index")
    assert labels[2].startswith("Resting pulse")


def test_prediction_works_without_hardware(app):
    app.number_input[0].set_value(58)
    app.selectbox[0].set_value("Female")
    app.selectbox[1].set_value("Non-Hispanic Black")
    submit = [b for b in app.button if "prediction" in b.label.lower()][0]
    submit.click().run()
    assert not app.exception and not app.error
    assert any("hypertension class" in m.label for m in app.metric)


def test_connect_to_missing_port_is_reported_not_faked(app):
    app.sidebar.text_input[0].set_value("COM_DOES_NOT_EXIST").run()
    connect = [b for b in app.sidebar.button if b.label == "Connect"][0]
    connect.click().run()
    assert not app.exception
    text = all_text(app)
    assert "Device: Disconnected" in text and "Cannot connect" in text
    metrics = {m.label: m.value for m in app.metric}
    assert metrics["Heart rate (BPM)"] == "—" and metrics["SpO₂ (%)"] == "—"
