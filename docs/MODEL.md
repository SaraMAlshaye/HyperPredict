# HyperPredict model: training, evaluation and selection

> **Academic prototype.** The model is not clinically validated, not a medical device, and not a diagnostic tool. It does not diagnose hypertension or predict future disease. Only a blood-pressure measurement by a qualified professional can show whether someone has hypertension.

All numbers below come from `results/reports/model_evaluation.json`, written by `python -m machine_learning.train`. Rerunning the commands at the end reproduces them exactly, because all random seeds are fixed at 42.

**Current model: version 3 (5 features, 3 candidate models).**

| Version | Features | Change |
|---|---|---|
| 1 | 7 | Included `Poverty_Income_Ratio` and waist circumference |
| 2 | 6 | Income ratio removed (see [below](#why-the-income-ratio-was-removed)) |
| 3 | 5 | Waist circumference removed at the team's request; `BMXWAIST` is no longer loaded. XGBoost was also removed from the candidate models. |

Older models and reports are archived:
- `machine_learning/models/archive/` (local, gitignored)
- `results/reports/archive/`

## Data and target

| Item | Value |
|---|---|
| Source | CDC NHANES August 2021 – August 2023 (see [DATASET.md](DATASET.md)) |
| Rows | 6,081 adults: 3,242 with hypertension, 2,839 without |
| Target | `Hypertension_Status` = 1 if mean BP ≥ 130/80 mmHg or taking prescribed BP medication, else 0 (NCHS Data Brief 511) |

**Features (5)**

| Type | Features |
|---|---|
| Numeric (3) | Age_Years, BMI, Pulse_BPM |
| Categorical (2) | Sex, Race_Ethnicity |

**Never used as features**
- All blood-pressure readings and averages: they define the target.
- BP questionnaire answers (BPQ020, BPQ030) and BP medication (BPQ150): they define or reveal the target.
- SEQN: an identifier.
- SpO₂: NHANES 2021–2023 does not measure it, so it is not in the data.

`machine_learning/features.py` checks this list every time the data is loaded. The app also refuses to run if the saved model's feature list differs from the code's.

**BMI stays in the model.** The MAX30102 does not measure it, so users type it in. It is optional in the app; a blank is filled with the training-data median.

## Method

1. **Split.** One stratified 80/20 split with seed 42: 4,864 training rows and 1,217 test rows. The test set is used only for the final scoring.
2. **Preprocessing.** This happens inside each model's scikit-learn `Pipeline` (`features.build_preprocessor()`):
   - Numeric features: median imputation, then standardization.
   - Categorical features: most-frequent imputation, then one-hot encoding.

   Because the preprocessing sits inside the pipeline, it is refitted on the training part of every cross-validation fold and never sees the test set.
3. **Tuning.** 5-fold stratified cross-validation on the training set only, using a small hyperparameter grid per model (`machine_learning/models.py`) and scored by ROC-AUC. No resampling or synthetic data was used. All three models use `class_weight="balanced"`; the classes are nearly balanced (53% / 47%).
4. **Test scoring.** Each tuned model is scored once on the held-out test set, at a decision threshold of 0.5.
5. **Selection rule** (decided before looking at test results, and using cross-validation results only): pick the highest mean CV ROC-AUC. Models within 0.01 of the best count as tied, and the simplest of those wins. The ranking from simplest to most complex is Logistic Regression, Decision Tree, Random Forest.

## Why the income ratio was removed (version 2)

The app should not ask users for their family income, and the feature added almost nothing. `python -m machine_learning.check_income_ablation` compared every model with and without it, on the training data only, and saved `results/reports/income_ablation.csv`. Every difference in CV ROC-AUC was at most 0.0014, about ten times smaller than the fold-to-fold variation. That evidence was produced on the version 2 feature set.

## Models trained and results (version 3)

Three models were trained: Logistic Regression, Decision Tree and Random Forest.

| Model | Best settings | CV ROC-AUC (mean ± sd) | Test accuracy | Test precision | Test recall | Test specificity | Test F1 | Test ROC-AUC | Missed cases (FN) | False alarms (FP) |
|---|---|---|---|---|---|---|---|---|---|---|
| **Logistic Regression** (selected) | C = 0.1 | 0.788 ± 0.017 | 0.721 | **0.733** | 0.749 | **0.688** | 0.741 | **0.791** | 163 | 177 |
| Decision Tree | depth 6, min leaf 20 | 0.772 ± 0.011 | 0.709 | 0.726 | 0.730 | 0.685 | 0.728 | 0.764 | 175 | 179 |
| Random Forest | depth 10, min leaf 20 | 0.790 ± 0.014 | 0.725 | 0.726 | **0.777** | 0.665 | **0.751** | 0.789 | **145** | 190 |

The test set has 649 people with hypertension and 568 without.

**Change from version 2** (6 features, with waist): the selected Logistic Regression's test ROC-AUC went from 0.794 to 0.791. Its accuracy, precision and recall at the 0.5 threshold, and its confusion counts, stayed the same.

**Figures** (in `results/figures/`):

| File | Shows |
|---|---|
| `roc_curves.png` | ROC curves for all three models |
| `confusion_matrices.png` | One confusion matrix per model |
| `model_comparison.png` | Bar chart of all test metrics |
| `confusion_matrix.png` | Confusion matrix of the selected model |
| `feature_importance.png` | Which features the selected model relies on |
| `threshold_tradeoff.png` | How recall, precision and specificity change with the decision threshold |

## Why Logistic Regression was selected

- **It ties with Random Forest on ranking quality.** Random Forest has the highest mean CV ROC-AUC (0.790), but Logistic Regression is only 0.002 lower (0.788). That gap is within the pre-set 0.01 tie margin, and smaller than the fold-to-fold standard deviation (about 0.015). On the test set, Logistic Regression is in fact slightly higher (0.791 vs 0.789).
- **It is the simplest and easiest to explain.** Its coefficients can be read directly, it is fast, and the saved artifact is a few kilobytes.
- **Test results confirm it generalizes.** Cross-validation (0.788) and test (0.791) agree, so it is not overfitting.
- **Decision Tree is the weakest** (CV ROC-AUC 0.772, test ROC-AUC 0.764).

## False negatives vs false positives

- **A false negative** means a person who meets the hypertension definition is labelled "no hypertension". This is the more harmful error for a screening-style tool, because it could delay a real blood-pressure check.
- **A false positive** means a person who does not meet the definition is flagged. This costs an unnecessary check and possibly worry, but blood-pressure checks are cheap and safe.

At the 0.5 threshold, Random Forest misses fewer people (145 vs 163 for Logistic Regression), but it raises more false alarms (190 vs 177). Their ROC-AUCs are almost equal, so this difference comes mainly from where each model's 0.5 cut-off falls. `threshold_tradeoff.png` shows that lowering Logistic Regression's threshold would also raise recall, at the cost of specificity. The threshold was deliberately **not** tuned on the test set. Choosing a recall-oriented threshold with cross-validation on the training data is future work.

## Adequacy

**The performance is moderate.** ROC-AUC 0.791 means the model ranks a random person with hypertension above a random person without it about 79% of the time. About 1 in 4 people with hypertension is still missed. That is adequate for an educational demonstration. It is not adequate for any medical use.

## What the model relies on

Permutation importance on the test set (drop in ROC-AUC when a feature is shuffled):

| Feature | Drop in ROC-AUC |
|---|---|
| Age | 0.211 |
| BMI | 0.054 |
| Pulse | 0.015 |
| Race/ethnicity | 0.009 |
| Sex | 0.008 |

- **Age dominates.**
- **BMI's importance roughly doubled** compared with version 2 (0.029 → 0.054). It now carries the body-size information that the removed measurement used to share with it.
- **Pulse helps a little only once age and body size are known.** On its own, its correlation with the target is 0.04.

## Saved artifacts

| Path | Contents | In Git? |
|---|---|---|
| `machine_learning/models/hypertension_model.joblib` | The selected pipeline (preprocessing + Logistic Regression), fitted on the 4,864 training rows. It stores fitted parameters only, not data. | No (gitignored: regenerate with the training command) |
| `machine_learning/models/feature_schema.json` | Schema version 3: feature names and order, categories, input ranges for the app, dropped features, "SpO2 is not a model input", threshold, test metrics, and library versions | No (gitignored) |
| `machine_learning/models/archive/` | Version 1 and version 2 models and schemas | No (gitignored) |
| `results/reports/model_comparison.csv`, `model_evaluation.json` / `.md` | Version 3 reports | Yes |
| `results/reports/income_ablation.csv` | Version 2 evidence for removing the income ratio | Yes |
| `results/reports/archive/` | Version 1 and version 2 reports | Yes |

The model was trained with Python 3.10.11, scikit-learn 1.7.2, pandas 2.3.3, numpy 1.26.4 and joblib 1.5.3.

**Caution:** joblib files can run code when they are loaded. Only load model files you generated yourself.

## Application

`streamlit run app/app.py` loads the saved pipeline through `machine_learning/inference.py`.

**Inputs**
- Only the 5 trained features are passed to the model, in the trained order.
- Age, sex and race/ethnicity are required.
- BMI and pulse are optional and range-checked.
- Any extra input, such as an SpO₂ value or a removed feature, is rejected rather than passed to the model.

**Sensor panel**
- The app also shows a live sensor panel (heart rate, SpO₂, connection status, time of the latest measurement) for a future Arduino/ESP32 + MAX30102.
- These readings are **display only**: SpO₂ was not in the training data, and the sensor heart rate has not been validated against the cuff pulse the model learned from.
- Without hardware, the panel shows "Disconnected" and "—". See [iot/README.md](../iot/README.md).

## Reproduce

From the project root:

```bash
pip install -r requirements.txt
python data_analysis/run_pipeline.py      # build and validate the dataset (30 checks)
python -m machine_learning.train          # tune, compare, select, save model + reports + figures
python -m machine_learning.evaluate       # reload saved model, re-check metrics and inputs
python -m pytest                          # unit + app tests (no hardware needed)
streamlit run app/app.py                  # educational demo
```

## Limitations and remaining work

1. **No SpO₂ in the training data**, so the model cannot use the MAX30102 SpO₂ reading.
2. **Pulse was measured differently.** Training pulse came from a BP cuff after 5 minutes of seated rest. A fingertip sensor reading is not yet validated as a replacement (see the compatibility plan in iot/README.md).
3. **The label comes from one exam visit plus self-reported medication.** It is not a clinical diagnosis, and the model does not predict future disease.
4. **Survey weights are not used**, so the model reflects the NHANES sample (53% hypertension), not the U.S. population (47.7%). The scores are not calibrated personal risks.
5. **Evaluation is a single split.** There is no external validation on another population.
6. **Possible next steps (not done):**
   - Choose a recall-oriented threshold using training-set cross-validation.
   - Try survey-weighted training.
   - Get instructor review.
