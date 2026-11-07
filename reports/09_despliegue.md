# Despliegue de la app

> Plantilla en blanco. Complétala durante la clase 5 (viernes 6 de noviembre), después de desplegar la app.
> Guía paso a paso: `material-del-curso/guias/streamlit-despliegue.md` y `material-del-curso/kit/guia-despliegue-y-presentacion.md`.

## 1. Enlace y estado

| Dato | Valor |
|---|---|
| Enlace público de la app | |
| Plataforma | Streamlit Community Cloud |
| Repo, rama y archivo principal | |
| Versión de Python elegida | ☐ 3.12  ☐ otra → motivo: _______________ |
| ¿Se comprobó en una **ventana privada**? | ☐ sí  ☐ no |
| ¿Se desplegó? | ☐ sí  ☐ no → **plan B** (apartado 4) |

## 2. Decisiones de despliegue y su motivo

| Decisión | Motivo |
|---|---|
| La app carga `models/model.joblib` desde el repo y **no consulta Databricks** | En la nube no hay credenciales ni debe haberlas, y la app no depende de otra plataforma. Una prueba la abre y evalúa en una copia con solo `app/`, `src/`, `models/model.joblib` y `models/input_schema.json` |
| Versiones fijadas en `requirements.txt` | Streamlit Community Cloud lee ese archivo. El modelo guardado con Python 3.14 cargó en Python 3.12.16 con probabilidades idénticas a las de la etapa 7 (diferencia máxima 0,0; solo se compararon probabilidades, sin calcular métricas) |
| Qué NO se subió al repo (y por qué) | `.env` y tokens (seguridad); `data/raw/` y los parquet con `MemberKey` (datos personales); `mlflow_local.db` y `models/final_pipeline.joblib` (son locales y regenerables). Lo define `.gitignore` |
| Los campos numéricos no tienen mínimo ni máximo en pantalla | Con límites, Streamlit impide escribir -500 y nadie vería el mensaje de error. Rechaza `validate_inputs`, que nombra el campo y su rango (rúbrica A3) |
| Vacío significa "No sé": los números empiezan vacíos y las listas en "(no sé)", que va primero | Evita sugerir datos en el formulario en blanco (ni `$0` ni la calificación `A` salen elegidos) y quita 33 casillas. El pipeline ya imputa los vacíos |
| El valor del ejemplo se pone en `session_state`, no en el `value` del campo | Con `value`, Streamlit devuelve ese número cuando la persona borra el campo: "No sé" no funcionaría sobre un ejemplo. Se encontró con una prueba de la app y se confirmó en el código de Streamlit 1.66.0 |
| La recomendación traduce `decision`: `impago` es **Enviar a revisión**; `pagó`, **Sin revisión prioritaria** | Una sola fuente para la regla congelada (P(impago) > 0,2): la app no vuelve a comparar con 0,2 y el empate queda en "sin revisión" |
| No se muestra `needs_review` en la pantalla | Esa señal decide en 0,5 y el umbral es 0,2: casi toda solicitud marcada saldría como "el modelo duda" |
| Las cifras de rendimiento viajan en `models/input_schema.json`, copiadas de `reports/07_metricas_test.json` por el notebook 09 | La app no depende de `reports/` para arrancar y ninguna cifra se escribe a mano. Una prueba compara cada valor con el reporte |
| El propósito del préstamo y Sí/No se muestran por su nombre; el modelo recibe el valor original | La analista no conoce los códigos, y cambiar los valores rompería las categorías del entrenamiento y la identidad de las probabilidades. `IncomeRange` y `EmploymentStatus` siguen en inglés, tal como las conoce el modelo: no estaban en el alcance de `category_labels` |
| Caso límite de la demo: préstamo que cayó en impago, plazo de 36 a 12 meses (de 45,7 % a 17,0 %) | Se buscó con el modelo y los ejemplos, sin usar la prueba. En una búsqueda de cada dato por su rango observado, `Term` es el único que cruza 20 % en este ejemplo. En el préstamo pagado (6,6 %) ningún dato por sí solo lo cruza: el máximo es 14,4 %. El cambio es parcial: la cuota no se recalcula sola |

**Datos esenciales (6 nov).** La app pide a la vista 12 datos, elegidos por su peso SHAP de la etapa 7, sin `CreditGrade`, que solo existe antes de 2009, y con el monto. Los otros 27 quedan plegados como opcionales. El modelo sigue usando los 39: lo que no se llena se completa con valores típicos. Medido en los 9.910 préstamos reservados, sin usar la prueba: AUC-PR 0,6080 a 0,5816; desde julio de 2009, 0,4898 a 0,4382; costo 0,5073 a 0,5424; cambia la decisión en el 11,4 % de los préstamos. Sigue por encima de la línea base, pero rinde menos que con todos los datos, y por eso la app lo dice a la vista. La medición está en `notebooks/09_inferencia.ipynb`.

## 3. Pruebas del enlace público

| Caso | Datos usados | Resultado esperado | Resultado real |
|---|---|---|---|
| Normal | | | |
| Límite (cambia la decisión) | | | |
| Inválido (debe rechazarse con un mensaje claro) | | | |
| Con un campo en «No sé» | | | |

## 4. Problemas encontrados y plan B

- Errores de despliegue que aparecieron y cómo se resolvieron (qué decía el registro y qué se cambió): _______________
- **Plan B** (si la app falla en vivo): captura con fecha y repo → `_______________`; app en local → `_______________`
- Si **no se desplegó**: **plan de despliegue escrito** (qué se intentó, qué error dio, qué harían): _______________

## 5. Ensayo cronometrado (clase 5)

| Parte | Tiempo previsto | Tiempo real |
|---|---|---|
| Caso de negocio | 2 min | |
| App (demo en vivo) | 4 min | |
| Resultados | 3 min | |
| Cierre | 1 min | |
| **Total** | **10 min** | |

- ¿Se pasó de 10 minutos? ☐ no  ☐ sí → qué se recortó: _______________
- Retroalimentación recibida (lo mejor y la corrección que propusieron): _______________
- **Corrección concreta que hicimos por ella:** _______________
- Quién habla de qué y quién responde las preguntas técnicas: _______________
