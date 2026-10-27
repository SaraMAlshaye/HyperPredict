# HyperPredict
## Hypertension Risk Prediction Using Machine Learning

HyperPredict is an academic machine-learning project exploring hypertension-status classification from a tabular dataset. It includes data inspection, preprocessing, model training and evaluation, and a Streamlit prototype. An optional IoT component may demonstrate pulse and SpO₂ readings separately.

> **Academic prototype only:** This project is not a medical device and must not be used for diagnosis, treatment, or personal medical decisions. Predictions are experimental and depend on the dataset's quality and label definition.

## Project goals
- Inspect the dataset and document its quality.
- Build a reproducible preprocessing and training workflow.
- Evaluate models with suitable classification metrics, including per-class precision/recall and a confusion matrix.
- Provide a simple educational interface for model outputs.
- Keep optional sensor demonstrations separate from the model unless suitable, documented training data containing those measurements becomes available.

## Dataset
Place the instructor-approved dataset in `data/raw/` and update the path/configuration if needed. The starter scripts expect a CSV file named `hypertension.csv` and a target column named `Hypertension_Status` by default.

The previously explored candidate dataset was reported to have 1,249 records and 14 variables. Verify the source, usage conditions, column names, and label-generation rules before using it in the final report. Do not commit private data or data that the license does not permit redistribution.

**Important validation note:** If `Hypertension_Status` was assigned using systolic or diastolic blood-pressure thresholds, including those same blood-pressure measurements as predictors can create target leakage. Document the label definition and compare models with and without any label-defining features before drawing conclusions.

## Repository structure
```text
HyperPredict/
├── app/                    # Streamlit prototype
├── data/
│   ├── raw/                # Put approved source data here (not committed)
│   └── processed/          # Generated clean data (not committed)
├── data_analysis/          # Data checks, EDA, preprocessing
├── machine_learning/       # Training and evaluation scripts
├── iot/                    # Optional sensor demonstration
├── results/figures/        # Generated charts
├── docs/                   # Project documentation
├── requirements.txt
└── README.md
```

## Setup
Use Python 3.10 or later.

```bash
python -m venv .venv
```

Windows:
```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python data_analysis/eda.py
python data_analysis/preprocessing.py
python machine_learning/train.py
python machine_learning/evaluate.py
streamlit run app/app.py
```

The scripts stop with a clear message when the expected dataset or trained model is missing. Generated files are stored locally and are intentionally excluded from Git.

## Technologies
Python, pandas, NumPy, scikit-learn, Matplotlib, seaborn, joblib, and Streamlit. The optional IoT demo may use an ESP32/Arduino board with a MAX30102 sensor.

## Team
This project is being developed collaboratively by three team members: **Sara Alshaye, Mashael, and Sara**. The team is working on the dataset analysis, machine-learning workflow, evaluation, and educational Streamlit prototype as part of CSC 418 — Machine Learning.

## Disclaimer
This software is an educational prototype. It has not been clinically validated, and no prediction should replace assessment by a qualified healthcare professional.