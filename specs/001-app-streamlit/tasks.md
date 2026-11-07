# Tasks: App de Eco-Score para priorizar la revisión

**Input**: `specs/001-app-streamlit/` (spec.md, plan.md, research.md, data-model.md, contracts/app-ui.md, quickstart.md)

**Tests**: sí, por `CLAUDE.md` (regla 9) y por pedido del usuario: cada tarea de código tiene su prueba. Una tarea se marca hecha solo cuando su prueba pasa.

**Reglas para quien implementa**: textos en español y nombres de código en inglés. No cambiar el modelo, sus parámetros ni la regla de decisión. No calcular métricas con la prueba. No hacer commit, push ni despliegue. No tocar `data/raw/`, `reports/07_*`, `reports/08_*` ni `.env`. Comando de pruebas: `.venv/Scripts/python.exe -m pytest -q`, con `PYTHONUTF8=1`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia de usuario de `spec.md`

---

## Phase 1: Setup

- [x] T001 Confirmar el punto de partida: ejecutar pytest (deben pasar 82 pruebas) y comprobar que existen `models/model.joblib`, `models/input_schema.json` y `mlflow_local.db`; si algo falla, detenerse y reportarlo

---

## Phase 2: Foundational

**Propósito**: datos y funciones que usan todas las historias.

- [x] T002 Agregar a `src/proyecto/config.py` `LISTING_CATEGORY_LABELS` (21 códigos, de "0" a "20", traducidos del diccionario `data/diccionario_datos.md`, con "0" = "No disponible"), `YES_NO_LABELS` (`FALSO` = "No", `VERDADERO` = "Sí") y `FIELD_GROUPS` con 5 grupos: "Condiciones del préstamo", "Ingreso y empleo", "Historial de crédito", "Evaluación de Prosper" e "Historial en Prosper"
- [x] T003 Crear `tests/test_presentation.py` con una prueba que falle si `FIELD_GROUPS` no contiene las 39 columnas de `form_columns()` exactamente una vez, y una prueba de que `LISTING_CATEGORY_LABELS` tiene los 21 códigos del esquema
- [x] T004 Crear `src/proyecto/inference/presentation.py`, sin importar Streamlit, con `display_label(schema, column, value)` y su prueba en `tests/test_presentation.py`: devuelve el nombre visible y, sin nombre, el valor original
- [x] T005 Agregar a `notebooks/09_inferencia.ipynb`, en la sección 2, las claves `field_groups`, `category_labels` y `performance` del esquema según `specs/001-app-streamlit/data-model.md`, leyendo las cifras de `reports/07_metricas_test.json`, sin escribirlas a mano
- [x] T006 Ejecutar el notebook 09 y confirmar la salida `probabilidades idénticas a las del notebook 07: True` y que `models/input_schema.json` contiene las 3 claves nuevas
- [x] T007 Agregar a `tests/test_presentation.py` una prueba que compare `performance` de `models/input_schema.json` con `reports/07_metricas_test.json`, valor por valor

**Checkpoint**: datos listos; las historias se pueden implementar.

---

## Phase 3: User Story 1 - Evaluar una solicitud (Priority: P1) 🎯 MVP

**Goal**: recomendación en lenguaje de negocio.

**Independent Test**: evaluar una solicitud válida muestra la recomendación y la probabilidad.

- [x] T008 [US1] Escribir en `tests/test_presentation.py` las pruebas de `build_recommendation`: `impago` da "Enviar a revisión", `pagó` da "Sin revisión prioritaria", la probabilidad no se altera y la explicación menciona 20 %
- [x] T009 [US1] Implementar `build_recommendation(row, schema, warnings)` en `src/proyecto/inference/presentation.py`, traduciendo `decision` sin volver a comparar con 0,2 (research.md, decisión 3)
- [x] T010 [US1] Reescribir `app/streamlit_app.py`: orden de la página de `contracts/app-ui.md`, grupos con `field_groups`, importación directa de `proyecto`, constante `UNKNOWN = "(no sé)"` y mensaje claro si falta un archivo; sin `needs_review`, sin "el modelo está seguro" y sin mostrar `pagó`/`impago` como decisión
- [x] T011 [US1] Crear `tests/test_app.py` con `streamlit.testing`: la app abre sin excepciones y evaluar un ejemplo muestra una de las dos recomendaciones
- [x] T012 [US1] Agregar a `tests/test_app.py` una prueba en carpeta temporal con solo `app/`, `src/`, `models/model.joblib` y `models/input_schema.json`: la app abre y evalúa (SC-006)

**Checkpoint**: US1 funciona por sí sola.

---

## Phase 4: User Story 2 - Demostrar con casos preparados (Priority: P1)

**Goal**: ejemplos que llenan el formulario y formulario neutro.

**Independent Test**: elegir cada ejemplo y evaluar sin escribir nada.

- [x] T013 [US2] Escribir en `tests/test_app.py` las pruebas: cada ejemplo llena sus 39 campos, el cambio entre ejemplos no deja valores anteriores, volver a "Formulario en blanco" vacía todo y las 6 listas empiezan en "(no sé)"
- [x] T014 [US2] Implementar en `app/streamlit_app.py` el selector fuera del formulario, con la clave de cada campo incluyendo el ejemplo elegido (research.md, decisión 6), y valores nulos iniciales en el formulario en blanco
- [x] T015 [US2] Agregar a `tests/test_app.py` una prueba de que, tras evaluar, cambiar de ejemplo elimina el resultado anterior (FR-005)
- [x] T016 [US2] Agregar a `tests/test_app.py` una prueba de caso límite: modificar un dato de un ejemplo hasta que cambie la recomendación, buscando el dato con el modelo y solo con los ejemplos, sin usar la prueba

**Checkpoint**: la demo normal y límite funciona.

---

## Phase 5: User Story 3 - Error claro con datos inválidos (Priority: P1)

**Goal**: rechazar datos imposibles con un mensaje útil.

**Independent Test**: -500 en el puntaje muestra el error y ninguna recomendación.

- [x] T017 [US3] Escribir en `tests/test_inference.py` pruebas de que el error usa la etiqueta en español y los números no salen en notación científica, y de que se nombran todos los campos inválidos
- [x] T018 [US3] Cambiar `validate_inputs` en `src/proyecto/inference/predict.py` para usar `schema["labels"]` y números legibles, conservando las pruebas actuales
- [x] T019 [US3] Quitar mínimo y máximo de los campos numéricos en `app/streamlit_app.py` (research.md, decisión 1)
- [x] T020 [US3] Agregar a `tests/test_app.py` las pruebas: -500 muestra el error con el campo y el rango y sin recomendación; corregirlo devuelve la recomendación; un valor en el límite del rango se acepta; un valor posible y raro muestra advertencia

**Checkpoint**: los tres casos de la demo funcionan.

---

## Phase 6: User Story 4 - Evaluar sin todos los datos (Priority: P2)

**Goal**: "No sé" funciona y queda avisado.

**Independent Test**: formulario en blanco y evaluar.

- [x] T021 [P] [US4] Escribir en `tests/test_presentation.py` las pruebas de `count_missing`, y de que con los 39 datos vacíos se agrega el aviso de valores típicos
- [x] T022 [US4] Implementar `count_missing(form_row, schema)` en `src/proyecto/inference/presentation.py` y su uso en `build_recommendation`
- [x] T023 [US4] Mostrar "Se evaluó sin N de 39 datos" en `app/streamlit_app.py` y probar en `tests/test_app.py` el formulario en blanco y un ejemplo con un dato vacío

---

## Phase 7: User Story 5 - Conocer los límites (Priority: P2)

**Goal**: uso responsable y rendimiento a la vista.

**Independent Test**: abrir la app sin evaluar.

- [x] T024 [P] [US5] Escribir en `tests/test_presentation.py` las pruebas de `performance_lines`: coma decimal, 0,4789 antes que 0,6209 e intervalo incluido
- [x] T025 [US5] Implementar `performance_lines(schema)` en `src/proyecto/inference/presentation.py`
- [x] T026 [US5] Mostrar el aviso y el rendimiento sin expansores en `app/streamlit_app.py`, y probar en `tests/test_app.py` que aparecen antes de evaluar

---

## Phase 8: User Story 6 - Formulario largo (Priority: P3)

**Goal**: grupos y nombres comprensibles.

**Independent Test**: recorrer el formulario.

- [x] T027 [US6] Mostrar categorías con `display_label` en `app/streamlit_app.py`, enviando al modelo el valor original
- [x] T028 [US6] Probar en `tests/test_app.py` que elegir "Consolidación de deudas" entrega el valor "1" y que el resultado es igual al del código original

---

## Phase 9: Polish

- [x] T029 Ejecutar pytest completo con `.venv` y confirmar que pasa todo
- [x] T030 Confirmar en `notebooks/09_inferencia.ipynb` la diferencia máxima 0.00e+00 frente a `data/processed/prueba_probabilidades.joblib`, sin calcular métricas
- [x] T031 Repetir la carga del modelo y las pruebas de `tests/test_app.py` con Python 3.12 en el entorno temporal `venv312` de la carpeta de trabajo de la sesión; instalar `pytest` allí si falta
- [x] T032 Escribir en `reports/09_despliegue.md`, sección 2, las decisiones de esta pieza y su motivo, y agregarlas a la sección 7 de `especificacion-proyecto.md`
- [x] T033 Revisar `app/streamlit_app.py` contra `specs/001-app-streamlit/contracts/app-ui.md`, confirmar que no importa `mlflow` ni usa credenciales, y marcar las tareas hechas en este archivo

---

## Phase 10: Datos esenciales y diseño (pedido del usuario, 6 nov)

- [x] T034 Medir en la reserva, nunca en la prueba, qué se pierde con menos datos y fijar `ESSENTIAL_FIELDS` en `src/proyecto/config.py`
- [x] T035 Agregar `blank_unasked` en `src/proyecto/inference/predict.py` y la medición al esquema en `notebooks/09_inferencia.ipynb`, con prueba en `tests/test_presentation.py`
- [x] T036 Agregar `essential_columns`, `optional_groups`, `review_threshold`, `reduced_input_note`, `performance_tiles_html` y `probability_meter_html` en `src/proyecto/inference/presentation.py`, con pruebas en `tests/test_presentation.py`
- [x] T037 Rediseñar `app/streamlit_app.py`, con `app/style.css` y `.streamlit/config.toml`, y actualizar `tests/test_app.py`
- [x] T038 Comprobar la app en Edge real: casos normal, límite, inválido y "No sé", cambio de ejemplo y ancho de celular
- [x] T039 Documentar en `specs/001-app-streamlit/spec.md`, `reports/09_despliegue.md` y `especificacion-proyecto.md`

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → US1 → resto de historias → Polish.
- US2, US3, US4, US5 y US6 dependen de US1 porque todas editan `app/streamlit_app.py`; conviene hacerlas en orden.

### Parallel Opportunities

T021 y T024 solo escriben pruebas y pueden ir en paralelo. Las demás tocan el mismo archivo o dependen de una anterior.

```text
Parallel: T021 (count_missing) · T024 (performance_lines)
```

## Implementation Strategy

- **MVP**: Fases 1 a 3 (US1), ya usable con un ejemplo.
- **Mínimo para la exposición**: hasta la Fase 5, que cubre los casos normal, límite e inválido.
- **Completo**: Fases 6 a 9.
- Detenerse en cada checkpoint y correr las pruebas antes de seguir.
