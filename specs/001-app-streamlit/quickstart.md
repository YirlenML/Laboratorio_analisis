# Quickstart: comprobar la app

Desde la raíz del repositorio, en PowerShell.

## 1. Pruebas

```powershell
.venv\Scripts\python.exe -m pytest -q
```

Resultado esperado: todas pasan, sin fallos.

## 2. Identidad del modelo

Ejecutar el notebook 09 completo:

```powershell
$env:PYTHONUTF8=1
.venv\Scripts\python.exe -m nbconvert --to notebook --execute --inplace notebooks/09_inferencia.ipynb
```

Debe imprimir `probabilidades idénticas a las del notebook 07: True (diferencia máxima 0.00e+00)`.

## 3. Prueba manual

```powershell
.venv\Scripts\streamlit.exe run app/streamlit_app.py
```

| Caso | Pasos | Qué debes ver |
|---|---|---|
| Normal | Elige "Préstamo real que se pagó" y pulsa Evaluar | Recomendación y probabilidad |
| Límite | Con un ejemplo, cambia un dato hasta cruzar 20 % | La recomendación cambia |
| Inválido | Escribe -500 en el puntaje de crédito y pulsa Evaluar | Error con el campo y el rango; sin recomendación |
| No sé | Formulario en blanco y Evaluar | Recomendación y aviso de datos faltantes |
| Cambio de ejemplo | Evalúa y cambia de ejemplo | Desaparece el resultado anterior |

## 4. Copia limpia

La app debe abrir y evaluar en una carpeta con solo `app/`, `src/`, `models/model.joblib` y `models/input_schema.json`.
Lo cubre `tests/test_app.py`.
