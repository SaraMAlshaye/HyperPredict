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
    CATEGORICAL_FEATURES, CLEAN_PATH, FEATURE_COLUMNS, LEAKAGE_COLUMNS,
    NUMERIC_FEATURES, TARGET_COLUMN,
)

DATA_PATH = CLEAN_PATH
RANDOM_STATE = 42
TEST_SIZE = 0.2


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
