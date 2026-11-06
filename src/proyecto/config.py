"""Constantes del proyecto Eco-Score: rutas, columnas, objetivo, partición y matriz de costos."""
from pathlib import Path

import numpy as np

# src/proyecto/config.py -> la raíz del repo está dos niveles arriba de src/
ROOT = Path(__file__).resolve().parents[2]
RAW_CSV = ROOT / "data" / "raw" / "prosperLoanData.csv"
RAW_SEP = ";"
PROCESSED_DIR = ROOT / "data" / "processed"  # se regenera con el notebook 03; no se versiona
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"

RANDOM_STATE = 42
TEST_SIZE = 0.2
GROUP_COL = "MemberKey"  # unidad para partir: el prestatario, no la fila
ANONYMOUS_GROUP_COL = "borrower_id"  # número que reemplaza a MemberKey en los archivos que se versionan
TARGET = "is_default"

# 0 = pagó, 1 = impago
CLASSES = ["pagó", "impago"]

# Matriz de costos de equivocarse: filas = clase real, columnas = clase predicha (orden CLASSES).
# No detectar un impago cuesta unas 4 veces más que rechazar a un buen cliente (notebooks/01_caso_negocio.ipynb).
COST_MATRIX = np.array(
    [
        [0, 1],  # real pagó:   predice pagó / impago
        [4, 0],  # real impago
    ],
    dtype=float,
)

# Objetivo: solo préstamos terminados (decisión 1 del EDA)
DEFAULT_STATUSES = ["Chargedoff", "Defaulted"]
PAID_STATUSES = ["Completed"]

# Datos personales y llaves (sección 2 de especificaciones/03-preprocesamiento.md)
GROUP_KEY_COLUMNS = ["GroupKey"]  # se quita al cargar
LISTING_KEY_COLUMNS = ["ListingKey", "ListingNumber", "LoanKey", "LoanNumber"]  # se quitan tras quitar repetidos
QUASI_IDENTIFIER_COLUMNS = ["Occupation"]  # cuasi-identificador: se quita (ver reports/03_preprocesamiento.md)

# Columnas que solo se conocen después de otorgar el préstamo (decisión 5 del EDA)
LEAKAGE_COLUMNS = [
    "LP_CustomerPayments",
    "LP_CustomerPrincipalPayments",
    "LP_InterestandFees",
    "LP_ServiceFees",
    "LP_CollectionFees",
    "LP_GrossPrincipalLoss",
    "LP_NetPrincipalLoss",
    "LP_NonPrincipalRecoverypayments",
    "ClosedDate",
    "LoanCurrentDaysDelinquent",
    "LoanFirstDefaultedCycleNumber",
    "LoanMonthsSinceOrigination",
]

# Fechas dañadas (decisión 9 del EDA)
DAMAGED_DATE_COLUMNS = ["ListingCreationDate", "DateCreditPulled"]
ORIGINATION_DATE_FORMAT = "%d/%m/%Y %H:%M"

# Categorías válidas de IncomeRange (decisión 6 del EDA)
INCOME_RANGE_CATEGORIES = [
    "$0",
    "$1-24,999",
    "$25,000-49,999",
    "$50,000-74,999",
    "$75,000-99,999",
    "$100,000+",
    "Not employed",
    "Not displayed",
]
# Rangos en los que un ingreso mensual de 0 es coherente
ZERO_INCOME_RANGES = ["$0", "Not employed"]

MAX_MONTHLY_INCOME = 100_000  # USD/mes; por encima se considera imposible (decisión 7 del EDA)

# Índice climático: supuesto académico del grupo, sin fuente verificable (decisión 10 del EDA)
CLIMATE_INDEX_COL = "Precipitation_Risk_Index"
CLIMATE_RISK_MATRIX = {
    "FL": 94.2, "LA": 91.0, "TX": 83.5, "NC": 77.1, "GA": 70.4,
    "NY": 56.8, "CA": 48.0, "OH": 40.2, "NV": 14.1, "UT": 10.5,
}
CLIMATE_DEFAULT = 50.0

# Desde esta fecha Prosper asigna ProsperRating, ProsperScore y las estimaciones (diccionario de datos de Kaggle)
PROSPER_RATING_START = "2009-07-01"
