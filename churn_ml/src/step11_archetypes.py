"""Paso 11 · Arquetipos y acción: qué agrega el ML por arquetipo (val, eventos B).

- Arquetipos del M1 (`churn_scorecard/outputs/model/step16_archetypes.pkl`, K = 3) cargados en solo lectura y asignados
  a los eventos de val sin reajuste (WoE con los bins del paso 9 del M1).
- Por arquetipo: % de eventos que cada modelo pone en Crítico / Crítico+Alto y probabilidad media asignada (M1, EBM;
  A-lite en el subconjunto justo). Foco en "desgaste silencioso" (punto débil del M1: 21% de sus eventos en Estable).
"""
from __future__ import annotations

import hashlib
import pickle
import sys

import numpy as np
import pandas as pd

from common import ID, INH, M1, REPORTS, SCORES, load_split, md_table, save_table, set_seed

set_seed()
sys.path.insert(0, str(M1 / "src"))                       # clases de binning del M1 para deserializar (solo lectura)
from woe import woe_frame  # noqa: E402

ARQ_P, BIN_P = M1 / "outputs/model/step16_archetypes.pkl", M1 / "outputs/model/step09_binning.pkl"
h0 = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (ARQ_P, BIN_P)]
ARQ, B9 = pickle.load(open(ARQ_P, "rb")), pickle.load(open(BIN_P, "rb"))
NAMES = {0: "relación desatendida", 1: "salida activa a competidor", 2: "desgaste silencioso"}      # paso 16 del M1

val = load_split("val")
ev = val[val.in_pop_B & (val.y_B == 1)].reset_index(drop=True)
Z = ARQ["scaler"].transform(-woe_frame(ev, B9, ARQ["signals"]))
ev["arquetipo"] = pd.Series(ARQ["kmeans"].predict(Z)).map(NAMES)
assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in (ARQ_P, BIN_P)] == h0      # el M1 no cambió

O = pd.read_csv(SCORES / "household_scores_ml.csv")[[ID, "tramo_ebm", "p_ebm_calibrada", "tramo_m1", "p_m1_calibrada"]]
A = pd.read_csv(INH / "alite_scored_households.csv")[[ID, "tramo_lite", "probabilidad_lite"]]
SPL = pd.read_csv(INH / "alite_split.csv")[[ID, "muestra"]]
ev = ev.merge(O, on=ID).merge(A, on=ID).merge(SPL, on=ID, how="left")
rows = []
for a in NAMES.values():
    g = ev[ev.arquetipo == a]
    f = g[g.muestra == "holdout"]
    rows.append({"arquetipo": a, "eventos val": len(g), "% eventos": 100 * len(g) / len(ev),
                 "% en Crítico · M1": 100 * (g.tramo_m1 == "Crítico").mean(), "% en Crítico · EBM": 100 * (g.tramo_ebm == "Crítico").mean(),
                 "% en Crítico+Alto · M1": 100 * g.tramo_m1.isin(["Crítico", "Alto"]).mean(), "% en Crítico+Alto · EBM": 100 * g.tramo_ebm.isin(["Crítico", "Alto"]).mean(),
                 "% en Estable · M1": 100 * (g.tramo_m1 == "Estable").mean(), "% en Estable · EBM": 100 * (g.tramo_ebm == "Estable").mean(),
                 "p media % · M1": 100 * g.p_m1_calibrada.mean(), "p media % · EBM": 100 * g.p_ebm_calibrada.mean(),
                 "eventos justos (A-lite)": len(f), "% en Crítico+Alto · A-lite (justo)": 100 * f.tramo_lite.isin(["Crítico", "Alto"]).mean() if len(f) else np.nan,
                 "% en Crítico+Alto · M1 (justo)": 100 * f.tramo_m1.isin(["Crítico", "Alto"]).mean() if len(f) else np.nan,
                 "% en Crítico+Alto · EBM (justo)": 100 * f.tramo_ebm.isin(["Crítico", "Alto"]).mean() if len(f) else np.nan})
AR = pd.DataFrame(rows)
AR["Δ Crítico+Alto EBM − M1 (pp)"] = AR["% en Crítico+Alto · EBM"] - AR["% en Crítico+Alto · M1"]
save_table(AR, "step11_archetypes")
def change(a):
    r = AR.set_index("arquetipo").loc[a]
    d = r["Δ Crítico+Alto EBM − M1 (pp)"]
    return (f"el EBM marca {abs(d):.1f} pp {'más' if d > 0 else 'menos'} de estos eventos en Crítico+Alto que el M1 "
            f"(el EBM marca {100 * share_e:.1f}% de hogares en Crítico+Alto vs {100 * share_m:.1f}% del M1): sin ventaja; se mantiene la acción del M1")


O2 = pd.read_csv(SCORES / "household_scores_ml.csv").merge(val[[ID, "in_pop_B"]], on=ID)
O2 = O2[O2.in_pop_B]
share_e, share_m = O2.tramo_ebm.isin(["Crítico", "Alto"]).mean(), O2.tramo_m1.isin(["Crítico", "Alto"]).mean()
ACT = pd.DataFrame([(a, act, change(a)) for a, act in (
    ("relación desatendida", "reactivar la relación: reunión del banquero y plan de contacto"),
    ("salida activa a competidor", "retención inmediata con líder + banquero"),
    ("desgaste silencioso", "revisión proactiva ligera de portafolio y rendimiento; punto ciego común a los modelos (L6, L7)"))],
    columns=["arquetipo", "acción (playbook M1)", "qué cambia con el ML [DATA]"])
save_table(ACT, "step11_actions")

sil = AR.set_index("arquetipo").loc["desgaste silencioso"]
rep = f"""# Paso 11 · Arquetipos y acción

## Objetivo
- Ver, por tipo de cliente que se va, si el ML detecta mejor que el M1 (en especial el "desgaste silencioso").

## Método
- Arquetipos del M1 (K = 3) asignados sin reajuste a los {len(ev)} eventos B de val; archivos del M1 leídos en solo
  lectura (sha256 verificado antes y después). A-lite en el subconjunto justo.

## Código
- `src/step11_archetypes.py` · `tests/test_step11.py` · `step11_*.csv`.

## Resultados

### Detección por arquetipo (eventos B de val) [DATA]
{md_table(AR, floatfmt=",.1f")}

- Verificación: % eventos suma {AR['% eventos'].sum():.1f}% [DATA].
- Desgaste silencioso: Crítico+Alto M1 {sil['% en Crítico+Alto · M1']:.1f}% vs EBM {sil['% en Crítico+Alto · EBM']:.1f}%; en Estable M1 {sil['% en Estable · M1']:.1f}% vs EBM {sil['% en Estable · EBM']:.1f}% [DATA].

### Acción por arquetipo
{md_table(ACT)}

## Tests
- `tests/test_step11.py` (ver pytest).

## Decisiones y preguntas abiertas
- D11.1 en `reports/decision_log.md`.
"""
(REPORTS / "step11.md").write_text(rep, encoding="utf-8")
print(AR.round(1).T.to_string())
