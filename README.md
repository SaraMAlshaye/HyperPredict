# HyperPredict
## Hypertension Risk Prediction Using Machine Learning

HyperPredict is an academic machine-learning project exploring hypertension-risk classification using health survey data. The team is evaluating the U.S. CDC National Health and Nutrition Examination Survey (NHANES) as a candidate source because it includes measured blood pressure and pulse data in selected cycles.

> **Dataset status:** NHANES is a candidate source, not yet the finalized dataset. The team must verify the selected cycle, required variables, availability of oxygen saturation (SpO₂), sample size after merging files, and the definition of the prediction target before model training.

> **Academic prototype only:** This project is not a medical device and must not be used for diagnosis, treatment, or personal medical decisions. Predictions are experimental and depend on data quality and target definition.

## Project goals
- Select and document an appropriate, publicly documented dataset.
- Inspect data quality, missingness, distributions, and participant counts.
- Build a reproducible preprocessing and training workflow.
- Evaluate classification models using appropriate metrics, including per-class precision/recall and a confusion matrix.
- Provide an educational Streamlit interface for model outputs.
- Explore an optional sensor demonstration for pulse and SpO₂, keeping sensor readings separate from model inputs unless suitable training data is available.

## Candidate dataset: NHANES
Official source: https://wwwn.cdc.gov/nchs/nhanes/

The 2021–2023 blood pressure and pulse file (BPXO_L) is an initial candidate:
https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BPXO_L.htm

Before adoption, the team must:
1. Verify all required variables and their units in the selected cycle.
2. Confirm whether a suitable SpO₂ variable is available in that same cycle. Do not assume it is available.
3. Identify the participant identifier (SEQN) and merge related files carefully.
4. Document inclusion/exclusion criteria and missing-data handling.
5. Define the target variable and check for target leakage. If hypertension labels are derived from systolic/diastolic blood-pressure thresholds, using those same measurements as predictors may inflate performance.
6. Review NHANES documentation, survey design considerations, and any applicable data-use requirements.

Do not commit downloaded raw datasets or other large/generated files unless the team has confirmed that this is appropriate. Keep raw and processed data local by default and document how to obtain the source files.

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

Run scripts only after checking their expected paths and column names. The dataset and final target schema have not yet been finalized, so training commands may need updating after the dataset audit.

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
