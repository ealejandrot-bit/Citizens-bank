"""Paso 1 · Conjunto de variables candidatas del ML (dev, target B).

Cribado sobre valores crudos (NaN nativo, sin imputar):
  f1 casi constante: valor modal (incluido NaN) ≥ 99% de dev B.
  f2 fuga: AUC univariada > 0.85 o IV > 0.50 (tabla univariada B heredada del paso 6 de M1).
  f3 duplicado casi exacto: |ρ Spearman| > 0.95 con otra candidata ⟹ se queda la de mayor IV del par.
`cluster` entra como categórica (sin ρ). Los compuestos entran (I-2); su variante sin ellos se evalúa en el paso 2.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import COMPOSITES, INH, REPORTS, candidates, load_split, md_table, save_table, set_seed, signs

set_seed()
dev = load_split("dev")
D = dev[dev.in_pop_B].reset_index(drop=True)
C = candidates()
U = pd.read_csv(INH / "step06_univariate_B.csv").set_index("variable")
IV9 = pd.read_csv(INH / "step09_iv_summary.csv").set_index("variable")
SP = pd.read_csv(INH / "step08_spearman.csv").set_index("variable")
SG = signs()

T = pd.DataFrame({"variable": C})
T["modal %"] = [100 * D[c].value_counts(normalize=True, dropna=False).iloc[0] for c in C]
T["% missing"] = [100 * D[c].isna().mean() for c in C]
T["IV"] = T.variable.map(U["IV preliminar"]).fillna(T.variable.map(IV9.IV))
T["AUC univariada"] = T.variable.map(U["AUC univariada"])
T["signo"] = T.variable.map(SG).fillna("?")
T.loc[T.variable == "cluster", "signo"] = "categórica"
T["f1 casi constante"] = T["modal %"] >= 99
T["f2 fuga"] = (T["AUC univariada"] > 0.85) | (T["IV"] > 0.50)
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

num = [c for c in C if c in SP.index]
R = SP.loc[num, num].abs().fillna(0).to_numpy()
np.fill_diagonal(R, 1)
lab = fcluster(linkage(squareform(1 - R, checks=False), "complete"), t=0.05, criterion="distance")   # todos los pares |ρ| > 0.95
ivs = T.set_index("variable").IV
pairs, drop = [], set()
for g in np.unique(lab):
    mem = [c for c, l in zip(num, lab) if l == g]
    if len(mem) < 2:
        continue
    keep = max(mem, key=lambda c: ivs[c])
    for m_ in mem:
        if m_ != keep:
            pairs.append({"grupo": int(g), "se queda": keep, "sale": m_, "Spearman con la que queda": SP.loc[keep, m_]})
            drop.add(m_)
PR = pd.DataFrame(pairs)
T["f3 duplicado |ρ| > 0.95"] = T.variable.isin(drop)
T["pasa"] = ~T[["f1 casi constante", "f2 fuga", "f3 duplicado |ρ| > 0.95"]].any(axis=1)
save_table(T, "step01_screen")
save_table(PR, "step01_duplicate_pairs")
P = T[T.pasa].variable.tolist()
pd.DataFrame({"variable": P, "compuesto": [c in COMPOSITES for c in P], "signo": [T.set_index("variable").loc[c, "signo"] for c in P]}).to_csv(
    __import__("common").PROC / "step01_pool.csv", index=False)
FUN = pd.DataFrame([("candidatas", len(C)), ("− casi constantes", int(T["f1 casi constante"].sum())), ("− fuga", int(T["f2 fuga"].sum())),
                    ("− duplicados |ρ| > 0.95", int(T["f3 duplicado |ρ| > 0.95"].sum())), ("= pool", len(P))], columns=["etapa", "variables"])
save_table(FUN, "step01_funnel")

rep = f"""# Paso 1 · Conjunto de variables

## Objetivo
- Dejar un pool de candidatas crudas sin constantes, sin fuga y sin duplicados casi exactos.

## Método
- Casi constante: valor modal (con NaN) ≥ 99%; fuga: AUC > 0.85 o IV > 0.50 (univariado B heredado); duplicado:
  grupos con |ρ Spearman| > 0.95 en todos sus pares (enlace completo) ⟹ queda el de mayor IV (D1.1). NaN nativo; `cluster` categórica; compuestos incluidos (I-2).

## Código
- `src/step01_features.py` · `tests/test_step01.py` · `step01_screen.csv`, `step01_duplicate_pairs.csv`, `step01_funnel.csv`.

## Resultados

### Embudo [DATA]
{md_table(FUN)}

- Verificación: {len(C)} − {int(T['f1 casi constante'].sum())} − {int(T['f2 fuga'].sum())} − {int(T['f3 duplicado |ρ| > 0.95'].sum())} = {len(P)} (sin solapes entre filtros: {int(T[['f1 casi constante', 'f2 fuga', 'f3 duplicado |ρ| > 0.95']].sum(axis=1).max()) <= 1}) [DATA].

### Grupos de duplicados [DATA]
{md_table(PR, floatfmt=",.3f") if len(PR) else '- Ninguno.'}

### Cribado completo [DATA]
{md_table(T, floatfmt=",.3f")}

## Tests
- `tests/test_step01.py` (ver pytest).

## Decisiones y preguntas abiertas
- D1.1 en `reports/decision_log.md`.
"""
(REPORTS / "step01.md").write_text(rep, encoding="utf-8")
print(FUN.to_string(index=False)); print(PR.round(3).to_string(index=False)); print(T[~T.pasa][["variable", "modal %", "IV", "AUC univariada"]].round(3).to_string(index=False))
