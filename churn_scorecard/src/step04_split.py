"""Paso 4 · Muestra (termina en G1).

Split 70/30 de la población A (19,473 = población B + 212 indeterminados), estratificado por clase (hard / soft con
pérdida ≥ θ / indeterminado / no evento) × segment, SEED = 42. Así dev/val quedan balanceados para B y para A.
RepeatedStratifiedKFold 5×5 dentro de dev con la misma estratificación (columnas cv_r1..cv_r5).
Sin OOT (un solo snapshot): limitación L1.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import RepeatedStratifiedKFold, train_test_split

from common import PROC, REPORTS, SEED, load_raw, md_table, save_table, set_seed

set_seed()
df = load_raw()
pop = pd.read_parquet(PROC / "step01_population.parquet")
X = df.merge(pop.drop(columns="segment"), on="household_id")
P = X[X.in_pop_A].reset_index(drop=True)
# 4 clases: hard (evento A y B) / soft ≥ θ (evento B, no A) / indeterminado / no evento → balancea A y B (D4.1)
cls = np.select([P.y_A == 1, P.y_B == 1, P.y_B_indet], ["hard", "soft_ge_theta", "indet"], "no_evento")
strata = pd.Series(cls) + "_" + P.segment
dev_i, val_i = train_test_split(np.arange(len(P)), test_size=0.30, stratify=strata, random_state=SEED)
P["partición"] = "dev"
P.loc[val_i, "partición"] = "val"

dev = P[P["partición"] == "dev"].reset_index(drop=True)
rskf = RepeatedStratifiedKFold(n_splits=5, n_repeats=5, random_state=SEED)
folds = np.full((len(dev), 5), -1)
st_dev = (pd.Series(cls)[P["partición"] == "dev"].reset_index(drop=True) + "_" + dev.segment)
for k, (_, te) in enumerate(rskf.split(dev, st_dev)):
    folds[te, k // 5] = k % 5
for r in range(5):
    dev[f"cv_r{r + 1}"] = folds[:, r]
val = P[P["partición"] == "val"].reset_index(drop=True)
dev.to_parquet(PROC / "dev.parquet", index=False)
val.to_parquet(PROC / "val.parquet", index=False)

rows = []
for part, g in (("dev", dev), ("val", val)):
    for s_ in ("Total", "HNW", "UHNW"):
        m = g if s_ == "Total" else g[g.segment == s_]
        b = m[m.in_pop_B]
        rows.append({"partición": part, "segmento": s_, "hogares (pobl. A)": len(m), "indeterminados B": int(m.y_B_indet.sum()),
                     "hogares B": len(b), "eventos B": int(b.y_B.sum()), "tasa B %": 100 * b.y_B.mean(),
                     "eventos A": int(m.y_A.sum()), "tasa A %": 100 * m.y_A.mean(), "% UHNW": 100 * (m.segment == "UHNW").mean(),
                     "% RV del total": 100 * m.relationship_value.sum() / P.relationship_value.sum()})
sp = pd.DataFrame(rows)
save_table(sp, "step04_split")
fr = []
for r in range(1, 6):
    g = dev.groupby(f"cv_r{r}")
    fr.append({"repetición": r, "hogares por fold": f"{g.size().min()}–{g.size().max()}",
               "eventos B por fold": f"{int(g.y_B.sum().min())}–{int(g.y_B.sum().max())}",
               "eventos A por fold": f"{int(g.y_A.sum().min())}–{int(g.y_A.sum().max())}",
               "eventos B UHNW por fold": f"{int(dev[dev.segment == 'UHNW'].groupby(f'cv_r{r}').y_B.sum().min())}–{int(dev[dev.segment == 'UHNW'].groupby(f'cv_r{r}').y_B.sum().max())}"})
fo = pd.DataFrame(fr)
save_table(fo, "step04_folds")

t = sp.set_index(["partición", "segmento"])
rep = f"""# Paso 4 · Muestra

## Objetivo
- Separar desarrollo (70%) y validación (30%) y fijar las particiones de la CV repetida.

## Método
- Población: 19,473 hogares (A) = 19,261 (B) + 212 indeterminados [DATA]. Estratos: clase (hard / soft ≥ θ /
  indeterminado / no evento) × `segment`; `train_test_split` 70/30, SEED = 42 [DEF]. Una fila por household ⟹ no hay
  agrupación. Estratificar solo por B desbalanceaba A (6.22% vs 5.48%) y se corrigió (D4.1).
- CV: RepeatedStratifiedKFold 5 × 5 dentro de dev, mismos estratos (`cv_r1`–`cv_r5` en `dev.parquet`).
- Sin OOT ni cohortes: limitación **L1**.

## Código
- `src/step04_split.py` · `tests/test_step04.py` · `data/processed/dev.parquet`, `val.parquet`.

## Resultados

### Particiones [DATA]
{md_table(sp, floatfmt=",.2f")}

- Verificación: dev + val = {int(t.loc[('dev', 'Total'), 'hogares (pobl. A)'] + t.loc[('val', 'Total'), 'hogares (pobl. A)']):,} = 19,473 [DATA];
  eventos B {int(t.loc[('dev', 'Total'), 'eventos B'])} + {int(t.loc[('val', 'Total'), 'eventos B'])} = {int(t.loc[('dev', 'Total'), 'eventos B'] + t.loc[('val', 'Total'), 'eventos B']):,} = 2,674 [DATA];
  eventos A {int(t.loc[('dev', 'Total'), 'eventos A'])} + {int(t.loc[('val', 'Total'), 'eventos A'])} = 1,168 [DATA].
- Tasa B dev vs val: {t.loc[('dev', 'Total'), 'tasa B %']:.2f}% vs {t.loc[('val', 'Total'), 'tasa B %']:.2f}%; tasa A {t.loc[('dev', 'Total'), 'tasa A %']:.2f}% vs
  {t.loc[('val', 'Total'), 'tasa A %']:.2f}% [DATA]. La RV no se estratificó (colas reales, paso 3).
- Régimen (SPEC H, tabla 1): eventos B en dev = {int(t.loc[('dev', 'Total'), 'eventos B']):,} > 300 ⟹ logística sobre WoE + challenger ML [DATA].
- UHNW en val: {int(t.loc[('val', 'UHNW'), 'eventos B'])} eventos B y {int(t.loc[('val', 'UHNW'), 'eventos A'])} eventos A [DATA] → métricas UHNW con IC anchos.

### Folds de la CV 5 × 5 en dev [DATA]
{md_table(fo)}

## Tests
- `tests/test_step04.py` (ver pytest).

## Decisiones y preguntas abiertas
- D4.1 y limitación L1 en `reports/decision_log.md`; preguntas de G1 en `reports/gate_1.md`.
"""
(REPORTS / "step04.md").write_text(rep, encoding="utf-8")
print(sp.round(2).to_string(index=False)); print(fo.to_string(index=False))
