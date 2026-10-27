# HyperPredict
## Hypertension Risk Prediction Using Machine Learning

HyperPredict is an academic machine-learning project exploring hypertension-risk classification using health survey data from the U.S. CDC National Health and Nutrition Examination Survey (NHANES), cycle August 2021 – August 2023.

> **Dataset status:** The data-preparation pipeline is implemented and validated (31/31 checks pass). It produces 6,081 adults with a CDC-defined hypertension target, 3,242 positive and 2,839 negative. **SpO₂ is not available in NHANES 2021–2023 and is not a model input.** Full details, decisions and limitations: [docs/DATASET.md](docs/DATASET.md). Awaiting team/instructor review before model training.

> **Academic prototype only:** This project is not a medical device and must not be used for diagnosis, treatment, or personal medical decisions. Predictions are experimental and depend on data quality and target definition.

## Project goals
- Select and document an appropriate, publicly documented dataset.
- Inspect data quality, missingness, distributions, and participant counts.
- Build a reproducible preprocessing and training workflow.
- Evaluate classification models using appropriate metrics, including per-class precision/recall and a confusion matrix.
- Provide an educational Streamlit interface for model outputs.
- Explore an optional sensor demonstration for pulse and SpO₂, keeping sensor readings separate from model inputs unless suitable training data is available.

## Dataset: NHANES August 2021 – August 2023
Official source: https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023

**Files:**
- DEMO_L: demographics
- BPXO_L: blood pressure and cuff pulse
- BPQ_L: BP questionnaire
- BMX_L: body measures

The files are merged on `SEQN`.

**Target:** `Hypertension_Status` = 1 if mean BP ≥ 130/80 mmHg or the person takes prescribed BP medication, else 0. This reproduces NCHS Data Brief 511.

**Features:**
- Age_Years
- Sex
- Race_Ethnicity
- BMI
- Waist_Circumference_cm
- Pulse_BPM
- Poverty_Income_Ratio

Blood-pressure readings and questionnaire answers define the target, so they are **excluded from the predictors** to prevent leakage.

See [docs/DATASET.md](docs/DATASET.md) for:
- merge strategy
- exclusions and row counts
- EDA findings
- limitations

Raw and processed data stay local (gitignored). Anyone can regenerate them from the official CDC files with the pipeline below.

## Repository structure
```text
HyperPredict/
├── app/                    # Streamlit prototype
├── data/
│   ├── raw/                # Local source files; not committed
│   └── processed/          # Generated data; not committed
├── data_analysis/          # Data checks, EDA, preprocessing
├── machine_learning/       # Training and evaluation scripts
├── iot/                    # Optional sensor demonstration
├── results/figures/        # Generated charts; commit selected report-ready figures only
├── results/reports/        # Generated pipeline reports (aggregate statistics only)
├── docs/                   # Dataset notes and project documentation
├── TASKS.md                # Team task tracker
├── requirements.txt
└── README.md
```

## Setup
Use Python 3.10 or later.

```bash
python -m venv .venv
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Build the dataset (downloads the CDC files, merges, cleans, runs EDA and validation):
```bash
python data_analysis/run_pipeline.py
```
Outputs:
- `data/processed/hypertension_clean.csv`: the model-ready file
- `results/figures/`: EDA charts
- `results/reports/`: merge, cleaning, EDA and validation reports

Model training (`machine_learning/evaluate.py`, then `machine_learning/train.py`) is the next stage. Do not run it until the dataset has been reviewed.

## Team workflow
- Track ownership, status, and deliverables in [TASKS.md](TASKS.md).
- Use GitHub Issues for individual work items and pull requests for substantial changes when practical.
- Do not mark work complete until its output has been checked.
- Never commit API keys, credentials, private data, or unapproved raw datasets.

## Technologies
Python, pandas, NumPy, scikit-learn, Matplotlib, seaborn, joblib, and Streamlit. The optional IoT demonstration may use an ESP32/Arduino board with a MAX30102 sensor.

## Team
Three team members:
- **Sara Alshaye** — [@SaraMAlshaye](https://github.com/SaraMAlshaye)
- **Mashael Almojally** — [@mashaelalmojally](https://github.com/mashaelalmojally)
- **Sara Aldayel** — [@saaraaldayel](https://github.com/saaraaldayel)

## Disclaimer
This software is an educational prototype. It has not been clinically validated, and no prediction should replace assessment by a qualified healthcare professional.
