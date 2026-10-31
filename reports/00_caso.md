# Ficha de caso

> Instrucciones y un ejemplo completo (CreditSight): `material-del-curso/evaluacion/ficha-de-caso.md`.
> Estados: `borrador` → (`devuelta` → `borrador`)* → `aprobada`. Solo con la ficha **aprobada** se avanza al EDA.

- **case_id:** `eco-score`

- **business_question:**
  - El analista de riesgo de una plataforma de préstamos entre personas (Prosper, EE. UU.) debe decidir qué
    solicitudes revisar con más cuidado y en qué condiciones prestar.
  - Queremos un modelo que estime la probabilidad de **impago** de cada préstamo a partir del perfil financiero
    del prestatario, y medir si el **riesgo climático del estado** (inundación o precipitación extrema) agrega
    información a esa predicción.
  - El analista usa el puntaje para priorizar su revisión y conserva la decisión final. Enfoque académico.

- **dataset_source:** *Prosper Loan Data* (Kaggle), archivo `prosperLoanData.csv`. Enlace exacto:
  https://www.kaggle.com/datasets/henryokam/prosper-loan-data (publicado por Henry Okam). Licencia: **CC0: Public
  Domain**. El índice climático por estado (`Precipitation_Risk_Index`, 10 estados) es un **supuesto académico** del
  grupo, sin fuente verificable: se usa como hipótesis a probar, no como dato oficial.

- **dataset_rows:** 113.937 préstamos (nov. 2005 – mar. 2014). Para modelar se usan 49.552 préstamos
  **terminados** con estado conocido y sin `ListingKey` repetido.

- **dataset_columns:** 81. No hay nombres ni documentos. Hay llaves seudónimas (`MemberKey`, `ListingKey`,
  `LoanKey`, `GroupKey`).

- **target:** `is_default` (aprobado por el grupo el 30 oct). Vale 1 si `LoanStatus` ∈ {`Chargedoff`, `Defaulted`} y 0 si es
  `Completed`. Hay 15.380 impagos (31,04 %) y 34.172 pagados (68,96 %).
  - Unidad de análisis: **un préstamo**.
  - Un mismo prestatario (`MemberKey`) puede tener varios préstamos: 7.028 prestatarios suman 16.128 filas
    dentro de la población a modelar. Por eso la partición se hace **por prestatario**.

- **problem_type:** clasificación binaria (desbalanceada, 31 / 69)

- **primary_metric:** **AUC-PR de la clase impago** (aprobada por el grupo el 30 oct).
  - El impago es minoritario y el error más caro es no detectarlo.
  - AUC-PR mide si los impagos quedan arriba en la lista de revisión.
  - La exactitud no se usa: decir "nadie cae en impago" ya da 68,96 %.
  - Como control se reporta la diferencia de AUC-PR **con y sin el índice climático**, que es la respuesta a la
    pregunta del caso.

- **business_cost_note:**
  - **No detectar un impago** (falso negativo): se presta a quien no pagará y se pierde el capital. Es el error
    más caro.
  - **Marcar como riesgoso a quien sí paga** (falso positivo): se rechaza o encarece un buen crédito y se pierden
    sus intereses. El daño es recuperable porque el analista revisa.
  - Riesgo adicional de equidad: si el índice climático no agrega información, usarlo castigaría a prestatarios
    solo por su estado de residencia.
  - **Matriz de costos 4 a 1, medida con los datos** (`notebooks/01_caso_negocio.ipynb`):
    - un impago cuesta en promedio 4.672,50 USD de capital perdido (72,2 % del monto prestado);
    - un buen cliente deja en promedio 1.154,30 USD en intereses y cargos;
    - la proporción es 4,05 con medias y 4,15 con medianas.

    | real \ predicho | pagó | impago |
    |---|---|---|
    | **pagó** | 0 | 1 |
    | **impago** | 4 | 0 |

  - Línea base de costo esperado por préstamo: aprobar a todos 1,24; rechazar a todos 0,69; azar 1,07.
    El modelo debe costar menos de 0,69.

- **status:** borrador

- **reviewer_notes:** <!-- las llena el instructor -->
