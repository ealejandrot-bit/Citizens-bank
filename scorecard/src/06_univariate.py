"""Paso 6 · Análisis univariado (solo muestra de desarrollo; el holdout no se mira).

Por predictor candidato:
- distribución churn = 1 vs 0 (mediana, p25, p75), % missing por grupo;
- effect size: Cliff's δ = 2U/(n₁n₀) − 1 (no paramétrico, robusto a colas), p-valor Mann-Whitney;
  magnitud según Romano et al. (|δ| < 0.147 despreciable, < 0.33 pequeño, < 0.474 mediano, resto grande);
- tasa de churn por decil (continuas) o por categoría (flags, conteos, ≤ 10 valores);
- tasa de churn por razón de missing (ok / no_aplica / sin_dato);
- δ por segmento (HNW / UHNW) y consistencia de signo;
- binarias (0/1) e infladas en su mínimo (≥ 70% en el mínimo, p. ej. conteos en 0): risk ratio tasa|1 ÷ tasa|0 con IC 95% (log-RR) y p de Fisher. δ de Cliff subestima flags
  raros (con prevalencia p, |δ| ≤ p aun con lift alto), así que la evidencia en binarias se lee por RR:
  fuerte (RR ≥ 2 y IC inf > 1), moderada (RR ≥ 1.5 e IC inf > 1), débil (IC excluye 1), sin evidencia;
- lift máximo de decil / categoría (con dato, ≥ 30 eventos) para todas;
- dirección observada (signo de δ) vs esperada (paso 2): marca discrepancias.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd
from scipy.stats import fisher_exact, mannwhitneyu

from common import FIGURES, OUT, PARAMS, QC, TABLES, save_table

T = PARAMS["target_primary"]
X = pd.read_pickle(OUT / "data" / "05_features.pkl")
meta = pd.read_csv(OUT / "data" / "05_predictor_meta.csv").set_index("columna")
split = pd.read_csv(TABLES / "04_split.csv", usecols=["household_id", "muestra"])
X = X.merge(split, on="household_id")
dev = X[X.muestra == "desarrollo"].reset_index(drop=True)
y = dev[T].astype(int).to_numpy()
base_rate = y.mean()
predictors = meta.index.tolist()


def cliffs(x: np.ndarray, yy: np.ndarray) -> tuple[float, float, int, int]:
    m = ~np.isnan(x)
    a, b = x[m & (yy == 1)], x[m & (yy == 0)]
    if len(a) < 5 or len(b) < 5 or np.nanstd(x[m]) == 0:
        return np.nan, np.nan, len(a), len(b)
    u, p = mannwhitneyu(a, b, alternative="two-sided")
    return 2 * u / (len(a) * len(b)) - 1, p, len(a), len(b)


def magnitude(d: float) -> str:
    if np.isnan(d):
        return "n/a"
    a = abs(d)
    return "despreciable" if a < 0.147 else "pequeño" if a < 0.33 else "mediano" if a < 0.474 else "grande"


rows, dec_rows = [], []
seg = dev["segment"].to_numpy()
for c in predictors:
    x = dev[c].astype(float).to_numpy()
    d, p, n1, n0 = cliffs(x, y)
    d_h, _, _, _ = cliffs(x[seg == 0], y[seg == 0])
    d_u, _, n1u, _ = cliffs(x[seg == 1], y[seg == 1])
    xv = x[~np.isnan(x)]
    vals, cnt = np.unique(xv, return_counts=True)
    mode, mode_share = vals[cnt.argmax()], cnt.max() / len(xv)
    binary = set(vals) <= {0.0, 1.0} and len(vals) == 2
    zinfl = not binary and mode_share >= 0.70 and mode == xv.min()   # inflada en su mínimo (p. ej. conteos en 0)
    rr = rr_lo = rr_hi = p_f = np.nan
    if binary or zinfl:
        m = ~np.isnan(x)
        hi = x > mode if zinfl else x == 1
        a, n_a = y[m & hi].sum(), (m & hi).sum()
        b, n_b = y[m & ~hi].sum(), (m & ~hi).sum()
        rr = (a / n_a) / (b / n_b)
        se = np.sqrt(1 / a - 1 / n_a + 1 / b - 1 / n_b) if a > 0 and b > 0 else np.nan
        rr_lo, rr_hi = rr * np.exp(-1.96 * se), rr * np.exp(1.96 * se)
        p_f = fisher_exact([[a, n_a - a], [b, n_b - b]])[1]
    exp = meta.loc[c, "dirección_esperada"] if isinstance(meta.loc[c, "dirección_esperada"], str) else "?"
    obs = "n/a" if np.isnan(d) else ("+" if d > 0 else "−" if d < 0 else "0")
    evid = magnitude(d)
    if binary or zinfl:
        rr_eff = rr if rr >= 1 else 1 / rr
        lo_eff = rr_lo if rr >= 1 else 1 / rr_hi
        evid = ("RR fuerte" if rr_eff >= 2 and lo_eff > 1 else "RR moderado" if rr_eff >= 1.5 and lo_eff > 1
                else "RR débil" if lo_eff > 1 else "despreciable")
        p = p_f
    if exp in ("+", "−") and obs in ("+", "−") and evid != "despreciable" and p < 0.05:
        agree = "coincide" if exp == obs else "DISCREPANCIA"
    elif exp in ("+", "−"):
        agree = "sin evidencia"
    else:
        agree = "sin hipótesis"
    q = lambda g, pct: np.nanpercentile(x[g], pct) if np.isfinite(x[g]).any() else np.nan
    g1, g0 = y == 1, y == 0
    miss = X.columns.str.fullmatch(f"{c}__miss").any()
    rows.append({
        "variable": c, "dimensión": meta.loc[c, "dimensión"],
        "mediana churn": q(g1, 50), "p25–p75 churn": f"{q(g1, 25):.4g} – {q(g1, 75):.4g}",
        "mediana no churn": q(g0, 50), "p25–p75 no churn": f"{q(g0, 25):.4g} – {q(g0, 75):.4g}",
        "% missing churn": 100 * np.isnan(x[g1]).mean(), "% missing no churn": 100 * np.isnan(x[g0]).mean(),
        "δ Cliff": d, "tipo efecto": "RR 1 vs 0" if binary else f"RR > {mode:g} vs = {mode:g}" if zinfl else "δ",
        "RR": rr, "IC95 RR": "" if not (binary or zinfl) else f"[{rr_lo:.2f}, {rr_hi:.2f}]",
        "p (MW o Fisher)": p, "magnitud": evid,
        "δ HNW": d_h, "δ UHNW": d_u, "eventos UHNW con dato": n1u,
        "signo estable por segmento": "n/a" if np.isnan(d_h) or np.isnan(d_u) or abs(d_u) < 0.147
        else ("sí" if np.sign(d_h) == np.sign(d_u) else "NO"),
        "dirección esperada": exp, "dirección observada": obs, "evaluación": agree,
    })
    # Tasa de churn por decil / categoría
    s = pd.Series(x)
    nun = s.nunique()
    if nun <= 10:
        grp = s.round(6).astype("string").fillna("NaN")
    else:
        grp = pd.qcut(s, 10, duplicates="drop").astype("string").fillna("NaN")
    if miss:  # separa no_aplica / sin_dato
        reason = dev[f"{c}__miss"]
        grp = grp.where(reason == "ok", "NaN:" + reason)
    t = pd.DataFrame({"grupo": grp, "y": y}).groupby("grupo", sort=False).agg(hogares=("y", "size"), eventos=("y", "sum"))
    t["tasa %"] = 100 * t.eventos / t.hogares
    t["lift"] = t["tasa %"] / (100 * base_rate)
    t["orden"] = [(1, float(str(i).strip("([").split(",")[0])) if str(i)[:1] in "([" else
                  (0, float(i)) if str(i).replace(".", "", 1).replace("-", "", 1).isdigit() else (2, 0) for i in t.index]
    t = t.sort_values("orden").drop(columns="orden").reset_index()
    t.insert(0, "variable", c)
    dec_rows.append(t)
    ok = ~t.grupo.astype(str).str.startswith("NaN") & (t.eventos >= PARAMS["min_bin_events"])
    rows[-1]["lift máx (grupo ≥ 30 eventos)"] = t.loc[ok, "lift"].max()

uni = pd.DataFrame(rows)
EVID_ORDER = {"RR fuerte": 0, "grande": 0, "mediano": 1, "RR moderado": 1, "pequeño": 2, "RR débil": 2, "despreciable": 3, "n/a": 4}
uni = uni.assign(_o=uni.magnitud.map(EVID_ORDER), _d=-uni["δ Cliff"].abs()).sort_values(["_o", "_d"]).drop(columns=["_o", "_d"])
dec = pd.concat(dec_rows, ignore_index=True)
save_table(uni.round(4), "06_univariate")
save_table(dec.round(3), "06_rate_by_decile")
disc = uni[uni["evaluación"] == "DISCREPANCIA"]
save_table(disc.round(4), "06_sign_discrepancies")

qc = QC("06")
qc.check("Solo desarrollo (holdout no usado)", set(dev.muestra) == {"desarrollo"} and len(dev) == 13_913, 13_913, len(dev))
qc.check("Todos los candidatos evaluados", len(uni) == len(predictors), len(predictors), len(uni))
qc.check("Tablas por decil: hogares suman el total de desarrollo por variable",
         bool((dec.groupby("variable").hogares.sum() == len(dev)).all()), len(dev), "ok" if (dec.groupby("variable").hogares.sum() == len(dev)).all() else "diferencias")
qc.check("Tablas por decil: eventos suman 840 por variable", bool((dec.groupby("variable").eventos.sum() == y.sum()).all()), int(y.sum()), "ok")
qc.check("Discrepancias de signo (se investigan, no se ocultan)", disc.empty, "0", disc["variable"].tolist(), severity="warn")
unstable = uni[uni["signo estable por segmento"] == "NO"]
qc.check("Signo estable HNW vs UHNW (|δ UHNW| ≥ 0.147)", unstable.empty, "0", unstable["variable"].tolist(), severity="warn")

# ── Figuras ─────────────────────────────────────────────────────────────────────────────
INK, MUTED, GRID, BLUE, GRAY = "#0b0b0b", "#52514e", "#e6e5e0", "#2a78d6", "#a3a29c"


def style(ax):
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=MUTED, length=0, labelsize=7)


def short(g, i):
    g = str(g)
    if g.startswith("NaN"):
        return {"NaN:no_aplica": "no aplica", "NaN:sin_dato": "sin dato"}.get(g, "sin dato")
    return f"D{i + 1}" if g[:1] in "([" else g.replace(".0", "")


# (a) 12 señales continuas con mayor |δ|: tasa por decil
cont = uni[(uni["tipo efecto"] == "δ") & (uni.variable.map(lambda v: meta.loc[v, "rol"]) == "señal")].head(12).variable.tolist()
fig, axes = plt.subplots(3, 4, figsize=(15, 9), sharey=True)
for ax, v in zip(axes.flat, cont):
    t = dec[dec.variable == v].reset_index(drop=True)
    ax.bar(range(len(t)), t["tasa %"], color=[GRAY if str(g).startswith("NaN") else BLUE for g in t.grupo], width=0.8)
    ax.axhline(100 * base_rate, color=MUTED, lw=1, ls="--")
    ax.set_xticks(range(len(t)), [short(g, i) for i, g in enumerate(t.grupo)], rotation=90, fontsize=6.5, color=MUTED)
    ax.set_title(f"{v}\nδ = {uni.set_index('variable').loc[v, 'δ Cliff']:+.2f}", fontsize=8.5, color=INK, loc="left")
    style(ax)
for ax in axes[:, 0]:
    ax.set_ylabel("tasa hard %", color=MUTED)
fig.suptitle("Tasa de hard churn por decil · 12 señales continuas con mayor |δ| · desarrollo [DATA-SINT]"
             "  (D1 = decil más bajo; gris = sin dato / no aplica; línea = tasa base 6.04%)", x=0.01, ha="left", color=INK, fontsize=11)
fig.tight_layout()
fig.savefig(FIGURES / "06_rate_by_decile_top12.png", dpi=140)
plt.close(fig)

# (b) Forest plot del RR para binarias e infladas en su mínimo
rrt = uni[uni["tipo efecto"] != "δ"].dropna(subset=["RR"]).sort_values("RR")
lo = rrt["IC95 RR"].str.extract(r"\[([\d.]+),")[0].astype(float)
hi = rrt["IC95 RR"].str.extract(r", ([\d.]+)\]")[0].astype(float)
fig, ax = plt.subplots(figsize=(9, 0.32 * len(rrt) + 1.2))
yy = np.arange(len(rrt))
ax.hlines(yy, lo, hi, color=BLUE, lw=2)
ax.plot(rrt["RR"], yy, "o", color=BLUE, ms=6)
ax.axvline(1, color=MUTED, lw=1, ls="--")
ax.set_xscale("log")
ax.set_xticks([0.5, 1, 2, 4, 8], ["0.5", "1", "2", "4", "8"])
ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
ax.set_yticks(yy, [f"{v}  ({t.replace('RR ', '')})" for v, t in zip(rrt.variable, rrt["tipo efecto"])], fontsize=7.5, color=INK)
ax.set_xlabel("risk ratio de hard churn (IC 95%, escala log)", color=MUTED)
ax.set_title("Binarias y conteos inflados en cero: risk ratio · desarrollo [DATA-SINT]", loc="left", color=INK, fontsize=11)
ax.grid(axis="x", color=GRID, lw=0.8)
ax.set_axisbelow(True)
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.tick_params(colors=MUTED, length=0)
fig.tight_layout()
fig.savefig(FIGURES / "06_risk_ratio_binary.png", dpi=140, bbox_inches="tight")

print(uni[["variable", "δ Cliff", "tipo efecto", "RR", "lift máx (grupo ≥ 30 eventos)", "magnitud", "δ HNW", "δ UHNW", "dirección esperada", "dirección observada", "evaluación"]]
      .round(3).to_string(index=False))
qc.gate()
