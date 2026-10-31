"""Shared feature definitions and preprocessing for training, evaluation and the app.

The preprocessor below is UNFITTED. Put it inside a sklearn Pipeline with the model
and call fit() on the training split only, so imputation medians/modes and scaling
statistics never see test data. The fitted Pipeline then applies the same
transformations at prediction time.
"""
from pathlib import Path
import sys

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "data_analysis"))
from nhanes_config import (  # noqa: E402  (shared single source of truth)
    ANALYSIS_PATH, BMI_RANGE, CATEGORICAL_FEATURES, CLEAN_PATH, DROPPED_FEATURES,
    FEATURE_COLUMNS,
    LEAKAGE_COLUMNS,
    MIN_AGE, NUMERIC_FEATURES, PULSE_RANGE, REPORTS_DIR, FIGURES_DIR, TARGET_COLUMN,
)
from sklearn.model_selection import train_test_split  # noqa: E402

DATA_PATH = CLEAN_PATH
MODEL_DIR = ROOT / "machine_learning" / "models"
MODEL_PATH = MODEL_DIR / "hypertension_model.joblib"
SCHEMA_PATH = MODEL_DIR / "feature_schema.json"
RANDOM_STATE = 42
TEST_SIZE = 0.2
CV_FOLDS = 5
TARGET_LABELS = {0: "No hypertension", 1: "Hypertension"}

# Input metadata for the app: label, unit, allowed range, and whether it may be left blank.
# Ranges are the same plausibility rules used to clean the training data.
NUMERIC_INPUTS = {
    "Age_Years": {"label": "Age", "unit": "years", "min": MIN_AGE, "max": 80,
                  "step": 1.0, "optional": False,
                  "help": "Adults only. NHANES records ages 80 and over as 80."},
    "BMI": {"label": "Body mass index (BMI)", "unit": "kg/m²", "min": BMI_RANGE[0],
            "max": BMI_RANGE[1], "step": 0.1, "optional": True, "help": "Weight (kg) / height (m)²."},
    "Pulse_BPM": {"label": "Resting pulse", "unit": "beats/min", "min": PULSE_RANGE[0],
                  "max": PULSE_RANGE[1], "step": 1.0, "optional": True,
                  "help": "Training data used a seated, rested blood-pressure-cuff pulse."},
}
assert list(NUMERIC_INPUTS) == NUMERIC_FEATURES, "App inputs must match the model features"


def split_train_test(X: pd.DataFrame, y: pd.Series):
    """The single, reproducible 80/20 stratified split used by every script."""
    return train_test_split(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y)


def build_preprocessor() -> ColumnTransformer:
    """Median imputation + scaling for numbers; mode imputation + one-hot for categories."""
    return ColumnTransformer(transformers=[
        ("numeric", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), NUMERIC_FEATURES),
        ("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), CATEGORICAL_FEATURES),
    ])


def load_features_and_target(path: Path = DATA_PATH):
    """Load the model-ready CSV and return (X, y) using only approved feature columns."""
    if not path.exists():
        sys.exit(f"Cleaned dataset not found: {path}\nRun: python data_analysis/run_pipeline.py")
    df = pd.read_csv(path)
    missing = [c for c in FEATURE_COLUMNS + [TARGET_COLUMN] if c not in df.columns]
    if missing:
        sys.exit(f"Columns missing from {path.name}: {missing}")
    leaked = sorted(set(FEATURE_COLUMNS) & set(LEAKAGE_COLUMNS))
    if leaked:
        sys.exit(f"Leakage-prone columns listed as features: {leaked}")
    df = df.dropna(subset=[TARGET_COLUMN])
    return df[FEATURE_COLUMNS].copy(), df[TARGET_COLUMN].astype(int)
