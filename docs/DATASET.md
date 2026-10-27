# HyperPredict dataset: NHANES August 2021 – August 2023

This file records how the model-ready dataset is built, what every decision was, and what the data cannot do. All numbers below come from the pipeline outputs in `results/reports/` and can be regenerated with one command (see [Reproduce](#reproduce)).

## 1. Source

| Item | Value |
|---|---|
| Survey | U.S. CDC/NCHS National Health and Nutrition Examination Survey (NHANES), cycle August 2021 – August 2023 |
| Cycle page | https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2021-2023 |
| Population | U.S. civilian, non-institutionalized; awake participants measured in a mobile examination center (MEC) |
| Data type | Real participant data (not synthetic), public-use files |
| Access | Free public download, no registration. NCHS data-use terms forbid any attempt to identify participants. Raw and processed files are kept out of Git anyway (see `.gitignore`). |
| Reference analysis | NCHS Data Brief 511, *Hypertension Prevalence, Awareness, Treatment, and Control Among Adults Age 18 and Older: United States, August 2021–August 2023* — https://www.cdc.gov/nchs/products/databriefs/db511.htm (CDC analysis code: https://wwwn.cdc.gov/Nchs/data/Tutorials/Code/DB511_SUDAAN.sas) |

### Files and variables used

| File | Codebook | Rows | Variables used |
|---|---|---|---|
| DEMO_L | [DEMO_L.htm](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/DEMO_L.htm) | 11,933 | SEQN, RIDSTATR (exam status), RIAGENDR (sex), RIDAGEYR (age, 80+ top-coded as 80), RIDRETH3 (race/Hispanic origin), RIDEXPRG (pregnancy), INDFMPIR (income-to-poverty ratio, top-coded at 5), WTMEC2YR, SDMVPSU, SDMVSTRA (survey design) |
| BPXO_L | [BPXO_L.htm](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BPXO_L.htm) | 7,801 | BPXOSY1–3 / BPXODI1–3 (systolic/diastolic, mmHg), BPXOPLS1–3 (pulse, beats/min). Omron HEM-907XL oscillometric cuff, 3 readings 60 s apart after 5 min seated rest |
| BPQ_L | [BPQ_L.htm](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BPQ_L.htm) | 8,501 | BPQ020 (ever told high BP), BPQ030 (told on 2+ visits), BPQ150 (now taking prescribed BP medication) |
| BMX_L | [BMX_L.htm](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/BMX_L.htm) | 8,860 | BMXBMI (kg/m²), BMXWAIST (cm), BMXHT (cm), BMXWT (kg) |

Download URLs follow the pattern `https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2021/DataFiles/<FILE>.xpt` (SAS transport format). All four were downloaded and their row counts match the official codebooks.

### SpO₂ is not available

No NHANES 2021–2023 examination file contains oxygen saturation. The cycle's examination files are BMX_L, BPXO_L, LUX_L and BAX_L, and none has an SpO₂ or pulse-oximetry variable. **SpO₂ is therefore not a model input.** No SpO₂ values were created or imputed. The MAX30102 sensor demo must stay separate from the model (see `iot/README.md`).

Pulse **is** available, but it comes from the blood-pressure cuff, not a fingertip optical sensor.

## 2. Merge strategy

- **Key:** `SEQN` (respondent sequence number). Every raw file was checked for duplicate SEQN values (none found) before merging.
- **Join:** DEMO_L is the master list (one row per sampled person). BPXO_L, BPQ_L and BMX_L are **left-joined** onto it with `validate="one_to_one"`, so pandas refuses to run if any ID repeats.
- **Why a left join:** it keeps every participant and shows explicitly (as missing values) who has no exam or questionnaire record. Who is excluded is then decided by documented inclusion rules, not silently by an inner join.
- **Check:** every SEQN in the other files exists in DEMO_L.

| Step | Rows |
|---|---|
| DEMO_L (master) | 11,933 |
| + BPXO_L (7,801 records matched) | 11,933 |
| + BPQ_L (8,501 matched) | 11,933 |
| + BMX_L (8,860 matched) | 11,933 |

Raw `.xpt` files are only read, never modified. A pandas quirk reads SAS zeros as about 5.4e-79; these are restored to exact 0 during the merge (this affected 53 `Poverty_Income_Ratio` values in the final data).

## 3. Target definition

`Hypertension_Status` (integer): **1 = hypertension, 0 = no hypertension.**

This reproduces NCHS Data Brief 511, which follows the 2017 ACC/AHA guideline:

- **1** if mean systolic BP ≥ 130 mmHg **or** mean diastolic BP ≥ 80 mmHg **or** currently taking prescribed BP medication (BPQ150 = 1).
- **0** if mean BP < 130/80 **and** the person is known not to take BP medication. "Known" means either BPQ150 = 2, or BPQ020 = 2. If BPQ020 = 2 (never told they had high BP), the questionnaire skips BPQ150, so the person is not on BP medication.
- **Excluded** if BP is < 130/80 but medication status is unknown (refused, don't know, or missing). The NCHS code would label these 0; we exclude them so that missing information is never treated as "healthy". This affects 3 people.

The mean BP is the average of up to three valid readings, as in the CDC code.

**Measured vs diagnosed.** The target is *measured or treated* hypertension, not *previously diagnosed* hypertension. Both are kept as separate columns in the analysis file:

| Column | Meaning |
|---|---|
| `BP_Elevated` | Measured mean BP ≥ 130/80 at the exam |
| `Told_High_BP` | Self-reported previous diagnosis (BPQ020) |
| `Taking_BP_Medication` | Self-reported current BP medication |

Among the 6,081 included adults:
- 1,156 meet the BP threshold but were never told they had high BP (undiagnosed).
- 779 are labelled 1 only because of medication (their BP is controlled below 130/80).
- 153 report a past diagnosis but have normal BP and take no medication, so they are labelled 0.

**Official comparison:**

| | NCHS Data Brief 511 | This pipeline |
|---|---|---|
| Eligible adults | 6,084 | 6,084 before our extra rule, 6,081 after |
| Survey-weighted prevalence | 47.7% | 47.7% |

The 1-percentage-point tolerance check passes in `validate_dataset.py`.

## 4. Cleaning and exclusions

| Step | Removed | Remaining |
|---|---|---|
| Merged participants | – | 11,933 |
| Keep MEC-examined (RIDSTATR = 2) | 3,073 | 8,860 |
| Keep adults 18+ | 2,523 | 6,337 |
| Exclude pregnant at exam (RIDEXPRG = 1) | 41 | 6,296 |
| Keep ≥1 valid systolic and diastolic reading | 212 | 6,084 |
| Exclude normal BP with unknown medication status | 3 | **6,081** |

**Plausibility rules (project-defined).** These apply to single readings; an implausible value is set to missing, and the person is kept if other readings exist:

| Measurement | Plausible range | Values set to missing |
|---|---|---|
| Systolic BP | 60–270 mmHg | 0 |
| Diastolic BP | 30–150 mmHg | 1 (a reading of 24) |
| Pulse | 30–220 beats/min | 0 |
| BMI | 10–100 kg/m² | 0 |
| Waist | 40–200 cm | 0 |

A reading pair where diastolic ≥ systolic would be invalid; none occurred.

**Duplicates:** 0 duplicate SEQN values, and 0 fully identical rows.

**Outliers:** the 1.5×IQR rule flags 167 BMI, 69 waist and 85 pulse values. All of them are physiologically possible, so they are **retained**. Example: the lowest adult BMI is 11.1 (27.9 kg, 158 cm). Height and weight are consistent with that value, so it is a real, extreme measurement.

**Missing feature values:**

| Feature | Missing | % |
|---|---|---|
| Poverty_Income_Ratio | 787 | 12.9% |
| Waist_Circumference_cm | 201 | 3.3% |
| BMI | 62 | 1.0% |
| Age, Sex, Race_Ethnicity, Pulse | 0 | 0% |

Rows are **not** dropped for missing features. Missing values are imputed inside the model pipeline (median for numbers, most frequent value for categories), fitted on the training split only (`machine_learning/features.py`).

**Types and encoding:**
- Sex and race/ethnicity are stored as readable text labels and one-hot encoded inside the pipeline.
- Numeric features are standardized inside the pipeline (also fitted on training data only).

## 5. Final features and target leakage

**Model-ready file:** `data/processed/hypertension_clean.csv` (6,081 rows × 8 columns).

| Feature | Source | Unit |
|---|---|---|
| Age_Years | RIDAGEYR | years (80 = 80+) |
| Sex | RIAGENDR | Male / Female |
| Race_Ethnicity | RIDRETH3 | 6 categories |
| BMI | BMXBMI | kg/m² |
| Waist_Circumference_cm | BMXWAIST | cm |
| Pulse_BPM | mean of valid BPXOPLS1–3 | beats/min |
| Poverty_Income_Ratio | INDFMPIR | ratio, 0–5 |
| **Hypertension_Status** (target) | derived | 0 / 1 |

**Excluded from the predictors, with reasons:**

| Column(s) | Reason |
|---|---|
| SEQN | Identifier |
| BPXOSY1–3, BPXODI1–3, Mean_Systolic_BP, Mean_Diastolic_BP, N_BP_Readings, BP_Elevated | They define the target (direct leakage) |
| BPQ150 / Taking_BP_Medication | Defines the target |
| BPQ020, BPQ030 / Told_High_BP(_2Plus) | Previous hypertension diagnosis reveals the target |
| WTMEC2YR, SDMVPSU, SDMVSTRA | Survey-design variables, not personal characteristics |
| RIDSTATR, RIDEXPRG | Used only for inclusion rules |
| Height_cm, Weight_kg | Redundant with BMI; kept in the analysis file only |

The leakage list lives in `data_analysis/nhanes_config.py` (`LEAKAGE_COLUMNS`). The model-ready file contains only the features and the target. `features.load_features_and_target()` and `validate_dataset.py` both enforce this.

## 6. EDA findings

Figures are in `results/figures/`; numbers are in `results/reports/eda_summary.md`.

**Class balance**
- 3,242 hypertension (53.3%) vs 2,839 no hypertension (46.7%) in the sample.
- This is mild imbalance. The survey-weighted prevalence is 47.7%, because NHANES deliberately oversamples older and some minority groups.

**Age is the strongest signal**
- Spearman ρ = 0.41 with the target.
- Prevalence rises from 16% (ages 18–29) to 75% (ages 70+).

**Body size matters**
- Waist circumference: ρ = 0.32.
- BMI: ρ = 0.26.
- Median waist is 104 cm in the hypertension class vs 93 cm otherwise.

**Pulse is almost uninformative**
- ρ = 0.04.
- Median 71 vs 70 beats/min across the two classes.

**Other features**
- Income-to-poverty ratio is close to zero correlation (ρ = −0.03).
- Prevalence is higher in men (57%) than women (50%), and highest in non-Hispanic Black adults (64%).

**Target check:** the BP scatter plot (`bp_target_definition.png`) shows the label behaves exactly as defined. Every point at or above 130/80 is labelled 1; the labelled-1 points below the lines are people on medication.

**Medication effect on pulse:** adults on BP medication with normal BP have the lowest median pulse (69.3 vs 72.0 in untreated people with high BP). This is consistent with drugs such as beta-blockers lowering heart rate. Pulse is therefore partly influenced by treatment, not only by the disease.

## 7. Limitations and unresolved decisions

1. **No SpO₂.** A model trained on this dataset cannot use the MAX30102 SpO₂ reading. A model claiming to use SpO₂ would need a different, verified training dataset.
2. **Pulse is a cuff pulse.** It was measured by the BP device after 5 minutes of rest; a MAX30102 fingertip reading may differ (sensor accuracy, motion, not resting). Pulse is also a weak predictor and is partly affected by medication.
3. **The target is a one-visit measurement plus self-report.** A clinical diagnosis needs repeated measurements on separate days, and medication use is self-reported.
4. **Survey weights are not used in modeling.** The model learns from the sample, which over-represents some groups. Weighted prevalence (47.7%) differs from sample prevalence (53.3%).
5. **Top-coding and missing values.** Age is top-coded at 80 and income ratio at 5. Income ratio is missing for 13% of people (imputed in the pipeline).
6. **Not decided yet (team):**
   - Whether to keep `Poverty_Income_Ratio`, since the app would have to ask users for it.
   - Whether to use survey weights as `sample_weight` during training.
   - Whether to test the older 140/90 definition as a sensitivity analysis.

**Class imbalance options for the modeling stage:** imbalance is mild (53/47), so stratified splitting plus `class_weight="balanced"` (already in `train.py`) should be enough. Report per-class recall, ROC-AUC and the confusion matrix. **Do not** oversample or create synthetic records.

## Reproduce

```bash
pip install -r requirements.txt
python data_analysis/run_pipeline.py          # download (if needed) → merge → clean → EDA → validate
python data_analysis/run_pipeline.py --force  # same, but re-download the raw CDC files
```

Individual steps (run from the project root):

```bash
python data_analysis/download_nhanes.py
python data_analysis/merge_nhanes.py
python data_analysis/preprocessing.py
python data_analysis/eda.py
python data_analysis/validate_dataset.py
```

**Outputs**

| Path | Contents |
|---|---|
| `data/raw/*.xpt` | Unchanged CDC files |
| `data/processed/nhanes_merged.csv` | Merged file |
| `data/processed/hypertension_analysis.csv` | Audit / EDA file |
| `data/processed/hypertension_clean.csv` | Model-ready file |
| `results/figures/*.png` | EDA charts |
| `results/reports/*.json, *.md` | Merge, cleaning, EDA and validation reports |
