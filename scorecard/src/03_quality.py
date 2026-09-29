"""Paso 3 · Calidad de datos.

1. Perfil de cada variable numérica (missing, momentos, percentiles).
2. Missing explicado: estructural (has_*), historia corta (history_months < 24) u operativo.
3. Valores imposibles (rangos duros) y extremos plausibles (rangos blandos).
4. Consistencia lógica entre columnas.
5. Outliers de relationship_value: clasificados (error / real / extraordinario), sin eliminar ni recortar.

Instrucción del usuario (2026-09-29): base sintética → las inconsistencias se documentan y se sigue
con los datos tal cual; no se mueve la concentración de valor (sin capping de relationship_value).
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIGURES, QC, load_raw, save_table
from dictionary import dictionary

raw = load_raw()
dd = dictionary().set_index("columna")
qc = QC("03")
short = raw["history_months"] < 24

# ── 1. Perfil numérico ───────────────────────────────────────────────────────────────────
num_cols = [c for c in raw.columns if pd.api.types.is_numeric_dtype(raw[c]) and raw[c].dtype != bool]
q = [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
prof = pd.DataFrame({
    "variable": num_cols,
    "rol": [dd.loc[c, "rol"] for c in num_cols],
    "% missing": [raw[c].isna().mean() * 100 for c in num_cols],
    "media": [raw[c].mean() for c in num_cols],
    "desv": [raw[c].std() for c in num_cols],
    "mín": [raw[c].min() for c in num_cols],
    **{f"p{int(p * 100)}": [raw[c].quantile(p) for c in num_cols] for p in q},
    "máx": [raw[c].max() for c in num_cols],
})
save_table(prof.round(4), "03_numeric_profile")

# ── 2. Missing explicado ─────────────────────────────────────────────────────────────────
has_any_stream = raw[["has_payroll_stream", "has_pension_stream", "has_dividend_stream", "has_linked_business"]].any(axis=1)
COND = {  # condición "no aplica" (True = la variable no aplica al hogar)
    "has_investments": ~raw["has_investments"], "has_advisory": ~raw["has_advisory"],
    "has_payroll_stream": ~raw["has_payroll_stream"], "has_pension_stream": ~raw["has_pension_stream"],
    "has_linked_business": ~raw["has_linked_business"], "has_trust": ~raw["has_trust"],
    "sin flujo recurrente (ningún has_*_stream ni negocio)": ~has_any_stream,
}
# Causas secundarias documentadas en el diccionario del generador (NaN restante con historia = 24)
DETECTOR = "patrón no detectado por el algoritmo de recurrencia"
SECONDARY = {
    "salary_deposit_stopped_flag": DETECTOR, "pension_deposit_stopped_flag": DETECTOR,
    "business_payroll_stopped_flag": DETECTOR, "recurring_deposit_stopped_flag": DETECTOR,
    "recurring_deposit_change_pct": DETECTOR,
    "deposit_balance_change_pct_90d": "saldo base < $10k", "deposit_balance_vs_6m_avg_pct": "saldo base < $10k",
    "net_deposit_flow_pct_90d": "saldo base < $10k",
}
rows = []
for c in raw.columns:
    na = raw[c].isna()
    if na.sum() == 0 or dd.loc[c, "rol"] == "outcome":
        continue
    cond_name = dd.loc[c, "missing_estructural"]
    na_cond = COND.get(cond_name, pd.Series(False, index=raw.index))
    applies = ~na_cond
    n_struct = int((na & na_cond).sum())
    n_viol = int((~na & na_cond).sum())
    rest = na & applies
    n_rest_short, n_rest_long = int((rest & short).sum()), int((rest & ~short).sum())
    if cond_name.startswith("operativa"):
        cause = cond_name
    elif n_rest_long > 0 and c in SECONDARY:
        cause = ("estructural + " if n_struct else "") + ("historia corta + " if n_rest_short else "") + SECONDARY[c]
    elif n_rest_long == 0 and n_rest_short > 0 and n_struct > 0:
        cause = "estructural + historia corta"
    elif n_rest_long == 0 and n_rest_short > 0:
        cause = "historia corta (< 24 meses)"
    elif n_rest_long + n_rest_short == 0:
        cause = "estructural"
    else:
        cause = "estructural + no explicado" if n_struct else "no explicado"
    max_hist_na = raw.loc[rest, "history_months"].max() if rest.any() else np.nan
    rows.append({"variable": c, "% missing": round(na.mean() * 100, 2), "causa": cause,
                 "NaN estructural (no aplica)": n_struct, "valor donde no aplica": n_viol,
                 "NaN restante | historia<24": n_rest_short, "NaN restante | historia=24": n_rest_long,
                 "% missing restante no estructural": round(rest.mean() * 100, 2),
                 "máx history_months con NaN restante": max_hist_na})
miss = pd.DataFrame(rows).sort_values("% missing", ascending=False)
save_table(miss, "03_missing_explained")

print("Missing")
unexpl = miss[miss["causa"].str.contains("no explicado")]
qc.check("Missing no estructural explicado (historia corta u operativo)", unexpl.empty, "0 variables no explicadas",
         unexpl["variable"].tolist(), severity="warn")
over90 = miss[miss["% missing restante no estructural"] > 90]
qc.check("Ninguna variable con > 90% missing no estructural", over90.empty, "0", over90["variable"].tolist())
viol = miss[miss["valor donde no aplica"] > 0]
qc.check("Sin valores donde la variable no aplica", viol.empty, "0",
         ", ".join(f"{r.variable}={r._5}" for r in viol.itertuples()), severity="warn")

# ── 3. Rangos: imposibles (duros) y extremos plausibles (blandos) ─────────────────────────
FLAGS = [c for c in raw.columns if dd.loc[c, "unidad"] == "0/1" and dd.loc[c, "rol"] != "outcome"] + ["hard_churn_6m", "soft_churn_3m"]
COUNTS = ["new_external_destinations_90d", "products_closed_180d", "accounts_closed_90d", "meetings_cancelled_by_client",
          "multi_signal_count", "complaint_age_days", "history_months"]
HARD = {  # variable: (mín, máx) lógicamente posibles
    **{c: (0, 1) for c in ["share_of_wallet", "client_reply_rate", "positions_liquidated_pct",
                           "fixed_income_maturity_not_reinvested", "external_destination_concentration"]},
    **{c: (-1, np.inf) for c in ["deposit_balance_change_pct_90d", "deposit_balance_vs_6m_avg_pct", "aum_vs_baseline_pct",
                                 "recurring_deposit_change_pct", "outflow_vs_baseline_pct"]},
    **{c: (0, np.inf) for c in ["relationship_value", "deposit_balance", "aum", "recurring_income_monthly", "aum_outflow_90d",
                                "aum_outflow_pct_90d", "investment_redemption_pct", "external_transfer_pct_of_balance_60d",
                                "transfer_to_competitor_bank_amount_90d", "transfer_to_competitor_pct_90d", "contact_gap_ratio",
                                "value_lost_6m", "tenure_years"] + COUNTS},
    **{c: (-1, 1) for c in ["share_of_wallet_change", "cash_pct_of_portfolio_chg", "return_vs_benchmark"]},
    "age_primary": (18, 110), "history_months": (0, 24),
}
SOFT = {  # extremo plausible pero a revisar: (condición, descripción)
    "aum_outflow_pct_90d": (lambda s: s > 1, "salida 90d > 100% del AUM promedio"),
    "investment_redemption_pct": (lambda s: s > 1, "redención > 100% del AUM promedio"),
    "external_transfer_pct_of_balance_60d": (lambda s: s > 1, "transferencias 60d > 100% del saldo promedio"),
    "transfer_to_competitor_pct_90d": (lambda s: s > 1, "a competidores > 100% del saldo promedio"),
    "net_deposit_flow_pct_90d": (lambda s: s < -1, "salida neta > 100% del saldo promedio"),
    "net_external_flow_pct_90d": (lambda s: s < -1, "salida externa neta > 100% del saldo promedio"),
    "outflow_vs_baseline_pct": (lambda s: s > 10, "salidas > 11× la base"),
    "contact_gap_ratio": (lambda s: s > 6, "> 6 cadencias sin contacto"),
    "complaint_age_days": (lambda s: s > 180, "queja abierta > 180 días"),
    "age_primary": (lambda s: s < 30, "titular < 30 años"),
}
rr = []
for c, (lo, hi) in HARD.items():
    s = raw[c].dropna()
    n_bad = int(((s < lo) | (s > hi)).sum())
    rr.append({"variable": c, "regla": f"[{lo}, {hi}]", "tipo": "imposible", "n": n_bad, "% no nulos": 100 * n_bad / max(len(s), 1)})
for c in FLAGS:
    s = raw[c].dropna()
    n_bad = int((~s.isin([0, 1])).sum())
    rr.append({"variable": c, "regla": "{0, 1}", "tipo": "imposible", "n": n_bad, "% no nulos": 100 * n_bad / max(len(s), 1)})
for c in COUNTS:
    s = raw[c].dropna()
    n_bad = int((s != np.round(s)).sum())
    rr.append({"variable": c, "regla": "entero", "tipo": "imposible", "n": n_bad, "% no nulos": 100 * n_bad / max(len(s), 1)})
for c, (f, desc) in SOFT.items():
    s = raw[c].dropna()
    n = int(f(s).sum())
    rr.append({"variable": c, "regla": desc, "tipo": "extremo plausible", "n": n, "% no nulos": 100 * n / max(len(s), 1)})
neg0 = int((np.signbit(raw["contact_gap_ratio"].fillna(1)) & (raw["contact_gap_ratio"] == 0)).sum())
rr.append({"variable": "contact_gap_ratio", "regla": "cero con signo negativo (−0.0)", "tipo": "cosmético", "n": neg0,
           "% no nulos": 100 * neg0 / len(raw)})
ranges = pd.DataFrame(rr)
save_table(ranges.round(3), "03_range_checks")
print("\nRangos")
bad = ranges[(ranges.tipo == "imposible") & (ranges.n > 0)]
qc.check("Sin valores imposibles", bad.empty, "0 variables", ", ".join(f"{r.variable}={r.n}" for r in bad.itertuples()), severity="warn")

# ── 4. Consistencia lógica ───────────────────────────────────────────────────────────────
lg = []
def logic(name, mask, note=""):
    n = int(mask.sum())
    lg.append({"control": name, "n inconsistentes": n, "% hogares": 100 * n / len(raw), "nota": note})
    qc.check(name, n == 0, 0, n, severity="warn")

print("\nLógica")
logic("relationship_value = aum + deposit_balance (±$1)", (raw.relationship_value - raw.aum.fillna(0) - raw.deposit_balance).abs() > 1)
logic("segment = UHNW ⇔ relationship_value ≥ $30M", (raw.segment == "UHNW") != (raw.relationship_value >= 30e6))
logic("HNW: relationship_value ≥ $1M", raw.relationship_value < 1e6)
exp_hist = np.minimum(np.floor(raw.tenure_years * 12 + 1e-9), 24)
logic("history_months = min(24, ⌊tenure_years·12⌋)", exp_hist != raw.history_months,
      "diferencias de ±1 mes por redondeo de antigüedad; ver tabla")
logic("history_months ≤ tenure_years·12 + 1", raw.history_months > raw.tenure_years * 12 + 1)
logic("history_months = 0 (sin historia transaccional)", raw.history_months == 0, "hogares recién abiertos")
logic("tenure_years ≤ age_primary − 18", raw.tenure_years > raw.age_primary - 18)
sow_prev = raw.share_of_wallet - raw.share_of_wallet_change
logic("SOW hace 6m = SOW − cambio ∈ [0, 1]", ((sow_prev < -1e-4) | (sow_prev > 1 + 1e-4)) & sow_prev.notna())
logic("aum_outflow_90d > 0 ⇔ aum_outflow_pct_90d > 0", ((raw.aum_outflow_90d > 0) != (raw.aum_outflow_pct_90d > 0)) & raw.aum_outflow_90d.notna())
logic("transfer_to_competitor_amount > 0 ⇔ pct > 0",
      ((raw.transfer_to_competitor_bank_amount_90d > 0) != (raw.transfer_to_competitor_pct_90d > 0)) & raw.transfer_to_competitor_pct_90d.notna())
logic("salary_deposit_stopped_flag = 1 ⇒ recurring_deposit_stopped_flag = 1",
      (raw.salary_deposit_stopped_flag == 1) & (raw.recurring_deposit_stopped_flag == 0),
      "la nómina puede ser < 10% del ingreso recurrente (umbral de #4)")
logic("pension_deposit_stopped_flag con valor sin has_pension_stream", raw.pension_deposit_stopped_flag.notna() & ~raw.has_pension_stream,
      "siempre 0; patrón detectado sin flag de estructura (D0.4)")
logic("salary_deposit_stopped_flag NaN con has_payroll_stream", raw.salary_deposit_stopped_flag.isna() & raw.has_payroll_stream,
      "patrón de nómina no detectado por el algoritmo")
logic("value_lost_6m ≤ relationship_value", raw.value_lost_6m > raw.relationship_value * (1 + 1e-9))
logic("tenure_years = 0", raw.tenure_years == 0, "no hay; mínimo 0.01 años")
logic_t = pd.DataFrame(lg)
save_table(logic_t.round(3), "03_logic_checks")

hist_diff = (raw.history_months - exp_hist)
hist_tab = (pd.DataFrame({"diferencia history − ⌊tenure·12⌋": hist_diff[hist_diff != 0]})
            .value_counts().rename("hogares").reset_index())
save_table(hist_tab, "03_history_tenure_diff")

# ── 5. Outliers de relationship_value (no se eliminan ni se recortan) ────────────────────
rv = raw.relationship_value
lrv = np.log10(rv)
q1, q3 = lrv.quantile([0.25, 0.75])
fence = q3 + 3 * (q3 - q1)
err = ((rv - raw.aum.fillna(0) - raw.deposit_balance).abs() > 1) | ((raw.segment == "UHNW") != (rv >= 30e6)) | (rv <= 0)
extra = (lrv > fence) & ~err
cls = np.select([err, extra], ["error", "extraordinario"], "real")
out_tab = (pd.DataFrame({"clase": cls, "rv": rv, "hard": raw.hard_churn_6m})
           .groupby("clase").agg(hogares=("rv", "size"), rv_total_M=("rv", lambda s: s.sum() / 1e6),
                                 rv_mín_M=("rv", lambda s: s.min() / 1e6), rv_máx_M=("rv", lambda s: s.max() / 1e6),
                                 eventos_hard=("hard", "sum")).reset_index())
out_tab["% del RV total"] = 100 * out_tab["rv_total_M"] / (rv.sum() / 1e6)
out_tab["criterio"] = out_tab["clase"].map({
    "error": "rompe identidad RV = AUM + depósitos o regla de segmento",
    "extraordinario": f"log10(RV) > Q3 + 3·IQR (RV > ${10 ** fence / 1e6:,.0f}M); consistente",
    "real": "dentro de la cola esperada"})
save_table(out_tab.round(3), "03_value_outliers")
top = raw.nlargest(15, "relationship_value")[["household_id", "segment", "relationship_value", "deposit_balance", "aum",
                                              "tenure_years", "hard_churn_6m", "soft_churn_3m", "value_lost_6m"]]
save_table(top, "03_top15_households")
qc.check("relationship_value: 0 errores", int(err.sum()) == 0, 0, int(err.sum()), severity="warn")
print(f"  [INFO] Extraordinarios: {int(extra.sum())} hogares, {100 * rv[extra].sum() / rv.sum():.1f}% del RV; se conservan sin capping")

# Figura: distribución de log10(relationship_value) por segmento con umbrales
INK, MUTED, GRID, BLUE, ORANGE = "#0b0b0b", "#52514e", "#e6e5e0", "#2a78d6", "#eb6834"
fig, ax = plt.subplots(figsize=(9, 3.8))
bins = np.linspace(lrv.min(), lrv.max(), 80)
ax.hist(lrv[raw.segment == "HNW"], bins=bins, color=BLUE, label="HNW", edgecolor="white", linewidth=0.5)
ax.hist(lrv[raw.segment == "UHNW"], bins=bins, color=ORANGE, label="UHNW", edgecolor="white", linewidth=0.5)
for x, lab in [(np.log10(30e6), "$30M (UHNW)"), (fence, "extraordinario"), (np.log10(rv.quantile(0.99)), "p99")]:
    ax.axvline(x, color=MUTED, lw=1, ls="--")
    ax.text(x, ax.get_ylim()[1] * 0.95, f" {lab}", color=MUTED, fontsize=8, va="top")
ticks = [6, 7, 8, 9]
ax.set_xticks(ticks, ["$1M", "$10M", "$100M", "$1B"], color=MUTED)
ax.set_ylabel("hogares", color=MUTED)
ax.set_title("Distribución de relationship_value (escala log) [DATA-SINT]", loc="left", color=INK, fontsize=11)
ax.legend(frameon=False, labelcolor=INK)
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_axisbelow(True)
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.tick_params(colors=MUTED, length=0)
fig.tight_layout()
fig.savefig(FIGURES / "03_relationship_value.png", dpi=150)

print("\n" + miss[["variable", "% missing", "causa", "valor donde no aplica", "NaN restante | historia=24"]].to_string(index=False))
print("\n" + ranges[ranges.n > 0].round(2).to_string(index=False))
print("\n" + logic_t.round(2).to_string(index=False))
print("\n" + out_tab.round(1).to_string(index=False))
qc.gate()
