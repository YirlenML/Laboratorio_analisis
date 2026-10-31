"""Una prueba por regla de limpieza (especificaciones/03-preprocesamiento.md, sección 3)."""
import numpy as np
import pandas as pd
import pytest

from proyecto.config import LEAKAGE_COLUMNS, LISTING_KEY_COLUMNS
from proyecto.data.cleaning import (
    add_climate_index,
    build_target,
    clean,
    clean_income_range,
    drop_duplicate_listings,
    drop_leakage_columns,
    drop_missing_state,
    load_raw,
    mark_impossible_values,
    parse_origination_date,
    repair_monthly_payment,
)


def _raw(**overrides) -> pd.DataFrame:
    """Cuatro préstamos crudos con lo mínimo para correr `clean`; cada prueba sobrescribe lo que necesita."""
    base = {
        "ListingKey": ["L1", "L1", "L2", "L3"],
        "ListingNumber": [1, 1, 2, 3],
        "LoanKey": ["K1", "K1", "K2", "K3"],
        "LoanNumber": [10, 10, 20, 30],
        "MemberKey": ["M1", "M1", "M2", "M3"],
        "Occupation": ["Analyst", "Analyst", "Other", "Teacher"],
        "LoanStatus": ["Completed", "Completed", "Chargedoff", "Current"],
        "BorrowerState": ["FL", "FL", "WA", "UT"],
        "IncomeRange": ["$0 ", "$0 ", "$25,000-49,999", "Not displayed"],
        "StatedMonthlyIncome": [0.0, 0.0, 3000.0, 4000.0],
        "CreditScoreRangeLower": [700.0, 700.0, 0.0, 650.0],
        "CreditScoreRangeUpper": [719.0, 719.0, 19.0, 669.0],
        "BorrowerRate": [0.12, 0.12, 0.2, 0.15],
        "Term": [36, 36, 36, 60],
        "LoanOriginalAmount": [4000, 4000, 1000, 5000],
        "MonthlyLoanPayment": [132.86, 132.86, 0.0, 118.95],
        "LoanOriginationDate": ["24/06/2010 0:00", "24/06/2010 0:00", "9/08/2007 0:00", "1/01/2013 0:00"],
        "ListingCreationDate": ["09:29.3"] * 4,
        "DateCreditPulled": ["09:29.3"] * 4,
    }
    for col in LEAKAGE_COLUMNS:
        base[col] = [0.0] * 4
    base.update(overrides)
    return pd.DataFrame(base)


def test_load_raw_drops_group_key(tmp_path):
    path = tmp_path / "raw.csv"
    pd.DataFrame({"GroupKey": ["G1"], "MemberKey": ["M1"]}).to_csv(path, sep=";", index=False)
    assert list(load_raw(path).columns) == ["MemberKey"]


def test_build_target():
    statuses = ["Completed", "Chargedoff", "Defaulted", "Current", "Past Due (1-15 days)", "Cancelled"]
    out = build_target(pd.DataFrame({"LoanStatus": statuses}))
    assert out["is_default"].tolist() == [0, 1, 1]  # solo quedan los tres terminados
    assert "LoanStatus" not in out.columns


def test_drop_duplicate_listings():
    out = drop_duplicate_listings(pd.DataFrame({"ListingKey": ["A", "A", "B"], "ProsperScore": [5, 7, 3]}))
    assert out["ListingKey"].tolist() == ["A", "B"]
    assert out["ProsperScore"].tolist() == [5, 3]  # se conserva la primera fila


def test_drop_missing_state():
    out = drop_missing_state(pd.DataFrame({"BorrowerState": ["CA", None, np.nan, "NY"]}))
    assert out["BorrowerState"].tolist() == ["CA", "NY"]


def test_drop_leakage_columns():
    out = drop_leakage_columns(pd.DataFrame({col: [1] for col in LEAKAGE_COLUMNS + ["Term"]}))
    assert list(out.columns) == ["Term"]
    assert len(LEAKAGE_COLUMNS) == 12


def test_clean_income_range():
    values = ["$0 ", " Not employed", "Not displayed", "$100,000+"]
    out = clean_income_range(pd.DataFrame({"IncomeRange": values}))
    assert out["IncomeRange"].tolist() == ["$0", "Not employed", "Not displayed", "$100,000+"]
    # "Not displayed" es una categoría propia, no vacío ni "$0"
    assert out["IncomeRange"].notna().all()


@pytest.mark.parametrize("bad", ["Not Employed", "$0-1", None])
def test_clean_income_range_rejects_unknown_values(bad):
    with pytest.raises(ValueError):
        clean_income_range(pd.DataFrame({"IncomeRange": ["$0", bad]}))


def test_mark_impossible_values():
    df = pd.DataFrame(
        {
            "CreditScoreRangeLower": [700.0, 0.0, 500.0, 600.0],
            "CreditScoreRangeUpper": [719.0, 19.0, 519.0, 619.0],
            "StatedMonthlyIncome": [5000.0, 250_000.0, 0.0, 0.0],
            "IncomeRange": ["$50,000-74,999", "$100,000+", "$0", "Not displayed"],
        }
    )
    out = mark_impossible_values(df)
    assert out["CreditScoreRangeLower"].isna().tolist() == [False, True, False, False]
    assert out["CreditScoreRangeUpper"].isna().tolist() == [False, True, False, False]
    # > 100.000 es imposible; 0 con "$0" es coherente; 0 con "Not displayed" no lo es
    assert out["StatedMonthlyIncome"].isna().tolist() == [False, True, False, True]
    assert out.loc[2, "StatedMonthlyIncome"] == 0


def test_repair_monthly_payment():
    df = pd.DataFrame(
        {
            "BorrowerRate": [0.12, 0.12, 0.0],
            "Term": [36, 36, 12],
            "LoanOriginalAmount": [4000, 4000, 1200],
            "MonthlyLoanPayment": [140.0, 0.0, 0.0],
        }
    )
    out = repair_monthly_payment(df)
    assert out.loc[0, "MonthlyLoanPayment"] == 140.0  # un valor real no se toca
    assert out.loc[1, "MonthlyLoanPayment"] == pytest.approx(132.86, abs=0.01)  # cuota fija al 12 % anual
    assert out.loc[2, "MonthlyLoanPayment"] == pytest.approx(100.0)  # tasa 0 -> monto / plazo


def test_parse_origination_date():
    df = pd.DataFrame(
        {
            "LoanOriginationDate": ["24/06/2010 0:00", "9/08/2007 0:00"],
            "ListingCreationDate": ["09:29.3", "10:11.2"],
            "DateCreditPulled": ["09:29.3", "1/02/2007 10:00"],
        }
    )
    out = parse_origination_date(df)
    assert out["LoanOriginationDate"].tolist() == [pd.Timestamp("2010-06-24"), pd.Timestamp("2007-08-09")]
    assert list(out.columns) == ["LoanOriginationDate"]


def test_add_climate_index():
    out = add_climate_index(pd.DataFrame({"BorrowerState": ["FL", "UT", "WA"]}))
    assert out["Precipitation_Risk_Index"].tolist() == [94.2, 10.5, 50.0]


def test_no_personal_columns():
    out = clean(_raw())
    for col in LISTING_KEY_COLUMNS + ["GroupKey", "Occupation"]:
        assert col not in out.columns
    assert "MemberKey" in out.columns  # se conserva solo para partir


def test_clean_end_to_end():
    out = clean(_raw())
    # L1 repetido -> una fila; L3 es "Current" (sin resultado) -> fuera
    assert out["MemberKey"].tolist() == ["M1", "M2"]
    assert out["is_default"].tolist() == [0, 1]
    assert out.loc[1, "MonthlyLoanPayment"] > 0
    assert np.isnan(out.loc[1, "CreditScoreRangeLower"])
    assert out["Precipitation_Risk_Index"].tolist() == [94.2, 50.0]
    assert not set(LEAKAGE_COLUMNS) & set(out.columns)
