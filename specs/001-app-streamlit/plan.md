# Implementation Plan: App de Eco-Score para priorizar la revisión

**Branch**: `camilo/speckit` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-app-streamlit/spec.md`

## Summary

Convertir la plantilla `app/streamlit_app.py` en la app de Eco-Score: la analista carga un préstamo de ejemplo o llena el
formulario, y recibe **enviar a revisión** o **sin revisión prioritaria** con la probabilidad de impago. El modelo y la regla no
cambian. La lógica nueva va en `src/proyecto/inference/`, con pruebas; la app solo dibuja. Las cifras de rendimiento viajan dentro
de `models/input_schema.json`, generadas por el notebook 09 desde los reportes.

## Technical Context

**Language/Version**: Python 3.12 en la nube. El `.venv` local usa 3.14.10; la verificación final se repite en un entorno 3.12 temporal.

**Primary Dependencies**: Streamlit 1.66.0, pandas 3.0.6, scikit-learn 1.9.1, lightgbm 4.7.0, joblib 1.6.0 (ya fijadas en `requirements.txt`; no se agrega ninguna)

**Storage**: archivos del repositorio: `models/model.joblib` y `models/input_schema.json`. Sin base de datos ni historial.

**Testing**: pytest (`tests/test_inference.py`, nuevo `tests/test_presentation.py`, nuevo `tests/test_app.py` con `streamlit.testing`)

**Target Platform**: Streamlit Community Cloud (Linux, Python 3.12)

**Project Type**: aplicación web de una sola página

**Performance Goals**: una recomendación en menos de 2 segundos después de cargar la app

**Constraints**: sin credenciales; sin Databricks ni MLflow en la app; probabilidades idénticas a las de la etapa 7

**Scale/Scope**: una solicitud a la vez; 39 campos; demo de 4 minutos

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo se cumple | Estado |
|---|---|---|
| I. Datos originales | No se toca `data/raw/` | ✅ |
| II. Partición por grupo | No se parte ni se reentrena | ✅ |
| III. La prueba se abre una vez | No se calcula ninguna métrica nueva. La prueba solo se usa para comparar probabilidades contra las guardadas; el umbral sigue congelado | ✅ |
| IV. Decisiones escritas | Decisiones en `research.md`, `reports/09_despliegue.md` y sección 7 de la especificación; cada función con prueba | ✅ |
| V. Nada sensible | Sin `.env` ni tokens. Los ejemplos son préstamos reales sin identificadores | ✅ |
| VI. Código entendible | La app solo orquesta; la lógica vive en `src/`, en español y con nombres en inglés | ✅ |
| VII. Nada inventado | Las cifras se copian de los reportes con el notebook 09; una prueba las compara | ✅ |

**Después del diseño:** los siete siguen en ✅. No hay violaciones que justificar.

## Project Structure

### Documentation (this feature)

```text
specs/001-app-streamlit/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/app-ui.md
├── checklists/requirements.md
└── tasks.md            # lo crea /speckit-tasks
```

### Source Code (repository root)

```text
app/streamlit_app.py                 # se reescribe: solo dibuja y llama a src/
src/proyecto/config.py               # + LISTING_CATEGORY_LABELS, YES_NO_LABELS, FIELD_GROUPS
src/proyecto/inference/predict.py    # validate_inputs usa etiquetas y formato legible en los mensajes
src/proyecto/inference/presentation.py  # NUEVO: recomendación, datos faltantes, resumen de rendimiento
notebooks/09_inferencia.ipynb        # agrega al esquema grupos, nombres de categorías y rendimiento
models/input_schema.json             # se regenera con el notebook 09
tests/test_presentation.py           # NUEVO
tests/test_app.py                    # NUEVO: la app completa, sin navegador
tests/test_inference.py              # ajustes por los mensajes con etiqueta
reports/09_despliegue.md             # solo las decisiones de esta pieza
```

**Structure Decision**: se respeta la estructura obligatoria del curso; `presentation.py` queda en `inference/` porque traduce el
resultado de `predict` para una persona y no importa Streamlit, así que se puede probar sin la app.

## Fuera de esta pieza

- Duplicado `decide_min_cost` en `train.py` y `predict.py`: se mantiene. Unificarlo haría que la app importara `xgboost`, o
  movería una función ya registrada en la etapa 5. Queda anotado en `research.md`.
- Funciones auxiliares de los notebooks (`profile`, generación de la ficha y otras): no afectan al despliegue.
- Borrar `material-del-curso/`, hacer commit, desplegar, presentación e informe.

## Complexity Tracking

No aplica: el Constitution Check no tiene violaciones.
