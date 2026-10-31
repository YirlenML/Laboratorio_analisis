# Informe del EDA

> Resultado de `notebooks/02_eda.ipynb` (ejecutado el 30 oct) y de la revisión de `eco_score_pd.ipynb`.
> Cada hallazgo termina en una decisión, y cada decisión se implementa con pruebas en `src/proyecto/data/`.
> Guía: `material-del-curso/kit/guia-eda-y-preprocesamiento.md`.
> **Estado: borrador.** Las decisiones marcadas como *propuesta* las confirma el grupo.

## Qué son los datos

- **Filas × columnas:** 113.937 × 81 (separador `;`). Préstamos originados entre 2005 y 2014; 2013 es el año con
  más préstamos (34.345).
- **Unidad de análisis (qué es una fila):** un préstamo personal otorgado por Prosper a un prestatario de EE. UU.,
  con su estado al cierre del dataset (marzo de 2014).
- **¿Una entidad aparece en varias filas?**
  - El prestatario (`MemberKey`) sí: hay 90.824 prestatarios, y 15.744 de ellos tienen más de un préstamo
    (38.149 filas, máximo 9 por persona).
  - El préstamo (`ListingKey`) también se repite por error de carga: 889 filas extra en 844 llaves.
  - En la población a modelar, 7.028 prestatarios tienen varios préstamos. El 15,2 % de ellos tiene resultados
    distintos entre sus préstamos.
  - Los préstamos de prestatarios repetidos caen en impago menos (18,1 %) que los de prestatarios con un solo
    préstamo (37,3 %).
  - Entre préstamos del mismo prestatario cambian `BorrowerState` (4,7 %), `IsBorrowerHomeowner` (8,1 %),
    `Occupation` (11,2 %), `IncomeRange` (30,2 %) y `EmploymentStatus` (30,6 %). Se toma como cambio real, porque son
    préstamos de fechas distintas, y no se repara.
- **Objetivo y distribución:**
  - `LoanStatus` tiene 12 valores: `Current` 56.576, `Completed` 38.074, `Chargedoff` 11.992, `Defaulted` 5.018,
    `Past Due (…)` 2.067 en total, `FinalPaymentInProgress` 205 y `Cancelled` 5.
  - Objetivo `is_default` (aprobado) sobre préstamos terminados (sin duplicados y con estado): 15.380 impagos
    (31,04 %) y 34.172 pagados (68,96 %).
- **Línea base** (resultado de una regla trivial): "nadie cae en impago" → exactitud 68,96 %, recall de impago 0
  y AUC-PR ≈ 0,31.

## Calidad de los datos

- **El objetivo actual del notebook tiene un error de texto.** `clasificar_financiero` busca `'Charged-Off'`, que
  aparece 0 veces; en los datos se escribe `Chargedoff` (11.992 filas). Por eso 10.952 préstamos perdidos (entre
  los que tienen estado) quedaron como "Saludable".
- **El objetivo actual es circular.**
  - `Target_Risk_Scale` usa `Precipitation_Risk_Index`, que también es una variable del modelo.
  - El 94,0 % de las filas (101.926 de 108.422) son "Saludable", y en ellas la escala 1, 2 o 3 depende **solo** del
    índice climático.
- **El índice climático cubre 10 estados.** Los otros 41 reciben 50,0 por defecto (58.204 de 108.422 filas).
  En los 10 estados con valor, la tasa de impago de los préstamos terminados (población a modelar: 49.552) no sigue
  al índice:

  | Estado | Índice | Impago % |
  |---|---|---|
  | FL | 94,2 | 32,0 |
  | LA | 91,0 | 35,3 |
  | TX | 83,5 | 33,5 |
  | NC | 77,1 | 31,5 |
  | GA | 70,4 | 37,0 |
  | NY | 56,8 | 23,1 |
  | CA | 48,0 | 31,7 |
  | OH | 40,2 | 31,7 |
  | NV | 14,1 | 29,8 |
  | UT | 10,5 | 28,3 |

  Los estados fuera del índice tienen 30,6 % de impago (`notebooks/01_caso_negocio.ipynb`, sección 5).
- **Préstamos repetidos.** 844 `ListingKey` aparecen 2 o más veces (889 filas extra). En el 99,3 % de esos casos
  solo cambia `ProsperScore`. `df.duplicated()` no los detecta (da 0) porque compara la fila completa.
- **`BorrowerState` vacío en 5.515 filas (4,84 %).** Casi todas son antiguas: 22 en 2005, 3.000 en 2006, 2.462 en
  2007 y 31 en 2008. Desde 2009 no hay vacíos.
- **Cambio de sistema en 2009.**
  - `EstimatedEffectiveYield`, `EstimatedLoss`, `EstimatedReturn`, `ProsperRating` y `ProsperScore` están vacíos
    en el 100 % de los préstamos de 2005–2008 (25,53 % del total).
  - `CreditGrade` hace lo contrario: solo existe antes de 2009.
  - En la población a modelar, `EstimatedEffectiveYield` está vacío en el 47,6 % de las filas.
- **Fechas dañadas.**
  - `ListingCreationDate` llega como `09:29.3` (solo minutos y segundos, típico de una conversión de Excel).
  - `DateCreditPulled` mezcla ese formato con `dd/mm/aaaa hh:mm`.
  - `LoanOriginationDate` (`dd/mm/aaaa`) y `LoanOriginationQuarter` (`Q3 2007`) sí son legibles.
- **Categorías inconsistentes en `IncomeRange`.**
  - `'$0 '` lleva un espacio al final (621 filas) y `'Not employed'` usa minúscula (806 filas).
  - El mapa del notebook (`'$0'`, `'Not Employed'`) no las reconoce; terminan en 0 por el `fillna(0)`, no por
    el mapa.
  - `Not displayed` (7.741 filas) se codifica como 0, igual que "sin ingresos".
- **Valores imposibles o en el tope.**
  - `CreditScoreRangeLower` = 0 en 133 filas, cuando el rango normal es 500–880.
  - `StatedMonthlyIncome` = 0 en 1.394 filas y > 100.000 USD/mes en 17 (máximo 1.750.003).
  - `DebtToIncomeRatio` = 10,01 en 272 filas: es el tope del sistema, no un valor real. Además 799 filas están
    por encima de 1.
  - `EstimatedEffectiveYield` < 0 en 190 filas: es posible (pérdida estimada), así que se conserva.
  - `MonthlyLoanPayment` = 0 en 935 filas.
- **Vacíos en variables financieras.** `DebtToIncomeRatio` 7,51 %, `BorrowerAPR` 25 filas (0,02 %).
- **Imputación que no funciona.** En el notebook, `df[col].fillna(..., inplace=True)` lanza `ChainedAssignmentError`
  con pandas 3 y **no imputa nada**. Además, la imputación con mediana se hace sobre todos los datos antes de
  partir.
- **Datos personales.** No hay nombres, documentos ni direcciones. Hay llaves seudónimas (`MemberKey`,
  `ListingKey`, `LoanKey`, `GroupKey`) y cuasi-identificadores (`Occupation`, 67 valores; `BorrowerState`).

## Sospechas de fuga de información

- **Se conocen después de otorgar el préstamo** y se excluyen:
  - `LP_CustomerPayments`, `LP_CustomerPrincipalPayments`, `LP_InterestandFees`, `LP_ServiceFees`,
    `LP_CollectionFees`, `LP_GrossPrincipalLoss`, `LP_NetPrincipalLoss` y `LP_NonPrincipalRecoverypayments`;
  - `ClosedDate`, `LoanCurrentDaysDelinquent`, `LoanFirstDefaultedCycleNumber` y `LoanMonthsSinceOrigination`;
  - `LoanStatus`, que es la fuente del objetivo.
- **`Target_Risk_Scale` y `Financial_Status`** del notebook se calculan con el objetivo y el índice climático;
  no pueden ser variables.
- **`BorrowerState_Encoded`** (frecuencia del estado) se calcula sobre todo el dataset. Debe calcularse dentro del
  `Pipeline`, solo con entrenamiento.
- **Se miden con y sin ellas en la etapa 4:**
  - `Investors` y `PercentFunded` se conocen al cerrar la financiación, antes del desembolso. Hay que confirmar si
    están disponibles en el momento de la decisión.
  - `EstimatedLoss`, `EstimatedReturn`, `ProsperRating` y `ProsperScore` son el propio puntaje de riesgo de Prosper:
    pueden dominar el modelo.

## Decisiones

> Mínimo **5**. Cada una con una cifra que la respalda, una acción concreta y un motivo.

| # | Hallazgo (con cifra) | Decisión | Motivo |
|---|---|---|---|
| 1 | `Target_Risk_Scale` depende del índice climático en el 94,0 % de las filas, y 10.952 `Chargedoff` quedaron como "Saludable" | Objetivo `is_default` (aprobado el 30 oct) = 1 si `LoanStatus` ∈ {`Chargedoff`, `Defaulted`} y 0 si es `Completed`. Se excluyen `Current` (56.576), `Past Due` (2.067), `FinalPaymentInProgress` (205) y `Cancelled` (5) | El resultado de un préstamo sin terminar no se conoce, y el objetivo no puede construirse con una variable del modelo |
| 2 | 844 `ListingKey` repetidos (889 filas extra); el 99,3 % solo difiere en `ProsperScore` | Dejar una fila por `ListingKey` (la primera) | Es el mismo préstamo; repetirlo le da doble peso y puede caer en entrenamiento y prueba a la vez |
| 3 | 15.744 prestatarios con varios préstamos (38.149 filas; 7.028 en la población a modelar) | Partir por `MemberKey` con `StratifiedGroupKFold` / `GroupShuffleSplit` | Si un prestatario está en entrenamiento y en prueba, la métrica se infla |
| 4 | `BorrowerState` vacío en 5.515 filas (4,84 %), casi todas de 2006–2007 | Eliminar esas filas y anotar el efecto en la distribución por año | Sin estado no se puede asignar el índice climático, que es la variable central del caso |
| 5 | 12 columnas se conocen después de otorgar el préstamo (`LP_*`, `ClosedDate`, `LoanCurrentDaysDelinquent`, `LoanFirstDefaultedCycleNumber`, `LoanMonthsSinceOrigination`) | Excluirlas al cargar | Contienen la respuesta: el modelo "acertaría" sin aprender nada útil |
| 6 | `IncomeRange`: `'$0 '` con espacio (621), `'Not employed'` (806) y `Not displayed` (7.741) | Quitar espacios y mapear explícitamente; `Not displayed` queda como su propia categoría, no como 0 | No mostrar el ingreso no es lo mismo que no tener ingresos |
| 7 | Valores imposibles: `CreditScoreRangeLower` = 0 (133) y `StatedMonthlyIncome` > 100.000 (17) | Convertirlos en vacío | No son valores reales; se imputan después dentro del `Pipeline` |
| 8 | `EstimatedEffectiveYield` y `ProsperRating` vacíos en el 100 % de 2005–2008 (47,6 % de la población a modelar) | Dejar el vacío y no imputar fuera del `Pipeline`; en la etapa 4 se decide si se usan con un indicador "antes de 2009" | El vacío significa "la métrica no existía", no "dato perdido" |
| 9 | `ListingCreationDate` y `DateCreditPulled` dañadas (`09:29.3`) | No usarlas; usar `LoanOriginationDate` / `LoanOriginationQuarter` para el orden temporal | No se pueden recuperar las fechas reales |
| 10 | 41 de 51 estados reciben el índice por defecto 50,0 (58.204 filas) | Usar `Precipitation_Risk_Index` solo como variable, documentar su fuente y medir el modelo con y sin ella | Es una hipótesis del caso, no un hecho; hay que probarla con datos |

## Qué queda abierto

- **Validar con el instructor** el objetivo `is_default` y la métrica AUC-PR (ambos aprobados por el grupo el 30 oct).
- **Índice climático:** el grupo lo declaró **supuesto académico** el 30 oct, porque no tiene la tabla de origen.
  - Se usa como hipótesis y así debe presentarse en el informe y en la app.
  - Mejora posible: reemplazarlo por una fuente pública que cubra los 51 estados.
- **Orden temporal:** la tasa de impago cambia mucho por año entre los terminados (53,1 % en 2006, 12,9 % en 2013).
  Los préstamos recientes que ya terminaron son sobre todo los que terminaron rápido. Hay que decidir si la prueba
  usa solo los años más recientes o si se agrega el año como variable.
- **Variables de Prosper** (`ProsperRating`, `EstimatedLoss`, `EstimatedReturn`, `ProsperScore`): medir el modelo
  con y sin ellas en la etapa 4.
- **`DebtToIncomeRatio` = 10,01** (272 filas): decidir si se deja como tope o se convierte en vacío.
- **`StatedMonthlyIncome` = 0** (1.394 filas): revisar si coincide con `IncomeRange` `$0` / `Not employed` antes
  de tratarlo como imposible.
- **`MonthlyLoanPayment` = 0** (935 filas): averiguar qué significa una cuota 0 en un préstamo otorgado.
- **`EmploymentStatus`** cambia en el 30,6 % de los prestatarios repetidos: revisar si Prosper cambió las
  categorías con el tiempo.
- **Prestatarios repetidos** tienen la mitad de impago (18,1 % frente a 37,3 %): evaluar en la etapa 4 una variable
  de "préstamos previos en Prosper", disponible al otorgar el préstamo (`TotalProsperLoans`).
