"""Diccionario de columnas: unidad y descripción.

Toda columna que se agregue a la base debe declararse aquí; el build falla si
falta alguna. Los montos son siempre USD nominales (banco de EE. UU., sin
conversión de moneda).
"""

USD = "USD"
USD_SIGNED = "USD±"  # monto en USD que puede ser negativo (p. ej. flujos netos)

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

# Paso 1 · Balances & AUM (variables 1, 2, 17, 18 del Excel)
STEP1_COLUMNS: dict[str, tuple[str, str]] = {
    "household_id": ("id", "Identificador del hogar"),
    "aum_outflow_30d": (USD, "#1 · max(0, retiros − aportes) de inversión, último mes; NULL sin inversiones"),
    "aum_outflow_pct_30d": ("fracción", "#1 · aum_outflow_30d ÷ AUM promedio de la ventana"),
    "aum_outflow_90d": (USD, "#1 · max(0, retiros − aportes) de inversión, últimos 3 meses"),
    "aum_outflow_pct_90d": ("fracción", "#1 · aum_outflow_90d ÷ AUM promedio (alerta > 10%)"),
    "deposit_balance_change_pct_30d": ("fracción", "#2 · media último mes ÷ mes previo − 1"),
    "deposit_balance_change_pct_90d": ("fracción", "#2 · media 3m ÷ 3m previos − 1 (alerta ≤ −25%); NULL si base < $10k"),
    "deposit_balance_change_pct_180d": ("fracción", "#2 · media 6m ÷ 6m previos − 1"),
    "aum_vs_baseline_pct": ("fracción", "#17 · AUM ex-mercado t ÷ media meses −6..−1 − 1 (alerta ≤ −20%)"),
    "deposit_balance_vs_6m_avg_pct": ("fracción", "#18 · depósitos último mes ÷ media meses −6..−1 − 1 (alerta ≤ −30%)"),
}

# Paso 2 · Recurring deposits & flows (variables 3, 4, 5, 6, 19, 20 del Excel)
STEP2_COLUMNS: dict[str, tuple[str, str]] = {
    "household_id": ("id", "Identificador del hogar"),
    "salary_deposit_stopped_flag": ("0/1", "#3 · nómina detectada que dejó de llegar (45d); NULL sin patrón de nómina"),
    "pension_deposit_stopped_flag": ("0/1", "#19 · pensión detectada que dejó de llegar; NULL sin patrón de pensión"),
    "recurring_deposit_stopped_flag": ("0/1", "#4 · algún flujo recurrente ≥ 10% del ingreso dejó de llegar"),
    "recurring_deposit_stopped_type": ("categoría", "#4 · tipo del flujo detenido (explica la alerta)"),
    "recurring_deposit_change_pct": ("fracción", "#5 · recurrente últimos 30d ÷ promedio mensual meses −7..−1 − 1"),
    "net_deposit_flow_30d": (USD_SIGNED, "#6 · entradas − salidas de depósitos, último mes"),
    "net_deposit_flow_pct_30d": ("fracción", "#6 · net_deposit_flow_30d ÷ saldo promedio"),
    "net_deposit_flow_90d": (USD_SIGNED, "#6 · entradas − salidas de depósitos, últimos 3 meses"),
    "net_deposit_flow_pct_90d": ("fracción", "#6 · net_deposit_flow_90d ÷ saldo promedio (alerta ≤ −15%)"),
    "business_payroll_stopped_flag": ("0/1", "#20 · la nómina del negocio no corrió en 60d; NULL sin negocio / patrón"),
}
