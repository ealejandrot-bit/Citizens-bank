"""Fase 1 · Target y población.

- Exclusiones de config.target (heredadas de M1): churn_excluded; tenure_years < exclude_tenure_lt. Conteo exacto por
  regla, secuencial (cada regla sobre lo que queda) y por separado (cuántos cumple cada regla sin importar el orden).
- Tasas por segmento tras exclusiones: hard (A), soft, any_churn (hard ∪ soft) y B (hard ∪ soft con pérdida ≥ θ; soft
  con pérdida < θ = indeterminado, fuera del denominador de B).
- data/processed/population.parquet: household_id, segment, población, y_A, y_soft, y_any, y_B (NaN si indeterminado).
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from config import P, get, need, set_seed
from report import render

set_seed()
df = pd.read_excel(P.raw, sheet_name=get("paths.sheet"))
theta = need("target.theta", fase=1)
excl_ce = need("target.exclude_churn_excluded", fase=1)
t_min = need("target.exclude_tenure_lt", fase=1)
N = len(df)
r1 = df.churn_excluded.astype(bool) if excl_ce else pd.Series(False, index=df.index)
r2 = df.tenure_years < t_min
EX = pd.DataFrame([
    {"regla": "churn_excluded = True", "cumplen (independiente)": int(r1.sum()), "salen (secuencial)": int(r1.sum()), "quedan": int(N - r1.sum())},
    {"regla": f"tenure_years < {t_min:g}", "cumplen (independiente)": int(r2.sum()), "salen (secuencial)": int((r2 & ~r1).sum()), "quedan": int(N - (r1 | r2).sum())},
])
EX["solape con reglas previas"] = [0, int((r1 & r2).sum())]
pop = df[~(r1 | r2)].copy()
hard, soft = pop.hard_churn_6m == 1, pop.soft_churn_3m == 1
loss = pop.value_lost_6m / pop.relationship_value
indet = soft & (loss < theta)
out_pop = pd.DataFrame({"household_id": pop.household_id, "segment": pop.segment, "y_A": hard.astype(int), "y_soft": soft.astype(int),
                        "y_any": (hard | soft).astype(int), "y_B": np.where(indet, np.nan, (hard | (soft & (loss >= theta))).astype(float)), "indeterminado_B": indet})
P.processed.mkdir(parents=True, exist_ok=True)
out_pop.to_parquet(P.processed / "population.parquet", index=False)

rows = []
for s, g in list(out_pop.groupby("segment")) + [("total", out_pop)]:
    b = g[~g.indeterminado_B]
    rows.append({"segmento": s, "hogares": len(g), "hard (A) n": int(g.y_A.sum()), "hard %": 100 * g.y_A.mean(), "soft n": int(g.y_soft.sum()),
                 "soft %": 100 * g.y_soft.mean(), "any_churn n": int(g.y_any.sum()), "any_churn %": 100 * g.y_any.mean(),
                 "B hogares (sin indeterminados)": len(b), "B n": int(b.y_B.sum()), "B %": 100 * b.y_B.mean(), "indeterminados B": int(g.indeterminado_B.sum())})
RT = pd.DataFrame(rows)
out = P.out(1)
EX.to_csv(out / "exclusions.csv", index=False)
RT.to_csv(out / "rates_by_segment.csv", index=False)
tot = RT.set_index("segmento").loc["total"]
chk = {"población tras exclusiones": int(len(out_pop)), "Σ hogares por segmento = total": bool(RT.hogares.iloc[:-1].sum() == len(out_pop)),
       "any_churn = hard + soft (disjuntos)": bool(tot["any_churn n"] == tot["hard (A) n"] + tot["soft n"]),
       "coincide con M1 (B 19,261 hogares / 2,674 eventos; A 19,473 / 1,168)": bool((int(tot["B hogares (sin indeterminados)"]), int(tot["B n"]), len(out_pop), int(tot["hard (A) n"])) == (19261, 2674, 19473, 1168)),
       "θ (pérdida mínima de soft para B)": theta}
json.dump(chk, open(out / "checks.json", "w"), ensure_ascii=False)
json.dump({"title": "Fase 1 · Target y población", "order": ["exclusions.csv", "rates_by_segment.csv", "checks.json"],
           "notes": {"exclusions.csv": "secuencial = cada regla sobre lo que queda tras las anteriores.",
                     "rates_by_segment.csv": "B excluye del denominador a los soft con pérdida < θ (indeterminados)."}}, open(out / "_meta.json", "w"), ensure_ascii=False)
print(render(1)); print(EX.to_string(index=False)); print(RT.round(2).to_string(index=False)); print(chk)
