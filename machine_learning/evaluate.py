"""Evaluate a baseline pipeline on a stratified held-out test set."""
from pathlib import Path
import sys

import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    ConfusionMatrixDisplay,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from features import (
    RANDOM_STATE, TEST_SIZE, build_preprocessor, load_features_and_target,
)

ROOT = Path(__file__).resolve().parents[1]
FIGURES_DIR = ROOT / "results" / "figures"


def main() -> None:
    X, y = load_features_and_target()
    if y.nunique() < 2:
        sys.exit("Evaluation requires at least two target classes.")

    # Split first; the preprocessor inside the Pipeline is fitted on X_train only.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    model = Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier", RandomForestClassifier(
            n_estimators=300, class_weight="balanced",
            random_state=RANDOM_STATE, n_jobs=-1
        )),
    ])
    model.fit(X_train, y_train)
    predictions = model.predict(X_test)

    print(f"Test records: {len(y_test)}")
    print(f"Predictors: {X.columns.tolist()}")
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
