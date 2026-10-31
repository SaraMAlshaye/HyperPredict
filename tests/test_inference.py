"""Model input tests: only trained features reach the model; SpO2/income are rejected."""
import pytest

from machine_learning.features import (
    DROPPED_FEATURES, FEATURE_COLUMNS, LEAKAGE_COLUMNS, MODEL_PATH,
)

pytestmark = pytest.mark.skipif(not MODEL_PATH.exists(),
                                reason="model not trained (python -m machine_learning.train)")

# The approved model inputs, in order. Changing them must be a deliberate decision.
EXPECTED_FEATURES = ["Age_Years", "BMI", "Pulse_BPM", "Sex", "Race_Ethnicity"]

VALID = {"Age_Years": 55, "BMI": 31.0, "Pulse_BPM": 72,
         "Sex": "Male", "Race_Ethnicity": "Non-Hispanic White"}


@pytest.fixture(scope="module")
def artifacts():
    from machine_learning.inference import load_artifacts
    return load_artifacts()


def test_schema_matches_code_and_has_no_leakage(artifacts):
    model, schema = artifacts
    assert FEATURE_COLUMNS == EXPECTED_FEATURES
    assert schema["feature_columns"] == EXPECTED_FEATURES
    assert list(schema["numeric_inputs"]) == ["Age_Years", "BMI", "Pulse_BPM"]
    assert list(model.feature_names_in_) == FEATURE_COLUMNS
    assert not set(FEATURE_COLUMNS) & set(LEAKAGE_COLUMNS)
    assert not set(FEATURE_COLUMNS) & set(DROPPED_FEATURES)
    assert not any("spo2" in c.lower() for c in FEATURE_COLUMNS)


def test_valid_prediction(artifacts):
    from machine_learning.inference import build_input_row, predict
    model, schema = artifacts
    row, errors = build_input_row(VALID, schema)
    assert errors == [] and list(row.columns) == FEATURE_COLUMNS
    result = predict(model, schema, row)
    assert 0 <= result["probability"] <= 1 and result["label"] in (0, 1)


def test_optional_fields_may_be_blank(artifacts):
    from machine_learning.inference import build_input_row, predict
    model, schema = artifacts
    values = dict(VALID, BMI=None, Pulse_BPM=None)
    row, errors = build_input_row(values, schema)
    assert errors == []
    assert 0 <= predict(model, schema, row)["probability"] <= 1


@pytest.mark.parametrize("extra", [{"SpO2": 97}, {"Poverty_Income_Ratio": 2.5},
                                   {"Mean_Systolic_BP": 140}])
def test_inputs_not_in_model_are_rejected(artifacts, extra):
    from machine_learning.inference import build_input_row
    _, schema = artifacts
    row, errors = build_input_row(dict(VALID, **extra), schema)
    assert row is None and any("not used by the model" in e for e in errors)


@pytest.mark.parametrize("changes, message", [
    ({"Age_Years": None}, "required"),
    ({"Age_Years": 10}, "between"),
    ({"Pulse_BPM": 400}, "between"),
    ({"Pulse_BPM": "fast"}, "number"),
    ({"Sex": "Unknown"}, "must be one of"),
    ({"Race_Ethnicity": None}, "must be one of"),
])
def test_invalid_inputs_are_rejected(artifacts, changes, message):
    from machine_learning.inference import build_input_row
    _, schema = artifacts
    row, errors = build_input_row(dict(VALID, **changes), schema)
    assert row is None and any(message in e for e in errors)
