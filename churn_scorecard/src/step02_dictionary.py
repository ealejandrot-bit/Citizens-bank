"""Paso 2 · Diccionario de datos: una fila por columna (62).

Bloques (SPEC): transaccional · patrimonial · relación · producto · servicio · digital · vida · economía · compuesto ·
estructural · resultado. Dimensiones ausentes en el archivo: digital (sin logins / sesiones) y vida (sin eventos de vida).
Dirección esperada: "+" mayor valor ⟹ más churn; "−" mayor valor ⟹ menos churn; "?" sin hipótesis a priori (a confirmar
por el usuario en G1). Uso: predictor · prohibido · auxiliar (compuestos: solo challenger / análisis [DEF-default I-3];
value_lost_6m: solo churn por valor y calibración [DEF-default I-10]).
"""
from __future__ import annotations

import pandas as pd

from common import REPORTS, STRUCTURAL, eligible, load_raw, md_table, save_table

df = load_raw()
d = df[eligible(df)]
TRIG = {c: t for t, cs in STRUCTURAL.items() for c in cs}

# columna: (unidad, significado de negocio, bloque, dirección, uso)
M = {
    "household_id": ("id", "identificador del hogar", "estructural", "", "prohibido"),
    "snapshot_date": ("fecha", "fecha de corte T0 (única)", "estructural", "", "prohibido"),
    "segment": ("categoría", "HNW / UHNW (UHNW si RV ≥ $30M)", "estructural", "?", "predictor"),
    "relationship_value": ("USD", "valor de la relación con el banco (= AUM + depósitos, G0-a)", "patrimonial", "?", "predictor"),
    "deposit_balance": ("USD", "saldo en depósitos", "patrimonial", "?", "predictor"),
    "aum": ("USD", "activos bajo gestión (inversión, custodia, trust)", "patrimonial", "?", "predictor"),
    "has_investments": ("bool", "tiene cuentas de inversión", "producto", "−", "predictor"),
    "has_advisory": ("bool", "tiene advisory con benchmark", "producto", "−", "predictor"),
    "has_linked_business": ("bool", "tiene negocio vinculado", "producto", "−", "predictor"),
    "has_trust": ("bool", "tiene trust", "producto", "−", "predictor"),
    "has_credit_anchor": ("bool", "tiene hipoteca / línea con el banco", "producto", "−", "predictor"),
    "has_payroll_stream": ("bool", "recibe nómina en el banco", "producto", "−", "predictor"),
    "has_pension_stream": ("bool", "recibe pensión en el banco", "producto", "−", "predictor"),
    "has_dividend_stream": ("bool", "recibe dividendos en el banco", "producto", "−", "predictor"),
    "age_primary": ("años", "edad del titular (revisión de fair lending si se usa)", "estructural", "?", "predictor"),
    "tenure_years": ("años", "antigüedad con el banco", "relación", "−", "predictor"),
    "history_months": ("meses", "historia transaccional disponible (tope 24)", "estructural", "?", "predictor"),
    "recurring_income_monthly": ("USD/mes", "ingreso recurrente mensual", "patrimonial", "?", "predictor"),
    "aum_outflow_pct_90d": ("fracción", "salida neta de AUM 90d ÷ AUM promedio", "transaccional", "+", "predictor"),
    "deposit_balance_change_pct_90d": ("fracción", "cambio de depósitos 3m vs 3m previos", "transaccional", "−", "predictor"),
    "salary_deposit_stopped_flag": ("0/1", "la nómina dejó de llegar", "transaccional", "+", "predictor"),
    "recurring_deposit_stopped_flag": ("0/1", "algún flujo recurrente relevante dejó de llegar", "transaccional", "+", "predictor"),
    "recurring_deposit_change_pct": ("fracción", "cambio del ingreso recurrente vs su promedio", "transaccional", "−", "predictor"),
    "net_deposit_flow_pct_90d": ("fracción", "flujo neto de depósitos 90d ÷ saldo promedio", "transaccional", "−", "predictor"),
    "external_transfer_pct_of_balance_60d": ("fracción", "transferencias externas 60d ÷ saldo promedio", "transaccional", "+", "predictor"),
    "new_external_destinations_90d": ("conteo", "destinos externos nuevos 90d", "transaccional", "+", "predictor"),
    "investment_redemption_pct": ("fracción", "redenciones netas 90d ÷ AUM promedio", "transaccional", "+", "predictor"),
    "products_closed_180d": ("conteo", "productos cerrados 180d", "producto", "+", "predictor"),
    "banker_change_6m_flag": ("0/1", "cambió el banquero principal 6m", "relación", "+", "predictor"),
    "contact_gap_ratio": ("ratio", "días sin contacto ÷ cadencia acordada", "relación", "+", "predictor"),
    "client_reply_rate": ("fracción", "contactos respondidos ≤ 7d ÷ contactos 90d (NaN si < 3 contactos)", "relación", "−", "predictor"),
    "complaint_escalated_flag": ("0/1", "queja escalada 12m", "servicio", "+", "predictor"),
    "complaint_age_days": ("días", "antigüedad de la queja abierta más vieja", "servicio", "+", "predictor"),
    "multi_signal_flag": ("0/1", "compuesto del proveedor: ≥ 3 grupos en alerta", "compuesto", "+", "auxiliar"),
    "aum_vs_baseline_pct": ("fracción", "AUM ex-mercado vs media 6m", "patrimonial", "−", "predictor"),
    "deposit_balance_vs_6m_avg_pct": ("fracción", "depósitos del último mes vs media 6m", "transaccional", "−", "predictor"),
    "pension_deposit_stopped_flag": ("0/1", "la pensión dejó de llegar", "transaccional", "+", "predictor"),
    "business_payroll_stopped_flag": ("0/1", "la nómina del negocio no corrió", "transaccional", "+", "predictor"),
    "transfer_to_competitor_pct_90d": ("fracción", "enviado a bancos competidores 90d ÷ saldo promedio", "transaccional", "+", "predictor"),
    "external_transfer_acceleration": ("fracción", "aceleración de transferencias externas (3 × 30d)", "transaccional", "+", "predictor"),
    "net_external_flow_pct_90d": ("fracción", "flujo externo neto 90d ÷ saldo promedio", "transaccional", "−", "predictor"),
    "external_destination_concentration": ("fracción (HHI)", "concentración de destinos externos", "transaccional", "+", "predictor"),
    "outflow_vs_baseline_pct": ("fracción", "salidas del último mes vs promedio 6m", "transaccional", "+", "predictor"),
    "fixed_income_maturity_not_reinvested": ("fracción", "principal vencido no reinvertido ÷ vencido", "transaccional", "+", "predictor"),
    "cash_pct_of_portfolio_chg": ("fracción (pp)", "cambio del % en cash del portafolio vs 6m", "transaccional", "+", "predictor"),
    "return_vs_benchmark": ("fracción (pp)", "rendimiento 12m − benchmark", "economía", "−", "predictor"),
    "accounts_closed_90d": ("conteo", "cuentas cerradas 90d", "producto", "+", "predictor"),
    "share_of_wallet": ("fracción", "RV ÷ patrimonio total estimado (denominador sin definir, I-5)", "patrimonial", "−", "predictor"),
    "share_of_wallet_change": ("fracción (pp)", "cambio de SOW 6m", "patrimonial", "−", "predictor"),
    "trustee_change_flag": ("0/1", "cambio de trustee 12m", "producto", "+", "predictor"),
    "repeat_complaint_flag": ("0/1", "queja repetida o reabierta 12m", "servicio", "+", "predictor"),
    "positions_liquidated_pct": ("fracción", "posiciones vendidas sin reemplazo 90d", "transaccional", "+", "predictor"),
    "meetings_cancelled_by_client": ("conteo", "reuniones canceladas por el cliente 6m", "relación", "+", "predictor"),
    "relationship_dissatisfaction_flag": ("0/1", "insatisfacción detectada y confirmada (piloto)", "servicio", "+", "predictor"),
    "bureau_new_mortgage_elsewhere": ("0/1", "hipoteca / HELOC nueva con otro acreedor 6m (buró)", "producto", "+", "predictor"),
    "multi_signal_count": ("conteo", "compuesto del proveedor: grupos en alerta (0–7)", "compuesto", "+", "auxiliar"),
    "aum_outflow_90d": ("USD", "salida neta de AUM 90d", "transaccional", "+", "predictor"),
    "transfer_to_competitor_bank_amount_90d": ("USD", "monto enviado a competidores 90d", "transaccional", "+", "predictor"),
    "churn_excluded": ("bool", "excluido del target (motivo desconocido, I-4)", "resultado", "", "prohibido"),
    "hard_churn_6m": ("0/1", "salida total en 6m", "resultado", "", "prohibido"),
    "soft_churn_3m": ("0/1", "contracción > 20% en 3m sin salida", "resultado", "", "prohibido"),
    "value_lost_6m": ("USD", "valor perdido en 6m (post-T0)", "resultado", "", "auxiliar (solo churn por valor y calibración; nunca predictor)"),
}
rows = []
for c in df.columns:
    u, sig, blk, dirn, uso = M[c]
    s = df[c]
    num = pd.api.types.is_numeric_dtype(s) and s.dtype != bool
    rows.append({"columna": c, "tipo": str(s.dtype), "unidad": u, "% missing [DATA]": round(100 * s.isna().mean(), 2),
                 "% missing elegibles [DATA]": round(100 * d[c].isna().mean(), 2),
                 "missing estructural": "sí" if c in TRIG else "no", "gatillo": TRIG.get(c, ""),
                 "rango [DATA]": f"{s.min():.4g} – {s.max():.4g}" if num else f"{s.nunique()} valores",
                 "significado de negocio": sig, "bloque": blk, "dirección esperada": dirn, "uso": uso})
dic = pd.DataFrame(rows)
save_table(dic, "step02_dictionary")
blk = dic.groupby("bloque").agg(columnas=("columna", "size"), predictores=("uso", lambda s: (s == "predictor").sum())).reset_index()
absent = pd.DataFrame([{"bloque": "digital", "columnas": 0, "predictores": 0}, {"bloque": "vida", "columnas": 0, "predictores": 0}])
blk = pd.concat([blk, absent], ignore_index=True)
save_table(blk, "step02_blocks")
signs = dic[dic.uso == "predictor"][["columna", "bloque", "dirección esperada"]]
save_table(signs, "step02_signs_a_priori")

rep = f"""# Paso 2 · Diccionario de datos

## Objetivo
- Clasificar las 62 columnas (tipo, unidad, missing, bloque, dirección esperada, uso) antes de mirar su relación con el target.

## Método
- Metadatos de negocio fijados a priori en `src/step02_dictionary.py`; % missing, rango y gatillo estructural calculados del archivo.
- Uso: predictor · prohibido (resultados, id, fecha) · auxiliar (compuestos [DEF-default I-3]; `value_lost_6m` [DEF-default I-10]).

## Código
- `src/step02_dictionary.py` · `tests/test_step02.py` · `outputs/tables/step02_dictionary.csv` (tabla completa).

## Resultados

### Columnas por bloque [DATA]
{md_table(blk)}

- Verificación: {int(blk.columnas.sum())} columnas = 62 [DATA].
- Dimensiones ausentes: **digital** (sin logins ni sesiones) y **vida** (sin eventos de vida; `salary_…` /
  `pension_deposit_stopped_flag` son proxies transaccionales, no eventos) → limitación L6.

### Uso [DATA]
{md_table(dic.uso.value_counts().rename_axis('uso').reset_index(name='columnas'))}

### Dirección esperada de los predictores (a confirmar en G1)
{md_table(signs.groupby(['bloque', 'dirección esperada']).size().rename('predictores').reset_index())}

- Sin hipótesis ("?"): `segment`, `relationship_value`, `deposit_balance`, `aum`, `age_primary`, `history_months`,
  `recurring_income_monthly`. En GBM quedan sin restricción monótona salvo que el usuario fije el signo en G1.
- `age_primary` es predictor candidato con revisión de fair lending; `bureau_new_mortgage_elsewhere` con revisión FCRA
  (propósito permisible): se decide en el paso 10.

## Tests
- `tests/test_step02.py` (ver pytest).

## Decisiones y preguntas abiertas
- D2.1–D2.2 en `reports/decision_log.md`; confirmación de signos en G1.
"""
(REPORTS / "step02.md").write_text(rep, encoding="utf-8")
print(blk.to_string(index=False)); print(dic.uso.value_counts())
