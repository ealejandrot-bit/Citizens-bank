"""Paso 13 · Validación del campeón en el holdout (val, target B; se toca una sola vez con el modelo final).

- Discriminación dev vs val: AUC, Gini, PR-AUC, KS; gains y lift por decil de score; Precision@K, Lift@K, captura y
  captura ponderada por RV para K = 1 / 5 / 10 / 20%; matriz de confusión al corte de Crítico con falsos positivos por
  evento capturado.
- Aprobación (SPEC): tasa observada monótona por tramo en dev y val; caída de Gini dev→val ≤ 15% relativo; PSI dev→val
  de la distribución por tramo < 0.10; ≥ 30 eventos por tramo y por banda en val; precisión de overrides en val.
- UHNW aparte: solo métricas globales (sin tramos). Target A como sensibilidad.
Probabilidades pre-calibración (la calibración es el paso 14).
"""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from common import MODEL, PROC, REPORTS, load_split, md_table, save_table, set_seed

set_seed()
SC = pd.read_parquet(PROC / "step12_scores.parquet")
K12 = pickle.load(open(MODEL / "step12_scaling.pkl", "rb"))
TR = ["Crítico", "Alto", "Vigilancia", "Estable"]


def part(p):
    d = load_split(p).merge(SC, on="household_id")
    return d[d.in_pop_B].reset_index(drop=True), d[d.in_pop_A.astype(bool)].reset_index(drop=True)


dev, devA = part("dev")
val, valA = part("val")


def ks(y, p):
    o = np.argsort(-p)
    return float(np.max(np.abs(np.cumsum(y[o]) / y.sum() - np.cumsum(1 - y[o]) / (1 - y).sum())))


def glob(d, ycol="y_B"):
    y, p = d[ycol].astype(int).to_numpy(), d.probabilidad.to_numpy()
    a = roc_auc_score(y, p)
    return {"hogares": len(d), "eventos": int(y.sum()), "tasa %": 100 * y.mean(), "AUC": a, "Gini": 2 * a - 1, "PR-AUC": average_precision_score(y, p), "KS": ks(y, p)}


G = pd.DataFrame([{"muestra": "dev", **glob(dev)}, {"muestra": "val", **glob(val)},
                  {"muestra": "val · HNW", **glob(val[val.segment_uhnw == 0])}, {"muestra": "val · UHNW", **glob(val[val.segment_uhnw == 1])},
                  {"muestra": "dev · target A (sensibilidad)", **glob(devA, "y_A")}, {"muestra": "val · target A (sensibilidad)", **glob(valA, "y_A")}])
save_table(G, "step13_global")
g_dev, g_val = G.Gini.iloc[0], G.Gini.iloc[1]
drop = (g_dev - g_val) / g_dev

# Gains por decil (val)
y, rv = val.y_B.astype(int).to_numpy(), val.relationship_value.to_numpy()
dec = pd.qcut(val.score.rank(method="first"), 10, labels=False) + 1       # 1 = peor score
gn = pd.DataFrame({"decil": dec, "y": y, "rv": rv, "ev_rv": y * rv, "score": val.score}).groupby("decil").agg(
    hogares=("y", "size"), eventos=("y", "sum"), score_mín=("score", "min"), score_máx=("score", "max"), rv_eventos=("ev_rv", "sum")).reset_index()
gn["tasa %"] = 100 * gn.eventos / gn.hogares
gn["captura %"] = 100 * gn.eventos / y.sum()
gn["captura acumulada %"] = gn["captura %"].cumsum()
gn["captura RV eventos acumulada %"] = 100 * gn.rv_eventos.cumsum() / (y * rv).sum()
gn["lift"] = gn["tasa %"] / (100 * y.mean())
gn = gn.drop(columns="rv_eventos")
save_table(gn, "step13_gains_val")

o = np.argsort(val.score.to_numpy(), kind="stable")
pk = []
for k in (1, 5, 10, 20):
    top = o[: int(round(len(val) * k / 100))]
    pk.append({"K %": k, "hogares": len(top), "eventos": int(y[top].sum()), "Precision@K %": 100 * y[top].mean(), "Lift@K": y[top].mean() / y.mean(),
               "captura %": 100 * y[top].sum() / y.sum(), "captura RV eventos %": 100 * (y * rv)[top].sum() / (y * rv).sum(),
               "% RV de la cartera": 100 * rv[top].sum() / rv.sum()})
pk = pd.DataFrame(pk)
save_table(pk, "step13_precision_at_k")

# Matriz de confusión al corte de Crítico (tramo final)
crit = (val.tramo == "Crítico").to_numpy()
TP, FP, FN, TN = int((crit & (y == 1)).sum()), int((crit & (y == 0)).sum()), int((~crit & (y == 1)).sum()), int((~crit & (y == 0)).sum())
cm = pd.DataFrame([{"TP": TP, "FP": FP, "FN": FN, "TN": TN, "precisión %": 100 * TP / (TP + FP), "recall %": 100 * TP / (TP + FN),
                    "falsos positivos por evento capturado": FP / TP}])
save_table(cm, "step13_confusion_critico")


# Tramos dev vs val, PSI
def tramos(d, col):
    t = d.groupby(col).agg(hogares=("y_B", "size"), eventos=("y_B", "sum")).reindex(TR).fillna(0)
    t["% hogares"] = 100 * t.hogares / t.hogares.sum()
    t["tasa %"] = 100 * t.eventos / t.hogares
    return t


rows = []
for col, lab in (("tramo", "final (con overrides)"), ("tramo_modelo", "modelo (sin overrides)")):
    td, tv = tramos(dev, col), tramos(val, col)
    pd_, pv = td["% hogares"] / 100, tv["% hogares"] / 100
    psi_c = (pv - pd_) * np.log(pv / pd_)
    for t in TR:
        rows.append({"tramos": lab, "tramo": t, "hogares dev": int(td.loc[t, "hogares"]), "% dev": td.loc[t, "% hogares"], "tasa dev %": td.loc[t, "tasa %"],
                     "hogares val": int(tv.loc[t, "hogares"]), "% val": tv.loc[t, "% hogares"], "eventos val": int(tv.loc[t, "eventos"]),
                     "tasa val %": tv.loc[t, "tasa %"], "PSI (contribución)": psi_c[t]})
TT = pd.DataFrame(rows)
save_table(TT, "step13_tramos_dev_val")
PSI = TT.groupby("tramos")["PSI (contribución)"].sum()

bd = val.groupby("banda").agg(hogares=("y_B", "size"), eventos=("y_B", "sum")).reset_index()
bd["tasa %"] = 100 * bd.eventos / bd.hogares
ORDER = [b for t in TR for b in K12["bands_used"][t]]
bd = bd.set_index("banda").reindex(ORDER).reset_index()
save_table(bd, "step13_bands_val")

# Overrides en val (hogares movidos)
RANK = {t: i for i, t in enumerate(TR)}
RULES = {"banker_change_6m_flag = 1": val.banker_change_6m_flag == 1, "complaint_escalated_flag = 1": val.complaint_escalated_flag == 1,
         "transfer_to_competitor_pct_90d ≥ 10%": val.transfer_to_competitor_pct_90d >= 0.10}
ovr = []
for name, dest in K12["overrides"].items():
    m = RULES[name].fillna(False).to_numpy() & (val.tramo_modelo.map(RANK).to_numpy() > RANK[dest])
    ovr.append({"regla": name, "destino": dest, "movidos val": int(m.sum()), "eventos": int(y[m].sum()), "precisión val %": 100 * y[m].mean(),
                "cumple umbral (12% Alto / 25% Crítico)": 100 * y[m].mean() >= (25 if dest == "Crítico" else 12)})
ovr = pd.DataFrame(ovr)
save_table(ovr, "step13_overrides_val")

fin = TT[TT.tramos == "final (con overrides)"]
mod = TT[TT.tramos == "modelo (sin overrides)"]
mono = lambda s: bool((np.diff(s.to_numpy()) < 0).all())  # noqa: E731
AP = pd.DataFrame([
    ("Tasa monótona por tramo en dev (final)", mono(fin["tasa dev %"])),
    ("Tasa monótona por tramo en val (final)", mono(fin["tasa val %"])),
    ("Tasa monótona por tramo en val (modelo)", mono(mod["tasa val %"])),
    (f"Caída de Gini dev→val ≤ 15% relativo ({100 * drop:.1f}%)", drop <= 0.15),
    (f"PSI dev→val por tramo < 0.10 (final {PSI['final (con overrides)']:.4f}; modelo {PSI['modelo (sin overrides)']:.4f})",
     PSI.max() < 0.10),
    (f"≥ 30 eventos por tramo en val (mín {int(fin['eventos val'].min())})", fin["eventos val"].min() >= 30),
    (f"≥ 30 eventos por banda en val (mín {int(bd.eventos.min())})", bd.eventos.min() >= 30),
    ("Overrides con precisión ≥ umbral en val", bool(ovr["cumple umbral (12% Alto / 25% Crítico)"].all())),
    (f"Lift Crítico/Estable ≥ 5x en val ({fin['tasa val %'].iloc[0] / fin['tasa val %'].iloc[3]:.1f}x)", fin["tasa val %"].iloc[0] >= 5 * fin["tasa val %"].iloc[3]),
], columns=["criterio", "cumple"])
AP["cumple"] = AP.cumple.map({True: "sí", False: "no"})
save_table(AP, "step13_approval")

rep = f"""# Paso 13 · Validación

## Objetivo
- Medir el campeón final una sola vez en validación (30%) y aplicar los criterios de aprobación del SPEC.

## Método
- Métricas sobre la probabilidad pre-calibración del score (el orden no cambia con Platt). Gains por decil de score,
  Precision@K / Lift@K con captura ponderada por RV, matriz de confusión al corte de Crítico.
- Aprobación: monotonía por tramo (dev y val), caída de Gini ≤ 15% relativo, PSI dev→val de la distribución por tramo
  < 0.10, ≥ 30 eventos por tramo y banda en val, precisión de overrides en val. UHNW solo global. Sin OOT (L1).

## Código
- `src/step13_validation.py` · `tests/test_step13.py` · `step13_*.csv`.

## Resultados

### Discriminación global [DATA]
{md_table(G, floatfmt=",.4f")}

- Caída de Gini dev→val: ({g_dev:.4f} − {g_val:.4f}) / {g_dev:.4f} = {100 * drop:.1f}% relativo [DATA].
- UHNW: {int(G.eventos.iloc[3])} eventos en val [DATA]; solo métricas globales (L5).

### Gains y lift por decil de score (val) [DATA]
{md_table(gn, floatfmt=",.2f")}

- Verificación: captura suma {gn['captura %'].sum():.1f}%; eventos suman {int(gn.eventos.sum()):,} = {int(y.sum()):,} [DATA].

### Precision@K y Lift@K (val) [DATA]
{md_table(pk, floatfmt=",.2f")}

### Matriz de confusión al corte de Crítico (val) [DATA]
{md_table(cm, floatfmt=",.2f")}

- Verificación: TP + FP + FN + TN = {TP + FP + FN + TN:,} = {len(val):,} hogares de val [DATA].

### Tramos dev vs val y PSI [DATA]
{md_table(TT, floatfmt=",.4f")}

- Verificación: % dev y % val suman 100% por tipo de tramo; churn de cartera val = Σ share × tasa =
  {(fin['% val'] * fin['tasa val %']).sum() / 100:.2f}% = {100 * y.mean():.2f}% [DATA].

### Bandas (val) [DATA]
{md_table(bd, floatfmt=",.2f")}

### Overrides (val) [DATA]
{md_table(ovr, floatfmt=",.2f")}

### Criterios de aprobación [DATA]
{md_table(AP)}

## Tests
- `tests/test_step13.py` (ver pytest).

## Decisiones y preguntas abiertas
- D13.1 en `reports/decision_log.md`.
"""
(REPORTS / "step13.md").write_text(rep, encoding="utf-8")
print(G.round(4).to_string(index=False)); print(pk.round(2).to_string(index=False)); print(cm.round(2).to_string(index=False))
print(TT.round(3).to_string(index=False)); print(bd.round(2).to_string(index=False)); print(ovr.round(2).to_string(index=False)); print(AP.to_string(index=False))
