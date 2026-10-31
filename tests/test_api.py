"""FastAPI backend tests: real model output, strict inputs, clear errors."""
import pytest

from machine_learning.features import MODEL_PATH

pytestmark = pytest.mark.skipif(not MODEL_PATH.exists(),
                                reason="model not trained (python -m machine_learning.train)")

VALID = {"Age_Years": 55, "BMI": 31.2, "Pulse_BPM": 72, "Sex": "Female",
         "Race_Ethnicity": "Non-Hispanic Black"}


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    from api.main import app
    with TestClient(app) as c:  # runs startup, which loads the saved model
        yield c


def test_health(client):
    body = client.get("/api/health").json()
    assert body["model_loaded"] is True and body["model_name"] == "Logistic Regression"
    assert body["schema_version"] == 3


def test_schema_comes_from_saved_model(client):
    body = client.get("/api/schema").json()
    assert body["feature_columns"] == ["Age_Years", "BMI", "Pulse_BPM", "Sex", "Race_Ethnicity"]
    assert body["categorical_options"]["Sex"] == ["Female", "Male"]
    assert "not a medical diagnosis" in body["disclaimer"]


def test_prediction_matches_existing_pipeline(client):
    from machine_learning.inference import build_input_row, load_artifacts, predict
    model, schema = load_artifacts()
    row, errors = build_input_row(VALID, schema)
    expected = predict(model, schema, row)

    res = client.post("/api/predict", json=VALID)
    assert res.status_code == 200
    body = res.json()
    assert body["probability"] == pytest.approx(expected["probability"], abs=1e-12)
    assert body["label"] == expected["label"]
    assert body["label_text"] == expected["label_text"]
    assert body["decision_threshold"] == 0.5
    assert set(body["inputs"]) == set(schema["feature_columns"])


def test_different_inputs_give_different_scores(client):
    young = client.post("/api/predict", json=dict(VALID, Age_Years=22, BMI=21.0)).json()
    older = client.post("/api/predict", json=dict(VALID, Age_Years=70, BMI=34.0)).json()
    assert young["probability"] < older["probability"]


def test_optional_values_may_be_null(client):
    res = client.post("/api/predict", json=dict(VALID, BMI=None, Pulse_BPM=None))
    assert res.status_code == 200 and 0 <= res.json()["probability"] <= 1


@pytest.mark.parametrize("extra", [{"SpO2": 97}, {"Height_cm": 160}, {"Weight_kg": 60},
                                   {"Mean_Systolic_BP": 140}, {"Poverty_Income_Ratio": 2}])
def test_extra_fields_are_rejected(client, extra):
    res = client.post("/api/predict", json=dict(VALID, **extra))
    assert res.status_code == 422


@pytest.mark.parametrize("changes", [{"Age_Years": 10}, {"Age_Years": 95}, {"BMI": 5},
                                     {"Pulse_BPM": 300}, {"Sex": "Other"},
                                     {"Race_Ethnicity": "Unknown"}])
def test_invalid_values_are_rejected_with_messages(client, changes):
    res = client.post("/api/predict", json=dict(VALID, **changes))
    assert res.status_code == 422
    assert isinstance(res.json()["detail"], list) and res.json()["detail"]


def test_missing_required_field(client):
    body = dict(VALID)
    body.pop("Age_Years")
    assert client.post("/api/predict", json=body).status_code == 422


def test_model_missing_returns_503(monkeypatch):
    from fastapi.testclient import TestClient
    import api.main as main
    monkeypatch.setattr(main, "load_artifacts",
                        lambda: (_ for _ in ()).throw(FileNotFoundError("Model not trained yet.")))
    with TestClient(main.app) as c:
        assert c.get("/api/health").json()["model_loaded"] is False
        res = c.post("/api/predict", json=VALID)
        assert res.status_code == 503 and "not trained" in res.json()["detail"]
    main._load()  # restore the real model for other tests
