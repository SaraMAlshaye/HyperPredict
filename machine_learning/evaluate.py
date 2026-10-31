"""Independently check the saved model artifact on the held-out test set.

Run from the project root (after training):   python -m machine_learning.evaluate

It reloads machine_learning/models/hypertension_model.joblib, rebuilds the same
stratified test split, recomputes the metrics, confirms they match the numbers saved
at training time, checks the feature schema, and runs edge-case predictions
(missing optional values). It also saves the selected model's confusion matrix.
Exit code 1 means a check failed.
"""
import json
import sys

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay, accuracy_score, classification_report, f1_score,
    precision_score, recall_score, roc_auc_score,
)

from machine_learning.features import (
    FEATURE_COLUMNS, FIGURES_DIR, LEAKAGE_COLUMNS, MODEL_PATH, SCHEMA_PATH, TARGET_LABELS,
    load_features_and_target, split_train_test,
)

failures = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
    if not ok:
        failures.append(name)


def main() -> None:
    if not MODEL_PATH.exists() or not SCHEMA_PATH.exists():
        sys.exit("No trained model found. Run: python -m machine_learning.train")
    model = joblib.load(MODEL_PATH)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {schema['model_name']} (trained {schema['trained_utc']})")

    check("schema features match approved feature list",
          schema["feature_columns"] == FEATURE_COLUMNS)
    check("no leakage columns in schema features",
          not set(schema["feature_columns"]) & set(LEAKAGE_COLUMNS))
    check("SpO2 is not a model input",
          not any("spo2" in c.lower() or "oxygen" in c.lower() for c in schema["feature_columns"]))
    check("model expects the same feature names and order",
          list(model.feature_names_in_) == FEATURE_COLUMNS)

    X, y = load_features_and_target()
    _, X_test, _, y_test = split_train_test(X, y)
    check("test split size matches training run", len(X_test) == schema["test_rows"],
          f"{len(X_test)} rows")

    threshold = schema["decision_threshold"]
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= threshold).astype(int)
    metrics = {
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred),
        "recall": recall_score(y_test, pred),
        "specificity": recall_score(1 - y_test, 1 - pred),
        "f1": f1_score(y_test, pred),
        "roc_auc": roc_auc_score(y_test, proba),
    }
    for k, v in metrics.items():
        saved = schema["test_metrics"][k]
        check(f"test {k} reproduces saved value", abs(v - saved) < 1e-3,
              f"{v:.4f} (saved {saved:.4f})")
    print("\n" + classification_report(y_test, pred,
                                       target_names=[TARGET_LABELS[0], TARGET_LABELS[1]]))

    # Edge cases the app can send: optional fields left blank, extreme but valid values.
    base = X_test.iloc[[0]].copy()
    blank = base.copy()
    optional = [c for c, spec in schema["numeric_inputs"].items() if spec["optional"]]
    blank[optional] = np.nan
    extreme = base.copy()
    extreme[["Age_Years", "BMI", "Pulse_BPM"]] = [80, 60.0, 150.0]
    for label, row in [("all optional inputs missing", blank), ("extreme valid inputs", extreme)]:
        p = model.predict_proba(row[FEATURE_COLUMNS])[0, 1]
        check(f"prediction works with {label}", 0.0 <= p <= 1.0, f"p={p:.3f}")

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    disp = ConfusionMatrixDisplay.from_predictions(
        y_test, pred, labels=[0, 1], display_labels=[TARGET_LABELS[0], TARGET_LABELS[1]],
        cmap="Blues", colorbar=False)
    disp.ax_.set_title(f"{schema['model_name']} - held-out test set (threshold {threshold})")
    disp.figure_.tight_layout()
    disp.figure_.savefig(FIGURES_DIR / "confusion_matrix.png", dpi=160)
    plt.close(disp.figure_)
    print(f"Confusion matrix saved to {FIGURES_DIR / 'confusion_matrix.png'}")

    print(f"\n{'All checks passed.' if not failures else f'{len(failures)} check(s) failed.'}")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    pd.set_option("display.width", 120)
    main()
