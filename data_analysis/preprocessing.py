"""Clean the merged NHANES data, build the target, and write model-ready files.

Outputs
- data/processed/hypertension_analysis.csv : one row per included adult, with SEQN,
  survey design variables, BP readings, target components, features and target.
  For auditing and EDA only; never used as model input.
- data/processed/hypertension_clean.csv    : model-ready file = FEATURE_COLUMNS +
  Hypertension_Status only (no identifiers, no BP, no questionnaire answers).
- results/reports/cleaning_report.json     : counts for every exclusion/transformation.

Target (reproduces NCHS Data Brief 511, 2017 ACC/AHA definition):
  Hypertension_Status = 1 if mean SBP >= 130 or mean DBP >= 80 mmHg,
                          or currently taking prescribed BP medication (BPQ150 = 1)
  Hypertension_Status = 0 if mean SBP < 130 and mean DBP < 80 and medication status
                          is known to be "no" (BPQ150 = 2, or BPQ020 = 2 meaning the
                          person was never told they had high BP and so was not asked).
  Excluded             if BP is normal but medication status is unknown
                          (refused/don't know/missing): we cannot call them healthy.
Imputation and scaling are NOT done here; they are fitted on the training split only
(see machine_learning/features.py).
"""
import json
import sys

import numpy as np
import pandas as pd

from nhanes_config import (
    ANALYSIS_PATH, BMI_RANGE, CLEAN_PATH, DBP_RANGE, DBP_THRESHOLD, FEATURE_COLUMNS,
    MERGED_PATH, MIN_AGE, NUMERIC_FEATURES, PULSE_RANGE, RACE_LABELS, REPORTS_DIR,
    SBP_RANGE, SBP_THRESHOLD, SEX_LABELS, TARGET_COLUMN, WAIST_RANGE,
)

SBP_COLS = ["BPXOSY1", "BPXOSY2", "BPXOSY3"]
DBP_COLS = ["BPXODI1", "BPXODI2", "BPXODI3"]
PULSE_COLS = ["BPXOPLS1", "BPXOPLS2", "BPXOPLS3"]


class StepLog:
    """Records row counts so every exclusion is reported."""

    def __init__(self, df: pd.DataFrame):
        self.rows = [{"step": "Merged NHANES participants", "rows": len(df), "removed": 0}]

    def filter(self, df: pd.DataFrame, mask: pd.Series, step: str) -> pd.DataFrame:
        kept = df[mask].copy()
        self.rows.append({"step": step, "rows": len(kept), "removed": len(df) - len(kept)})
        print(f"{step}: removed {len(df) - len(kept):,}, remaining {len(kept):,}")
        return kept


def null_out_of_range(df: pd.DataFrame, cols: list, bounds: tuple, report: dict) -> None:
    """Set physiologically implausible values to NaN (the row is kept)."""
    low, high = bounds
    for col in cols:
        bad = df[col].notna() & ~df[col].between(low, high)
        report[col] = {"bounds": [low, high], "values_set_to_missing": int(bad.sum())}
        df.loc[bad, col] = np.nan


def medication_status(df: pd.DataFrame) -> pd.Series:
    """1 = taking BP medication, 0 = not taking, NaN = unknown."""
    meds = pd.Series(np.nan, index=df.index)
    meds[df["BPQ150"] == 2] = 0
    meds[df["BPQ020"] == 2] = 0  # never told high BP -> BPQ150 not asked (skip pattern)
    meds[df["BPQ150"] == 1] = 1
    return meds


def told_high_bp(df: pd.DataFrame) -> pd.Series:
    """Previously diagnosed (self-reported): 1 yes, 0 no, NaN refused/don't know/missing."""
    return df["BPQ020"].map({1: 1, 2: 0})


def main() -> None:
    if not MERGED_PATH.exists():
        sys.exit(f"Missing {MERGED_PATH}. Run: python data_analysis/merge_nhanes.py")
    df = pd.read_csv(MERGED_PATH)
    log = StepLog(df)
    report = {"plausibility_rules": {}}

    # 1. Inclusion criteria (same population as NCHS Data Brief 511).
    df = log.filter(df, df["RIDSTATR"] == 2, "Keep MEC-examined participants (RIDSTATR = 2)")
    df = log.filter(df, df["RIDAGEYR"] >= MIN_AGE, f"Keep adults aged {MIN_AGE}+")
    df = log.filter(df, df["RIDEXPRG"] != 1, "Exclude pregnant at exam (RIDEXPRG = 1)")

    # 2. Plausibility checks on single measurements.
    rules = report["plausibility_rules"]
    null_out_of_range(df, SBP_COLS, SBP_RANGE, rules)
    null_out_of_range(df, DBP_COLS, DBP_RANGE, rules)
    null_out_of_range(df, PULSE_COLS, PULSE_RANGE, rules)
    null_out_of_range(df, ["BMXBMI"], BMI_RANGE, rules)
    null_out_of_range(df, ["BMXWAIST"], WAIST_RANGE, rules)
    for i in range(3):  # a reading pair where DBP >= SBP is invalid
        bad = df[DBP_COLS[i]] >= df[SBP_COLS[i]]
        rules[f"reading_{i + 1}_DBP_ge_SBP"] = int(bad.sum())
        df.loc[bad, [SBP_COLS[i], DBP_COLS[i]]] = np.nan

    # 3. Blood pressure summary: mean of up to 3 valid readings (as in NCHS code).
    df["Mean_Systolic_BP"] = df[SBP_COLS].mean(axis=1)
    df["Mean_Diastolic_BP"] = df[DBP_COLS].mean(axis=1)
    df["N_BP_Readings"] = df[SBP_COLS].notna().sum(axis=1)
    has_bp = df["Mean_Systolic_BP"].notna() & df["Mean_Diastolic_BP"].notna()
    df = log.filter(df, has_bp, "Keep participants with >=1 valid SBP and DBP reading")

    # 4. Target components (kept separate so measured vs diagnosed can be compared).
    df["BP_Elevated"] = ((df["Mean_Systolic_BP"] >= SBP_THRESHOLD) |
                         (df["Mean_Diastolic_BP"] >= DBP_THRESHOLD)).astype(int)
    df["Told_High_BP"] = told_high_bp(df)
    df["Told_High_BP_2Plus"] = df["BPQ030"].map({1: 1, 2: 0})
    df["Taking_BP_Medication"] = medication_status(df)

    target = pd.Series(np.nan, index=df.index)
    target[(df["BP_Elevated"] == 0) & (df["Taking_BP_Medication"] == 0)] = 0
    target[(df["BP_Elevated"] == 1) | (df["Taking_BP_Medication"] == 1)] = 1
    df[TARGET_COLUMN] = target
    # The NCHS code would label the unknown-medication rows 0; we exclude them instead.
    report["nchs_vs_project_label_difference"] = int(target.isna().sum())
    df = log.filter(df, target.notna(),
                    "Exclude normal BP with unknown medication status (label undeterminable)")
    df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(int)

    # 5. Features with consistent names and readable categories.
    df["Age_Years"] = df["RIDAGEYR"].astype(int)  # NHANES top-codes 80+ as 80
    df["Sex"] = df["RIAGENDR"].map(SEX_LABELS)
    df["Race_Ethnicity"] = df["RIDRETH3"].map(RACE_LABELS)
    df["BMI"] = df["BMXBMI"]
    df["Waist_Circumference_cm"] = df["BMXWAIST"]
    df["Height_cm"] = df["BMXHT"]
    df["Weight_kg"] = df["BMXWT"]
    df["Pulse_BPM"] = df[PULSE_COLS].mean(axis=1)  # mean of valid cuff pulse readings
    df["Poverty_Income_Ratio"] = df["INDFMPIR"]    # top-coded at 5.0
    if df["Sex"].isna().any() or df["Race_Ethnicity"].isna().any():
        sys.exit("Unmapped Sex or Race_Ethnicity code found.")

    # 6. Duplicate checks.
    report["duplicate_SEQN"] = int(df["SEQN"].duplicated().sum())
    report["identical_feature_and_target_rows"] = int(
        df[FEATURE_COLUMNS + [TARGET_COLUMN]].duplicated().sum())
    if report["duplicate_SEQN"]:
        sys.exit("Duplicate participants found after cleaning.")

    # 7. Outlier review (IQR rule). Plausible values are retained, only counted.
    outliers = {}
    for col in NUMERIC_FEATURES:
        q1, q3 = df[col].quantile([0.25, 0.75])
        iqr = q3 - q1
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers[col] = {"iqr_low": round(low, 2), "iqr_high": round(high, 2),
                         "n_outside": int((~df[col].between(low, high) & df[col].notna()).sum()),
                         "min": float(df[col].min()), "max": float(df[col].max())}
    report["iqr_outliers_retained"] = outliers

    # 8. Missing values left for the training pipeline to impute (fitted on train only).
    report["feature_missing_counts"] = {c: int(df[c].isna().sum()) for c in FEATURE_COLUMNS}

    # 9. Class balance, unweighted and survey-weighted.
    counts = df[TARGET_COLUMN].value_counts().sort_index()
    weighted = float(np.average(df[TARGET_COLUMN], weights=df["WTMEC2YR"]))
    report["class_counts"] = {str(k): int(v) for k, v in counts.items()}
    report["prevalence_unweighted"] = round(float(df[TARGET_COLUMN].mean()), 4)
    report["prevalence_weighted_WTMEC2YR"] = round(weighted, 4)
    report["reference_NCHS_DB511"] = {"n_adults": 6084, "weighted_prevalence": 0.477}
    report["row_log"] = log.rows

    analysis_cols = (["SEQN", "WTMEC2YR", "SDMVPSU", "SDMVSTRA"] + SBP_COLS + DBP_COLS +
                     PULSE_COLS + ["Mean_Systolic_BP", "Mean_Diastolic_BP", "N_BP_Readings",
                                   "BP_Elevated", "Told_High_BP", "Told_High_BP_2Plus",
                                   "Taking_BP_Medication", "Height_cm", "Weight_kg"] +
                     FEATURE_COLUMNS + [TARGET_COLUMN])
    ANALYSIS_PATH.parent.mkdir(parents=True, exist_ok=True)
    df[analysis_cols].to_csv(ANALYSIS_PATH, index=False)
    df[FEATURE_COLUMNS + [TARGET_COLUMN]].to_csv(CLEAN_PATH, index=False)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "cleaning_report.json").write_text(json.dumps(report, indent=2),
                                                     encoding="utf-8")
    print(f"\nFinal adults: {len(df):,}; class counts {report['class_counts']}")
    print(f"Prevalence: unweighted {report['prevalence_unweighted']:.1%}, "
          f"survey-weighted {weighted:.1%} (NCHS DB511 reports 47.7%)")
    print(f"Analysis file: {ANALYSIS_PATH}\nModel-ready file: {CLEAN_PATH}")


if __name__ == "__main__":
    main()
