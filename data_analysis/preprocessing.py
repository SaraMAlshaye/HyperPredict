"""Validate and create a cleaned copy of the input dataset."""
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "raw" / "hypertension.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "hypertension_clean.csv"
TARGET_COLUMN = "Hypertension_Status"


def main() -> None:
    if not INPUT_PATH.exists():
        sys.exit(
            f"Dataset not found: {INPUT_PATH}\n"
            "Place your instructor-approved CSV in data/raw/."
        )

    df = pd.read_csv(INPUT_PATH)
    if TARGET_COLUMN not in df.columns:
        sys.exit(
            f"Required target column {TARGET_COLUMN!r} is missing. "
            f"Available columns: {list(df.columns)}"
        )

    before = len(df)
    df = df.drop_duplicates().copy()
    duplicates_removed = before - len(df)

    missing_target = int(df[TARGET_COLUMN].isna().sum())
    df = df.dropna(subset=[TARGET_COLUMN]).copy()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)

    print(f"Rows before cleaning: {before}")
    print(f"Duplicate rows removed: {duplicates_removed}")
    print(f"Rows missing target removed: {missing_target}")
    print(f"Rows after cleaning: {len(df)}")
    print("Missing feature values are left for the model pipeline to impute.")
    print(f"Cleaned dataset saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
