# Research: App de Eco-Score

No quedaron puntos "NEEDS CLARIFICATION". Estas son las decisiones de diseño y lo comprobado.

## 1. Cómo demostrar un dato inválido

- **Decision:** los campos numéricos no llevan mínimo ni máximo en pantalla. La persona puede escribir -500, y `validate_inputs` lo rechaza con un mensaje.
- **Rationale:** con mínimo y máximo, Streamlit limita el valor y el error del rango no se puede demostrar. La rúbrica A3 pide un error claro.
- **Alternatives considered:** mantener los límites: se descarta porque el evaluador no vería el mensaje.

## 2. Cómo representar "No sé"

- **Decision:** cada campo numérico empieza vacío, con el texto "No sé"; vacío significa dato faltante. Las listas tienen "(no sé)" como primera opción.
- **Rationale:** quita 33 casillas del formulario y evita sugerir valores en el formulario neutro. El pipeline ya imputa los vacíos.
- **Alternatives considered:** casillas por campo: duplican el formulario. Medianas como valor inicial: parecen datos reales de la solicitud.

## 3. Traducción del resultado

- **Decision:** `recommendation()` traduce la decisión ya calculada por `predict_with_scores`: `impago` → **enviar a revisión**; `pagó` → **sin revisión prioritaria**. No vuelve a comparar con 0,2.
- **Rationale:** una sola fuente para la regla. El empate en 0,2 queda en "sin revisión", igual que la regla congelada.
- **Alternatives considered:** recalcular el umbral en la app: dos reglas podrían separarse.

Se deja de usar `needs_review` en la pantalla: con esa señal, casi toda solicitud marcada para revisión saldría como "el modelo duda", porque el umbral es 0,2 y la clase más probable se decide en 0,5.

## 4. Cifras de rendimiento

- **Decision:** el notebook 09 agrega al esquema una clave `performance`, copiada de `reports/07_metricas_test.json`. La app solo la lee.
- **Rationale:** en la nube la app funciona con sus propios archivos, y `reports/` no debe ser una dependencia para arrancar (SC-006). Las cifras no se escriben a mano.
- **Alternatives considered:** leer `reports/` desde la app: acopla la app a esa carpeta. Escribirlas en el código: viola el principio VII.

## 5. Nombres en las listas

- **Decision:** `ListingCategory` y los valores `FALSO`/`VERDADERO` se muestran con nombres en español; el modelo recibe el valor original.
- **Rationale:** el analista no conoce los códigos, y las categorías deben seguir siendo las del entrenamiento.
- **Alternatives considered:** cambiar los valores del modelo: rompería el one-hot y la identidad de las probabilidades.

## 6. Ejemplos y resultado anterior

- **Decision:** el selector de ejemplo va fuera del formulario y la clave de cada campo incluye el nombre del ejemplo, como en el ejemplo del curso. El resultado solo se dibuja en la ejecución del envío.
- **Rationale:** Streamlit conserva el valor anterior si la clave no cambia, y mostrar un resultado de otro préstamo sería engañoso.

## 7. Python 3.12

- **Decision:** se conserva `requirements.txt` y se verifica al final en un entorno 3.12 temporal.
- **Evidence:** el `model.joblib` guardado con Python 3.14 cargó en 3.12.16 con diferencia máxima 0,0. `uv pip compile` resolvió `requirements.txt` para Python 3.12 en Linux. El conflicto de `pip` se debía a evaluar `pywin32` con los marcadores de Windows.

## 8. Duplicado de `decide_min_cost`

- **Decision:** no se unifica en esta pieza.
- **Rationale:** `train.py` importa `xgboost`, que la app no necesita. El cambio no aporta al despliegue y toca código ya evaluado.
