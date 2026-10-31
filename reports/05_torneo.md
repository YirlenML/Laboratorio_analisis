# Informe del torneo de modelos

> Resultado de `notebooks/05_torneo.ipynb` (re-ejecutado el 31 oct con el conjunto de variables revisado y las funciones alineadas con el ejemplo del curso). El torneo
> **descarta**: elige 1–2 finalistas con evidencia, no un campeón. Tablas: `reports/05_torneo_tabla.csv`,
> `05_torneo_tecnicas.csv` y `05_torneo_pliegues.csv`. Código: `candidates()` y `evaluate_folds()` en
> `src/proyecto/models/train.py`.

## Reglas del torneo

- **Mismos datos y mismos pliegues:**
  - 39.641 préstamos de entrenamiento;
  - 5 pliegues con `StratifiedGroupKFold` por `MemberKey` (semilla 42), los mismos del notebook 04;
  - la prueba sigue cerrada.
- **Línea base:** predice la proporción de impagos (0,31) para todos. Con la regla de costo equivale a "rechazar a
  todos": AUC-PR 0,310 y costo 0,690.
- **Métrica principal:** AUC-PR de impago.
- **Métrica de negocio:** costo esperado por solicitud con la matriz 4 a 1 (marcar impago si P > 0,2).
- **Métricas técnicas:** ROC-AUC, log loss, Brier, recall, precisión y F1 de impago, % de solicitudes marcadas
  (calculado exacto desde las decisiones) y costo con umbral 0,5 (para medir el aporte de la regla de costo).
- **Variables:** `FINAL_FEATURES` revisado de la etapa 4 (34 numéricas y 6 categóricas, sin índice climático).

## Tabla comparativa

| Modelo | AUC-PR (± ruido) | Costo 4 a 1 (± ruido) | Costo con umbral 0,5 | Segundos por ajuste |
|---|---|---|---|---|
| LightGBM | **0,6107** ± 0,0100 | 0,517 ± 0,009 | 0,819 | 2,0 |
| XGBoost | 0,6104 ± 0,0139 | **0,516** ± 0,013 | 0,823 | 4,0 |
| Random forest | 0,6045 ± 0,0125 | 0,528 ± 0,007 | 0,870 | 11,7 |
| Regresión logística | 0,5850 ± 0,0078 | 0,537 ± 0,012 | 0,869 | 1,8 |
| Línea base | 0,3104 ± 0,0001 | 0,690 ± 0,000 | 1,242 | 0,8 |

**La regla de decisión vale tanto como el modelo.** Con la clase más probable (umbral 0,5), todos los modelos cuestan
más que rechazar a todos (0,69), porque dejan pasar demasiados impagos. Con la regla de menor costo (P > 0,2), LightGBM
baja de 0,82 a 0,52: ≈ 350.000 USD por cada 1.000 solicitudes.

## Métricas técnicas

Es un problema binario: la "clase de interés" es el impago y el "AUC macro" es el ROC-AUC.

| Modelo | ROC-AUC | Log loss | Brier | Recall impago | Precisión impago | F1 impago | % marcado para revisión |
|---|---|---|---|---|---|---|---|
| LightGBM | 0,775 | 0,510 | 0,170 | 0,870 | 0,432 | 0,577 | 62,5 % |
| XGBoost | 0,775 | 0,510 | 0,170 | 0,872 | 0,432 | 0,577 | 62,7 % |
| Random forest | 0,769 | 0,516 | 0,172 | 0,904 | 0,407 | 0,561 | 69,0 % |
| Regresión logística | 0,758 | 0,524 | 0,176 | 0,878 | 0,414 | 0,563 | 65,8 % |
| Línea base | 0,500 | 0,619 | 0,214 | 1,000 | 0,310 | 0,474 | 100 % |

## ¿Coinciden los rankings de negocio y técnico?

| Modelo | AUC-PR | Costo | ROC-AUC | Log loss | F1 impago |
|---|---|---|---|---|---|
| LightGBM | 1 | 2 | 1 | 1 | 2 |
| XGBoost | 2 | 1 | 2 | 2 | 1 |
| Random forest | 3 | 3 | 3 | 3 | 4 |
| Regresión logística | 4 | 4 | 4 | 4 | 3 |

- **¿El mejor por la métrica de negocio también es el mejor por AUC?** No exactamente. LightGBM es primero en AUC-PR,
  ROC-AUC y log loss, y XGBoost en costo y F1. Pero las diferencias entre los dos están muy por debajo del ruido.
- **¿Hay modelos con AUC casi igual y costo distinto?** Sí, LightGBM y XGBoost, aunque la diferencia de costo (0,001)
  es menor que su ruido (0,009–0,013).
- **¿Alguna clase con recall casi nulo?** No. El recall de impago va de 0,87 a 0,90. El costo está en el otro lado:
  se marca para revisión el 63–69 % de las solicitudes.

## Comparación pareada de los mejores

| Mejor | Contra | Diferencia AUC-PR | Pliegues que gana | De a pares | Ahorro de costo | Pliegues que gana (costo) | De a pares (costo) |
|---|---|---|---|---|---|---|---|
| LightGBM | XGBoost | +0,0002 | 2 de 5 | 0,06 | −0,001 | 3 de 5 | −0,13 |
| LightGBM | Random forest | +0,0062 | 5 de 5 | 1,95 | 0,011 | 5 de 5 | 5,65 |
| XGBoost | Random forest | +0,0060 | 5 de 5 | 2,51 | 0,012 | 5 de 5 | 1,46 |

## ¿Cuánto vale la diferencia?

- **Unidad:** 1 unidad de costo = rechazar a un buen cliente ≈ 1.154,30 USD de intereses y cargos
  (`notebooks/01_caso_negocio.ipynb`). Es una aproximación.
- **Volumen:** por cada 1.000 solicitudes revisadas (el repo no tiene una cifra del volumen mensual; no se inventa).
- **Ahorro frente a la línea base:** XGBoost ≈ 200.700 USD, LightGBM ≈ 199.600 USD, random forest ≈ 186.900 USD y
  regresión logística ≈ 176.600 USD.
- **Diferencia entre el mejor y el siguiente:** ≈ 1.200 USD por cada 1.000 solicitudes, dentro del ruido.

## Finalistas

| Finalista | Por qué | Qué podría cambiar con la optimización |
|---|---|---|
| LightGBM | Primero en AUC-PR (empatado) y el más rápido de los dos (2 s) | Regularización (`min_child_samples`, `reg_lambda`) y tamaño de los árboles |
| XGBoost | Primero en costo (empatado) | Profundidad y `min_child_weight` |

**Modelos descartados y por qué:**

- **Random forest:** pierde con los dos boosting en los 5 pliegues y tarda 4 veces más que LightGBM.
- **Regresión logística:** queda 0,026 de AUC-PR por debajo (≈ 24.100 USD más por cada 1.000 solicitudes). Se
  conserva como referencia interpretable.

**Por qué el torneo no elige un campeón:** los dos primeros difieren menos que el ruido entre pliegues. La
optimización puede cambiar el orden, y solo la prueba final dice qué tan bueno es el modelo elegido.

## Efectos que la métrica principal no ve

- **Carga del analista.** Con la matriz 4 a 1, los dos mejores modelos envían a revisión el **63 %** de las
  solicitudes. Detectan el 87 % de los impagos, pero solo el 43 % de las marcadas cae en impago. Si el equipo no
  puede revisar ese volumen, hace falta un umbral por capacidad. Se decide en la etapa 7.
- **Dependencia del puntaje de Prosper.** Todos los modelos usan el puntaje de la propia plataforma (decisión de la
  etapa 4).
