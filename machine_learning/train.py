"""Train, compare and select hypertension classifiers on NHANES 2021-2023.

Run from the project root:   python -m machine_learning.train

Method
1. One stratified 80/20 train/test split (seed 42). The test set is not touched
   until step 3.
2. For each candidate model, 5-fold stratified cross-validation on the TRAINING set
   picks the hyperparameters (by ROC-AUC). Preprocessing lives inside the pipeline,
   so it is refitted on each fold's training part only.
3. Each tuned model is scored once on the held-out test set.
4. The final model is chosen with training-data CV results only (see SELECTION RULE),
   so the test set stays an unbiased check. The chosen pipeline, fitted on the
   training split, is saved as one artifact.
"""
from datetime import datetime, timezone
import json
import platform
import sys

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import sklearn
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score, roc_curve,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold

from machine_learning.features import (
    CATEGORICAL_FEATURES, CV_FOLDS, DROPPED_FEATURES, FEATURE_COLUMNS, FIGURES_DIR,
    LEAKAGE_COLUMNS,
    MODEL_DIR, MODEL_PATH, NUMERIC_FEATURES, NUMERIC_INPUTS, RANDOM_STATE, REPORTS_DIR,
    SCHEMA_PATH, TARGET_COLUMN, TARGET_LABELS, TEST_SIZE, load_features_and_target,
    split_train_test,
)
from machine_learning.models import COMPLEXITY_RANK, get_candidates

CV_METRICS = ["roc_auc", "recall", "precision", "f1", "accuracy"]
# SELECTION RULE: highest mean CV ROC-AUC; any model within this margin of the best
# counts as equivalent, and the simplest of those is chosen (easier to explain/check).
AUC_TIE_MARGIN = 0.01
# Below this test ROC-AUC the result is reported as inadequate even for a prototype.
MIN_ACCEPTABLE_AUC = 0.70
DECISION_THRESHOLD = 0.5
# Version 1: 7 features incl. Poverty_Income_Ratio. Version 2: income ratio removed.
# Version 3: 5 features (Age_Years, BMI, Pulse_BPM, Sex, Race_Ethnicity).
SCHEMA_VERSION = 3


def test_metrics(model, X_test, y_test) -> dict:
    proba = model.predict_proba(X_test)[:, 1]
    pred = (proba >= DECISION_THRESHOLD).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, pred, labels=[0, 1]).ravel()
    return {
        "accuracy": accuracy_score(y_test, pred),
        "precision": precision_score(y_test, pred, zero_division=0),
        "recall": recall_score(y_test, pred, zero_division=0),
        "specificity": tn / (tn + fp),
        "f1": f1_score(y_test, pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, proba),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "classification_report": classification_report(
            y_test, pred, target_names=[TARGET_LABELS[0], TARGET_LABELS[1]],
            output_dict=True, zero_division=0),
        "_proba": proba,
    }


def select_model(results: dict) -> tuple[str, str]:
    best_auc = max(r["cv"]["roc_auc_mean"] for r in results.values())
    tied = [n for n, r in results.items() if r["cv"]["roc_auc_mean"] >= best_auc - AUC_TIE_MARGIN]
    chosen = min(tied, key=lambda n: COMPLEXITY_RANK[n])
    leader = max(results, key=lambda n: results[n]["cv"]["roc_auc_mean"])
    if chosen == leader:
        why = (f"{chosen} had the highest mean cross-validated ROC-AUC on the training data "
               f"({best_auc:.3f}).")
    else:
        why = (f"{leader} had the highest mean CV ROC-AUC ({best_auc:.3f}), but {chosen} "
               f"was within {AUC_TIE_MARGIN} ({results[chosen]['cv']['roc_auc_mean']:.3f}) "
               f"and is simpler, so it was preferred. Models within the margin: {tied}.")
    return chosen, why


def plot_roc(results, y_test):
    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    for name, r in results.items():
        fpr, tpr, _ = roc_curve(y_test, r["test"]["_proba"])
        ax.plot(fpr, tpr, lw=1.8, label=f"{name} (AUC {r['test']['roc_auc']:.3f})")
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="Chance (AUC 0.500)")
    ax.set_xlabel("False positive rate (1 - specificity)")
    ax.set_ylabel("True positive rate (recall)")
    ax.set_title("ROC curves on the held-out test set")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "roc_curves.png", dpi=150)
    plt.close(fig)


def plot_confusion_matrices(results):
    n = len(results)
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 4))
    for ax, (name, r) in zip(np.atleast_1d(axes), results.items()):
        cm = r["test"]["confusion_matrix"]
        matrix = np.array([[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]])
        sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax,
                    xticklabels=["Pred: No HTN", "Pred: HTN"],
                    yticklabels=["True: No HTN", "True: HTN"])
        ax.set_title(f"{name}\nrecall {r['test']['recall']:.2f}, "
                     f"specificity {r['test']['specificity']:.2f}", fontsize=10)
    fig.suptitle("Confusion matrices on the held-out test set (threshold 0.5)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "confusion_matrices.png", dpi=150)
    plt.close(fig)


def plot_comparison(table: pd.DataFrame):
    metrics = ["test_accuracy", "test_precision", "test_recall", "test_f1", "test_roc_auc"]
    data = table.set_index("model")[metrics]
    data.columns = ["Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]
    ax = data.T.plot(kind="bar", figsize=(9, 5), rot=0, width=0.8)
    ax.set_ylim(0, 1.2)
    ax.set_ylabel("Score on held-out test set")
    ax.set_title("Model comparison (held-out test set, threshold 0.5)")
    ax.legend(fontsize=8, loc="upper center", ncol=len(data))
    for container in ax.containers:
        ax.bar_label(container, fmt="%.2f", fontsize=6, rotation=90, padding=2)
    ax.figure.tight_layout()
    ax.figure.savefig(FIGURES_DIR / "model_comparison.png", dpi=150)
    plt.close(ax.figure)


def plot_importance(model, X_test, y_test, name) -> dict:
    """Permutation importance on the test set, measured as the drop in ROC-AUC."""
    result = permutation_importance(model, X_test, y_test, scoring="roc_auc",
                                    n_repeats=20, random_state=RANDOM_STATE, n_jobs=-1)
    imp = pd.DataFrame({"feature": X_test.columns, "mean": result.importances_mean,
                        "std": result.importances_std}).sort_values("mean")
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.barh(imp["feature"], imp["mean"], xerr=imp["std"], color="#4C72B0")
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("Drop in test ROC-AUC when the feature is shuffled")
    ax.set_title(f"Permutation feature importance - {name}")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "feature_importance.png", dpi=150)
    plt.close(fig)
    return {row.feature: {"mean": round(row.mean, 4), "std": round(row.std, 4)}
            for row in imp.sort_values("mean", ascending=False).itertuples()}


def plot_threshold_tradeoff(y_test, proba, name):
    """Shows how recall and precision trade off as the decision threshold moves."""
    rows = []
    for t in np.linspace(0.05, 0.95, 91):
        pred = (proba >= t).astype(int)
        rows.append((t, recall_score(y_test, pred, zero_division=0),
                     precision_score(y_test, pred, zero_division=0),
                     recall_score(1 - y_test, 1 - pred, zero_division=0)))
    t, rec, prec, spec = map(np.array, zip(*rows))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(t, rec, label="Recall (hypertension found)")
    ax.plot(t, prec, label="Precision (positive predictions that are correct)")
    ax.plot(t, spec, label="Specificity (no-hypertension correctly cleared)")
    ax.axvline(DECISION_THRESHOLD, color="black", ls="--", lw=1, label="Threshold used (0.5)")
    ax.set_xlabel("Decision threshold on predicted probability")
    ax.set_ylabel("Score")
    ax.set_title(f"Threshold trade-off on the test set - {name}\n"
                 "(for discussion only; the threshold was not tuned on the test set)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "threshold_tradeoff.png", dpi=150)
    plt.close(fig)


def write_markdown(report: dict, table: pd.DataFrame) -> None:
    sel = report["selected_model"]
    t = report["models"][sel]["test"]
    cm = t["confusion_matrix"]
    lines = [
        "# Model evaluation report (generated by `python -m machine_learning.train`)", "",
        f"- Generated: {report['generated_utc']}",
        f"- Data: `{report['data']['file']}`; {report['data']['train_rows']:,} training rows, "
        f"{report['data']['test_rows']:,} test rows (stratified 80/20 split, seed {RANDOM_STATE})",
        f"- Features: {', '.join(FEATURE_COLUMNS)}",
        "- Excluded (leakage/identifiers): BP readings, BP questionnaire and medication "
        "answers, SEQN. SpO2 is not in the dataset and is not a feature.",
        "- Removed on purpose: " + "; ".join(f"{k} ({v})" for k, v in DROPPED_FEATURES.items()),
        f"- Tuning: {CV_FOLDS}-fold stratified CV on the training set only, scored by ROC-AUC.",
        f"- Selection rule: {report['selection_rule']}",
        f"- Decision threshold: {DECISION_THRESHOLD}", "",
        "## Results", "",
        "| Model | CV ROC-AUC (mean ± sd) | Test accuracy | Test precision | Test recall "
        "| Test specificity | Test F1 | Test ROC-AUC | FN | FP |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for _, r in table.iterrows():
        lines.append(
            f"| {r.model} | {r.cv_roc_auc_mean:.3f} ± {r.cv_roc_auc_std:.3f} | "
            f"{r.test_accuracy:.3f} | {r.test_precision:.3f} | {r.test_recall:.3f} | "
            f"{r.test_specificity:.3f} | {r.test_f1:.3f} | {r.test_roc_auc:.3f} | "
            f"{int(r.test_fn)} | {int(r.test_fp)} |")
    if report["unavailable_models"]:
        lines += ["", "Not trained: " + "; ".join(f"{k}: {v}" for k, v in
                                                   report["unavailable_models"].items())]
    lines += ["", "## Selected model", "", f"**{sel}**. {report['selection_rationale']}", "",
              f"Test set: recall {t['recall']:.3f} (found {cm['tp']} of {cm['tp'] + cm['fn']} "
              f"people with hypertension, missed {cm['fn']}), specificity "
              f"{t['specificity']:.3f} ({cm['fp']} false alarms), precision "
              f"{t['precision']:.3f}, ROC-AUC {t['roc_auc']:.3f}.", "",
              f"Adequacy: {report['adequacy']}", "",
              "## Permutation importance (selected model, test set, drop in ROC-AUC)", "",
              "| Feature | Mean | SD |", "|---|---|---|"]
    for f, v in report["feature_importance"].items():
        lines.append(f"| {f} | {v['mean']:.4f} | {v['std']:.4f} |")
    lines += ["", "Academic prototype only: not clinically validated and not a diagnostic tool."]
    (REPORTS_DIR / "model_evaluation.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    X, y = load_features_and_target()
    if list(X.columns) != FEATURE_COLUMNS or set(X.columns) & set(LEAKAGE_COLUMNS):
        sys.exit("Feature columns do not match the approved, leakage-free feature list.")
    X_train, X_test, y_train, y_test = split_train_test(X, y)
    print(f"Train rows: {len(X_train):,}  Test rows: {len(X_test):,}  "
          f"Train class counts: {y_train.value_counts().sort_index().to_dict()}")

    candidates, unavailable = get_candidates()
    for name, reason in unavailable.items():
        print(f"[skip] {name}: {reason}")
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    results, fitted = {}, {}
    for name, (pipeline, grid) in candidates.items():
        n_settings = int(np.prod([len(v) for v in grid.values()]))
        print(f"\n--- {name}: tuning {n_settings} settings x {CV_FOLDS} folds")
        search = GridSearchCV(pipeline, grid, scoring=CV_METRICS, refit="roc_auc", cv=cv,
                              n_jobs=-1, error_score="raise")
        search.fit(X_train, y_train)  # training data only
        i = search.best_index_
        cv_summary = {}
        for m in CV_METRICS:
            cv_summary[f"{m}_mean"] = float(search.cv_results_[f"mean_test_{m}"][i])
            cv_summary[f"{m}_std"] = float(search.cv_results_[f"std_test_{m}"][i])
        model = search.best_estimator_
        fitted[name] = model
        results[name] = {"best_params": {k.replace("classifier__", ""): v
                                         for k, v in search.best_params_.items()},
                         "cv": cv_summary, "test": test_metrics(model, X_test, y_test)}
        r = results[name]
        print(f"best {r['best_params']}  CV AUC {cv_summary['roc_auc_mean']:.3f}  "
              f"| test AUC {r['test']['roc_auc']:.3f} recall {r['test']['recall']:.3f} "
              f"precision {r['test']['precision']:.3f} F1 {r['test']['f1']:.3f}")

    selected, rationale = select_model(results)
    sel_test = results[selected]["test"]
    adequacy = ("Adequate for an educational prototype (test ROC-AUC "
                f"{sel_test['roc_auc']:.3f} >= {MIN_ACCEPTABLE_AUC}), but moderate: it is a "
                "screening-style risk estimate from demographics and body size, not a diagnosis."
                if sel_test["roc_auc"] >= MIN_ACCEPTABLE_AUC else
                f"NOT adequate: test ROC-AUC {sel_test['roc_auc']:.3f} is below "
                f"{MIN_ACCEPTABLE_AUC}. Do not present this model as useful.")
    print(f"\nSelected: {selected}. {rationale}\n{adequacy}")

    # Reports and figures.
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, r in results.items():
        row = {"model": name, "selected": name == selected,
               "best_params": json.dumps(r["best_params"])}
        row.update({f"cv_{k}": round(v, 4) for k, v in r["cv"].items()})
        row.update({f"test_{k}": round(r["test"][k], 4) for k in
                    ["accuracy", "precision", "recall", "specificity", "f1", "roc_auc"]})
        row.update({f"test_{k}": v for k, v in r["test"]["confusion_matrix"].items()})
        rows.append(row)
    table = pd.DataFrame(rows)
    table.to_csv(REPORTS_DIR / "model_comparison.csv", index=False)

    plot_roc(results, y_test)
    plot_confusion_matrices(results)
    plot_comparison(table)
    importance = plot_importance(fitted[selected], X_test, y_test, selected)
    plot_threshold_tradeoff(y_test.to_numpy(), sel_test["_proba"], selected)

    versions = {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                "pandas": pd.__version__, "numpy": np.__version__, "joblib": joblib.__version__}
    for r in results.values():
        r["test"].pop("_proba")
    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data": {"file": "data/processed/hypertension_clean.csv", "train_rows": len(X_train),
                 "test_rows": len(X_test), "test_size": TEST_SIZE, "random_state": RANDOM_STATE,
                 "cv_folds": CV_FOLDS},
        "target": {"column": TARGET_COLUMN, "labels": TARGET_LABELS,
                   "definition": "1 if mean BP >= 130/80 mmHg or taking prescribed BP "
                                 "medication (NCHS Data Brief 511), else 0"},
        "features": FEATURE_COLUMNS, "excluded_leakage_columns": sorted(LEAKAGE_COLUMNS),
        "selection_rule": f"Highest mean CV ROC-AUC on training data; models within "
                          f"{AUC_TIE_MARGIN} are treated as tied and the simplest is chosen.",
        "decision_threshold": DECISION_THRESHOLD,
        "models": results, "unavailable_models": unavailable,
        "selected_model": selected, "selection_rationale": rationale, "adequacy": adequacy,
        "feature_importance": importance, "versions": versions,
    }
    (REPORTS_DIR / "model_evaluation.json").write_text(
        json.dumps(report, indent=2, default=float), encoding="utf-8")
    write_markdown(report, table)

    # Deployable artifact: the selected pipeline (preprocessing + model), fitted on the
    # training split only. It holds fitted parameters, not the training or test data.
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(fitted[selected], MODEL_PATH)
    schema = {
        "schema_version": SCHEMA_VERSION,
        "model_name": selected,
        "target_column": TARGET_COLUMN,
        "target_labels": {str(k): v for k, v in TARGET_LABELS.items()},
        "feature_columns": FEATURE_COLUMNS,
        "numeric_columns": NUMERIC_FEATURES,
        "categorical_columns": CATEGORICAL_FEATURES,
        "categorical_options": {c: sorted(X_train[c].dropna().unique().tolist())
                                for c in CATEGORICAL_FEATURES},
        "numeric_inputs": NUMERIC_INPUTS,
        "classes": [0, 1],
        "decision_threshold": DECISION_THRESHOLD,
        "excluded_leakage_columns": sorted(LEAKAGE_COLUMNS),
        "dropped_features": DROPPED_FEATURES,
        "not_model_inputs": {"SpO2": "Not measured in NHANES 2021-2023; display only."},
        "test_metrics": {k: round(sel_test[k], 4) for k in
                         ["accuracy", "precision", "recall", "specificity", "f1", "roc_auc"]},
        "train_rows": len(X_train), "test_rows": len(X_test),
        "versions": versions, "trained_utc": report["generated_utc"],
        "note": "Academic prototype trained on NHANES 2021-2023. SpO2 is not a model input. "
                "Not clinically validated; not a diagnostic tool.",
    }
    SCHEMA_PATH.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved model: {MODEL_PATH}\nSaved schema: {SCHEMA_PATH}\n"
          f"Reports: {REPORTS_DIR}\nFigures: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
