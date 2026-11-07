"""Traduce el resultado del modelo a lo que lee una persona.

No importa Streamlit: así se puede probar sin abrir la app. Tampoco calcula nada del modelo: la decisión llega ya
tomada por `predict_with_scores` y aquí solo se le pone nombre, para que la regla viva en un solo lugar.
"""
import pandas as pd

from proyecto.config import CLASSES

REVIEW_CLASS = CLASSES[1]  # "impago": la clase que manda la solicitud a revisión
ACTION_REVIEW = "Enviar a revisión"
ACTION_NO_REVIEW = "Sin revisión prioritaria"
EXPLANATION = "Se envía a revisión si la probabilidad de impago supera 20 %. La decisión final es de una persona."
TYPICAL_VALUES_WARNING = (
    "No se conoce ningún dato de esta solicitud: el resultado se apoya casi por completo en valores típicos."
)

METER_ICONS = {
    "review": "M14.4 6 14 4H5v17h2v-7h5.6l.4 2h7V6z",
    "clear": "M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4z",
}


def format_number(value: float, digits: int = 4) -> str:
    """Número con coma decimal."""
    return f"{value:.{digits}f}".replace(".", ",")


def format_percent(value: float) -> str:
    """Proporción como porcentaje con un decimal y coma decimal: 0,0656 -> '6,6 %'."""
    return f"{format_number(value * 100, 1)} %"


def display_label(schema: dict, column: str, value) -> str:
    """Nombre visible de una categoría; si no tiene, el valor tal como llega."""
    return schema.get("category_labels", {}).get(column, {}).get(value, value)


def essential_columns(schema: dict) -> list[str]:
    """Datos que la app pide a la vista."""
    return list(schema["essential_fields"])


def optional_groups(schema: dict) -> dict:
    """Grupos del formulario sin los datos esenciales; un grupo que queda vacío no se muestra."""
    essential = set(essential_columns(schema))
    groups = {group: [c for c in columns if c not in essential] for group, columns in schema["field_groups"].items()}
    return {group: columns for group, columns in groups.items() if columns}


def review_threshold(schema: dict) -> float:
    """Umbral de la regla de menor costo, deducido de la matriz: con 4 a 1 da 0,2. Solo se usa para dibujar."""
    (_, reject_good), (miss_default, _) = schema["cost_matrix"]
    return reject_good / (reject_good + miss_default)


def count_missing(form_row, schema: dict) -> int:
    """Cuántos datos del formulario llegaron vacíos. `form_row` es un diccionario o una fila de tabla."""
    columns = schema["numeric"] + schema["categorical"]
    return int(sum(pd.isna(form_row.get(column)) for column in columns))


def build_recommendation(row, schema: dict, warnings: list[str], form_row=None) -> dict:
    """Arma el resultado para la persona a partir de una fila de `predict_with_scores`.

    Traduce `decision` y no vuelve a comparar con 0,2: la regla se aplica una sola vez, en `predict.py`.
    `form_row` es la fila del formulario y sirve para contar los datos faltantes.
    """
    missing_count = 0 if form_row is None else count_missing(form_row, schema)
    missing_essential = 0 if form_row is None else int(sum(pd.isna(form_row.get(c)) for c in essential_columns(schema)))
    all_missing = missing_count == len(schema["numeric"] + schema["categorical"])
    needs_review = row["decision"] == REVIEW_CLASS
    return {
        "action": ACTION_REVIEW if needs_review else ACTION_NO_REVIEW,
        "needs_review": bool(needs_review),
        "default_probability": row[f"proba_{REVIEW_CLASS}"],
        "explanation": EXPLANATION,
        "missing_count": missing_count,
        "missing_essential": missing_essential,
        "warnings": [*warnings, TYPICAL_VALUES_WARNING] if all_missing else list(warnings),
    }


def performance_lines(schema: dict) -> list[str]:
    """Rendimiento esperado en frases, primero la cifra de las solicitudes parecidas a las actuales."""
    p = schema["performance"]
    return [
        f"En solicitudes parecidas a las actuales (desde julio de 2009) se espera un AUC-PR de "
        f"{format_number(p['pr_auc_recent'])} (IC 95 %: {format_number(p['pr_auc_recent_low'])} a "
        f"{format_number(p['pr_auc_recent_high'])}), no el {format_number(p['pr_auc'])} del total.",
        f"En toda la prueba, el AUC-PR es {format_number(p['pr_auc'])} (IC 95 %: {format_number(p['pr_auc_low'])} a "
        f"{format_number(p['pr_auc_high'])}), frente a {format_number(p['baseline_pr_auc'])} de la línea base. "
        "El AUC-PR mide qué tan bien el modelo pone primero los impagos: mayor es mejor.",
        f"En toda la prueba, la regla marca para revisión el {format_percent(p['flagged_rate'])} de las solicitudes y "
        f"detecta el {format_percent(p['recall_default'])} de los impagos. De las marcadas, "
        f"el {format_percent(p['precision_default'])} cayó en impago.",
    ]


def reduced_input_note(schema: dict) -> str:
    """Lo que se pierde al llenar solo los datos esenciales, medido en préstamos reservados."""
    r = schema["reduced_input"]
    return (
        f"Con solo los {len(essential_columns(schema))} datos esenciales, en préstamos reservados el AUC-PR baja de "
        f"{format_number(r['pr_auc_all'])} a {format_number(r['pr_auc_essential'])}, y desde julio de 2009 de "
        f"{format_number(r['pr_auc_recent_all'])} a {format_number(r['pr_auc_recent_essential'])}. "
        "Cada dato adicional acerca el resultado al del modelo completo."
    )


def performance_tiles_html(schema: dict) -> str:
    """Dos cifras grandes; la de las solicitudes actuales va primero."""
    p = schema["performance"]
    return (
        '<div class="tiles">'
        f'<div class="tile main"><strong>{format_number(p["pr_auc_recent"])}</strong>'
        "<span>AUC-PR esperado en solicitudes actuales</span></div>"
        f'<div class="tile"><strong>{format_number(p["pr_auc"])}</strong><span>AUC-PR en toda la prueba</span></div>'
        "</div>"
    )


def probability_meter_html(probability: float, needs_review: bool, schema: dict) -> str:
    """Barra de 0 a 100 % con la marca del umbral. El estado lleva icono y texto: nunca depende solo del color.

    `needs_review` llega ya decidido: esta función dibuja la decisión, no la toma.
    """
    state = "review" if needs_review else "clear"
    threshold = review_threshold(schema) * 100
    share = min(max(probability * 100, 0.0), 100.0)
    limit = f"{threshold:.0f} %"
    text = f"Supera el umbral de {limit}" if needs_review else f"No supera el umbral de {limit}"
    icon = METER_ICONS[state]
    return (
        f'<div class="meter" role="img" aria-label="Probabilidad de impago {format_percent(probability)}. {text}.">'
        f'<div class="meter-status {state}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="{icon}"/></svg>{text}</div>'
        f'<div class="meter-track"><div class="meter-fill {state}" style="width:{share:.1f}%"></div>'
        f'<div class="meter-mark" style="left:{threshold:.1f}%"></div></div>'
        f'<div class="meter-scale"><span>0 %</span><span class="threshold" style="left:{threshold:.1f}%">{limit}</span>'
        '<span class="end">100 %</span></div></div>'
    )
