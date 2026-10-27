"""Train a baseline classifier and save model artifacts."""
from pathlib import Path
import json
import sys

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

from features import (
    CATEGORICAL_FEATURES, LEAKAGE_COLUMNS, NUMERIC_FEATURES, RANDOM_STATE,
    TARGET_COLUMN, build_preprocessor, load_features_and_target,
)

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "machine_learning" / "models"


def main() -> None:
    # Only the approved features are loaded; BP readings, questionnaire answers and
    # SEQN are never in X (see docs/DATASET.md, "Target leakage").
    X, y = load_features_and_target()
    if y.nunique() < 2:
        sys.exit("Training requires at least two target classes.")

    model = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier", RandomForestClassifier(
            n_estimators=300, class_weight="balanced",
            random_state=RANDOM_STATE, n_jobs=-1
        )),
    ])
    model.fit(X, y)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_DIR / "hypertension_model.joblib")
    options = {c: sorted(X[c].dropna().astype(str).unique().tolist())
               for c in CATEGORICAL_FEATURES}

    schema = {
        "target_column": TARGET_COLUMN,
        "target_labels": {"0": "No hypertension", "1": "Hypertension"},
        "feature_columns": X.columns.tolist(),
        "numeric_columns": NUMERIC_FEATURES,
        "categorical_columns": CATEGORICAL_FEATURES,
        "categorical_options": options,
        "classes": sorted(int(v) for v in y.unique()),
        "excluded_leakage_columns": sorted(LEAKAGE_COLUMNS),
        "record_count": int(len(X)),
        "note": "Academic baseline on NHANES 2021-2023; SpO2 is not a model input.",
    }
    (MODEL_DIR / "feature_schema.json").write_text(
        json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Training records: {len(X)}")
    print(f"Predictors: {X.columns.tolist()}")
    print(f"Target classes: {schema['classes']}")
    print(f"Model saved to: {MODEL_DIR / 'hypertension_model.joblib'}")
    print(f"Feature schema saved to: {MODEL_DIR / 'feature_schema.json'}")
    print("Evaluate on a held-out test set before reporting results.")


if __name__ == "__main__":
    main()
