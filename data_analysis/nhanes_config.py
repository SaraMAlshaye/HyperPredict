"""Shared settings for the NHANES August 2021-August 2023 data pipeline.

Every step (download, merge, preprocessing, EDA, validation) imports from here so
file names, column names, and cleaning rules are defined in one place.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
FIGURES_DIR = ROOT / "results" / "figures"
REPORTS_DIR = ROOT / "results" / "reports"

CYCLE = "August 2021-August 2023"
BASE_URL = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles"

# Official NHANES files used by the pipeline. Codebooks: f"{BASE_URL}/{name}.htm"
NHANES_FILES = {
    "DEMO_L": "Demographic Variables and Sample Weights",
    "BPXO_L": "Blood Pressure - Oscillometric Measurements",
    "BPQ_L": "Blood Pressure & Cholesterol (questionnaire)",
    "BMX_L": "Body Measures",
}

# Variables kept from each raw file (all verified in the official codebooks).
KEEP_COLUMNS = {
    "DEMO_L": ["SEQN", "RIDSTATR", "RIAGENDR", "RIDAGEYR", "RIDRETH3",
               "RIDEXPRG", "INDFMPIR", "WTMEC2YR", "SDMVPSU", "SDMVSTRA"],
    "BPXO_L": ["SEQN", "BPXOSY1", "BPXODI1", "BPXOSY2", "BPXODI2",
               "BPXOSY3", "BPXODI3", "BPXOPLS1", "BPXOPLS2", "BPXOPLS3"],
    "BPQ_L": ["SEQN", "BPQ020", "BPQ030", "BPQ150"],
    "BMX_L": ["SEQN", "BMXWT", "BMXHT", "BMXBMI", "BMXWAIST"],
}

MERGED_PATH = PROCESSED_DIR / "nhanes_merged.csv"
ANALYSIS_PATH = PROCESSED_DIR / "hypertension_analysis.csv"
CLEAN_PATH = PROCESSED_DIR / "hypertension_clean.csv"

TARGET_COLUMN = "Hypertension_Status"  # 1 = hypertension, 0 = no hypertension

# Hypertension definition reproduced from NCHS Data Brief 511 (2017 ACC/AHA).
SBP_THRESHOLD = 130
DBP_THRESHOLD = 80
MIN_AGE = 18

# Plausibility bounds for single readings. Values outside are treated as
# measurement errors and set to missing (project rule, documented in docs/DATASET.md).
SBP_RANGE = (60, 270)
DBP_RANGE = (30, 150)
PULSE_RANGE = (30, 220)
BMI_RANGE = (10, 100)
WAIST_RANGE = (40, 200)

# Model inputs. Only demographics, body measures, and cuff pulse.
NUMERIC_FEATURES = ["Age_Years", "BMI", "Waist_Circumference_cm",
                    "Pulse_BPM", "Poverty_Income_Ratio"]
CATEGORICAL_FEATURES = ["Sex", "Race_Ethnicity"]
FEATURE_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES

# Never allowed as predictors: they define the target, reveal it, or identify people.
LEAKAGE_COLUMNS = [
    "SEQN",
    "BPXOSY1", "BPXOSY2", "BPXOSY3", "BPXODI1", "BPXODI2", "BPXODI3",
    "Systolic_BP", "Diastolic_BP", "Mean_Systolic_BP", "Mean_Diastolic_BP",
    "N_BP_Readings", "BP_Elevated", "Told_High_BP", "Told_High_BP_2Plus",
    "Taking_BP_Medication", "BPQ020", "BPQ030", "BPQ150",
]

SEX_LABELS = {1: "Male", 2: "Female"}
RACE_LABELS = {
    1: "Mexican American", 2: "Other Hispanic", 3: "Non-Hispanic White",
    4: "Non-Hispanic Black", 6: "Non-Hispanic Asian", 7: "Other/Multi-Racial",
}
