"""Variables del modelo y preprocesamiento.

Todas las columnas que se usan aquí se conocen **al publicar la solicitud**, antes de decidir. Quedan fuera las
del resultado de la financiación (`Investors`, `PercentFunded`, `InvestmentFromFriends*`), `MemberKey` (solo
sirve para partir) y `BorrowerState` (su efecto se prueba solo a través del índice climático).

`add_features` trabaja fila por fila (no aprende nada de los datos), así que puede ir dentro del `Pipeline`.
Lo que sí aprende (medianas, categorías) lo hace `build_preprocessor`, ajustado solo con entrenamiento.
En el notebook 04 se midió cada grupo (`reports/04_features.md`): el pipeline final activa el puntaje de Prosper y
el historial en Prosper, y la revisión de variables (sección 10) quita 8 columnas y agrupa `EmploymentStatus`
(`FINAL_FEATURES`). El índice climático, las razones, el año y las tasas de comportamiento quedan apagados; el código
se conserva porque documenta la prueba.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from proyecto.config import CLIMATE_INDEX_COL

FIRST_CREDIT_LINE_FORMAT = "%d/%m/%Y %H:%M"

# Referencia: perfil de buró del prestatario y condiciones del préstamo que solicita
NUMERIC_BASE = [
    "Term",
    "LoanOriginalAmount",
    "MonthlyLoanPayment",
    "CreditScoreRangeLower",  # CreditScoreRangeUpper = Lower + 19: redundante
    "EmploymentStatusDuration",
    "CurrentCreditLines",
    "OpenCreditLines",
    "TotalCreditLinespast7years",
    "OpenRevolvingAccounts",
    "OpenRevolvingMonthlyPayment",
    "InquiriesLast6Months",
    "TotalInquiries",
    "CurrentDelinquencies",
    "AmountDelinquent",
    "DelinquenciesLast7Years",
    "PublicRecordsLast10Years",
    "PublicRecordsLast12Months",
    "RevolvingCreditBalance",
    "BankcardUtilization",
    "AvailableBankcardCredit",
    "TotalTrades",
    "TradesNeverDelinquent (percentage)",
    "TradesOpenedLast6Months",
    "DebtToIncomeRatio",
    "StatedMonthlyIncome",
    "Recommendations",
]
CATEGORICAL_BASE = [
    "IncomeRange",
    "EmploymentStatus",
    "IsBorrowerHomeowner",
    "IncomeVerifiable",
    "CurrentlyInGroup",
    "ListingCategory (numeric)",  # es un código de propósito del préstamo, no una cantidad
]

# Idea 1: índice climático por estado (supuesto académico)
NUMERIC_CLIMATE = [CLIMATE_INDEX_COL]

# Idea 2: el puntaje y el precio que Prosper asigna a la solicitud (CreditGrade antes de 2009, ProsperRating después)
NUMERIC_PROSPER_SCORES = [
    "BorrowerAPR",  # BorrowerRate y LenderYield tienen correlación 0,99 con ella: se usa solo una
    "ProsperRating (numeric)",
    "ProsperScore",
    "EstimatedLoss",
    "EstimatedReturn",
    "EstimatedEffectiveYield",
]
CATEGORICAL_PROSPER_SCORES = ["CreditGrade"]

# Idea 3: historial del prestatario en Prosper al publicar la solicitud (vacío = no tenía préstamos previos)
PROSPER_HISTORY_COUNTS = [
    "TotalProsperLoans",
    "TotalProsperPaymentsBilled",
    "OnTimeProsperPayments",
    "ProsperPaymentsLessThanOneMonthLate",
    "ProsperPaymentsOneMonthPlusLate",
    "ProsperPrincipalBorrowed",
    "ProsperPrincipalOutstanding",
]
NUMERIC_PROSPER_HISTORY = PROSPER_HISTORY_COUNTS + ["ScorexChangeAtTimeOfListing", "has_prior_prosper_loan"]

# Idea 4: razones financieras
NUMERIC_RATIOS = ["payment_to_income", "amount_to_annual_income", "credit_history_years"]

# Idea 5: año de originación (control: mide cuánto pesa la época en la muestra)
NUMERIC_YEAR = ["origination_year"]


# Revisión de variables (31 oct): candidatas a crear
# Comportamiento en Prosper: proporción de pagos atrasados y parte de lo prestado que sigue pendiente
NUMERIC_PROSPER_HISTORY_RATES = ["prosper_late_payment_rate", "prosper_outstanding_share"]
# EmploymentStatus cambió de codificación en julio de 2009 ("Employed" solo existe después; "Not available" solo antes):
# se agrupan las categorías equivalentes para que la variable no marque la época
EMPLOYMENT_GROUPS = {
    "Employed": "Employed", "Full-time": "Employed", "Part-time": "Employed",
    "Self-employed": "Self-employed", "Retired": "Retired", "Not employed": "Not employed", "Other": "Other",
}  # "Not available" y vacío -> vacío ("Unknown" en el pipeline)

# Revisión de variables (31 oct): candidatas a eliminar, por grupo
REDUNDANT_COLUMNS = [
    "TotalProsperPaymentsBilled",  # = pagos a tiempo + atrasados (100 % de las filas)
    "OpenCreditLines",  # Spearman 0,95 con CurrentCreditLines
    "TotalCreditLinespast7years",  # Spearman 0,95 con TotalTrades
    "EstimatedReturn",  # = EstimatedEffectiveYield − EstimatedLoss según el diccionario
]
NEAR_CONSTANT_COLUMNS = [
    "ProsperPaymentsOneMonthPlusLate",  # 0 en el 99,6 %
    "Recommendations",  # 0 en el 92,7 %
    "PublicRecordsLast12Months",  # 0 en el 90,4 %
]
ERA_MARKER_COLUMNS = ["CurrentlyInGroup"]  # 33 % antes de julio de 2009 frente a 5 % después (Prosper retiró los grupos)

# Variables finales (etapa 4, aprobadas el 31 oct): referencia + puntaje de Prosper + historial en Prosper.
# Revisión del 31 oct (notebook 04, sección 10): se quitan 8 columnas redundantes, casi constantes o que marcan la
# época, y se agrupa EmploymentStatus. Rinde igual (AUC-PR 0,6107 frente a 0,6104) con 34 numéricas y 6 categóricas.
FINAL_FEATURES = {
    "use_prosper_scores": True,
    "use_prosper_history": True,
    "group_employment": True,
    "exclude": tuple(REDUNDANT_COLUMNS + NEAR_CONSTANT_COLUMNS + ERA_MARKER_COLUMNS),
}


def _ratio(num: pd.Series, den: pd.Series) -> pd.Series:
    """División segura: denominador cero o ausente -> NaN."""
    return num / den.where(den > 0)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Añade las variables calculadas (ideas 3, 4 y 5). No modifica el original.

    - Historial en Prosper: un vacío significa "sin préstamos previos", así que los conteos y montos pasan a 0
      y se marca `has_prior_prosper_loan`. `ScorexChangeAtTimeOfListing` queda vacío: sin préstamo previo no
      hay cambio de puntaje que medir.
    - Razones: cuota / ingreso mensual, monto / ingreso anual y años de historial crediticio al originar.
    - Año de originación.
    - Comportamiento en Prosper: pagos atrasados / pagos facturados y principal pendiente / principal prestado
      (vacío si no hubo préstamos previos).
    - `employment_status_grouped`: `EmploymentStatus` con las categorías equivalentes agrupadas.
    """
    out = df.copy()

    out["has_prior_prosper_loan"] = out["TotalProsperLoans"].notna().astype(float)
    out[PROSPER_HISTORY_COUNTS] = out[PROSPER_HISTORY_COUNTS].fillna(0)

    out["payment_to_income"] = _ratio(out["MonthlyLoanPayment"], out["StatedMonthlyIncome"])
    out["amount_to_annual_income"] = _ratio(out["LoanOriginalAmount"], 12 * out["StatedMonthlyIncome"])
    origination = pd.to_datetime(out["LoanOriginationDate"])
    first_line = pd.to_datetime(out["FirstRecordedCreditLine"], format=FIRST_CREDIT_LINE_FORMAT, errors="coerce")
    out["credit_history_years"] = (origination - first_line).dt.days / 365.25

    out["origination_year"] = origination.dt.year.astype(float)

    late = out["ProsperPaymentsLessThanOneMonthLate"] + out["ProsperPaymentsOneMonthPlusLate"]
    out["prosper_late_payment_rate"] = _ratio(late, out["TotalProsperPaymentsBilled"])
    out["prosper_outstanding_share"] = _ratio(out["ProsperPrincipalOutstanding"], out["ProsperPrincipalBorrowed"])
    out["employment_status_grouped"] = out["EmploymentStatus"].map(EMPLOYMENT_GROUPS)
    return out


def feature_columns(
    use_climate: bool = False,
    use_prosper_scores: bool = False,
    use_prosper_history: bool = False,
    use_ratios: bool = False,
    use_year: bool = False,
    use_history_rates: bool = False,
    group_employment: bool = False,
    exclude: list[str] | tuple[str, ...] | None = None,
) -> tuple[list[str], list[str]]:
    """Devuelve (numéricas, categóricas) que usa el modelo según las ideas activadas.

    `exclude` quita columnas (p. ej. `REDUNDANT_COLUMNS`); `group_employment` cambia `EmploymentStatus` por su
    versión agrupada.
    """
    numeric = list(NUMERIC_BASE)
    categorical = list(CATEGORICAL_BASE)
    if use_climate:
        numeric += NUMERIC_CLIMATE
    if use_prosper_scores:
        numeric += NUMERIC_PROSPER_SCORES
        categorical += CATEGORICAL_PROSPER_SCORES
    if use_prosper_history:
        numeric += NUMERIC_PROSPER_HISTORY
    if use_ratios:
        numeric += NUMERIC_RATIOS
    if use_year:
        numeric += NUMERIC_YEAR
    if use_history_rates:
        numeric += NUMERIC_PROSPER_HISTORY_RATES
    if group_employment:
        categorical = ["employment_status_grouped" if c == "EmploymentStatus" else c for c in categorical]
    drop = set(exclude or [])
    return [c for c in numeric if c not in drop], [c for c in categorical if c not in drop]


def to_text(X: pd.DataFrame) -> pd.DataFrame:
    """Convierte las categóricas a texto (incluidos códigos numéricos) y deja los vacíos como NaN."""
    return X.apply(lambda col: col.map(lambda v: np.nan if pd.isna(v) else str(v))).astype(object)


def build_preprocessor(scale: bool = True, **feature_flags) -> ColumnTransformer:
    """Imputación (+ escalado) de numéricas y one-hot de categóricas, ajustados solo con entrenamiento."""
    numeric, categorical = feature_columns(**feature_flags)
    numeric_steps = [("impute", SimpleImputer(strategy="median", add_indicator=True))]
    if scale:
        numeric_steps.append(("scale", StandardScaler()))
    categorical_steps = [
        ("text", FunctionTransformer(to_text, feature_names_out="one-to-one")),
        ("impute", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=0.01, sparse_output=False)),
    ]
    return ColumnTransformer(
        [
            ("num", Pipeline(numeric_steps), numeric),
            ("cat", Pipeline(categorical_steps), categorical),
        ],
        remainder="drop",
    )
