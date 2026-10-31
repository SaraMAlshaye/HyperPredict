"""Educational Streamlit interface for the trained HyperPredict model.

Run from the project root:   streamlit run app/app.py
Optional sensor: set HYPERPREDICT_SERIAL_PORT (e.g. COM3) or enter the port in the
sidebar. Sensor readings are displayed only; they are never sent to the model.
"""
import os
from pathlib import Path
import sys

import sklearn
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from iot.display import format_snapshot  # noqa: E402
from iot.sensor_source import NoDeviceSource, SerialSensorSource  # noqa: E402
from machine_learning.features import FEATURE_COLUMNS  # noqa: E402
from machine_learning.inference import build_input_row, load_artifacts, predict  # noqa: E402

st.set_page_config(page_title="HyperPredict", page_icon="🩺", layout="centered")
st.title("HyperPredict")
st.caption("Educational hypertension-status classification prototype (NHANES 2021–2023)")
st.warning(
    "Not a medical device. Do not use this demo for diagnosis, treatment, or "
    "personal medical decisions. Consult a qualified healthcare professional."
)


@st.cache_resource
def get_model():
    return load_artifacts()


try:
    model, schema = get_model()
except FileNotFoundError as exc:
    st.info(f"{exc}\n\nFirst build the data: python data_analysis/run_pipeline.py")
    st.stop()

if schema["feature_columns"] != FEATURE_COLUMNS:
    # Never silently feed a model inputs it was not trained on.
    st.error(f"The saved model expects {schema['feature_columns']}, but this code version "
             f"uses {FEATURE_COLUMNS}. Retrain: python -m machine_learning.train")
    st.stop()

if schema["versions"].get("scikit-learn") != sklearn.__version__:
    st.caption(f"Note: model saved with scikit-learn {schema['versions'].get('scikit-learn')}, "
               f"running {sklearn.__version__}. Retrain if predictions fail.")


# --- Optional sensor device (display only) -------------------------------------
def current_source():
    return st.session_state.get("sensor_source") or NoDeviceSource()


with st.sidebar:
    st.header("Sensor device")
    st.caption("Arduino/ESP32 + MAX30102 over USB serial. Hardware is optional; the "
               "prediction form works without it.")
    port = st.text_input("Serial port", value=os.environ.get("HYPERPREDICT_SERIAL_PORT", ""),
                         placeholder="e.g. COM3 or /dev/ttyUSB0")
    col_connect, col_disconnect = st.columns(2)
    if col_connect.button("Connect", disabled=not port.strip()):
        current_source().close()
        source = SerialSensorSource(port.strip())
        source.start()  # on failure the source reports why; nothing is faked
        st.session_state["sensor_source"] = source
    if col_disconnect.button("Disconnect"):
        current_source().close()
        st.session_state.pop("sensor_source", None)

live_source = "sensor_source" in st.session_state


@st.fragment(run_every=2 if live_source else None)
def sensor_panel():
    view = format_snapshot(current_source().snapshot())
    st.subheader("Live sensor readings")
    show = {"ok": st.success, "info": st.info, "warn": st.warning,
            "error": st.error, "off": st.info}[view["level"]]
    show(f"**Device: {view['connection']}** — {view['status']}. {view['detail']}")
    c1, c2 = st.columns(2)
    c1.metric("Heart rate (BPM)", view["heart_rate"])
    c2.metric("SpO₂ (%)", view["spo2"])
    st.caption(f"Latest measurement received: {view['timestamp']}"
               + ("" if view["values_are_live"] or view["timestamp"] == "No reading received"
                  else " — not current"))
    st.caption("Display only. These readings are **not** sent to the model: it was not "
               "trained on SpO₂, and fingertip heart rate has not been validated against the "
               "blood-pressure-cuff pulse used in training.")


sensor_panel()
st.divider()

# --- Prediction form (model inputs only) ----------------------------------------
st.subheader("Educational prediction")
st.write(
    f"Model: **{schema['model_name']}**. It estimates whether a person would meet the "
    "survey's hypertension definition (measured BP ≥ 130/80 mmHg or taking BP medication) "
    "from age, sex, race/ethnicity, BMI and resting pulse."
)
st.caption(
    "Blood-pressure readings are deliberately not inputs: they define the label. "
    "SpO₂ is not used, because the training data has no oxygen-saturation measurement. "
    "Enter pulse by hand; the sensor heart rate is not copied in automatically."
)

with st.form("prediction_form"):
    values = {}
    for col, spec in schema["numeric_inputs"].items():
        label = f"{spec['label']} ({spec['unit']})" + ("" if not spec["optional"] else " — optional")
        values[col] = st.number_input(label, min_value=float(spec["min"]),
                                      max_value=float(spec["max"]), value=None,
                                      step=float(spec["step"]), help=spec["help"],
                                      placeholder="Leave blank if unknown" if spec["optional"]
                                      else "Required")
    for col, options in schema["categorical_options"].items():
        values[col] = st.selectbox(col.replace("_", " "), options=options, index=None,
                                   placeholder="Choose one")
    submitted = st.form_submit_button("Run educational prediction")

if submitted:
    row, errors = build_input_row(values, schema)
    if errors:
        for error in errors:
            st.error(error)
    else:
        try:
            result = predict(model, schema, row)
        except Exception as exc:  # unexpected model failure
            st.error(f"Could not produce a prediction for these inputs: {exc}")
        else:
            st.subheader("Model output")
            st.metric("Model score for the hypertension class", f"{result['probability']:.0%}")
            st.write(f"Dataset label predicted at threshold {schema['decision_threshold']}: "
                     f"**{result['label_text']}**")
            blanks = [schema["numeric_inputs"][c]["label"] for c in schema["numeric_inputs"]
                      if row[c].isna().any()]
            if blanks:
                st.caption("Left blank and filled with the training-data median: "
                           + ", ".join(blanks) + ".")
            m = schema["test_metrics"]
            st.caption(
                f"On held-out survey participants this model found {m['recall']:.0%} of people "
                f"with hypertension and was right {m['precision']:.0%} of the time it predicted "
                f"hypertension (ROC-AUC {m['roc_auc']:.2f}). The score is not a calibrated "
                "personal risk and is not a diagnosis; only a blood-pressure measurement by a "
                "professional can tell whether someone has hypertension."
            )
