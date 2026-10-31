# Diccionario de datos — Prosper Loan Data

> Definiciones **originales en inglés**, copiadas de la descripción del dataset en Kaggle
> (https://www.kaggle.com/datasets/henryokam/prosper-loan-data, Henry Okam, licencia CC0; consultado el 31 oct 2026).
> Las columnas «Uso en Eco-Score» y «Nota» son del grupo. Las 81 columnas siguen el orden del CSV.

| # | Variable | Definición (Kaggle) | Uso en Eco-Score | Nota |
|---|---|---|---|---|
| 1 | `ListingKey` | Unique key for each listing, same value as the 'key' used in the listing object in the API. | Fuera: llave (dato personal seudónimo) |  |
| 2 | `ListingNumber` | The number that uniquely identifies the listing to the public as displayed on the website. | Fuera: llave (dato personal seudónimo) |  |
| 3 | `ListingCreationDate` | The date the listing was created. | Fuera: fecha dañada en el CSV |  |
| 4 | `CreditGrade` | The Credit rating that was assigned at the time the listing went live. Applicable for listings pre-2009 period and will only be populated for those listings. | Modelo: puntaje y precio de Prosper |  |
| 5 | `Term` | The length of the loan expressed in months. | Modelo: referencia |  |
| 6 | `LoanStatus` | The current status of the loan: Cancelled, Chargedoff, Completed, Current, Defaulted, FinalPaymentInProgress, PastDue. The PastDue status will be accompanied by a delinquency bucket. | Fuente del objetivo `is_default`; se quita |  |
| 7 | `ClosedDate` | Closed date is applicable for Cancelled, Completed, Chargedoff and Defaulted loan statuses. | Fuera: se conoce después de otorgar (fuga) |  |
| 8 | `BorrowerAPR` | The Borrower's Annual Percentage Rate (APR) for the loan. | Modelo: puntaje y precio de Prosper |  |
| 9 | `BorrowerRate` | The Borrower's interest rate for this loan. | Fuera: redundante con `BorrowerAPR` (correlación 0,99) |  |
| 10 | `LenderYield` | The Lender yield on the loan. Lender yield is equal to the interest rate on the loan less the servicing fee. | Fuera: redundante con `BorrowerAPR` (correlación 0,99) |  |
| 11 | `EstimatedEffectiveYield` | Effective yield is equal to the borrower interest rate (i) minus the servicing fee rate, (ii) minus estimated uncollected interest on charge-offs, (iii) plus estimated collected late fees. Applicable for loans originated after July 2009. | Modelo: puntaje y precio de Prosper |  |
| 12 | `EstimatedLoss` | Estimated loss is the estimated principal loss on charge-offs. Applicable for loans originated after July 2009. | Modelo: puntaje y precio de Prosper |  |
| 13 | `EstimatedReturn` | The estimated return assigned to the listing at the time it was created. Estimated return is the difference between the Estimated Effective Yield and the Estimated Loss Rate. Applicable for loans originated after July 2009. | Modelo: puntaje y precio de Prosper |  |
| 14 | `ProsperRating (numeric)` | The Prosper Rating assigned at the time the listing was created: 0 - N/A, 1 - HR, 2 - E, 3 - D, 4 - C, 5 - B, 6 - A, 7 - AA. Applicable for loans originated after July 2009. | Modelo: puntaje y precio de Prosper | Existe desde julio de 2009 |
| 15 | `ProsperRating (Alpha)` | The Prosper Rating assigned at the time the listing was created between AA - HR. Applicable for loans originated after July 2009. | Fuera: igual a la versión numérica |  |
| 16 | `ProsperScore` | A custom risk score built using historical Prosper data. The score ranges from 1-10, with 10 being the best, or lowest risk score. Applicable for loans originated after July 2009. | Modelo: puntaje y precio de Prosper | El diccionario dice 1–10; en entrenamiento hay 29 préstamos con 11 |
| 17 | `ListingCategory (numeric)` | The category of the listing that the borrower selected when posting their listing: 0 - Not Available, 1 - Debt Consolidation, 2 - Home Improvement, 3 - Business, 4 - Personal Loan, 5 - Student Use, 6 - Auto, 7- Other, 8 - Baby&Adoption, 9 - Boat, 10 - Cosmetic Procedure, 11 - Engagement Ring, 12 - Green Loans, 13 - Household Expenses, 14 - Large Purchases, 15 - Medical/Dental, 16 - Motorcycle, 17 - RV, 18 - Taxes, 19 - Vacation, 20 - Wedding Loans | Modelo: referencia | 0 = "Not Available" (23 % del entrenamiento); se trata como categoría propia |
| 18 | `BorrowerState` | The two letter abbreviation of the state of the address of the borrower at the time the Listing was created. | Solo para calcular el índice climático |  |
| 19 | `Occupation` | The Occupation selected by the Borrower at the time they created the listing. | Fuera: cuasi-identificador |  |
| 20 | `EmploymentStatus` | The employment status of the borrower at the time they posted the listing. | Modelo: referencia |  |
| 21 | `EmploymentStatusDuration` | The length in months of the employment status at the time the listing was created. | Modelo: referencia |  |
| 22 | `IsBorrowerHomeowner` | A Borrower will be classified as a homowner if they have a mortgage on their credit profile or provide documentation confirming they are a homeowner. | Modelo: referencia |  |
| 23 | `CurrentlyInGroup` | Specifies whether or not the Borrower was in a group at the time the listing was created. | Modelo: referencia |  |
| 24 | `GroupKey` | The Key of the group in which the Borrower is a member of. Value will be null if the borrower does not have a group affiliation. | Fuera: llave (dato personal seudónimo) |  |
| 25 | `DateCreditPulled` | The date the credit profile was pulled. | Fuera: fecha dañada en el CSV |  |
| 26 | `CreditScoreRangeLower` | The lower value representing the range of the borrower's credit score as provided by a consumer credit rating agency. | Modelo: referencia |  |
| 27 | `CreditScoreRangeUpper` | The upper value representing the range of the borrower's credit score as provided by a consumer credit rating agency. | Fuera: redundante (= Lower + 19) |  |
| 28 | `FirstRecordedCreditLine` | The date the first credit line was opened. | Solo en la idea descartada de razones (años de historial) |  |
| 29 | `CurrentCreditLines` | Number of current credit lines at the time the credit profile was pulled. | Modelo: referencia |  |
| 30 | `OpenCreditLines` | Number of open credit lines at the time the credit profile was pulled. | Modelo: referencia |  |
| 31 | `TotalCreditLinespast7years` | Number of credit lines in the past seven years at the time the credit profile was pulled. | Modelo: referencia |  |
| 32 | `OpenRevolvingAccounts` | Number of open revolving accounts at the time the credit profile was pulled. | Modelo: referencia |  |
| 33 | `OpenRevolvingMonthlyPayment` | Monthly payment on revolving accounts at the time the credit profile was pulled. | Modelo: referencia |  |
| 34 | `InquiriesLast6Months` | Number of inquiries in the past six months at the time the credit profile was pulled. | Modelo: referencia |  |
| 35 | `TotalInquiries` | Total number of inquiries at the time the credit profile was pulled. | Modelo: referencia |  |
| 36 | `CurrentDelinquencies` | Number of accounts delinquent at the time the credit profile was pulled. | Modelo: referencia |  |
| 37 | `AmountDelinquent` | Dollars delinquent at the time the credit profile was pulled. | Modelo: referencia |  |
| 38 | `DelinquenciesLast7Years` | Number of delinquencies in the past 7 years at the time the credit profile was pulled. | Modelo: referencia |  |
| 39 | `PublicRecordsLast10Years` | Number of public records in the past 10 years at the time the credit profile was pulled. | Modelo: referencia |  |
| 40 | `PublicRecordsLast12Months` | Number of public records in the past 12 months at the time the credit profile was pulled. | Modelo: referencia |  |
| 41 | `RevolvingCreditBalance` | Dollars of revolving credit at the time the credit profile was pulled. | Modelo: referencia |  |
| 42 | `BankcardUtilization` | The percentage of available revolving credit that is utilized at the time the credit profile was pulled. | Modelo: referencia |  |
| 43 | `AvailableBankcardCredit` | The total available credit via bank card at the time the credit profile was pulled. | Modelo: referencia |  |
| 44 | `TotalTrades` | Number of trade lines ever opened at the time the credit profile was pulled. | Modelo: referencia |  |
| 45 | `TradesNeverDelinquent (percentage)` | Number of trades that have never been delinquent at the time the credit profile was pulled. | Modelo: referencia | En el CSV viene como proporción 0–1, no como número |
| 46 | `TradesOpenedLast6Months` | Number of trades opened in the last 6 months at the time the credit profile was pulled. | Modelo: referencia |  |
| 47 | `DebtToIncomeRatio` | The debt to income ratio of the borrower at the time the credit profile was pulled. This value is Null if the debt to income ratio is not available. This value is capped at 10.01 (any debt to income ratio larger than 1000% will be returned as 1001%). | Modelo: referencia | Tope 10,01 = "1000 % o más" (confirma la decisión de conservarlo) |
| 48 | `IncomeRange` | The income range of the borrower at the time the listing was created. | Modelo: referencia |  |
| 49 | `IncomeVerifiable` | The borrower indicated they have the required documentation to support their income. | Modelo: referencia |  |
| 50 | `StatedMonthlyIncome` | The monthly income the borrower stated at the time the listing was created. | Modelo: referencia |  |
| 51 | `LoanKey` | Unique key for each loan. This is the same key that is used in the API. | Fuera: llave (dato personal seudónimo) |  |
| 52 | `TotalProsperLoans` | Number of Prosper loans the borrower at the time they created this listing. This value will be null if the borrower had no prior loans. | Modelo: historial en Prosper (vacío → 0 + marca) | Vacío = sin préstamos previos (confirma el tratamiento) |
| 53 | `TotalProsperPaymentsBilled` | Number of on time payments the borrower made on Prosper loans at the time they created this listing. This value will be null if the borrower had no prior loans. | Modelo: historial en Prosper (vacío → 0 + marca) |  |
| 54 | `OnTimeProsperPayments` | Number of on time payments the borrower had made on Prosper loans at the time they created this listing. This value will be null if the borrower has no prior loans. | Modelo: historial en Prosper (vacío → 0 + marca) |  |
| 55 | `ProsperPaymentsLessThanOneMonthLate` | Number of payments the borrower made on Prosper loans that were less than one month late at the time they created this listing. This value will be null if the borrower had no prior loans. | Modelo: historial en Prosper (vacío → 0 + marca) |  |
| 56 | `ProsperPaymentsOneMonthPlusLate` | Number of payments the borrower made on Prosper loans that were greater than one month late at the time they created this listing. This value will be null if the borrower had no prior loans. | Modelo: historial en Prosper (vacío → 0 + marca) |  |
| 57 | `ProsperPrincipalBorrowed` | Total principal borrowed on Prosper loans at the time the listing was created. This value will be null if the borrower had no prior loans. | Modelo: historial en Prosper (vacío → 0 + marca) |  |
| 58 | `ProsperPrincipalOutstanding` | Principal outstanding on Prosper loans at the time the listing was created. This value will be null if the borrower had no prior loans. | Modelo: historial en Prosper (vacío → 0 + marca) |  |
| 59 | `ScorexChangeAtTimeOfListing` | Borrower's credit score change at the time the credit profile was pulled. This will be the change relative to the borrower's last Prosper loan. This value will be null if the borrower had no prior loans. | Modelo: historial en Prosper (vacío → 0 + marca) |  |
| 60 | `LoanCurrentDaysDelinquent` | The number of days delinquent. | Fuera: se conoce después de otorgar (fuga) |  |
| 61 | `LoanFirstDefaultedCycleNumber` | The cycle the loan was charged off. If the loan has not charged off the value will be null. | Fuera: se conoce después de otorgar (fuga) |  |
| 62 | `LoanMonthsSinceOrigination` | Number of months since the loan originated. | Fuera: se conoce después de otorgar (fuga) |  |
| 63 | `LoanNumber` | Unique numeric value associated with the loan. | Fuera: llave (dato personal seudónimo) |  |
| 64 | `LoanOriginalAmount` | The origination amount of the loan. | Modelo: referencia | Monto originado; en el 0,8 % de los préstamos la financiación no fue del 100 % |
| 65 | `LoanOriginationDate` | The date the loan was originated. | Fecha de referencia; no es variable del modelo |  |
| 66 | `LoanOriginationQuarter` | The quarter in which the loan was originated. | Fecha de referencia; no es variable del modelo |  |
| 67 | `MemberKey` | The unique key that is associated with the borrower. This is the same identifier that is used in the API member object. | Solo para partir por prestatario |  |
| 68 | `MonthlyLoanPayment` | The scheduled monthly loan payment. | Modelo: referencia | Es la cuota programada: una cuota 0 es imposible (se recalcula, regla 11) |
| 69 | `LP_CustomerPayments` | Pre charge-off cumulative gross payments made by the borrower on the loan. If the loan has charged off, this value will exclude any recoveries. | Fuera: se conoce después de otorgar (fuga) |  |
| 70 | `LP_CustomerPrincipalPayments` | Pre charge-off cumulative principal payments made by the borrower on the loan. If the loan has charged off, this value will exclude any recoveries. | Fuera: se conoce después de otorgar (fuga) |  |
| 71 | `LP_InterestandFees` | Pre charge-off cumulative interest and fees paid by the borrower. If the loan has charged off, this value will exclude any recoveries. | Fuera: se conoce después de otorgar (fuga) |  |
| 72 | `LP_ServiceFees` | Cumulative service fees paid by the investors who have invested in the loan. | Fuera: se conoce después de otorgar (fuga) |  |
| 73 | `LP_CollectionFees` | Cumulative collection fees paid by the investors who have invested in the loan. | Fuera: se conoce después de otorgar (fuga) |  |
| 74 | `LP_GrossPrincipalLoss` | The gross charged off amount of the loan. | Fuera: se conoce después de otorgar (fuga) |  |
| 75 | `LP_NetPrincipalLoss` | The principal that remains uncollected after any recoveries. | Fuera: se conoce después de otorgar (fuga) |  |
| 76 | `LP_NonPrincipalRecoverypayments` | The interest and fee component of any recovery payments. The current payment policy applies payments in the following order: Fees, interest, principal. | Fuera: se conoce después de otorgar (fuga) |  |
| 77 | `PercentFunded` | Percent the listing was funded. | Fuera: resultado de la financiación (después de publicar) |  |
| 78 | `Recommendations` | Number of recommendations the borrower had at the time the listing was created. | Modelo: referencia |  |
| 79 | `InvestmentFromFriendsCount` | Number of friends that made an investment in the loan. | Fuera: resultado de la financiación (después de publicar) |  |
| 80 | `InvestmentFromFriendsAmount` | Dollar amount of investments that were made by friends. | Fuera: resultado de la financiación (después de publicar) |  |
| 81 | `Investors` | The number of investors that funded the loan. | Fuera: resultado de la financiación (después de publicar) |  |

Variables creadas por el proyecto (no están en el CSV):

| Variable | Definición | Uso |
|---|---|---|
| `is_default` | 1 si `LoanStatus` es `Chargedoff` o `Defaulted`; 0 si es `Completed` | Objetivo |
| `Precipitation_Risk_Index` | Índice climático manual de 10 estados (el resto 50,0); supuesto académico sin fuente verificable | Medido en el notebook 04: no entra |
| `has_prior_prosper_loan` | 1 si `TotalProsperLoans` no está vacío | Modelo: historial en Prosper |
| `payment_to_income`, `amount_to_annual_income`, `credit_history_years`, `origination_year` | Razones y año calculados en `add_features` | Medidas en el notebook 04: no entran |
