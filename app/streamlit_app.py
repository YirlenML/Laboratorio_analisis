"""Eco-Score: apoyo a la analista de riesgo para priorizar la revisión de solicitudes.

- Carga `models/model.joblib` y `models/input_schema.json` desde ESTE repositorio. No consulta Databricks ni
  MLflow y no usa credenciales.
- Solo dibuja la pantalla. Validar, predecir y redactar el resultado se hace en `src/proyecto/inference/`.
- El aspecto vive en `app/style.css` y en `.streamlit/config.toml`.

Ejecutar en local (desde la raíz del repositorio):  streamlit run app/streamlit_app.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# Se calcula desde este archivo para que funcione desde cualquier carpeta, también en la nube
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from proyecto.inference.predict import InputValidationError, load_model, predict_with_scores  # noqa: E402
from proyecto.inference.presentation import (  # noqa: E402
    build_recommendation,
    display_label,
    essential_columns,
    format_percent,
    optional_groups,
    performance_lines,
    performance_tiles_html,
    probability_meter_html,
    reduced_input_note,
)
from proyecto.inference.schema import load_schema  # noqa: E402

MODEL_PATH = ROOT / "models" / "model.joblib"
SCHEMA_PATH = ROOT / "models" / "input_schema.json"
STYLE_PATH = Path(__file__).with_name("style.css")
UNKNOWN = "(no sé)"
BLANK_FORM = "Formulario en blanco"
FORM_COLUMNS_PER_ROW = 3
PROPORTION_MAX = 11  # un campo decimal con tope hasta aquí es una proporción: necesita más decimales a la vista
OPTIONAL_LABEL = "Datos adicionales (opcional)"
GROUP_ICONS = {
    "Condiciones del préstamo": ":material/request_quote:",
    "Ingreso y empleo": ":material/work:",
    "Historial de crédito": ":material/credit_score:",
    "Evaluación de Prosper": ":material/verified:",
    "Historial en Prosper": ":material/history:",
}


@st.cache_resource
def get_model():
    return load_model(MODEL_PATH)


@st.cache_data
def get_schema() -> dict:
    return load_schema(SCHEMA_PATH)


def missing_files() -> list[str]:
    """Archivos necesarios que no están en el repositorio."""
    return [f"models/{path.name}" for path in (MODEL_PATH, SCHEMA_PATH) if not path.exists()]


def apply_style() -> None:
    """Carga el diseño. Si falta el archivo, la app sigue funcionando con el tema base."""
    if STYLE_PATH.exists():
        st.html(f"<style>{STYLE_PATH.read_text(encoding='utf-8')}</style>")


def numeric_field(schema: dict, column: str, defaults: dict, key: str) -> float:
    """Campo numérico sin mínimo ni máximo: el rango lo revisa `validate_inputs`, que explica qué corregir.

    Vacío significa "No sé" y se entrega como NaN, para que el pipeline lo impute. El valor del ejemplo se pone en
    `session_state` y no en `value`: con `value`, Streamlit devuelve ese número cuando la persona borra el campo, y
    "No sé" no funcionaría sobre un ejemplo.
    """
    label, default = schema["labels"][column], defaults.get(column)
    is_integer = column in schema["integer_columns"]
    if default is not None and key not in st.session_state:
        st.session_state[key] = int(default) if is_integer else default
    if is_integer:
        answer = st.number_input(label, value=None, step=1, placeholder="No sé", key=key)
    else:
        decimals = 5 if schema["valid_range"][column][1] <= PROPORTION_MAX else 2
        answer = st.number_input(label, value=None, step=0.01, format=f"%.{decimals}f", placeholder="No sé", key=key)
    return np.nan if answer is None else float(answer)


def category_field(schema: dict, column: str, defaults: dict, key: str):
    """Lista con su nombre visible; "(no sé)" va primero para no sugerir un dato. El modelo recibe el valor original."""
    categories = sorted(schema["categories"][column], key=lambda value: display_label(schema, column, value))
    options = [UNKNOWN, *categories]
    default = defaults.get(column)
    choice = st.selectbox(
        schema["labels"][column],
        options,
        index=options.index(default) if default in options else 0,
        format_func=lambda value: display_label(schema, column, value),
        key=key,
    )
    return np.nan if choice == UNKNOWN else choice


def draw_fields(schema: dict, columns: list[str], defaults: dict, example: str) -> dict:
    """Dibuja los campos fila por fila, para que queden alineados y conserven su orden en el celular."""
    row = {}
    for start in range(0, len(columns), FORM_COLUMNS_PER_ROW):
        grid = st.columns(FORM_COLUMNS_PER_ROW, vertical_alignment="bottom")
        for cell, column in zip(grid, columns[start:start + FORM_COLUMNS_PER_ROW]):
            draw = category_field if column in schema["categorical"] else numeric_field
            with cell:
                row[column] = draw(schema, column, defaults, f"{column}|{example}")
    return row


def build_form(schema: dict, example: str) -> dict:
    """Dibuja los datos esenciales y, plegados, los opcionales. Devuelve la fila completa.

    La clave de cada campo incluye el ejemplo: si no, Streamlit conservaría el valor anterior al cambiar de ejemplo.
    """
    defaults = schema["examples"].get(example, {})
    essential = essential_columns(schema)
    st.markdown(f"#### :material/task_alt: {len(essential)} datos esenciales")
    row = draw_fields(schema, essential, defaults, example)

    groups = optional_groups(schema)
    with st.expander(OPTIONAL_LABEL, icon=":material/tune:"):
        st.caption(
            "No son obligatorios. Lo que dejes vacío se completa con un valor típico; "
            "en el historial en Prosper, vacío significa que no tiene préstamos previos."
        )
        tabs = st.tabs([f"{GROUP_ICONS.get(group, '')} {group}".strip() for group in groups])
        for tab, columns in zip(tabs, groups.values(), strict=True):
            with tab:
                row.update(draw_fields(schema, columns, defaults, example))
    return row


def show_recommendation(recommendation: dict, schema: dict, total_fields: int, example: str) -> None:
    key = "result-review" if recommendation["needs_review"] else "result-clear"
    with st.container(border=True, key=key):
        # Una debajo de la otra: "Sin revisión prioritaria" no cabe en media tarjeta y se cortaría
        st.metric("Recomendación", recommendation["action"])
        st.metric("Probabilidad de impago", format_percent(recommendation["default_probability"]))
        st.html(probability_meter_html(recommendation["default_probability"], recommendation["needs_review"], schema))
        st.write(recommendation["explanation"])
        if example != BLANK_FORM:
            st.caption("Es lo que estima el modelo con los datos de este préstamo; no indica cómo terminó.")
    if recommendation["missing_count"]:
        message = f"Se evaluó sin {recommendation['missing_count']} de {total_fields} datos."
        if recommendation["missing_essential"]:
            message += f" Faltan {recommendation['missing_essential']} de los esenciales."
        st.info(message, icon=":material/info:")
    for message in recommendation["warnings"]:
        st.warning(message, icon=":material/warning:")


def show_evaluation(row: dict, model, schema: dict, example: str) -> None:
    try:
        result = predict_with_scores(pd.DataFrame([row]), model, schema)
    except InputValidationError as error:
        st.error(f"Revisa los datos: {error}", icon=":material/error:")
        return
    recommendation = build_recommendation(result.iloc[0], schema, result.attrs["warnings"], row)
    show_recommendation(recommendation, schema, len(row), example)


def main() -> None:
    st.set_page_config(page_title="Eco-Score", page_icon=":material/water_drop:", layout="wide")
    apply_style()

    missing = missing_files()
    if missing:
        st.title("Eco-Score")
        st.error(f"Falta {', '.join(missing)}. Sin ese archivo la app no puede evaluar solicitudes.")
        st.stop()

    model, schema = get_model(), get_schema()
    with st.container(key="hero"):
        st.title(schema["app_title"])
        st.write("Apoyo a la priorización. La decisión final es de una persona.")

    form_side, result_side = st.columns([5, 3], gap="large")
    with form_side, st.container(border=True, key="request"):
        st.subheader(":material/assignment: Solicitud")
        example = st.radio("Empezar desde", [BLANK_FORM, *schema["examples"]], horizontal=True)
        with st.form("solicitud", border=False):
            row = build_form(schema, example)
            submitted = st.form_submit_button("Evaluar", type="primary", icon=":material/analytics:", width="stretch")

    with result_side:
        st.subheader(":material/insights: Resultado")
        # Solo se dibuja en la ejecución del envío: cambiar de ejemplo lo quita de la pantalla
        if submitted:
            show_evaluation(row, model, schema, example)
        else:
            st.info(
                "Completa los datos esenciales y pulsa **Evaluar**. Deja vacío o en *(no sé)* lo que no conozcas.",
                icon=":material/touch_app:",
            )

        with st.container(border=True, key="responsible"):
            st.subheader(":material/shield: Uso responsable")
            st.markdown(schema["responsible_use"])

        with st.container(border=True, key="performance"):
            st.subheader(":material/monitoring: Rendimiento esperado")
            st.html(performance_tiles_html(schema))
            st.markdown("\n".join(f"- {line}" for line in [*performance_lines(schema), reduced_input_note(schema)]))


if __name__ == "__main__":  # `streamlit run` ejecuta el archivo como programa principal
    main()
