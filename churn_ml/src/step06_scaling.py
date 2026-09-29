"""Paso 6 · Escalamiento PDO, tramos, overrides y salida por household (termina en G2).

- EBM (principal): logit calibrado = a + b·(intercepto + Σ f_j) (Platt, paso 5). Puntos_j = round(−Factor·b·f_j(x_j))
  (tabla por bin, exacta); base = round(Offset − Factor·(a + b·intercepto)); score = base + Σ puntos (assert por fila);
  probabilidad publicada = la del score. Drivers = top 3 variables con más puntos en contra (puntos más negativos).
- XGBoost (segundo): score = round(Offset − Factor·logit p_cal); sin lookup (reason codes por SHAP en el paso 4).
- Tramos (H-3, en dev): grilla de percentiles 1%; saltos ≥ 2x / 2x / 1.5x, lift Crítico/Estable ≥ 5x, ≥ 70 eventos por
  tramo en dev; mayor IV de tramo (misma regla que M1). Vista a igual % de hogares por tramo que M1 (I-6).
- Overrides: las 3 reglas activas del M1 re-evaluadas (≥ 25% Crítico, 12–25% Alto, ≤ 30% del tramo destino).
"""
from __future__ import annotations

import itertools
import json
import pickle
import warnings

import numpy as np
import pandas as pd
import xgboost as xgb

from common import FACTOR, ID, INH, MODEL, OFFSET, PROC, REPORTS, SCORES, md_table, save_table, set_seed

warnings.filterwarnings("ignore")
set_seed()
S = json.loads((PROC / "step02_selected.json").read_text(encoding="utf-8"))
V = S["vars"]
E = pickle.load(open(MODEL / "step04_ebm.pkl", "rb"))
M = xgb.XGBClassifier()
M.load_model(str(MODEL / "step04_xgb.json"))
CAL = pickle.load(open(MODEL / "step05_calibrators.pkl", "rb"))
assert CAL["EBM"]["method"] == "platt", "el lookup exacto requiere Platt"
TR = ["Crítico", "Alto", "Vigilancia", "Estable"]

F = pd.read_parquet(INH / "features.parquet").merge(pd.read_parquet(INH / "step07_clusters.parquet"), on=ID)
pop = pd.read_parquet(INH / "step01_population.parquet")[[ID, "excl_reason", "in_pop_B", "y_B", "y_B_indet"]]
part = pd.concat([pd.read_parquet(INH / f"{p}.parquet", columns=[ID]).assign(partición=p) for p in ("dev", "val")])
F = F.merge(pop, on=ID).merge(part, on=ID, how="left")
F["partición"] = F["partición"].fillna("fuera de desarrollo")
M1 = pd.read_csv(INH / "m1_household_scores.csv")[[ID, "score", "probabilidad_calibrada", "tramo", "tramo_modelo"]].rename(
    columns={"score": "score_m1", "probabilidad_calibrada": "p_m1", "tramo": "tramo_m1", "tramo_modelo": "tramo_m1_modelo"})
F = F.merge(M1, on=ID, how="left")
X = F[V]

# ── EBM: puntos ──────────────────────────────────────────────────────────────────────────────────────────────
a, b = CAL["EBM"]["a"], CAL["EBM"]["b"]
C = E.eval_terms(X)
BASE = int(round(OFFSET - FACTOR * (a + b * E.intercept_[0])))
PTS = np.round(-FACTOR * b * C).astype(int)
F["score"] = BASE + PTS.sum(1)
F["probabilidad"] = 1 / (1 + np.exp((F.score - OFFSET) / FACTOR))
exact = 1 / (1 + np.exp(-(a + b * E.decision_function(X))))
look = []
for j, c in enumerate(V):
    cuts = np.asarray(E.bins_[j][0], float)
    sc = np.asarray(E.term_scores_[j], float)
    edges = np.concatenate([[-np.inf], cuts, [np.inf]])
    for i in range(len(cuts) + 1):
        look.append({"variable": c, "bin": f"[{edges[i]:.6g}, {edges[i + 1]:.6g})", "f(x) log-odds": sc[i + 1], "puntos": int(round(-FACTOR * b * sc[i + 1]))})
    look.append({"variable": c, "bin": "missing", "f(x) log-odds": sc[0], "puntos": int(round(-FACTOR * b * sc[0]))})
LK = pd.DataFrame(look)
save_table(LK, "step06_lookup")
# Lookup compacto: bins consecutivos con los mismos puntos se unen (mismo score; tabla legible, D6.3)
comp = []
for c in V:
    t = LK[(LK.variable == c) & (LK.bin != "missing")].reset_index(drop=True)
    lo = t.bin.str.extract(r"\[(.*),")[0]
    hi = t.bin.str.extract(r", (.*)\)")[0]
    start = 0
    for i in range(1, len(t) + 1):
        if i == len(t) or t.puntos[i] != t.puntos[start]:
            comp.append({"variable": c, "desde": lo[start], "hasta": hi[i - 1], "puntos": int(t.puntos[start]), "bins EBM unidos": i - start})
            start = i
    mrow = LK[(LK.variable == c) & (LK.bin == "missing")].iloc[0]
    comp.append({"variable": c, "desde": "missing", "hasta": "", "puntos": int(mrow.puntos), "bins EBM unidos": 1})
LKC = pd.DataFrame(comp)
save_table(LKC, "step06_lookup_compact")
order = np.argsort(PTS, axis=1)                                     # más negativos primero
for i in range(3):
    F[f"driver_{i + 1}"] = [V[j] if PTS[r, j] < 0 else "" for r, j in enumerate(order[:, i])]
    F[f"driver_{i + 1}_puntos"] = [int(PTS[r, j]) if PTS[r, j] < 0 else 0 for r, j in enumerate(order[:, i])]

# ── XGBoost: score ───────────────────────────────────────────────────────────────────────────────────────────
dev_y = F.loc[(F["partición"] == "dev") & F.in_pop_B, "y_B"]
SPW = (dev_y == 0).sum() / dev_y.sum()
xm = M.predict(X, output_margin=True) - np.log(SPW)
ax_, bx_ = CAL["XGBoost"]["a"], CAL["XGBoost"]["b"]
px = CAL["XGBoost"]["isotonic"].predict(xm) if CAL["XGBoost"]["method"] == "isotonic" else 1 / (1 + np.exp(-(ax_ + bx_ * xm)))
F["score_xgb"] = np.round(OFFSET - FACTOR * np.log(px / (1 - px))).astype(int)
F["p_xgb"] = 1 / (1 + np.exp((F.score_xgb - OFFSET) / FACTOR))

# ── Tramos ───────────────────────────────────────────────────────────────────────────────────────────────────
isdev = ((F["partición"] == "dev") & F.in_pop_B).to_numpy()
yd = F.y_B[isdev].astype(int).to_numpy()
MIN_EV = int(np.ceil(30 * 1871 / 803))


def woe_iv(g, b_):
    pg, pb = g / g.sum(), b_ / b_.sum()
    return ((pg - pb) * np.log(pg / pb)).sum()


def search(score_dev):
    q = pd.Series(score_dev).rank(pct=True, method="first").to_numpy()
    best, n_ok = None, 0
    for A_, B_, C_ in itertools.product(range(1, 16), range(5, 51), range(15, 81)):
        if not A_ < B_ < C_:
            continue
        g = np.select([q <= A_ / 100, q <= B_ / 100, q <= C_ / 100], [0, 1, 2], 3)
        n_ = np.bincount(g, minlength=4)
        e_ = np.bincount(g, weights=yd, minlength=4)
        r_ = e_ / n_
        if (e_ >= MIN_EV).all() and r_[0] >= 2 * r_[1] and r_[1] >= 2 * r_[2] and r_[2] >= 1.5 * r_[3] and r_[0] >= 5 * r_[3]:
            n_ok += 1
            iv = woe_iv(n_ - e_, e_)
            if best is None or iv > best[0] + 1e-12 or (abs(iv - best[0]) <= 1e-12 and A_ > best[1]):
                best = (iv, A_, B_, C_)
    sd = np.sort(score_dev)
    cuts = [float(sd[int(np.ceil(c / 100 * len(sd))) - 1]) for c in best[1:]]
    return cuts, best, n_ok


def assign(s, cuts):
    return np.select([s <= cuts[0], s <= cuts[1], s <= cuts[2]], TR[:3], TR[3])


CUTS, BEST, NOK = search(F.score[isdev].to_numpy())
F["tramo_modelo"] = assign(F.score, CUTS)
CUTS_X, BEST_X, NOK_X = search(F.score_xgb[isdev].to_numpy())
F["tramo_xgb"] = assign(F.score_xgb, CUTS_X)
m1_share = F.loc[isdev, "tramo_m1_modelo"].value_counts(normalize=True).reindex(TR).cumsum().to_numpy()[:3]
sd = np.sort(F.score[isdev].to_numpy())
CUTS_EQ = [float(sd[int(np.ceil(c * len(sd))) - 1]) for c in m1_share]
F["tramo_igual_M1"] = assign(F.score, CUTS_EQ)

# ── Overrides (dev) ──────────────────────────────────────────────────────────────────────────────────────────
RULES = {"banker_change_6m_flag = 1": F.banker_change_6m_flag == 1, "complaint_escalated_flag = 1": F.complaint_escalated_flag == 1,
         "transfer_to_competitor_pct_90d ≥ 10%": F.transfer_to_competitor_pct_90d >= 0.10}
RANK = {t: i for i, t in enumerate(TR)}
ov, ACTIVE = [], {}
for name, m in RULES.items():
    m = m.fillna(False).to_numpy()
    for dest in ("Crítico", "Alto"):
        moved = m & (F.tramo_modelo.map(RANK).to_numpy() > RANK[dest]) & isdev
        prec = float(F.y_B[moved].mean()) if moved.sum() else np.nan
        share = moved.sum() / ((F.tramo_modelo == dest).to_numpy() & isdev).sum()
        need = 0.25 if dest == "Crítico" else 0.12
        ok = prec >= need and share <= 0.30
        ov.append({"regla": name, "destino": dest, "movidos dev": int(moved.sum()), "precisión %": 100 * prec, "movidos / tramo %": 100 * share, "cumple": ok})
        if ok and name not in ACTIVE:
            ACTIVE[name] = dest
OV = pd.DataFrame(ov)
OV["decisión"] = OV.regla.map(lambda r: ACTIVE.get(r, "eliminada"))
save_table(OV, "step06_overrides")
F["overrides"] = ""
F["tramo"] = F.tramo_modelo
for name, dest in ACTIVE.items():
    act = RULES[name].fillna(False)
    F.loc[act, "overrides"] = (F.loc[act, "overrides"] + "; " + name).str.strip("; ")
    F.loc[act & (F.tramo.map(RANK) > RANK[dest]), "tramo"] = dest


# ── Escalas maestras (dev) ───────────────────────────────────────────────────────────────────────────────────
def master(col, score_col, p_col):
    d = F[isdev]
    rows = []
    for t in TR:
        g = d[d[col] == t]
        rows.append({"tramo": t, "score mín": int(g[score_col].min()) if len(g) else np.nan, "score máx": int(g[score_col].max()) if len(g) else np.nan,
                     "hogares": len(g), "% hogares": 100 * len(g) / len(d), "% RV": 100 * g.relationship_value.sum() / d.relationship_value.sum(),
                     "p media %": 100 * g[p_col].mean(), "eventos": int(g.y_B.sum()), "tasa %": 100 * g.y_B.mean(), "captura eventos %": 100 * g.y_B.sum() / d.y_B.sum(),
                     "captura RV eventos %": 100 * (g.relationship_value * g.y_B).sum() / (d.relationship_value * d.y_B).sum(), "lift": g.y_B.mean() / d.y_B.mean()})
    return pd.DataFrame(rows)


MS = master("tramo", "score", "probabilidad")
MS_model = master("tramo_modelo", "score", "probabilidad")
MS_eq = master("tramo_igual_M1", "score", "probabilidad")
MS_x = master("tramo_xgb", "score_xgb", "p_xgb")
MS_m1 = master("tramo_m1", "score_m1", "p_m1")
save_table(MS, "step06_master_scale_households")
save_table(MS[["tramo", "% RV", "captura RV eventos %"]], "step06_master_scale_rv")
CMPT = pd.concat([t_.assign(modelo=n_) for n_, t_ in (("EBM (final, con overrides)", MS), ("EBM (modelo)", MS_model), ("EBM a igual % que M1", MS_eq),
                                                       ("XGBoost (modelo)", MS_x), ("M1 (final)", MS_m1))], ignore_index=True)
save_table(CMPT, "step06_tramos_comparison")
CUT = pd.DataFrame([{"modelo": "EBM", "corte": ["Crítico/Alto", "Alto/Vigilancia", "Vigilancia/Estable"][i], "percentil dev": BEST[i + 1], "score ≤": CUTS[i]} for i in range(3)] +
                   [{"modelo": "XGBoost", "corte": ["Crítico/Alto", "Alto/Vigilancia", "Vigilancia/Estable"][i], "percentil dev": BEST_X[i + 1], "score ≤": CUTS_X[i]} for i in range(3)] +
                   [{"modelo": "EBM a igual % que M1", "corte": ["Crítico/Alto", "Alto/Vigilancia", "Vigilancia/Estable"][i], "percentil dev": 100 * m1_share[i], "score ≤": CUTS_EQ[i]} for i in range(3)])
save_table(CUT, "step06_cuts")

# ── Salida ───────────────────────────────────────────────────────────────────────────────────────────────────
F["población"] = np.select([F.excl_reason == "tenure_lt_1", F.excl_reason == "churn_excluded", F.y_B_indet.astype(bool)],
                           ["fuera de población de desarrollo (antigüedad < 1)", "excluido (churn_excluded)", "indeterminado B"], "desarrollo")
F["prioridad_intra_tramo"] = F.probabilidad * F.relationship_value
out = F[[ID, "segment", "cluster", "score", "probabilidad", "tramo", "tramo_modelo", "tramo_igual_M1", "driver_1", "driver_1_puntos", "driver_2", "driver_2_puntos",
         "driver_3", "driver_3_puntos", "overrides", "prioridad_intra_tramo", "score_xgb", "p_xgb", "tramo_xgb", "score_m1", "p_m1", "tramo_m1", "población", "partición"]]
out = out.rename(columns={"segment": "segmento", "score": "score_ebm", "probabilidad": "p_ebm_calibrada", "tramo": "tramo_ebm", "tramo_modelo": "tramo_ebm_modelo",
                          "tramo_igual_M1": "tramo_ebm_igual_M1", "p_xgb": "p_xgb_calibrada", "p_m1": "p_m1_calibrada"})
SCORES.mkdir(parents=True, exist_ok=True)
out.to_csv(SCORES / "household_scores_ml.csv", index=False)
with open(MODEL / "step06_scaling.pkl", "wb") as fh:
    pickle.dump({"base": BASE, "a": a, "b": b, "cuts": CUTS, "cuts_xgb": CUTS_X, "cuts_eq_m1": CUTS_EQ, "overrides": ACTIVE, "min_ev_dev": MIN_EV, "spw_xgb": SPW}, fh)
rnd = pd.DataFrame([{"error máx. |p del score − p exacta|": float(np.max(np.abs(F.probabilidad - exact))), "error máx. score (puntos)": float(np.max(np.abs(F.score - (OFFSET - FACTOR * np.log(exact / (1 - exact))))))}])
save_table(rnd, "step06_rounding")
ex = F[isdev].iloc[0]
ex_row = F.index[F[ID] == ex[ID]][0]
EXT = pd.DataFrame({"componente": ["base"] + V, "puntos": [BASE] + PTS[ex_row].tolist()})

rep = f"""# Paso 6 · Escalamiento, tramos, salida

## Objetivo
- Pasar el EBM a puntos PDO con tabla exacta por bin, definir tramos con las reglas del M1 y entregar el score por hogar
  con el M1 y el XGBoost al lado.

## Método
- Score = base + Σ puntos; puntos_j = round(−Factor·b·f_j) con b de Platt = {b:.3f}; base = {BASE} [DATA]. Probabilidad
  publicada = la del score. Tramos H-3 en dev (mayor IV entre {NOK:,} configuraciones factibles para EBM y {NOK_X:,} para
  XGBoost) [DATA]; vista a igual % de hogares que M1 (I-6). Overrides re-evaluados.

## Código
- `src/step06_scaling.py` · `tests/test_step06.py` · `step06_*.csv`, `outputs/scores/household_scores_ml.csv`.

## Resultados

### Cortes [DATA]
{md_table(CUT, floatfmt=",.1f")}

### Escala maestra EBM (dev, con overrides) [DATA]
{md_table(MS, floatfmt=",.2f")}

- Verificación: % hogares suma {MS['% hogares'].sum():.1f}%; captura suma {MS['captura eventos %'].sum():.1f}%; Σ share × tasa =
  {(MS['% hogares'] * MS['tasa %']).sum() / 100:.2f}% = tasa dev {100 * yd.mean():.2f}% [DATA].

### Comparación de tramos en dev: EBM vs XGBoost vs M1 [DATA]
{md_table(CMPT[['modelo', 'tramo', '% hogares', 'eventos', 'tasa %', 'captura eventos %', 'captura RV eventos %', 'lift']], floatfmt=",.2f")}

### Overrides (dev) [DATA]
{md_table(OV, floatfmt=",.1f")}

### Ejemplo: base + Σ puntos = score (hogar {ex[ID]}) [DATA]
{md_table(EXT)}

- Verificación: {BASE} + {int(PTS[ex_row].sum())} = {BASE + int(PTS[ex_row].sum())} = score {int(ex.score)}; el test lo verifica en los 20,000 hogares [DATA].
- Redondeo: {md_table(rnd, floatfmt=",.4f")}

### Lookup EBM compacto (puntos por tramo de valor) [DATA]
{md_table(LKC)}

- {len(LK):,} bins del EBM se reducen a {len(LKC):,} filas uniendo bins consecutivos con los mismos puntos; el score no cambia
  (lookup completo en `step06_lookup.csv`) [DATA].

## Tests
- `tests/test_step06.py` (ver pytest).

## Decisiones y preguntas abiertas
- D6.1–D6.2 en `reports/decision_log.md`; preguntas G2 en `reports/gate_2.md`.
"""
(REPORTS / "step06.md").write_text(rep, encoding="utf-8")
print(CUT.to_string(index=False)); print(CMPT[["modelo", "tramo", "% hogares", "eventos", "tasa %", "captura eventos %", "captura RV eventos %", "lift"]].round(2).to_string(index=False))
print(OV.round(1).to_string(index=False)); print(rnd.to_string(index=False))
