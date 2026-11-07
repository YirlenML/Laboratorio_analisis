# Ficha del modelo — Eco-Score

## Qué es

Estima la probabilidad de **impago** de un préstamo personal de Prosper a partir del perfil financiero del prestatario y de las
condiciones del préstamo. Apoya al analista de riesgo a **priorizar la revisión**: no decide por sí solo y la decisión final es
siempre humana.

- **Modelo:** lightgbm con parámetros optimizados, sin calibrar.
- **Registro:** `eco_score_default` versión 1, alias `champion` (MLflow local). El archivo para la app es `models/model.joblib`.
- **Regla de decisión:** menor costo esperado con la matriz 4 a 1: marcar para revisión si P(impago) > 0,2.

## Datos de entrenamiento

- **Fuente y licencia:** *Prosper Loan Data* (Kaggle, Henry Okam), CC0: Public Domain.
- **Tamaño:** 39.641 préstamos de 32.341 prestatarios (nov. 2005 a mar. 2014), solo préstamos terminados.
- **Partición:** por prestatario. La prueba (9.911 préstamos de 8.111 prestatarios) se abrió **una sola vez**, con las decisiones congeladas antes (2026-11-05T20:09:49).
- **Datos personales:** no hay nombres ni documentos. Las llaves del préstamo y `Occupation` se eliminaron; `MemberKey` se cambió por un número anónimo que no entra al modelo.

## Rendimiento (prueba, prestatarios nunca vistos)

| Métrica | Modelo | Línea base | Intervalo del 95 % (modelo) |
|---|---|---|---|
| AUC-PR de impago (principal) | 0,6209 | 0,3104 | 0,6044 a 0,6407 |
| Costo por solicitud, matriz 4 a 1 (menor es mejor) | 0,5208 | 0,6896 | 0,5043 a 0,5376 |
| AUC-PR desde julio de 2009 | 0,4789 | no calculada | 0,4480 a 0,5102 |

- **Frente a la línea base:** AUC-PR +0,3105 (IC 95 %: +0,2959 a +0,3270) y costo -0,1688 (IC 95 %: -0,1887 a -0,1485), unos 194.849 USD por cada 1.000 solicitudes. La conversión a dólares es una aproximación.
- **Carga de trabajo:** marca para revisión el 63,7 % de las solicitudes y detecta el 87,5 % de los impagos. De cada 100 marcadas, 43 caen en impago, y 384 impagos pasan sin revisión.

## Variables que más pesan

`BorrowerAPR` (0,2931), `EstimatedEffectiveYield` (0,1765), `MonthlyLoanPayment` (0,1513), `StatedMonthlyIncome` (0,1428), `CreditScoreRangeLower` (0,0918) (|SHAP| medio). `BorrowerAPR` y `EstimatedEffectiveYield` las calcula Prosper: el modelo depende en buena parte del riesgo
que la plataforma ya había puesto en el precio. SHAP explica al modelo, no al mundo: una importancia alta no es una causa.

## Límites y usos no recomendados

- **Datos de una época:** préstamos de Prosper de 2005 a 2014, solo terminados. Los recientes que ya terminaron son sobre todo los que terminaron rápido.
- **Espera el rendimiento de 0,4789, no el de 0,6209**, en solicitudes parecidas a las actuales: la cifra global se apoya en préstamos antiguos con más impagos.
- **Supuesto de negocio:** el modelo usa el puntaje y el precio de Prosper, disponibles al crear la solicitud. Si aún no existen, los campos quedan en "no sé" y el modelo imputa.
- **Índice climático:** no entra al modelo. Con él, el AUC-PR de la prueba sube 0,0023 (IC 95 %: 0,0003 a 0,0045) y el costo no se distingue del ruido. Es un supuesto académico del grupo, sin fuente verificable, y no muestra que el clima cause impagos.
- **Atributos sensibles o de uso regulado:** ingreso declarado, rango de ingreso, situación laboral y vivienda propia. Deben revisarse con el área legal, junto con un análisis de trato desigual, antes de cualquier uso real. `BorrowerState` no entra al modelo.
- **No debe usarse para:** rechazar solicitudes de forma automática, penalizar a alguien por su estado de residencia ni tomar decisiones reales sin validarlo con datos posteriores a 2014.
- **No se evaluó:** estabilidad en el tiempo, deriva y préstamos que aún no habían terminado.

## Reproducibilidad

Código en `src/`, pruebas en `tests/`, notebooks en `notebooks/`. Esta ficha se genera con `notebooks/09_inferencia.ipynb`.
