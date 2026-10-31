import numpy as np
import pandas as pd
import pytest

from proyecto.data.split import group_cv
from proyecto.features.engineering import CATEGORICAL_BASE, FINAL_FEATURES, NUMERIC_BASE, PROSPER_HISTORY_COUNTS
from proyecto.models.train import build_pipeline, candidates, evaluate_folds
from proyecto.models.tuning import (
    MODELS,
    OBJETIVOS,
    bootstrap_cost_difference,
    bootstrap_metric_ci,
    bootstrap_metric_difference,
    pr_auc,
    tune,
)


@pytest.fixture(scope="module")
def loans():
    """Préstamos de juguete con las columnas que piden las variables finales; el impago depende de una variable."""
    rng = np.random.default_rng(1)
    n = 240
    df = pd.DataFrame({c: rng.normal(size=n) for c in NUMERIC_BASE})
    for c in CATEGORICAL_BASE + ["CreditGrade"]:
        df[c] = rng.choice(["a", "b"], size=n)
    df["EmploymentStatus"] = rng.choice(["Employed", "Full-time", "Self-employed"], size=n)
    for c in ["BorrowerAPR", "ProsperRating (numeric)", "ProsperScore", "EstimatedLoss", "EstimatedReturn",
              "EstimatedEffectiveYield", "ScorexChangeAtTimeOfListing"]:
        df[c] = rng.normal(size=n)
    df[PROSPER_HISTORY_COUNTS] = np.nan
    df["StatedMonthlyIncome"] = rng.uniform(1000, 5000, size=n)
    df["LoanOriginationDate"] = pd.Timestamp("2012-01-01")
    df["FirstRecordedCreditLine"] = "1/01/2000 0:00"
    df["MemberKey"] = np.repeat([f"M{i}" for i in range(80)], 3)
    y = (df["BorrowerAPR"] + rng.normal(scale=0.5, size=n) > 0.5).astype(int).to_numpy()
    return df, y


def test_candidates_include_a_baseline_and_three_models():
    models = candidates()
    assert any("línea base" in name for name in models) and len(models) >= 4


def test_baseline_ranks_at_chance_and_rejects_everyone(loans):
    X, y = loans
    folds = list(group_cv(3).split(X, y, groups=X["MemberKey"]))
    model, scale = candidates()["línea base (proporción de impago)"]
    table = evaluate_folds(build_pipeline(model, scale=scale, **FINAL_FEATURES), X, y, folds)
    assert (table["roc_auc"] == 0.5).all()
    # predice la proporción de impago (> 0,2) para todos -> los marca a todos como impago
    assert (table["recall_default"] == 1).all()


def test_tune_runs_a_small_study_without_mlflow(loans):
    X, y = loans
    folds = list(group_cv(3).split(X, y, groups=X["MemberKey"]))
    study = tune("lightgbm", X, y, folds, n_trials=2, log=False)
    assert len(study.trials) == 2 and 0 <= study.best_value <= 1
    assert set(study.best_params) == {"n_estimators", "learning_rate", "num_leaves", "min_child_samples",
                                      "subsample", "colsample_bytree", "reg_lambda"}
    assert set(MODELS) == {"lightgbm", "xgboost", "random forest"}


def test_tune_rejects_unknown_metric(loans):
    X, y = loans
    with pytest.raises(ValueError):
        tune("lightgbm", X, y, [], n_trials=1, log=False, metric="exactitud")
    assert OBJETIVOS["pr_auc"] == "maximize" and OBJETIVOS["log_loss"] == "minimize"


def test_bootstrap_difference_of_identical_predictions_is_zero():
    rng = np.random.default_rng(0)
    y = (rng.random(300) < 0.3).astype(int)
    p = rng.random(300)
    groups = np.repeat(np.arange(100), 3)
    diff, low, high = bootstrap_metric_difference(y, p, p, groups, n_boot=50)
    assert diff == low == high == 0


def test_bootstrap_detects_a_clearly_better_model():
    rng = np.random.default_rng(0)
    y = (rng.random(600) < 0.3).astype(int)
    good = y * 0.6 + rng.random(600) * 0.4   # ordena casi perfecto
    noise = rng.random(600)                    # sin información
    groups = np.repeat(np.arange(200), 3)
    diff, low, high = bootstrap_metric_difference(y, good, noise, groups, n_boot=100)
    assert diff > 0 and low > 0
    value, ci_low, ci_high = bootstrap_metric_ci(y, good, groups, n_boot=100)
    assert ci_low <= value <= ci_high


# --- Pruebas adaptadas del ejemplo del curso (tests/test_tuning.py y test_tuning_ci.py), en versión binaria ---

def test_bootstrap_cost_difference_is_zero_for_identical_models():
    rng = np.random.default_rng(0)
    y = (rng.random(400) < 0.3).astype(int)
    p = rng.random(400)
    groups = np.repeat(np.arange(100), 4)
    assert bootstrap_cost_difference(y, p, p, groups, n_boot=200) == (0.0, 0.0, 0.0)


def test_bootstrap_cost_difference_detects_a_clearly_better_model():
    rng = np.random.default_rng(1)
    y = (rng.random(800) < 0.3).astype(int)
    good = np.where(y == 1, 0.9, 0.05)   # casi siempre acierta
    bad = np.where(y == 1, 0.05, 0.9)    # casi siempre se equivoca
    groups = np.repeat(np.arange(200), 4)
    diff, low, high = bootstrap_cost_difference(y, good, bad, groups, n_boot=300)
    assert diff < 0 and high < 0  # todo el intervalo bajo cero: A cuesta menos
    # acepta también la matriz de predict_proba
    assert bootstrap_cost_difference(y, np.column_stack([1 - good, good]), bad, groups, n_boot=300)[0] == diff


def test_every_objective_has_a_direction():
    assert set(OBJETIVOS.values()) <= {"minimize", "maximize"}
    assert OBJETIVOS["cost"] == "minimize" and OBJETIVOS["pr_auc"] == "maximize"


def test_tune_rejects_unknown_metric_before_touching_data():
    with pytest.raises(ValueError, match="no soportada"):
        tune("lightgbm", None, None, None, n_trials=1, metric="inventada")


def test_bootstrap_metric_ci_is_reproducible_and_accepts_the_matrix():
    rng = np.random.default_rng(0)
    groups = np.repeat(np.arange(60), 4)
    y = (rng.random(240) < 0.3).astype(int)
    p = rng.random(240)
    first = bootstrap_metric_ci(y, p, groups)
    assert first == bootstrap_metric_ci(y, p, groups)
    assert first == bootstrap_metric_ci(y, np.column_stack([1 - p, p]), groups)
    perfect = bootstrap_metric_ci(y, y.astype(float), groups, pr_auc)
    assert perfect == (1.0, 1.0, 1.0)
