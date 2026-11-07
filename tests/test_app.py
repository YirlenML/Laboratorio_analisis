"""Pruebas de la app completa, sin navegador, con el modelo y el esquema reales.

Para el caso límite se busca el dato con el modelo y los ejemplos del esquema: no se usa el conjunto de prueba.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from proyecto.inference.predict import load_model, predict_with_scores  # noqa: E402
from proyecto.inference.presentation import (  # noqa: E402
    ACTION_NO_REVIEW,
    ACTION_REVIEW,
    TYPICAL_VALUES_WARNING,
    format_percent,
    optional_groups,
    performance_lines,
    reduced_input_note,
)
from proyecto.inference.schema import load_schema  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "streamlit_app.py"
BLANK, UNKNOWN = "Formulario en blanco", "(no sé)"
PAID, DEFAULTED = "Préstamo real que se pagó", "Préstamo real que cayó en impago"
SCORE = "CreditScoreRangeLower"
ACTIONS = {ACTION_REVIEW, ACTION_NO_REVIEW}


@pytest.fixture(scope="module")
def schema() -> dict:
    return load_schema(ROOT / "models" / "input_schema.json")


@pytest.fixture(scope="module")
def model():
    return load_model(ROOT / "models" / "model.joblib")


def open_app(example: str = BLANK) -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    if example != BLANK:
        at.radio[0].set_value(example).run()
        assert not at.exception
    return at


def evaluate(at: AppTest) -> AppTest:
    at.button[0].click().run()
    assert not at.exception
    return at


def number(at: AppTest, column: str, example: str):
    return at.number_input(key=f"{column}|{example}")


def category(at: AppTest, column: str, example: str):
    return at.selectbox(key=f"{column}|{example}")


def markdown_outside_expanders(at: AppTest) -> list[str]:
    inside = [m.value for expander in at.expander for m in expander.markdown]
    return [m.value for m in at.markdown if m.value not in inside]


def metrics(at: AppTest) -> dict:
    return {metric.label: metric.value for metric in at.metric}


def recommendation(at: AppTest) -> str | None:
    return metrics(at).get("Recomendación")


def all_text(at: AppTest) -> str:
    parts = [e.value for e in [*at.title, *at.subheader, *at.markdown, *at.caption, *at.info, *at.warning, *at.error]]
    parts = [part for part in parts if part != "--"]
    return "\n".join([*parts, *(str(m.value) for m in at.metric)])


def check_form_shows(at: AppTest, schema: dict, values: dict, example: str) -> None:
    """Los 39 campos muestran `values`; lo que no está en `values` queda vacío."""
    for column in schema["numeric"]:
        assert number(at, column, example).value == values.get(column), column
    for column in schema["categorical"]:
        expected = values.get(column)
        assert category(at, column, example).value == (UNKNOWN if expected is None else expected), column


def direct_probability(values: dict, model, schema: dict) -> float:
    """Lo que dice el modelo sin pasar por la pantalla."""
    row = {column: values.get(column, np.nan) for column in schema["numeric"] + schema["categorical"]}
    return float(predict_with_scores(pd.DataFrame([row]), model, schema)["proba_impago"].iloc[0])


def find_crossing(example: str, model, schema: dict) -> tuple[str, float]:
    """Busca un solo dato numérico que, dentro de lo visto en el entrenamiento, cambie la recomendación del ejemplo."""
    base = schema["examples"][example]
    crosses = direct_probability(base, model, schema) > 0.2
    candidates = []
    for column in schema["numeric"]:
        low, high = schema["observed_range"][column]
        for value in np.linspace(low, high, 21):
            value = float(round(value)) if column in schema["integer_columns"] else float(value)
            candidates.append((column, value))
    rows = pd.DataFrame([{**base, column: value} for column, value in candidates])
    proba = predict_with_scores(rows, model, schema)["proba_impago"].to_numpy()
    # El más cercano al 20 %: la demo muestra el cruce sin datos extremos
    flips = [(abs(p - 0.2), c) for p, c in zip(proba, candidates) if (p > 0.2) != crosses]
    assert flips, f"Ningún dato cruza el umbral en {example}"
    return min(flips, key=lambda item: item[0])[1]


def clean_copy(tmp_path: Path, *model_files: str) -> Path:
    """Copia a una carpeta nueva solo `app/`, `src/` y los archivos de `models/` que se pidan."""
    copy = tmp_path / "copia"
    ignore = shutil.ignore_patterns("__pycache__")
    shutil.copytree(ROOT / "app", copy / "app", ignore=ignore)
    shutil.copytree(ROOT / "src", copy / "src", ignore=ignore)
    (copy / "models").mkdir()
    for name in model_files:
        shutil.copy2(ROOT / "models" / name, copy / "models" / name)
    return copy


# Corre en otro proceso: aquí `proyecto` ya está cargado y taparía una dependencia de la carpeta original
COPY_SCRIPT = """
import json, sys
from pathlib import Path
from streamlit.testing.v1 import AppTest
at = AppTest.from_file(str(Path("app/streamlit_app.py").resolve()), default_timeout=60).run()
report = {"exception": [e.value for e in at.exception], "errors": [e.value for e in at.error]}
if at.button:
    at.radio[0].set_value("Préstamo real que se pagó").run()
    at.button[0].click().run()
    report["exception"] += [e.value for e in at.exception]
    report["metrics"] = {m.label: m.value for m in at.metric}
    report["package"] = sys.modules["proyecto"].__file__
report["uses_mlflow"] = "mlflow" in sys.modules
print("RESULT" + json.dumps(report))
"""


def run_in_copy(copy: Path) -> dict:
    secret_free = {k: v for k, v in os.environ.items() if "DATABRICKS" not in k and k != "PYTHONPATH"}
    done = subprocess.run(
        [sys.executable, "-c", COPY_SCRIPT], cwd=copy, env={**secret_free, "PYTHONUTF8": "1"},
        capture_output=True, text=True, encoding="utf-8", timeout=180,
    )
    assert done.returncode == 0, done.stderr
    line = next(line for line in done.stdout.splitlines() if line.startswith("RESULT"))
    return json.loads(line.removeprefix("RESULT"))


# --- Historia 1: evaluar una solicitud ---


def test_app_opens_without_exceptions():
    at = open_app()
    assert at.title[0].value == "Eco-Score · Riesgo de impago"
    assert "La decisión final es de una persona." in all_text(at)
    assert at.button[0].label == "Evaluar"


@pytest.mark.parametrize("example", [PAID, DEFAULTED])
def test_evaluating_an_example_shows_a_recommendation_and_the_probability(example, model, schema):
    at = evaluate(open_app(example))
    expected = direct_probability(schema["examples"][example], model, schema)
    assert recommendation(at) in ACTIONS
    assert metrics(at)["Probabilidad de impago"] == format_percent(expected)
    assert "Se envía a revisión si la probabilidad de impago supera 20 %." in all_text(at)


def test_the_two_examples_give_the_recommendation_of_the_frozen_rule():
    assert recommendation(evaluate(open_app(PAID))) == ACTION_NO_REVIEW
    assert recommendation(evaluate(open_app(DEFAULTED))) == ACTION_REVIEW


@pytest.mark.parametrize("example", [BLANK, PAID, DEFAULTED])
def test_screen_avoids_forbidden_wording(example):
    at = evaluate(open_app(example))
    text = all_text(at).lower()
    for forbidden in ["rechazad", "está seguro", "needs_review", "matriz de costos", "resultado sugerido"]:
        assert forbidden not in text
    assert metrics(at)["Recomendación"] in ACTIONS  # nunca `pagó` ni `impago` como decisión


def test_example_result_is_not_presented_as_the_real_outcome():
    assert "no indica cómo terminó" in all_text(evaluate(open_app(DEFAULTED)))


def test_app_works_in_a_copy_with_only_its_own_files(tmp_path):
    copy = clean_copy(tmp_path, "model.joblib", "input_schema.json")
    report = run_in_copy(copy)
    assert report["exception"] == [] and report["errors"] == []
    assert report["metrics"]["Recomendación"] == ACTION_NO_REVIEW
    assert Path(report["package"]).is_relative_to(copy)
    assert report["uses_mlflow"] is False


@pytest.mark.parametrize(
    ("present", "absent"),
    [("input_schema.json", "model.joblib"), ("model.joblib", "input_schema.json")],
)
def test_missing_file_is_named_without_a_technical_error(tmp_path, present, absent):
    report = run_in_copy(clean_copy(tmp_path, present))
    assert report["exception"] == []
    assert len(report["errors"]) == 1 and f"models/{absent}" in report["errors"][0]


# --- Historia 2: casos preparados ---


@pytest.mark.parametrize("example", [PAID, DEFAULTED])
def test_each_example_fills_its_39_fields(example, schema):
    check_form_shows(open_app(example), schema, schema["examples"][example], example)


def test_changing_examples_leaves_no_value_from_the_previous_one(schema):
    at = open_app(PAID)
    number(at, SCORE, PAID).set_value(777)
    at.run()
    at.radio[0].set_value(DEFAULTED).run()
    check_form_shows(at, schema, schema["examples"][DEFAULTED], DEFAULTED)


def test_coming_back_to_an_example_restores_its_values(schema):
    at = open_app(PAID)
    number(at, SCORE, PAID).set_value(777)
    at.run()
    at.radio[0].set_value(BLANK).run()
    at.radio[0].set_value(PAID).run()
    check_form_shows(at, schema, schema["examples"][PAID], PAID)


def test_going_back_to_blank_empties_every_field(schema):
    at = open_app(PAID)
    at.radio[0].set_value(BLANK).run()
    check_form_shows(at, schema, {}, BLANK)


def test_blank_form_suggests_nothing(schema):
    at = open_app()
    check_form_shows(at, schema, {}, BLANK)
    assert len(at.number_input) == 33 and len(at.selectbox) == 6
    assert all(box.options[0] == UNKNOWN and box.index == 0 for box in at.selectbox)


def test_changing_example_removes_the_previous_result():
    at = evaluate(open_app(PAID))
    assert recommendation(at) in ACTIONS
    at.radio[0].set_value(DEFAULTED).run()
    assert not at.metric


def test_changing_example_removes_the_previous_error():
    at = open_app(PAID)
    number(at, SCORE, PAID).set_value(-500)
    evaluate(at)
    assert at.error
    at.radio[0].set_value(DEFAULTED).run()
    assert not at.error


def test_changing_one_field_crosses_the_threshold(model, schema):
    # Solo con este ejemplo: en el préstamo pagado (6,6 %) ningún dato por sí solo llega a 20 %
    example = DEFAULTED
    column, value = find_crossing(example, model, schema)
    at = evaluate(open_app(example))
    assert recommendation(at) == ACTION_REVIEW
    number(at, column, example).set_value(value)
    evaluate(at)
    assert recommendation(at) == ACTION_NO_REVIEW
    assert not at.warning  # el valor es normal: la recomendación no cambia por un dato raro


# --- Historia 3: datos inválidos ---


def test_impossible_value_shows_field_and_range_and_no_recommendation():
    at = open_app(PAID)
    number(at, SCORE, PAID).set_value(-500)
    evaluate(at)
    assert [e.value for e in at.error] == ["Revisa los datos: Puntaje de crédito (límite inferior): debe estar entre 300 y 900"]
    assert not at.metric


def test_every_impossible_value_is_named():
    at = open_app(PAID)
    number(at, SCORE, PAID).set_value(-500)
    number(at, "StatedMonthlyIncome", PAID).set_value(-1.0)
    number(at, "AmountDelinquent", PAID).set_value(99_000_000)
    evaluate(at)
    message = at.error[0].value
    assert "Puntaje de crédito (límite inferior): debe estar entre 300 y 900" in message
    assert "Ingreso mensual declarado (USD): debe estar entre 0 y 100.000" in message
    assert "Monto en mora (USD): debe estar entre 0 y 10.000.000" in message
    assert message.count(";") == 2 and "e+" not in message and not at.metric


def test_correcting_the_value_brings_the_recommendation_back(schema):
    at = open_app(PAID)
    number(at, SCORE, PAID).set_value(-500)
    evaluate(at)
    assert at.error
    number(at, SCORE, PAID).set_value(int(schema["examples"][PAID][SCORE]))
    evaluate(at)
    assert not at.error and recommendation(at) in ACTIONS


@pytest.mark.parametrize("value", [300, 900])
def test_value_at_the_limit_of_the_possible_range_is_accepted(value):
    at = open_app(PAID)
    number(at, SCORE, PAID).set_value(value)
    evaluate(at)
    assert not at.error and recommendation(at) in ACTIONS


def test_rare_but_possible_value_answers_with_a_warning():
    at = open_app(PAID)
    number(at, "AmountDelinquent", PAID).set_value(900_000)
    evaluate(at)
    assert recommendation(at) in ACTIONS
    assert [w.value for w in at.warning] == ["Monto en mora (USD): fuera del rango visto en el entrenamiento (0 a 444.745)"]


def test_numeric_fields_have_no_limits_on_screen():
    assert all(field.min is None and field.max is None for field in open_app().number_input)


# --- Historia 4: "No sé" ---


def test_blank_form_answers_with_the_model_on_empty_data_and_warns(model, schema):
    at = evaluate(open_app())
    assert recommendation(at) in ACTIONS
    assert metrics(at)["Probabilidad de impago"] == format_percent(direct_probability({}, model, schema))
    assert "Se evaluó sin 39 de 39 datos" in at.info[0].value
    assert [w.value for w in at.warning] == [TYPICAL_VALUES_WARNING]


def test_emptying_a_field_of_an_example_counts_it_and_reaches_the_model_as_empty(model, schema):
    values = dict(schema["examples"][PAID])
    missing_before = sum(value is None for value in values.values())
    at = open_app(PAID)
    number(at, "StatedMonthlyIncome", PAID).set_value(None)
    evaluate(at)
    del values["StatedMonthlyIncome"]
    assert f"Se evaluó sin {missing_before + 1} de 39 datos" in at.info[0].value
    assert metrics(at)["Probabilidad de impago"] == format_percent(direct_probability(values, model, schema))
    assert number(at, "StatedMonthlyIncome", PAID).value is None  # sigue vacío: no vuelve el valor del ejemplo


def test_unknown_in_a_list_counts_as_missing(schema):
    missing_before = sum(value is None for value in schema["examples"][PAID].values())
    at = open_app(PAID)
    category(at, "IncomeRange", PAID).set_value(UNKNOWN)
    evaluate(at)
    assert f"Se evaluó sin {missing_before + 1} de 39 datos" in at.info[0].value


# --- Historia 5: límites a la vista ---


def test_responsible_use_is_visible_before_evaluating_and_outside_any_expander(schema):
    at = open_app()
    assert schema["responsible_use"] in markdown_outside_expanders(at)
    assert not at.metric


def test_performance_is_visible_before_evaluating_and_outside_any_expander(schema):
    at = open_app()
    text = "\n".join(markdown_outside_expanders(at))
    assert all(line in text for line in performance_lines(schema))
    assert text.index("0,4789") < text.index("0,6209")


def test_page_follows_the_contract_order():
    at = open_app()
    titles = [s.value.split(": ", 1)[-1] for s in at.subheader]
    assert titles == ["Solicitud", "Resultado", "Uso responsable", "Rendimiento esperado"]
    assert at.radio[0].label == "Empezar desde" and at.button[0].label == "Evaluar"


# --- Historia 6: formulario largo ---


def test_optional_data_is_folded_in_one_section(schema):
    at = open_app()
    assert [e.label for e in at.expander] == ["Datos adicionales (opcional)"]
    assert at.expander[0].proto.expanded is False


def test_only_the_essential_fields_are_outside_the_folded_section(schema):
    at = open_app()
    folded = {field.label for field in [*at.expander[0].number_input, *at.expander[0].selectbox]}
    shown = {field.label for field in [*at.number_input, *at.selectbox]} - folded
    assert shown == {schema["labels"][column] for column in schema["essential_fields"]}
    assert len(shown) == 12 and len(folded) == 27


def test_each_optional_tab_holds_its_columns(schema):
    at = open_app()
    groups = optional_groups(schema)
    assert len(at.expander[0].tabs) == len(groups)
    for tab, (group, columns) in zip(at.expander[0].tabs, groups.items(), strict=True):
        assert tab.label.endswith(group)
        labels = [field.label for field in [*tab.number_input, *tab.selectbox]]
        assert sorted(labels) == sorted(schema["labels"][column] for column in columns)


def test_app_says_what_is_lost_with_only_the_essential_fields(schema):
    at = open_app()
    assert reduced_input_note(schema) in "\n".join(markdown_outside_expanders(at))


def test_filling_only_the_essentials_gives_the_model_answer_and_says_what_is_missing(model, schema):
    values = {column: schema["examples"][DEFAULTED][column] for column in schema["essential_fields"]}
    at = open_app()
    for column in schema["essential_fields"]:
        if column in schema["numeric"]:
            number(at, column, BLANK).set_value(values[column])
        else:
            category(at, column, BLANK).set_value(values[column])
    evaluate(at)
    assert "Se evaluó sin 27 de 39 datos." == at.info[0].value
    assert metrics(at)["Probabilidad de impago"] == format_percent(direct_probability(values, model, schema))


def test_missing_essential_fields_are_counted():
    at = evaluate(open_app())
    assert "Faltan 12 de los esenciales." in at.info[0].value


def test_purpose_list_shows_names_and_no_codes():
    options = category(open_app(), "ListingCategory (numeric)", BLANK).options
    assert "Consolidación de deudas" in options and "No disponible" in options
    assert len(options) == 22 and not any(option.isdigit() for option in options)


def test_yes_no_lists_show_names():
    assert category(open_app(), "IsBorrowerHomeowner", BLANK).options == [UNKNOWN, "No", "Sí"]
    assert category(open_app(), "IncomeVerifiable", BLANK).options == [UNKNOWN, "No", "Sí"]


def test_choosing_a_purpose_by_name_delivers_the_original_code(model, schema):
    column = "ListingCategory (numeric)"
    at = open_app(PAID)  # este ejemplo trae el código 1: se elige otro antes, para que la prueba no pase sin hacer nada
    for name, code in [("Negocio", "3"), ("Consolidación de deudas", "1")]:
        box = category(at, column, PAID)
        box.select_index(box.options.index(name))
        evaluate(at)
        assert category(at, column, PAID).value == code
        values = {**schema["examples"][PAID], column: code}
        assert metrics(at)["Probabilidad de impago"] == format_percent(direct_probability(values, model, schema))
