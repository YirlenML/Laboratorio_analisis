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

# Rangos POSIBLES en el mundo real (conocimiento del analista, no de los datos). Fuera de ellos, la predicción se niega.
# Son más amplios que lo observado: el rango observado solo genera una advertencia (ver `validate_inputs`).
PLAUSIBLE_RANGE = {
    "Term": (1, 120),  # meses
    "LoanOriginalAmount": (1, 1_000_000),  # USD
    "MonthlyLoanPayment": (0, 100_000),  # USD/mes
    "CreditScoreRangeLower": (300, 900),  # escala de los puntajes de crédito; 0 es imposible (decisión 7 del EDA)
    "EmploymentStatusDuration": (0, 960),  # meses: 80 años
    "CurrentCreditLines": (0, 500),
    "OpenRevolvingAccounts": (0, 500),
    "OpenRevolvingMonthlyPayment": (0, 1_000_000),
    "InquiriesLast6Months": (0, 1_000),
    "TotalInquiries": (0, 5_000),
    "CurrentDelinquencies": (0, 500),
    "AmountDelinquent": (0, 10_000_000),
    "DelinquenciesLast7Years": (0, 1_000),
    "PublicRecordsLast10Years": (0, 200),
    "RevolvingCreditBalance": (0, 100_000_000),
    "BankcardUtilization": (0, 10),  # proporción: puede pasar de 1 si se excede el cupo
    "AvailableBankcardCredit": (0, 100_000_000),
    "TotalTrades": (0, 1_000),
    "TradesNeverDelinquent (percentage)": (0, 1),  # llega como proporción
    "TradesOpenedLast6Months": (0, 500),
    "DebtToIncomeRatio": (0, 10.01),  # 10,01 es el tope del sistema (diccionario de datos)
    "StatedMonthlyIncome": (0, MAX_MONTHLY_INCOME),  # decisión 7 del EDA
    "BorrowerAPR": (0, 1),  # proporción
    "ProsperRating (numeric)": (0, 7),  # diccionario de datos: 0 = N/A ... 7 = AA
    "ProsperScore": (1, 11),  # el diccionario dice 1-10, pero el entrenamiento trae 11 (reports/04_features.md)
    "EstimatedLoss": (0, 1),  # proporción
    "EstimatedEffectiveYield": (-1, 1),  # proporción; puede ser negativa
    "TotalProsperLoans": (0, 100),
    "OnTimeProsperPayments": (0, 2_000),
    "ProsperPaymentsLessThanOneMonthLate": (0, 2_000),
    "ProsperPrincipalBorrowed": (0, 10_000_000),
    "ProsperPrincipalOutstanding": (0, 10_000_000),
    "ScorexChangeAtTimeOfListing": (-600, 600),  # los puntajes van de 300 a 900
}

# Etiquetas del formulario de la app
INPUT_LABELS = {
    "Term": "Plazo (meses)",
    "LoanOriginalAmount": "Monto del préstamo (USD)",
    "MonthlyLoanPayment": "Cuota mensual (USD)",
    "CreditScoreRangeLower": "Puntaje de crédito (límite inferior)",
    "EmploymentStatusDuration": "Meses en la situación laboral actual",
    "CurrentCreditLines": "Líneas de crédito actuales",
    "OpenRevolvingAccounts": "Cuentas revolventes abiertas",
    "OpenRevolvingMonthlyPayment": "Pago mensual revolvente (USD)",
    "InquiriesLast6Months": "Consultas de crédito, últimos 6 meses",
    "TotalInquiries": "Consultas de crédito, total",
    "CurrentDelinquencies": "Cuentas en mora hoy",
    "AmountDelinquent": "Monto en mora (USD)",
    "DelinquenciesLast7Years": "Moras, últimos 7 años",
    "PublicRecordsLast10Years": "Registros públicos, últimos 10 años",
    "RevolvingCreditBalance": "Saldo revolvente (USD)",
    "BankcardUtilization": "Uso de tarjetas (proporción)",
    "AvailableBankcardCredit": "Cupo disponible en tarjetas (USD)",
    "TotalTrades": "Cuentas de crédito abiertas en la historia",
    "TradesNeverDelinquent (percentage)": "Proporción de cuentas nunca en mora",
    "TradesOpenedLast6Months": "Cuentas abiertas, últimos 6 meses",
    "DebtToIncomeRatio": "Deuda / ingreso (proporción)",
    "StatedMonthlyIncome": "Ingreso mensual declarado (USD)",
    "BorrowerAPR": "Tasa anual del prestatario, APR (proporción)",
    "ProsperRating (numeric)": "Calificación Prosper (1 = HR ... 7 = AA)",
    "ProsperScore": "Puntaje Prosper",
    "EstimatedLoss": "Pérdida estimada (proporción)",
    "EstimatedEffectiveYield": "Rendimiento efectivo estimado (proporción)",
    "TotalProsperLoans": "Préstamos previos en Prosper",
    "OnTimeProsperPayments": "Pagos a tiempo en Prosper",
    "ProsperPaymentsLessThanOneMonthLate": "Pagos con menos de un mes de atraso en Prosper",
    "ProsperPrincipalBorrowed": "Capital prestado antes en Prosper (USD)",
    "ProsperPrincipalOutstanding": "Capital pendiente en Prosper (USD)",
    "ScorexChangeAtTimeOfListing": "Cambio del puntaje desde el último préstamo",
    "IncomeRange": "Rango de ingreso anual",
    "EmploymentStatus": "Situación laboral",
    "IsBorrowerHomeowner": "¿Tiene vivienda propia?",
    "IncomeVerifiable": "¿Ingreso verificable?",
    "ListingCategory (numeric)": "Propósito del préstamo",
    "CreditGrade": "Calificación antigua (solo antes de 2009)",
}

# Nombres visibles de los propósitos (traducidos de data/diccionario_datos.md). El modelo sigue recibiendo el código.
LISTING_CATEGORY_LABELS = {
    "0": "No disponible",
    "1": "Consolidación de deudas",
    "2": "Mejoras del hogar",
    "3": "Negocio",
    "4": "Préstamo personal",
    "5": "Uso estudiantil",
    "6": "Automóvil",
    "7": "Otro",
    "8": "Bebé y adopción",
    "9": "Barco",
    "10": "Procedimiento estético",
    "11": "Anillo de compromiso",
    "12": "Préstamos verdes",
    "13": "Gastos del hogar",
    "14": "Compras grandes",
    "15": "Médico o dental",
    "16": "Motocicleta",
    "17": "Casa rodante",
    "18": "Impuestos",
    "19": "Vacaciones",
    "20": "Préstamo para boda",
}

# Nombres visibles de los valores FALSO/VERDADERO; el modelo sigue recibiendo el valor original
YES_NO_LABELS = {"FALSO": "No", "VERDADERO": "Sí"}

# Grupos del formulario: las 39 columnas de `form_columns()`, cada una una sola vez
FIELD_GROUPS = {
    "Condiciones del préstamo": [
        "LoanOriginalAmount",
        "Term",
        "MonthlyLoanPayment",
        "BorrowerAPR",
        "ListingCategory (numeric)",
    ],
    "Ingreso y empleo": [
        "StatedMonthlyIncome",
        "IncomeRange",
        "IncomeVerifiable",
        "EmploymentStatus",
        "EmploymentStatusDuration",
        "IsBorrowerHomeowner",
        "DebtToIncomeRatio",
    ],
    "Historial de crédito": [
        "CreditScoreRangeLower",
        "CurrentCreditLines",
        "OpenRevolvingAccounts",
        "OpenRevolvingMonthlyPayment",
        "RevolvingCreditBalance",
        "BankcardUtilization",
        "AvailableBankcardCredit",
        "InquiriesLast6Months",
        "TotalInquiries",
        "CurrentDelinquencies",
        "AmountDelinquent",
        "DelinquenciesLast7Years",
        "PublicRecordsLast10Years",
        "TotalTrades",
        "TradesNeverDelinquent (percentage)",
        "TradesOpenedLast6Months",
    ],
    "Evaluación de Prosper": [
        "ProsperRating (numeric)",
        "ProsperScore",
        "CreditGrade",
        "EstimatedLoss",
        "EstimatedEffectiveYield",
    ],
    "Historial en Prosper": [
        "TotalProsperLoans",
        "OnTimeProsperPayments",
        "ProsperPaymentsLessThanOneMonthLate",
        "ProsperPrincipalBorrowed",
        "ProsperPrincipalOutstanding",
        "ScorexChangeAtTimeOfListing",
    ],
}

# Datos que la app pide a la vista; los demás son opcionales. Salen del peso SHAP de la etapa 7, sin `CreditGrade`, que
# solo existe antes de 2009, y con el monto, sin el cual una solicitud no se entiende. Lo que se pierde por no llenar el
# resto se mide con la reserva en el notebook 09 y se muestra en la app.
ESSENTIAL_FIELDS = [
    "LoanOriginalAmount",
    "Term",
    "MonthlyLoanPayment",
    "BorrowerAPR",
    "ListingCategory (numeric)",
    "StatedMonthlyIncome",
    "DebtToIncomeRatio",
    "CreditScoreRangeLower",
    "TotalInquiries",
    "InquiriesLast6Months",
    "CurrentDelinquencies",
    "EstimatedEffectiveYield",
]
