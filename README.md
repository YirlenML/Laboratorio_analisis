# Proyecto Eco-Score

Modelo predictivo que mide el impago por impactos climáticos (inundación y/o precipitación extrema) con un enfoque académico.

## Conocimiento inicial de dat
La base de datos utilizada es un dataframe extraído del sitio Kaggle el cual contiene información financiera de los clientes ubicados en EE.UU, cada fila representa un préstamo individual otorgado a un único prestatario

No contiene transacciones, ni saldos de cuentas, es la hoja de vida de un crédito espeçifico desde el momento en que se originó en la plataforma con su status, cierre o vigencia al momento de cierre del análisis, consolidando información noviembre de 2005 hasta marzo de 2014.

Nota: El periodo analizado permite incluir la ventana de tiempo de la gran recesión de 2008 permitiendo estudiar la reacción de los prestatarios ante choques financieros en combinación con los patrones climáticos extremos de esta década.

## Configuración

Se partió de conocer la el dataframe y seleccionar las columnas que si generarán valor al modelo en función del caso de estudio planteado, para optimizar su procesamiento.

## Qué contiene
Estructura obligatoria del curso. Cada carpeta tiene un propósito:

| Carpeta | Contenido |
|---|---|
| `.specify/` y `.claude/` | Entorno de IA: constitución del proyecto, Spec Kit (`/speckit-…`) y subagentes |
| `specs/` | Lo que genera Spec Kit: `spec.md`, `plan.md`, `tasks.md` de cada pieza (aparece al usarlo) |
| `especificaciones/` | Guías que se llenan **antes** de programar cada etapa |
| `data/raw/` | Datos originales, intocables |
| `data/processed/` | Datos limpios generados por el código |
| `notebooks/` | Un notebook por etapa; solo orquestan |
| `src/proyecto/` | Código reutilizable (data, features, models, tracking, inference) |
| `tests/` | Pruebas con `pytest` |
| `models/` | `model.joblib` y `ficha_modelo.md` |
| `app/` | `streamlit_app.py` |
| `reports/` | Una sección por hito e `informe_tecnico.md` |
| `presentacion/` | `ejecutiva.md` (máximo 5 diapositivas) |

## Cómo ejecutarlo
```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt   # en Mac/Linux: .venv/bin/python
cp .env.example .env     # completa PROFILE o DATABRICKS_HOST y DATABRICKS_TOKEN
python scripts/check_databricks.py
pytest
streamlit run app/streamlit_app.py
```

## Equipo
| Integrante | Rol |
|---|---|
| Carolina Florez Lopez | Datos |
| Monica Patricia Vega | App |
| Juan Camilo Ramirez | Negocio |
| Carolina Giraldo Toro | Modelado |
| Yirlen Dayanny Mosquera | App |

Especificación del proyecto: [`especificacion-proyecto.md`](especificacion-proyecto.md) · Especificaciones por etapa: [`especificaciones/`](especificaciones/)
