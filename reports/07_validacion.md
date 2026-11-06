# Validación e interpretación

Cifras de `notebooks/07_validacion_interpretacion.ipynb`, `reports/07_metricas_test.json` y
`reports/07_decisiones_congeladas.json`.

## 1. Decisiones congeladas (escritas ANTES de abrir la prueba)

| Decisión | Valor | Cómo se decidió (con qué datos) |
|---|---|---|
| Modelo final | LightGBM | Regla de la etapa 6: empate con XGBoost y se elige el más rápido (reserva de 9.910 préstamos) |
| Parámetros (optimizados o de partida) | Optimizados | Mejora de AUC-PR +0,0082, IC 95 % [+0,0041; +0,0123] en la reserva |
| ¿Calibrar las probabilidades? | No | Reserva: el log loss baja menos de 0,005 (0,5088 a 0,5087) |
| Métrica principal | AUC-PR de impago | Aprobada el 30 oct; controles: costo, ROC-AUC, Brier, recall y F1 de impago |
| Regla de decisión (clase más probable, umbral, menor costo…) | Menor costo esperado: marcar impago si P(impago) > 0,2 | Matriz de costos 4 a 1 del caso |
| **Fecha y hora en que se congelaron** | **2026-11-05 20:09:49** | `reports/07_decisiones_congeladas.json` |

**Umbral por capacidad:** no se adoptó, porque el proyecto no tiene una cifra de capacidad del analista. En la reserva:

| Umbral | % marcado | Recall de impago | Precisión | Costo |
|---|---|---|---|---|
| 0,2 (elegido) | 63,0 % | 0,879 | 0,433 | 0,507 |
| 0,3 | 45,3 % | 0,732 | 0,502 | 0,558 |
| 0,4 | 30,0 % | 0,561 | 0,580 | 0,671 |
| 0,5 | 18,3 % | 0,384 | 0,652 | 0,828 |

**Partición:** las decisiones usan la reserva local de 9.910 préstamos, la misma de la búsqueda. `reports/06_optimizacion_tabla.csv`
trae hoy las cifras de una ejecución en Databricks con 9.875 préstamos, calculados a partir de sus costos, por lo que no
se usó. El notebook 07 se detiene si la reserva no tiene 9.910 préstamos.

## 2. Calibración (con entidades reservadas, no con la prueba)

- ¿Se evaluó? ☒ sí  ☐ no
- Resultado y decisión: método sigmoide con 3 pliegues por prestatario. Log loss 0,5088 a 0,5087, Brier 0,1698 a 0,1697 y
  costo 0,5073 a 0,5082 (diferencia +0,0009, IC [−0,0056; +0,0072]). La regla pedía bajar el log loss más de 0,005, así
  que **no se calibra**.

## 3. La prueba, abierta **una sola vez**

- Fecha y hora en que se abrió (la marca está en `reports/prueba_abierta.txt`): **2026-11-05 20:11:30**, con 9.911 préstamos
  de 8.111 prestatarios.
- ¿Se cambió algo del modelo después de verla? ☒ no  ☐ sí
- Antes de abrirla, el código se ensayó con la reserva en lugar de la prueba, en una carpeta temporal.

| Métrica | Modelo final | Línea base | Intervalo del 95 % (entidades) |
|---|---|---|---|
| AUC-PR (principal) | 0,6209 | 0,3104 | [0,6044; 0,6407] |
| Costo por solicitud (control) | 0,5208 | 0,6896 | [0,5043; 0,5376] |
| Brier (control) | 0,1686 | 0,2140 | [0,1644; 0,1725] |
| ROC-AUC (control) | 0,7780 | 0,5000 | No calculado |
| Recall de impago (control) | 0,8752 | 1,0000 | No calculado |
| F1 de impago (control) | 0,5731 | 0,4737 | No calculado |

**¿Mejora al baseline con confianza?** Sí. AUC-PR: +0,3105, IC [+0,2959; +0,3270]. Costo: −0,1688, IC [−0,1887; −0,1485],
unos 194.800 USD por cada 1.000 solicitudes. Los dos intervalos excluyen el cero.

**¿Cae cerca de validación?** Sí. En la reserva, AUC-PR 0,6080 y costo 0,507; en la prueba, 0,6209 y 0,521.

### Preguntas pendientes del caso

- **Desde julio de 2009:** AUC-PR **0,4789**, IC [0,4480; 0,5102], con 5.329 préstamos y 24,2 % de impago. Antes de esa fecha,
  0,6963 con 39,0 % de impago. La cifra global exagera lo que se puede esperar en una solicitud nueva.
- **Índice climático:** con el índice, AUC-PR +0,0023, IC [+0,0003; +0,0045], y costo −0,0046, IC [−0,0106; +0,0010]. La mejora
  en AUC-PR excluye el cero por poco y es mínima; el costo no se distingue del ruido. Contradice la medición de la etapa 4
  (+0,0012, dentro del ruido). **No cambia el modelo**, como se escribió antes de abrir la prueba, y no prueba que el clima
  cause impagos.

## 4. Errores y carga de trabajo

| Segmento | Casos | AUC-PR | % que el modelo marca | % real |
|---|---|---|---|---|
| Antes de jul. 2009 | 4.582 | 0,696 | 77,1 % | 39,0 % |
| Desde jul. 2009 | 5.329 | 0,479 | 52,2 % | 24,2 % |
| Plazo 12 meses | 325 | 0,347 | 3,1 % | 6,2 % |
| Plazo 36 meses | 8.840 | 0,626 | 65,0 % | 31,7 % |
| Plazo 60 meses | 746 | 0,584 | 75,7 % | 33,5 % |
| Ingreso `$100,000+` | 1.130 | 0,542 | 42,0 % | 21,7 % |
| Ingreso `$1-24,999` | 882 | 0,616 | 77,2 % | 35,4 % |
| Ingreso `Not displayed` | 773 | 0,855 | 86,5 % | 55,1 % |
| Vivienda propia: no | 5.108 | 0,638 | 66,6 % | 32,4 % |
| Vivienda propia: sí | 4.803 | 0,599 | 60,7 % | 29,6 % |

La tabla completa, con los estados, está en `reports/07_errores_por_segmento.csv`.

- ¿Hay un segmento al que le va peor? ¿Por qué podría ser?:
  - **Desde julio de 2009** es el más importante: AUC-PR 0,479 y recall 0,789. Hay menos impagos y el puntaje antiguo ya no
    existe.
  - **Plazo de 12 meses:** recall 0,20, pero con solo 325 préstamos y 6,2 % de impago la cifra es ruidosa.
  - **`Not displayed`** rinde muy bien (AUC-PR 0,855) y puede estar marcando la época. Falta comprobarlo, sin usar la prueba.
  - Los grupos `$0` (122) y `Not employed` (94) son demasiado pequeños para concluir.
- Si el modelo prioriza revisión humana: carga que genera frente a la carga real: marca el **63,7 %** de las solicitudes frente
  a **31,0 %** de impagos reales. De cada 100 marcadas, 43 caen en impago. Pasan sin revisión 384 de 3.076 impagos.

## 5. Interpretación

- Variables que más pesan (y qué significa para el negocio): `BorrowerAPR` (0,293), `EstimatedEffectiveYield` (0,177),
  `MonthlyLoanPayment` (0,151), `StatedMonthlyIncome` (0,143) y `CreditScoreRangeLower` (0,092). Las dos primeras las calcula
  Prosper, así que el modelo depende en buena parte del riesgo que la plataforma ya había puesto en el precio.
- **Límite de la explicación:** SHAP explica al modelo, no al mundo. No dice si el modelo acertó, una importancia alta no es
  causa, y las variables correlacionadas se reparten el crédito.
- Atributos sensibles o de uso regulado entre las variables (¿cuáles, y qué se hace?): el modelo usa ingreso declarado
  (0,143), vivienda propia (0,045), rango de ingreso (0,036) y situación laboral con su duración (0,032). Antes de producción
  debe revisarlos el área legal, junto con un análisis de trato desigual. `BorrowerState`, `MemberKey` y `borrower_id` no
  entran al modelo.

## 6. Conclusión

- ¿El modelo sirve para la decisión del caso? ¿Con qué condiciones?: sirve para **priorizar la revisión** en un contexto
  académico. Supera con claridad a la línea base, siempre que el analista conserve la decisión final y pueda revisar cerca de
  dos de cada tres solicitudes. Para solicitudes recientes hay que esperar el rendimiento de 0,479, no el de 0,6209.
- Qué NO debe hacerse con él:
  - rechazar solicitudes de forma automática;
  - usar el 0,6209 como rendimiento esperado en solicitudes actuales;
  - presentar el índice climático como causa del impago o penalizar a alguien por su estado;
  - usarlo en producción sin revisión legal y sin evaluar datos posteriores a 2014.
- Lo que no se evaluó: estabilidad en el tiempo, deriva, y préstamos que aún no habían terminado.
