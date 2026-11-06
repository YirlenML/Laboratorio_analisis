# Registro del modelo

Cifras de `notebooks/08_registro_modelo.ipynb` y `reports/08_registro.json`.

## 1. Dónde quedó registrado

| Dato | Valor |
|---|---|
| Plataforma | ☐ Databricks  ☒ MLflow local (respaldo) → motivo: el equipo donde se ejecutó no tiene `.env` ni perfil de Databricks |
| Experimento | `eco-score-registro` |
| Nombre del modelo registrado | `eco_score_default` |
| Versión | 1 |
| Alias | `champion` |
| Quién lo registró y cuándo | Juan Camilo Ramirez, 2026-11-05 20:25:38 |

## 2. Qué se registró junto al modelo

- Parámetros: `modelo` = lightgbm, `calibrado` = False, `umbral_de_costo` = 0,2 y los 7 hiperparámetros optimizados.
- Métricas de la prueba: las 10 de la etapa 7, entre ellas AUC-PR 0,6209, IC 95 % [0,6044; 0,6407], y costo 0,5208. También la
  línea base (0,3104) y el tramo desde julio de 2009 (0,4789, IC [0,4480; 0,5102]). Son 16 métricas en total.
- Firma y ejemplo de entrada (¿qué columnas espera?): 43 columnas crudas de entrada y 2 probabilidades de salida. La lista está
  en `reports/08_registro.json`. El ejemplo tiene 5 filas. No incluye identificadores de prestatario ni `BorrowerState`.
- Etiquetas: `etapa`, `decisiones_congeladas`, `unidad_de_particion`, `prueba_filas` y `supera_linea_base`.

**Ojo para la app:** 4 de las 43 columnas (`LoanOriginationDate`, `FirstRecordedCreditLine`, `TotalProsperPaymentsBilled` y
`ProsperPaymentsOneMonthPlusLate`) las lee `add_features`, pero el modelo no usa lo que calcula con ellas. Deben existir en la
entrada; el notebook 09 debe decidir cómo llenarlas.

## 3. Comprobación de ida y vuelta

- ¿El modelo recuperado del registro predice igual que el local? ☒ sí  ☐ no
- Cómo se comprobó (qué filas, qué función): `predict_proba` en 500 filas del entrenamiento, con el modelo cargado desde
  `models:/eco_score_default@champion`. Diferencia máxima: 0,00.
- Antes de registrar, se comprobó que el modelo da las mismas probabilidades guardadas al abrir la prueba en sus 9.911
  préstamos. No se calculó ninguna métrica nueva con la prueba.

## 4. Tracking frente a registro (en tus palabras)

- ¿Qué guarda el **tracking** en tu proyecto y para qué lo usaron?: guarda ejecuciones. En la etapa 6 son 50 ensayos de
  Optuna con sus parámetros y métricas, más sus 2 ejecuciones madre. Sirvió para comparar configuraciones y reproducir la
  búsqueda.
- ¿Qué guarda el **registro** y por qué el alias `champion` ayuda?: guarda versiones del modelo final con firma, ejemplo y
  métricas. El alias dice cuál está vigente: quien lo use pide `champion` y, si hay una versión mejor, se mueve el alias sin
  cambiar código.

## 5. Reproducibilidad

- ¿Alguien de otro grupo podría recuperar tu modelo con lo que dejaste escrito? ☐ sí  ☒ no → qué falta: el registro local
  vive en `mlflow_local.db` y `notebooks/mlruns/`, que no se suben al repositorio. Para recuperarlo, hay que registrarlo en
  Databricks o ejecutar los notebooks 07 y 08 con las versiones de `requirements.txt`. Una vez exportado en el notebook 09,
  `models/model.joblib` sí viaja con el repositorio.
