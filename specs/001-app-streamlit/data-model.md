# Data Model: App de Eco-Score

## Esquema de entrada (`models/input_schema.json`)

Conserva sus claves actuales y agrega tres:

| Clave nueva | Contenido | Origen |
|---|---|---|
| `field_groups` | `{grupo: [columnas]}`: las 39 columnas, cada una una sola vez | `FIELD_GROUPS` en `config.py` |
| `category_labels` | `{columna: {valor: nombre}}` para `ListingCategory (numeric)`, `IsBorrowerHomeowner` e `IncomeVerifiable` | `config.py` y diccionario de datos |
| `performance` | Ver abajo | `reports/07_metricas_test.json` |

### `performance`

| Campo | Valor esperado | Clave de origen |
|---|---|---|
| `pr_auc`, `pr_auc_low`, `pr_auc_high` | 0,6209 [0,6044; 0,6407] | `intervalos`, "AUC-PR (mayor es mejor)" |
| `pr_auc_recent`, `pr_auc_recent_low`, `pr_auc_recent_high` | 0,4789 [0,4480; 0,5102] | `desde_julio_2009` |
| `baseline_pr_auc` | 0,3104 | `metricas_linea_base.pr_auc` |
| `flagged_rate` | 63,7 % | `metricas_modelo.flagged_rate` |
| `recall_default` | 87,5 % | `metricas_modelo.recall_default` |
| `precision_default` | 42,6 % | `metricas_modelo.precision_default` |

## Solicitud

Una fila con las 39 columnas de `form_columns()`. Un dato vacío es `NaN`. Numéricas: número o vacío. Categóricas: una categoría
conocida o vacío.

## Resultado para la persona (`Recommendation`)

| Campo | Regla |
|---|---|
| `action` | `enviar a revisión` si `decision` es `impago`; si no, `sin revisión prioritaria` |
| `default_probability` | `proba_impago`, sin alterar |
| `explanation` | Una frase con la regla de 20 % y que la decisión es de la persona |
| `missing_count` | Cuántas de las 39 columnas llegaron vacías |
| `warnings` | Las de `validate_inputs` y, si faltan todos los datos, el aviso de valores típicos |

## Estados de la pantalla

```text
sin evaluar -> (evaluar con datos válidos) -> con recomendación
sin evaluar -> (evaluar con dato imposible) -> con error
con recomendación o con error -> (cambiar de ejemplo) -> sin evaluar
```

## Reglas de validación

Se conservan las de `validate_inputs`: fuera de `valid_range` o no numérico es error; fuera de `observed_range` o categoría no vista es
advertencia. Los mensajes pasan a usar la etiqueta en español y números legibles, sin notación científica.
