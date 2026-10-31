"""Limpieza del dataset crudo de Prosper.

Cada función implementa una regla de `especificaciones/03-preprocesamiento.md` (sección 3), que a su
vez sale de las decisiones del EDA (`reports/01_eda.md`). Las reglas 11 y 12 tratan los valores atípicos
que el EDA dejó abiertos (ver `reports/03_preprocesamiento.md`).

La limpieza no imputa con medias ni medianas: eso depende del entrenamiento y va dentro del `Pipeline`
(etapa 4). Aquí solo se marca como vacío lo imposible y se repara lo que se deduce con una regla exacta.
"""
import numpy as np
import pandas as pd

from proyecto.config import (
    CLIMATE_DEFAULT,
    CLIMATE_INDEX_COL,
    CLIMATE_RISK_MATRIX,
    DAMAGED_DATE_COLUMNS,
    DEFAULT_STATUSES,
    GROUP_KEY_COLUMNS,
    INCOME_RANGE_CATEGORIES,
    LEAKAGE_COLUMNS,
    LISTING_KEY_COLUMNS,
    MAX_MONTHLY_INCOME,
    ORIGINATION_DATE_FORMAT,
    PAID_STATUSES,
    QUASI_IDENTIFIER_COLUMNS,
    RAW_CSV,
    RAW_SEP,
    TARGET,
    ZERO_INCOME_RANGES,
)


def load_raw(path=RAW_CSV) -> pd.DataFrame:
    """Lee el CSV crudo (separador ';') y quita `GroupKey` en el primer paso."""
    return pd.read_csv(path, sep=RAW_SEP, low_memory=False).drop(columns=GROUP_KEY_COLUMNS)


def build_target(df: pd.DataFrame) -> pd.DataFrame:
    """Regla 1: deja solo préstamos terminados y crea `is_default` (1 = Chargedoff/Defaulted, 0 = Completed)."""
    finished = df[df["LoanStatus"].isin(DEFAULT_STATUSES + PAID_STATUSES)].copy()
    finished[TARGET] = finished["LoanStatus"].isin(DEFAULT_STATUSES).astype(int)
    return finished.drop(columns=["LoanStatus"])


def drop_duplicate_listings(df: pd.DataFrame) -> pd.DataFrame:
    """Regla 2: una fila por `ListingKey` (se conserva la primera)."""
    return df.drop_duplicates(subset="ListingKey", keep="first")


def drop_missing_state(df: pd.DataFrame) -> pd.DataFrame:
    """Regla 4: elimina filas sin `BorrowerState` (sin estado no hay índice climático)."""
    return df[df["BorrowerState"].notna()]


def drop_personal_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Sección 2: quita las llaves del préstamo y la ocupación. `MemberKey` se conserva solo para partir."""
    return df.drop(columns=LISTING_KEY_COLUMNS + QUASI_IDENTIFIER_COLUMNS, errors="ignore")


def drop_leakage_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Regla 5: quita las 12 columnas que solo se conocen después de otorgar el préstamo."""
    return df.drop(columns=LEAKAGE_COLUMNS, errors="ignore")


def clean_income_range(df: pd.DataFrame) -> pd.DataFrame:
    """Regla 6: quita espacios de `IncomeRange` y exige una de las 8 categorías fijas; otro valor -> error."""
    df = df.copy()
    income = df["IncomeRange"].astype("string").str.strip()
    unknown = set(income.dropna().unique()) - set(INCOME_RANGE_CATEGORIES)
    if unknown or income.isna().any():
        raise ValueError(f"IncomeRange con valores no esperados: {sorted(unknown) or 'vacíos'}")
    df["IncomeRange"] = pd.Categorical(income, categories=INCOME_RANGE_CATEGORIES)
    return df


def mark_impossible_values(df: pd.DataFrame) -> pd.DataFrame:
    """Reglas 7 y 12: convierte en vacío los valores imposibles.

    - `CreditScoreRangeLower` = 0 -> vacío, y también su `CreditScoreRangeUpper` (que en esas filas vale 19).
    - `StatedMonthlyIncome` > 100.000 USD/mes -> vacío.
    - `StatedMonthlyIncome` = 0 cuando `IncomeRange` dice que sí hay ingresos (no es `$0` ni `Not employed`) -> vacío.
    """
    df = df.copy()
    zero_score = df["CreditScoreRangeLower"] == 0
    df.loc[zero_score, ["CreditScoreRangeLower", "CreditScoreRangeUpper"]] = np.nan

    income = df["StatedMonthlyIncome"]
    zero_income_incoherent = (income == 0) & ~df["IncomeRange"].isin(ZERO_INCOME_RANGES)
    df["StatedMonthlyIncome"] = income.mask((income > MAX_MONTHLY_INCOME) | zero_income_incoherent)
    return df


def repair_monthly_payment(df: pd.DataFrame) -> pd.DataFrame:
    """Regla 11: `MonthlyLoanPayment` = 0 se recalcula con la fórmula de la cuota fija.

    cuota = monto · r / (1 − (1 + r)^−plazo), con r = `BorrowerRate` / 12. Las tres variables se conocen al
    otorgar el préstamo, y en las filas con cuota la fórmula coincide con el dato (error mediano 0,001 %).
    """
    df = df.copy()
    rate = df["BorrowerRate"] / 12
    term = df["Term"]
    amount = df["LoanOriginalAmount"]
    with np.errstate(divide="ignore", invalid="ignore"):
        formula = np.where(rate > 0, amount * rate / (1 - (1 + rate) ** -term), amount / term)
    zero_payment = df["MonthlyLoanPayment"] == 0
    df["MonthlyLoanPayment"] = df["MonthlyLoanPayment"].where(~zero_payment, np.round(formula, 2))
    return df


def parse_origination_date(df: pd.DataFrame) -> pd.DataFrame:
    """Regla 9: lee `LoanOriginationDate` (dd/mm/aaaa hh:mm) y quita las dos fechas dañadas."""
    df = df.copy()
    df["LoanOriginationDate"] = pd.to_datetime(df["LoanOriginationDate"], format=ORIGINATION_DATE_FORMAT)
    return df.drop(columns=DAMAGED_DATE_COLUMNS, errors="ignore")


def add_climate_index(df: pd.DataFrame) -> pd.DataFrame:
    """Regla 10: agrega el índice climático (supuesto académico): 10 estados con valor, el resto 50,0."""
    df = df.copy()
    df[CLIMATE_INDEX_COL] = df["BorrowerState"].map(CLIMATE_RISK_MATRIX).fillna(CLIMATE_DEFAULT).astype(float)
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica todas las reglas en orden y devuelve la población a modelar."""
    df = build_target(df)
    df = drop_duplicate_listings(df)
    df = drop_missing_state(df)
    df = drop_personal_columns(df)
    df = drop_leakage_columns(df)
    df = clean_income_range(df)
    df = mark_impossible_values(df)
    df = repair_monthly_payment(df)
    df = parse_origination_date(df)
    df = add_climate_index(df)
    return df.reset_index(drop=True)
