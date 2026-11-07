# Contrato de la pantalla

## Orden de la página

1. Título (`app_title`) y frase: "Apoyo a la priorización. La decisión final es de una persona."
2. Aviso de uso responsable, visible (FR-011).
3. Rendimiento esperado, visible, con 0,4789 antes que 0,6209 (FR-012).
4. Selector: "Formulario en blanco", "Préstamo real que se pagó", "Préstamo real que cayó en impago".
5. Formulario por grupos, con el primer grupo abierto, y botón **Evaluar**.
6. Resultado o error.

> **Cambio del 6 nov:** la página pasa a dos columnas. Izquierda: solicitud, con 12 datos esenciales y 27 opcionales plegados por tema. Derecha: resultado, uso responsable y rendimiento. El resultado agrega un medidor con la marca de 20 %, y su estado lleva icono y texto.

## Resultado

- Recomendación: **Enviar a revisión** o **Sin revisión prioritaria**.
- Probabilidad de impago, en porcentaje con un decimal.
- Explicación: "Se envía a revisión si la probabilidad de impago supera 20 %."
- Si hay datos faltantes: "Se evaluó sin N de 39 datos".
- Advertencias, una por línea.
- La recomendación de los ejemplos no se presenta como el resultado real del préstamo.

No debe aparecer en la pantalla: `pagó`/`impago` como decisión, "rechazado", "el modelo está seguro" ni la matriz de costos sin explicación.

## Error

- Sin recomendación ni probabilidad.
- Mensaje: `Revisa los datos: Puntaje de crédito (límite inferior): debe estar entre 300 y 900`.
- Varios errores se separan con `;`.

## Faltan archivos

Título y mensaje que nombra el archivo que falta. Sin traza técnica.

## Funciones de `src/proyecto/inference/presentation.py`

| Función | Entrada | Salida |
|---|---|---|
| `build_recommendation(row, schema, warnings)` | fila de `predict_with_scores`, esquema, advertencias | diccionario `Recommendation` de `data-model.md` |
| `count_missing(form_row, schema)` | fila del formulario | entero |
| `performance_lines(schema)` | esquema | lista de frases en español con coma decimal |
| `display_label(schema, column, value)` | columna y valor | nombre visible; sin nombre, el valor |

No importan Streamlit.
