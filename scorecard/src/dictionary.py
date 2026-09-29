"""Diccionario de datos del scorecard: una entrada por columna de la base (62).

Campos: rol, dimensión, ventana, unidad, tipo de feature, condición de missing estructural,
dirección esperada respecto al churn y elegibilidad como predictor.

Dirección esperada: "+" = a mayor valor, más churn; "−" = a mayor valor, menos churn;
"?" = sin hipótesis a priori (se deja a los datos, sin imponer signo).
Descripciones y unidades tomadas del diccionario del generador (synthetic/schema.py).
"""
from __future__ import annotations

import pandas as pd

# columna: (rol, dimensión, ventana, unidad, tipo_feature, missing_estructural, dirección, descripción)
D = {
    # ── Identificador / corte ───────────────────────────────────────────────────────────
    "household_id": ("identificador", "—", "—", "id", "—", "", "", "Identificador del hogar"),
    "snapshot_date": ("identificador", "—", "T0", "fecha", "—", "", "", "Fecha de corte (única: 2025-12-31)"),
    # ── Estructura ─────────────────────────────────────────────────────────────────────
    "segment": ("estructura", "estructura", "T0", "categoría", "nivel", "", "?", "HNW / UHNW (UHNW si relationship_value ≥ $30M)"),
    "has_investments": ("estructura", "estructura", "T0", "bool", "nivel", "", "−", "Tiene cuentas de inversión"),
    "has_advisory": ("estructura", "estructura", "T0", "bool", "nivel", "", "−", "Tiene cuentas advisory con benchmark"),
    "has_linked_business": ("estructura", "estructura", "T0", "bool", "nivel", "", "−", "Tiene un negocio vinculado"),
    "has_trust": ("estructura", "estructura", "T0", "bool", "nivel", "", "−", "Tiene trust"),
    "has_credit_anchor": ("estructura", "estructura", "T0", "bool", "nivel", "", "−", "Tiene hipoteca o línea de crédito con Citizens"),
    "has_payroll_stream": ("estructura", "estructura", "T0", "bool", "nivel", "", "−", "Recibe nómina en Citizens"),
    "has_pension_stream": ("estructura", "estructura", "T0", "bool", "nivel", "", "−", "Recibe pensión / Social Security en Citizens"),
    "has_dividend_stream": ("estructura", "estructura", "T0", "bool", "nivel", "", "−", "Recibe dividendos en Citizens"),
    "age_primary": ("estructura", "estructura", "T0", "años", "nivel", "", "?", "Edad del titular principal"),
    "tenure_years": ("estructura", "estructura", "T0", "años", "nivel", "", "−", "Antigüedad con el banco"),
    "history_months": ("estructura", "estructura", "T0", "meses", "nivel", "", "?", "Historia transaccional disponible, tope 24"),
    # ── Nivel patrimonial ──────────────────────────────────────────────────────────────
    "relationship_value": ("nivel patrimonial", "nivel patrimonial", "T0", "USD", "nivel", "", "?", "AUM + depósitos en Citizens"),
    "deposit_balance": ("nivel patrimonial", "nivel patrimonial", "T0", "USD", "nivel", "", "?", "Saldo en depósitos"),
    "aum": ("nivel patrimonial", "nivel patrimonial", "T0", "USD", "nivel", "has_investments", "?", "Valor de mercado de inversión, custodia y trust"),
    "recurring_income_monthly": ("nivel patrimonial", "nivel patrimonial", "T0", "USD/mes", "nivel", "", "?", "Ingreso recurrente mensual sin bono"),
    "share_of_wallet": ("nivel patrimonial", "nivel patrimonial", "T0", "fracción", "nivel", "", "−", "(AUM + depósitos) ÷ patrimonio total estimado, tope 1"),
    # ── Señales · salida de activos ────────────────────────────────────────────────────
    "aum_outflow_90d": ("señal", "salida de activos", "90d", "USD", "magnitud", "has_investments", "+", "max(0, retiros − aportes) de inversión"),
    "aum_outflow_pct_90d": ("señal", "salida de activos", "90d", "fracción", "magnitud", "has_investments", "+", "aum_outflow_90d ÷ AUM promedio"),
    "investment_redemption_pct": ("señal", "salida de activos", "90d", "fracción", "magnitud", "has_investments", "+", "Ventas y redenciones netas ÷ AUM promedio"),
    "positions_liquidated_pct": ("señal", "salida de activos", "90d", "fracción", "magnitud", "has_investments", "+", "Posiciones vendidas completas sin reemplazo ÷ valor hace 90d"),
    "aum_vs_baseline_pct": ("señal", "salida de activos", "baseline 6m", "fracción", "cambio vs baseline", "has_investments", "−", "AUM ex-mercado ÷ media meses −6..−1 − 1"),
    "cash_pct_of_portfolio_chg": ("señal", "salida de activos", "baseline 6m", "fracción (pp)", "cambio vs baseline", "has_investments", "+", "Cash % en T0 − promedio meses −6..−1"),
    "fixed_income_maturity_not_reinvested": ("señal", "salida de activos", "30d", "fracción", "magnitud", "operativa: sin vencimientos", "+", "Principal vencido no reinvertido ÷ principal vencido"),
    # ── Señales · deterioro de saldos ──────────────────────────────────────────────────
    "deposit_balance_change_pct_90d": ("señal", "deterioro de saldos", "90d", "fracción", "tendencia", "", "−", "Media 3m ÷ 3m previos − 1"),
    "deposit_balance_vs_6m_avg_pct": ("señal", "deterioro de saldos", "baseline 6m", "fracción", "cambio vs baseline", "", "−", "Depósitos último mes ÷ media meses −6..−1 − 1"),
    "net_deposit_flow_pct_90d": ("señal", "deterioro de saldos", "90d", "fracción", "magnitud", "", "−", "Entradas − salidas de depósitos ÷ saldo promedio"),
    # ── Señales · externalización / competencia ────────────────────────────────────────
    "external_transfer_pct_of_balance_60d": ("señal", "externalización/competencia", "60d", "fracción", "magnitud", "", "+", "Transferencias externas ÷ saldo promedio"),
    "new_external_destinations_90d": ("señal", "externalización/competencia", "90d", "conteo", "frecuencia", "", "+", "Destinos externos nuevos (≥ $50k, ausentes 12m previos)"),
    "transfer_to_competitor_bank_amount_90d": ("señal", "externalización/competencia", "90d", "USD", "magnitud", "", "+", "Enviado a bancos competidores"),
    "transfer_to_competitor_pct_90d": ("señal", "externalización/competencia", "90d", "fracción", "magnitud", "", "+", "Enviado a competidores ÷ saldo promedio"),
    "external_transfer_acceleration": ("señal", "externalización/competencia", "3×30d", "fracción", "aceleración", "", "+", "[(A1 − A2) − (A2 − A3)] ÷ saldo promedio 90d"),
    "net_external_flow_pct_90d": ("señal", "externalización/competencia", "90d", "fracción", "magnitud", "", "−", "Entradas − salidas externas ÷ saldo promedio"),
    "external_destination_concentration": ("señal", "externalización/competencia", "90d", "fracción (HHI)", "persistencia", "", "+", "HHI de destinos externos por institución"),
    "outflow_vs_baseline_pct": ("señal", "externalización/competencia", "baseline 6m", "fracción", "cambio vs baseline", "", "+", "Salidas último mes ÷ promedio meses −7..−1 − 1"),
    "bureau_new_mortgage_elsewhere": ("señal", "externalización/competencia", "6m", "0/1", "recencia", "operativa: sin propósito permisible (FCRA) / sin aprobación legal", "+", "Hipoteca / HELOC nueva con otro acreedor"),
    # ── Señales · ingresos recurrentes ─────────────────────────────────────────────────
    "salary_deposit_stopped_flag": ("señal", "ingresos recurrentes", "45d", "0/1", "recencia", "has_payroll_stream", "+", "Nómina detectada que dejó de llegar"),
    "pension_deposit_stopped_flag": ("señal", "ingresos recurrentes", "60d", "0/1", "recencia", "has_pension_stream", "+", "Pensión detectada que dejó de llegar"),
    "business_payroll_stopped_flag": ("señal", "ingresos recurrentes", "60d", "0/1", "recencia", "has_linked_business", "+", "La nómina del negocio no corrió"),
    "recurring_deposit_stopped_flag": ("señal", "ingresos recurrentes", "45–60d", "0/1", "recencia", "sin flujo recurrente (ningún has_*_stream ni negocio)", "+", "Algún flujo recurrente ≥ 10% del ingreso dejó de llegar"),
    "recurring_deposit_change_pct": ("señal", "ingresos recurrentes", "baseline 6m", "fracción", "cambio vs baseline", "sin flujo recurrente (ningún has_*_stream ni negocio)", "−", "Recurrente últimos 30d ÷ promedio mensual −7..−1 − 1"),
    # ── Señales · pérdida de productos ─────────────────────────────────────────────────
    "products_closed_180d": ("señal", "pérdida de productos", "180d", "conteo", "frecuencia", "", "+", "Productos distintos cerrados"),
    "accounts_closed_90d": ("señal", "pérdida de productos", "90d", "conteo", "frecuencia", "", "+", "Cuentas cerradas"),
    "share_of_wallet_change": ("señal", "pérdida de productos", "6m", "fracción (pp)", "tendencia", "", "−", "SOW hoy − SOW hace 6 meses"),
    "trustee_change_flag": ("señal", "pérdida de productos", "12m", "0/1", "recencia", "has_trust", "+", "Citizens deja de ser trustee o entra uno externo"),
    # ── Señales · fricción de servicio ─────────────────────────────────────────────────
    "complaint_escalated_flag": ("señal", "fricción de servicio", "12m", "0/1", "recencia", "", "+", "Queja escalada a gerencia / ombudsman / regulador / legal"),
    "complaint_age_days": ("señal", "fricción de servicio", "T0", "días", "persistencia", "", "+", "Días de la queja abierta más antigua (0 si no hay)"),
    "repeat_complaint_flag": ("señal", "fricción de servicio", "12m", "0/1", "persistencia", "", "+", "≥ 2 quejas misma categoría o alguna reabierta"),
    "relationship_dissatisfaction_flag": ("señal", "fricción de servicio", "30d", "0/1", "recencia", "operativa: fuera del piloto del Assistant", "+", "Insatisfacción detectada por el Assistant y confirmada"),
    # ── Señales · relación con banquero ────────────────────────────────────────────────
    "banker_change_6m_flag": ("señal", "relación con banquero", "6m", "0/1", "recencia", "", "+", "Cambió el banker principal"),
    "contact_gap_ratio": ("señal", "relación con banquero", "T0", "ratio", "recencia", "", "+", "Días sin contacto significativo ÷ cadencia acordada"),
    "client_reply_rate": ("señal", "relación con banquero", "90d", "fracción", "frecuencia", "operativa: < 3 contactos en 90d", "−", "Contactos respondidos en ≤ 7d ÷ contactos"),
    "meetings_cancelled_by_client": ("señal", "relación con banquero", "6m", "conteo", "frecuencia", "operativa: campo no registrado por el banker", "+", "Reuniones canceladas por el cliente"),
    # ── Señales · rendimiento ──────────────────────────────────────────────────────────
    "return_vs_benchmark": ("señal", "rendimiento", "12m", "fracción (pp)", "magnitud", "has_advisory", "−", "TWR neto 12m − benchmark por perfil"),
    # ── Compuestos (no predictores) ────────────────────────────────────────────────────
    "multi_signal_flag": ("compuesto", "compuesto", "mixta", "0/1", "—", "", "", "≥ 3 grupos en alerta (regla existente; benchmark)"),
    "multi_signal_count": ("compuesto", "compuesto", "mixta", "conteo", "—", "", "", "Nº de grupos (0–7) en alerta (regla existente; benchmark)"),
    # ── Outcomes (no predictores) ──────────────────────────────────────────────────────
    "churn_excluded": ("outcome", "outcome", "—", "bool", "—", "", "", "Excluido del target (muerte / reubicación)"),
    "hard_churn_6m": ("outcome", "outcome", "(T0, T0+6m]", "0/1", "—", "churn_excluded", "", "Salida total en 6m"),
    "soft_churn_3m": ("outcome", "outcome", "(T0, T0+3m]", "0/1", "—", "churn_excluded", "", "Contracción > 20% sin salida en 3m"),
    "value_lost_6m": ("outcome", "outcome", "(T0, T0+6m]", "USD", "—", "churn_excluded", "", "Valor perdido por churn"),
}

FIELDS = ["rol", "dimensión", "ventana", "unidad", "tipo_feature", "missing_estructural", "dirección_esperada", "descripción"]
NOT_ELIGIBLE_ROLES = {"identificador", "compuesto", "outcome"}
# Elegibles con revisión regulatoria pendiente (paso 10)
REVIEW = {
    "age_primary": "fair lending / edad como atributo protegido (ECOA si el score se usa en decisiones de crédito; UDAAP)",
    "bureau_new_mortgage_elsewhere": "FCRA: uso del buró requiere propósito permisible; el missing ya refleja hogares sin él",
}


def dictionary() -> pd.DataFrame:
    df = pd.DataFrame.from_dict(D, orient="index", columns=FIELDS).rename_axis("columna").reset_index()
    df["elegible"] = ~df["rol"].isin(NOT_ELIGIBLE_ROLES)
    df["revisión"] = df["columna"].map(REVIEW).fillna("")
    return df


def eligible() -> list[str]:
    d = dictionary()
    return d.loc[d["elegible"], "columna"].tolist()
