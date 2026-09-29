"""Paso 0 · Herencia y verificación (termina en G0).

- Copia (nunca mueve) a data/inherited/ los archivos de M1 listados en common.INHERIT, con sha256 de origen y destino.
- Registra el sha256 de los modelos de M1 (outputs/model/) y de scorecard/ para verificar en cada corrida que no cambian.
- Re-verifica en el archivo raw los hechos que usa el ML y en los heredados las cifras de la sección B del SPEC.
"""
from __future__ import annotations

import hashlib
import json
import shutil

import numpy as np
import pandas as pd

from common import COMPOSITES, INH, INHERIT, M1, RAW, REPORTS, ROOT, candidates, load_split, md_table, save_table, set_seed

set_seed()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731

INH.mkdir(parents=True, exist_ok=True)
rows = []
for src, dst in INHERIT:
    s, d = M1 / src, INH / dst
    shutil.copy2(s, d)
    rows.append({"origen (churn_scorecard/)": src, "destino (data/inherited/)": dst, "bytes": d.stat().st_size, "sha256": sha(d), "copia idéntica": sha(s) == sha(d)})
INV = pd.DataFrame(rows)
save_table(INV, "step00_inherited")

# Huella de los modelos anteriores (no se tocan; test en cada corrida)
prev = {}
for base in (M1 / "outputs" / "model", ROOT.parent / "scorecard" / "outputs"):
    for f in sorted(base.rglob("*")):
        if f.is_file() and f.suffix in (".pkl", ".json", ".csv", ".parquet"):
            prev[str(f.relative_to(ROOT.parent))] = sha(f)
(INH / "previous_models_sha256.json").write_text(json.dumps(prev, indent=2, ensure_ascii=False), encoding="utf-8")
PREV = pd.DataFrame({"archivo": list(prev), "sha256 (12)": [v[:12] for v in prev.values()]})
PREV["modelo"] = np.where(PREV.archivo.str.startswith("churn_scorecard"), "M1 · churn_scorecard (1.0.0)", "M1 previo · scorecard/")
save_table(PREV, "step00_previous_models")

# Verificación de hechos
cache = sorted((M1 / "data/processed").glob("raw_cache_*.parquet"))          # caché de lectura de M1 (mismo xlsx)
raw = pd.read_parquet(cache[0]) if cache else pd.read_excel(RAW, sheet_name="client_pulse_synthetic")
pop = pd.read_parquet(INH / "step01_population.parquet")
dev, val = load_split("dev"), load_split("val")
dB, vB = dev[dev.in_pop_B], val[val.in_pop_B]
m1g = pd.read_csv(INH / "m1_step13_global.csv").set_index("muestra")
m1cv = pd.read_csv(INH / "m1_step11A_cv_folds.csv")
F = []


def fact(h, esp, obs, ok):
    F.append({"hecho": h, "esperado (SPEC B)": esp, "observado [DATA]": obs, "coincide": bool(ok)})


fact("Filas / columnas raw", "20,000 / 62", f"{len(raw):,} / {raw.shape[1]}", raw.shape == (20000, 62))
fact("Target B: hogares / eventos / tasa", "19,261 / 2,674 / 13.88%", f"{int(pop.in_pop_B.sum()):,} / {int(pop.y_B.sum()):,} / {100 * pop.loc[pop.in_pop_B, 'y_B'].mean():.2f}%",
     (pop.in_pop_B.sum(), int(pop.y_B.sum())) == (19261, 2674))
fact("dev: hogares / B hogares / B eventos", "13,631 / 13,482 / 1,871", f"{len(dev):,} / {len(dB):,} / {int(dB.y_B.sum()):,}", (len(dev), len(dB), int(dB.y_B.sum())) == (13631, 13482, 1871))
fact("val: hogares / B hogares / B eventos", "5,842 / 5,779 / 803", f"{len(val):,} / {len(vB):,} / {int(vB.y_B.sum()):,}", (len(val), len(vB), int(vB.y_B.sum())) == (5842, 5779, 803))
fact("dev ∩ val", "0 hogares", f"{len(set(dev.household_id) & set(val.household_id))}", not (set(dev.household_id) & set(val.household_id)))
fact("Folds CV 5×5 en dev", "cv_r1..cv_r5 con 5 folds", ", ".join(str(dev[f'cv_r{r}'].nunique()) for r in range(1, 6)), all(dev[f"cv_r{r}"].nunique() == 5 for r in range(1, 6)))
fact("Campeón M1 · CV anidada Gini / PR-AUC", "0.429 / 0.344", f"{m1cv.Gini.mean():.3f} / {m1cv['PR-AUC'].mean():.3f}", round(m1cv.Gini.mean(), 3) == 0.429 and round(m1cv["PR-AUC"].mean(), 3) == 0.344)
fact("Campeón M1 · val Gini / PR-AUC", "0.390 / 0.328", f"{m1g.loc['val', 'Gini']:.3f} / {m1g.loc['val', 'PR-AUC']:.3f}", round(m1g.loc["val", "Gini"], 3) == 0.390 and round(m1g.loc["val", "PR-AUC"], 3) == 0.328)
na_inv = raw.loc[~raw.has_investments.astype(bool), "aum"].isna().all() and raw.loc[raw.has_investments.astype(bool), "aum"].notna().all()
fact("Missing estructural aum ⟺ sin inversiones", "exacto", "exacto" if na_inv else "no", na_inv)
cand = candidates()
bad = [c for c in cand if c in ("hard_churn_6m", "soft_churn_3m", "value_lost_6m", "churn_excluded", "age_primary", "bureau_new_mortgage_elsewhere")]
fact("Candidatas sin resultado / edad / buró", "0 prohibidas", f"{len(cand)} candidatas, {len(bad)} prohibidas", not bad)
fact("Copias heredadas idénticas", f"{len(INHERIT)} de {len(INHERIT)}", f"{int(INV['copia idéntica'].sum())} de {len(INV)}", INV["copia idéntica"].all())
FT = pd.DataFrame(F)
save_table(FT, "step00_facts")
CD = pd.DataFrame({"variable": cand, "compuesto": [c in COMPOSITES for c in cand]})
save_table(CD, "step00_candidates")

rep = f"""# Paso 0 · Herencia y verificación

## Objetivo
- Partir exactamente de los mismos datos, target, split y holdout que el Modelo 1, sin modificar nada del Modelo 1.

## Método
- Copia con sha256 de {len(INHERIT)} archivos de `churn_scorecard/` a `data/inherited/` (nunca se mueven ni se reescriben).
- Huella sha256 de {len(prev)} archivos de modelos anteriores (`churn_scorecard/outputs/model/` y `scorecard/outputs/`);
  un test verifica en cada corrida que no cambiaron (pedido del usuario: se usan para comparar).
- Verificación de los hechos de la sección B del SPEC en los datos heredados y en el raw.

## Código
- `src/step00_inherit.py` · `tests/test_step00.py` · `step00_inherited.csv`, `step00_previous_models.csv`, `step00_facts.csv`,
  `step00_candidates.csv`.

## Resultados

### Hechos verificados [DATA]
{md_table(FT)}

### Archivos heredados [DATA]
{md_table(INV.drop(columns='sha256'))}

### Modelos anteriores protegidos [DATA]
- {int((PREV.modelo.str.startswith('M1 ·')).sum())} archivos de `churn_scorecard/outputs/model/` y {int((PREV.modelo.str.startswith('M1 previo')).sum())} de `scorecard/outputs/`
  con su sha256 en `data/inherited/previous_models_sha256.json` (lista completa en `step00_previous_models.csv`).

### Candidatas [DATA]
- {len(cand)} variables: {len(cand) - len(COMPOSITES) - 1} de M1 + {len(COMPOSITES)} compuestos (I-2) + `cluster`.

## Tests
- `tests/test_step00.py` (ver pytest).

## Decisiones y preguntas abiertas
- D0.1–D0.2 y respuestas G0 en `reports/decision_log.md`.
"""
(REPORTS / "step00.md").write_text(rep, encoding="utf-8")
print(FT.to_string(index=False)); print(len(prev), "archivos protegidos")
