"""Evaluate a baseline pipeline on a stratified held-out test set."""
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    ConfusionMatrixDisplay,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed" / "hypertension_clean.csv"
FIGURES_DIR = ROOT / "results" / "figures"
TARGET_COLUMN = "Hypertension_Status"
RANDOM_STATE = 42
POTENTIAL_LEAKAGE_COLUMNS = {"Systolic_BP", "Diastolic_BP"}


def main() -> None:
    if not DATA_PATH.exists():
        sys.exit("Cleaned dataset not found. Run data_analysis/preprocessing.py first.")

    df = pd.read_csv(DATA_PATH).dropna(subset=[TARGET_COLUMN]).copy()
    excluded = [c for c in POTENTIAL_LEAKAGE_COLUMNS if c in df.columns]
    X = df.drop(columns=[TARGET_COLUMN, *excluded], errors="ignore")
    y = df[TARGET_COLUMN].astype(str)
    if y.nunique() < 2:
        sys.exit("Evaluation requires at least two target classes.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
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
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    print(f"Test records: {len(y_test)}")
    print(f"Potential leakage columns excluded: {excluded or 'none present'}")
    print(f"Accuracy: {accuracy_score(y_test, predictions):.4f}")
    print("\nClassification report:")
    print(classification_report(y_test, predictions, zero_division=0))
    labels = sorted(y.unique().tolist())
    print("Confusion matrix:")
    print(confusion_matrix(y_test, predictions, labels=labels))

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    display = ConfusionMatrixDisplay.from_predictions(
        y_test, predictions, labels=labels, xticks_rotation=30, cmap="Blues"
    )
    display.ax_.set_title("Baseline model - held-out test set")
    display.figure_.tight_layout()
    path = FIGURES_DIR / "confusion_matrix.png"
    display.figure_.savefig(path, dpi=160)
    plt.close(display.figure_)
    print(f"Confusion matrix figure saved to: {path}")


if __name__ == "__main__":
    main()
