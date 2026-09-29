"""Diccionario de columnas: unidad y descripción.

Toda columna que se agregue a la base debe declararse aquí; el build falla si
falta alguna. Los montos son siempre USD nominales (banco de EE. UU., sin
conversión de moneda).
"""

USD = "USD"

COLUMNS: dict[str, tuple[str, str]] = {
    "household_id": ("id", "Identificador del hogar"),
    "snapshot_date": ("fecha", "Fecha de corte t (ISO 8601)"),
    "segment": ("categoría", "HNW / UHNW (UHNW si relationship_value ≥ USD 30M)"),
    "relationship_value": (USD, "AUM + depósitos en Citizens"),
    "deposit_balance": (USD, "Saldo en depósitos (checking, savings, MM, CD)"),
    "aum": (USD, "Valor de mercado de inversión, custodia y trust; NULL sin inversiones"),
    "has_investments": ("bool", "Tiene cuentas de inversión"),
    "has_advisory": ("bool", "Tiene cuentas advisory con benchmark"),
    "has_linked_business": ("bool", "Tiene un negocio vinculado"),
    "has_trust": ("bool", "Tiene trust"),
    "has_credit_anchor": ("bool", "Tiene hipoteca o línea de crédito con Citizens"),
    "has_payroll_stream": ("bool", "Recibe nómina en Citizens"),
    "has_pension_stream": ("bool", "Recibe pensión / Social Security en Citizens"),
    "has_dividend_stream": ("bool", "Recibe dividendos en Citizens"),
    "has_any_recurring_stream": ("bool", "Tiene al menos un flujo recurrente (incl. negocio)"),
    "age_primary": ("años", "Edad del titular principal"),
    "tenure_years": ("años", "Antigüedad con el banco"),
    "history_months": ("meses", "Historia disponible, tope 24"),
    "salary_base_annual": (USD, "Sueldo base anual; NULL sin nómina"),
    "bonus_annual": (USD, "Bono anual (un pago); NULL sin nómina"),
    "pay_frequency": ("categoría", "biweekly / semimonthly / monthly"),
    "pension_monthly": (USD, "Pensión mensual; NULL sin pensión"),
    "dividend_annual": (USD, "Dividendos anuales; NULL sin flujo de dividendos"),
    "business_distribution_annual": (USD, "Distribuciones anuales del negocio; NULL sin negocio"),
    "recurring_income_monthly": (USD, "Ingreso recurrente mensual sin bono"),
    "churn_excluded": ("bool", "Excluido del target (muerte / reubicación)"),
    "hard_churn_6m": ("0/1", "Salida total en (t, t+6m]; NULL si excluido"),
    "soft_churn_3m": ("0/1", "Contracción > 20% sin salida en (t, t+3m]; NULL si excluido"),
    "value_lost_6m": (USD, "Valor perdido por churn; NULL si excluido"),
}
