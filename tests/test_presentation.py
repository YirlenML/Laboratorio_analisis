"""Pruebas de lo que la app le muestra a una persona: grupos, nombres, recomendación y rendimiento."""
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from proyecto.config import ESSENTIAL_FIELDS, FIELD_GROUPS, LISTING_CATEGORY_LABELS, YES_NO_LABELS
from proyecto.inference.predict import blank_unasked, form_columns
from proyecto.inference.presentation import (
    essential_columns,
    optional_groups,
    performance_tiles_html,
    probability_meter_html,
    reduced_input_note,
    review_threshold,
    ACTION_NO_REVIEW,
    ACTION_REVIEW,
    TYPICAL_VALUES_WARNING,
    build_recommendation,
    count_missing,
    display_label,
    format_percent,
    performance_lines,
)
from proyecto.inference.schema import load_schema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "models" / "input_schema.json"
METRICS_PATH = ROOT / "reports" / "07_metricas_test.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return load_schema(SCHEMA_PATH)


def scored_row(decision: str, proba: float = 0.3) -> pd.Series:
    """Una fila como las que devuelve `predict_with_scores`."""
    return pd.Series({"decision": decision, "proba_pagó": 1 - proba, "proba_impago": proba})


def complete_form(schema: dict) -> dict:
    return {**{c: 1.0 for c in schema["numeric"]}, **{c: "x" for c in schema["categorical"]}}


def test_field_groups_hold_the_39_columns_exactly_once():
    numeric, categorical = form_columns()
    grouped = [column for columns in FIELD_GROUPS.values() for column in columns]
    assert Counter(grouped) == Counter(numeric + categorical)
    assert len(FIELD_GROUPS) == 5


def test_listing_labels_cover_the_21_codes_of_the_schema(schema):
    assert set(LISTING_CATEGORY_LABELS) == set(schema["categories"]["ListingCategory (numeric)"])
    assert len(LISTING_CATEGORY_LABELS) == 21
    assert LISTING_CATEGORY_LABELS["0"] == "No disponible"


def test_yes_no_labels_cover_the_values_of_the_schema(schema):
    assert set(YES_NO_LABELS) == set(schema["categories"]["IsBorrowerHomeowner"])
    assert set(YES_NO_LABELS) == set(schema["categories"]["IncomeVerifiable"])


def test_display_label_returns_the_visible_name():
    toy = {"category_labels": {"color": {"r": "Rojo"}}}
    assert display_label(toy, "color", "r") == "Rojo"


def test_display_label_without_a_name_returns_the_original_value():
    toy = {"category_labels": {"color": {"r": "Rojo"}}}
    assert display_label(toy, "color", "v") == "v"
    assert display_label(toy, "talla", "M") == "M"
    assert display_label({}, "color", "r") == "r"


def test_schema_field_groups_match_the_configuration(schema):
    assert schema["field_groups"] == FIELD_GROUPS


def test_schema_category_labels_match_the_configuration(schema):
    assert schema["category_labels"] == {
        "ListingCategory (numeric)": LISTING_CATEGORY_LABELS,
        "IsBorrowerHomeowner": YES_NO_LABELS,
        "IncomeVerifiable": YES_NO_LABELS,
    }


def test_schema_performance_matches_the_stage_7_report_value_by_value(schema):
    metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    global_pr = next(r for r in metrics["intervalos"] if r["medida"] == "AUC-PR (mayor es mejor)")
    recent, model = metrics["desde_julio_2009"], metrics["metricas_modelo"]
    assert schema["performance"] == {
        "pr_auc": global_pr["valor"],
        "pr_auc_low": global_pr["IC 95 % inferior"],
        "pr_auc_high": global_pr["IC 95 % superior"],
        "pr_auc_recent": recent["pr_auc"],
        "pr_auc_recent_low": recent["ic95"][0],
        "pr_auc_recent_high": recent["ic95"][1],
        "baseline_pr_auc": metrics["metricas_linea_base"]["pr_auc"],
        "flagged_rate": model["flagged_rate"],
        "recall_default": model["recall_default"],
        "precision_default": model["precision_default"],
    }


def test_impago_becomes_send_to_review(schema):
    assert build_recommendation(scored_row("impago"), schema, [])["action"] == "Enviar a revisión"


def test_pago_becomes_no_priority_review(schema):
    assert build_recommendation(scored_row("pagó"), schema, [])["action"] == "Sin revisión prioritaria"


def test_recommendation_translates_the_decision_without_comparing_again(schema):
    # Filas imposibles a propósito: si alguien volviera a comparar con 0,2, estas pruebas fallarían
    assert build_recommendation(scored_row("impago", 0.05), schema, [])["action"] == ACTION_REVIEW
    assert build_recommendation(scored_row("pagó", 0.95), schema, [])["action"] == ACTION_NO_REVIEW


def test_probability_is_not_altered(schema):
    proba = 0.123456789012345
    assert build_recommendation(scored_row("pagó", proba), schema, [])["default_probability"] == proba


def test_explanation_mentions_the_20_percent_rule_and_the_person(schema):
    explanation = build_recommendation(scored_row("pagó"), schema, [])["explanation"]
    assert "20 %" in explanation and "persona" in explanation


def test_recommendation_keeps_the_warnings_it_receives(schema):
    assert build_recommendation(scored_row("pagó"), schema, ["aviso"])["warnings"] == ["aviso"]


def test_recommendation_without_a_form_row_counts_nothing_missing(schema):
    assert build_recommendation(scored_row("pagó"), schema, [])["missing_count"] == 0


def test_format_percent_uses_a_decimal_comma():
    assert format_percent(0.0656) == "6,6 %"
    assert format_percent(0.2) == "20,0 %"


def test_count_missing_counts_nan_none_and_absent_columns(schema):
    form_row = complete_form(schema)
    assert count_missing(form_row, schema) == 0
    form_row[schema["numeric"][0]] = np.nan
    form_row[schema["categorical"][0]] = None
    assert count_missing(form_row, schema) == 2
    del form_row[schema["numeric"][1]]
    assert count_missing(form_row, schema) == 3


def test_count_missing_accepts_a_table_row(schema):
    form_row = pd.DataFrame([{**complete_form(schema), "Term": np.nan}]).iloc[0]
    assert count_missing(form_row, schema) == 1


def test_count_missing_ignores_columns_outside_the_form(schema):
    assert count_missing({**complete_form(schema), "otra": np.nan}, schema) == 0


def test_recommendation_reports_how_many_fields_were_missing(schema):
    form_row = {**complete_form(schema), "Term": np.nan}
    result = build_recommendation(scored_row("pagó"), schema, [], form_row)
    assert result["missing_count"] == 1 and TYPICAL_VALUES_WARNING not in result["warnings"]


def test_all_fields_empty_adds_the_typical_values_warning(schema):
    form_row = {column: np.nan for column in schema["numeric"] + schema["categorical"]}
    result = build_recommendation(scored_row("impago"), schema, ["aviso"], form_row)
    assert result["missing_count"] == 39
    assert result["warnings"] == ["aviso", TYPICAL_VALUES_WARNING]


def test_performance_lines_use_a_decimal_comma(schema):
    text = " ".join(performance_lines(schema))
    assert "0,4789" in text and "0,6209" in text and "0.4789" not in text and "0.6209" not in text


def test_performance_lines_put_the_recent_figure_first(schema):
    text = " ".join(performance_lines(schema))
    assert text.index("0,4789") < text.index("0,6209")


def test_performance_lines_say_what_to_expect_in_current_applications(schema):
    first = performance_lines(schema)[0]
    assert "parecidas a las actuales" in first and "0,4789" in first and "no" in first and "0,6209" in first


def test_performance_lines_include_the_intervals_and_the_workload(schema):
    text = " ".join(performance_lines(schema))
    for expected in ["0,4480", "0,5102", "0,6044", "0,6407", "0,3104", "63,7 %", "87,5 %", "42,6 %"]:
        assert expected in text


# --- Datos esenciales y diseño ---


def test_essential_fields_are_twelve_form_columns_without_repeats():
    numeric, categorical = form_columns()
    assert len(ESSENTIAL_FIELDS) == len(set(ESSENTIAL_FIELDS)) == 12
    assert set(ESSENTIAL_FIELDS) <= set(numeric + categorical)
    assert "CreditGrade" not in ESSENTIAL_FIELDS  # solo existe antes de 2009


def test_schema_essential_fields_match_the_configuration(schema):
    assert essential_columns(schema) == ESSENTIAL_FIELDS


def test_optional_groups_hold_the_other_27_columns_once_and_skip_empty_groups(schema):
    groups = optional_groups(schema)
    columns = [column for group in groups.values() for column in group]
    assert len(columns) == len(set(columns)) == 27
    assert not set(columns) & set(ESSENTIAL_FIELDS)
    assert "Condiciones del préstamo" not in groups  # sus 5 datos son esenciales
    assert all(groups.values())


def test_blank_unasked_empties_only_what_was_not_asked():
    df = pd.DataFrame({"a": [1.0], "b": ["x"], "c": [3.0]})
    out = blank_unasked(df, ["a"])
    assert out["a"].tolist() == [1.0] and out["b"].isna().all() and out["c"].isna().all()
    assert df["b"].tolist() == ["x"]  # no modifica el original


def test_review_threshold_comes_from_the_cost_matrix(schema):
    assert review_threshold(schema) == pytest.approx(0.2)


def test_reduced_input_was_measured_and_the_note_uses_those_figures(schema):
    r = schema["reduced_input"]
    assert r["pr_auc_essential"] < r["pr_auc_all"] and r["pr_auc_recent_essential"] < r["pr_auc_recent_all"]
    note = reduced_input_note(schema)
    assert f"{r['pr_auc_all']:.4f}".replace(".", ",") in note and f"{r['pr_auc_essential']:.4f}".replace(".", ",") in note
    assert "12 datos esenciales" in note


def test_reduced_input_reproduces_the_stage_7_reserve(schema):
    frozen = json.loads((ROOT / "reports" / "07_decisiones_congeladas.json").read_text(encoding="utf-8"))
    assert schema["reduced_input"]["pr_auc_all"] == pytest.approx(frozen["reserva"]["pr_auc"])


@pytest.mark.parametrize(
    ("probability", "needs_review", "text", "css"),
    [(0.457, True, "Supera el umbral de 20 %", "review"), (0.066, False, "No supera el umbral de 20 %", "clear")],
)
def test_meter_shows_state_with_text_icon_and_threshold(schema, probability, needs_review, text, css):
    html = probability_meter_html(probability, needs_review, schema)
    assert text in html and f"meter-status {css}" in html and "<svg" in html
    assert "left:20.0%" in html and f"width:{probability * 100:.1f}%" in html
    assert "aria-label" in html


def test_meter_draws_the_decision_it_receives_and_stays_inside_the_bar(schema):
    assert "meter-status review" in probability_meter_html(0.01, True, schema)
    assert "width:100.0%" in probability_meter_html(1.5, True, schema)


def test_tiles_put_the_recent_figure_first(schema):
    html = performance_tiles_html(schema)
    assert html.index("0,4789") < html.index("0,6209")

