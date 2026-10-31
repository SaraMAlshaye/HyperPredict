"""Reproducible exploratory data analysis for the cleaned NHANES hypertension data.

Reads data/processed/hypertension_analysis.csv (written by preprocessing.py) and
writes charts to results/figures/ plus a text summary to results/reports/eda_summary.md.
All statistics are unweighted sample statistics unless labeled "survey-weighted".
"""
import sys

import matplotlib
matplotlib.use("Agg")  # no display needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from nhanes_config import (
    ANALYSIS_PATH, CATEGORICAL_FEATURES, DBP_THRESHOLD, FEATURE_COLUMNS, FIGURES_DIR,
    NUMERIC_FEATURES, REPORTS_DIR, SBP_THRESHOLD, TARGET_COLUMN,
)

CLASS_NAMES = {0: "No hypertension", 1: "Hypertension"}
PALETTE = {"No hypertension": "#4C72B0", "Hypertension": "#C44E52"}
UNITS = {"Age_Years": "years", "BMI": "kg/m²",
         "Pulse_BPM": "beats/min", "Poverty_Income_Ratio": "ratio (top-coded at 5)"}


def save(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / name, dpi=150)
    plt.close(fig)
    print(f"  saved {name}")


def plot_target(df):
    counts = df["Class"].value_counts().reindex(CLASS_NAMES.values())
    fig, ax = plt.subplots(figsize=(6, 4.5))
    bars = ax.bar(counts.index, counts.values, color=[PALETTE[c] for c in counts.index])
    for bar, n in zip(bars, counts.values):
        ax.annotate(f"{n:,}\n({n / len(df):.1%})", (bar.get_x() + bar.get_width() / 2, n),
                    ha="center", va="bottom")
    ax.set_ylim(0, counts.max() * 1.2)
    ax.set_title("Target class distribution (adults 18+, unweighted)")
    ax.set_ylabel("Participants")
    save(fig, "target_distribution.png")


def plot_missing(df):
    miss = df[FEATURE_COLUMNS].isna().mean().mul(100).sort_values()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(miss.index, miss.values, color="#8172B2")
    for y, v in enumerate(miss.values):
        ax.text(v + 0.2, y, f"{v:.1f}%", va="center")
    ax.set_xlabel("Missing (%)")
    ax.set_xlim(0, max(miss.max() * 1.3, 5))
    ax.set_title("Missing values per model feature (before imputation)")
    save(fig, "missing_values.png")


def plot_distributions(df):
    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    for ax, col in zip(axes.flat, NUMERIC_FEATURES):
        sns.histplot(data=df, x=col, hue="Class", palette=PALETTE, stat="density",
                     common_norm=False, element="step", bins=40, ax=ax)
        ax.set_xlabel(f"{col} ({UNITS[col]})")
    for ax in list(axes.flat)[len(NUMERIC_FEATURES):]:
        ax.axis("off")
    fig.suptitle("Numeric feature distributions by class (density, each class normalised)")
    save(fig, "feature_distributions.png")


def plot_boxplots(df):
    fig, axes = plt.subplots(1, len(NUMERIC_FEATURES), figsize=(16, 4.5))
    for ax, col in zip(axes, NUMERIC_FEATURES):
        sns.boxplot(data=df, x="Class", y=col, hue="Class", palette=PALETTE,
                    legend=False, ax=ax, fliersize=2)
        ax.set_xlabel("")
        ax.set_ylabel(f"{col} ({UNITS[col]})")
        ax.tick_params(axis="x", rotation=20)
    fig.suptitle("Outlier check: boxplots by class (points = beyond 1.5×IQR, retained)")
    save(fig, "outlier_boxplots.png")


def plot_categorical(df):
    df = df.assign(Age_Group=pd.cut(df["Age_Years"], [17, 29, 39, 49, 59, 69, 80],
                                    labels=["18-29", "30-39", "40-49", "50-59",
                                            "60-69", "70-80+"]))
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), gridspec_kw={"width_ratios": [3, 1, 3]})
    for ax, col in zip(axes, ["Age_Group", "Sex", "Race_Ethnicity"]):
        rate = df.groupby(col, observed=True)[TARGET_COLUMN].agg(["mean", "size"])
        ax.bar(rate.index.astype(str), rate["mean"] * 100, color="#C44E52")
        for x, (m, n) in enumerate(zip(rate["mean"], rate["size"])):
            ax.text(x, m * 100 + 1, f"{m:.0%}\nn={n}", ha="center", fontsize=8)
        ax.set_ylim(0, 105)
        ax.set_ylabel("Hypertension (%)")
        ax.set_title(col.replace("_", " "))
        ax.tick_params(axis="x", rotation=30)
    fig.suptitle("Hypertension prevalence by group (unweighted)")
    save(fig, "prevalence_by_group.png")


def plot_correlation(df):
    cols = NUMERIC_FEATURES + [TARGET_COLUMN]
    corr = df[cols].corr(method="spearman")
    fig, ax = plt.subplots(figsize=(7.5, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, vmin=-1, vmax=1,
                square=True, ax=ax)
    ax.set_title("Spearman correlation: numeric features and target")
    save(fig, "correlation_heatmap.png")
    return corr


def plot_bp_definition(df):
    fig, ax = plt.subplots(figsize=(7, 5.5))
    sns.scatterplot(data=df, x="Mean_Systolic_BP", y="Mean_Diastolic_BP", hue="Class",
                    palette=PALETTE, s=8, alpha=0.5, ax=ax, linewidth=0)
    ax.axvline(SBP_THRESHOLD, color="black", ls="--", lw=1)
    ax.axhline(DBP_THRESHOLD, color="black", ls="--", lw=1)
    ax.set_xlabel("Mean systolic BP (mmHg)")
    ax.set_ylabel("Mean diastolic BP (mmHg)")
    ax.set_title("Target definition check: BP thresholds 130/80\n"
                 "(BP defines the target — NOT a model input; red below lines = on medication)")
    save(fig, "bp_target_definition.png")


def plot_measured_vs_diagnosed(df):
    told = df["Told_High_BP"].map({1: "Told high BP", 0: "Never told"}).fillna("Unknown")
    groups = pd.crosstab(told, [df["BP_Elevated"].map({1: "BP ≥130/80", 0: "BP <130/80"})])
    fig, ax = plt.subplots(figsize=(7, 4.5))
    groups.plot(kind="bar", ax=ax, color=["#4C72B0", "#C44E52"], rot=0)
    for container in ax.containers:
        ax.bar_label(container, fmt="{:,.0f}")
    ax.set_xlabel("Previously diagnosed (BPQ020)")
    ax.set_ylabel("Participants")
    ax.set_title("Measured high BP vs previous diagnosis")
    ax.legend(title="Measured at exam")
    save(fig, "measured_vs_diagnosed.png")


def markdown_table(frame: pd.DataFrame) -> str:
    frame = frame.reset_index()
    lines = ["| " + " | ".join(map(str, frame.columns)) + " |",
             "|" + "---|" * len(frame.columns)]
    lines += ["| " + " | ".join(map(str, row)) + " |" for row in frame.itertuples(index=False)]
    return "\n".join(lines)


def main() -> None:
    if not ANALYSIS_PATH.exists():
        sys.exit(f"Missing {ANALYSIS_PATH}. Run: python data_analysis/preprocessing.py")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ANALYSIS_PATH)
    df["Class"] = df[TARGET_COLUMN].map(CLASS_NAMES)
    model_df = df[FEATURE_COLUMNS + [TARGET_COLUMN]]

    print(f"Shape (model-ready columns): {model_df.shape}")
    print(model_df.dtypes.to_string())
    print("\nGenerating figures:")
    plot_target(df)
    plot_missing(df)
    plot_distributions(df)
    plot_boxplots(df)
    plot_categorical(df)
    corr = plot_correlation(df)
    plot_bp_definition(df)
    plot_measured_vs_diagnosed(df)

    desc = model_df[NUMERIC_FEATURES].describe().T.round(2)
    by_class = df.groupby("Class")[NUMERIC_FEATURES].median().T.round(1)
    weighted = np.average(df[TARGET_COLUMN], weights=df["WTMEC2YR"])
    undiagnosed = int(((df["BP_Elevated"] == 1) & (df["Told_High_BP"] == 0)).sum())
    on_meds_normal = int(((df["BP_Elevated"] == 0) & (df["Taking_BP_Medication"] == 1)).sum())

    lines = [
        "# EDA summary (generated by data_analysis/eda.py)", "",
        f"- Model-ready shape: {model_df.shape[0]:,} rows x {model_df.shape[1]} columns",
        f"- Class counts: {df[TARGET_COLUMN].value_counts().sort_index().to_dict()} "
        f"(unweighted prevalence {df[TARGET_COLUMN].mean():.1%}; survey-weighted {weighted:.1%})",
        f"- Meet BP threshold but never told they had high BP: {undiagnosed:,}",
        f"- Labelled hypertensive only because of BP medication (BP < 130/80): {on_meds_normal:,}",
        "", "## Data types", "", markdown_table(model_df.dtypes.astype(str).to_frame("dtype")),
        "", "## Missing values (before imputation)", "",
        markdown_table(model_df.isna().sum().to_frame("missing")),
        "", "## Descriptive statistics", "", markdown_table(desc),
        "", "## Median by class", "", markdown_table(by_class),
        "", "## Spearman correlation with target", "",
        markdown_table(corr[TARGET_COLUMN].drop(TARGET_COLUMN).round(3).to_frame("rho")),
        "", "## Categorical features (count, % hypertension)", "",
    ]
    for col in CATEGORICAL_FEATURES:
        tab = df.groupby(col)[TARGET_COLUMN].agg(n="size", pct_hypertension="mean")
        tab["pct_hypertension"] = (tab["pct_hypertension"] * 100).round(1)
        lines += [markdown_table(tab), ""]
    (REPORTS_DIR / "eda_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nEDA summary written to {REPORTS_DIR / 'eda_summary.md'}")


if __name__ == "__main__":
    main()
