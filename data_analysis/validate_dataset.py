"""Validate the generated NHANES pipeline outputs. Exits with code 1 if any check fails.

Also fits ONLY the preprocessing step on a training split (no model is trained) to
confirm imputation/encoding work and leave no missing values in the training matrix.
"""
import json
import sys

import numpy as np
import pandas as pd

from nhanes_config import (
    ANALYSIS_PATH, CATEGORICAL_FEATURES, CLEAN_PATH, DROPPED_FEATURES, FEATURE_COLUMNS,
    FIGURES_DIR,
    LEAKAGE_COLUMNS, MERGED_PATH, NUMERIC_FEATURES, RAW_DIR, NHANES_FILES, REPORTS_DIR,
    ROOT, SBP_THRESHOLD, DBP_THRESHOLD, TARGET_COLUMN, MIN_AGE,
)

EXPECTED_FIGURES = ["target_distribution.png", "missing_values.png",
                    "feature_distributions.png", "outlier_boxplots.png",
                    "prevalence_by_group.png", "correlation_heatmap.png",
                    "bp_target_definition.png", "measured_vs_diagnosed.png"]
results = []


def check(name: str, passed: bool, detail: str = "") -> None:
    results.append({"check": name, "passed": bool(passed), "detail": detail})
    print(f"[{'PASS' if passed else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))


def main() -> None:
    for name in NHANES_FILES:
        check(f"raw file {name}.xpt present", (RAW_DIR / f"{name}.xpt").exists())
    for path in [MERGED_PATH, ANALYSIS_PATH, CLEAN_PATH]:
        check(f"output {path.name} present", path.exists())
    if not CLEAN_PATH.exists() or not ANALYSIS_PATH.exists():
        sys.exit("Required outputs missing; run data_analysis/run_pipeline.py")

    merged = pd.read_csv(MERGED_PATH)
    clean = pd.read_csv(CLEAN_PATH)
    analysis = pd.read_csv(ANALYSIS_PATH)

    check("merged file has one row per SEQN", merged["SEQN"].is_unique, f"{len(merged):,} rows")
    check("clean columns = features + target",
          list(clean.columns) == FEATURE_COLUMNS + [TARGET_COLUMN], str(list(clean.columns)))
    check("clean and analysis row counts match", len(clean) == len(analysis), f"{len(clean):,}")
    check("no identifiers or leakage columns in model file",
          not set(clean.columns) & set(LEAKAGE_COLUMNS))
    check("analysis SEQN unique", analysis["SEQN"].is_unique)

    check("numeric features are numeric",
          all(pd.api.types.is_numeric_dtype(clean[c]) for c in NUMERIC_FEATURES))
    check("categorical features are text",
          all(clean[c].dtype == object for c in CATEGORICAL_FEATURES))
    check("target has no missing values", clean[TARGET_COLUMN].notna().all())
    check("target labels are exactly {0, 1}", set(clean[TARGET_COLUMN].unique()) == {0, 1})
    counts = clean[TARGET_COLUMN].value_counts().sort_index().to_dict()
    check("each class has >= 100 rows", min(counts.values()) >= 100, str(counts))
    check("age within adult range", clean["Age_Years"].between(MIN_AGE, 80).all())
    check("no fully duplicated participant rows in analysis file",
          not analysis.duplicated().any())

    # Target must follow the documented rule exactly.
    elevated = ((analysis["Mean_Systolic_BP"] >= SBP_THRESHOLD) |
                (analysis["Mean_Diastolic_BP"] >= DBP_THRESHOLD))
    rule = (elevated | (analysis["Taking_BP_Medication"] == 1)).astype(int)
    check("target matches definition (BP >=130/80 or BP medication)",
          (rule == analysis[TARGET_COLUMN]).all())
    negatives = analysis[analysis[TARGET_COLUMN] == 0]
    check("every negative has known 'not on medication' status",
          (negatives["Taking_BP_Medication"] == 0).all())
    weighted = np.average(analysis[TARGET_COLUMN], weights=analysis["WTMEC2YR"])
    check("survey-weighted prevalence close to NCHS DB511 (47.7%)",
          abs(weighted - 0.477) < 0.01, f"{weighted:.1%}")

    check("dropped features absent from model file",
          not set(DROPPED_FEATURES) & set(clean.columns), str(sorted(DROPPED_FEATURES)))
    for col, (low, high) in {"Pulse_BPM": (30, 220), "BMI": (10, 100)}.items():
        values = clean[col].dropna()
        check(f"{col} within [{low}, {high}]", values.between(low, high).all(),
              f"min {values.min():.1f}, max {values.max():.1f}, missing {clean[col].isna().sum()}")

    # Preprocessing-only fit on a training split (no model training).
    sys.path.insert(0, str(ROOT / "machine_learning"))
    from sklearn.model_selection import train_test_split
    from features import RANDOM_STATE, TEST_SIZE, build_preprocessor
    X, y = clean[FEATURE_COLUMNS], clean[TARGET_COLUMN]
    X_train, X_test, _, _ = train_test_split(X, y, test_size=TEST_SIZE,
                                             random_state=RANDOM_STATE, stratify=y)
    pre = build_preprocessor().fit(X_train)
    Xt_train, Xt_test = pre.transform(X_train), pre.transform(X_test)
    Xt_train = Xt_train.toarray() if hasattr(Xt_train, "toarray") else Xt_train
    Xt_test = Xt_test.toarray() if hasattr(Xt_test, "toarray") else Xt_test
    check("preprocessor (fit on train only) leaves no NaN",
          not np.isnan(Xt_train).any() and not np.isnan(Xt_test).any(),
          f"train {Xt_train.shape}, test {Xt_test.shape}")

    missing_figs = [f for f in EXPECTED_FIGURES if not (FIGURES_DIR / f).exists()]
    check("all EDA figures generated", not missing_figs, str(missing_figs or "8/8"))
    for report in ["merge_log.json", "cleaning_report.json", "eda_summary.md"]:
        check(f"report {report} generated", (REPORTS_DIR / report).exists())

    failed = [r for r in results if not r["passed"]]
    (REPORTS_DIR / "validation_report.json").write_text(
        json.dumps({"passed": len(results) - len(failed), "failed": len(failed),
                    "checks": results}, indent=2), encoding="utf-8")
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed.")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
