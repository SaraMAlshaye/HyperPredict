"""Basic exploratory data analysis for the HyperPredict CSV dataset."""
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw" / "hypertension.csv"
FIGURES_DIR = ROOT / "results" / "figures"
TARGET_COLUMN = "Hypertension_Status"


def main() -> None:
    if not DATA_PATH.exists():
        sys.exit(
            f"Dataset not found: {DATA_PATH}\n"
            "Place your instructor-approved CSV there and confirm the filename."
        )

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH)

    print("\n=== Dataset overview ===")
    print(f"Shape: {df.shape}")
    print("\nColumn types:")
    print(df.dtypes.to_string())
    print("\nMissing values per column:")
    print(df.isna().sum().sort_values(ascending=False).to_string())
    print(f"\nDuplicate rows: {df.duplicated().sum()}")

    numeric = df.select_dtypes(include="number")
    if not numeric.empty:
        print("\n=== Numeric summary ===")
        print(numeric.describe().round(2).to_string())

    if TARGET_COLUMN in df.columns:
        print("\n=== Target distribution ===")
        print(df[TARGET_COLUMN].value_counts(dropna=False).to_string())
        plt.figure(figsize=(9, 5))
        order = df[TARGET_COLUMN].astype(str).value_counts().index
        sns.countplot(data=df, x=TARGET_COLUMN, order=order)
        plt.title("Hypertension status distribution")
        plt.xlabel(TARGET_COLUMN)
        plt.ylabel("Records")
        plt.xticks(rotation=25, ha="right")
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "target_distribution.png", dpi=160)
        plt.close()
    else:
        print(f"\nWARNING: target column {TARGET_COLUMN!r} not found.")

    if len(numeric.columns) >= 2:
        plt.figure(figsize=(10, 8))
        sns.heatmap(numeric.corr(), annot=True, fmt=".2f", cmap="coolwarm", center=0)
        plt.title("Numeric feature correlation")
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "numeric_correlation.png", dpi=160)
        plt.close()

    print(f"\nEDA figures saved in: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
