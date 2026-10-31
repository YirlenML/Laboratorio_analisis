# Informe del preprocesamiento (etapa 3)

> Resultado de `notebooks/03_preprocesamiento.ipynb` (ejecutado desde cero el 31 oct). Implementa
> `especificaciones/03-preprocesamiento.md`. Código: `src/proyecto/data/cleaning.py` y `split.py`; pruebas:
> `tests/test_cleaning.py` y `tests/test_split.py`.

## Resultado

- **Crudo:** 113.937 filas × 81 columnas. **Limpio:** 49.552 préstamos × 62 columnas (incluye `is_default` e
  índice climático). La cifra coincide con la población del EDA.
- **Impagos:** 15.380 (31,04 %).
- **Unidad de análisis:** un préstamo personal de Prosper (una fila por `ListingKey`). **Entidad que se repite:**
  el prestatario (`MemberKey`).

| Partición | Filas | Prestatarios | % de filas | % impago |
|---|---|---|---|---|
| Entrenamiento | 39.641 | 32.341 | 80,0 % | 31,04 % |
| Prueba (cerrada hasta la etapa 7) | 9.911 | 8.111 | 20,0 % | 31,04 % |

Partición con `StratifiedGroupKFold` (5 pliegues, se toma uno como prueba), por `MemberKey`, estratificada por
`is_default` y con semilla 42. Ningún prestatario cae en los dos lados (lo verifican el código y `tests/test_split.py`).

## Decisiones aplicadas

| # | Regla | Función | Filas afectadas | Motivo |
|---|---|---|---|---|
| 1 | Solo `Completed`, `Chargedoff`, `Defaulted`; `is_default` = 1 si impago; se quita `LoanStatus` | `build_target()` | 58.853 préstamos sin resultado salen | Sin resultado final no hay objetivo |
| 2 | Una fila por `ListingKey` (la primera) | `drop_duplicate_listings()` | — | Mismo préstamo con doble peso |
| 4 | Se eliminan las filas sin `BorrowerState` | `drop_missing_state()` | — | Sin estado no hay índice climático |
| — | Se quitan `GroupKey` (al cargar) y `ListingKey`, `ListingNumber`, `LoanKey`, `LoanNumber`, `Occupation` | `load_raw()`, `drop_personal_columns()` | todas | Datos personales y cuasi-identificadores |
| 5 | Se quitan las 12 columnas posteriores al otorgamiento | `drop_leakage_columns()` | todas | Fuga de información |
| 6 | `IncomeRange` sin espacios y con 8 categorías fijas; otro valor → error | `clean_income_range()` | — | `Not displayed` ≠ `$0` |
| 7 | `CreditScoreRangeLower` = 0 → vacío (y su `CreditScoreRangeUpper` = 19); `StatedMonthlyIncome` > 100.000 → vacío | `mark_impossible_values()` | 89 y 8 | Valores imposibles |
| 9 | `LoanOriginationDate` como fecha; se quitan `ListingCreationDate` y `DateCreditPulled` | `parse_origination_date()` | todas | Fechas dañadas |
| 10 | Índice climático: 10 estados con valor, el resto 50,0 | `add_climate_index()` | todas | Supuesto académico, se mide con y sin él |

**Orden de las reglas 1 y 2.** Primero se filtra por estado y luego se quitan los repetidos. Algunos `ListingKey`
repetidos tienen dos `LoanStatus` distintos. Si se quitaran los repetidos primero, se podría conservar la copia
"sin terminar" y perder la terminada. Con este orden salen 49.552 filas, la cifra del EDA; con el orden inverso
saldrían 49.551.

## Valores atípicos (decisiones nuevas, 31 oct)

El EDA dejó abiertos varios valores extremos. **Ninguna fila se borra por ser atípica:** lo imposible pasa a vacío
(se imputa en la etapa 4, dentro del `Pipeline`), lo que se deduce con una regla exacta se repara y lo extremo pero
posible se conserva. Cifras sobre la población a modelar (49.552):

| # | Hallazgo | Decisión | Motivo | Función |
|---|---|---|---|---|
| 11 | `MonthlyLoanPayment` = 0 en 838 préstamos (todos con monto ≥ 1.000 y tasa > 0) | Recalcular con la fórmula de cuota fija: monto · r / (1 − (1 + r)^−plazo), r = `BorrowerRate`/12 | Una cuota 0 es imposible. En las filas con cuota, la fórmula coincide con el dato (error mediano 0,001 %). Las tres variables se conocen al otorgar el préstamo | `repair_monthly_payment()` |
| 12 | `StatedMonthlyIncome` = 0 en 1.058 préstamos: 1.037 tienen `IncomeRange` `$0` o `Not employed`; 21 no (20 `Not displayed`, 1 `$1-24,999`) | El 0 se conserva si es coherente con `IncomeRange`; en los otros 21 pasa a vacío | Un ingreso 0 con ingresos declarados es contradictorio | `mark_impossible_values()` |
| — | `DebtToIncomeRatio` = 10,01 en 187 préstamos (51,9 % de impago) | Se conserva | Es el tope del sistema ("10 o más"; el diccionario de datos lo confirma: `data/diccionario_datos.md`): mantiene el orden y es informativo. Convertirlo en vacío lo mezclaría con el dato perdido | (sin función) |
| — | `EstimatedEffectiveYield` < 0 en 190 préstamos | Se conserva | Una pérdida estimada es posible | (sin función) |
| — | `Recommendations` hasta 39; `StatedMonthlyIncome` hasta 100.000 | Se conserva | Extremos pero posibles; los modelos de árboles no se afectan y el escalado irá dentro del `Pipeline` | (sin función) |

**Riesgo a vigilar.** Los 838 préstamos con cuota 0 tienen solo 13,8 % de impago (frente a 31 %). Si la cuota 0
se dejara como vacío, el modelo podría aprender que "falta la cuota" equivale a "paga bien", que es un artefacto de
carga y no algo del prestatario. Recalcularla elimina ese atajo.

## Datos personales

- `Occupation` estaba **[por confirmar]**. **Decisión (31 oct):** se elimina. Es un cuasi-identificador
  (67 valores) que no está entre las variables del caso. Si el grupo quiere probarla en la etapa 4, basta con
  quitarla de `QUASI_IDENTIFIER_COLUMNS` en `src/proyecto/config.py`.
- `MemberKey` se conserva en `train`/`test` **solo para partir** y para la validación cruzada por grupo. La etapa 4
  debe excluirla de las variables del modelo.

## Por qué partir por prestatario (demostración)

Solo dentro del entrenamiento (la prueba no se tocó), con LightGBM rápido sobre las variables numéricas:

| Forma de separar la validación | Prestatarios en ambos lados | AUC-PR validación |
|---|---|---|
| Por fila (mal) | 2.013 | 0,620 |
| Por prestatario (bien) | 0 | 0,598 |

La partición por fila da 0,022 más de AUC-PR. Esa ventaja es falsa: el modelo ya vio préstamos de los mismos
prestatarios al entrenar.

## Lo que queda para la etapa 4

- Imputar dentro del `Pipeline`, con la mediana del entrenamiento: `DebtToIncomeRatio`, `CreditScoreRange*`,
  `StatedMonthlyIncome` y `BorrowerAPR`.
- Decidir el indicador "antes de 2009" para `EstimatedEffectiveYield`, `ProsperRating` y `ProsperScore`.
- Excluir `MemberKey` y medir con y sin el índice climático y las variables de puntaje de Prosper.
- Otras columnas posibles candidatas a fuga que siguen en los datos y hay que revisar: `Investors`, `PercentFunded`,
  `LenderYield`, `EstimatedLoss` y `EstimatedReturn`.
- `data/processed/` guarda `train.parquet` y `test.parquet`. No se versionan: se regeneran con el notebook 03.
