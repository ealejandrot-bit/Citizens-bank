"""Paso 5 · Calibración con OOF cruzado en dev (sin tocar el holdout; I-5). Target B.

- OOF por hogar = promedio de sus 5 predicciones fuera de fold (una por repetición de la CV 5×5): EBM (re-ajustado en
  cada fold) y XGBoost (OOF del paso 3, probabilidad corregida por prior).
- Platt (y ~ a + b·logit p_OOF) vs isotónica: Brier y ECE en un segundo nivel de 5 folds sobre las OOF, IC bootstrap 95%
  (1,000) de la diferencia; isotónica solo si el IC de la diferencia de Brier < 0. Aceptación Platt 0.8 ≤ b ≤ 1.2.
- Alineación de la media; calibración por segmento y por quintil de RV (Σ p·RV vs Σ RV de eventos), con las decisiones
  G3-2 / G3-3 del M1 como referencia.
"""
from __future__ import annotations

import json
import pickle
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from interpret.glassbox import ExplainableBoostingClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import StratifiedKFold

from common import FIGS, MODEL, PROC, REPORTS, SEED, load_split, md_table, save_table, set_seed

warnings.filterwarnings("ignore")
set_seed()
dev = load_split("dev")
D = dev[dev.in_pop_B].reset_index(drop=True)
y = D.y_B.astype(int).to_numpy()
S = json.loads((PROC / "step02_selected.json").read_text(encoding="utf-8"))
V = S["vars"]
MONO = [{"+": 1, "−": -1}.get(S["signs"][c], 0) for c in V]
X = D[V]
CV = {r: D[f"cv_r{r}"].to_numpy() for r in range(1, 6)}

oof_e = np.zeros((5, len(y)))
for r in range(1, 6):
    for k in range(5):
        tr, te = CV[r] != k, CV[r] == k
        oof_e[r - 1, te] = ExplainableBoostingClassifier(monotone_constraints=MONO, interactions=0, random_state=SEED, n_jobs=4).fit(X[tr], y[tr]).predict_proba(X[te])[:, 1]
O3 = pd.read_parquet(PROC / "step03_oof.parquet").set_index("household_id").loc[D.household_id]
oof_x = np.vstack([O3[f"p_xgboost_r{r}"].to_numpy() for r in range(1, 6)])
P = {"EBM": oof_e.mean(0), "XGBoost": oof_x.mean(0)}
pd.DataFrame({"household_id": D.household_id, "p_oof_ebm": P["EBM"], "p_oof_xgb": P["XGBoost"]}).to_parquet(PROC / "step05_oof.parquet", index=False)
lg = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))  # noqa: E731


def ece(yy, p, k=10):
    d = pd.qcut(pd.Series(p).rank(method="first"), k, labels=False)
    g = pd.DataFrame({"d": d, "p": p, "y": yy}).groupby("d").agg(n=("y", "size"), p=("p", "mean"), y=("y", "mean"))
    return float((g.n / g.n.sum() * (g.p - g.y).abs()).sum())


def platt(xx, yy):
    return sm.GLM(yy, sm.add_constant(xx), family=sm.families.Binomial()).fit()


rng = np.random.default_rng(SEED)
CMP, DIFF, CAL, OUT = [], [], {}, {}
for name, p in P.items():
    x = lg(p)
    op, oi = np.zeros(len(y)), np.zeros(len(y))
    for tr, te in StratifiedKFold(5, shuffle=True, random_state=SEED).split(x, y):
        op[te] = platt(x[tr], y[tr]).predict(sm.add_constant(x[te], has_constant="add"))
        oi[te] = IsotonicRegression(out_of_bounds="clip", y_min=1e-4, y_max=1 - 1e-4).fit(x[tr], y[tr]).predict(x[te])
    bs = []
    for _ in range(1000):
        i = rng.choice(len(y), len(y), replace=True)
        bs.append((brier_score_loss(y[i], oi[i]) - brier_score_loss(y[i], op[i]), ece(y[i], oi[i]) - ece(y[i], op[i])))
    bs = np.array(bs)
    use_iso = np.quantile(bs[:, 0], 0.975) < 0
    m = platt(x, y)
    a_, b_ = float(m.params[0]), float(m.params[1])
    ci = np.asarray(m.conf_int())[1]
    for lab, q in (("sin calibrar (OOF)", p), ("Platt (2º nivel OOF)", op), ("isotónica (2º nivel OOF)", oi)):
        CMP.append({"modelo": name, "método": lab, "Brier": brier_score_loss(y, q), "ECE (pp)": 100 * ece(y, q), "media p %": 100 * q.mean(), "tasa %": 100 * y.mean()})
    DIFF.append({"modelo": name, "ΔBrier (iso − Platt)": bs[:, 0].mean(), "IC95 inf": np.quantile(bs[:, 0], 0.025), "IC95 sup": np.quantile(bs[:, 0], 0.975),
                 "ΔECE": bs[:, 1].mean(), "a": a_, "b": b_, "b IC95 inf": ci[0], "b IC95 sup": ci[1], "0.8 ≤ b ≤ 1.2": 0.8 <= b_ <= 1.2,
                 "método elegido": "isotónica" if use_iso else "Platt"})
    iso = IsotonicRegression(out_of_bounds="clip", y_min=1e-4, y_max=1 - 1e-4).fit(x, y) if use_iso else None
    CAL[name] = {"method": "isotonic" if use_iso else "platt", "a": a_, "b": b_, "isotonic": iso}
    OUT[name] = iso.predict(x) if use_iso else 1 / (1 + np.exp(-(a_ + b_ * x)))
CMP, DIFF = pd.DataFrame(CMP), pd.DataFrame(DIFF)
save_table(CMP, "step05_methods")
save_table(DIFF, "step05_platt")
with open(MODEL / "step05_calibrators.pkl", "wb") as fh:
    pickle.dump(CAL, fh)

# Por segmento y por quintil de RV (OOF calibrado)
D["q_rv"] = pd.qcut(D.relationship_value, 5, labels=["Q1 (menor)", "Q2", "Q3", "Q4", "Q5 (mayor)"])
seg_rows, rv_rows = [], []
for name, pc in OUT.items():
    for s_ in ("HNW", "UHNW"):
        m = (D.segment == s_).to_numpy()
        seg_rows.append({"modelo": name, "segmento": s_, "hogares": int(m.sum()), "eventos": int(y[m].sum()), "p media %": 100 * pc[m].mean(), "tasa %": 100 * y[m].mean()})
    for q in D.q_rv.cat.categories:
        m = (D.q_rv == q).to_numpy()
        rvq = D.relationship_value.to_numpy()[m]
        rv_rows.append({"modelo": name, "quintil RV": q, "hogares": int(m.sum()), "p media %": 100 * pc[m].mean(), "tasa %": 100 * y[m].mean(),
                        "Σ p·RV / Σ RV eventos": (pc[m] * rvq).sum() / (y[m] * rvq).sum()})
SEG, RVQ = pd.DataFrame(seg_rows), pd.DataFrame(rv_rows)
save_table(SEG, "step05_segment")
save_table(RVQ, "step05_rv_quintile")

fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
for ax, (name, pc) in zip(axes, OUT.items()):
    for p, lab, col in ((P[name], "OOF sin calibrar", "#a3a29c"), (pc, "calibrada", "#2a78d6")):
        d = pd.qcut(pd.Series(p).rank(method="first"), 10, labels=False)
        g = pd.DataFrame({"d": d, "p": p, "y": y}).groupby("d").mean()
        ax.plot(g.p, g.y, marker="o", ms=5, lw=2, color=col, label=lab, markeredgecolor="white", markeredgewidth=1.5)
    ax.plot([0, .65], [0, .65], ls="--", lw=1, color="#52514e")
    ax.set_xlim(0, .65); ax.set_ylim(0, .65)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0)); ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    ax.set_title(name, fontsize=10, loc="left"); ax.grid(color="#e6e5df", lw=0.6)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0, labelsize=7.5, colors="#52514e"); ax.set_xlabel("probabilidad (media del decil)", fontsize=8, color="#52514e")
axes[0].set_ylabel("tasa de churn B observada", fontsize=8, color="#52514e"); axes[0].legend(frameon=False, fontsize=8)
fig.suptitle("Calibración por decil · OOF de dev (CV 5×5) · target B [DATA]", x=0.01, ha="left", fontsize=10.5)
fig.tight_layout(rect=(0, 0, 1, 0.93))
fig.savefig(FIGS / "step05_calibration.png", dpi=120)

rep = f"""# Paso 5 · Calibración

## Objetivo
- Que la probabilidad publicada del ML coincida con la tasa observada, sin usar el holdout.

## Método
- OOF por hogar = promedio de 5 predicciones fuera de fold (CV 5×5). Platt vs isotónica en un 2º nivel de 5 folds,
  IC bootstrap 95%; isotónica solo si ΔBrier < 0 con IC (D5.1). Aceptación 0.8 ≤ b ≤ 1.2.

## Código
- `src/step05_calibration.py` · `tests/test_step05.py` · `step05_*.csv`, `outputs/model/step05_calibrators.pkl`.

## Resultados

### Métodos [DATA]
{md_table(CMP, floatfmt=",.4f")}

### Platt e isotónica vs Platt [DATA]
{md_table(DIFF, floatfmt=",.4f")}

![Calibración](../outputs/figs/step05_calibration.png)

### Por segmento (OOF calibrado) [DATA]
{md_table(SEG, floatfmt=",.2f")}

### Por quintil de RV (OOF calibrado) [DATA]
{md_table(RVQ, floatfmt=",.3f")}

- Referencia M1 (G3-2): en validación el M1 subestimaba el quintil superior (Σ p·RV / Σ RV eventos = 0.85) [DATA].

## Tests
- `tests/test_step05.py` (ver pytest).

## Decisiones y preguntas abiertas
- D5.1 en `reports/decision_log.md`.
"""
(REPORTS / "step05.md").write_text(rep, encoding="utf-8")
print(CMP.round(4).to_string(index=False)); print(DIFF.round(4).to_string(index=False)); print(SEG.round(2).to_string(index=False)); print(RVQ.round(3).to_string(index=False))
