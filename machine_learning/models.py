"""Candidate classifiers and their small hyperparameter grids."""

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from machine_learning.features import RANDOM_STATE, build_preprocessor


COMPLEXITY_RANK = {
    "Logistic Regression": 1,
    "Decision Tree": 2,
    "Random Forest": 3,
}


def _pipeline(classifier) -> Pipeline:
    return Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier", classifier),
    ])


def get_candidates() -> tuple[dict, dict]:
    candidates = {
        "Logistic Regression": (
            _pipeline(LogisticRegression(
                max_iter=2000,
                class_weight="balanced",
                random_state=RANDOM_STATE,
            )),
            {"classifier__C": [0.01, 0.1, 1.0, 10.0]},
        ),
        "Decision Tree": (
            _pipeline(DecisionTreeClassifier(
                class_weight="balanced",
                random_state=RANDOM_STATE,
            )),
            {
                "classifier__max_depth": [3, 4, 5, 6, 8],
                "classifier__min_samples_leaf": [20, 50, 100],
            },
        ),
        "Random Forest": (
            _pipeline(RandomForestClassifier(
                n_estimators=300,
                class_weight="balanced",
                max_features="sqrt",
                n_jobs=-1,
                random_state=RANDOM_STATE,
            )),
            {
                "classifier__max_depth": [6, 10, None],
                "classifier__min_samples_leaf": [5, 20, 50],
            },
        ),
    }

    return candidates, {}