"""Train a baseline classifier and save model artifacts."""
from pathlib import Path
import json
import sys

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "hypertension_clean.csv"
MODEL_DIR = ROOT / "machine_learning" / "models"
TARGET_COLUMN = "Hypertension_Status"
RANDOM_STATE = 42

# Confirm the target's definition before finalizing this decision. If labels were
# created from blood-pressure thresholds, including those measurements can leak
# the rule used to create the target. This baseline excludes them when present.
POTENTIAL_LEAKAGE_COLUMNS = {"Systolic_BP", "Diastolic_BP"}


def main() -> None:
    if not DATA_PATH.exists():
        sys.exit(
            f"Cleaned dataset not found: {DATA_PATH}\n"
            "Run: python data_analysis/preprocessing.py"
        )

    df = pd.read_csv(DATA_PATH)
    if TARGET_COLUMN not in df.columns:
        sys.exit(f"Target column {TARGET_COLUMN!r} is missing.")

    df = df.dropna(subset=[TARGET_COLUMN]).copy()
    excluded = [c for c in POTENTIAL_LEAKAGE_COLUMNS if c in df.columns]
    X = df.drop(columns=[TARGET_COLUMN, *excluded], errors="ignore")
    y = df[TARGET_COLUMN].astype(str)

    if X.shape[1] == 0:
        sys.exit("No predictor columns remain after excluding target/leakage fields.")
    if y.nunique() < 2:
        sys.exit("Training requires at least two target classes.")

    numeric_columns = X.select_dtypes(include="number").columns.tolist()
    categorical_columns = [c for c in X.columns if c not in numeric_columns]
    transformers = []

    if numeric_columns:
        transformers.append(("numeric", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), numeric_columns))
    if categorical_columns:
        transformers.append(("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical_columns))

    model = Pipeline([
        ("preprocessor", ColumnTransformer(transformers=transformers)),
        ("classifier", RandomForestClassifier(
            n_estimators=300, class_weight="balanced",
            random_state=RANDOM_STATE, n_jobs=-1
        )),
    ])
    model.fit(X, y)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_DIR / "hypertension_model.joblib")
    options = {}
    for column in categorical_columns:
        values = X[column].dropna().astype(str).unique().tolist()
        options[column] = sorted(values)[:100]

    schema = {
        "target_column": TARGET_COLUMN,
        "feature_columns": X.columns.tolist(),
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "categorical_options": options,
        "classes": sorted(y.unique().tolist()),
        "excluded_potential_leakage_columns": sorted(excluded),
        "record_count": int(len(df)),
        "note": "Academic baseline; validate target definition and leakage risk.",
    }
    (MODEL_DIR / "feature_schema.json").write_text(
        json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Training records: {len(df)}")
    print(f"Predictor count: {len(X.columns)}")
    print(f"Excluded possible leakage columns: {excluded or 'none present'}")
    print(f"Target classes: {sorted(y.unique().tolist())}")
    print(f"Model saved to: {MODEL_DIR / 'hypertension_model.joblib'}")
    print(f"Feature schema saved to: {MODEL_DIR / 'feature_schema.json'}")
    print("Evaluate on a held-out test set before reporting results.")


if __name__ == "__main__":
    main()
