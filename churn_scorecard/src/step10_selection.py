"""Paso 10 · Selección de variables (dev, target B).

Campeón (sobre WoE del paso 9):
  1. Elegibles: IV ≥ 0.02, sin compuestos / edad / buró, signo esperado definido y tendencia de bins coincidente.
  2. Clustering de variables (VarClus divisivo: se parte el cluster con 2º autovalor > 1; reasignación por R² con la
     1ª componente de cada cluster). Representante = menor (1 − R²propio) / (1 − R²vecino), desempate por IV.
  3. Adición hacia adelante con ΔGini en los 25 folds de la CV 5×5 (bins fijos): entra la variable de mayor ΔGini medio
     si ΔGini > 0 en ≥ 80% de los folds, todos los β con el signo correcto y VIF(WoE) < 5; tope 10 variables.
  4. ElasticNet (logística, l1_ratio 0.5, C por CV) sobre los representantes como control cruzado.
Challenger (preselección sobre valores crudos, NaN nativo):
  casi constantes (valor modal ≥ 99%) → fuga (AUC > 0.85 o IV > 0.50, paso 6) → un representante por cluster de
  |ρ Spearman| > 0.75 (mayor IV) → permutation importance OOF (ΔPR-AUC > 0 en ≥ 80% de los 25 folds) → signo
  (a priori o "?" sin restricción, G1-1). Cierre 15–30.
"""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd
import xgboost as xgb
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn.metrics import average_precision_score, roc_auc_score
from statsmodels.stats.outliers_influence import variance_inflation_factor

from common import COMPOSITES, EXCLUDED_G13, MODEL, PROC, REPORTS, SEED, TABLES, candidates, load_split, md_table, save_table, set_seed
from woe import woe_frame

set_seed()
dev = load_split("dev").merge(pd.read_parquet(PROC / "step07_clusters.parquet"), on="household_id")
D = dev[dev.in_pop_B].reset_index(drop=True)
y = D.y_B.astype(int).to_numpy()
FOLDS = [(r, k) for r in range(1, 6) for k in range(5)]
B = pickle.load(open(MODEL / "step09_binning.pkl", "rb"))
IV9 = pd.read_csv(TABLES / "step09_iv_summary.csv").set_index("variable")
U6 = pd.read_csv(TABLES / "step06_univariate_B.csv").set_index("variable")
FE = pd.read_csv(TABLES / "step05_features.csv").set_index("variable")
SIGN = FE["signo esperado"].to_dict()
DIM = FE["dimensión"].to_dict()
TREND = {"+": "ascendente", "−": "descendente"}

# ── Campeón · 1. elegibles ─────────────────────────────────────────────────────────────────────────────────────
elig = []
for v, r in IV9.iterrows():
    s = SIGN.get(v, "?")
    why = ("IV < 0.02" if r.IV < 0.02 else "compuesto" if v in COMPOSITES else "G1-3" if v in EXCLUDED_G13
           else "sin signo esperado (\"?\")" if s not in TREND else "tendencia ≠ signo" if r.tendencia != TREND[s] else "")
    elig.append({"variable": v, "IV": r.IV, "signo esperado": s, "tendencia": r.tendencia, "dimensión": DIM.get(v, "—"),
                 "elegible campeón": why == "", "motivo de exclusión": why})
elig = pd.DataFrame(elig)
P0 = elig.loc[elig["elegible campeón"], "variable"].tolist()
Wd = woe_frame(D, B, P0)

# ── 2. VarClus ────────────────────────────────────────────────────────────────────────────────────────────────


def pc1(cols):
    Z = (Wd[cols] - Wd[cols].mean()) / Wd[cols].std()
    if len(cols) == 1:
        return Z.iloc[:, 0].to_numpy()
    w, V = np.linalg.eigh(np.corrcoef(Z.T.to_numpy()))
    return Z.to_numpy() @ V[:, -1]


def eig2(cols):
    return 0.0 if len(cols) < 2 else float(np.sort(np.linalg.eigvalsh(np.corrcoef(Wd[cols].T.to_numpy())))[-2])


def varimax(L, it=100):
    p, k = L.shape
    R = np.eye(k)
    for _ in range(it):
        Lr = L @ R
        u, s, vt = np.linalg.svd(L.T @ (Lr ** 3 - Lr @ np.diag((Lr ** 2).sum(0)) / p))
        R = u @ vt
    return L @ R


def r2(a, b):
    return np.corrcoef(a, b)[0, 1] ** 2


clusters = [P0[:]]
while True:
    e2 = [eig2(c) for c in clusters]
    i = int(np.argmax(e2))
    if e2[i] <= 1.0:
        break
    cols = clusters.pop(i)
    w, V = np.linalg.eigh(np.corrcoef(Wd[cols].T.to_numpy()))
    L = varimax(V[:, -2:] * np.sqrt(w[-2:]))
    a = [c for c, l in zip(cols, L) if abs(l[0]) >= abs(l[1])]
    b = [c for c in cols if c not in a]
    clusters += [a, b] if a and b else [cols]
    for _ in range(20):                                       # reasignación global (NCS)
        comps = [pc1(c) for c in clusters]
        new = [[] for _ in clusters]
        for v in P0:
            new[int(np.argmax([r2(Wd[v], p) for p in comps]))].append(v)
        new = [c for c in new if c]
        if sorted(map(sorted, new)) == sorted(map(sorted, clusters)):
            break
        clusters = new
comps = [pc1(c) for c in clusters]
vc = []
for j, cols in enumerate(clusters):
    for v in cols:
        own = r2(Wd[v], comps[j])
        nb = max([r2(Wd[v], comps[k]) for k in range(len(clusters)) if k != j], default=0.0)
        vc.append({"cluster": j + 1, "variable": v, "R² propio": own, "R² vecino": nb, "1−R² ratio": (1 - own) / (1 - nb),
                   "IV": IV9.loc[v, "IV"], "dimensión": DIM[v]})
vc = pd.DataFrame(vc).sort_values(["cluster", "1−R² ratio", "IV"], ascending=[True, True, False]).reset_index(drop=True)
vc["representante"] = ~vc.duplicated("cluster")
vc["2º autovalor del cluster"] = vc.cluster.map({j + 1: eig2(c) for j, c in enumerate(clusters)})
save_table(vc, "step10_varclus")
REP = vc.loc[vc.representante].sort_values("IV", ascending=False).variable.tolist()
CL = vc.set_index("variable").cluster.to_dict()

# ── 3. Adición hacia adelante (ΔGini CV), a lo sumo una variable por cluster (D10.2) ──────────────────────────
POOL = vc.sort_values("IV", ascending=False).variable.tolist()
Xrep = Wd[POOL].to_numpy()
cvm = {rr: D[f"cv_r{rr}"].to_numpy() for rr in range(1, 6)}


def gini_folds(cols):
    idx = [POOL.index(c) for c in cols]
    g = []
    for rr, k in FOLDS:
        tr, te = cvm[rr] != k, cvm[rr] == k
        if not idx:
            g.append(0.0)
            continue
        m = LogisticRegression(C=1e6, class_weight="balanced", max_iter=2000).fit(Xrep[tr][:, idx], y[tr])
        g.append(2 * roc_auc_score(y[te], m.decision_function(Xrep[te][:, idx])) - 1)
    return np.array(g)


def vif_max(cols):
    if len(cols) < 2:
        return 1.0
    V = Wd[cols].assign(const=1.0).to_numpy()
    return max(variance_inflation_factor(V, i) for i in range(len(cols)))


def signs_ok(cols):
    m = LogisticRegression(C=1e6, class_weight="balanced", max_iter=2000).fit(Wd[cols].to_numpy(), y)
    return bool((m.coef_[0] < 0).all())                        # WoE = ln(%buenos/%malos): β(churn) < 0 ⟺ β(buenos) > 0


def forward(allowed):
    sel, g_cur, steps = [], gini_folds([]), []
    while len(sel) < 10:
        best = None
        used = {CL[c] for c in sel}
        for v in [c for c in allowed if CL[c] not in used]:
            g = gini_folds(sel + [v])
            d = g - g_cur
            row = {"paso": len(sel) + 1, "variable": v, "cluster": CL[v], "representante 1−R²": v in REP, "Gini CV": g.mean(), "ΔGini medio": d.mean(),
                   "% folds ΔGini > 0": 100 * (d > 0).mean(), "VIF máx": vif_max(sel + [v]), "signos β correctos": signs_ok(sel + [v])}
            row["cumple"] = row["% folds ΔGini > 0"] >= 80 and row["VIF máx"] < 5 and row["signos β correctos"]
            steps.append(row)
            if row["cumple"] and (best is None or row["ΔGini medio"] > best[1]):
                best = (v, row["ΔGini medio"], g)
        if best is None:
            break
        sel.append(best[0])
        g_cur = best[2]
        for s_ in steps:
            if s_["paso"] == len(sel) and s_["variable"] == best[0]:
                s_["entra"] = True
    return sel, steps, g_cur


sel_lit, steps_lit, g_lit = forward(REP)                      # regla literal del SPEC: solo representantes 1−R²
sel, steps, g_sel = forward(POOL)                              # D10.2: cualquier miembro, uno por cluster
lit = pd.DataFrame([{"variante": "SPEC literal (solo representantes 1−R²)", "variables": len(sel_lit), "Gini CV": g_lit.mean(), "sd folds": g_lit.std(),
                     "selección": ", ".join(sel_lit)},
                    {"variante": "D10.2 (uno por cluster, cualquier miembro)", "variables": len(sel), "Gini CV": g_sel.mean(), "sd folds": g_sel.std(),
                     "selección": ", ".join(sel)}])
d_ = g_sel - g_lit
lit["% folds D10.2 > literal"] = [np.nan, 100 * (d_ > 0).mean()]
save_table(lit, "step10_rule_comparison")
fw = pd.DataFrame(steps)
fw["entra"] = fw.get("entra", False)
fw["entra"] = fw["entra"].fillna(False).astype(bool)
save_table(fw, "step10_forward")

# ── 4. ElasticNet de control ──────────────────────────────────────────────────────────────────────────────────
en = LogisticRegressionCV(Cs=np.logspace(-3, 1, 20), penalty="elasticnet", solver="saga", l1_ratios=[0.5], scoring="roc_auc",
                          cv=[(np.where(cvm[1] != k)[0], np.where(cvm[1] == k)[0]) for k in range(5)], class_weight="balanced",
                          max_iter=5000, random_state=SEED).fit(Xrep, y)
sc = en.scores_[1][:, :, 0]
mean, se = sc.mean(0), sc.std(0) / np.sqrt(sc.shape[0])
C_1se = en.Cs_[np.argmax(mean >= mean.max() - se[np.argmax(mean)])]
en1 = LogisticRegression(C=C_1se, penalty="elasticnet", solver="saga", l1_ratio=0.5, class_weight="balanced", max_iter=5000,
                         random_state=SEED).fit(Xrep, y)
enr = pd.DataFrame({"variable": POOL, "β EN (C óptimo)": en.coef_[0], "β EN (C 1-SE)": en1.coef_[0]})
enr["≠ 0 en 1-SE"] = enr["β EN (C 1-SE)"].abs() > 1e-8
enr["seleccionada (adición)"] = enr.variable.isin(sel)
save_table(enr, "step10_elasticnet")

final = pd.DataFrame({"variable": sel})
final["IV"] = final.variable.map(IV9.IV)
final["dimensión"] = final.variable.map(DIM)
final["signo esperado"] = final.variable.map(SIGN)
final["VIF (WoE)"] = [variance_inflation_factor(Wd[sel].assign(const=1.0).to_numpy(), i) for i in range(len(sel))]
final["β EN 1-SE ≠ 0"] = final.variable.map(enr.set_index("variable")["≠ 0 en 1-SE"])
final["regla de bins"] = final.variable.map(IV9["regla de bins"])
final["cluster"] = final.variable.map(CL)
final["representante 1−R² del cluster"] = final.cluster.map(vc[vc.representante].set_index("cluster").variable)
save_table(final, "step10_champion_vars")

# ── Challenger · preselección ─────────────────────────────────────────────────────────────────────────────────
CP = candidates(include_composites=True) + ["cluster"]
ch = pd.DataFrame({"variable": CP})
ch["valor modal %"] = [100 * D[c].value_counts(normalize=True, dropna=False).iloc[0] for c in CP]
ch["IV (paso 6)"] = ch.variable.map(U6["IV preliminar"]).fillna(ch.variable.map(IV9.IV))
ch["AUC (paso 6)"] = ch.variable.map(U6["AUC univariada"])
ch["signo"] = ch.variable.map(SIGN).fillna("?")
ch["f1 casi constante"] = ch["valor modal %"] >= 99
ch["f2 fuga"] = (ch["AUC (paso 6)"] > 0.85) | (ch["IV (paso 6)"] > 0.50)
sp = pd.read_csv(TABLES / "step08_spearman.csv").set_index("variable")
num = [c for c in CP if c in sp.index and not ch.set_index("variable").loc[c, ["f1 casi constante", "f2 fuga"]].any()]
R = sp.loc[num, num].abs().fillna(0).to_numpy()
np.fill_diagonal(R, 1)
lab = fcluster(linkage(squareform(1 - R, checks=False), "complete"), t=0.25, criterion="distance")
grp = pd.DataFrame({"variable": num, "cluster ρ": lab, "IV": [ch.set_index("variable").loc[c, "IV (paso 6)"] for c in num]})
grp = grp.sort_values(["cluster ρ", "IV"], ascending=[True, False])
grp["rep"] = ~grp.duplicated("cluster ρ")
ch = ch.merge(grp[["variable", "cluster ρ", "rep"]], on="variable", how="left")
ch["f3 redundante (|ρ| > 0.75)"] = ch.rep.eq(False)
P3 = ch.loc[~ch[["f1 casi constante", "f2 fuga", "f3 redundante (|ρ| > 0.75)"]].any(axis=1), "variable"].tolist()

Xc = D[P3].copy()
if "cluster" in Xc:
    Xc["cluster"] = Xc["cluster"].astype("category")
PI = {c: [] for c in P3}
rng = np.random.default_rng(SEED)
for rr, k in FOLDS:
    tr, te = cvm[rr] != k, cvm[rr] == k
    m = xgb.XGBClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, tree_method="hist",
                          enable_categorical=True, random_state=SEED, n_jobs=4, scale_pos_weight=(y[tr] == 0).sum() / y[tr].sum())
    m.fit(Xc[tr], y[tr])
    Xte = Xc[te].reset_index(drop=True)
    base = average_precision_score(y[te], m.predict_proba(Xte)[:, 1])
    for c in P3:
        drops = []
        for _ in range(3):
            Xp = Xte.copy()
            Xp[c] = Xp[c].to_numpy()[rng.permutation(len(Xp))]
            if c == "cluster":
                Xp[c] = pd.Categorical(Xp[c], categories=Xc[c].cat.categories)
            drops.append(base - average_precision_score(y[te], m.predict_proba(Xp)[:, 1]))
        PI[c].append(np.mean(drops))
pi = pd.DataFrame({"variable": P3, "ΔPR-AUC medio": [np.mean(PI[c]) for c in P3], "% folds > 0": [100 * np.mean(np.array(PI[c]) > 0) for c in P3]})
ch = ch.merge(pi, on="variable", how="left")
ch["f4 permutación (< 80% folds)"] = ch["% folds > 0"].lt(80) & ch["% folds > 0"].notna()
ch["f5 sin signo de negocio"] = False                        # "?" entra sin restricción monótona (G1-1)
ch["pasa"] = ~ch[[c for c in ch.columns if c.startswith("f")]].any(axis=1) & ch["% folds > 0"].notna()
ch = ch.sort_values(["pasa", "ΔPR-AUC medio"], ascending=[False, False]).reset_index(drop=True)
if ch.pasa.sum() > 30:
    ch.loc[ch.index[30:], "pasa"] = False
save_table(ch.drop(columns="rep"), "step10_challenger_prescreen")
CH = ch.loc[ch.pasa, "variable"].tolist()
with open(MODEL / "step10_selection.pkl", "wb") as fh:
    pickle.dump({"champion": sel, "challenger": CH, "varclus_reps": REP}, fh)

funnel = pd.DataFrame([
    ("candidatas (con compuestos y cluster)", len(CP)),
    ("− casi constantes", int(ch["f1 casi constante"].sum())),
    ("− fuga", int(ch["f2 fuga"].sum())),
    ("− redundantes |ρ| > 0.75", int(ch["f3 redundante (|ρ| > 0.75)"].sum())),
    ("− permutación < 80% folds", int(ch["f4 permutación (< 80% folds)"].sum())),
    ("= challenger", len(CH))], columns=["etapa", "variables"])
save_table(funnel, "step10_challenger_funnel")
cf = pd.DataFrame([("candidatas paso 9", len(IV9)), ("elegibles campeón", len(P0)), ("clusters VarClus", len(REP)),
                   ("seleccionadas por adición", len(sel))], columns=["etapa", "variables"])
save_table(cf, "step10_champion_funnel")

fw_in = fw[fw.entra][["paso", "variable", "cluster", "representante 1−R²", "Gini CV", "ΔGini medio", "% folds ΔGini > 0", "VIF máx"]]
dims = final["dimensión"].value_counts()
rep = f"""# Paso 10 · Selección

## Objetivo
- Campeón: 6–10 variables WoE no redundantes, con signo de negocio y aporte incremental. Challenger: 15–30 variables.

## Método
- Campeón: elegibles (IV ≥ 0.02, signo esperado definido y tendencia coincidente, sin compuestos / edad / buró) →
  VarClus sobre WoE (partir si 2º autovalor > 1) → representante = menor (1−R²propio)/(1−R²vecino), desempate IV →
  adición hacia adelante sobre todos los miembros, a lo sumo uno por cluster (D10.2): entra la de mayor ΔGini medio en los 25 folds (5×5) si ΔGini > 0 en ≥ 80% de los folds
  [DEF-default D10.1], VIF(WoE) < 5 y todos los β con signo correcto; tope 10 → ElasticNet (l1_ratio 0.5, C por CV y
  regla 1-SE) como control.
- Challenger: casi constantes (modal ≥ 99%) → fuga (AUC > 0.85 o IV > 0.50) → un representante (mayor IV) por cluster
  de |ρ Spearman| > 0.75 (enlace completo) → permutation importance OOF (XGBoost prof. 3, ΔPR-AUC en el fold de
  prueba, 3 permutaciones) > 0 en ≥ 80% de los folds → signo (a priori, o "?" sin restricción por G1-1). Tope 30.

## Código
- `src/step10_selection.py` · `tests/test_step10.py` · `step10_*.csv`, `outputs/model/step10_selection.pkl`.

## Resultados

### Embudo del campeón [DATA]
{md_table(cf)}

- Excluidas por motivo [DATA]: {', '.join(f'{k}: {v}' for k, v in elig.loc[~elig['elegible campeón'], 'motivo de exclusión'].value_counts().items())}.

### VarClus: representantes [DATA]
{md_table(vc[vc.representante][['cluster', 'variable', 'R² propio', 'R² vecino', '1−R² ratio', 'IV', 'dimensión', '2º autovalor del cluster']], floatfmt=",.3f")}

- {len(clusters)} clusters, todos con 2º autovalor ≤ 1 [DATA]. Composición completa en `step10_varclus.csv`.

### Adición hacia adelante (variables que entran) [DATA]
{md_table(fw_in, floatfmt=",.4f")}

- La adición se detiene en {len(sel)} variables: ninguna otra cumple las tres condiciones [DATA].
- Verificación: Gini CV final = {fw_in['Gini CV'].iloc[-1]:.4f} = Σ ΔGini ({fw_in['ΔGini medio'].sum():.4f}) [DATA].

### Regla del representante: literal vs D10.2 [DATA]
{md_table(lit, floatfmt=",.4f")}

- La regla literal elige por (1−R²propio)/(1−R²vecino) y deja fuera variables fuertes cuando el cluster agrupa señales
  de negocio distintas (p. ej. cluster {CL['banker_change_6m_flag']}: `banker_change_6m_flag` IV {IV9.loc['banker_change_6m_flag', 'IV']:.3f} pierde contra
  `relationship_dissatisfaction_flag` IV {IV9.loc['relationship_dissatisfaction_flag', 'IV']:.3f}) [DATA]. D10.2 mantiene la no redundancia (una por cluster, VIF < 5)
  y deja que el aporte incremental elija el miembro. Pregunta G2-3.

### Variables del campeón [DATA]
{md_table(final, floatfmt=",.3f")}

- Dimensiones [DATA]: {', '.join(f'{k} {v}' for k, v in dims.items())}.
- ElasticNet 1-SE (C = {C_1se:.4g}) sobre las {len(POOL)} elegibles conserva {int(final['β EN 1-SE ≠ 0'].sum())} de {len(final)} seleccionadas [DATA].

### Embudo del challenger [DATA]
{md_table(funnel)}

### Challenger: variables que pasan [DATA]
{md_table(ch[ch.pasa][['variable', 'signo', 'IV (paso 6)', 'ΔPR-AUC medio', '% folds > 0']], floatfmt=",.4f")}

- Verificación: {len(CP)} − {int(ch['f1 casi constante'].sum())} − {int(ch['f2 fuga'].sum())} − {int(ch['f3 redundante (|ρ| > 0.75)'].sum())} − {int(ch['f4 permutación (< 80% folds)'].sum())} − {len(ch) - int(ch[[c for c in ch.columns if c.startswith('f')]].any(axis=1).sum()) - len(CH)} (tope 30) = {len(CH)} [DATA].

## Tests
- `tests/test_step10.py` (ver pytest).

## Decisiones y preguntas abiertas
- D10.1–D10.4 en `reports/decision_log.md`.
"""
(REPORTS / "step10.md").write_text(rep, encoding="utf-8")
print(cf.to_string(index=False)); print(vc[vc.representante].round(3).to_string(index=False)); print(fw_in.round(4).to_string(index=False))
print(final.round(3).to_string(index=False)); print(funnel.to_string(index=False)); print(ch[ch.pasa][["variable", "ΔPR-AUC medio", "% folds > 0"]].round(4).to_string(index=False))
