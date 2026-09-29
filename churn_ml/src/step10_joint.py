"""Paso 10 · Uso conjunto de los modelos (val, target B; modelos congelados).

- Matriz tramo M1 × tramo EBM: hogares, tasa observada y acuerdo; hogares que solo uno marca como Crítico/Alto.
- Opciones a igual capacidad (K = 1 / 5 / 10 / 20 / 28% de hogares; 28% ≈ Crítico+Alto del M1):
    lente política (tramo primero, luego p × RV): M1 · EBM · (b) tramo del M1 con orden p_EBM × RV · (c) M1 + alerta
    EBM (Crítico del EBM fuera de Crítico/Alto del M1 entra primero en Alto); lente valor (p × RV global) y lente
    probabilidad (p global) para M1, EBM y promedio.
  Métricas: eventos capturados, RV de eventos capturado, precisión.
- A-lite: mismas opciones con el tramo de A-lite en el subconjunto justo (fuera del desarrollo de todos; D9b.1).
- Regla fijada antes de ver resultados (D10.1): se recomienda la opción con mayor captura de RV de eventos al 10% de
  hogares dentro de la lente política; empate (< 1 pp) ⟹ la más simple de operar (M1 < b < c < EBM).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import ID, INH, REPORTS, SCORES, md_table, save_table, set_seed

set_seed()
TR = ["Crítico", "Alto", "Vigilancia", "Estable"]
RK = {t: i for i, t in enumerate(TR)}
O = pd.read_csv(SCORES / "household_scores_ml.csv")
pop = pd.read_parquet(INH / "step01_population.parquet")[[ID, "in_pop_B", "y_B"]]
F = pd.read_parquet(INH / "features.parquet")[[ID, "relationship_value"]]
A = pd.read_csv(INH / "alite_scored_households.csv")[[ID, "probabilidad_lite", "tramo_lite"]]
SPL = pd.read_csv(INH / "alite_split.csv")[[ID, "muestra"]]
O = O.merge(pop, on=ID).merge(F, on=ID).merge(A, on=ID).merge(SPL, on=ID, how="left")
val = O[(O["partición"] == "val") & O.in_pop_B].reset_index(drop=True)

# Matriz M1 × EBM
MX = pd.crosstab(val.tramo_m1, val.tramo_ebm).reindex(index=TR, columns=TR).fillna(0).astype(int)
RT = val.groupby(["tramo_m1", "tramo_ebm"]).y_B.mean().unstack().reindex(index=TR, columns=TR) * 100
agree = np.trace(MX.to_numpy()) / MX.to_numpy().sum()
MXt = MX.reset_index().rename(columns={"tramo_m1": "M1 \\ EBM"})
RTt = RT.round(1).reset_index().rename(columns={"tramo_m1": "M1 \\ EBM (tasa B %)"})
save_table(MXt, "step10_matrix_counts")
save_table(RTt, "step10_matrix_rates")
hi_m1, hi_e = val.tramo_m1.isin(TR[:2]), val.tramo_ebm.isin(TR[:2])
ONLY = pd.DataFrame([{"grupo": g, "hogares": int(m.sum()), "eventos": int(val.y_B[m].sum()), "tasa B %": 100 * val.y_B[m].mean()}
                     for g, m in (("Crítico/Alto en ambos", hi_m1 & hi_e), ("solo M1", hi_m1 & ~hi_e), ("solo EBM", ~hi_m1 & hi_e), ("ninguno", ~hi_m1 & ~hi_e))])
save_table(ONLY, "step10_only_one")


def rank_orders(d, tramo_col, p_own, label):
    """Tres lentes consistentes (D10.1): política (tramo primero, luego p × RV), valor (p × RV global), probabilidad (p global)."""
    rv = d.relationship_value.to_numpy()
    pe, po = d.p_ebm_calibrada.to_numpy(), d[p_own].to_numpy()
    tr = d[tramo_col].map(RK).to_numpy()
    tr_e = d.tramo_ebm.map(RK).to_numpy()
    alert = (tr_e == 0) & (tr > 1)                                  # Crítico EBM fuera de Crítico/Alto del modelo base
    tr_c = np.where(alert, 1, tr)
    pr_c = np.where(alert, np.inf, po * rv)
    return {f"política · {label} (tramo, luego p×RV)": np.lexsort((-(po * rv), tr)),
            "política · EBM (tramo, luego p×RV)": np.lexsort((-(pe * rv), tr_e)),
            f"política · {label} tramo + orden EBM (b)": np.lexsort((-(pe * rv), tr)),
            f"política · {label} + alerta EBM (c)": np.lexsort((-pr_c, tr_c)),
            f"valor · {label} (p×RV global)": np.argsort(-(po * rv), kind="stable"),
            "valor · EBM (p×RV global)": np.argsort(-(pe * rv), kind="stable"),
            f"valor · promedio {label}/EBM": np.argsort(-(0.5 * (pe + po) * rv), kind="stable"),
            f"probabilidad · {label} (p global)": np.argsort(-po, kind="stable"),
            "probabilidad · EBM (p global)": np.argsort(-pe, kind="stable")}


def capture(d, orders, sample):
    y, rv = d.y_B.astype(int).to_numpy(), d.relationship_value.to_numpy()
    rows = []
    for name, o in orders.items():
        for k in (1, 5, 10, 20, 28):
            t = o[: int(round(len(d) * k / 100))]
            rows.append({"muestra": sample, "opción": name, "K % hogares": k, "hogares": len(t), "eventos": int(y[t].sum()), "precisión %": 100 * y[t].mean(),
                         "captura eventos %": 100 * y[t].sum() / y.sum(), "captura RV eventos %": 100 * (y * rv)[t].sum() / (y * rv).sum()})
    return rows


CAP = pd.DataFrame(capture(val, rank_orders(val, "tramo_m1", "p_m1_calibrada", "M1"), "val completo (5,779)"))
fair = val[val.muestra == "holdout"].reset_index(drop=True)
CAP_A = pd.DataFrame(capture(fair, rank_orders(fair, "tramo_lite", "probabilidad_lite", "A-lite"), f"justo ({len(fair):,})") +
                     capture(fair, {k: v for k, v in rank_orders(fair, "tramo_m1", "p_m1_calibrada", "M1").items() if "M1" in k}, f"justo ({len(fair):,})"))
save_table(CAP, "step10_capture_options")
save_table(CAP_A, "step10_capture_alite")

k10 = CAP[CAP["K % hogares"] == 10].set_index("opción")
SIMPLE = ["política · M1 (tramo, luego p×RV)", "política · M1 tramo + orden EBM (b)", "política · M1 + alerta EBM (c)", "política · EBM (tramo, luego p×RV)"]
best = k10.loc[SIMPLE, "captura RV eventos %"].max()
REC = next(o for o in SIMPLE if best - k10.loc[o, "captura RV eventos %"] < 1.0)
piv = CAP.pivot_table(index="opción", columns="K % hogares", values="captura RV eventos %").reset_index()
piv.columns = ["opción"] + [f"RV capturado @{c}%" for c in piv.columns[1:]]
piv_e = CAP.pivot_table(index="opción", columns="K % hogares", values="captura eventos %").reset_index()
piv_e.columns = ["opción"] + [f"eventos @{c}%" for c in piv_e.columns[1:]]
SUMM = piv.merge(piv_e, on="opción")
save_table(SUMM, "step10_summary")
pa = CAP_A.pivot_table(index="opción", columns="K % hogares", values="captura RV eventos %").reset_index()
pa.columns = ["opción"] + [f"RV capturado @{c}%" for c in pa.columns[1:]]

rep = f"""# Paso 10 · Uso conjunto

## Objetivo
- Decidir cómo aprovechar el ML si no reemplaza al M1: ¿ordena mejor dentro de los tramos, alerta casos que el M1 no
  ve, o no agrega?

## Método
- Val (modelos congelados). Matriz de tramos M1 × EBM. Opciones a igual número de hogares contactados (K) en tres lentes
  consistentes. Regla previa (D10.1): dentro de la lente política, mayor captura de RV de eventos al 10%; empate < 1 pp
  ⟹ la más simple de operar.
- A-lite: mismas opciones en el subconjunto justo (1,737 hogares fuera del desarrollo de todos).

## Código
- `src/step10_joint.py` · `tests/test_step10.py` · `step10_*.csv`.

## Resultados

### Hogares por tramo M1 × EBM (val) [DATA]
{md_table(MXt)}

- Acuerdo de tramo: {100 * agree:.1f}% de los hogares [DATA]. Verificación: la matriz suma {int(MX.to_numpy().sum()):,} = {len(val):,}.

### Tasa B observada por celda (val) [DATA]
{md_table(RTt)}

### Marcados Crítico/Alto por uno solo [DATA]
{md_table(ONLY, floatfmt=",.2f")}

### Captura por opción a igual capacidad (val) [DATA]
{md_table(SUMM, floatfmt=",.1f")}

- Recomendación por la regla D10.1: **{REC}** (captura de RV al 10%: {k10.loc[REC, 'captura RV eventos %']:.1f}% vs M1 {k10.loc[SIMPLE[0], 'captura RV eventos %']:.1f}%) [DATA].
- Las lentes "valor" y "probabilidad" muestran el efecto de cambiar la prioridad (no solo el modelo): ordenar por p×RV
  global concentra más RV y menos eventos; es una decisión de negocio separada de la elección de modelo.

### A-lite en el subconjunto justo (captura de RV de eventos) [DATA]
{md_table(pa, floatfmt=",.1f")}

## Tests
- `tests/test_step10.py` (ver pytest).

## Decisiones y preguntas abiertas
- D10.1 en `reports/decision_log.md`.
"""
(REPORTS / "step10.md").write_text(rep, encoding="utf-8")
print(MXt.to_string(index=False)); print(RTt.to_string(index=False)); print(ONLY.round(2).to_string(index=False)); print(SUMM.round(1).to_string(index=False)); print(pa.round(1).to_string(index=False)); print("REC", REC, agree)
