"""Paso 0 · Setup e inventario.

Crea la estructura de salidas, registra versiones, lee la base (solo lectura) y verifica por
código cada hecho de la sección DATOS del brief. Salida: outputs/tables/00_inventory.md.
QC gate: cualquier hecho que no cuadre detiene la ejecución.
"""
from __future__ import annotations

import hashlib
import importlib
import platform

import numpy as np
import pandas as pd

from common import DATA_PATH, FIGURES, MODELS, SCORED, TABLES, QC, save_table, set_seed, load_raw, COMPOSITES, OUTCOMES

set_seed()
for d in (TABLES, FIGURES, MODELS, SCORED):
    d.mkdir(parents=True, exist_ok=True)

# ── Entorno ────────────────────────────────────────────────────────────────────────────
print("Entorno")
pkgs = ["pandas", "numpy", "scipy", "sklearn", "statsmodels", "optbinning", "matplotlib", "openpyxl", "lightgbm"]
versions = {"python": platform.python_version()}
for p in pkgs:
    try:
        versions[p] = importlib.import_module(p).__version__
    except Exception as e:  # lightgbm opcional: fallback a HistGradientBoosting
        versions[p] = f"NO DISPONIBLE ({type(e).__name__})"
for k, v in versions.items():
    print(f"  {k:12s} {v}")

# ── Lectura ────────────────────────────────────────────────────────────────────────────
sha = hashlib.sha256(DATA_PATH.read_bytes()).hexdigest()
df = load_raw()
print(f"\nBase: {DATA_PATH}  sha256={sha[:16]}…  shape={df.shape}")

qc = QC("00")
print("\nHechos de la sección DATOS")

# Forma y unidad de análisis
qc.check("Filas", len(df) == 20_000, 20_000, len(df))
qc.check("household_id únicos", df["household_id"].nunique() == 20_000, 20_000, df["household_id"].nunique())
qc.check("Columnas", df.shape[1] == 62, 62, df.shape[1])
snap = df["snapshot_date"].unique()
qc.check("snapshot_date único = 2025-12-31", len(snap) == 1 and str(snap[0])[:10] == "2025-12-31", "2025-12-31", list(snap))

# Segmentos
seg = df["segment"].value_counts().to_dict()
qc.check("segment HNW / UHNW", seg == {"HNW": 18_897, "UHNW": 1_103}, "HNW 18,897 / UHNW 1,103", seg)

# Targets
excl = df["churn_excluded"].astype(bool)
hard, soft = df["hard_churn_6m"], df["soft_churn_3m"]
n_elig = int(hard.notna().sum())
qc.check("churn_excluded = True", excl.sum() == 123, 123, int(excl.sum()))
qc.check("Excluidos con los 3 targets NaN", df.loc[excl, ["hard_churn_6m", "soft_churn_3m", "value_lost_6m"]].isna().all().all(),
         "todos NaN", int(df.loc[excl, ["hard_churn_6m", "soft_churn_3m", "value_lost_6m"]].notna().sum().sum()))
qc.check("No excluidos con targets completos", df.loc[~excl, ["hard_churn_6m", "soft_churn_3m", "value_lost_6m"]].notna().all().all(),
         "0 NaN", int(df.loc[~excl, ["hard_churn_6m", "soft_churn_3m", "value_lost_6m"]].isna().sum().sum()))
qc.check("hard_churn_6m eventos / base", hard.sum() == 1_200 and n_elig == 19_877, "1,200 / 19,877 (6.04%)",
         f"{int(hard.sum()):,} / {n_elig:,} ({hard.mean():.2%})")
qc.check("soft_churn_3m eventos", soft.sum() == 1_756, "1,756 (8.83%)", f"{int(soft.sum()):,} ({soft.mean():.2%})")
qc.check("hard y soft nunca coinciden", int(((hard == 1) & (soft == 1)).sum()) == 0, 0, int(((hard == 1) & (soft == 1)).sum()))
union = ((hard == 1) | (soft == 1))
qc.check("Unión hard ∪ soft", union.sum() == 2_956, "2,956 (14.9%)", f"{int(union.sum()):,} ({union.sum() / n_elig:.2%})")
vl = df["value_lost_6m"]
qc.check("value_lost_6m > 0 solo con evento", int((vl[~excl & ~union] > 0).sum()) == 0, "0 hogares sin evento con valor perdido",
         int((vl[~excl & ~union] > 0).sum()))
qc.check("value_lost_6m > 0 en todo hogar con evento", bool((vl[union] > 0).all()), "100%", f"{(vl[union] > 0).mean():.1%}", severity="warn")
hs = df.groupby("segment")["hard_churn_6m"].sum().astype(int).to_dict()
qc.check("Eventos duros por segmento", hs == {"HNW": 1_120, "UHNW": 80}, "HNW 1,120 / UHNW 80", hs)

# Colas de relationship_value
rv = df["relationship_value"]
top5 = rv.nlargest(int(round(0.05 * len(rv)))).sum() / rv.sum()
qc.check("relationship_value mediana ≈ $4.8M", abs(rv.median() / 1e6 - 4.8) < 0.05, "$4.8M", f"${rv.median() / 1e6:.2f}M")
qc.check("relationship_value p99 ≈ $92M", abs(rv.quantile(0.99) / 1e6 - 92) < 1, "$92M", f"${rv.quantile(0.99) / 1e6:.1f}M")
qc.check("relationship_value máx ≈ $904M", abs(rv.max() / 1e6 - 904) < 1, "$904M", f"${rv.max() / 1e6:.1f}M")
qc.check("Top 5% hogares = 37.5% del valor", abs(top5 - 0.375) < 0.001, "37.5%", f"{top5:.2%}")

# Missing estructural (brief): la variable falta cuando el has_* es False.
# Regla verificada: ~has ⇒ NaN (sin valores donde no aplica). NaN adicionales con has = True se reportan aparte.
STRUCT = {
    "has_investments": ["aum", "aum_outflow_90d", "aum_outflow_pct_90d", "investment_redemption_pct",
                        "positions_liquidated_pct", "aum_vs_baseline_pct", "cash_pct_of_portfolio_chg"],
    "has_pension_stream": ["pension_deposit_stopped_flag"],
    "has_linked_business": ["business_payroll_stopped_flag"],
    "has_trust": ["trustee_change_flag"],
    # Del bloque 40–74%: condición encontrada por crosstab
    "has_payroll_stream": ["salary_deposit_stopped_flag"],
    "has_advisory": ["return_vs_benchmark"],
}
# Del bloque 40–74% sin has_* asociado: condición operativa no observable en la base
# (documentada en synthetic/schema.py del generador).
OPERATIONAL = {
    "client_reply_rate": "< 3 contactos del banker en 90d",
    "meetings_cancelled_by_client": "el banker no registra el campo",
    "relationship_dissatisfaction_flag": "hogar fuera del piloto del Client Assistant",
    "fixed_income_maturity_not_reinvested": "sin vencimientos de renta fija en la ventana (o sin inversiones)",
}
print("\nMissing estructural vs has_*")
rows = []
for flag, cols in STRUCT.items():
    h = df[flag].astype(bool)
    for c in cols:
        na = df[c].isna()
        val_without = int((~na & ~h).sum())       # valores donde no aplica: violación
        na_with = int((na & h).sum())             # NaN adicionales donde sí aplica
        rows.append({"variable": c, "condición": f"{flag} = False", "% missing": round(na.mean() * 100, 2),
                     "NaN con has=False": int((na & ~h).sum()), "valor con has=False": val_without,
                     "NaN extra con has=True": na_with,
                     "NaN extra | history<24": int((na & h & (df["history_months"] < 24)).sum())})
        sev = "gate" if flag in ("has_investments", "has_linked_business", "has_trust") else "warn"
        qc.check(f"{c}: NaN cuando {flag}=False", val_without == 0, "0 valores donde no aplica", val_without, severity=sev)
for c, cond in OPERATIONAL.items():
    na = df[c].isna()
    rows.append({"variable": c, "condición": f"operativa: {cond}", "% missing": round(na.mean() * 100, 2),
                 "NaN con has=False": None, "valor con has=False": None, "NaN extra con has=True": None,
                 "NaN extra | history<24": None})
miss_map = pd.DataFrame(rows)

block = ["salary_deposit_stopped_flag", "client_reply_rate", "return_vs_benchmark", "meetings_cancelled_by_client",
         "relationship_dissatisfaction_flag", "fixed_income_maturity_not_reinvested"]
rates = df[block].isna().mean()
qc.check("Bloque 40–74% missing", bool(rates.between(0.40, 0.745).all()), "40–74%",
         ", ".join(f"{c}={r:.1%}" for c, r in rates.items()))

# Historia corta
short = df["history_months"] < 24
qc.check("history_months < 24", short.sum() == 1_425, 1_425, int(short.sum()))
vs_base = ["aum_vs_baseline_pct", "deposit_balance_vs_6m_avg_pct", "outflow_vs_baseline_pct", "share_of_wallet_change"]
hist_tab = pd.DataFrame({"variable": vs_base,
                         "% missing history<24": [round(df.loc[short, c].isna().mean() * 100, 1) for c in vs_base],
                         "% missing history≥24": [round(df.loc[~short, c].isna().mean() * 100, 1) for c in vs_base]})
qc.check("aum_vs_baseline_pct ~24% missing en history<24", abs(df.loc[short, "aum_vs_baseline_pct"].isna().mean() - 0.24) < 0.02,
         "~24%", f"{df.loc[short, 'aum_vs_baseline_pct'].isna().mean():.1%}")

# Compuestos y outcomes presentes
qc.check("Compuestos presentes", all(c in df for c in COMPOSITES), COMPOSITES, [c for c in COMPOSITES if c in df])
qc.check("Outcomes presentes", all(c in df for c in OUTCOMES), OUTCOMES, [c for c in OUTCOMES if c in df])

# ── Inventario de columnas ───────────────────────────────────────────────────────────────
inv = pd.DataFrame({
    "columna": df.columns,
    "dtype": [str(t) for t in df.dtypes],
    "n_missing": df.isna().sum().values,
    "% missing": (df.isna().mean() * 100).round(2).values,
    "n_únicos": df.nunique().values,
    "mín": [df[c].min() if pd.api.types.is_numeric_dtype(df[c]) and df[c].dtype != bool else "" for c in df],
    "máx": [df[c].max() if pd.api.types.is_numeric_dtype(df[c]) and df[c].dtype != bool else "" for c in df],
})
facts = qc.table()
save_table(inv, "00_columns")
save_table(miss_map, "00_missing_map")
save_table(facts, "00_facts_qc")
pd.Series(versions, name="versión").rename_axis("paquete").reset_index().to_csv(TABLES / "00_versions.csv", index=False)

md = [
    "# Paso 0 · Inventario [DATA-SINT]\n",
    f"- Fuente (solo lectura): `{DATA_PATH.relative_to(DATA_PATH.parents[2])}` · sha256 `{sha[:16]}…`",
    f"- Forma: {df.shape[0]:,} filas × {df.shape[1]} columnas · {df['household_id'].nunique():,} `household_id` únicos · corte único {snap[0]}",
    f"- Entorno: " + ", ".join(f"{k} {v}" for k, v in versions.items()) + "\n",
    "## Verificación de hechos\n", facts.to_markdown(index=False), "\n",
    "## Mapa de missing estructural\n", miss_map.to_markdown(index=False), "\n",
    "## Missing en features vs baseline por historia\n", hist_tab.to_markdown(index=False), "\n",
    "## Columnas\n", inv.to_markdown(index=False), "\n",
]
(TABLES / "00_inventory.md").write_text("\n".join(md), encoding="utf-8")
print(f"\nEscrito {TABLES / '00_inventory.md'}")
qc.gate()
