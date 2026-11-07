---
marp: true
theme: default
paginate: true
header: "Presentación ejecutiva · Eco-Score"
footer: "Casos Avanzados · Maestría en Ingeniería Analítica"
---

# 1 · Cada impago que no vemos cuesta cuatro veces más que frenar a un buen cliente

- **¿Quién decide?** El analista de riesgo de una plataforma de préstamos entre personas.
- **¿Qué decide con el resultado?** Qué solicitudes revisar primero y en qué condiciones prestar (monto, plazo, tasa).
- **¿Cuánto cuesta equivocarse?** Un impago pierde en promedio USD 4.672 de capital; un buen cliente deja USD 1.154 en intereses. La proporción es de 4 a 1.

> De cada 100 préstamos terminados, 31 cayeron en impago.

<!-- 1 min. Rol negocio. Abrir con la decisión, no con el algoritmo. Fuente: reports/00_caso.md. -->

---

# 2 · Probamos si el clima ayudaba a anticipar el impago: casi no aporta, y lo dejamos fuera

- **Los datos:** 49.552 préstamos terminados de Prosper (2005–2014), con 15.380 impagos.
- **Cómo se validó con honestidad:** partimos por prestatario, para que nadie aparezca en dos grupos, y abrimos la prueba una sola vez, con las decisiones ya congeladas.
- **Qué se comparó y qué se eligió:** cuatro modelos contra una línea base. Elegimos LightGBM: empató con XGBoost y es más rápido.
- **Qué se descartó y por qué:** el índice climático. Sube el AUC-PR solo 0,0023 y su efecto en el costo no se distingue del ruido. Es un supuesto académico sin fuente verificable: esto no prueba que el clima no importe ni que cause impagos.

<!-- 1 min. Rol datos. Fuentes: reports/05_torneo.md y reports/07_validacion.md. -->

---

# 3 · Por cada 1.000 solicitudes, el modelo ahorra cerca de USD 195.000 frente a marcarlas todas

| | Sin el modelo (marcar todas) | Con el modelo |
|---|---|---|
| Solicitudes marcadas para revisión | 100 % | 63,7 % |
| Impagos detectados | 100 % | 87,5 % (384 de 3.076 pasan sin revisión) |
| De cada 100 marcadas, cuántas caen en impago | 31 | 43 |
| Costo de los errores por cada 1.000 solicitudes | ≈ USD 796.000 | ≈ USD 601.000 |

- **Mejora y su intervalo:** ahorro de ≈ USD 195.000 por cada 1.000 solicitudes, IC 95 %: USD 171.000 a 218.000. La conversión a dólares es aproximada y no incluye el costo de revisar.
- **La métrica técnica:** AUC-PR 0,6209 (IC 95 %: 0,6044 a 0,6407) frente a 0,3104 de la línea base, en 9.911 préstamos de prestatarios nunca vistos, con los 39 datos.

<!-- 2 min. Rol modelado. Se usa "por cada 1.000 solicitudes" porque el proyecto no tiene un volumen mensual real. -->

---

# 4 · En la app, cada solicitud recibe una recomendación clara y la decisión sigue siendo humana

**Enlace:** https://lvtfbkczdgz2aawa7etysv.streamlit.app

La app pide 12 datos esenciales; los otros 27 son opcionales.

1. **Un caso normal:** «Préstamo real que se pagó» → 6,6 % de probabilidad de impago → **Sin revisión prioritaria**.
2. **Un caso límite:** «Préstamo real que cayó en impago» → 45,7 % → **Enviar a revisión**. Con plazo de 12 meses en vez de 36 → 17,0 % → **Sin revisión prioritaria**.
3. **Un dato inválido:** puntaje de crédito −500 → «debe estar entre 300 y 900», sin recomendación.

> Plan B: captura de pantalla con fecha y la app en local (`streamlit run app/streamlit_app.py`).

<!-- 4 min. Rol app. Si sobra tiempo: dejar el ingreso vacío en el primer ejemplo → 7,7 % y aviso «Se evaluó sin 2 de 39 datos». -->

---

# 5 · Recomendación: usarlo para priorizar, nunca para decidir solo

- **Qué NO hace el modelo:** no rechaza solicitudes de forma automática, no explica causas y no usa el estado de residencia.
- **Límites de los datos:** préstamos de 2005 a 2014, solo terminados. Desde julio de 2009 detecta el 78,9 % de los impagos, no el 87,5 %, y su AUC-PR baja a 0,4789, con los 39 datos. Con solo los 12 datos esenciales rinde menos: en la reserva, el AUC-PR baja de 0,6080 a 0,5816.
- **Uso responsable:** usa ingreso, vivienda y situación laboral. Antes de un uso real necesita revisión legal y un análisis de trato desigual.
- **Siguientes pasos:** validarlo con datos posteriores a 2014, definir cuántas solicitudes puede revisar el equipo y vigilar la deriva en producción.

<!-- 1 min de riesgos (rol modelado) + 1 min de cierre (rol negocio). Decisión que cambiaríamos: [POR CONFIRMAR POR EL GRUPO]. -->
