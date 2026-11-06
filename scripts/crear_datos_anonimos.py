"""Genera las copias versionables de train y test: sin `MemberKey` y con `borrower_id`.

Requiere `data/processed/train.parquet` y `test.parquet`, que crea el notebook 03 y no se suben al repositorio.
Ejecutar desde la raíz del repo: python scripts/crear_datos_anonimos.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from proyecto.config import PROCESSED_DIR  # noqa: E402
from proyecto.data.split import anonymize_members  # noqa: E402


def main() -> None:
    train = pd.read_parquet(PROCESSED_DIR / "train.parquet")
    test = pd.read_parquet(PROCESSED_DIR / "test.parquet")
    anon_train, anon_test = anonymize_members(train, test)
    anon_train.to_parquet(PROCESSED_DIR / "train_sin_memberkey.parquet", index=False)
    anon_test.to_parquet(PROCESSED_DIR / "test_sin_memberkey.parquet", index=False)
    print(f"Creados: train {anon_train.shape} y test {anon_test.shape}")


if __name__ == "__main__":
    main()
