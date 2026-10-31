# HyperPredict implementation plan

## Suggested work sequence
1. Dataset verification (done, awaiting review): NHANES 2021–2023. See docs/DATASET.md for source, variables and target-label rules. Instructor approval is still needed.
2. Data pipeline (done, awaiting review): run python data_analysis/run_pipeline.py. It downloads, merges, cleans, runs EDA and validates the data. Review results/reports/ and results/figures/.
3. Preprocessing for modeling: machine_learning/features.py defines the shared imputation, scaling and encoding. It is fitted on the training split only, inside the model Pipeline.
4. Leakage review (done): Hypertension_Status is derived from measured BP and BP medication. All BP readings and BP questionnaire answers are excluded from the predictors (docs/DATASET.md §5).
5. Training and model selection (done, awaiting review): run python -m machine_learning.train. It tunes Logistic Regression, Decision Tree and Random Forest with 5-fold CV on the training data, scores them on the held-out test set, selects a model by a pre-set rule, and saves the model, reports and figures. Results: docs/MODEL.md.
6. Artifact check (done): run python -m machine_learning.evaluate. It reloads the saved model and re-checks metrics, the feature schema and missing-input predictions.
7. Interface (done, awaiting review): run streamlit run app/app.py. Input validation was tested with valid, missing and invalid values.
8. Optional hardware:
   - Software side done: serial protocol, connection layer, app sensor panel and tests (python -m pytest).
   - Hardware open: build the wiring, compile and upload the untested firmware template, and follow the bring-up checklist in iot/README.md.
   - SpO2 must never be fed to the model. Using sensor heart rate as the pulse input needs the compatibility study in iot/README.md first.
9. Report (open): write up data provenance, methods, results from docs/MODEL.md, limitations, and ethical considerations.

## Possible improvements (not done)
- Choose a recall-oriented decision threshold using training-set cross-validation (not the test set).
- Try survey-weighted training, and test the 140/90 definition as a sensitivity analysis.

## Before submission
- Confirm dataset approval and usage conditions.
- Do not describe the prototype as clinically validated.
- Do not invent performance numbers; report only results you actually obtain.
- Include limitations from dataset size, target-label definition, class imbalance, and possible leakage.
- Keep private keys, credentials, and raw dataset files out of Git.
