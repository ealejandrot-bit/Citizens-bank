"""Paso 5 · Auditoría de features y derivadas.

1. Mapa de cada señal a su tipo (nivel / frecuencia / recencia / magnitud / tendencia / aceleración /
   persistencia / cambio vs baseline) por dimensión → huecos.
2. Derivadas permitidas:
   - Razón de missing por variable: "ok" / "no_aplica" (estructural, has_*) / "sin_dato" (historia corta,
     operativa, patrón no detectado, saldo base < $10k). Se usa como bin propio en el paso 9.
   - Recodificación D3.3: pension_deposit_stopped_flag → NaN "no_aplica" si has_pension_stream = False.
   - aum_outflow_to_rv_90d = aum_outflow_90d ÷ relationship_value; 0 si has_investments = False (no hay AUM que
     sacar), NaN "sin_dato" si hay inversiones pero falta el dato.
   - log_relationship_value = log10(relationship_value) (solo legibilidad; el WoE es invariante a monotonía).
   - Conteo propio de señales activas (umbrales del Excel) SOLO para comparar con multi_signal_count; no predictor.
3. Guarda la matriz de features (outputs/data/05_features.pkl) con predictores elegibles + razones de missing.
Prohibidos como predictor: outcomes, compuestos, snapshot_date, household_id.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from common import FORBIDDEN, OUT, QC, load_raw, save_table
from dictionary import dictionary

raw = load_raw()
dd = dictionary()
ddi = dd.set_index("columna")
qc = QC("05")
DATA_OUT = OUT / "data"
DATA_OUT.mkdir(parents=True, exist_ok=True)

# ── 1. Mapa de tipos por dimensión y huecos ──────────────────────────────────────────────
TYPES = ["nivel", "frecuencia", "recencia", "magnitud", "tendencia", "aceleración", "persistencia", "cambio vs baseline"]
sig = dd[dd.rol == "señal"]
cov = (sig.assign(n=1).pivot_table(index="dimensión", columns="tipo_feature", values="n", aggfunc="sum", fill_value=0)
       .reindex(columns=TYPES, fill_value=0))
cov["total"] = cov.sum(axis=1)
cov["huecos"] = cov[TYPES].apply(lambda r: ", ".join(t for t in TYPES if r[t] == 0 and t != "nivel"), axis=1)
save_table(cov.reset_index(), "05_feature_type_map")
feat_map = sig[["columna", "dimensión", "tipo_feature", "ventana", "dirección_esperada"]]
save_table(feat_map, "05_feature_map")

# ── 2. Derivadas ────────────────────────────────────────────────────────────────────────
f = raw.copy()
# D3.3: pensión con valor donde no aplica → NaN (no aplica)
n_recode = int((f.pension_deposit_stopped_flag.notna() & ~f.has_pension_stream).sum())
f.loc[~f.has_pension_stream, "pension_deposit_stopped_flag"] = np.nan

has_any_stream = f[["has_payroll_stream", "has_pension_stream", "has_dividend_stream", "has_linked_business"]].any(axis=1)
NA_COND = {  # variable estructural → máscara "no aplica"
    "has_investments": ~f.has_investments, "has_advisory": ~f.has_advisory, "has_payroll_stream": ~f.has_payroll_stream,
    "has_pension_stream": ~f.has_pension_stream, "has_linked_business": ~f.has_linked_business, "has_trust": ~f.has_trust,
    "sin flujo recurrente (ningún has_*_stream ni negocio)": ~has_any_stream,
}

# Derivada: salida de AUM relativa a la relación completa
f["aum_outflow_to_rv_90d"] = f.aum_outflow_90d / f.relationship_value
f.loc[~f.has_investments, "aum_outflow_to_rv_90d"] = 0.0
f["log_relationship_value"] = np.log10(f.relationship_value)

predictors = [c for c in dd.loc[dd.elegible, "columna"]] + ["aum_outflow_to_rv_90d", "log_relationship_value"]
DERIVED_META = {
    "aum_outflow_to_rv_90d": ("señal", "salida de activos", "90d", "fracción", "magnitud", "", "+",
                              "aum_outflow_90d ÷ relationship_value; 0 sin inversiones"),
    "log_relationship_value": ("nivel patrimonial", "nivel patrimonial", "T0", "log10 USD", "nivel", "", "?",
                               "log10(relationship_value)"),
}

miss_reason = pd.DataFrame(index=f.index)
rows = []
for c in predictors:
    na = f[c].isna()
    if not na.any():
        continue
    cond = ddi.loc[c, "missing_estructural"] if c in ddi.index else ""
    reason = pd.Series("ok", index=f.index)
    na_mask = NA_COND.get(cond, pd.Series(False, index=f.index))
    reason[na & na_mask] = "no_aplica"
    reason[na & ~na_mask] = "sin_dato"
    miss_reason[f"{c}__miss"] = reason
    rows.append({"variable": c, "no_aplica": int((reason == "no_aplica").sum()), "sin_dato": int((reason == "sin_dato").sum()),
                 "condición no aplica": cond if na_mask.any() else "—",
                 "tasa hard | ok %": 100 * f.loc[reason == "ok", "hard_churn_6m"].mean(),
                 "tasa hard | no_aplica %": 100 * f.loc[reason == "no_aplica", "hard_churn_6m"].mean() if (reason == "no_aplica").any() else np.nan,
                 "tasa hard | sin_dato %": 100 * f.loc[reason == "sin_dato", "hard_churn_6m"].mean() if (reason == "sin_dato").any() else np.nan})
mr = pd.DataFrame(rows)
save_table(mr.round(3), "05_missing_reasons")

# ── Conteo propio de señales activas (comparación con multi_signal_count; NO predictor) ─────
# Umbrales de la columna "Alert threshold" del Excel de 37 variables, con las columnas disponibles en la base.
ALERTS = {
    "Balances & AUM": [f.aum_outflow_pct_90d > 0.10, f.deposit_balance_change_pct_90d <= -0.25,
                       f.aum_vs_baseline_pct <= -0.20, f.deposit_balance_vs_6m_avg_pct <= -0.30],
    "Recurring": [f.salary_deposit_stopped_flag == 1, f.recurring_deposit_stopped_flag == 1, f.recurring_deposit_change_pct <= -0.40,
                  f.net_deposit_flow_pct_90d <= -0.15, f.pension_deposit_stopped_flag == 1, f.business_payroll_stopped_flag == 1],
    "Transfers": [f.external_transfer_pct_of_balance_60d > 0.15, f.new_external_destinations_90d >= 1,
                  f.transfer_to_competitor_pct_90d > 0.10, f.net_external_flow_pct_90d <= -0.15, f.outflow_vs_baseline_pct > 1.0],
    "Investments": [f.investment_redemption_pct > 0.20, f.fixed_income_maturity_not_reinvested > 0.50,
                    f.cash_pct_of_portfolio_chg > 0.10, f.return_vs_benchmark <= -0.03, f.positions_liquidated_pct > 0.15],
    "Relationship": [f.products_closed_180d >= 1, f.accounts_closed_90d >= 1, f.share_of_wallet < 0.30,
                     f.share_of_wallet_change <= -0.10, f.trustee_change_flag == 1],
    "Banker": [f.banker_change_6m_flag == 1, f.contact_gap_ratio > 2.0, f.client_reply_rate < 0.5, f.meetings_cancelled_by_client >= 2],
    "Complaints": [f.complaint_escalated_flag == 1, f.complaint_age_days > 30, f.repeat_complaint_flag == 1,
                   f.relationship_dissatisfaction_flag == 1],
}
sig_active = pd.concat({g: pd.concat([c.fillna(False).astype(bool) for c in conds], axis=1).sum(axis=1) for g, conds in ALERTS.items()}, axis=1)
own_signals = sig_active.sum(axis=1)
own_groups = (sig_active > 0).sum(axis=1)
elig = ~f.churn_excluded.astype(bool)
rho_s = spearmanr(own_signals, f.multi_signal_count).statistic
rho_g = spearmanr(own_groups, f.multi_signal_count).statistic
agree = (own_groups == f.multi_signal_count).mean()
comp = pd.DataFrame([
    {"medida": "multi_signal_count (base)", "media": f.multi_signal_count.mean(), "ρ Spearman vs base": 1.0, "% coincidencia exacta": 100.0,
     "tasa hard si ≥ 3 %": 100 * f.loc[elig & (f.multi_signal_count >= 3), "hard_churn_6m"].mean()},
    {"medida": "grupos activos propios (0–7)", "media": own_groups.mean(), "ρ Spearman vs base": rho_g, "% coincidencia exacta": 100 * agree,
     "tasa hard si ≥ 3 %": 100 * f.loc[elig & (own_groups >= 3), "hard_churn_6m"].mean()},
    {"medida": "señales activas propias (0–33)", "media": own_signals.mean(), "ρ Spearman vs base": rho_s, "% coincidencia exacta": np.nan,
     "tasa hard si ≥ 3 %": 100 * f.loc[elig & (own_signals >= 3), "hard_churn_6m"].mean()},
])
save_table(comp.round(3), "05_signal_count_comparison")

# ── 3. Matriz de features ───────────────────────────────────────────────────────────────
X = f[["household_id", "churn_excluded", "hard_churn_6m", "soft_churn_3m", "value_lost_6m", "multi_signal_flag", "multi_signal_count"]].copy()
for c in predictors:
    s = f[c]
    X[c] = (s == "UHNW").astype(int) if c == "segment" else (s.astype(int) if s.dtype == bool else s)
X = pd.concat([X, miss_reason], axis=1)
X["own_signal_count"] = own_signals   # solo comparación / diagnóstico
X.to_pickle(DATA_OUT / "05_features.pkl")
meta = pd.concat([dd[dd.columna.isin(predictors)],
                  pd.DataFrame([(k, *v, True, "") for k, v in DERIVED_META.items()], columns=dd.columns)], ignore_index=True)
meta.to_csv(DATA_OUT / "05_predictor_meta.csv", index=False)

# ── QC ──────────────────────────────────────────────────────────────────────────────────
print("QC")
qc.check("Ningún predictor prohibido", not set(predictors) & set(FORBIDDEN), "∅", sorted(set(predictors) & set(FORBIDDEN)))
qc.check("Ningún predictor es compuesto o contiene 'churn'/'value_lost'", not any(k in c for c in predictors for k in ("churn", "value_lost", "multi_signal")),
         "∅", [c for c in predictors if any(k in c for k in ("churn", "value_lost", "multi_signal"))])
qc.check("Recodificación pensión (D3.3)", n_recode == 134, 134, n_recode)
qc.check("Pensión: sin valores donde no aplica tras recodificar", int((f.pension_deposit_stopped_flag.notna() & ~f.has_pension_stream).sum()) == 0, 0,
         int((f.pension_deposit_stopped_flag.notna() & ~f.has_pension_stream).sum()))
qc.check("aum_outflow_to_rv_90d definido sin inversiones", bool((f.loc[~f.has_investments, "aum_outflow_to_rv_90d"] == 0).all()), "100% = 0",
         f"{(f.loc[~f.has_investments, 'aum_outflow_to_rv_90d'] == 0).mean():.0%}")
# El denominador es RV en T0, ya neto de la salida: la razón puede superar 1 (D5.2). Solo se exige ≥ 0.
qc.check("aum_outflow_to_rv_90d ≥ 0", bool((f.aum_outflow_to_rv_90d.dropna() >= 0).all()), "≥ 0",
         f"[{f.aum_outflow_to_rv_90d.min():.4f}, {f.aum_outflow_to_rv_90d.max():.4f}]")
gt1 = f.aum_outflow_to_rv_90d > 1
qc.check("aum_outflow_to_rv_90d > 1 (salida 90d mayor que la relación que queda)", False, "informativo",
         f"{int(gt1.sum())} hogares, tasa hard {f.loc[gt1 & elig, 'hard_churn_6m'].mean():.1%}", severity="warn")
qc.check("Toda variable con NaN tiene razón de missing", all(f"{c}__miss" in X for c in predictors if f[c].isna().any()), "100%", "ok")
qc.check("Filas de la matriz = base", len(X) == len(raw), len(raw), len(X))
qc.check("Conteo propio vs multi_signal_count (ρ ≥ 0.8)", rho_g >= 0.8, "ρ ≥ 0.8", f"ρ = {rho_g:.3f}, coincidencia {agree:.1%}", severity="warn")
print(f"\nPredictores candidatos: {len(predictors)} (54 elegibles + 2 derivadas) · razones de missing: {miss_reason.shape[1]}")
print("\n" + cov.to_string())
print("\n" + mr.round(2).to_string(index=False))
print("\n" + comp.round(3).to_string(index=False))
qc.gate()
