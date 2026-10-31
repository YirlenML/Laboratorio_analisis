# Especificación · Etapa 2 · EDA

> Se llena **antes** de abrir `notebooks/02_eda.ipynb` (las secciones 1 y 2) y se completa **mientras**
> lo ejecutan (3 y 4). El resultado final, con las decisiones, va a `reports/01_eda.md`.
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md` · Ejemplo: `material-del-curso/ejemplo-creditsight/reports/01_eda.md`.

**Grupo:** Eco-Score   **Fecha:** 30 oct 2026   **Estado:** ☒ borrador  ☐ cerrada

## 1. Qué esperamos encontrar (se escribe ANTES de mirar los datos)

Una hipótesis por pregunta. Si después no se cumple, es un hallazgo: anótenlo.

> **Cómo se llenó:** se reconstruyó con lo que el grupo escribió **antes** del EDA, en `README.md` y
> `eco_score_pd.ipynb`. Aprobado por el grupo el 30 oct. La última columna compara con lo medido (sección 3):
> cada "no" es un hallazgo.

| Pregunta | Lo que creíamos | Fuente | ¿Se cumplió? |
|---|---|---|---|
| ¿Qué representa una fila? | Un préstamo individual otorgado a un único prestatario | `README.md`, "Conocimiento inicial de datos" | **Sí**, una fila es un préstamo. Pero 844 préstamos aparecen repetidos (889 filas extra) |
| ¿Alguna entidad se repite en varias filas? | No: "un único prestatario" por préstamo, y `df.duplicated()` daba 0 duplicados | `README.md` y celda de duplicados de `eco_score_pd.ipynb` | **No**: 15.744 prestatarios tienen varios préstamos, y `df.duplicated()` no detecta los `ListingKey` repetidos |
| ¿Qué variable **debería** ser estable y no cambiar? | El estado del prestatario (`BorrowerState`), usado como su ubicación fija para asignar el riesgo climático | Uso de `BorrowerState` en `eco_score_pd.ipynb` (deducido, no escrito) | **Casi**: cambia en el 4,7 % de los prestatarios con varios préstamos. Se toma como mudanza real |
| ¿Qué significaría un vacío en nuestras columnas clave? | `BorrowerState` vacío = cliente "sin geolocalización" (se elimina). En `DebtToIncomeRatio` y `EstimatedEffectiveYield` = dato perdido (se imputa con la mediana) | Celdas de limpieza e imputación de `eco_score_pd.ipynb` | **En parte**: el vacío de `EstimatedEffectiveYield` no es pérdida, la métrica no existía antes de 2009 (100 % vacío en 2005–2008) |
| ¿Qué columna solo se conoce **después** de la decisión que queremos apoyar? | No se identificó ninguna. `LoanStatus` se usó para construir el objetivo junto con el índice climático | `eco_score_pd.ipynb` | **No**: hay 12 columnas posteriores al otorgamiento (`LP_*` y 4 más), y el objetivo anterior dependía del índice climático (94,0 % de las filas) |

## 2. Qué vamos a medir

Marquen lo que aplica a su dataset. Lo que no aplique se tacha **con una razón** (no se deja en blanco).

| Chequeo (guía, sección 3) | ¿Aplica? | Columnas a revisar | Quién lo hace |
|---|---|---|---|
| 3.1 Números guardados como texto | ☒ sí ☐ no: | `IncomeRange` (rangos en texto, `'$0 '` con espacio) | |
| 3.2 Valores centinela (`-1`, `9999`, `?`) | ☒ sí ☐ no: | `DebtToIncomeRatio` (tope 10,01), `CreditScoreRangeLower` (0) | |
| 3.3 Valores imposibles (percentiles, negativos) | ☒ sí ☐ no: | `StatedMonthlyIncome`, `CreditScoreRangeLower`, `EstimatedEffectiveYield` | |
| 3.4 Constancia por entidad | ☒ sí ☐ no: | `ListingKey` repetido (cambia `ProsperScore`) | |
| 3.5 Vacíos que significan algo | ☒ sí ☐ no: | `EstimatedEffectiveYield`, `ProsperRating`, `CreditGrade` (cambio de 2009), `BorrowerState` | |
| 3.6 Duplicados | ☒ sí ☐ no: | `ListingKey` (no la fila completa) | |
| 3.7 Fechas y orden temporal | ☒ sí ☐ no: | `LoanOriginationDate`, `ListingCreationDate`, `DateCreditPulled` | |
| 3.8 Categorías raras / alta cardinalidad | ☒ sí ☐ no: | `BorrowerState` (51; ND con 52 filas), `Occupation` (67) | |
| 3.9 Identidad y datos personales | ☒ sí ☐ no: | `MemberKey`, `ListingKey`, `LoanKey`, `GroupKey`, `Occupation` | |

## 3. Lo que medimos (se llena mientras corre el notebook)

- **Filas × columnas:** 113.937 × 81
- **Unidad de análisis (una frase):** un préstamo personal otorgado por Prosper a un prestatario de EE. UU.
- **Columna que identifica a la entidad (`ID_COL`):** `MemberKey`   **¿Se repite?** ☐ no ☒ sí, 1 a 9 préstamos
  por prestatario (15.744 prestatarios con más de uno, 38.149 filas)
- **Objetivo (`TARGET`):** `is_default` (aprobado el 30 oct)   **Distribución:** 15.380 impagos (31,04 %) y 34.172 pagados
  (68,96 %) en 49.552 préstamos terminados
- **Línea base** (regla trivial) y su resultado: "nadie cae en impago" → exactitud 68,96 %, recall de impago 0
- **Vacíos en el objetivo:** 58.853 préstamos sin resultado final (`Current`, `Past Due`,
  `FinalPaymentInProgress`, `Cancelled`)   **Qué haremos con esas filas:** excluirlas del entrenamiento
- **Datos personales encontrados:** llaves seudónimas (`MemberKey`, `ListingKey`, `LoanKey`, `GroupKey`); no hay
  nombres ni documentos
- **Columnas sospechosas de fuga:** `LP_*` (8), `ClosedDate`, `LoanCurrentDaysDelinquent`,
  `LoanFirstDefaultedCycleNumber`, `LoanMonthsSinceOrigination`, `Target_Risk_Scale`, `Financial_Status`. Se miden
  con y sin ellas: `ProsperRating`, `ProsperScore`, `EstimatedLoss`, `EstimatedReturn`, `Investors` y
  `PercentFunded` (etapa 4).

## 4. Decisiones (mínimo 5)

> Cada una con **cifra**, acción **concreta** y **motivo**. Se copian tal cual a `reports/01_eda.md`.
> Cada decisión se convierte en una función de `src/proyecto/data/` y en una prueba (ver `03-preprocesamiento.md`).

| # | Hallazgo (con cifra) | Decisión | Motivo | Función que la implementa |
|---|---|---|---|---|
| 1 | `Target_Risk_Scale` depende del índice climático en el 94,0 % de las filas; 10.952 `Chargedoff` quedaron como "Saludable" | `is_default` sobre préstamos terminados (aprobado) | Resultado conocido y sin circularidad | `build_target()` |
| 2 | 844 `ListingKey` repetidos (889 filas extra) | Dejar la primera fila por `ListingKey` | Mismo préstamo con doble peso | `drop_duplicate_listings()` |
| 3 | 15.744 prestatarios con varios préstamos | Partir por `MemberKey` | Evitar que un prestatario quede en entrenamiento y en prueba | `split_by_member()` (en `split.py`) |
| 4 | `BorrowerState` vacío en 5.515 filas (4,84 %) | Eliminar esas filas | Sin estado no hay índice climático | `drop_missing_state()` |
| 5 | 12 columnas posteriores al otorgamiento (`LP_*` y 4 más) | Excluirlas al cargar | Fuga de información | `drop_leakage_columns()` |
| 6 | `IncomeRange`: `'$0 '` (621), `'Not employed'` (806), `Not displayed` (7.741) | Quitar espacios y mapear explícitamente; `Not displayed` como categoría propia | "No mostrado" ≠ "sin ingresos" | `clean_income_range()` |
| 7 | `CreditScoreRangeLower` = 0 (133); `StatedMonthlyIncome` > 100.000 (17) | Convertir en vacío | Valores imposibles | `mark_impossible_values()` |
| 8 | Vacíos de `EstimatedEffectiveYield` y `ProsperRating` en el 100 % de 2005–2008 | Dejar el vacío; no imputar fuera del `Pipeline` | El vacío significa "la métrica no existía" | (sin función: se documenta) |
| 9 | `ListingCreationDate` y `DateCreditPulled` dañadas | No usarlas; fechar con `LoanOriginationDate` | No son recuperables | `parse_origination_date()` |
| 10 | 41 de 51 estados con índice por defecto 50,0 | Índice climático solo como variable; medir con y sin él | Hipótesis a probar | `add_climate_index()` |

## 5. Criterios de cierre

- ☒ `notebooks/02_eda.ipynb` corre de principio a fin sin errores (30 oct).
- ☐ Unidad de análisis y `ID_COL` declarados por escrito (sección 3).
- ☐ Al menos **5 decisiones** con cifra, acción y motivo.
- ☐ Datos personales identificados y plan para eliminarlos al cargar.
- ☐ Valores imposibles, centinelas y significado de los vacíos revisados.
- ☐ Fuga sospechada: lista escrita, aunque sea "ninguna, porque…".
- ☐ `reports/01_eda.md` completado.
- ☐ Quien **no** escribió una decisión sabe explicar por qué se tomó.
