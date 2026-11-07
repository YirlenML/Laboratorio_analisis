# Feature Specification: App de Eco-Score para priorizar la revisión

**Feature Branch**: `camilo/speckit` (el grupo trabaja en esta rama; la carpeta de la especificación es independiente de la rama)

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "App de Streamlit de Eco-Score lista para desplegar en Streamlit Community Cloud (hito H3; exposición el 7 nov). El analista de riesgo prioriza la revisión de solicitudes y conserva la decisión final. Partir de la app, el modelo y el esquema que ya existen."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evaluar una solicitud y saber qué hacer (Priority: P1)

Una analista de riesgo recibe una solicitud de préstamo, escribe sus datos y obtiene una recomendación clara: **enviar a revisión** o **sin revisión prioritaria**, junto con la probabilidad estimada de impago. Entiende el resultado sin saber de modelos y conserva la decisión final.

**Why this priority**: es la razón de ser de la app y lo mínimo que exige la rúbrica: devolver la predicción del modelo final con datos válidos.

**Independent Test**: se llena el formulario con los datos de un préstamo y se comprueba que aparece la recomendación, la probabilidad y la explicación de la regla.

**Acceptance Scenarios**:

1. **Given** una solicitud con datos válidos, **When** la analista pulsa evaluar, **Then** ve una de las dos recomendaciones y la probabilidad de impago en porcentaje.
2. **Given** una solicitud cuya probabilidad de impago es mayor que 20 %, **When** se evalúa, **Then** la recomendación es **enviar a revisión**.
3. **Given** una solicitud cuya probabilidad de impago es 20 % o menos, **When** se evalúa, **Then** la recomendación es **sin revisión prioritaria**.
4. **Given** cualquier resultado, **When** la analista lo lee, **Then** la pantalla deja claro que es un apoyo y que la decisión es de una persona; nunca dice que la solicitud fue rechazada ni que el prestatario pagará o no pagará.

---

### User Story 2 - Demostrar la app con casos preparados (Priority: P1)

Durante la exposición, un integrante del grupo elige un préstamo de ejemplo, ve el formulario lleno, lo evalúa y luego cambia un dato para mostrar cómo cambia la recomendación. También puede empezar con un formulario neutro, sin datos sugeridos.

**Why this priority**: la exposición dedica 4 minutos a una demo en vivo con caso normal, límite e inválido; llenar a mano 39 campos en vivo no es viable.

**Independent Test**: se elige cada ejemplo, se comprueba que el formulario toma sus valores y se evalúa sin escribir nada.

**Acceptance Scenarios**:

1. **Given** la app recién abierta, **When** se elige un préstamo de ejemplo, **Then** todos los campos toman los valores de ese préstamo.
2. **Given** un ejemplo cargado, **When** se cambia a otro ejemplo, **Then** todos los campos se actualizan y no queda ningún valor del anterior.
3. **Given** un ejemplo cargado, **When** se vuelve a la opción en blanco, **Then** el formulario regresa a su estado neutro.
4. **Given** un ejemplo, **When** se cambia un dato hasta cruzar el umbral del 20 %, **Then** la recomendación cambia.

---

### User Story 3 - Recibir un error claro con datos inválidos (Priority: P1)

Si alguien escribe un dato imposible, por ejemplo un puntaje de crédito de -500, la app no responde con un número: dice qué campo corregir y cuál es el rango permitido.

**Why this priority**: la rúbrica (criterio A3, nivel 3) exige un error claro con datos inválidos, y el evaluador lo probará en vivo.

**Independent Test**: se escribe un valor fuera del rango posible y se comprueba que no aparece ninguna recomendación y sí un mensaje con el campo y el rango.

**Acceptance Scenarios**:

1. **Given** un formulario con un valor fuera del rango posible, **When** se pulsa evaluar, **Then** no aparece recomendación y el mensaje nombra el campo, en español, y su rango permitido.
2. **Given** varios valores imposibles a la vez, **When** se pulsa evaluar, **Then** el mensaje los nombra todos.
3. **Given** un valor poco común pero posible, **When** se evalúa, **Then** aparece la recomendación con una advertencia.
4. **Given** el error, **When** se corrige el dato y se evalúa de nuevo, **Then** aparece la recomendación.

---

### User Story 4 - Evaluar sin conocer todos los datos (Priority: P2)

La analista no siempre tiene todos los datos. Puede dejar en "No sé" lo que no conoce y aun así recibe una recomendación, sabiendo que se hizo con información incompleta.

**Why this priority**: es un caso real de uso y una pregunta anunciada del instructor, pero la app ya entrega valor sin esto.

**Independent Test**: se marca "No sé" en uno o varios campos y se comprueba que hay resultado y aviso.

**Acceptance Scenarios**:

1. **Given** uno o más campos marcados "No sé", **When** se evalúa, **Then** aparece la recomendación y un aviso de cuántos datos faltaron.
2. **Given** todos los campos en "No sé", **When** se evalúa, **Then** la app responde sin fallar y advierte que el resultado se apoya casi por completo en valores típicos.

---

### User Story 5 - Conocer los límites antes de confiar (Priority: P2)

Quien usa la app ve, sin buscarlo, para qué sirve, para qué no y qué rendimiento esperar, incluida la diferencia entre el resultado global y el de solicitudes parecidas a las actuales.

**Why this priority**: es un requisito del proyecto (aviso de uso responsable) y evita una lectura engañosa de la métrica.

**Independent Test**: se abre la app y se comprueba que el aviso y las cifras están visibles sin evaluar nada y coinciden con los reportes.

**Acceptance Scenarios**:

1. **Given** la app abierta, **When** se mira la pantalla, **Then** el aviso de uso responsable está visible sin abrir nada.
2. **Given** la sección de rendimiento, **When** se compara con los reportes, **Then** todas las cifras coinciden.
3. **Given** la sección de rendimiento, **When** se lee, **Then** dice que en solicitudes parecidas a las actuales se espera 0,4789 y no 0,6209.

---

### User Story 6 - Llenar un formulario largo sin perderse (Priority: P3)

El formulario tiene 39 datos. Están agrupados por tema, con nombres comprensibles, y el propósito del préstamo se elige por su nombre, no por un código.

**Why this priority**: mejora la experiencia y la demo, pero no cambia el resultado.

**Independent Test**: se recorre el formulario y se comprueba que cada campo pertenece a un grupo y que el propósito se muestra con nombre.

**Acceptance Scenarios**:

1. **Given** el formulario, **When** se recorre, **Then** los 39 campos aparecen en grupos temáticos, una sola vez cada uno.
2. **Given** la lista de propósitos, **When** se elige uno por su nombre, **Then** el modelo recibe el mismo valor que recibiría con el código original.

### Edge Cases

- Falta el modelo o el esquema: la app explica qué falta y no muestra un error técnico.
- Llega texto en un dato numérico: se trata como dato inválido, con mensaje claro (el campo de la pantalla no deja escribir letras; la validación lo cubre para cualquier otra entrada).
- Se cambia de ejemplo después de evaluar: el resultado anterior deja de mostrarse hasta volver a evaluar.
- Un valor exactamente en el límite del rango posible se acepta.
- Una probabilidad exactamente igual a 20 % queda como **sin revisión prioritaria**, porque la regla es "mayor que 0,2".
- En una categoría sin dato, la opción neutra equivale a "No sé" y no a una categoría real.
- El ingreso `$0` o la calificación `A` nunca aparecen elegidos por defecto.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La app MUST recibir los 39 datos del formulario y devolver la probabilidad de impago del modelo final, sin alterarla.
- **FR-002**: La app MUST traducir la decisión a **enviar a revisión** o **sin revisión prioritaria** con la regla ya congelada: revisar si P(impago) > 0,2.
- **FR-003**: La app MUST mostrar que el resultado es un apoyo a la persona que decide, y MUST NOT presentarlo como rechazo automático.
- **FR-004**: Users MUST be able to elegir un préstamo de ejemplo o empezar con un formulario neutro.
- **FR-005**: Al cambiar de ejemplo, todos los campos MUST reflejar el nuevo ejemplo y MUST NOT mostrarse un resultado anterior.
- **FR-006**: En el formulario neutro, ninguna categoría MUST sugerir un dato: todas empiezan en la opción "No sé".
- **FR-007**: Users MUST be able to escribir un valor fuera del rango posible, para que sea la validación la que lo rechace y no un campo que impida escribirlo.
- **FR-008**: Ante un valor fuera del rango posible o no numérico, la app MUST negarse a dar una recomendación y MUST decir, en español, qué campo y qué rango corregir.
- **FR-009**: Ante un valor posible pero fuera de lo visto en el entrenamiento, la app MUST responder y advertirlo.
- **FR-010**: Users MUST be able to dejar en "No sé" cualquier campo; la app MUST responder e indicar cuántos datos faltaron.
- **FR-011**: La app MUST mostrar el aviso de uso responsable a la vista, sin necesidad de abrir nada.
- **FR-012**: La app MUST mostrar el rendimiento esperado, y MUST indicar que en solicitudes parecidas a las actuales se espera 0,4789 y no 0,6209.
- **FR-013**: Toda cifra de rendimiento MUST salir de los resultados ya registrados del proyecto; MUST NOT escribirse a mano ni calcularse de nuevo con la prueba.
- **FR-014**: Los 39 campos MUST estar agrupados por tema, con etiquetas en español, y el propósito del préstamo MUST elegirse por su nombre según el diccionario de datos.
- **FR-015**: La app MUST funcionar solo con los archivos del repositorio: no consulta Databricks ni MLflow y no usa credenciales.
- **FR-016**: Si falta un archivo necesario, la app MUST explicar cuál es, sin mostrar un error técnico.
- **FR-017**: El modelo, sus parámetros y la regla de decisión MUST NOT cambiar; las probabilidades de la prueba deben seguir idénticas a las guardadas en la etapa 7.
- **FR-018**: La lógica reutilizable MUST quedar fuera de la pantalla, con pruebas automáticas, según los principios IV y VI de la constitución.
- **FR-019** (6 nov): La app MUST pedir a la vista solo 12 datos esenciales y dejar los otros 27 plegados como opcionales; la persona MUST poder evaluar sin abrirlos.
- **FR-020** (6 nov): La app MUST decir, con la cifra medida en préstamos reservados, qué se pierde al llenar solo los datos esenciales.
- **FR-021** (6 nov): La app MUST usar una identidad visual en tonos agua marina, con iconos, y el estado del resultado MUST mostrarse con icono y texto, no solo con color.

### Key Entities *(include if feature involves data)*

- **Solicitud**: los 39 datos de un préstamo que se evalúa; cada uno puede venir vacío ("No sé").
- **Resultado**: probabilidad de impago, recomendación, datos faltantes y advertencias.
- **Préstamo de ejemplo**: un préstamo real del entrenamiento, sin identificadores, que llena el formulario para una demostración.
- **Esquema de entrada**: define campos, etiquetas, categorías y rangos posibles y observados.
- **Resultados registrados**: cifras de rendimiento ya medidas en la etapa 7.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una persona que no conoce la app obtiene una recomendación desde un ejemplo en menos de 30 segundos.
- **SC-002**: El caso normal, el límite, el inválido y el de "No sé" se demuestran en vivo en menos de 4 minutos en total.
- **SC-003**: En el 100 % de los valores imposibles probados no aparece recomendación y el mensaje nombra el campo y el rango.
- **SC-004**: El 100 % de las cifras de rendimiento visibles coincide con los reportes del proyecto.
- **SC-005**: Las probabilidades de los 9.911 préstamos de la prueba son idénticas a las guardadas (diferencia máxima 0,0) después del cambio.
- **SC-006**: La app abre y evalúa en una copia que solo contiene sus archivos, sin credenciales ni acceso a otros servicios.
- **SC-007**: Una persona sin formación técnica explica con sus palabras qué significa el resultado después de leerlo una vez.

## Assumptions

- La usuaria es una analista de riesgo y quien expone es el grupo; el enfoque es académico.
- Se conservan el modelo LightGBM registrado, los rangos posibles propuestos el 6 nov (aún por confirmar por el grupo) y los dos préstamos de ejemplo.
- La recomendación usa dos niveles. Los cortes por capacidad del analista quedan fuera porque el proyecto no tiene una cifra de capacidad.
- Se muestra una sola recomendación por solicitud; no hay carga masiva de archivos ni historial.
- La nube ejecuta Python 3.12. Ya se comprobó que el modelo carga ahí con probabilidades idénticas y que `requirements.txt` se resuelve para Python 3.12 en Linux.
- Quedan fuera: el despliegue, la presentación, el informe técnico, el cambio de nombre de campos del modelo y cualquier reentrenamiento.
- Para el caso límite se parte de un préstamo de ejemplo y se cambia un dato; el grupo elegirá el dato durante el ensayo, con la app.
