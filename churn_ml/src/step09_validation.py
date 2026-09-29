"""Paso 9 · Validación en el holdout (una sola vez, modelos congelados) y tabla H-2 contra M1 (termina en G3).

- Mismos 5,779 hogares B de val para EBM, XGBoost y M1 (M1 ya validado en su paso 13; aquí se recalcula en paralelo).
- Métricas: AUC, Gini, PR-AUC, KS, Brier, pendiente b; gains por decil; Precision@K / Lift@K / captura ponderada por RV;
  confusión al corte de Crítico; calibración por tramo (Wilson 90%); PSI dev→val por tramo.
- ΔGini y ΔPR-AUC contra M1 con IC bootstrap pareado 95% (1,000 réplicas).
- Nota: la probabilidad de M1 fue calibrada con Platt sobre este mismo val (paso 14 de M1): su Brier y b en val son
  favorables a M1 por construcción; el orden (AUC, PR-AUC) no se ve afectado.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from statsmodels.stats.proportion import proportion_confint

from common import ID, INH, REPORTS, SCORES, SEED, TABLES, md_table, save_table, set_seed

set_seed()
O = pd.read_csv(SCORES / "household_scores_ml.csv")
pop = pd.read_parquet(INH / "step01_population.parquet")[[ID, "in_pop_B", "y_B"]]
F = pd.read_parquet(INH / "features.parquet")[[ID, "relationship_value"]]
O = O.merge(pop, on=ID).merge(F, on=ID)
dev = O[(O["partición"] == "dev") & O.in_pop_B].reset_index(drop=True)
val = O[(O["partición"] == "val") & O.in_pop_B].reset_index(drop=True)
TR = ["Crítico", "Alto", "Vigilancia", "Estable"]
MODS = {"EBM": ("p_ebm_calibrada", "tramo_ebm"), "XGBoost": ("p_xgb_calibrada", "tramo_xgb"), "M1": ("p_m1_calibrada", "tramo_m1")}


def ks(y, p):
    o = np.argsort(-p)
    return float(np.max(np.abs(np.cumsum(y[o]) / y.sum() - np.cumsum(1 - y[o]) / (1 - y).sum())))


def slope(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(sm.GLM(y, sm.add_constant(np.log(p / (1 - p))), family=sm.families.Binomial()).fit().params[1])


def glob(d, pcol):
    y, p = d.y_B.astype(int).to_numpy(), d[pcol].to_numpy()
    a = roc_auc_score(y, p)
    rv = d.relationship_value.to_numpy()
    top = np.argsort(-p)[: int(round(0.10 * len(p)))]
    return {"AUC": a, "Gini": 2 * a - 1, "PR-AUC": average_precision_score(y, p), "KS": ks(y, p), "Brier": brier_score_loss(y, p), "pendiente b": slope(y, p),
            "media p %": 100 * p.mean(), "tasa %": 100 * y.mean(), "captura RV eventos decil 1 %": 100 * (rv * y)[top].sum() / (rv * y).sum()}


G = pd.DataFrame([{"modelo": m, "muestra": s_, **glob(d, pc)} for m, (pc, _) in MODS.items() for s_, d in (("dev", dev), ("val", val))])
save_table(G, "step09_global")
g = G.set_index(["modelo", "muestra"])

# Bootstrap pareado vs M1
y = val.y_B.astype(int).to_numpy()
rng = np.random.default_rng(SEED)
BS = {m: [] for m in ("EBM", "XGBoost")}
for _ in range(1000):
    i = rng.choice(len(y), len(y), replace=True)
    if y[i].sum() == 0:
        continue
    base_g = 2 * roc_auc_score(y[i], val.p_m1_calibrada.to_numpy()[i]) - 1
    base_p = average_precision_score(y[i], val.p_m1_calibrada.to_numpy()[i])
    for m in BS:
        p = val[MODS[m][0]].to_numpy()[i]
        BS[m].append((2 * roc_auc_score(y[i], p) - 1 - base_g, average_precision_score(y[i], p) - base_p))
DL = []
for m, b in BS.items():
    b = np.array(b)
    DL.append({"modelo": m, "ΔGini vs M1": g.loc[(m, "val"), "Gini"] - g.loc[("M1", "val"), "Gini"], "ΔGini IC95": f"[{np.quantile(b[:, 0], .025):+.4f}, {np.quantile(b[:, 0], .975):+.4f}]",
               "ΔPR-AUC vs M1": g.loc[(m, "val"), "PR-AUC"] - g.loc[("M1", "val"), "PR-AUC"], "ΔPR-AUC IC95": f"[{np.quantile(b[:, 1], .025):+.4f}, {np.quantile(b[:, 1], .975):+.4f}]",
               "% réplicas ΔPR-AUC > 0": 100 * (b[:, 1] > 0).mean()})
DL = pd.DataFrame(DL)
save_table(DL, "step09_delta_vs_m1")

# Gains (EBM) y Precision@K (todos)
rv = val.relationship_value.to_numpy()
pe = val.p_ebm_calibrada.to_numpy()
dec = pd.qcut(pd.Series(-pe).rank(method="first"), 10, labels=False) + 1
GN = pd.DataFrame({"decil": dec, "y": y, "evrv": y * rv}).groupby("decil").agg(hogares=("y", "size"), eventos=("y", "sum"), rv_ev=("evrv", "sum")).reset_index()
GN["tasa %"] = 100 * GN.eventos / GN.hogares
GN["captura acumulada %"] = 100 * GN.eventos.cumsum() / y.sum()
GN["captura RV eventos acumulada %"] = 100 * GN.rv_ev.cumsum() / (y * rv).sum()
GN["lift"] = GN["tasa %"] / (100 * y.mean())
GN = GN.drop(columns="rv_ev")
save_table(GN, "step09_gains_ebm")
PK = []
for m, (pc, _) in MODS.items():
    o = np.argsort(-val[pc].to_numpy(), kind="stable")
    for k in (1, 5, 10, 20):
        t = o[: int(round(len(val) * k / 100))]
        PK.append({"modelo": m, "K %": k, "Precision@K %": 100 * y[t].mean(), "Lift@K": y[t].mean() / y.mean(), "captura %": 100 * y[t].sum() / y.sum(),
                   "captura RV eventos %": 100 * (y * rv)[t].sum() / (y * rv).sum()})
PK = pd.DataFrame(PK)
save_table(PK, "step09_precision_at_k")

# Tramos: calibración, PSI, confusión en Crítico
TT, PSI, CM = [], {}, []
for m, (pc, tc) in MODS.items():
    pdv = dev[tc].value_counts(normalize=True).reindex(TR).fillna(0).to_numpy()
    pvl = val[tc].value_counts(normalize=True).reindex(TR).fillna(0).to_numpy()
    PSI[m] = float(((pvl - pdv) * np.log(np.clip(pvl, 1e-4, None) / np.clip(pdv, 1e-4, None))).sum())
    for t in TR:
        gg = val[val[tc] == t]
        e, n = int(gg.y_B.sum()), len(gg)
        lo, hi = proportion_confint(e, n, alpha=0.10, method="wilson")
        TT.append({"modelo": m, "tramo": t, "% val": 100 * n / len(val), "eventos": e, "esperada %": 100 * gg[pc].mean(), "observada %": 100 * e / n,
                   "Wilson 90%": f"[{100 * lo:.1f}, {100 * hi:.1f}]", "dentro de IC": lo <= gg[pc].mean() <= hi, "tasa dev %": 100 * dev.loc[dev[tc] == t, "y_B"].mean()})
    c = (val[tc] == "Crítico").to_numpy()
    tp, fp = int((c & (y == 1)).sum()), int((c & (y == 0)).sum())
    CM.append({"modelo": m, "hogares Crítico": int(c.sum()), "TP": tp, "FP": fp, "precisión %": 100 * tp / (tp + fp), "recall %": 100 * tp / y.sum(), "FP por evento capturado": fp / tp})
TT, CM = pd.DataFrame(TT), pd.DataFrame(CM)
save_table(TT, "step09_tramos_val")
save_table(CM, "step09_confusion_critico")
save_table(pd.DataFrame([{"modelo": k, "PSI dev→val por tramo": v} for k, v in PSI.items()]), "step09_psi")

# Tabla H-2
MON = pd.read_csv(TABLES / "step04_monotonicity.csv")
RC = pd.read_csv(TABLES / "step04_reason_stability.csv").set_index("modelo")
H = []
for m, mon_cols in (("EBM", ["violaciones en f(x) EBM", "ICE EBM", "PDP EBM"]), ("XGBoost", ["ICE XGBoost", "PDP XGBoost"])):
    drop_m = (g.loc[(m, "dev"), "Gini"] - g.loc[(m, "val"), "Gini"]) / g.loc[(m, "dev"), "Gini"]
    drop_1 = (g.loc[("M1", "dev"), "Gini"] - g.loc[("M1", "val"), "Gini"]) / g.loc[("M1", "dev"), "Gini"]
    viol = int(MON[mon_cols].fillna(0).to_numpy().sum())
    d_ = DL.set_index("modelo").loc[m]
    rows = [("ΔGini ≥ +0.05", f"{d_['ΔGini vs M1']:+.4f} {d_['ΔGini IC95']}", d_["ΔGini vs M1"] >= 0.05),
            ("ΔPR-AUC ≥ +0.03", f"{d_['ΔPR-AUC vs M1']:+.4f} {d_['ΔPR-AUC IC95']}", d_["ΔPR-AUC vs M1"] >= 0.03),
            ("Caída de Gini dev→val ≤ 15% y no peor que M1", f"{100 * drop_m:.1f}% vs M1 {100 * drop_1:.1f}%", drop_m <= 0.15 and drop_m <= drop_1),
            ("Brier ≤ M1 con b ∈ [0.8, 1.2] (val)", f"{g.loc[(m, 'val'), 'Brier']:.4f} vs {g.loc[('M1', 'val'), 'Brier']:.4f}; b = {g.loc[(m, 'val'), 'pendiente b']:.3f}",
             g.loc[(m, "val"), "Brier"] <= g.loc[("M1", "val"), "Brier"] and 0.8 <= g.loc[(m, "val"), "pendiente b"] <= 1.2),
            ("Violaciones de monotonía = 0", str(viol), viol == 0),
            ("Reason codes ≥ 70% (top 1) y signo coherente 100%", f"{RC.loc[m, 'acuerdo top 1 %']:.1f}%; signo {RC.loc[m, '% variables con signo coherente']:.2f}%",
             RC.loc[m, "acuerdo top 1 %"] >= 70 and RC.loc[m, "% variables con signo coherente"] >= 99.999),
            ("Captura RV de eventos decil 1 ≥ M1 (val)", f"{g.loc[(m, 'val'), 'captura RV eventos decil 1 %']:.1f}% vs {g.loc[('M1', 'val'), 'captura RV eventos decil 1 %']:.1f}%",
             g.loc[(m, "val"), "captura RV eventos decil 1 %"] >= g.loc[("M1", "val"), "captura RV eventos decil 1 %"]),
            ("PSI dev→val por tramo < 0.10", f"{PSI[m]:.4f}", PSI[m] < 0.10)]
    H += [{"modelo": m, "criterio H-2": a, "valor [DATA]": b_, "cumple": "sí" if c_ else "no"} for a, b_, c_ in rows]
H = pd.DataFrame(H)
save_table(H, "step09_h2")
nf = H[H.cumple == "no"].groupby("modelo").size().reindex(["EBM", "XGBoost"]).fillna(0).astype(int)

rep = f"""# Paso 9 · Validación en el holdout y tabla H-2

## Objetivo
- Medir el ML congelado una sola vez en validación y decidir con la tabla H-2 si reemplaza al M1.

## Método
- Mismos 5,779 hogares B de val para EBM, XGBoost y M1; ΔGini y ΔPR-AUC con IC bootstrap pareado (1,000).
- Probabilidad publicada de cada modelo (EBM y XGBoost calibrados en dev; M1 calibrado sobre val en su paso 14, lo que
  favorece su Brier y b aquí).

## Código
- `src/step09_validation.py` · `tests/test_step09.py` · `step09_*.csv`.

## Resultados

### Métricas globales dev y val [DATA]
{md_table(G, floatfmt=",.4f")}

### Diferencias contra M1 (val, pareado) [DATA]
{md_table(DL, floatfmt=",.4f")}

### Precision@K (val) [DATA]
{md_table(PK, floatfmt=",.2f")}

### Gains por decil · EBM (val) [DATA]
{md_table(GN, floatfmt=",.2f")}

- Verificación: eventos suman {int(GN.eventos.sum()):,} = {int(y.sum()):,}; captura acumulada final 100% [DATA].

### Tramos en val (calibración y estabilidad) [DATA]
{md_table(TT, floatfmt=",.2f")}

- Verificación: % val suma 100% por modelo; PSI dev→val por tramo: {', '.join(f'{k} {v:.4f}' for k, v in PSI.items())} [DATA].

### Confusión al corte de Crítico (val) [DATA]
{md_table(CM, floatfmt=",.2f")}

### Tabla H-2 (reemplazo del M1) [DATA]
{md_table(H)}

- Criterios no cumplidos: EBM {nf['EBM']}, XGBoost {nf['XGBoost']} [DATA]. Si hay alguno, el ML no reemplaza al M1 y el paso 10
  evalúa el uso conjunto (I-7).

## Tests
- `tests/test_step09.py` (ver pytest).

## Decisiones y preguntas abiertas
- D9.1 en `reports/decision_log.md`; preguntas G3 en `reports/gate_3.md`.
"""
(REPORTS / "step09.md").write_text(rep, encoding="utf-8")
print(G.round(4).to_string(index=False)); print(DL.round(4).to_string(index=False)); print(PK.round(2).to_string(index=False)); print(TT.round(2).to_string(index=False))
print(CM.round(2).to_string(index=False)); print(PSI); print(H.to_string(index=False))
