"""Merge the NHANES 2021-2023 files on SEQN into data/processed/nhanes_merged.csv.

Join strategy: DEMO_L is the master list (one row per sampled participant), so the
other files are LEFT-joined onto it. This keeps every participant and makes it
explicit (as missing values) who lacks an exam or questionnaire record. Inclusion
criteria are applied later, in preprocessing.py, where each exclusion is counted.
Raw files in data/raw/ are only read, never modified.
"""
import json
import sys

import pandas as pd

from nhanes_config import KEEP_COLUMNS, MERGED_PATH, RAW_DIR, REPORTS_DIR


def load(name: str) -> pd.DataFrame:
    path = RAW_DIR / f"{name}.xpt"
    if not path.exists():
        sys.exit(f"Missing {path}. Run: python data_analysis/download_nhanes.py")
    df = pd.read_sas(path, format="xport")[KEEP_COLUMNS[name]].copy()
    # pandas reads SAS XPORT zeros as ~5.4e-79; restore them to exact 0.
    df = df.mask(df.abs() < 1e-10, 0.0)
    df["SEQN"] = df["SEQN"].astype("int64")
    if df["SEQN"].duplicated().any():
        sys.exit(f"{name} has duplicate SEQN values; refusing to merge.")
    return df


def main() -> None:
    merged = load("DEMO_L")
    log = [{"step": "DEMO_L (master)", "rows": len(merged), "matched": len(merged)}]
    print(f"DEMO_L: {len(merged):,} participants")

    for name in ["BPXO_L", "BPQ_L", "BMX_L"]:
        other = load(name)
        unmatched = (~other["SEQN"].isin(merged["SEQN"])).sum()
        if unmatched:
            sys.exit(f"{name} has {unmatched} SEQN values not in DEMO_L.")
        before = len(merged)
        # validate="one_to_one" makes pandas raise if any SEQN repeats (no row multiplication).
        merged = merged.merge(other, on="SEQN", how="left", validate="one_to_one")
        if len(merged) != before:
            sys.exit(f"Row count changed after merging {name}: {before} -> {len(merged)}")
        log.append({"step": f"+ {name} (left join)", "rows": len(merged),
                    "matched": int(len(other))})
        print(f"+ {name}: {len(other):,} records matched; merged rows = {len(merged):,}")

    if merged["SEQN"].duplicated().any():
        sys.exit("Duplicate SEQN after merge.")

    MERGED_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(MERGED_PATH, index=False)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "merge_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    print(f"Merged dataset: {merged.shape[0]:,} rows x {merged.shape[1]} columns -> {MERGED_PATH}")


if __name__ == "__main__":
    main()
