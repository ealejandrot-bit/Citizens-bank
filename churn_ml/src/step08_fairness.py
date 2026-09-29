"""Paso 8 · Equidad y uso responsable (diagnóstico; nada de esto entra al modelo). Dev.

- La edad (`age_primary`) y el buró no son entradas (G1-3 de M1). Prueba de proxy: ¿las 12 variables del modelo
  predicen la edad? AUC (CV 5 folds, GBM prof. 3) de separar el tercil de mayor edad del de menor edad.
- Tasa de Crítico y de Crítico+Alto por tercil de edad para EBM y M1, junto a la tasa de churn observada por tercil:
  la diferencia en marcado debe acompañar a la diferencia en churn real (ratio marcado / churn).
"""
from __future__ import annotations

import json
import warnings

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold

from common import ID, PROC, REPORTS, SCORES, SEED, load_split, md_table, save_table, set_seed

warnings.filterwarnings("ignore")
set_seed()
dev = load_split("dev")
D = dev[dev.in_pop_B].reset_index(drop=True)
V = json.loads((PROC / "step02_selected.json").read_text(encoding="utf-8"))["vars"]
D["tercil edad"] = pd.qcut(D.age_primary, 3, labels=["T1 (menor)", "T2", "T3 (mayor)"])
cuts = D.age_primary.quantile([1 / 3, 2 / 3]).to_numpy()

m = D["tercil edad"].isin(["T1 (menor)", "T3 (mayor)"]).to_numpy()
Xa, ya = D.loc[m, V], (D.loc[m, "tercil edad"] == "T3 (mayor)").astype(int).to_numpy()
pa = np.zeros(len(ya))
for tr, te in StratifiedKFold(5, shuffle=True, random_state=SEED).split(Xa, ya):
    pa[te] = xgb.XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, random_state=SEED, n_jobs=4).fit(Xa.iloc[tr], ya[tr]).predict_proba(Xa.iloc[te])[:, 1]
auc_proxy = roc_auc_score(ya, pa)
PX = pd.DataFrame([{"prueba": "predecir tercil mayor vs menor de edad con las 12 variables", "hogares": int(m.sum()), "AUC (CV 5)": auc_proxy,
                    "lectura": "sin proxy relevante" if auc_proxy < 0.60 else "proxy débil" if auc_proxy < 0.70 else "proxy fuerte: revisar"}])
save_table(PX, "step08_age_proxy")

O = pd.read_csv(SCORES / "household_scores_ml.csv")[[ID, "tramo_ebm", "tramo_m1"]]
D = D.merge(O, on=ID)
rows = []
for t in D["tercil edad"].cat.categories:
    g = D[D["tercil edad"] == t]
    r = {"tercil edad": t, "edad": f"{g.age_primary.min():.0f}–{g.age_primary.max():.0f}", "hogares": len(g), "tasa churn B %": 100 * g.y_B.mean()}
    for mod, col in (("EBM", "tramo_ebm"), ("M1", "tramo_m1")):
        r[f"% Crítico {mod}"] = 100 * (g[col] == "Crítico").mean()
        r[f"% Crítico+Alto {mod}"] = 100 * g[col].isin(["Crítico", "Alto"]).mean()
        r[f"ratio (Crítico+Alto / churn) {mod}"] = r[f"% Crítico+Alto {mod}"] / r["tasa churn B %"]
    rows.append(r)
AG = pd.DataFrame(rows)
save_table(AG, "step08_age_rates")
rng_ratio = {mod: AG[f"ratio (Crítico+Alto / churn) {mod}"].max() / AG[f"ratio (Crítico+Alto / churn) {mod}"].min() for mod in ("EBM", "M1")}

rep = f"""# Paso 8 · Equidad y uso responsable

## Objetivo
- Confirmar que el ML no reintroduce la edad por la puerta de atrás y que marca a los grupos de edad en proporción a
  su churn real. Solo diagnóstico: la edad nunca se usa para puntuar.

## Método
- Proxy: AUC de separar el tercil de mayor edad del de menor edad con las 12 variables (GBM, CV 5). Lectura [DEF-default
  D8.1]: < 0.60 sin proxy relevante; 0.60–0.70 débil; > 0.70 revisar.
- Marcado por tercil de edad (dev): % en Crítico y Crítico+Alto vs churn observado, EBM y M1.

## Código
- `src/step08_fairness.py` · `tests/test_step08.py` · `step08_*.csv`.

## Resultados

### Prueba de proxy [DATA]
{md_table(PX, floatfmt=",.3f")}

### Marcado por tercil de edad (dev) [DATA]
{md_table(AG, floatfmt=",.2f")}

- Dispersión del ratio marcado / churn entre terciles (máx / mín): EBM {rng_ratio['EBM']:.2f}, M1 {rng_ratio['M1']:.2f} [DATA].

## Tests
- `tests/test_step08.py` (ver pytest).

## Decisiones y preguntas abiertas
- D8.1 en `reports/decision_log.md`.
"""
(REPORTS / "step08.md").write_text(rep, encoding="utf-8")
print(PX.round(3).to_string(index=False)); print(AG.round(2).to_string(index=False)); print(rng_ratio)
