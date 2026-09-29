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

# Paso 3 · Transfers (variables 7, 8, 21, 22, 23, 24, 25 del Excel)
STEP3_COLUMNS: dict[str, tuple[str, str]] = {
    "household_id": ("id", "Identificador del hogar"),
    "external_transfer_amount_60d": (USD, "#7 · transferencias externas (wire, ACH, ACATS) 60d, sin excluidos"),
    "external_transfer_pct_of_balance_60d": ("fracción", "#7 · ÷ saldo promedio (depósitos + cash en inversión) (alerta > 15%)"),
    "external_transfer_pct_of_balance_30d": ("fracción", "#7 · versión 30d"),
    "new_external_destinations_30d": ("entero", "#8 · destinos nuevos en 30d (acumulado ≥ $50k, ausentes 12m previos)"),
    "new_external_destinations_90d": ("entero", "#8 · versión 90d (principal, D-18)"),
    "transfer_to_competitor_bank_amount_90d": (USD, "#21 · enviado a bancos del catálogo de competidores, 90d"),
    "transfer_to_competitor_pct_90d": ("fracción", "#21 · ÷ saldo promedio (alerta > 10%)"),
    "external_transfer_acceleration": ("fracción", "#22 · [(A1 − A2) − (A2 − A3)] ÷ saldo promedio 90d"),
    "external_outflow_pct_30d": ("fracción", "#22 · A1 ÷ saldo (condición de alerta: > 5%)"),
    "net_external_flow_30d": (USD_SIGNED, "#23 · entradas − salidas externas, 30d"),
    "net_external_flow_90d": (USD_SIGNED, "#23 · entradas − salidas externas, 90d"),
    "net_external_flow_pct_90d": ("fracción", "#23 · ÷ saldo promedio (alerta ≤ −15%)"),
    "external_destination_concentration": ("fracción", "#24 · HHI por institución (no por ABA), 90d"),
    "external_outflow_pct_90d": ("fracción", "#24 · salidas 90d ÷ saldo (condición de alerta: > 10%)"),
    "outflow_vs_baseline_pct": ("fracción", "#25 · salidas último mes ÷ promedio mensual meses −7..−1 (piso $10k) − 1"),
}

# Paso 4 · Investments (variables 9, 26, 27, 28, 34 del Excel)
STEP4_COLUMNS: dict[str, tuple[str, str]] = {
    "household_id": ("id", "Identificador del hogar"),
    "investment_redemption_pct": ("fracción", "#9 · max(0, ventas y redenciones del cliente − compras) 90d ÷ AUM promedio (alerta > 20%)"),
    "fixed_income_maturity_not_reinvested": ("fracción", "#26 · principal vencido no reinvertido en 30d ÷ principal vencido; NULL sin vencimientos"),
    "fixed_income_not_reinvested_amount": (USD, "#26 · monto no reinvertido"),
    "cash_pct_of_portfolio_chg": ("fracción", "#27 · cash % en t − promedio meses −6..−1 (0.10 = 10 pp)"),
    "return_vs_benchmark": ("fracción", "#28 · TWR neto 12m − benchmark por perfil (−0.03 = −3 pp); NULL sin advisory"),
    "positions_liquidated_pct": ("fracción", "#34 · posiciones vendidas completas sin reemplazo 90d ÷ valor hace 90d (alerta > 15%)"),
}

# Paso 5 · Relationship & closures (variables 10, 29, 30, 31, 32 del Excel)
STEP5_COLUMNS: dict[str, tuple[str, str]] = {
    "household_id": ("id", "Identificador del hogar"),
    "products_closed_90d": ("entero", "#10 · productos distintos cerrados en 90d (sin CD renovado, préstamo a término, conversión, consolidación)"),
    "accounts_closed_90d": ("entero", "#29 · cuentas cerradas en 90d (sin consolidación interna ni CD renovado)"),
    "products_closed_180d": ("entero", "#10 · versión 180d (principal, D-20)"),
    "accounts_closed_180d": ("entero", "#29 · versión 180d"),
    "share_of_wallet": ("fracción", "#30 · (AUM + depósitos en Citizens) ÷ patrimonio total estimado, tope 1 (alerta < 30%)"),
    "wealth_estimate_source": ("categoría", "#30 · fuente de la estimación: declared / vendor / model"),
    "share_of_wallet_change": ("fracción", "#31 · SOW hoy − SOW hace 6 meses (−0.10 = −10 pp)"),
    "trustee_change_flag": ("0/1", "#32 · Citizens deja de ser trustee o entra uno externo en 12m; NULL sin trust"),
}

# Paso 6 · Banker (variables 11, 12, 13, 35 del Excel)
STEP6_COLUMNS: dict[str, tuple[str, str]] = {
    "household_id": ("id", "Identificador del hogar"),
    "banker_change_6m_flag": ("0/1", "#11 · cambió el banker principal en 6m (sin cobertura temporal < 30d)"),
    "banker_change_reason": ("categoría", "#11 · banker_departure / client_request / book_rebalancing"),
    "days_since_meaningful_contact": ("días", "#12 · días desde el último contacto significativo (365 = sin contacto en 12m)"),
    "contact_gap_ratio": ("ratio", "#12 · días sin contacto significativo ÷ cadencia acordada (UHNW 30d, HNW 90d) (alerta > 2)"),
    "client_reply_rate": ("fracción", "#13 · contactos del banker respondidos en ≤ 7d ÷ contactos, 90d; NULL si < 3"),
    "meetings_cancelled_by_client": ("entero", "#35 · reuniones canceladas por el cliente en 6m; NULL si el banker no registra el campo"),
    "meetings_cancelled_pct": ("fracción", "#35 · ÷ reuniones agendadas"),
}

# Paso 7 · Complaints & voice of client (variables 14, 15, 33, 36 del Excel)
STEP7_COLUMNS: dict[str, tuple[str, str]] = {
    "household_id": ("id", "Identificador del hogar"),
    "complaint_escalated_flag": ("0/1", "#14 · alguna queja escalada a gerencia / ombudsman / regulador / legal en 12m"),
    "open_complaint_flag": ("0/1", "#15 · tiene queja abierta (distingue 0 días de sin queja)"),
    "complaint_age_days": ("días", "#15 · días de la queja abierta más antigua; 0 si no hay (alerta > 30)"),
    "complaint_out_of_sla_flag": ("0/1", "#15 · alguna queja abierta fuera de SLA (override del deck)"),
    "repeat_complaint_flag": ("0/1", "#33 · ≥ 2 quejas de la misma categoría (nivel 2) en 12m o alguna reabierta"),
    "complaints_12m": ("entero", "nº de quejas en 12m (contexto)"),
    "relationship_dissatisfaction_flag": ("0/1", "#36 · insatisfacción detectada por el Assistant y confirmada por una persona (30d); NULL fuera del piloto"),
}

# Paso 8 · External & composite (variables 16, 37 del Excel)
STEP8_COLUMNS: dict[str, tuple[str, str]] = {
    "household_id": ("id", "Identificador del hogar"),
    "multi_signal_count": ("entero", "#16 · nº de grupos del Excel (0–7) con alguna variable sobre su umbral de alerta"),
    "multi_signal_flag": ("0/1", "#16 · ≥ 3 grupos en alerta"),
    "group_alert_balances": ("0/1", "#16 · alerta en Balances & AUM"),
    "group_alert_recurring": ("0/1", "#16 · alerta en Recurring deposits & flows"),
    "group_alert_transfers": ("0/1", "#16 · alerta en Transfers"),
    "group_alert_investments": ("0/1", "#16 · alerta en Investments"),
    "group_alert_relationship": ("0/1", "#16 · alerta en Relationship & closures"),
    "group_alert_banker": ("0/1", "#16 · alerta en Banker"),
    "group_alert_complaints": ("0/1", "#16 · alerta en Complaints & voice of client"),
    "bureau_new_mortgage_elsewhere": ("0/1", "#37 · hipoteca / HELOC nueva con otro acreedor en 6m; NULL sin propósito permisible o sin aprobación legal"),
}

# Columna principal de cada variable del Excel en la base final (id del Excel → columna).
EXCEL_PRIMARY: dict[int, tuple[str, str]] = {
    1: ("aum_outflow", "aum_outflow_pct_90d"), 2: ("deposit_balance_change_pct", "deposit_balance_change_pct_90d"),
    3: ("salary_deposit_stopped_flag", "salary_deposit_stopped_flag"),
    4: ("recurring_deposit_stopped_flag", "recurring_deposit_stopped_flag"),
    5: ("recurring_deposit_change_pct", "recurring_deposit_change_pct"), 6: ("net_deposit_flow", "net_deposit_flow_pct_90d"),
    7: ("external_transfer_pct_of_balance", "external_transfer_pct_of_balance_60d"),
    8: ("new_external_destinations", "new_external_destinations_90d"),
    9: ("investment_redemption_pct", "investment_redemption_pct"), 10: ("products_closed", "products_closed_180d"),
    11: ("banker_change_6m_flag", "banker_change_6m_flag"), 12: ("contact_gap_ratio", "contact_gap_ratio"),
    13: ("client_reply_rate", "client_reply_rate"), 14: ("complaint_escalated_flag", "complaint_escalated_flag"),
    15: ("complaint_age_days", "complaint_age_days"), 16: ("multi_signal_flag", "multi_signal_flag"),
    17: ("aum_vs_baseline_pct", "aum_vs_baseline_pct"), 18: ("deposit_balance_vs_6m_avg_pct", "deposit_balance_vs_6m_avg_pct"),
    19: ("pension_deposit_stopped_flag", "pension_deposit_stopped_flag"),
    20: ("business_payroll_stopped_flag", "business_payroll_stopped_flag"),
    21: ("transfer_to_competitor_bank_amount", "transfer_to_competitor_pct_90d"),
    22: ("external_transfer_acceleration", "external_transfer_acceleration"), 23: ("net_external_flow", "net_external_flow_pct_90d"),
    24: ("external_destination_concentration", "external_destination_concentration"),
    25: ("outflow_vs_baseline_pct", "outflow_vs_baseline_pct"),
    26: ("fixed_income_maturity_not_reinvested", "fixed_income_maturity_not_reinvested"),
    27: ("cash_pct_of_portfolio_chg", "cash_pct_of_portfolio_chg"), 28: ("return_vs_benchmark", "return_vs_benchmark"),
    29: ("accounts_closed", "accounts_closed_90d"), 30: ("share_of_wallet", "share_of_wallet"),
    31: ("share_of_wallet_change", "share_of_wallet_change"), 32: ("trustee_change_flag", "trustee_change_flag"),
    33: ("repeat_complaint_flag", "repeat_complaint_flag"), 34: ("positions_liquidated_pct", "positions_liquidated_pct"),
    35: ("meetings_cancelled_by_client", "meetings_cancelled_by_client"),
    36: ("relationship_dissatisfaction_flag", "relationship_dissatisfaction_flag"),
    37: ("bureau_new_mortgage_elsewhere", "bureau_new_mortgage_elsewhere"),
}
