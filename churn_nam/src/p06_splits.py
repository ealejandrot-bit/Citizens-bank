"""Fase 6 · Diseño de validación (el test se define aquí y no se abre hasta la fase 10).

- test = val heredado de M1/M2 (5,842 hogares); dev heredado (13,631) → train + validación (validation_frac_of_dev),
  estratificado por clase (hard / soft ≥ θ / indeterminado / no evento) × segmento, semilla 42.
- test_alite = test ∩ holdout de A-lite (hogares fuera del desarrollo de A-lite): subconjunto justo para toda
  comparación contra A-lite congelado (comparison.alite_fair_subset).
- EPV (eventos por variable candidata) pooled y por segmento, targets A y B.
- Gate pre-registrado: se imprime tal cual queda en config.yaml, con sha256 del bloque y fecha.
Salidas: data/processed/splits.parquet (household_id, split, test_alite), outputs/p06/*.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

from config import CFG, P, SEED, get, need, set_seed
from report import render

set_seed()
frac = need("splits.validation_frac_of_dev", fase=6)
gate = {k: need(f"gate.{k}", fase=6) for k in ("delta_pr_auc", "delta_lift_at_5")}
pop = pd.read_parquet(P.processed / "population.parquet")
m1 = P.m1 / "data" / "processed"
dev_ids = set(pd.read_parquet(m1 / "dev.parquet").household_id)
test_ids = set(pd.read_parquet(m1 / "val.parquet").household_id)
al = pd.read_csv(P.alite / "outputs" / "tables" / "04_split.csv")[["household_id", "muestra"]]
alite_holdout = set(al.loc[al.muestra == "holdout", "household_id"])

pop["clase"] = pop.y_A.map({1: "hard"}).fillna(pop.indeterminado_B.map({True: "indet"})).fillna(pop.y_soft.map({1: "soft≥θ"})).fillna("no")
pop["estrato"] = pop.clase + "×" + pop.segment
dev = pop[pop.household_id.isin(dev_ids)].reset_index(drop=True)
tr_i, va_i = train_test_split(dev.index, test_size=frac, stratify=dev.estrato, random_state=SEED)
split = pd.Series("fuera", index=pop.index)
split[pop.household_id.isin(dev.household_id[tr_i])] = "train"
split[pop.household_id.isin(dev.household_id[va_i])] = "validation"
split[pop.household_id.isin(test_ids)] = "test"
S = pd.DataFrame({"household_id": pop.household_id, "split": split, "test_alite": pop.household_id.isin(test_ids) & pop.household_id.isin(alite_holdout)})
S.to_parquet(P.processed / "splits.parquet", index=False)

M = pop.merge(S, on="household_id")
rows = []
for sp in ["train", "validation", "test", "test ∩ holdout A-lite"]:
    g = M[M.test_alite] if sp.startswith("test ∩") else M[M.split == sp]
    for seg in ["total", "HNW", "UHNW"]:
        h = g if seg == "total" else g[g.segment == seg]
        b = h[~h.indeterminado_B]
        rows.append({"muestra": sp, "segmento": seg, "hogares": len(h), "eventos A": int(h.y_A.sum()), "tasa A %": 100 * h.y_A.mean(),
                     "hogares B": len(b), "eventos B": int(b.y_B.sum()), "tasa B %": 100 * b.y_B.mean()})
SZ = pd.DataFrame(rows)
n_feat = len(json.load(open(P.out(4) / "monotonicity_map.json")))
tr = SZ[SZ.muestra == "train"].set_index("segmento")
EPV = pd.DataFrame([{"segmento": s, "variables candidatas": n_feat, "eventos A train": int(tr.loc[s, "eventos A"]), "EPV A": tr.loc[s, "eventos A"] / n_feat,
                     "eventos B train": int(tr.loc[s, "eventos B"]), "EPV B": tr.loc[s, "eventos B"] / n_feat} for s in ["total", "HNW", "UHNW"]])
g_block = {"reference": get("gate.reference"), **gate, "bootstrap_reps": get("gate.bootstrap_reps"), "target principal": get("target.primary"),
           "subconjunto A-lite": "test ∩ holdout de A-lite" if get("comparison.alite_fair_subset") else "test completo"}
GATE = {"gate pre-registrado": g_block, "regla": "NAM reemplaza a A-lite solo si ΔPR-AUC ≥ delta_pr_auc y Δlift@5% ≥ delta_lift_at_5, con límite inferior del IC bootstrap pareado 95% > 0 en ambas, "
        "violación de monotonía = 0; UHNW solo reportado (enmienda del 2026-09-30)", "sha256 del bloque gate de config.yaml": hashlib.sha256(yaml.safe_dump(CFG["gate"], sort_keys=True).encode()).hexdigest(),
        "fecha de pre-registro (UTC)": "2026-09-29 23:52", "test abierto": False,
        "enmiendas": [{"fecha (UTC)": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), "cambio": "criterio UHNW pasa a solo reportado (gate.uhnw_criterion = report_only)",
                       "motivo": "7 eventos A en UHNW del subconjunto justo: el criterio no tiene potencia", "decisión": "usuario", "test abierto al enmendar": False}]}
out = P.out(6)
SZ.to_csv(out / "split_sizes.csv", index=False)
EPV.to_csv(out / "epv.csv", index=False)
json.dump(GATE, open(out / "gate_preregistered.json", "w"), ensure_ascii=False, indent=1)
json.dump({"title": "Fase 6 · Diseño de validación", "order": ["gate_preregistered.json", "split_sizes.csv", "epv.csv"],
           "notes": {"split_sizes.csv": "El test se cuenta aquí (tamaños y eventos) pero no se usa en ningún ajuste hasta la fase 10.",
                     "epv.csv": "EPV = eventos del train / variables candidatas (58)."}}, open(out / "_meta.json", "w"), ensure_ascii=False)
render(6)
print(json.dumps(GATE, ensure_ascii=False, indent=1)); print(SZ.round(2).to_string(index=False)); print(EPV.round(2).to_string(index=False))
