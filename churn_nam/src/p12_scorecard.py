"""Fase 12 · Scorecard (target A) para EBM (champion) y NAM (challenger), escala de config.scorecard.

Score = Offset + Factor · ln(odds buenos) = Offset − Factor · logit(p churn); Factor = PDO/ln2, Offset = S0 − Factor·ln(O0).
- EBM (probabilidad sin calibrar, decisión del usuario): logit = β₀ + Σ f_j (bins del EBM); puntos_j = round(−Factor·f_j),
  base = round(Offset − Factor·β₀). Lookup exacto por bin (compactado uniendo bins consecutivos con los mismos puntos).
- NAM (Platt a, b de la fase 11): logit_cal = a + b·(β₀ + Σ f_j); f_j continua ⟹ bins = 20 cuantiles de train por
  variable (≤ 20 valores distintos: un bin por valor) (+ bin "falta"); puntos del bin = round(−Factor·b·media de f_j en el bin); base = round(Offset − Factor·(a + b·β₀)).
- Residual de completeness = score exacto del modelo − score del lookup (antes de recortar).
- Recorte a [score_min, score_max]; % recortados. Escala maestra por tasa observada en test (bandas de 20 puntos);
  A-lite con su propio score en test ∩ holdout de A-lite, misma escala.
"""
from __future__ import annotations

import json
import pickle
import warnings

import numpy as np
import pandas as pd

from config import P, need, set_seed
from report import render

warnings.filterwarnings("ignore")
set_seed()
pdo, s0, o0 = (need(f"scorecard.{k}", fase=12) for k in ("pdo", "s0", "o0"))
assert need("scorecard.odds_convention", fase=12) == "good:bad"
lo_s, hi_s = need("scorecard.score_min", fase=12), need("scorecard.score_max", fase=12)
FACTOR = pdo / np.log(2)
OFFSET = s0 - FACTOR * np.log(o0)
X = pd.read_parquet(P.processed / "X_features.parquet")
pop = pd.read_parquet(P.processed / "population.parquet")[["household_id", "segment", "y_A"]]
S = pd.read_parquet(P.processed / "splits.parquet")
F = [c for c in X.columns if c != "household_id"]
D = X.merge(pop, on="household_id").merge(S, on="household_id")
EBM = pickle.load(open(P.out(8) / "models.pkl", "rb"))[("A", "EBM monótono")]
NAM = pickle.load(open(P.out(9) / "nam_models.pkl", "rb"))["models"]["A"]
cal = json.load(open(P.out(11) / "calibrators.json"))["NAM monótono (challenger)"]
a, b = cal["a"], cal["b"]
TR = D[D.split == "train"].reset_index(drop=True)
out = P.out(12)

# ── EBM ──────────────────────────────────────────────────────────────────────────────────────────────────────
b0_e = float(EBM.intercept_[0])
BASE_E = int(round(OFFSET - FACTOR * b0_e))
look_e = []
for j, c in enumerate(F):
    cuts = np.asarray(EBM.bins_[j][0], float)
    sc = np.asarray(EBM.term_scores_[j], float)
    edges = np.concatenate([[-np.inf], cuts, [np.inf]])
    for i in range(len(cuts) + 1):
        look_e.append({"variable": c, "desde": edges[i], "hasta": edges[i + 1], "puntos": int(round(-FACTOR * sc[i + 1]))})
    look_e.append({"variable": c, "desde": "falta", "hasta": "", "puntos": int(round(-FACTOR * sc[0]))})
LE = pd.DataFrame(look_e)
CE = EBM.eval_terms(D[F])
PTS_E = np.round(-FACTOR * CE).astype(int)
score_e_lookup = BASE_E + PTS_E.sum(1)
score_e_exact = OFFSET - FACTOR * EBM.decision_function(D[F])


def compact(L):
    rows = []
    for c, g in L.groupby("variable", sort=False):
        num = g[g.desde != "falta"].reset_index(drop=True)
        st = 0
        for i in range(1, len(num) + 1):
            if i == len(num) or num.puntos[i] != num.puntos[st]:
                rows.append({"variable": c, "desde": num.desde[st], "hasta": num.hasta[i - 1], "puntos": int(num.puntos[st])})
                st = i
        m = g[g.desde == "falta"]
        if len(m):
            rows.append({"variable": c, "desde": "falta", "hasta": "", "puntos": int(m.puntos.iloc[0])})
    return pd.DataFrame(rows)


LEC = compact(LE)

# ── NAM ──────────────────────────────────────────────────────────────────────────────────────────────────────
b0_n = float(np.mean([m.bias.item() for m in NAM.models]))
BASE_N = int(round(OFFSET - FACTOR * (a + b * b0_n)))
C_tr = NAM.contributions(TR[F].to_numpy(float))
C_all = NAM.contributions(D[F].to_numpy(float))
look_n, PTS_N = [], np.zeros((len(D), len(F)), int)
for j, c in enumerate(F):
    x_tr, x_all = TR[c].to_numpy(float), D[c].to_numpy(float)
    vals = np.unique(x_tr[~np.isnan(x_tr)])
    if len(vals) <= 20:                                           # binarias / pocos valores: un bin por valor (cortes en puntos medios)
        inner = (vals[:-1] + vals[1:]) / 2
    else:
        edges = np.unique(np.nanquantile(x_tr, np.linspace(0, 1, 21)))
        inner = edges[1:-1]
    bin_tr = np.searchsorted(inner, x_tr, side="right")
    bin_all = np.searchsorted(inner, x_all, side="right")
    e_full = np.concatenate([[-np.inf], inner, [np.inf]])
    for k in range(len(inner) + 1):
        mk = (bin_tr == k) & ~np.isnan(x_tr)
        pts = int(round(-FACTOR * b * C_tr[mk, j].mean())) if mk.any() else 0
        look_n.append({"variable": c, "desde": e_full[k], "hasta": e_full[k + 1], "puntos": pts})
        PTS_N[(bin_all == k) & ~np.isnan(x_all), j] = pts
    miss = np.isnan(x_tr)
    pm = int(round(-FACTOR * b * C_tr[miss, j].mean())) if miss.any() else int(round(-FACTOR * b * float(np.mean([m.nets[j].b_miss.item() for m in NAM.models]))))
    look_n.append({"variable": c, "desde": "falta", "hasta": "", "puntos": pm})
    PTS_N[np.isnan(x_all), j] = pm
LN = pd.DataFrame(look_n)
LNC = compact(LN)
score_n_lookup = BASE_N + PTS_N.sum(1)
score_n_exact = OFFSET - FACTOR * (a + b * NAM.logit(D[F].to_numpy(float)))

# ── Recorte, completeness, escala maestra ───────────────────────────────────────────────────────────────────
res, SCO = [], pd.DataFrame({"household_id": D.household_id, "split": D.split, "test_alite": D.test_alite, "segment": D.segment, "y_A": D.y_A})
for name, sl, sx, base, L, LC in (("EBM", score_e_lookup, score_e_exact, BASE_E, LE, LEC), ("NAM", score_n_lookup, score_n_exact, BASE_N, LN, LNC)):
    r = sx - sl
    clipped = (sl < lo_s) | (sl > hi_s)
    SCO[f"score_{name}"] = np.clip(sl, lo_s, hi_s)
    SCO[f"p_{name}"] = 1 / (1 + np.exp((SCO[f"score_{name}"] - OFFSET) / FACTOR))
    res.append({"modelo": name, "base": base, "filas lookup": len(L), "filas lookup compacto": len(LC), "score mín (sin recorte)": int(sl.min()), "score máx (sin recorte)": int(sl.max()),
                "% recortados": 100 * clipped.mean(), "recortados": int(clipped.sum()), "residual completeness: media |r|": float(np.abs(r).mean()),
                "residual: p95 |r|": float(np.quantile(np.abs(r), 0.95)), "residual: máx |r|": float(np.abs(r).max()), "corr(score exacto, lookup)": float(np.corrcoef(sx, sl)[0, 1])})
    L.to_csv(out / f"lookup_{name}.csv", index=False)
    LC.to_csv(out / f"lookup_{name}_compact.csv", index=False)
RES = pd.DataFrame(res)
al = pd.read_csv(P.alite / "outputs" / "scored" / "scored_households.csv")[["household_id", "score_lite"]]
SCO = SCO.merge(al, on="household_id", how="left")
SCO.to_parquet(P.processed / "scores_p12.parquet", index=False)


def master(sc, y):
    band = (np.floor((sc - lo_s) / 20) * 20 + lo_s).astype(int)
    t = pd.DataFrame({"banda": band, "y": y}).groupby("banda").y.agg(["size", "sum"]).sort_index()
    t.columns = ["hogares", "eventos"]
    t["% hogares"] = 100 * t.hogares / t.hogares.sum()
    t["tasa observada %"] = 100 * t.eventos / t.hogares
    t["captura acumulada % (desde el peor score)"] = 100 * t.eventos.cumsum() / t.eventos.sum()
    t = t.reset_index()
    t["rango"] = t.banda.astype(str) + "–" + (t.banda + 19).astype(str)
    return t[["rango", "hogares", "% hogares", "eventos", "tasa observada %", "captura acumulada % (desde el peor score)"]]


te = SCO[SCO.split == "test"]
tf = SCO[(SCO.split == "test") & SCO.test_alite]
MS = {"EBM": master(te.score_EBM.to_numpy(), te.y_A.to_numpy()), "NAM": master(te.score_NAM.to_numpy(), te.y_A.to_numpy()),
      "A-lite (test ∩ holdout A-lite)": master(tf.score_lite.to_numpy(), tf.y_A.to_numpy())}
for k, v in MS.items():
    v.to_csv(out / f"master_scale_{k.split(' ')[0]}.csv", index=False)
RES.to_csv(out / "scorecard_summary.csv", index=False)
json.dump({"escala": {"S0": s0, "O0": o0, "PDO": pdo, "Factor": FACTOR, "Offset": OFFSET, "odds": "good:bad", "recorte": [lo_s, hi_s]},
           "calibración": {"EBM": "sin calibrar (decisión del usuario tras ver el test en la fase 11)", "NAM": {"Platt a": a, "Platt b": b}}},
          open(out / "scale.json", "w"), ensure_ascii=False, indent=1)
json.dump({"title": "Fase 12 · Scorecard (target A)", "order": ["scale.json", "scorecard_summary.csv", "master_scale_EBM.csv", "master_scale_NAM.csv", "master_scale_A-lite.csv",
                                                               "lookup_EBM_compact.csv", "lookup_NAM_compact.csv"],
           "notes": {"scorecard_summary.csv": "Residual de completeness = score exacto del modelo − score del lookup (redondeo en EBM; binning + redondeo en NAM).",
                     "master_scale_EBM.csv": "Tasa observada en test por banda de 20 puntos; score alto = menos churn."}}, open(out / "_meta.json", "w"), ensure_ascii=False)
render(12)
print(RES.round(3).to_string(index=False))
for k, v in MS.items():
    print(k); print(v.round(2).to_string(index=False))
