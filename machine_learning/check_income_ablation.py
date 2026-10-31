"""Evidence for removing Poverty_Income_Ratio: CV ROC-AUC with vs without it.

Run from the project root:   python -m machine_learning.check_income_ablation

Uses the TRAINING split only (the test set is never touched). Each model is re-tuned
with the same grids as train.py, once with the income ratio and once without, and
the mean 5-fold CV ROC-AUC is compared. Writes results/reports/income_ablation.csv.
"""
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from machine_learning.features import (
    ANALYSIS_PATH, CATEGORICAL_FEATURES, CV_FOLDS, NUMERIC_FEATURES, RANDOM_STATE,
    REPORTS_DIR, TARGET_COLUMN, TEST_SIZE,
)
from machine_learning.models import get_candidates

INCOME = "Poverty_Income_Ratio"


def preprocessor(numeric):
    return ColumnTransformer([
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median")),
                              ("scaler", StandardScaler())]), numeric),
        ("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                                  ("onehot", OneHotEncoder(handle_unknown="ignore"))]),
         CATEGORICAL_FEATURES)])


def main() -> None:
    # The analysis file still holds the income ratio; rows/order match the clean file,
    # so this reproduces the exact training split used by train.py.
    df = pd.read_csv(ANALYSIS_PATH)
    with_income = NUMERIC_FEATURES + [INCOME]
    X = df[with_income + CATEGORICAL_FEATURES]
    y = df[TARGET_COLUMN].astype(int)
    X_train, _, y_train, _ = train_test_split(X, y, test_size=TEST_SIZE,
                                              random_state=RANDOM_STATE, stratify=y)
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    candidates, _ = get_candidates()
    rows = []
    for name, (pipe, grid) in candidates.items():
        scores = {}
        for label, numeric in [("with_income", with_income), ("without_income", NUMERIC_FEATURES)]:
            model = Pipeline([("preprocessor", preprocessor(numeric)),
                              ("classifier", clone(pipe.named_steps["classifier"]))])
            search = GridSearchCV(model, grid, scoring="roc_auc", cv=cv, n_jobs=-1)
            search.fit(X_train[numeric + CATEGORICAL_FEATURES], y_train)
            i = search.best_index_
            scores[label] = (search.cv_results_["mean_test_score"][i],
                             search.cv_results_["std_test_score"][i])
        diff = scores["without_income"][0] - scores["with_income"][0]
        rows.append({"model": name,
                     "cv_auc_with_income": round(scores["with_income"][0], 4),
                     "cv_auc_without_income": round(scores["without_income"][0], 4),
                     "difference": round(diff, 4),
                     "cv_sd_with_income": round(scores["with_income"][1], 4)})
        print(f"{name:20} with {scores['with_income'][0]:.4f}  without "
              f"{scores['without_income'][0]:.4f}  diff {diff:+.4f}")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(REPORTS_DIR / "income_ablation.csv", index=False)
    print(f"Saved {REPORTS_DIR / 'income_ablation.csv'}")


if __name__ == "__main__":
    main()
