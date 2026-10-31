"""Load the saved model and make validated predictions (used by app/app.py).

Keeping this logic outside Streamlit means it can be tested directly. Inputs are
checked against the feature schema saved at training time, so the app always sends
exactly the trained features, in the trained order, with the trained categories.
"""
import json
import math

import joblib
import numpy as np
import pandas as pd

from machine_learning.features import MODEL_PATH, SCHEMA_PATH


def load_artifacts():
    """Return (model, schema), or raise FileNotFoundError if training has not been run."""
    if not MODEL_PATH.exists() or not SCHEMA_PATH.exists():
        raise FileNotFoundError("Model not trained yet. Run: python -m machine_learning.train")
    return joblib.load(MODEL_PATH), json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def build_input_row(values: dict, schema: dict) -> tuple[pd.DataFrame | None, list[str]]:
    """Validate raw form values. Returns (one-row DataFrame, []) or (None, errors).

    Optional numeric fields may be None/blank; the model's training-fitted imputer
    fills them. Unknown keys (e.g. an SpO2 reading) are rejected, never passed on.
    """
    errors = []
    unexpected = sorted(set(values) - set(schema["feature_columns"]))
    if unexpected:
        errors.append(f"Inputs not used by the model were supplied: {unexpected}")
    row = {}
    for col, spec in schema["numeric_inputs"].items():
        value = values.get(col)
        if value is None or (isinstance(value, float) and math.isnan(value)):
            if not spec["optional"]:
                errors.append(f"{spec['label']} is required.")
            row[col] = np.nan
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            errors.append(f"{spec['label']} must be a number.")
            continue
        if not spec["min"] <= value <= spec["max"]:
            errors.append(f"{spec['label']} must be between {spec['min']} and {spec['max']} "
                          f"{spec['unit']}.")
        row[col] = value
    for col, options in schema["categorical_options"].items():
        value = values.get(col)
        if value not in options:
            errors.append(f"{col.replace('_', ' ')} must be one of: {', '.join(options)}.")
        row[col] = value
    if errors:
        return None, errors
    return pd.DataFrame([row], columns=schema["feature_columns"]), []


def predict(model, schema: dict, row: pd.DataFrame) -> dict:
    """Return the model's probability of the hypertension class and its label."""
    probability = float(model.predict_proba(row[schema["feature_columns"]])[0, 1])
    label = int(probability >= schema["decision_threshold"])
    return {"probability": probability, "label": label,
            "label_text": schema["target_labels"][str(label)]}
