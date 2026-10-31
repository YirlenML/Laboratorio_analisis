import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from proyecto.config import COST_MATRIX
from proyecto.data.split import group_cv
from proyecto.features.engineering import CATEGORICAL_BASE, NUMERIC_BASE, PROSPER_HISTORY_COUNTS
from proyecto.models.train import (
    build_pipeline,
    decide_min_cost,
    encode_target,
    evaluate_folds,
    expected_cost,
    fold_metrics,
    improvement_over_noise,
    metrics_from_proba,
    out_of_fold_proba,
)


def test_expected_cost_uses_the_cost_matrix():
    # real impago (1) predicho pagó (0) cuesta 4; real pagó (0) predicho impago (1) cuesta 1
    assert expected_cost(np.array([1]), np.array([0])) == COST_MATRIX[1, 0] == 4
    assert expected_cost(np.array([0]), np.array([1])) == COST_MATRIX[0, 1] == 1
    assert expected_cost(np.array([0, 1]), np.array([0, 1])) == 0


def test_decision_rule_flags_default_above_one_fifth():
    p = np.array([0.15, 0.25, 0.9])
    assert decide_min_cost(np.column_stack([1 - p, p])).tolist() == [0, 1, 1]


def test_perfect_probabilities_give_perfect_metrics():
    y = np.array([0, 1, 0, 1, 0])
    result = metrics_from_proba(y, y.astype(float))
    assert result["pr_auc"] == 1 and result["roc_auc"] == 1 and result["cost"] == 0
    assert result["recall_default"] == 1 and result["brier"] == 0


def test_uninformative_probabilities_give_chance_level_ranking():
    rng = np.random.default_rng(0)
    y = (rng.random(5000) < 0.3).astype(int)
    result = metrics_from_proba(y, rng.random(5000))
    assert abs(result["roc_auc"] - 0.5) < 0.05
    assert abs(result["pr_auc"] - y.mean()) < 0.05  # AUC-PR sin información = proporción de impagos


def test_improvement_over_noise_counts_folds_won():
    ref = pd.Series([0.50, 0.52, 0.48])
    var = pd.Series([0.53, 0.55, 0.47])
    out = improvement_over_noise(ref, var)
    assert out["mejora"] == pytest.approx(0.05 / 3)
    assert out["pliegues ganados"] == 2
    diffs = np.array([0.03, 0.03, -0.01])
    assert out["mejora / ruido de a pares"] == pytest.approx(diffs.mean() / diffs.std(ddof=1))
    # con "menor es mejor" el signo se invierte
    assert improvement_over_noise(ref, var, higher_is_better=False)["mejora"] == pytest.approx(-0.05 / 3)


def test_identical_variants_have_no_improvement():
    ref = pd.Series([0.5, 0.6, 0.55])
    out = improvement_over_noise(ref, ref)
    assert out["mejora"] == 0 and out["pliegues ganados"] == 0 and out["mejora / ruido de a pares"] == 0


def test_pipeline_runs_end_to_end_with_group_folds():
    rng = np.random.default_rng(0)
    n = 200
    df = pd.DataFrame({c: rng.normal(size=n) for c in NUMERIC_BASE})
    for c in CATEGORICAL_BASE:
        df[c] = rng.choice(["a", "b"], size=n)
    df["StatedMonthlyIncome"] = rng.uniform(1000, 5000, size=n)
    df["LoanOriginationDate"] = pd.Timestamp("2012-01-01")
    df["FirstRecordedCreditLine"] = "1/01/2000 0:00"
    df["ScorexChangeAtTimeOfListing"] = np.nan
    df[PROSPER_HISTORY_COUNTS] = np.nan
    df["MemberKey"] = np.repeat([f"M{i}" for i in range(50)], 4)
    y = (rng.random(n) < 0.3).astype(int)

    folds = list(group_cv(3).split(df, y, groups=df["MemberKey"]))
    pipeline = build_pipeline(LogisticRegression(max_iter=500), scale=True, use_ratios=True)
    table = evaluate_folds(pipeline, df, y, folds)
    assert len(table) == 3 and table["pr_auc"].between(0, 1).all()

    # las predicciones fuera de pliegue cubren todas las filas y reproducen las métricas por pliegue
    oof = out_of_fold_proba(pipeline, df, y, folds)
    assert not np.isnan(oof).any()
    pd.testing.assert_series_equal(fold_metrics(y, oof, folds)["pr_auc"], table["pr_auc"])

    # con un segmento, cada pliegue se mide solo en sus filas
    mask = np.arange(n) % 2 == 0
    assert len(fold_metrics(y, oof, folds, mask=mask)) == 3


def test_encode_target_accepts_only_zero_one():
    assert encode_target(pd.Series([0, 1, 1])).tolist() == [0, 1, 1]
    with pytest.raises(ValueError):
        encode_target(pd.Series([0, 2]))


def test_metrics_accept_the_predict_proba_matrix_or_one_column():
    rng = np.random.default_rng(3)
    y = (rng.random(300) < 0.3).astype(int)
    p = rng.random(300)
    assert metrics_from_proba(y, p) == metrics_from_proba(y, np.column_stack([1 - p, p]))


def test_evaluate_folds_accepts_a_splitter_or_precomputed_folds():
    rng = np.random.default_rng(0)
    n = 120
    df = pd.DataFrame({c: rng.normal(size=n) for c in NUMERIC_BASE})
    for c in CATEGORICAL_BASE:
        df[c] = rng.choice(["a", "b"], size=n)
    df["StatedMonthlyIncome"] = rng.uniform(1000, 5000, size=n)
    df["LoanOriginationDate"] = pd.Timestamp("2012-01-01")
    df["FirstRecordedCreditLine"] = "1/01/2000 0:00"
    df[PROSPER_HISTORY_COUNTS] = np.nan
    df["MemberKey"] = np.repeat([f"M{i}" for i in range(40)], 3)
    y = (rng.random(n) < 0.3).astype(int)
    pipeline = build_pipeline(LogisticRegression(max_iter=500), scale=True)
    with_splitter = evaluate_folds(pipeline, df, y, group_cv(3))   # estilo del ejemplo del curso
    with_folds = evaluate_folds(pipeline, df, y, list(group_cv(3).split(df, y, groups=df["MemberKey"])))
    pd.testing.assert_frame_equal(with_splitter.drop(columns="fit_seconds"), with_folds.drop(columns="fit_seconds"))


def test_flagged_rate_and_argmax_cost():
    y = np.array([0, 0, 1, 1])
    p = np.array([0.1, 0.3, 0.4, 0.9])   # regla de costo: marca si P > 0,2 -> 3 de 4
    result = metrics_from_proba(y, p)
    assert result["flagged_rate"] == 0.75
    assert result["cost"] == 1 / 4           # un buen cliente marcado (costo 1)
    assert result["cost_argmax"] == 4 / 4    # con umbral 0,5 se escapa un impago (costo 4)
