"""Candidatos, métricas con costo de negocio y evaluación con validación cruzada por prestatario.

Misma estructura y nombres que `creditsight/models/train.py` del ejemplo del curso. Diferencias, por el caso:
  - Problema binario (0 = pagó, 1 = impago); `metrics_from_proba` acepta la matriz de `predict_proba` o solo la
    columna de impago, y la métrica principal es AUC-PR.
  - `evaluate_folds`, `evaluate` y `out_of_fold_proba` aceptan un `cv` (p. ej. `group_cv(5)`) o los pliegues ya
    calculados (lista de pares de índices), para garantizar los MISMOS pliegues en todas las comparaciones.
  - Extras: `out_of_fold_proba`, `fold_metrics` e `improvement_over_noise` (etapa 4).
"""
import time

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from xgboost import XGBClassifier

from proyecto.config import COST_MATRIX, GROUP_COL, RANDOM_STATE, TARGET
from proyecto.features.engineering import add_features, build_preprocessor


def encode_target(y: pd.Series) -> np.ndarray:
    """`is_default` -> arreglo de enteros 0/1. Falla si hay otro valor (el objetivo ya viene codificado del notebook 03)."""
    values = np.asarray(y)
    if not set(np.unique(values)) <= {0, 1}:
        raise ValueError(f"El objetivo debe ser 0/1; hay {sorted(set(np.unique(values)) - {0, 1})}")
    return values.astype(int)


def _as_folds(cv, X: pd.DataFrame, y: np.ndarray) -> list:
    """Pliegues como lista de (entrenamiento, validación): de un objeto con `.split` (por prestatario) o ya calculados."""
    if hasattr(cv, "split"):
        return list(cv.split(X, y, groups=X[GROUP_COL]))
    return list(cv)


def default_probability(proba: np.ndarray) -> np.ndarray:
    """Probabilidad de impago: acepta la matriz de `predict_proba` (n x 2) o una sola columna."""
    proba = np.asarray(proba, dtype=float)
    return proba[:, 1] if proba.ndim == 2 else proba


def expected_cost(y_true, y_pred, cost: np.ndarray = COST_MATRIX) -> float:
    """Costo promedio por préstamo según la matriz de costos (menor es mejor)."""
    return float(cost[np.asarray(y_true), np.asarray(y_pred)].mean())


def decide_min_cost(proba: np.ndarray, cost: np.ndarray = COST_MATRIX) -> np.ndarray:
    """Elige la clase con menor costo esperado: argmin_j sum_i p_i * costo(i, j).

    Con la matriz 4 a 1 equivale a marcar impago si P(impago) > 1 / (1 + 4) = 0,2.
    """
    return np.argmin(proba @ cost, axis=1)


def candidates(random_state: int = RANDOM_STATE) -> dict:
    """Modelos del torneo con parámetros razonables (sin optimizar); el booleano indica si necesitan escalado.

    La línea base predice para todos la proporción de impagos del entrenamiento (≈ 0,31). Como 0,31 > 0,2, la regla de
    menor costo la convierte en "rechazar a todos" (costo 0,69, la mejor estrategia sin modelo del notebook 01).
    """
    return {
        "línea base (proporción de impago)": (DummyClassifier(strategy="prior"), False),
        "regresión logística": (LogisticRegression(max_iter=2000, random_state=random_state), True),
        "random forest": (
            RandomForestClassifier(n_estimators=200, min_samples_leaf=3, n_jobs=2, random_state=random_state),
            False,
        ),
        "lightgbm": (
            LGBMClassifier(n_estimators=300, learning_rate=0.05, num_leaves=31, random_state=random_state, verbose=-1, n_jobs=2),
            False,
        ),
        "xgboost": (
            XGBClassifier(
                n_estimators=300, learning_rate=0.05, max_depth=6, tree_method="hist",
                random_state=random_state, n_jobs=2, eval_metric="logloss",
            ),
            False,
        ),
    }


def build_pipeline(model, scale: bool, **feature_flags) -> Pipeline:
    """Pipeline completo: variables calculadas -> preprocesamiento -> modelo. Se guarda entero.

    Sin `feature_flags` usa solo la referencia de la etapa 4. Desde la etapa 5 se pasa `**FINAL_FEATURES`.
    """
    return Pipeline(
        [
            ("features", FunctionTransformer(add_features)),
            ("prep", build_preprocessor(scale=scale, **feature_flags)),
            ("model", model),
        ]
    )


def metrics_from_proba(y_true: np.ndarray, proba: np.ndarray) -> dict:
    """Métricas de negocio y técnicas a partir de las probabilidades.

    `proba` puede ser la matriz de `predict_proba` (n x 2) o solo la probabilidad de impago.
    - Ranking y calibración (no dependen de un umbral): AUC-PR (principal), ROC-AUC, log loss y Brier.
    - Decisión de negocio (clase de menor costo esperado): costo, recall, precisión y F1 de impago, y la proporción
      de solicitudes marcadas para revisión (carga del analista).
    - `cost_argmax`: costo si se decidiera por la clase más probable (umbral 0,5), para medir lo que aporta la regla
      de menor costo (como en el ejemplo del curso).
    """
    y_true = np.asarray(y_true)
    p_default = default_probability(proba)
    proba = np.column_stack([1 - p_default, p_default])
    decision = decide_min_cost(proba)
    argmax = proba.argmax(axis=1)
    return {
        "pr_auc": average_precision_score(y_true, p_default),
        "roc_auc": roc_auc_score(y_true, p_default),
        "log_loss": log_loss(y_true, proba, labels=[0, 1]),
        "brier": brier_score_loss(y_true, p_default),
        "cost": expected_cost(y_true, decision),
        "cost_argmax": expected_cost(y_true, argmax),
        "recall_default": recall_score(y_true, decision, zero_division=0),
        "precision_default": precision_score(y_true, decision, zero_division=0),
        "f1_default": f1_score(y_true, decision, zero_division=0),
        "flagged_rate": float(decision.mean()),
    }


def evaluate_folds(pipeline, X: pd.DataFrame, y: np.ndarray, cv) -> pd.DataFrame:
    """Validación cruzada por prestatario. Una fila por pliegue con todas las métricas y el tiempo de ajuste.

    `cv`: un objeto con `.split` (se parte por `MemberKey`) o los pliegues ya calculados.
    """
    y = np.asarray(y)
    rows = []
    for fold, (train_idx, valid_idx) in enumerate(_as_folds(cv, X, y)):
        model = clone(pipeline)
        start = time.time()
        model.fit(X.iloc[train_idx], y[train_idx])
        seconds = time.time() - start
        p_default = model.predict_proba(X.iloc[valid_idx])[:, 1]
        rows.append({"fold": fold, **metrics_from_proba(y[valid_idx], p_default), "fit_seconds": seconds})
    return pd.DataFrame(rows).set_index("fold")


def out_of_fold_proba(pipeline, X: pd.DataFrame, y: np.ndarray, cv) -> np.ndarray:
    """Probabilidad de impago de cada fila, predicha por el modelo del pliegue en que esa fila NO se entrenó."""
    y = np.asarray(y)
    oof = np.full(len(X), np.nan)
    for train_idx, valid_idx in _as_folds(cv, X, y):
        model = clone(pipeline).fit(X.iloc[train_idx], y[train_idx])
        oof[valid_idx] = model.predict_proba(X.iloc[valid_idx])[:, 1]
    return oof


def fold_metrics(y: np.ndarray, oof: np.ndarray, folds, mask: np.ndarray | None = None) -> pd.DataFrame:
    """Métricas por pliegue a partir de las predicciones fuera de pliegue.

    `mask` (opcional) restringe cada pliegue a un segmento de filas, p. ej. los préstamos desde 2009.
    """
    y = np.asarray(y)
    rows = []
    for fold, (_, valid_idx) in enumerate(folds):
        idx = valid_idx if mask is None else valid_idx[np.asarray(mask)[valid_idx]]
        rows.append({"fold": fold, **metrics_from_proba(y[idx], oof[idx])})
    return pd.DataFrame(rows).set_index("fold")


def evaluate(pipeline, X: pd.DataFrame, y: np.ndarray, cv) -> dict:
    """Como `evaluate_folds`, pero devuelve la media y la desviación entre pliegues de cada métrica."""
    table = evaluate_folds(pipeline, X, y, cv)
    out = {f"{name}_mean": float(table[name].mean()) for name in table if name != "fit_seconds"}
    out.update({f"{name}_std": float(table[name].std()) for name in table if name != "fit_seconds"})
    out["fit_seconds"] = float(table["fit_seconds"].mean())
    return out


def improvement_over_noise(reference: pd.Series, variant: pd.Series, higher_is_better: bool = True) -> dict:
    """Compara dos variantes medidas en los MISMOS pliegues.

    - `mejora`: diferencia de medias (positiva = la variante es mejor).
    - `mejora / ruido`: mejora dividida por la desviación de la variante entre pliegues (regla del curso).
    - `pliegues ganados`: en cuántos pliegues la variante supera a la referencia.
    - `mejora / ruido de a pares`: mejora dividida por la desviación de la *diferencia* entre pliegues. Quita la
      parte del ruido que comparten las dos variantes (un pliegue difícil lo es para ambas).
    """
    sign = 1 if higher_is_better else -1
    diff = sign * (np.asarray(variant) - np.asarray(reference))
    improvement = float(diff.mean())
    noise = float(np.std(variant, ddof=1))
    paired_noise = float(np.std(diff, ddof=1))
    return {
        "mejora": improvement,
        "ruido": noise,
        "mejora / ruido": improvement / noise if noise > 0 else np.inf,
        "pliegues ganados": int((diff > 0).sum()),
        "mejora / ruido de a pares": improvement / paired_noise if paired_noise > 0 else 0.0,
    }


def feature_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Quita el objetivo; conserva MemberKey para poder agrupar (el preprocesamiento lo ignora)."""
    return df.drop(columns=[TARGET])
