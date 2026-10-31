"""La regla más importante de la partición: ningún prestatario aparece en dos particiones."""
import numpy as np
import pandas as pd
import pytest

from proyecto.data.split import assert_disjoint_members, group_cv, split_by_member


@pytest.fixture
def loans() -> pd.DataFrame:
    """300 prestatarios con 1 a 4 préstamos cada uno (~30 % de impagos)."""
    rng = np.random.default_rng(0)
    members = np.repeat([f"M{i}" for i in range(300)], rng.integers(1, 5, size=300))
    return pd.DataFrame(
        {
            "MemberKey": members,
            "is_default": (rng.random(len(members)) < 0.3).astype(int),
            "x": rng.normal(size=len(members)),
        }
    )


def test_split_by_member_has_no_shared_members_and_loses_no_rows(loans):
    train, test = split_by_member(loans, test_size=0.2, seed=42)
    assert set(train["MemberKey"]).isdisjoint(set(test["MemberKey"]))
    assert len(train) + len(test) == len(loans)
    assert 0.1 < len(test) / len(loans) < 0.3


def test_split_by_member_keeps_default_rate(loans):
    train, test = split_by_member(loans, test_size=0.2, seed=42)
    assert abs(train["is_default"].mean() - test["is_default"].mean()) < 0.05


def test_split_by_member_is_reproducible(loans):
    test_a = split_by_member(loans, seed=42)[1]
    test_b = split_by_member(loans, seed=42)[1]
    pd.testing.assert_frame_equal(test_a, test_b)


def test_assert_disjoint_members_detects_row_split(loans):
    # Una partición por fila reparte prestatarios en los dos lados: la verificación debe fallar
    row_test = loans.sample(frac=0.2, random_state=42)
    row_train = loans.drop(row_test.index)
    with pytest.raises(AssertionError):
        assert_disjoint_members(row_train, row_test)


def test_group_cv_keeps_each_member_in_one_fold(loans):
    for train_idx, val_idx in group_cv(n_splits=5).split(loans, loans["is_default"], groups=loans["MemberKey"]):
        assert set(loans.iloc[train_idx]["MemberKey"]).isdisjoint(set(loans.iloc[val_idx]["MemberKey"]))
