# Informe de la optimización

> Resultado de `notebooks/06_optimizacion.ipynb` (re-ejecutado desde cero el 31 oct con el conjunto de variables revisado y las funciones alineadas con el ejemplo del curso; los resultados se reprodujeron exactos). La mejor
> puntuación de una búsqueda es **optimista**: se comprueba en prestatarios que la búsqueda no vio. Código:
> `src/proyecto/models/tuning.py`; parámetros: `reports/06_mejores_parametros.json`; tabla:
> `reports/06_optimizacion_tabla.csv`.

## Diseño de la búsqueda

- **Finalistas optimizados:** LightGBM y XGBoost (empatados en el torneo).
- **Métrica optimizada:** AUC-PR de impago (la principal del proyecto).
- **Espacio de búsqueda:**

| Parámetro | Rango | Motivo |
|---|---|---|
| `n_estimators` / `learning_rate` (ambos) | 150–600 / 0,01–0,2 (log) | Se compensan entre sí |
| `num_leaves` (LightGBM) | 15–63 | Complejidad de cada árbol; más sobreajusta con ~22.000 filas de búsqueda |
| `min_child_samples` (LightGBM) / `min_child_weight` (XGBoost) | 20–300 / 1–20 (log) | Regularización: tamaño mínimo de las hojas |
| `max_depth` (XGBoost) | 3–8 | XGBoost crece por profundidad |
| `subsample` / `colsample_bytree` (ambos) | 0,6–1 / 0,4–1 | Aleatoriedad por filas y columnas |
| `reg_lambda` (ambos) | 0,001–10 (log) | Penalización L2 |

- **Presupuesto (fijado antes):** 30 ensayos para LightGBM y 20 para XGBoost, que es casi el doble de lento.
- **Prestatarios reservados:** el 25 % de los prestatarios de entrenamiento (8.076 prestatarios, 9.910 préstamos),
  partidos por `MemberKey` con semilla 7. La búsqueda usa el 75 % restante con 3 pliegues por prestatario. La prueba
  sigue cerrada.

## Seguimiento (tracking)

- **Dónde quedó registrado:** MLflow **local** (`mlflow_local.db`), porque el repo no tiene `.env` con la conexión a
  Databricks. Experimento `eco-score-optimizacion`. Cuando el grupo configure `.env`, basta con volver a ejecutar el
  notebook.
- **¿Está cada ensayo como una ejecución con parámetros, métrica y etiquetas?** ☒ sí. Hay 50 ensayos anidados, con
  todas las métricas (media y desviación entre pliegues) y las etiquetas `etapa`, `modelo` y `metrica_optimizada`, más
  2 ejecuciones madre.
- **Mejor ejecución:** LightGBM, ensayo 24, AUC-PR 0,6131 ± 0,0121 en la búsqueda (run_id `fba5d3ae6e22…`).

## Resultados de la búsqueda

- **Mejor AUC-PR en validación cruzada** (optimista): LightGBM 0,6131 y XGBoost 0,6117.
- **Parámetros que más influyeron:**
  - LightGBM: `reg_lambda` (0,47), `min_child_samples` (0,14) y `colsample_bytree` (0,13), es decir, la
    regularización;
  - XGBoost: `colsample_bytree` (0,39), `n_estimators` (0,35) y `min_child_weight` (0,21).
- **Mejores parámetros de LightGBM:** `n_estimators` 598, `learning_rate` 0,0111, `num_leaves` 61,
  `min_child_samples` 60, `subsample` 0,81, `colsample_bytree` 0,42 y `reg_lambda` 0,60.

## Comprobación honesta (prestatarios reservados)

> Parámetros de **partida** (los del torneo) frente a **optimizados**. Los dos modelos se entrenan con los datos de
> búsqueda y se evalúan en los prestatarios reservados. Intervalo del 95 % remuestreando **prestatarios** completos
> (500 veces).

| Modelo | AUC-PR partida | AUC-PR optimizado | Diferencia (optimizado − partida) | Intervalo 95 % |
|---|---|---|---|---|
| LightGBM | 0,5999 | 0,6080 | +0,0082 | [+0,0041 ; +0,0123] |
| XGBoost | 0,6060 | 0,6083 | +0,0022 | [−0,0022 ; +0,0059] |

Control, LightGBM: log loss 0,513 → 0,509 y costo 0,520 → 0,507 (≈ 15.300 USD menos por cada 1.000 solicitudes).
Con `bootstrap_cost_difference` (la misma prueba que usa el ejemplo del curso):
- LightGBM optimizado frente al de partida: −0,013 por solicitud, IC 95 % [−0,023; −0,003]. También es más barato con
  confianza del 95 %.
- XGBoost: −0,005, IC [−0,015; +0,004]. No se distingue.

Carga del analista: con LightGBM optimizado, el % de solicitudes marcadas para revisión pasa de 61,4 % a 63,0 %.

**Reglas de decisión escritas antes de mirar:**
- **Parámetros:** se adoptan los optimizados solo si todo el intervalo de la mejora de AUC-PR queda por encima de 0.
- **Modelo final:** el finalista con mayor AUC-PR si el intervalo de la diferencia no cruza el 0; si lo cruza, LightGBM.

**Resultado de las reglas:**
- **LightGBM:** se adoptan los optimizados, porque el intervalo queda entero sobre 0.
- **XGBoost:** quedan los de partida, porque el intervalo cruza el 0.
- **Modelo final:** XGBoost de partida − LightGBM optimizado = −0,0020, IC [−0,0065; +0,0024]. Hay empate, así que la
  regla elige **LightGBM optimizado**.

## Decisión

- **Modelo que pasa a la etapa 7:** LightGBM con los parámetros optimizados, con las variables de `FINAL_FEATURES`.
- **Por qué:** es el único finalista cuya optimización mejoró con evidencia. Además, empata con XGBoost y es más rápido.
- **Lo que no pudimos concluir:**
  - Cuánto rinde en préstamos nuevos: eso solo lo dice la prueba.
  - Si un rango más amplio daría algo más. Los mejores parámetros quedaron en el borde (`n_estimators` 598 de 600 y
    `learning_rate` 0,011 con mínimo 0,01), pero no se amplió el rango después de ver el resultado.

## Para la etapa siguiente

- **Validación final (etapa 7):**
  - abrir la prueba **una sola vez** con LightGBM optimizado;
  - reportar AUC-PR con su intervalo, con y sin índice climático (la pregunta del caso), y desde julio de 2009 aparte;
  - decidir el umbral (por costo o por capacidad del analista) con validación, no con la prueba.
- **Pendiente del grupo:** configurar `.env` con Databricks para que el tracking quede en el workspace del curso.
