# Especificación · Etapa 3 · Preprocesamiento (limpieza y partición)

> Se llena **antes** de pedirle código a Claude, a partir de la tabla de decisiones de
> `especificaciones/02-eda.md`. Claude la lee y la implementa; ustedes revisan que el código haga
> **exactamente** esto (`material-del-curso/kit/checklist-revision-ia.md`).
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md`, sección 4 · Ejemplo: `material-del-curso/ejemplo-creditsight/src/creditsight/data/`.

**Grupo:** Eco-Score   **Fecha:** 30 oct 2026   **Estado:** ☒ borrador  ☐ cerrada

## 1. Unidad de análisis y partición

- **Una fila es:** un préstamo personal de Prosper (`ListingKey`, después de quitar repetidos).
- **Entidad que se repite (columna):** `MemberKey` (prestatario): 7.028 prestatarios con más de un préstamo en la
  población a modelar (16.128 filas).
- **Se parte por:** ☒ grupo (`GroupShuffleSplit` / `StratifiedGroupKFold`) ☐ fila
- **Proporción de prueba:** 20 % (aprobado el 30 oct)   **Semilla:** 42
- **¿Hay orden temporal que respetar?** ☐ no ☒ sí → la tasa de impago de los préstamos terminados cambia por año
  (53,1 % en 2006, 12,9 % en 2013). Por ahora se parte por grupo y estratificado por `is_default`. Si conviene
  reservar los años más recientes para la prueba queda abierto (`reports/01_eda.md`).
- **Dónde se guarda la prueba:** `data/processed/` (cerrada: **no se mira** hasta la etapa 7)

## 2. Datos personales

| Columna | Qué es | Se elimina en | Prueba que lo verifica |
|---|---|---|---|
| `ListingKey`, `ListingNumber`, `LoanKey`, `LoanNumber` | Llaves del préstamo | `drop_personal_columns()`, después de quitar repetidos | `test_no_personal_columns` |
| `GroupKey` | Llave del grupo de Prosper | `load_raw()` (primer paso al cargar) | `test_no_personal_columns` |
| `MemberKey` | Llave seudónima del prestatario | Se conserva solo para partir; se quita de las variables del modelo | `test_no_personal_columns` |
| `Occupation` | Ocupación (cuasi-identificador) | `drop_personal_columns()` (decidido el 31 oct: se elimina; ver `reports/03_preprocesamiento.md`) | `test_no_personal_columns` |

## 3. Reglas de limpieza

Una fila por decisión del EDA. **Una función, una prueba.** Se marca como vacío lo imposible; no se borran filas sin criterio.

| # (de la tabla del EDA) | Columna(s) | Problema | Regla exacta (con el umbral o valor) | Función en `src/proyecto/data/cleaning.py` | Prueba en `tests/test_cleaning.py` |
|---|---|---|---|---|---|
| 1 | `LoanStatus` | Objetivo circular y error `Charged-Off` / `Chargedoff` | Conservar solo `Completed`, `Chargedoff` y `Defaulted`; `is_default` = 1 si `Chargedoff` o `Defaulted` y 0 si `Completed`; quitar `LoanStatus` | `build_target()` | `test_build_target` |
| 2 | `ListingKey` | 889 filas repetidas | `drop_duplicates(subset="ListingKey", keep="first")` | `drop_duplicate_listings()` | `test_drop_duplicate_listings` |
| 4 | `BorrowerState` | 5.515 vacíos | Eliminar filas con `BorrowerState` vacío | `drop_missing_state()` | `test_drop_missing_state` |
| 5 | `LP_*` (8), `ClosedDate`, `LoanCurrentDaysDelinquent`, `LoanFirstDefaultedCycleNumber`, `LoanMonthsSinceOrigination` | Se conocen después de otorgar el préstamo | Eliminar estas 12 columnas | `drop_leakage_columns()` | `test_drop_leakage_columns` |
| 6 | `IncomeRange` | `'$0 '` con espacio, `'Not employed'` y `Not displayed` | Aplicar `strip()`; categorías fijas: `$0`, `$1-24,999`, `$25,000-49,999`, `$50,000-74,999`, `$75,000-99,999`, `$100,000+`, `Not employed`, `Not displayed`. Otro valor → error | `clean_income_range()` | `test_clean_income_range` |
| 7 | `CreditScoreRangeLower`, `StatedMonthlyIncome` | Valores imposibles | `CreditScoreRangeLower` = 0 → vacío; `StatedMonthlyIncome` > 100.000 → vacío | `mark_impossible_values()` | `test_mark_impossible_values` |
| 9 | `LoanOriginationDate` | `ListingCreationDate` y `DateCreditPulled` dañadas | Leer `LoanOriginationDate` con formato `%d/%m/%Y %H:%M`; quitar `ListingCreationDate` y `DateCreditPulled` | `parse_origination_date()` | `test_parse_origination_date` |
| 10 | `BorrowerState` | Índice climático manual | Mapear la matriz de 10 estados; los demás reciben 50,0 (como hoy). Supuesto académico, sin fuente verificable | `add_climate_index()` | `test_add_climate_index` |
| 11 (31 oct) | `MonthlyLoanPayment` | Cuota 0 en 838 préstamos | Recalcular con la cuota fija: monto · r / (1 − (1 + r)^−plazo), r = `BorrowerRate`/12 | `repair_monthly_payment()` | `test_repair_monthly_payment` |
| 12 (31 oct) | `StatedMonthlyIncome`, `CreditScoreRangeUpper` | 0 incoherente con `IncomeRange` (21); `Upper` = 19 cuando `Lower` = 0 | `StatedMonthlyIncome` = 0 y `IncomeRange` distinto de `$0` / `Not employed` → vacío; `CreditScoreRangeUpper` → vacío donde `Lower` = 0 | `mark_impossible_values()` | `test_mark_impossible_values` |

## 4. Vacíos

| Columna | Qué significa el vacío | Tratamiento hoy | Tratamiento en la etapa 4 (dentro del `Pipeline`) |
|---|---|---|---|
| `EstimatedEffectiveYield`, `ProsperRating`, `ProsperScore` | ☒ no aplica ☐ no se anotó ☐ perdido ☐ imposible (no existían antes de 2009) | ☒ dejar vacío ☐ categoría explícita ☐ reparar con valor de la entidad | Indicador "antes de 2009" + imputación con mediana de entrenamiento, o excluir **[por decidir]** |
| `DebtToIncomeRatio` (8,4 % en la población) | ☐ no aplica ☐ no se anotó ☒ perdido ☐ imposible | ☒ dejar vacío ☐ categoría explícita ☐ reparar con valor de la entidad | Mediana de entrenamiento (hoy el notebook lo hace antes de partir y con `inplace`, que no funciona) |
| `CreditScoreRangeLower`, `StatedMonthlyIncome` (tras la regla 7) | ☐ no aplica ☐ no se anotó ☐ perdido ☒ imposible | ☒ dejar vacío ☐ categoría explícita ☐ reparar con valor de la entidad | Mediana de entrenamiento |
| `IncomeRange` = `Not displayed` | ☐ no aplica ☒ no se anotó ☐ perdido ☐ imposible | ☐ dejar vacío ☒ categoría explícita ☐ reparar con valor de la entidad | Codificación que mantenga `Not displayed` aparte |
| `BorrowerAPR` (25 filas) | ☐ no aplica ☐ no se anotó ☒ perdido ☐ imposible | ☒ dejar vacío ☐ categoría explícita ☐ reparar con valor de la entidad | Mediana de entrenamiento |

> Imputar con medias o medianas **no se hace aquí**: depende del entrenamiento y va dentro del `Pipeline`.

## 5. Entradas y salidas

| | Ruta |
|---|---|
| Entrada | `data/raw/prosperLoanData.csv` (separador `;`, nunca se modifica) |
| Salida: entrenamiento | `data/processed/train.parquet` |
| Salida: prueba (cerrada) | `data/processed/test.parquet` |
| Código de limpieza | `src/proyecto/data/cleaning.py` |
| Código de partición | `src/proyecto/data/split.py` |
| Notebook que orquesta | `notebooks/03_preprocesamiento.ipynb` (solo llama a las funciones) |

## 6. Pruebas que deben existir

- ☒ **Partición:** ningún `MemberKey` aparece en dos particiones y no se pierde ninguna fila (`tests/test_split.py`).
- ☒ **La prueba de partición falla** si se cambia temporalmente a partición por fila (compruébenlo y vuelvan a dejarla bien).
- ☒ **Una prueba por regla de limpieza** de la sección 3, con un caso normal y un caso sucio hechos a mano.
- ☒ **Datos personales:** el resultado de cargar no contiene las columnas de la sección 2.
- ☒ `pytest` en verde desde la raíz del repo (31 oct: 37 pruebas).

## 7. Criterios de cierre (H1)

- ☒ La limpieza corre **de principio a fin desde cero** (`data/processed/` borrada y regenerada con el notebook 03), sin pasos manuales.
- ☐ Unidad de análisis y forma de partir **escritas** (sección 1) y documentadas en `reports/01_eda.md`.
- ☒ `pytest` en verde.
- ☒ Conjunto de prueba guardado y sin mirar.
- ☐ `data/raw/` intacta y `.env` fuera de Git (`git status`).
- ☐ Todo subido a GitHub.
- ☐ Revisaron el código de Claude con `checklist-revision-ia.md` y cada integrante puede explicar una función.
- ☐ **Hallazgo que no esperaban** (para la puesta en común): el objetivo de 4 escalas dependía casi por completo del
  índice climático (94,0 % de las filas), y un error de texto (`Charged-Off` contra `Chargedoff`) clasificaba
  10.952 préstamos perdidos como sanos.
