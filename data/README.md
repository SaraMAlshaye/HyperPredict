# Dataset instructions

1. Obtain the instructor-approved dataset and confirm its source, license, and target-label definition.
2. Place the CSV at data/raw/hypertension.csv.
3. Keep raw and processed datasets out of Git. The repository .gitignore excludes CSV files under these folders.
4. The starter scripts expect a target column named Hypertension_Status. Update the scripts if your real column name differs.

Do not upload private, identifiable, restricted, or non-redistributable data. A dataset being downloadable does not automatically mean it may be redistributed.

Before modeling, verify whether the target labels were created from systolic/diastolic blood-pressure thresholds. If so, using those same measurements as predictors may leak the rule used to create the target and lead to misleading performance.
