"""Educational Streamlit interface for the trained HyperPredict baseline."""
from pathlib import Path
import json

import joblib
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "machine_learning" / "models" / "hypertension_model.joblib"
SCHEMA_PATH = ROOT / "machine_learning" / "models" / "feature_schema.json"

st.set_page_config(page_title="HyperPredict", page_icon="🩺", layout="centered")
st.title("HyperPredict")
st.caption("Educational hypertension-status classification prototype")
st.warning(
    "Not a medical device. Do not use this demo for diagnosis, treatment, or "
    "personal medical decisions. Consult a qualified healthcare professional."
)

if not MODEL_PATH.exists() or not SCHEMA_PATH.exists():
    st.info(
        "The model has not been trained yet. Add the approved dataset to "
        "data/raw/hypertension.csv, then run the preprocessing and training scripts."
    )
    st.stop()

model = joblib.load(MODEL_PATH)
schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
st.write("Enter values that match the dataset used to train the model.")
st.caption(
    "This prototype is only as reliable as its dataset and evaluation process. "
    "Some health-related fields may be excluded from the baseline to reduce leakage."
)

with st.form("prediction_form"):
    values = {}
    for column in schema["feature_columns"]:
        if column in schema["numeric_columns"]:
            values[column] = st.number_input(column, value=0.0, format="%.3f")
        else:
            options = schema.get("categorical_options", {}).get(column, [])
            if options:
                values[column] = st.selectbox(column, options=options)
            else:
                values[column] = st.text_input(column)
    submitted = st.form_submit_button("Run educational prediction")

if submitted:
    row = pd.DataFrame([values], columns=schema["feature_columns"])
    try:
        prediction = str(model.predict(row)[0])
        st.subheader("Model output")
        st.write(f"Predicted dataset label: **{prediction}**")
        if hasattr(model, "predict_proba"):
            scores = model.predict_proba(row)[0]
            st.write("Model class scores (not calibrated medical probabilities):")
            results = pd.DataFrame({
                "Class": [str(value) for value in model.classes_],
                "Model score": scores,
            }).sort_values("Model score", ascending=False)
            st.dataframe(results, hide_index=True, use_container_width=True)
        st.caption(
            "This is an educational machine-learning output, not a clinical "
            "assessment or a measure of an individual's true risk."
        )
    except Exception as exc:
        st.error(f"Could not produce a prediction for these inputs: {exc}")
