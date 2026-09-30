"""Datos del reporte ejecutivo (4 diapositivas). Solo lee modelos y salidas ya congelados; no reentrena nada salvo los
benchmarks sin pesos (XGBoost, LightGBM), con el mismo código y semilla de la fase 10 (se verifica que reproducen su
PR-AUC en test).

Salidas en outputs/final/:
- deck_variables.csv: las variables de la base (diccionario del M1, paso 2) con unidad, rango, % missing, bloque,
  dirección esperada y qué modelo usa cada una (A-lite, M1, M2 EBM, M3).
- deck_archetypes.csv: arquetipos del M1 (K = 3, solo lectura) asignados a los eventos del test justo
  (test ∩ holdout de A-lite); por arquetipo y modelo, % de eventos capturados en el 10% de hogares con mayor riesgo
  según cada modelo (misma capacidad para todos).
- deck_archetypes_meta.json: tamaños, capacidad y verificación de reproducción.
"""
from __future__ import annotations

import hashlib
import json
import pickle
import sys
import warnings

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split

from config import P, SEED, set_seed

warnings.filterwarnings("ignore")
set_seed()
out = P.out(0).parent / "final"
out.mkdir(exist_ok=True)
CAP = 0.10                                                     # capacidad común: 10% de hogares con mayor riesgo
M1, M2, AL = P.m1, P.m2, P.alite

# ── 1 · Variables ────────────────────────────────────────────────────────────────────────────────────────────
DIC = pd.read_csv(M1 / "outputs/tables/step02_dictionary.csv")
alite = pd.read_csv(AL / "outputs/tables/11_modelAlite_coefficients.csv").variable.tolist()[1:]
m1v = pd.read_csv(M1 / "outputs/tables/step11A_coefficients.csv").variable.tolist()[1:]
m2v = pd.read_csv(M2 / "outputs/tables/step04_importance.csv").variable.tolist()
m3v = [c for c in pd.read_parquet(P.processed / "X_features.parquet").columns if c != "household_id"]
m3v = ["segment" if c == "segment_uhnw" else c for c in m3v]
V = DIC[["columna", "tipo", "unidad", "% missing [DATA]", "rango [DATA]", "significado de negocio", "bloque", "dirección esperada", "uso"]].copy()
V["A-lite"], V["M1"], V["M2 EBM"], V["M3"] = (V.columna.isin(s) for s in (alite, m1v, m2v, m3v))
reg = ["age_primary", "bureau_new_mortgage_elsewhere"]
V["estado"] = np.select([V.uso.str.startswith("prohibido") | V.bloque.eq("resultado"), V.columna.isin(reg), V.bloque.eq("compuesto")],
                        ["resultado / id (nunca predictor)", "excluida (regulatorio)", "excluida (compuesta, regla no documentada)"], "predictor")
V.to_csv(out / "deck_variables.csv", index=False)
derived_m1 = [v for v in m1v if v not in set(DIC.columna)]
miss_m3 = [v for v in m3v if v.startswith("miss_")]

# ── 2 · Arquetipos por modelo ────────────────────────────────────────────────────────────────────────────────
sys.path.insert(0, str(M2 / "src"))
from common import load_split  # noqa: E402  (M2, solo lectura: val del M1/M2 = test del M3)
sys.path.insert(0, str(M1 / "src"))
from woe import woe_frame  # noqa: E402

ARQ_P, BIN_P = M1 / "outputs/model/step16_archetypes.pkl", M1 / "outputs/model/step09_binning.pkl"
h0 = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (ARQ_P, BIN_P)]
ARQ, B9 = pickle.load(open(ARQ_P, "rb")), pickle.load(open(BIN_P, "rb"))
NAMES = {0: "relación desatendida", 1: "salida activa a competidor", 2: "desgaste silencioso"}      # paso 16 del M1

X = pd.read_parquet(P.processed / "X_features.parquet")
pop = pd.read_parquet(P.processed / "population.parquet")[["household_id", "y_A", "y_B"]]
S = pd.read_parquet(P.processed / "splits.parquet")
F = [c for c in X.columns if c != "household_id"]
D = X.merge(pop, on="household_id").merge(S, on="household_id")
TR, TE = D[D.split == "train"].reset_index(drop=True), D[D.split == "test"].reset_index(drop=True)

PR = pd.DataFrame({"household_id": TE.household_id})
PR = PR.merge(pd.read_csv(AL / "outputs/scored/scored_households.csv")[["household_id", "probabilidad_lite"]].rename(columns={"probabilidad_lite": "A-lite"}), on="household_id", how="left")
PR = PR.merge(pd.read_csv(M1 / "outputs/scores/household_scores.csv")[["household_id", "probabilidad_calibrada"]].rename(columns={"probabilidad_calibrada": "Scorecard M1"}), on="household_id", how="left")
PR = PR.merge(pd.read_csv(M2 / "outputs/scores/household_scores_ml.csv")[["household_id", "p_ebm_calibrada"]].rename(columns={"p_ebm_calibrada": "EBM M2"}), on="household_id", how="left")
CH = pickle.load(open(P.out(8) / "models.pkl", "rb"))
NAM = pickle.load(open(P.out(9) / "nam_models.pkl", "rb"))["models"]
PR["EBM M3"] = CH[("A", "EBM monótono")].predict_proba(TE[F])[:, 1]
PR["Red neuronal NAM"] = NAM["A"].predict_proba(TE[F].to_numpy(float))
tr = TR[TR.y_A.notna()]
a, b, ya, yb = train_test_split(tr[F], tr.y_A.astype(int), test_size=0.15, stratify=tr.y_A.astype(int), random_state=SEED)   # como la fase 10
xg = xgb.XGBClassifier(n_estimators=2000, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, min_child_weight=5, tree_method="hist",
                       eval_metric="aucpr", early_stopping_rounds=100, random_state=SEED, n_jobs=4).fit(a, ya, eval_set=[(b, yb)], verbose=False)
PR["XGBoost"] = xg.predict_proba(TE[F])[:, 1]
lg = lgb.LGBMClassifier(n_estimators=2000, max_depth=3, num_leaves=8, learning_rate=0.05, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, min_child_weight=5,
                        metric="average_precision", random_state=SEED, n_jobs=4, verbose=-1)
lg.fit(a, ya, eval_set=[(b, yb)], callbacks=[lgb.early_stopping(100, first_metric_only=True, verbose=False)])
PR["LightGBM"] = lg.predict_proba(TE[F])[:, 1]
MODELS = ["A-lite", "Scorecard M1", "EBM M2", "LightGBM", "XGBoost", "EBM M3", "Red neuronal NAM"]

# verificación: PR-AUC A en test completo igual a la fase 10 (modelos del M3)
REF = pd.read_csv(P.out(10) / "test_metrics_all.csv")
chk = {}
ya_te = TE.y_A.notna()
for m in ("EBM M3", "Red neuronal NAM", "XGBoost", "LightGBM"):
    chk[m] = float(average_precision_score(TE.y_A[ya_te].astype(int), PR[m][ya_te.to_numpy()]))
R = REF[(REF.target == "A") & (REF.subconjunto == "test completo") & (REF.segmento == "pooled")].set_index("modelo")["PR-AUC"]
for m, ref in (("EBM M3", "EBM monótono (champion)"), ("Red neuronal NAM", "NAM monótono"), ("XGBoost", "XGBoost"), ("LightGBM", "LightGBM")):
    assert np.isclose(chk[m], R[ref], atol=1e-9), (m, chk[m], R[ref])                  # mismos scores que la fase 10
json.dump(chk, open(out / "deck_reproduction_check.json", "w"), ensure_ascii=False, indent=1)

# arquetipos sobre los eventos B del test (= val del M1/M2), como el paso 11 del M2
val = load_split("val")
ev = val[val.in_pop_B & (val.y_B == 1)].reset_index(drop=True)
Z = ARQ["scaler"].transform(-woe_frame(ev, B9, ARQ["signals"]))
ev["arquetipo"] = pd.Series(ARQ["kmeans"].predict(Z)).map(NAMES)
assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in (ARQ_P, BIN_P)] == h0          # el M1 no cambió

FAIR = TE[TE.test_alite].household_id
G = PR[PR.household_id.isin(FAIR)].reset_index(drop=True)
assert G[MODELS].notna().all().all()
k = int(round(CAP * len(G)))
TOP = {m: set(G.household_id.iloc[np.argsort(-G[m].to_numpy(), kind="stable")[:k]]) for m in MODELS}
E = ev[ev.household_id.isin(FAIR)][["household_id", "arquetipo"]].merge(TE[["household_id", "y_A"]], on="household_id")
rows = []
for arq in list(NAMES.values()) + ["total"]:
    g = E if arq == "total" else E[E.arquetipo == arq]
    r = {"arquetipo": arq, "eventos B": len(g), "% de eventos B": 100 * len(g) / len(E), "de ellos hard (A)": int((g.y_A == 1).sum())}
    for m in MODELS:
        r[m] = 100 * g.household_id.isin(TOP[m]).mean()
    rows.append(r)
AR = pd.DataFrame(rows)
AR.to_csv(out / "deck_archetypes.csv", index=False)
json.dump({"subconjunto": "test ∩ holdout de A-lite", "hogares": len(G), "capacidad": CAP, "hogares marcados por modelo": k, "eventos B": len(E),
           "target de cada modelo": {"A-lite": "A", "Scorecard M1": "B", "EBM M2": "B", "LightGBM": "A", "XGBoost": "A", "EBM M3": "A", "Red neuronal NAM": "A"},
           "M1 derivadas": derived_m1, "M3 indicadores de missing": miss_m3,
           "n variables": {"A-lite": len(alite), "M1": len(m1v), "M2 EBM": len(m2v), "M3": len(m3v)}},
          open(out / "deck_archetypes_meta.json", "w"), ensure_ascii=False, indent=1)
print(AR.round(1).to_string(index=False))
print("reproducción fase 10 OK:", chk)
