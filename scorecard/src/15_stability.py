"""Paso 15 · Estabilidad (A y A-lite).

Sin dimensión temporal (corte único): la estabilidad se mide entre muestras y entre sub-poblaciones.
- PSI desarrollo vs holdout del score (10 bins por deciles de desarrollo) y de cada variable (bins del paso 9).
  PSI = Σ (%hold − %dev)·ln(%hold / %dev); < 0.10 estable, 0.10–0.25 moderado, > 0.25 inestable.
- Métricas por banda (holdout; desarrollo OOF como referencia): quintil de relationship_value, antigüedad,
  history_months (< 24 vs 24), segment y cluster del paso 7.
- Bootstrap de coeficientes (500 re-muestreos de desarrollo, bins fijos): IC 95% y % de réplicas con β > 0.
- Sensibilidad del AUC al re-binning: el mismo conjunto de variables re-binneado con reglas alternativas,
  re-estimado en desarrollo y medido en holdout (solo evaluación; no se elige nada con esto).
"""
from __future__ import annotations

import json
import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from common import FIGURES, MODELS, OUT, PARAMS, QC, SCORED, SEED, TABLES, save_table, set_seed
from metrics import bootstrap, ci, ks, top_capture_ties
from woe import fit_binning, is_discrete, load_sample, woe_frame

import warnings
warnings.filterwarnings("ignore")
set_seed()
T = PARAMS["target_primary"]
ALL = load_sample(OUT, TABLES, sample=None)
sc = pd.read_csv(SCORED / "scored_households.csv")[["household_id", "score", "score_lite", "probabilidad", "probabilidad_lite"]]
ALL = ALL.merge(sc, on="household_id")
elig = ~ALL.churn_excluded.astype(bool)
dev = ALL[(ALL.muestra == "desarrollo") & elig].reset_index(drop=True)
hold = ALL[(ALL.muestra == "holdout") & elig].reset_index(drop=True)
oof = pd.read_csv(OUT / "data" / "11_oof_dev.csv")
dev = dev.merge(oof[["household_id", "oof_A", "oof_A_lite"]], on="household_id")
yd, yh = dev[T].astype(int).to_numpy(), hold[T].astype(int).to_numpy()
with open(MODELS / "09_binning.pkl", "rb") as fh:
    B = pickle.load(fh)
cfg = json.loads((MODELS / "11_final_vars.json").read_text())
MODS = {"A": (cfg["models"]["A"], "score", "probabilidad", "oof_A"), "A-lite": (cfg["models"]["A-lite"], "score_lite", "probabilidad_lite", "oof_A_lite")}
iv = pd.read_csv(TABLES / "09_iv_summary.csv").set_index("variable")
qc = QC("15")


def psi(a_dev, a_hold):
    cats = sorted(set(a_dev) | set(a_hold), key=str)
    pd_ = np.array([(a_dev == c).mean() for c in cats]) + 1e-6
    ph = np.array([(a_hold == c).mean() for c in cats]) + 1e-6
    return float(np.sum((ph - pd_) * np.log(ph / pd_)))


def psi_class(v):
    return "estable" if v < 0.10 else "moderado" if v < 0.25 else "INESTABLE"


# ── PSI ─────────────────────────────────────────────────────────────────────────────────
ps = []
for m, (vars_, scol, pcol, _) in MODS.items():
    edges = np.unique(np.quantile(dev[scol], np.linspace(0, 1, 11)))
    bd = np.digitize(dev[scol], edges[1:-1])
    bh = np.digitize(hold[scol], edges[1:-1])
    v = psi(bd, bh)
    ps.append({"objeto": f"score {m}", "tipo": "score", "PSI": v, "clase": psi_class(v)})
for c in sorted(set(cfg["models"]["A"]) | set(iv[iv.IV >= 0.02].index)):
    r_d = dev[f"{c}__miss"] if f"{c}__miss" in dev else None
    r_h = hold[f"{c}__miss"] if f"{c}__miss" in hold else None
    v = psi(B[c].bin_labels(dev[c], r_d), B[c].bin_labels(hold[c], r_h))
    ps.append({"objeto": c, "tipo": "variable del modelo A" if c in cfg["models"]["A"] else "candidata (IV ≥ 0.02)", "PSI": v, "clase": psi_class(v)})
psi_t = pd.DataFrame(ps).sort_values(["tipo", "PSI"], ascending=[False, False])
save_table(psi_t.round(5), "15_psi")

# ── Métricas por banda ──────────────────────────────────────────────────────────────────
def bands(df):
    rvq = pd.qcut(df.relationship_value.rank(method="first"), 5, labels=[f"RV Q{i}" for i in range(1, 6)]).astype(str)
    ten = pd.cut(df.tenure_years, [-np.inf, 2, 5, 10, 20, np.inf], right=False,
                 labels=["antigüedad < 2", "2–5", "5–10", "10–20", "≥ 20"]).astype(str)
    return {"quintil RV": rvq, "antigüedad (años)": ten,
            "historia": np.where(df.history_months < 24, "history < 24", "history = 24"),
            "segmento": np.where(df.segment == 1, "UHNW", "HNW"), "cluster (paso 7)": "cluster " + df.cluster.astype(str)}


bh_, bd_ = bands(hold), bands(dev)
rows = []
for m, (vars_, scol, pcol, ocol) in MODS.items():
    ph, po = hold[pcol].to_numpy(), dev[ocol].to_numpy()
    for dim in bh_:
        for g in sorted(pd.unique(bh_[dim])):
            mh = np.asarray(bh_[dim] == g)
            md = np.asarray(bd_[dim] == g)
            ys, ps_ = yh[mh], ph[mh]
            auc = roc_auc_score(ys, ps_) if 0 < ys.sum() < len(ys) else np.nan
            bb = bootstrap(ys, {"m": ps_}, lambda yy, pp, bi: roc_auc_score(yy, pp), n=300, seed=SEED, strata=ys)["m"] if ys.sum() >= 5 else None
            rows.append({"modelo": m, "dimensión": dim, "banda": g, "hogares holdout": int(mh.sum()), "eventos holdout": int(ys.sum()),
                         "tasa holdout %": 100 * ys.mean(), "AUC holdout": auc, "IC95 AUC": "[%.3f, %.3f]" % ci(bb) if bb is not None else "",
                         "KS holdout": ks(ys, ps_) if 0 < ys.sum() < len(ys) else np.nan,
                         "esperado holdout %": 100 * ps_.mean(), "AUC dev OOF": roc_auc_score(yd[md], po[md]) if 0 < yd[md].sum() < md.sum() else np.nan,
                         "eventos dev": int(yd[md].sum())})
bt = pd.DataFrame(rows)
save_table(bt.round(4), "15_metrics_by_band")

# ── Bootstrap de coeficientes ───────────────────────────────────────────────────────────
rng = np.random.default_rng(SEED)
coef_rows = []
for m, (vars_, *_ ) in MODS.items():
    W = woe_frame(dev, B, vars_).to_numpy()
    base = LogisticRegression(C=np.inf, max_iter=5000).fit(W, 1 - yd)
    betas = []
    for b in range(PARAMS["n_bootstrap"]):
        bi = rng.choice(len(yd), len(yd), replace=True)
        betas.append(LogisticRegression(C=np.inf, max_iter=5000).fit(W[bi], 1 - yd[bi]).coef_[0])
    betas = np.array(betas)
    for j, v in enumerate(vars_):
        lo, hi = np.percentile(betas[:, j], [2.5, 97.5])
        coef_rows.append({"modelo": m, "variable": v, "β": base.coef_[0][j], "IC95 bootstrap": f"[{lo:.3f}, {hi:.3f}]",
                          "% réplicas β > 0": 100 * (betas[:, j] > 0).mean(), "CV del β (sd/|media|)": betas[:, j].std() / abs(betas[:, j].mean())})
cb = pd.DataFrame(coef_rows)
save_table(cb.round(4), "15_coef_bootstrap")

# ── Sensibilidad al re-binning ──────────────────────────────────────────────────────────
ALT = {"base (paso 9)": None,
       "bins más gruesos (mín. 10% continuas, 2% discretas)": dict(cont=0.10, disc=0.02, diff=0.005),
       "bins más finos (mín. 3% continuas, 1% discretas, sin dif. mínima de tasa)": dict(cont=0.03, disc=0.01, diff=0.0),
       "diferencia mínima de tasa 1 pp": dict(cont=0.05, disc=0.01, diff=0.01)}
sens = []
for m, (vars_, *_ ) in MODS.items():
    preds = {}
    for lab, cfg_b in ALT.items():
        if cfg_b is None:
            Bk = B
        else:
            Bk = {}
            for c in vars_:
                r = dev[f"{c}__miss"] if f"{c}__miss" in dev else None
                mbs = cfg_b["disc"] if is_discrete(dev[c]) else cfg_b["cont"]
                Bk[c] = fit_binning(c, dev[c], r, yd, dtype="numerical", min_bin_size=mbs,
                                    min_events=PARAMS["min_bin_events"], min_event_rate_diff=cfg_b["diff"])
        mdl = LogisticRegression(C=np.inf, max_iter=5000).fit(woe_frame(dev, Bk, vars_).to_numpy(), yd)
        preds[lab] = mdl.predict_proba(woe_frame(hold, Bk, vars_).to_numpy())[:, 1]
        preds[lab + "__nbins"] = sum(len(Bk[c].labels) for c in vars_)
    nb = {k: preds.pop(k) for k in list(preds) if k.endswith("__nbins")}
    bs = bootstrap(yh, preds, lambda yy, pp, bi: roc_auc_score(yy, pp), n=PARAMS["n_bootstrap"], seed=SEED, strata=yh)
    for lab in ALT:
        d = bs[lab] - bs["base (paso 9)"]
        sens.append({"modelo": m, "binning": lab, "bins totales": nb[lab + "__nbins"], "AUC holdout": roc_auc_score(yh, preds[lab]),
                     "ΔAUC vs base": roc_auc_score(yh, preds[lab]) - roc_auc_score(yh, preds["base (paso 9)"]), "IC95 Δ pareado": "[%.3f, %.3f]" % ci(d),
                     "captura decil top": top_capture_ties(yh, preds[lab])})
sn = pd.DataFrame(sens)
save_table(sn.round(4), "15_rebinning_sensitivity")

# ── QC ──────────────────────────────────────────────────────────────────────────────────
for m in MODS:
    v = psi_t[psi_t.objeto == f"score {m}"].PSI.iloc[0]
    qc.check(f"PSI score {m} < 0.10", v < PARAMS["psi_max"], "< 0.10", f"{v:.4f}")
    bad = psi_t[(psi_t.tipo == "variable del modelo A") & (psi_t.PSI >= PARAMS["psi_max"])]
    neg = cb[(cb.modelo == m) & (cb["% réplicas β > 0"] < 97.5) & (cb.variable != "segment")]
    qc.check(f"{m}: β > 0 en ≥ 97.5% de réplicas bootstrap (sin segment)", neg.empty, "todas", neg.variable.tolist(), severity="warn")
    seg_b = cb[(cb.modelo == m) & (cb.variable == "segment")].iloc[0]
    qc.check(f"{m}: segment (forzada) — % réplicas β > 0", True, "informativo", f"{seg_b['% réplicas β > 0']:.1f}% · {seg_b['IC95 bootstrap']}")
    ss = sn[(sn.modelo == m) & (sn.binning != "base (paso 9)")]
    qc.check(f"{m}: |ΔAUC| por re-binning ≤ 0.01", bool((ss["ΔAUC vs base"].abs() <= 0.01).all()), "≤ 0.01", f"máx {ss['ΔAUC vs base'].abs().max():.4f}", severity="warn")
    weak = bt[(bt.modelo == m) & (bt["eventos holdout"] >= 20) & (bt["AUC holdout"] < 0.65)]
    qc.check(f"{m}: AUC ≥ 0.65 en bandas con ≥ 20 eventos (holdout)", weak.empty, "todas", weak.banda.tolist(), severity="warn")
qc.check("PSI de variables del modelo A < 0.10", bad.empty, "0", bad.objeto.tolist())

# ── Figura: AUC por banda ───────────────────────────────────────────────────────────────
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
COL = {"A": "#2a78d6", "A-lite": "#eb6834"}
t = bt[bt.modelo == "A"].reset_index(drop=True)
fig, ax = plt.subplots(figsize=(11, 4.2))
for m, off in (("A", -0.15), ("A-lite", 0.15)):
    tt = bt[bt.modelo == m].reset_index(drop=True)
    lo = tt["IC95 AUC"].str.extract(r"\[([\d.]+),")[0].astype(float)
    hi = tt["IC95 AUC"].str.extract(r", ([\d.]+)\]")[0].astype(float)
    x = np.arange(len(tt)) + off
    ax.errorbar(x, tt["AUC holdout"], yerr=[tt["AUC holdout"] - lo, hi - tt["AUC holdout"]], fmt="o", color=COL[m], ms=5, capsize=2, label=m)
ax.axhline(0.5, color=MUTED, lw=1, ls=":")
ax.axhline(0.65, color=MUTED, lw=1, ls="--")
ax.set_xticks(range(len(t)), [f"{b}\n({e} ev.)" for b, e in zip(t.banda, t["eventos holdout"])], rotation=60, ha="right", fontsize=7, color=MUTED)
ax.set_ylabel("AUC holdout (IC 95%)", color=MUTED)
ax.set_title("Discriminación por sub-población · holdout [DATA-SINT] (línea discontinua = 0.65)", loc="left", color=INK, fontsize=10)
ax.legend(frameon=False, labelcolor=INK)
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_axisbelow(True)
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.tick_params(colors=MUTED, length=0)
fig.tight_layout()
fig.savefig(FIGURES / "15_auc_by_band.png", dpi=140)

print(psi_t.round(4).to_string(index=False))
print("\n" + bt.round(3).to_string(index=False))
print("\n" + cb.round(3).to_string(index=False))
print("\n" + sn.round(4).to_string(index=False))
qc.gate()
