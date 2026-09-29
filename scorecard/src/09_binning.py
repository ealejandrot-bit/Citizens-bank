"""Paso 9 · Binning, WoE e IV (solo desarrollo).

- optbinning, monotonic_trend="auto_asc_desc", ≥ 30 eventos por bin, min_event_rate_diff = 0.5 pp.
- Tamaño mínimo de bin (D9.1): 5% de la población en continuas; 1% en binarias / conteos / discretas
  (≤ 10 valores o ≥ 70% en el mínimo) — con 5% se fusionarían 8 flags con RR ≥ 3.
- Missing como bin propio: "no_aplica" (estructural) y "sin_dato" (D5.1, D9.3).
- Clasificación IV: < 0.02 fuera · 0.02–0.10 débil · 0.10–0.30 medio · 0.30–0.50 fuerte · > 0.50 sospechoso.
- Estabilidad: WoE por bin recalculado en los 25 folds de entrenamiento de la CV 5×5 (bins fijos);
  bin inestable = sd(WoE) > 0.25 y cambio de signo en > 20% de los folds → se fusiona con el vecino de WoE más
  cercano y se repite (D9.2).
- QC gate: tasa de evento no monótona en bins no especiales → rebinnear.
"""
from __future__ import annotations

import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIGURES, MODELS, OUT, PARAMS, QC, TABLES, save_table, set_seed
from woe import VarBinning, fit_binning, woe_iv

set_seed()
T = PARAMS["target_primary"]
MIN_EV = PARAMS["min_bin_events"]
X = pd.read_pickle(OUT / "data" / "05_features.pkl").merge(pd.read_csv(OUT / "data" / "07_clusters.csv"), on="household_id")
meta = pd.read_csv(OUT / "data" / "05_predictor_meta.csv").set_index("columna")
split = pd.read_csv(TABLES / "04_split.csv")
dev = X.merge(split[["household_id", "muestra"] + [f"cv_r{r}" for r in range(1, 6)]], on="household_id")
dev = dev[dev.muestra == "desarrollo"].reset_index(drop=True)
y = dev[T].astype(int).to_numpy()

# log_relationship_value es monótona de relationship_value: mismo WoE → se bina solo RV (D9.4)
CANDS = [c for c in meta.index if c != "log_relationship_value"] + ["cluster"]
DIM = {**meta["dimensión"].to_dict(), "cluster": "estructura"}


def reason(c):
    return dev[f"{c}__miss"] if f"{c}__miss" in dev else None


def is_discrete(s: pd.Series) -> bool:
    v = s.dropna()
    vals, cnt = np.unique(v, return_counts=True)
    return len(vals) <= 10 or (cnt.max() / len(v) >= 0.70 and vals[cnt.argmax()] == v.min())


def iv_class(iv):
    return ("fuera (< 0.02)" if iv < 0.02 else "débil" if iv < 0.10 else "medio" if iv < 0.30
            else "fuerte" if iv < 0.50 else "SOSPECHOSO (> 0.50)")


FOLDS = [(r, k) for r in range(1, 6) for k in range(5)]


def fold_woe(vb: VarBinning, c: str) -> pd.DataFrame:
    """WoE por bin en cada uno de los 25 conjuntos de entrenamiento de la CV (bins fijos)."""
    lab = vb.bin_labels(dev[c], reason(c))
    out = {}
    for r, k in FOLDS:
        tr = dev[f"cv_r{r}"].to_numpy() != k
        t = pd.DataFrame({"bin": lab[tr], "y": y[tr]}).groupby("bin").y.agg(["size", "sum"])
        t = t.reindex(vb.labels).fillna(0)
        w, _ = woe_iv(t["size"] - t["sum"], t["sum"])
        out[(r, k)] = pd.Series(w, index=vb.labels)
    return pd.DataFrame(out)


def unstable_bins(vb: VarBinning, W: pd.DataFrame) -> list[str]:
    bad = []
    for b in vb.labels:
        if b in vb.neutral or b in vb.special_map.values():
            continue
        w = W.loc[b]
        flips = (np.sign(w) != np.sign(np.median(w))).mean() if abs(np.median(w)) > 0.05 else 0.0
        if w.std() > 0.25 and flips > 0.20:
            bad.append(b)
    return bad


binnings, tables, merges, summ = {}, [], [], []
for c in CANDS:
    dtype = "categorical" if c == "cluster" else "numerical"
    disc = dtype == "categorical" or is_discrete(dev[c])
    mbs = 0.01 if disc else PARAMS["min_bin_pop"]
    vb = fit_binning(c, dev[c], reason(c), y, dtype=dtype, min_bin_size=mbs, min_events=MIN_EV, min_event_rate_diff=0.005)
    # Estabilidad entre folds y fusión de bins inestables (solo numéricas: se elimina un corte)
    for it in range(5):
        W = fold_woe(vb, c)
        bad = unstable_bins(vb, W)
        if not bad or dtype != "numerical" or not vb.splits:
            break
        b = bad[0]
        i = vb.labels.index(b)
        num = len(vb.splits) + 1
        neigh = [j for j in (i - 1, i + 1) if 0 <= j < num]
        j = min(neigh, key=lambda j: abs(vb.woe[vb.labels[j]] - vb.woe[b]))
        cut = vb.splits[min(i, j)]
        merges.append({"variable": c, "iteración": it + 1, "bin inestable": b, "sd WoE": W.loc[b].std(), "corte eliminado": cut})
        vb.splits = [s for s in vb.splits if s != cut]
        specials = [l for l in vb.labels if l in vb.special_map.values()]
        vb.labels = [vb.num_label(q) for q in range(len(vb.splits) + 1)] + specials
        t0 = vb.table(dev[c], reason(c), y)
        vb.woe = dict(zip(t0.bin, t0.WoE))
    W = fold_woe(vb, c)
    t = vb.table(dev[c], reason(c), y)
    t["sd WoE folds"] = [0.0 if b in vb.neutral else W.loc[b].std() for b in t.bin]
    t["% folds mismo signo"] = [100.0 if b in vb.neutral else 100 * (np.sign(W.loc[b]) == np.sign(t.set_index("bin").loc[b, "WoE"])).mean() for b in t.bin]
    t["WoE neutral (< 30 eventos)"] = t.bin.isin(vb.neutral)
    t.insert(0, "variable", c)
    tables.append(t)
    binnings[c] = vb
    reg = t[~t.especial]
    rates = reg["tasa %"].to_numpy()
    mono = "n/a" if dtype == "categorical" or len(rates) < 2 else (
        "ascendente" if np.all(np.diff(rates) >= -1e-9) else "descendente" if np.all(np.diff(rates) <= 1e-9) else "NO MONÓTONA")
    iv = t.IV.sum()
    summ.append({"variable": c, "dimensión": DIM[c], "IV": iv, "clase IV": iv_class(iv), "bins (con dato)": len(reg),
                 "bins especiales": int(t.especial.sum()), "min bin %": 100 * mbs, "tendencia": mono,
                 "tasa mín–máx %": f"{rates.min():.1f}–{rates.max():.1f}" if len(rates) else "",
                 "IV de bins especiales": t.loc[t.especial, "IV"].sum(),
                 "sd WoE máx (bins con dato)": reg["sd WoE folds"].max() if len(reg) else np.nan,
                 "bins fusionados por inestabilidad": sum(m["variable"] == c for m in merges)})

woe_t = pd.concat(tables, ignore_index=True)
iv_t = pd.DataFrame(summ).sort_values("IV", ascending=False).reset_index(drop=True)
save_table(woe_t.round(4), "09_woe_iv")
save_table(iv_t.round(4), "09_iv_summary")
save_table(pd.DataFrame(merges, columns=["variable", "iteración", "bin inestable", "sd WoE", "corte eliminado"]).round(4), "09_unstable_merges")
with open(MODELS / "09_binning.pkl", "wb") as fh:
    pickle.dump(binnings, fh)

# ── QC ──────────────────────────────────────────────────────────────────────────────────
qc = QC("09")
qc.check("Solo desarrollo", len(dev) == 13_913, 13_913, len(dev))
g = woe_t.groupby("variable")
qc.check("Bins suman 100% de hogares por variable", bool((g["% hogares"].sum().sub(100).abs() < 1e-9).all()), "100%", "ok")
qc.check("Eventos por variable = 840", bool((g.eventos.sum() == y.sum()).all()), int(y.sum()), "ok")
small = woe_t[(~woe_t.especial) & (woe_t.eventos < MIN_EV)]
qc.check("≥ 30 eventos en todo bin con dato", small.empty, "0 bins", small[["variable", "bin", "eventos"]].values.tolist())
small_sp = woe_t[woe_t.especial & (woe_t.eventos < MIN_EV) & ~woe_t["WoE neutral (< 30 eventos)"]]
qc.check("Bins especiales < 30 eventos con WoE neutral", small_sp.empty, "0", small_sp[["variable", "bin"]].values.tolist())
nonmono = iv_t[iv_t.tendencia == "NO MONÓTONA"]
qc.check("Monotonicidad en bins con dato", nonmono.empty, "0 variables", nonmono.variable.tolist())
unst = woe_t[(~woe_t.especial) & (woe_t["sd WoE folds"] > 0.25) & (woe_t["% folds mismo signo"] < 80)]
qc.check("Sin bins inestables tras fusión", unst.empty, "0", unst[["variable", "bin"]].values.tolist(), severity="warn")
sus = iv_t[iv_t.IV > PARAMS["iv_suspect"]]
qc.check("IV > 0.50 (sospecha de fuga: investigar)", sus.empty, "0", sus[["variable", "IV"]].round(3).values.tolist(), severity="warn")
print(f"  [INFO] Pasan IV ≥ 0.02: {int((iv_t.IV >= PARAMS['iv_min']).sum())} de {len(iv_t)}")

# ── Figura: tasa por bin, variables con IV ≥ 0.02 ─────────────────────────────────────────
INK, MUTED, GRID, BLUE, GRAY = "#0b0b0b", "#52514e", "#e6e5e0", "#2a78d6", "#a3a29c"
show = iv_t[iv_t.IV >= PARAMS["iv_min"]].variable.tolist()
ncol = 5
nrow = int(np.ceil(len(show) / ncol))
fig, axes = plt.subplots(nrow, ncol, figsize=(17, 2.9 * nrow), sharey=True)
for ax in axes.flat[len(show):]:
    ax.axis("off")
for ax, v in zip(axes.flat, show):
    t = woe_t[woe_t.variable == v].reset_index(drop=True)
    labs = []
    for _, r in t.iterrows():
        b = r.bin
        if r.especial:
            labs.append(b.replace("_", " "))
        elif b.startswith("["):
            lo, hi = b.strip("[)").split(", ")
            labs.append(f"< {float(hi):.3g}" if lo == "-inf" else f"≥ {float(lo):.3g}" if hi == "inf" else f"{float(lo):.3g}–{float(hi):.3g}")
        else:
            labs.append(b)
    ax.bar(range(len(t)), t["tasa %"], color=[GRAY if e else BLUE for e in t.especial], width=0.8)
    ax.axhline(100 * y.mean(), color=MUTED, lw=1, ls="--")
    ax.set_xticks(range(len(t)), labs, rotation=60, ha="right", fontsize=6, color=MUTED)
    ivv = iv_t.set_index("variable").loc[v, "IV"]
    ax.set_title(f"{v}\nIV = {ivv:.3f}", fontsize=8, color=INK, loc="left")
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=MUTED, length=0, labelsize=6.5)
for ax in axes[:, 0]:
    ax.set_ylabel("tasa hard %", color=MUTED, fontsize=8)
fig.suptitle("Tasa de hard churn por bin · variables con IV ≥ 0.02, orden por IV · desarrollo [DATA-SINT]"
             "  (gris = no aplica / sin dato; línea = tasa base)", x=0.01, ha="left", color=INK, fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.985))
fig.savefig(FIGURES / "09_bins_rate.png", dpi=120)

print(iv_t[["variable", "IV", "clase IV", "bins (con dato)", "bins especiales", "tendencia", "tasa mín–máx %",
            "IV de bins especiales", "sd WoE máx (bins con dato)", "bins fusionados por inestabilidad"]].round(3).to_string(index=False))
qc.gate()
