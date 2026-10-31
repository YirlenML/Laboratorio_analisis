import numpy as np
import pandas as pd

from proyecto.features.engineering import (
    CATEGORICAL_BASE,
    NUMERIC_BASE,
    PROSPER_HISTORY_COUNTS,
    add_features,
    build_preprocessor,
    feature_columns,
    to_text,
)


def _row(**kw) -> pd.DataFrame:
    base = {
        "MonthlyLoanPayment": [300.0],
        "StatedMonthlyIncome": [3000.0],
        "LoanOriginalAmount": [9000.0],
        "LoanOriginationDate": [pd.Timestamp("2010-06-24")],
        "FirstRecordedCreditLine": ["24/06/2000 0:00"],
        "ScorexChangeAtTimeOfListing": [np.nan],
        "EmploymentStatus": ["Full-time"],
        **{col: [np.nan] for col in PROSPER_HISTORY_COUNTS},
    }
    base.update(kw)
    return pd.DataFrame(base)


def test_ratios_and_credit_history():
    out = add_features(_row())
    assert out["payment_to_income"].iloc[0] == 300 / 3000
    assert out["amount_to_annual_income"].iloc[0] == 9000 / 36000
    assert abs(out["credit_history_years"].iloc[0] - 10) < 0.01
    assert out["origination_year"].iloc[0] == 2010


def test_division_by_zero_or_missing_gives_nan_not_inf():
    out = add_features(_row(StatedMonthlyIncome=[0.0], FirstRecordedCreditLine=[np.nan]))
    assert np.isnan(out["payment_to_income"].iloc[0]) and np.isnan(out["amount_to_annual_income"].iloc[0])
    assert np.isnan(out["credit_history_years"].iloc[0])
    assert not np.isinf(out.select_dtypes("number").to_numpy(dtype=float)).any()


def test_missing_prosper_history_means_no_prior_loans():
    out = add_features(_row())
    assert out["has_prior_prosper_loan"].iloc[0] == 0
    assert (out[PROSPER_HISTORY_COUNTS].iloc[0] == 0).all()
    assert np.isnan(out["ScorexChangeAtTimeOfListing"].iloc[0])  # sin préstamo previo no hay cambio de puntaje


def test_existing_prosper_history_is_kept():
    out = add_features(_row(TotalProsperLoans=[2.0], OnTimeProsperPayments=[30.0]))
    assert out["has_prior_prosper_loan"].iloc[0] == 1
    assert out["TotalProsperLoans"].iloc[0] == 2 and out["OnTimeProsperPayments"].iloc[0] == 30


def test_prosper_history_rates():
    out = add_features(_row(TotalProsperLoans=[1.0], TotalProsperPaymentsBilled=[20.0],
                            ProsperPaymentsLessThanOneMonthLate=[3.0], ProsperPaymentsOneMonthPlusLate=[1.0],
                            ProsperPrincipalBorrowed=[4000.0], ProsperPrincipalOutstanding=[1000.0]))
    assert out["prosper_late_payment_rate"].iloc[0] == 4 / 20
    assert out["prosper_outstanding_share"].iloc[0] == 1000 / 4000


def test_prosper_history_rates_are_missing_without_prior_loans():
    out = add_features(_row())  # sin historial: los conteos quedan en 0 y las tasas no se pueden calcular
    assert np.isnan(out["prosper_late_payment_rate"].iloc[0]) and np.isnan(out["prosper_outstanding_share"].iloc[0])


def test_employment_status_grouping_removes_the_2009_recoding():
    statuses = ["Employed", "Full-time", "Part-time", "Self-employed", "Not available", None, "Retired"]
    out = add_features(pd.concat([_row()] * len(statuses), ignore_index=True).assign(EmploymentStatus=statuses))
    grouped = out["employment_status_grouped"].tolist()
    assert grouped[:3] == ["Employed"] * 3 and grouped[3] == "Self-employed" and grouped[6] == "Retired"
    assert pd.isna(grouped[4]) and pd.isna(grouped[5])  # "Not available" no es una situación laboral


def test_feature_columns_exclude_and_group_employment():
    num, cat = feature_columns(use_prosper_history=True, exclude=["TotalProsperPaymentsBilled", "CurrentlyInGroup"],
                               group_employment=True)
    assert "TotalProsperPaymentsBilled" not in num and "CurrentlyInGroup" not in cat
    assert "employment_status_grouped" in cat and "EmploymentStatus" not in cat


def test_add_features_does_not_mutate_input():
    frame = _row()
    add_features(frame)
    assert "payment_to_income" not in frame.columns
    assert frame["TotalProsperLoans"].isna().all()


def test_feature_columns_toggles():
    num_ref, cat_ref = feature_columns()
    num_all, cat_all = feature_columns(
        use_climate=True, use_prosper_scores=True, use_prosper_history=True, use_ratios=True, use_year=True
    )
    assert num_ref == NUMERIC_BASE and cat_ref == CATEGORICAL_BASE
    for col in ["Precipitation_Risk_Index", "BorrowerAPR", "TotalProsperLoans", "payment_to_income", "origination_year"]:
        assert col in num_all and col not in num_ref
    assert "CreditGrade" in cat_all and "CreditGrade" not in cat_ref


def test_no_leakage_or_identifier_columns_are_features():
    num, cat = feature_columns(
        use_climate=True, use_prosper_scores=True, use_prosper_history=True, use_ratios=True, use_year=True
    )
    forbidden = {"MemberKey", "is_default", "Investors", "PercentFunded", "InvestmentFromFriendsCount",
                 "InvestmentFromFriendsAmount", "BorrowerState", "LoanStatus"}
    assert not forbidden & set(num + cat)


def test_to_text_keeps_missing_as_nan():
    out = to_text(pd.DataFrame({"code": [1, 7, 0], "flag": ["VERDADERO", None, "FALSO"]}))
    assert out["code"].tolist() == ["1", "7", "0"]  # el código de propósito se trata como categoría
    assert out["flag"].tolist()[::2] == ["VERDADERO", "FALSO"] and pd.isna(out.loc[1, "flag"])


def test_preprocessor_handles_unseen_category_and_missing():
    num, cat = feature_columns()
    train = pd.DataFrame({c: [1.0, 2.0, np.nan, 4.0] for c in num})
    for c in cat:
        train[c] = ["a", "b", "a", np.nan]
    prep = build_preprocessor().fit(train)
    new = train.iloc[:2].copy()
    for c in cat:
        new[c] = ["nunca_visto", np.nan]
    assert not np.isnan(prep.transform(new)).any()
