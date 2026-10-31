"""Optimización de hiperparámetros con Optuna, registrando cada ensayo en MLflow, y comprobación con bootstrap.

Misma estructura y nombres que `creditsight/models/tuning.py` del ejemplo del curso. Diferencias, por el caso:
  - Finalistas del torneo de Eco-Score: LightGBM y XGBoost (se conserva random forest, como en el ejemplo).
  - Métrica optimizada por defecto: AUC-PR (`pr_auc`), la principal del proyecto.
  - `tune` acepta las variables (`feature_flags`, por defecto `FINAL_FEATURES`) y un `cv` o pliegues ya calculados.
  - Los bootstrap remuestrean PRESTATARIOS (`MemberKey`) y aceptan la matriz de `predict_proba` o solo P(impago).
"""
from pathlib import Path

import mlflow
import numpy as np
import optuna
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score
from xgboost import XGBClassifier

from proyecto.config import COST_MATRIX, RANDOM_STATE
from proyecto.features.engineering import FINAL_FEATURES
from proyecto.models.train import build_pipeline, decide_min_cost, default_probability, evaluate_folds
from proyecto.tracking.mlflow_utils import log_run


def lgbm_space(trial: optuna.Trial) -> dict:
    """Espacio de búsqueda de LightGBM; los rangos salen del conocimiento del algoritmo, no al azar."""
    return {
        "n_estimators": trial.suggest_int("n_estimators", 150, 600),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 15, 63),
        "min_child_samples": trial.suggest_int("min_child_samples", 20, 300),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.4, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
    }


def xgb_space(trial: optuna.Trial) -> dict:
    """Espacio de búsqueda de XGBoost (árboles por profundidad, no por hojas)."""
    return {
        "n_estimators": trial.suggest_int("n_estimators", 150, 600),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "max_depth": trial.suggest_int("max_depth", 3, 8),
        "min_child_weight": trial.suggest_float("min_child_weight", 1.0, 20.0, log=True),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.4, 1.0),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
    }


def rf_space(trial: optuna.Trial) -> dict:
    """Espacio de búsqueda de random forest. Los árboles se fijan en 200: lo que se afina es su forma."""
    return {
        "max_depth": trial.suggest_int("max_depth", 6, 24),
        "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 30),
        "max_features": trial.suggest_float("max_features", 0.1, 0.8),
    }


def make_lgbm(params: dict, random_state: int = RANDOM_STATE) -> LGBMClassifier:
    return LGBMClassifier(subsample_freq=1, random_state=random_state, verbose=-1, n_jobs=2, **params)


def make_xgb(params: dict, random_state: int = RANDOM_STATE) -> XGBClassifier:
    return XGBClassifier(tree_method="hist", eval_metric="logloss", random_state=random_state, n_jobs=2, **params)


def make_rf(params: dict, random_state: int = RANDOM_STATE) -> RandomForestClassifier:
    return RandomForestClassifier(n_estimators=200, n_jobs=2, random_state=random_state, **params)


# nombre -> (espacio, constructor, ¿escalar?)
MODELS = {
    "lightgbm": (lgbm_space, make_lgbm, False),
    "xgboost": (xgb_space, make_xgb, False),
    "random forest": (rf_space, make_rf, False),
}

# Métricas que se pueden optimizar y en qué dirección. Todas salen de `metrics_from_proba`.
OBJETIVOS = {
    "pr_auc": "maximize",     # principal: AUC-PR de impago
    "roc_auc": "maximize",
    "log_loss": "minimize",   # calidad de las probabilidades
    "brier": "minimize",
    "cost": "minimize",       # negocio: costo esperado con la matriz 4 a 1
}


def tune(name: str, X: pd.DataFrame, y: np.ndarray, cv, n_trials: int, seed: int = RANDOM_STATE, log: bool = True,
         storage: str | None = None, metric: str = "pr_auc", feature_flags: dict | None = None):
    """Corre un estudio de Optuna que optimiza `metric` (ver OBJETIVOS). `cv`: objeto con `.split` o pliegues ya calculados.

    Cada ensayo queda como ejecución anidada en MLflow con TODAS las métricas (media y desviación entre pliegues).
    Con `storage` (ruta de un archivo .db) el estudio se guarda en disco y se reanuda si la ejecución se corta.
    """
    if metric not in OBJETIVOS:
        raise ValueError(f"Métrica no soportada: {metric}. Opciones: {sorted(OBJETIVOS)}")
    space_fn, make_fn, scale = MODELS[name]
    flags = FINAL_FEATURES if feature_flags is None else feature_flags

    def objective(trial: optuna.Trial) -> float:
        params = space_fn(trial)
        table = evaluate_folds(build_pipeline(make_fn(params), scale=scale, **flags), X, y, cv)
        trial.set_user_attr(f"{metric}_std", float(table[metric].std()))
        if log:
            board = {col: float(table[col].mean()) for col in table.columns}
            board.update({f"{col}_std": float(table[col].std()) for col in table.columns if col != "fit_seconds"})
            log_run(
                f"{name}-trial-{trial.number}",
                params,
                board,
                tags={"etapa": "06_optimizacion", "modelo": name, "metrica_optimizada": metric},
                nested=True,
            )
        return float(table[metric].mean())

    study = optuna.create_study(
        direction=OBJETIVOS[metric], sampler=optuna.samplers.TPESampler(seed=seed),
        study_name=f"eco-score-{name}-{metric}", storage=(f"sqlite:///{Path(storage).as_posix()}" if storage else None),
        load_if_exists=True,
    )
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    done = len([t for t in study.trials if t.state.is_finished()])
    remaining = max(n_trials - done, 0)
    if done:
        print(f"  {name}: se reanuda el estudio ({done} ensayos ya hechos, faltan {remaining})")
    if log:
        with mlflow.start_run(run_name=f"optuna-{name}") as parent:
            study.optimize(objective, n_trials=remaining)
            mlflow.log_metric(f"best_{metric}", study.best_value)
            mlflow.log_params({f"best_{k}": v for k, v in study.best_params.items()})
            mlflow.set_tags({"etapa": "06_optimizacion", "modelo": name, "metrica_optimizada": metric})
            study.set_user_attr("mlflow_parent_run_id", parent.info.run_id)
        study.set_user_attr("metric", metric)
    else:
        study.optimize(objective, n_trials=remaining)
    return study


def _rows_by_group(groups) -> np.ndarray:
    """Índices de filas agrupados por entidad (prestatario)."""
    groups = np.asarray(groups)
    return pd.Series(np.arange(len(groups))).groupby(groups).apply(lambda s: s.to_numpy()).to_numpy()


def pr_auc(y_true, proba) -> float:
    """AUC-PR de impago; acepta la matriz de `predict_proba` o solo la probabilidad de impago."""
    return float(average_precision_score(y_true, default_probability(proba)))


def _as_matrix(proba) -> np.ndarray:
    """Matriz (n x 2) para la regla de costo, desde la matriz de `predict_proba` o solo P(impago)."""
    p_default = default_probability(proba)
    return np.column_stack([1 - p_default, p_default])


def bootstrap_cost_difference(y_true, proba_a, proba_b, groups, n_boot: int = 1000, seed: int = RANDOM_STATE):
    """Diferencia de costo (A menos B) con intervalo del 95 %, remuestreando PRESTATARIOS completos.

    Remuestrear filas sería otra fuga: los préstamos de un prestatario no son independientes.
    Un valor negativo significa que A cuesta menos que B.
    """
    y_true = np.asarray(y_true)
    cost_a = COST_MATRIX[y_true, decide_min_cost(_as_matrix(proba_a))]
    cost_b = COST_MATRIX[y_true, decide_min_cost(_as_matrix(proba_b))]
    per_member = pd.DataFrame({"g": np.asarray(groups), "diff": cost_a - cost_b}).groupby("g")["diff"].agg(["sum", "count"])
    sums, counts = per_member["sum"].to_numpy(), per_member["count"].to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(sums), size=(n_boot, len(sums)))
    boot = sums[idx].sum(axis=1) / counts[idx].sum(axis=1)
    return float(sums.sum() / counts.sum()), float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def bootstrap_metric_ci(y_true, proba, groups, metric_fn=pr_auc, n_boot: int = 300, seed: int = RANDOM_STATE):
    """Una métrica con su intervalo del 95 %, remuestreando PRESTATARIOS completos (no filas).

    `metric_fn(y_true, proba)` devuelve un número; por defecto AUC-PR. Devuelve (valor, límite inferior, límite superior).
    """
    y_true, proba = np.asarray(y_true), np.asarray(proba)
    index_by_group = _rows_by_group(groups)
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(n_boot):
        rows = np.concatenate(index_by_group[rng.integers(0, len(index_by_group), len(index_by_group))])
        values.append(metric_fn(y_true[rows], proba[rows]))
    return float(metric_fn(y_true, proba)), float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))


def bootstrap_metric_difference(y_true, proba_a, proba_b, groups, metric_fn=pr_auc, n_boot: int = 300,
                                seed: int = RANDOM_STATE):
    """Diferencia de una métrica (A menos B) con intervalo del 95 %, remuestreando PRESTATARIOS completos.

    `metric_fn(y_true, proba)` devuelve un número; por defecto AUC-PR. Positivo = A obtiene la métrica mayor (para
    métricas donde más es mejor).
    """
    y_true, proba_a, proba_b = np.asarray(y_true), np.asarray(proba_a), np.asarray(proba_b)
    index_by_group = _rows_by_group(groups)
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        rows = np.concatenate(index_by_group[rng.integers(0, len(index_by_group), len(index_by_group))])
        diffs.append(metric_fn(y_true[rows], proba_a[rows]) - metric_fn(y_true[rows], proba_b[rows]))
    full = metric_fn(y_true, proba_a) - metric_fn(y_true, proba_b)
    return float(full), float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))
