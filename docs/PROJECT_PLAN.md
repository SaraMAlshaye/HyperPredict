# HyperPredict implementation plan

## Suggested work sequence
1. Dataset verification: confirm source, license, column definitions, target-label rules, and instructor approval.
2. Data checks and EDA: run python data_analysis/eda.py; review missing values, duplicates, outliers, class imbalance, and correlations.
3. Preprocessing: run python data_analysis/preprocessing.py; review printed row counts and generated clean data.
4. Leakage review: determine how Hypertension_Status was assigned. Compare a baseline excluding blood-pressure measurements with any justified alternative, and report the limitation clearly.
5. Baseline evaluation: run python machine_learning/evaluate.py for a stratified held-out test evaluation. Record per-class precision, recall, F1, and confusion matrix rather than reporting accuracy alone.
6. Final training: run python machine_learning/train.py to save the prototype model and its input schema.
7. Interface: run streamlit run app/app.py and test valid, unusual, and missing-value cases.
8. Optional hardware: demonstrate pulse/SpO2 separately; do not feed them to the model without appropriate training data.
9. Report: document data provenance, methods, baseline results, limitations, and ethical considerations.

## Before submission
- Confirm dataset approval and usage conditions.
- Do not describe the prototype as clinically validated.
- Do not invent performance numbers; report only results you actually obtain.
- Include limitations from dataset size, target-label definition, class imbalance, and possible leakage.
- Keep private keys, credentials, and raw dataset files out of Git.
