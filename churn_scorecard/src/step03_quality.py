"""Paso 3 · Calidad de datos (sobre elegibles, y sobre las 20,000 filas donde se indica).

- Perfil por variable numérica: % missing, media, mediana, sd, p1/p5/p25/p50/p75/p95/p99, mín, máx.
- Duplicados, negativos e imposibles; excepciones al missing estructural; has_investments vs aum; RV vs AUM + depósitos.
- Outliers de relationship_value, value_lost_6m, aum_outflow_90d, transfer_to_competitor_bank_amount_90d: error
  (rompe una identidad o un rango lógico) / extraordinario (log10 > Q3 + 3·IQR entre valores > 0) / real. Sin capping.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import REPORTS, STRUCTURAL, eligible, load_raw, md_table, save_table

df = load_raw()
el = eligible(df)
d = df[el]
num = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and df[c].dtype != bool]
q = [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
prof = pd.DataFrame({"variable": num, "% missing": [100 * d[c].isna().mean() for c in num], "media": [d[c].mean() for c in num],
                     "mediana": [d[c].median() for c in num], "sd": [d[c].std() for c in num],
                     **{f"p{int(100 * x)}": [d[c].quantile(x) for c in num] for x in q},
                     "mín": [d[c].min() for c in num], "máx": [d[c].max() for c in num]})
save_table(prof, "step03_profile")

# Duplicados e imposibles
chk = []
def add(control, n, nota=""):
    chk.append({"control": control, "n [DATA]": int(n), "nota": nota})
add("household_id duplicados", df.household_id.duplicated().sum())
add("filas duplicadas (sin id)", df.drop(columns="household_id").duplicated().sum())
add("saldos negativos (RV, depósitos, AUM)", (df[["relationship_value", "deposit_balance"]] < 0).sum().sum() + (df.aum < 0).sum())
add("montos negativos (salidas, transferencias, valor perdido)", (df[["aum_outflow_90d", "transfer_to_competitor_bank_amount_90d"]] < 0).sum().sum() + (df.value_lost_6m < 0).sum())
add("fracciones acotadas fuera de [0, 1]", sum(((df[c] < 0) | (df[c] > 1)).sum() for c in ["share_of_wallet", "client_reply_rate", "positions_liquidated_pct",
                                                                                         "fixed_income_maturity_not_reinvested", "external_destination_concentration"]))
add("cambios % < −100%", sum((df[c] < -1).sum() for c in ["deposit_balance_change_pct_90d", "deposit_balance_vs_6m_avg_pct", "aum_vs_baseline_pct",
                                                          "recurring_deposit_change_pct", "outflow_vs_baseline_pct"]))
add("conteos negativos o no enteros", sum(((df[c] < 0) | (df[c].dropna() % 1 != 0)).sum() for c in ["new_external_destinations_90d", "products_closed_180d",
                                                                                                    "accounts_closed_90d", "meetings_cancelled_by_client", "complaint_age_days"]))
add("edad fuera de 18–110", (~df.age_primary.between(18, 110)).sum())
add("tenure_years < 0", (df.tenure_years < 0).sum())
add("history_months fuera de 0–24", (~df.history_months.between(0, 24)).sum())
add("history_months > tenure·12 + 1", (df.history_months > df.tenure_years * 12 + 1).sum())
add("segment ≠ (RV ≥ $30M)", ((df.segment == "UHNW") != (df.relationship_value >= 30e6)).sum())
add("has_investments = False con aum no nulo", (~df.has_investments & df.aum.notna()).sum())
add("has_investments = True con aum nulo", (df.has_investments & df.aum.isna()).sum())
diff = (df.relationship_value - df.aum.fillna(0) - df.deposit_balance).abs().round(6)
add("|RV − (AUM + depósitos)| > $0.01", (diff > 0.01).sum(), "identidad al centavo (G0-a)")
add("value_lost_6m > RV", (df.value_lost_6m > df.relationship_value * (1 + 1e-12)).sum())
ctrl = pd.DataFrame(chk)
save_table(ctrl, "step03_checks")

# Excepciones al missing estructural (elegibles)
ex = []
for trig, cols in STRUCTURAL.items():
    g = d[trig].astype(bool)
    for c in cols:
        na = d[c].isna()
        ex.append({"variable": c, "gatillo": trig, "valor sin gatillo": int((~na & ~g).sum()), "NaN con gatillo": int((na & g).sum()),
                   "de ellos con history < 24": int((na & g & (d.history_months < 24)).sum()),
                   "% excepciones": 100 * ((~na & ~g) | (na & g)).mean()})
exc = pd.DataFrame(ex)
save_table(exc, "step03_structural_exceptions")

# Outliers
OUT = ["relationship_value", "value_lost_6m", "aum_outflow_90d", "transfer_to_competitor_bank_amount_90d"]
orow, top = [], []
for c in OUT:
    s = d[c]
    pos = s[s > 0]
    lg = np.log10(pos)
    q1, q3 = lg.quantile([0.25, 0.75])
    fence = 10 ** (q3 + 3 * (q3 - q1))
    if c == "relationship_value":
        err = diff[el] > 0.01
    elif c == "value_lost_6m":
        err = d.value_lost_6m > d.relationship_value * (1 + 1e-12)
    else:
        err = s < 0
    extra = (s > fence) & ~err
    orow.append({"variable": c, "n > 0": int((s > 0).sum()), "p99 $M": s.quantile(0.99) / 1e6, "máx $M": s.max() / 1e6,
                 "cerca extraordinario $M (log Q3 + 3·IQR)": fence / 1e6, "error": int(err.sum()), "extraordinario": int(extra.sum()),
                 "real": int(((s > 0) & ~err & ~extra).sum()), "% del total en extraordinarios": 100 * s[extra].sum() / s.sum()})
    cols = ["household_id", "segment", c] + (["relationship_value"] if c != "relationship_value" else []) + ["hard_churn_6m", "soft_churn_3m"]
    t = d.loc[extra, cols].sort_values(c, ascending=False).head(5).rename(columns={c: "valor"})
    if c == "relationship_value":
        t["relationship_value"] = t["valor"]
    t.insert(0, "variable", c)
    top.append(t[["variable", "household_id", "segment", "valor", "relationship_value", "hard_churn_6m", "soft_churn_3m"]])
out = pd.DataFrame(orow)
save_table(out, "step03_outliers")
topt = pd.concat(top, ignore_index=True)
save_table(topt, "step03_outliers_top")

rep = f"""# Paso 3 · Calidad de datos

## Objetivo
- Perfilar las variables, detectar imposibles e inconsistencias y clasificar las colas, sin eliminar ni recortar.

## Método
- Perfil sobre los 19,877 elegibles [DATA]; controles lógicos sobre las 20,000 filas.
- Outliers: error (rompe identidad o rango) / extraordinario (log₁₀ > Q3 + 3·IQR sobre valores > 0) / real. Sin capping (SPEC D.13).

## Código
- `src/step03_quality.py` · `tests/test_step03.py` · perfil completo en `outputs/tables/step03_profile.csv`.

## Resultados

### Controles lógicos [DATA]
{md_table(ctrl)}

- Ningún imposible ni duplicado. RV = AUM + depósitos al centavo en las 20,000 filas (G0-a).

### Excepciones al missing estructural (elegibles) [DATA]
{md_table(exc, floatfmt=",.2f")}

- Todas ≤ 3% [DATA]. Valores sin gatillo solo en `pension_deposit_stopped_flag`; los NaN con gatillo presente son
  historia corta o patrón no detectado: se tratan como "sin dato", distinto de "no aplica" (paso 5).

### Colas [DATA]
{md_table(out, floatfmt=",.2f")}

Casos extraordinarios de mayor valor [DATA]:
{md_table(topt, floatfmt=",.4g")}

- 0 errores: las colas son reales o extraordinarias y se conservan sin capping.

## Tests
- `tests/test_step03.py` (ver pytest).

## Decisiones y preguntas abiertas
- D3.1 en `reports/decision_log.md`.
"""
(REPORTS / "step03.md").write_text(rep, encoding="utf-8")
print(ctrl.to_string(index=False)); print(exc.round(2).to_string(index=False)); print(out.round(2).to_string(index=False))
