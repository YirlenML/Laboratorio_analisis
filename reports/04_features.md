# Informe de variables

> Resultado de `notebooks/04_features.ipynb` (ejecutado el 31 oct). Cada idea de variable es una **hipótesis medida**
> con la misma validación. Tabla completa: `reports/04_features_tabla.csv`. Código: `src/proyecto/features/engineering.py`
> y `src/proyecto/models/train.py`; pruebas: `tests/test_features.py` y `tests/test_models.py`.

## Cómo se midió

- **Datos:** solo entrenamiento (39.641 préstamos, 32.341 prestatarios, 31,04 % de impago). La prueba sigue cerrada.
- **Modelo (parámetros fijos):** LightGBM, `n_estimators=300`, `learning_rate=0.05`, `num_leaves=31`, semilla 42
  (los parámetros de partida del ejemplo del curso). Preprocesamiento dentro del `Pipeline`:
  - numéricas: mediana de entrenamiento con indicador de vacío;
  - categóricas: one-hot, con las categorías de menos del 1 % agrupadas.
- **Métrica principal:** AUC-PR de la clase impago (aprobada el 30 oct). Mide si los impagos quedan arriba en la lista
  de revisión, sin depender de un umbral.
- **Métricas de control:** log loss y Brier (calidad de las probabilidades), ROC-AUC, costo esperado con la matriz
  4 a 1 (marcar impago si P > 0,2) y recall de impago.
- **Pliegues:** 5, con `StratifiedGroupKFold` por `MemberKey` (semilla 42), calculados una vez y reutilizados en
  todas las variantes. Se verifica que ningún prestatario cae en los dos lados.
- **Regla de decisión escrita antes de medir:** se conserva una idea solo si (a) su mejora / ruido en AUC-PR es mayor
  que 1, (b) se conoce al predecir y (c) no es un artefacto de cómo se construyó la muestra.

## Referencia (fila 0)

Perfil de buró del prestatario y condiciones del préstamo, todas conocidas al publicar la solicitud:

- **26 numéricas:** plazo, monto, cuota, puntaje de crédito, antigüedad laboral, líneas de crédito, consultas,
  morosidad, registros públicos, saldo y utilización revolvente, deuda/ingreso, ingreso mensual y recomendaciones.
- **6 categóricas:** rango de ingreso, situación laboral, vivienda propia, ingreso verificable, pertenencia a grupo y
  propósito del préstamo.

**Fuera del modelo por diseño:**

- `Investors`, `PercentFunded` e `InvestmentFromFriends*`: son el resultado de la financiación y se conocen después
  de publicar la solicitud.
- `MemberKey`: solo sirve para partir.
- `BorrowerState`: su efecto se prueba solo a través del índice climático.
- `BorrowerRate` y `LenderYield`: correlación 0,99 con `BorrowerAPR`.
- `CreditScoreRangeUpper`: es igual a `Lower` + 19.

## Tabla de ideas medidas

> "Mejora / ruido" = mejora de AUC-PR / desviación de la variante entre pliegues (regla del curso). "De a pares" =
> mejora / desviación de la diferencia entre pliegues. "Desde jul. 2009" = mejora de AUC-PR medida solo en los préstamos
> desde julio de 2009 (52,5 % del entrenamiento), cuando Prosper empezó a asignar su puntaje (según el diccionario de datos).

| # | Idea | ¿Se conoce al predecir? | AUC-PR (± ruido) | Mejora / ruido | Pliegues ganados | Log loss / ruido | De a pares | Desde jul. 2009 | Decisión |
|---|---|---|---|---|---|---|---|---|---|
| 0 | **Referencia** | sí | 0,6005 ± 0,0120 | 0 | — | 0 | — | — | — |
| 1 | Índice climático (`Precipitation_Risk_Index`) | sí (supuesto académico) | 0,6007 ± 0,0119 | 0,01 | 3 de 5 | 0,06 | 0,05 | −0,0026 (2 de 5) | ☒ descartar |
| 2 | Puntaje y precio de Prosper (`BorrowerAPR`, `ProsperRating`, `ProsperScore`, `EstimatedLoss`, `EstimatedReturn`, `EstimatedEffectiveYield`, `CreditGrade`) | sí | 0,6067 ± 0,0121 | 0,51 | 5 de 5 | 1,11 | 2,82 | +0,0117 (5 de 5) | ☒ conservar (excepción) |
| 3 | Historial en Prosper (préstamos, pagos a tiempo y atrasados, monto prestado y pendiente, cambio de puntaje; vacío = sin préstamo previo → 0 + marca) | sí | 0,6080 ± 0,0118 | 0,63 | 5 de 5 | 1,30 | 4,47 | +0,0171 (5 de 5) | ☒ conservar (excepción) |
| 4 | Razones financieras (cuota / ingreso, monto / ingreso anual, años de historial crediticio) | sí | 0,6021 ± 0,0127 | 0,12 | 4 de 5 | 0,18 | 0,71 | +0,0010 (4 de 5) | ☒ descartar |
| 5 | Año de originación (control) | sí, pero es artefacto | 0,6053 ± 0,0144 | 0,33 | 5 de 5 | 0,73 | 1,23 | +0,0115 (5 de 5) | ☒ descartar (regla c) |
| — | **Final** = referencia + 2 + 3 | sí | 0,6104 ± 0,0117 | 0,84 | 5 de 5 | 1,78 | 4,81 | — | conjunto que pasa a la etapa 5 |
| — | Final + índice climático (vs final) | sí | 0,6116 ± 0,0118 | 0,10 | 4 de 5 | 0,26 | 0,69 | +0,0038 (4 de 5; de a pares 1,12) | ☒ descartar |

Costo esperado con la matriz 4 a 1 (validación, por préstamo): referencia 0,531; final 0,518. Las dos están por
debajo de la mejor estrategia sin modelo (rechazar a todos: 0,69).

## Decisiones y motivos

- **Con la regla escrita, ninguna idea entra.** La mayor mejora / ruido es 0,63, la de la idea 3. El ruido de la regla (≈ 0,012) es
  sobre todo la diferencia de dificultad entre pliegues, que afecta igual a todas las variantes.
- **Excepción (decidida después de ver los datos; aprobada por el grupo el 31 oct):** se
  conservan las ideas que cumplen las cuatro condiciones siguientes, que verifica el código:
  1. ganan en los 5 pliegues;
  2. su log loss / ruido es mayor que 1;
  3. su mejora de a pares es mayor que 2;
  4. la mejora se mantiene desde julio de 2009 en los 5 pliegues.

  Las cumplen solo las ideas 2 y 3. La guía del curso pide mirar los pliegues ganados y una segunda métrica, y el
  ejemplo del curso conservó `Credit_Mix` por su mejora en log loss.
- **Idea 2 (puntaje de Prosper):** se conserva. Sus vacíos coinciden con los préstamos de antes de julio de 2009, así que
  podía estar aprendiendo la época. No es así: desde julio de 2009, cuando ya existe el puntaje, mejora +0,0117 en los 5
  pliegues, el doble que en el total.
- **Idea 3 (historial en Prosper):** se conserva. Es la mayor mejora: +0,0074 en total y +0,0171 desde julio de 2009, con 5
  de 5 pliegues. Es coherente con el EDA: el impago es de 23,3 % con préstamo previo y de 33,1 % sin él, en
  entrenamiento.
- **Idea 4 (razones financieras):** se descarta. +0,0016 (0,12 del ruido). LightGBM ya combina cuota, monto e
  ingreso por su cuenta.
- **Idea 5 (año):** se descarta por la regla (c), escrita antes de medir. "Ayuda" (+0,0048; +0,0115 desde julio de 2009) porque
  la muestra solo tiene préstamos terminados, y los recientes que ya terminaron son sobre todo los que terminaron rápido.
  Es una advertencia para la validación de la etapa 7, no una variable.
- **Idea 1 (índice climático):** se descarta. Contra la referencia aporta +0,0001 (0,01 del ruido). Sobre el
  conjunto final aporta +0,0012 (0,10 del ruido; de a pares 0,69), y desde julio de 2009 +0,0038 (de a pares 1,12, 4 de 5
  pliegues). Es una tendencia pequeña dentro del ruido que no cumple ni la regla ni la excepción.

## Respuesta a la pregunta del caso (hasta ahora, solo con validación)

**Con estos datos, el índice climático no agrega información medible más allá del perfil financiero.** Es un
resultado y no un fracaso: un índice que da 50,0 a 41 de 51 estados y sin fuente verificable difícilmente puede
aportar. Además, usarlo penalizaría a los prestatarios por su estado sin evidencia de que mejore la predicción. En
la etapa 7 se reporta con y sin él, en la prueba, porque es la pregunta del caso.

## Supuestos y riesgos

- **Puntaje y precio de Prosper:** el diccionario de datos confirma que `ProsperRating`, `ProsperScore`,
  `EstimatedReturn` y `CreditGrade` se asignan **al crear la solicitud**, y que existen desde julio de 2009 (`CreditGrade`, antes). Si el modelo se usara **antes** de que Prosper asigne el puntaje, la idea 2 no estaría
  disponible y el modelo sería la referencia sin ella. La app debe pedirlos o permitir dejarlos vacíos.
- **El modelo se apoya en el puntaje de Prosper:** parte de su capacidad viene del puntaje de la propia plataforma.
  Eso se dirá en el informe.
- **Indicadores de vacío y la época:** antes de julio de 2009 vienen vacíos el 100 % del puntaje de Prosper y cerca del
  16 % de varias variables de buró (por ejemplo `BankcardUtilization` y `TotalTrades`). El pipeline agrega indicadores de vacío, que en parte marcan la época. En la etapa 7 se
  medirá el modelo desde julio de 2009 por separado.
- **Muestra sesgada en el tiempo:** la tasa de impago va de 52 % (2006) a 13 % (2013) por cómo se armó la muestra.
  Queda abierto si la prueba debe reservar los años más recientes (`reports/01_eda.md`).
- **Historial en Prosper (confirmado):** el diccionario de datos dice que estas columnas describen el historial
  "at the time they created this listing" y que son vacías "if the borrower had no prior loans". Eso confirma que se
  conocen al decidir y que el vacío se puede convertir en 0.
- **Otras precisiones del diccionario** (`data/diccionario_datos.md`):
  - `DebtToIncomeRatio` = 10,01 es el tope de "1000 % o más", lo que confirma la decisión de conservarlo.
  - `ListingCategory` = 0 significa "Not Available" (23 % del entrenamiento) y se trata como categoría propia.
  - `ProsperScore` debería ir de 1 a 10, pero 29 préstamos de entrenamiento tienen 11. Se conserva: no hay forma de
    saber cuál es el valor correcto y LightGBM no se afecta.
  - `TradesNeverDelinquent` llega como proporción (0–1), no como número de cuentas.
  - `PercentFunded` < 1 en el 0,8 % de los préstamos: en ellos, el monto originado puede ser menor que el pedido.

## Revisión de variables (31 oct, notebook 04 sección 10)

Revisión columna por columna del conjunto final, con los mismos pliegues y el mismo modelo. **Reglas escritas antes
de medir:**
- Eliminar o agrupar: se acepta si el AUC-PR no baja más que una vez el ruido de a pares, en todos los préstamos y
  desde julio de 2009.
- Crear: se acepta con la regla de la etapa 4 o con su excepción.

| Cambio | Por qué se revisó | Mejora AUC-PR | De a pares | Desde jul. 2009 (de a pares) | Decisión |
|---|---|---|---|---|---|
| A · Quitar `TotalProsperPaymentsBilled`, `OpenCreditLines`, `TotalCreditLinespast7years`, `EstimatedReturn` | Redundantes: `Billed` = pagos a tiempo + atrasados (100 %); Spearman 0,95; `EstimatedReturn` = `Yield` − `Loss` (diccionario) | +0,0001 | 0,16 | +0,0022 (0,79) | ☒ aceptar |
| B · Quitar `ProsperPaymentsOneMonthPlusLate`, `Recommendations`, `PublicRecordsLast12Months` | Casi constantes: 0 en el 99,6 %, 92,7 % y 90,4 % | −0,0006 | −0,70 | +0,0002 (0,08) | ☒ aceptar |
| C · Quitar `CurrentlyInGroup` | Marca la época: 33 % antes de julio de 2009 y 5 % después | +0,0009 | 0,59 | +0,0040 (0,69) | ☒ aceptar |
| D · Agrupar `EmploymentStatus` (Employed/Full-time/Part-time → Employed; "Not available" → desconocido) | Prosper cambió la codificación en 2009: "Employed" solo existe después y "Not available" solo antes | −0,0008 | −0,32 | +0,0018 (0,46) | ☒ aceptar |
| E · Crear `prosper_late_payment_rate` y `prosper_outstanding_share` | El historial solo tenía conteos con correlación 0,99 entre sí | +0,0013 | 0,70 | +0,0074 (1,74; 5 de 5) | ☒ no aceptar |

- **Conjunto revisado (A–D juntos):**
  - AUC-PR 0,6107 frente a 0,6104 (de a pares 0,15); desde julio de 2009, −0,0004 (de a pares −0,08). Rinde igual.
  - Pasa de 41 a **34 numéricas** y de 7 a **6 categóricas**: 8 columnas menos que pedir en la app.
  - Gana robustez: deja de usar dos señales que solo marcaban la época de la muestra.
- **E (tasas de comportamiento):** idea prometedora, no aprobada.
  - Desde julio de 2009 mejora en los 5 pliegues.
  - En todos los préstamos, la mejora está dentro del ruido y el log loss casi no cambia (0,28).
  - Se puede reconsiderar si el modelo se valida solo con préstamos recientes.

## Qué se lleva el pipeline final

- **Variables:** referencia + puntaje y precio de Prosper + historial en Prosper, **menos** las 8 columnas de la
  revisión, con `EmploymentStatus` agrupada. En total, **34 numéricas y 6 categóricas**, **sin** índice climático.
- **Cómo se activa:** `build_pipeline(model, scale, **FINAL_FEATURES)` en `src/proyecto/models/train.py`. `FINAL_FEATURES`
  y las listas de columnas están en `src/proyecto/features/engineering.py`.
- **Las ideas descartadas** (clima, razones, año, tasas de comportamiento) se conservan en el código con su opción
  apagada, porque documentan la prueba.
