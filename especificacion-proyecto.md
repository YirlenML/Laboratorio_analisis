# Especificación del proyecto

> Plantilla. Complétenla en el grupo y manténganla actualizada. Claude la lee antes de generar
> código: lo que escriban aquí manda sobre cualquier otra suposición.
>
> **Estado: borrador (30 oct).** Las cifras salen del CSV original `data/raw/prosperLoanData.csv`.
> Lo marcado como **[por confirmar]** lo decide el grupo.

## 1. Grupo

| Integrante | Rol (datos / modelado / app / negocio) |
|---|---|
| Carolina Florez Lopez | datos |
| Monica Patricia Vega | app |
| Juan Camilo Ramirez | negocio |
| Carolina Giraldo Toro | modelado |
| Yirlen Dayanny Mosquera | app |

> Roles asignados por sorteo el 30 oct. Hay 4 roles para 5 personas, por eso "app" quedó repetido.

Nombre de la "startup": **Eco-Score**   Repositorio (público): https://github.com/YirlenML/Laboratorio_analisis

## 2. Caso de negocio

- **Pregunta de negocio** (una frase, que alguien sin formación técnica entienda):
  ¿Podemos anticipar qué préstamos personales terminarán en impago y saber si vivir en un estado con alto
  riesgo de inundación o precipitación extrema agrega información a esa predicción, más allá del perfil
  financiero del prestatario?
- **¿Quién usará el resultado y qué decisión tomará con él?** El analista de riesgo de una plataforma de
  préstamos entre personas (como Prosper). Usa el puntaje para **priorizar la revisión** de solicitudes y
  ajustar condiciones (monto, plazo, tasa). El analista conserva la decisión final. Enfoque académico.
- **¿Qué cuesta equivocarse?** (cuál error es peor y por qué):
  - **No detectar un impago** (falso negativo): se presta a quien no pagará y se pierde el capital. Es el error
    **más caro**.
  - **Marcar como riesgoso a quien sí paga** (falso positivo): se rechaza o encarece un buen crédito y se pierden
    sus intereses. El daño es menor y recuperable porque el analista revisa el caso.
  - Además, penalizar a un prestatario **solo por el estado donde vive** sería injusto si el clima no agrega
    información real (ver sección 5).

## 3. Datos

- **Fuente** (enlace de Kaggle, empresa, etc.): *Prosper Loan Data* (Kaggle, publicado por Henry Okam),
  https://www.kaggle.com/datasets/henryokam/prosper-loan-data. Datos de la plataforma de préstamos Prosper,
  archivo `prosperLoanData.csv` (separador `;`).
- **Índice climático (`Precipitation_Risk_Index`):** **supuesto académico del grupo**, sin fuente verificable.
  - Es una matriz manual de 10 estados en `eco_score_pd.ipynb`, con valores de 0 a 100; los demás estados reciben 50,0.
  - Los valores se inspiraron en la idea general de los mapas de riesgo de FEMA y NOAA, pero no salen de una tabla
    citada.
  - Por eso no se presenta como dato oficial: es la hipótesis que el proyecto pone a prueba.
- **Filas / columnas:** 113.937 × 81 (préstamos originados entre nov. 2005 y mar. 2014).
- **Variable objetivo** (columna que queremos predecir o describir): `is_default` (**aprobado el 30 oct**), que vale 1 si
  `LoanStatus` es `Chargedoff` o `Defaulted` y 0 si es `Completed`. Solo se usan préstamos **terminados**, porque en
  los demás todavía no se sabe el resultado. Población: 49.552 préstamos, de los cuales 15.380 (31,04 %) cayeron
  en impago. Ver decisión 1 de `reports/01_eda.md`.
- **Tipo de problema:** ☒ clasificación (binaria)  ☐ regresión  ☐ clusterización
- **¿Una misma entidad (cliente, paciente, empresa) aparece en varias filas?** ☐ no  ☒ sí → la partición
  será por: **`MemberKey`** (prestatario). Hay 15.744 prestatarios con más de un préstamo, que suman 38.149 filas,
  y uno llega a tener 9 préstamos.
- **Datos personales o confidenciales presentes:** ☐ no  ☒ sí → no hay nombres ni documentos. Hay llaves
  seudónimas (`MemberKey`, `ListingKey`, `LoanKey`, `GroupKey`) y cuasi-identificadores (`Occupation`,
  `BorrowerState`). Las llaves se quitan de las variables del modelo y `MemberKey` se usa solo para partir.
- **Licencia o permiso de uso de los datos:** **CC0: Public Domain**, según los metadatos del dataset en Kaggle
  (consultados el 30 oct). Permite usarlo sin restricciones.

## 4. Métrica

- **Métrica principal:** **AUC-PR (precisión promedio) de la clase impago** — aprobada el 30 oct.
  **Por qué esa y no otra:** el impago es la clase minoritaria (31 %) y el error más caro es no detectarlo.
  AUC-PR mide qué tan bien se ordenan los impagos arriba de la lista de revisión, sin depender de un umbral.
  La exactitud (accuracy) no sirve: decir "nadie cae en impago" ya da 68,96 %.
- **Métricas secundarias:** recall de impago con el umbral elegido, ROC-AUC, F1 de impago y Brier (calibración).
  **Clave para el caso:** diferencia de AUC-PR **con y sin** el índice climático.
- **Línea base** (qué resultado obtiene una regla simple o un modelo trivial): predecir siempre "no impago" →
  exactitud 68,96 %, recall de impago 0 y AUC-PR igual a la proporción de impagos (≈ 0,31).

## 5. Riesgos

- **Fuga de información posible:**
  - Varias columnas solo se conocen **después** de otorgar el préstamo: `LP_*` (8 columnas de pagos y pérdidas),
    `ClosedDate`, `LoanCurrentDaysDelinquent`, `LoanFirstDefaultedCycleNumber` y `LoanMonthsSinceOrigination`.
  - La escala actual del notebook (`Target_Risk_Scale`) se construye con el índice climático, que también es una
    variable del modelo: el 94,0 % de las filas reciben su escala solo por el clima.
- **Sesgos o equidad:**
  - El índice climático asigna riesgo por **estado de residencia**. Puede castigar a toda la población de un estado.
  - 41 de los 51 estados reciben el valor por defecto 50,0 (58.204 de 108.422 filas).
  - La tasa de impago **no** sigue al índice en los 10 estados con valor: UT (10,5) tiene 28,3 % de impago y
    FL (94,2) tiene 32,0 %, mientras NY tiene 23,1 % y GA 37,0 %.
- **Datos faltantes o de mala calidad:**
  - `BorrowerState` vacío en 5.515 filas, casi todas de 2005–2007.
  - Antes de 2009 no existen `EstimatedEffectiveYield` ni `ProsperRating` (cambio de sistema de Prosper).
  - Las fechas `ListingCreationDate` y `DateCreditPulled` llegan dañadas (por ejemplo `09:29.3`).
  - Valores imposibles en `CreditScoreRangeLower` (0), `StatedMonthlyIncome` y `DebtToIncomeRatio`
    (ver `reports/01_eda.md`).
- **Límites de lo que el modelo puede decir:**
  - Muestra asociación, no causalidad: no puede afirmar que el clima **cause** impagos.
  - El índice es estatal y fijo en el tiempo, no mide un evento climático real en la fecha del préstamo.
  - Los préstamos recientes que ya terminaron son sobre todo los que terminaron rápido. Por eso la tasa de
    impago cambia mucho por año, de 53,1 % en 2006 a 12,9 % en 2013.

## 6. Entregables y fechas

| Hito | Contenido | Fecha |
|---|---|---|
| H1 | Ficha aprobada, EDA y preprocesamiento reproducible | Cierre de la clase 2 (vie 30 oct) |
| H2 | Torneo, optimización con tracking, modelo registrado, repo modular, app local | Cierre de la clase 4 (jue 5 nov) |
| H3 | App desplegada y presentación (≤ 5 diapositivas) | Clase 5 (vie 6 nov) |
| H4 | Informe técnico final (hasta 8 días tras la última clase) | Domingo 15 nov |

## 7. Decisiones tomadas (agréguenlas a medida que avancen)

| Fecha | Decisión | Motivo |
|---|---|---|
| (antes del 30 oct) | Conservar 11 de las 81 columnas (`eco_score_pd.ipynb`) | Limitaciones de procesamiento y foco en variables financiero-climáticas |
| (antes del 30 oct) | Crear `Precipitation_Risk_Index` (0–100) para 10 estados; el resto recibe 50,0 | Enfoque académico con referencia a FEMA/NOAA |
| 30 oct | El índice climático se declara **supuesto académico** sin fuente verificable | El grupo no tiene la tabla de origen de los 10 valores; se usa como hipótesis a probar, no como dato oficial |
| 30 oct · **aprobada** | Cambiar el objetivo de `Target_Risk_Scale` (4 escalas) a `is_default` binario sobre préstamos terminados | La escala actual depende del índice climático (fuga circular) y clasifica 10.952 `Chargedoff` como "Saludable" |
| 30 oct · **aprobada** | Usar el índice climático como **variable** y medir el modelo con y sin ella | Responde la pregunta de negocio sin suponer la respuesta |
| 30 oct · **aprobada** | Partir por `MemberKey`, con 20 % para prueba (semilla 42) | 15.744 prestatarios tienen varios préstamos y el 15,2 % de los repetidos tiene resultados distintos entre ellos |
| 30 oct · **aprobada** | Métrica principal: AUC-PR de la clase impago; control: costo esperado con matriz 4 a 1 | El impago es minoritario (31 %) y no detectarlo cuesta unas 4 veces más que rechazar a un buen cliente (`notebooks/01_caso_negocio.ipynb`) |
| 31 oct | Valores atípicos: cuota 0 recalculada con la fórmula de cuota fija; ingreso 0 incoherente y puntaje 0 a vacío; `DebtToIncomeRatio` = 10,01 se conserva; `Occupation` se elimina | Ver `reports/03_preprocesamiento.md` |
| 31 oct · **aprobada** | Variables finales: referencia + puntaje de Prosper + historial en Prosper, por una excepción escrita a la regla mejora / ruido > 1 | Ganan 5 de 5 pliegues, log loss / ruido > 1, de a pares > 2 y se mantienen desde julio de 2009 (`reports/04_features.md`) |
| 31 oct | El índice climático no entra al modelo | No agrega información medible: +0,0001 de AUC-PR contra la referencia y +0,0012 sobre el conjunto final, dentro del ruido (`reports/04_features.md`) |
| 31 oct | Revisión de variables: se quitan 8 columnas (redundantes, casi constantes y `CurrentlyInGroup`, que marca la época) y se agrupa `EmploymentStatus`; no se crean las tasas de comportamiento en Prosper | Rinde igual con menos columnas (AUC-PR 0,6107 frente a 0,6104); las tasas no superan el ruido (`reports/04_features.md`) |
| 31 oct | Finalistas del torneo: LightGBM y XGBoost (empate: +0,0002 de AUC-PR, 2 de 5 pliegues); se descartan random forest y regresión logística | Pierden en los 5 pliegues o quedan 0,026 de AUC-PR por debajo (`reports/05_torneo.md`) |
| 31 oct | Modelo final: LightGBM con parámetros optimizados (Optuna, 30 ensayos, MLflow local) | En prestatarios reservados mejora +0,0082 de AUC-PR con IC 95 % [+0,0041; +0,0123]; empata con XGBoost y la regla elige el más rápido (`reports/06_optimizacion.md`) |
| 5 nov | Prueba abierta una sola vez: LightGBM optimizado, sin calibrar, umbral 0,2. AUC-PR 0,6209, IC 95 % [0,6044; 0,6407]; desde julio de 2009, 0,4789 | Decisiones congeladas antes de abrir; la mejora mínima del índice climático (+0,0023) no cambia el modelo (`reports/07_validacion.md`) |
| 5 nov | Modelo registrado: `eco_score_default` versión 1, alias `champion`, en MLflow local | El equipo no tiene conexión con Databricks; es el respaldo previsto. Pendiente registrarlo en Unity Catalog (`reports/08_registro.md`) |
| 6 nov | Modelo registrado de nuevo en MLflow local (`eco_score_default` versión 1, alias `champion`) y exportado a `models/model.joblib` | El registro del 5 nov no estaba en este equipo. Mismas decisiones congeladas; probabilidades idénticas a las de la etapa 7 (`reports/08_registro.md`) |
| 6 nov | La app pregunta 39 columnas; las 4 que el modelo no usa se rellenan vacías | Son datos que no cambian la predicción: en la prueba, las probabilidades son idénticas (diferencia máxima 0,0; `notebooks/09_inferencia.ipynb`) |
| 6 nov | Rangos posibles de las 33 entradas numéricas en `PLAUSIBLE_RANGE` (`src/proyecto/config.py`); **[por confirmar por el grupo]** | Fuera de ellos la predicción se niega. Salen del diccionario de datos, de las decisiones del EDA y del criterio del analista; ningún dato de entrenamiento queda fuera |
| 6 nov | La app traduce `decision` a **Enviar a revisión** o **Sin revisión prioritaria** y no vuelve a comparar con 0,2; no muestra `needs_review` | Una sola fuente para la regla congelada. `needs_review` decide en 0,5 y casi toda solicitud marcada saldría como "el modelo duda" (`reports/09_despliegue.md`) |
| 6 nov | Los números de la app no tienen mínimo ni máximo en pantalla; vacío significa "No sé" y las listas empiezan en "(no sé)" | Permite demostrar el error con -500 (rúbrica A3) y no sugiere datos en el formulario en blanco (`reports/09_despliegue.md`) |
| 6 nov | El rendimiento de la app viaja en `models/input_schema.json`, copiado de `reports/07_metricas_test.json` por el notebook 09 | La app funciona solo con sus archivos y ninguna cifra se escribe a mano; una prueba compara cada valor con el reporte |
| 6 nov | Caso límite de la demo: préstamo que cayó en impago, plazo de 36 a 12 meses (45,7 % a 17,0 %) | Se buscó con el modelo y los ejemplos, sin usar la prueba; en el préstamo pagado ningún dato por sí solo cruza 20 % (`reports/09_despliegue.md`) |
| 6 nov | La app pide 12 datos esenciales; los otros 27 son opcionales y quedan plegados | Facilita el uso. Tiene un costo medido en la reserva: AUC-PR 0,6080 a 0,5816; desde julio de 2009, 0,4898 a 0,4382; costo 0,5073 a 0,5424; cambia la decisión en el 11,4 % de los préstamos. La app lo muestra (`reports/09_despliegue.md`) |
