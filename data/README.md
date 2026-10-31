# Dataset instructions

The dataset is built automatically from the official CDC NHANES August 2021 – August 2023 public files:

```bash
python data_analysis/run_pipeline.py
```

| Folder | Contents | In Git? |
|---|---|---|
| `data/raw/` | `DEMO_L.xpt`, `BPXO_L.xpt`, `BPQ_L.xpt`, `BMX_L.xpt`, downloaded unchanged from CDC | No |
| `data/processed/` | `nhanes_merged.csv`, `hypertension_analysis.csv` (audit/EDA, includes SEQN and BP), `hypertension_clean.csv` (model-ready: 6 features + `Hypertension_Status`) | No |

The model scripts read only `hypertension_clean.csv`. It contains no identifiers, blood-pressure readings or questionnaire answers, because those define the target (see [docs/DATASET.md](../docs/DATASET.md)).

Keep raw and processed data out of Git (enforced by `.gitignore`). NHANES public-use data must not be used to try to identify participants.
