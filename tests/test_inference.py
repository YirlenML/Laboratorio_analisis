"""Pruebas del esquema y de la inferencia, con un modelo de juguete (no necesitan tus datos).

Si renombraste el paquete `proyecto`, cambia los imports de arriba. Estas pruebas son un ejemplo de
qué comprobar; cuando tengas tu modelo real, añade una prueba con una fila de tus datos.
"""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from proyecto.config import INPUT_LABELS, PLAUSIBLE_RANGE
from proyecto.features.engineering import add_features
from proyecto.inference.predict import (
    FEATURE_STEP_NUMERIC,
    FEATURE_STEP_TEXT,
    InputValidationError,
    decide_min_cost,
    fill_unused_columns,
    form_columns,
    input_frame,
    predict_with_scores,
    required_columns,
    validate_inputs,
)
from proyecto.inference.schema import build_schema, load_schema

NUMERIC, CATEGORICAL, CLASSES = ["edad", "ingreso"], ["ciudad"], ["bajo", "alto"]
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def data() -> pd.DataFrame:
    rng = np.random.default_rng(0)
    n = 200
    df = pd.DataFrame({
        "edad": rng.integers(18, 70, n),
        "ingreso": rng.normal(2000, 500, n).round(1),
        "ciudad": rng.choice(["norte", "sur", "centro"], n),
    })
    df["y"] = ((df["ingreso"] > 2000) & (df["edad"] > 35)).astype(int)
    return df


@pytest.fixture(scope="module")
def model(data) -> Pipeline:
    prep = ColumnTransformer([
        ("num", SimpleImputer(strategy="median"), NUMERIC),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="most_frequent")), ("oh", OneHotEncoder(handle_unknown="ignore"))]), CATEGORICAL),
    ])
    return Pipeline([("prep", prep), ("clf", LogisticRegression(max_iter=500))]).fit(data[NUMERIC + CATEGORICAL], data["y"])


def make_schema(data, **kwargs) -> dict:
    return build_schema(data, NUMERIC, CATEGORICAL, CLASSES, valid_range={"edad": (0, 120)}, **kwargs)


def row(**overrides) -> pd.DataFrame:
    base = {"edad": 40, "ingreso": 2500.0, "ciudad": "norte"}
    base.update(overrides)
    return pd.DataFrame([base])


def test_build_schema_saves_and_reloads(data, tmp_path):
    path = tmp_path / "input_schema.json"
    schema = make_schema(data, path=path)
    assert path.exists() and load_schema(path) == json.loads(path.read_text(encoding="utf-8"))
    assert schema["numeric"] == NUMERIC and schema["class_names"] == CLASSES
    assert set(schema["categories"]["ciudad"]) == {"norte", "sur", "centro"}
    assert "edad" in schema["integer_columns"] and "ingreso" not in schema["integer_columns"]
    assert schema["observed_range"]["edad"][0] >= 18


def test_build_schema_rejects_bad_cost_matrix(data):
    with pytest.raises(ValueError, match="cost_matrix"):
        make_schema(data, cost_matrix=[[0, 1, 2], [1, 0, 2]])


def test_build_schema_rejects_missing_column(data):
    with pytest.raises(ValueError, match="Faltan columnas"):
        build_schema(data.drop(columns=["ingreso"]), NUMERIC, CATEGORICAL, CLASSES)


def test_valid_row_has_no_errors(data):
    assert validate_inputs(row(), make_schema(data)) == []


def test_missing_column_is_an_error_naming_it(data):
    with pytest.raises(InputValidationError, match="ingreso"):
        validate_inputs(row().drop(columns=["ingreso"]), make_schema(data))


def test_impossible_value_is_refused_not_predicted(data, model):
    with pytest.raises(InputValidationError, match="edad"):
        predict_with_scores(row(edad=-500), model, make_schema(data))


def test_non_numeric_value_is_an_error(data):
    with pytest.raises(InputValidationError, match="ingreso"):
        validate_inputs(row(ingreso="mucho"), make_schema(data))


def test_unseen_category_and_out_of_range_are_warnings(data):
    warnings = validate_inputs(row(ciudad="luna", ingreso=99999.0), make_schema(data))
    assert any("ciudad" in w for w in warnings) and any("ingreso" in w for w in warnings)


def test_error_uses_the_spanish_label_of_the_field(data):
    schema = make_schema(data, labels={"edad": "Edad (años)"})
    with pytest.raises(InputValidationError) as error:
        validate_inputs(row(edad=-500), schema)
    assert str(error.value) == "Edad (años): debe estar entre 0 y 120"


def test_error_without_a_label_falls_back_to_the_column_name(data):
    with pytest.raises(InputValidationError, match="^edad: debe estar entre 0 y 120$"):
        validate_inputs(row(edad=-500), make_schema(data))


def test_non_numeric_error_uses_the_label(data):
    schema = make_schema(data, labels={"ingreso": "Ingreso mensual"})
    with pytest.raises(InputValidationError, match="Ingreso mensual: hay valores que no son números"):
        validate_inputs(row(ingreso="mucho"), schema)


def test_error_numbers_are_not_in_scientific_notation(data):
    schema = make_schema(data)
    schema["valid_range"]["ingreso"] = [1.0, 100_000_000.0]
    with pytest.raises(InputValidationError) as error:
        validate_inputs(row(ingreso=-5.0), schema)
    assert str(error.value) == "ingreso: debe estar entre 1 y 100.000.000"


def test_error_keeps_the_decimals_of_the_limit_with_a_comma(data):
    schema = make_schema(data)
    schema["valid_range"]["ingreso"] = [0.0, 10.01]
    with pytest.raises(InputValidationError, match="debe estar entre 0 y 10,01"):
        validate_inputs(row(ingreso=11.0), schema)


def test_error_names_every_invalid_field(data):
    schema = make_schema(data, labels={"edad": "Edad (años)", "ingreso": "Ingreso mensual"})
    schema["valid_range"]["ingreso"] = [0.0, 1_000_000.0]
    with pytest.raises(InputValidationError) as error:
        validate_inputs(row(edad=-500, ingreso=-1.0), schema)
    assert str(error.value) == "Edad (años): debe estar entre 0 y 120; Ingreso mensual: debe estar entre 0 y 1.000.000"


def test_warnings_use_the_label_and_readable_numbers(data):
    schema = make_schema(data, labels={"ingreso": "Ingreso mensual", "ciudad": "Ciudad"})
    schema["observed_range"]["ingreso"] = [0.0, 1_500_000.0]
    warnings = validate_inputs(row(ingreso=2_000_000.0, ciudad="luna"), schema)
    assert "Ciudad: categoría no vista en el entrenamiento (luna)" in warnings
    assert "Ingreso mensual: fuera del rango visto en el entrenamiento (0 a 1.500.000)" in warnings


def test_value_at_the_limit_of_the_range_is_accepted(data):
    schema = make_schema(data)
    assert validate_inputs(row(edad=0), schema) == validate_inputs(row(edad=120), schema)


def test_predict_returns_probabilities_that_sum_to_one(data, model):
    result = predict_with_scores(row(), model, make_schema(data))
    assert np.isclose(result[["proba_bajo", "proba_alto"]].sum(axis=1).iloc[0], 1.0)
    assert result["decision"].iloc[0] in CLASSES and "expected_cost" not in result.columns


def test_missing_values_are_accepted_by_the_pipeline(data, model):
    result = predict_with_scores(row(ingreso=np.nan, ciudad=np.nan), model, make_schema(data))
    assert len(result) == 1


def test_cost_matrix_changes_the_decision_when_unsure():
    proba = np.array([[0.45, 0.55]])   # la clase 1 es apenas más probable
    assert decide_min_cost(proba, [[0, 1], [10, 0]])[0] == 1                 # errar la clase 1 cuesta 10: decide 1
    assert decide_min_cost(proba, [[0, 10], [1, 0]])[0] == 0                 # ahora errar la clase 0 cuesta 10: decide 0


def test_cost_matrix_adds_expected_cost_and_review_flag(data, model):
    schema = make_schema(data, cost_matrix=[[0, 1], [50, 0]])   # dejar pasar un "alto" como "bajo" cuesta 50
    result = predict_with_scores(row(edad=30, ingreso=1900.0), model, schema)
    assert "expected_cost" in result.columns and result["expected_cost"].iloc[0] >= 0


def test_app_module_imports_without_launching_streamlit():
    pytest.importorskip("streamlit")
    spec = importlib.util.spec_from_file_location("app_streamlit", ROOT / "app" / "streamlit_app.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)   # no ejecuta main(): solo importa
    assert callable(module.main) and module.UNKNOWN == "(no sé)"


def test_required_columns_exclude_identifiers():
    numeric, text = required_columns()
    columns = numeric + text
    assert len(columns) == len(set(columns))
    assert {"MemberKey", "borrower_id", "is_default", "BorrowerState", "has_prior_prosper_loan"}.isdisjoint(columns)
    assert "EmploymentStatus" in columns and "employment_status_grouped" not in columns


def test_input_frame_converts_types_and_keeps_missing_values():
    numeric, text = required_columns()
    df = pd.DataFrame({**{c: [1, 2] for c in numeric}, **{c: ["a", None] for c in text}, "borrower_id": [7, 8]})
    df["ListingCategory (numeric)"] = [3, 4]
    out = input_frame(df)
    assert list(out.columns) == numeric + text
    assert all(out[c].dtype == "float64" for c in numeric)
    assert out["CreditGrade"].tolist() == ["a", None]
    assert out["ListingCategory (numeric)"].tolist() == ["3", "4"]
    assert df["Term"].dtype != "float64"  # no modifica el original


def test_build_schema_keeps_examples(data):
    schema = make_schema(data, examples={"perfil": {"edad": 40}})
    assert schema["examples"] == {"perfil": {"edad": 40}}
    assert make_schema(data)["examples"] == {}


def test_form_columns_leave_out_the_four_unused_columns():
    numeric, categorical = form_columns()
    assert len(numeric) + len(categorical) == 39
    assert set(FEATURE_STEP_NUMERIC + FEATURE_STEP_TEXT).isdisjoint(numeric + categorical)


def test_every_form_column_has_a_label_and_every_numeric_a_possible_range():
    numeric, categorical = form_columns()
    assert set(INPUT_LABELS) == set(numeric + categorical)
    assert set(PLAUSIBLE_RANGE) == set(numeric)
    assert all(low < high for low, high in PLAUSIBLE_RANGE.values())


def test_fill_unused_columns_adds_only_what_is_missing():
    df = pd.DataFrame({"Term": [36], "LoanOriginationDate": ["2012-04-19"]})
    out = fill_unused_columns(df)
    assert out["LoanOriginationDate"].tolist() == ["2012-04-19"]  # si ya viene, se respeta
    assert out["FirstRecordedCreditLine"].isna().all() and out["TotalProsperPaymentsBilled"].isna().all()
    assert "FirstRecordedCreditLine" not in df.columns  # no modifica el original


def test_add_features_accepts_a_form_row_with_the_unused_columns_empty():
    numeric, categorical = form_columns()
    form_row = pd.DataFrame([{**{c: 1.0 for c in numeric}, **{c: "x" for c in categorical}}])
    out = add_features(fill_unused_columns(form_row))
    assert len(out) == 1 and out["has_prior_prosper_loan"].iloc[0] == 1.0
