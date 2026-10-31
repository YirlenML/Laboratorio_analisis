"""Partición de datos por prestatario (`MemberKey`).

7.028 prestatarios tienen varios préstamos en la población a modelar. Si se parte por fila, sus préstamos
caen a ambos lados y la métrica sale inflada (fuga de información). Aquí **todas** las particiones respetan
al prestatario completo y se estratifican por `is_default` para conservar la proporción de impagos.
"""
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from proyecto.config import GROUP_COL, RANDOM_STATE, TARGET, TEST_SIZE


def split_by_member(df: pd.DataFrame, test_size: float = TEST_SIZE, seed: int = RANDOM_STATE):
    """Separa entrenamiento y prueba sin repartir a ningún prestatario entre los dos.

    Usa un pliegue de `StratifiedGroupKFold` con 1/test_size pliegues (20 % -> 5 pliegues).
    """
    n_splits = round(1 / test_size)
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    train_idx, test_idx = next(splitter.split(df, df[TARGET], groups=df[GROUP_COL]))
    train = df.iloc[train_idx].reset_index(drop=True)
    test = df.iloc[test_idx].reset_index(drop=True)
    assert_disjoint_members(train, test)
    return train, test


def assert_disjoint_members(*frames: pd.DataFrame) -> None:
    """Falla si algún prestatario aparece en más de una partición."""
    seen: set = set()
    for i, frame in enumerate(frames):
        members = set(frame[GROUP_COL])
        overlap = seen & members
        if overlap:
            raise AssertionError(f"{len(overlap)} prestatarios aparecen en más de una partición (partición {i})")
        seen |= members


def group_cv(n_splits: int = 5, seed: int = RANDOM_STATE) -> StratifiedGroupKFold:
    """Validación cruzada (etapas 4-6) que mantiene a cada prestatario en un solo pliegue."""
    return StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
