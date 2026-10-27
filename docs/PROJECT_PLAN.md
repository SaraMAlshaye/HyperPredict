# HyperPredict implementation plan

## Suggested work sequence
1. Dataset verification (done, awaiting review): NHANES 2021–2023. See docs/DATASET.md for source, variables and target-label rules. Instructor approval is still needed.
2. Data pipeline (done, awaiting review): run python data_analysis/run_pipeline.py. It downloads, merges, cleans, runs EDA and validates the data. Review results/reports/ and results/figures/.
3. Preprocessing for modeling: machine_learning/features.py defines the shared imputation, scaling and encoding. It is fitted on the training split only, inside the model Pipeline.
4. Leakage review (done): Hypertension_Status is derived from measured BP and BP medication. All BP readings and BP questionnaire answers are excluded from the predictors (docs/DATASET.md §5).
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
