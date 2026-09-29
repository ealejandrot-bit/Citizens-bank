"""Paso 13 · Validación en holdout (A operativo y A-lite ejecutivo) vs reglas existentes.

- Discriminación con IC bootstrap 500 (pareado, estratificado por evento): AUC, PR-AUC, KS, Gini.
- Lift y gains por decil de probabilidad calibrada.
- Decisivas: captura de eventos ponderada por relationship_value en el decil top; captura de value_lost_6m;
  tasa de falsos positivos en Crítico.
- Por segmento (UHNW con 24 eventos: IC anchos, se reportan).
- Benchmark obligatorio: multi_signal_count y multi_signal_flag (captura con desempate aleatorio esperado).
  QC gate: el campeón debe superar a ambos en AUC y en captura del decil top con IC sin traslape; si no → detener.
- Criterios de aprobación explícitos (C1–C7, D13.1).
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score

from common import FIGURES, OUT, PARAMS, QC, SCORED, SEED, TABLES, load_raw, save_table, set_seed
from metrics import bootstrap, ci, decile_table, ks, top_capture_ties

set_seed()
T = PARAMS["target_primary"]
raw = load_raw()[["household_id", T, "value_lost_6m", "multi_signal_count", "multi_signal_flag", "relationship_value"]]
sc = pd.read_csv(SCORED / "scored_households.csv")
h = sc[(sc.muestra == "holdout") & ~sc.churn_excluded].merge(raw, on=["household_id", "relationship_value"])
y = h[T].astype(int).to_numpy()
rv = h.relationship_value.to_numpy()
lv = h.value_lost_6m.to_numpy()
seg = h.segment.to_numpy()
MODELS_ = {"A": h.probabilidad.to_numpy(), "A-lite": h.probabilidad_lite.to_numpy(),
           "multi_signal_count": h.multi_signal_count.to_numpy(float), "multi_signal_flag": h.multi_signal_flag.to_numpy(float)}
B = PARAMS["n_bootstrap"]
qc = QC("13")
qc.check("Holdout elegible", len(h) == 5_964 and y.sum() == 360, "5,964 / 360", f"{len(h):,} / {int(y.sum())}")

# ── Métricas con IC ─────────────────────────────────────────────────────────────────────
FUN = {
    "AUC": lambda yy, pp, bi: roc_auc_score(yy, pp),
    "PR-AUC": lambda yy, pp, bi: average_precision_score(yy, pp),
    "KS": lambda yy, pp, bi: ks(yy, pp),
    "captura eventos decil top": lambda yy, pp, bi: top_capture_ties(yy, pp),
    "captura valor (RV) decil top": lambda yy, pp, bi: top_capture_ties(yy, pp, rv[bi]),
    "captura value_lost decil top": lambda yy, pp, bi: top_capture_ties(yy, pp, lv[bi]),
}
point = {m: {"AUC": roc_auc_score(y, p), "PR-AUC": average_precision_score(y, p), "KS": ks(y, p),
             "captura eventos decil top": top_capture_ties(y, p), "captura valor (RV) decil top": top_capture_ties(y, p, rv),
             "captura value_lost decil top": top_capture_ties(y, p, lv)} for m, p in MODELS_.items()}
boots = {k: bootstrap(y, MODELS_, f, n=B, seed=SEED, strata=y) for k, f in FUN.items()}
rows = []
for m in MODELS_:
    r = {"modelo": m}
    for k in FUN:
        lo, hi = ci(boots[k][m])
        r[k] = point[m][k]
        r[f"IC95 {k}"] = f"[{lo:.3f}, {hi:.3f}]"
    r["Gini"] = 2 * point[m]["AUC"] - 1
    rows.append(r)
met = pd.DataFrame(rows)
save_table(met.round(4), "13_holdout_metrics")

# Diferencias pareadas A − benchmarks
diff = []
for champ in ("A", "A-lite"):
    for bm in ("multi_signal_count", "multi_signal_flag"):
        for k in ("AUC", "captura eventos decil top", "captura valor (RV) decil top"):
            d = boots[k][champ] - boots[k][bm]
            lo_c, hi_c = ci(boots[k][champ])
            lo_b, hi_b = ci(boots[k][bm])
            diff.append({"modelo": champ, "benchmark": bm, "métrica": k, "modelo (punto)": point[champ][k], "benchmark (punto)": point[bm][k],
                         "Δ": point[champ][k] - point[bm][k], "IC95 Δ pareado": "[%.3f, %.3f]" % ci(d),
                         "IC sin traslape": lo_c > hi_b})
diff = pd.DataFrame(diff)
save_table(diff.round(4), "13_benchmark_comparison")

# ── Deciles ─────────────────────────────────────────────────────────────────────────────
dec = {m: decile_table(y, MODELS_[m], rv, lv) for m in ("A", "A-lite")}
for m, t in dec.items():
    save_table(t.round(3), f"13_deciles_{m.replace('-', '').lower()}")

# ── Falsos positivos en Crítico ─────────────────────────────────────────────────────────
fp = []
for m, col in (("A", "tramo"), ("A-lite", "tramo_lite")):
    for t in ("Crítico", "Alto"):
        msk = (h[col] == t).to_numpy()
        fp.append({"modelo": m, "tramo": t, "hogares": int(msk.sum()), "churners": int(y[msk].sum()), "precisión %": 100 * y[msk].mean(),
                   "tasa falsos positivos % (no churners en el tramo)": 100 * (1 - y[msk].mean()),
                   "% de los no churners alertados": 100 * ((msk) & (y == 0)).sum() / (y == 0).sum(),
                   "RV alertado sin churn $M": rv[msk & (y == 0)].sum() / 1e6})
fp = pd.DataFrame(fp)
save_table(fp.round(3), "13_false_positives")

# ── Por segmento ────────────────────────────────────────────────────────────────────────
sg = []
for s_ in ("HNW", "UHNW"):
    msk = seg == s_
    ys = y[msk]
    for m in ("A", "A-lite", "multi_signal_count"):
        ps = MODELS_[m][msk]
        bb = bootstrap(ys, {m: ps}, lambda yy, pp, bi: roc_auc_score(yy, pp), n=B, seed=SEED, strata=ys)[m]
        bk = bootstrap(ys, {m: ps}, lambda yy, pp, bi: top_capture_ties(yy, pp), n=B, seed=SEED, strata=ys)[m]
        sg.append({"segmento": s_, "modelo": m, "hogares": int(msk.sum()), "eventos": int(ys.sum()), "AUC": roc_auc_score(ys, ps),
                   "IC95 AUC": "[%.3f, %.3f]" % ci(bb), "KS": ks(ys, ps), "PR-AUC": average_precision_score(ys, ps),
                   "captura decil top": top_capture_ties(ys, ps), "IC95 captura": "[%.3f, %.3f]" % ci(bk),
                   "captura valor decil top": top_capture_ties(ys, ps, rv[msk])})
sg = pd.DataFrame(sg)
save_table(sg.round(4), "13_by_segment")

# ── Criterios de aprobación (D13.1) ─────────────────────────────────────────────────────
def crit_rows(m):
    pm = point[m]
    lo_auc = ci(boots["AUC"][m])[0]
    d_m = dec[m]
    rate = d_m["tasa %"].to_numpy()
    mono = pd.Series(rate).corr(pd.Series(np.arange(10)), method="spearman")
    beats = diff[(diff.modelo == m) & diff.métrica.isin(["AUC", "captura eventos decil top"])]["IC sin traslape"].all()
    uh = sg[(sg.segmento == "UHNW") & (sg.modelo == m)].iloc[0]
    return [
        ("C1 · supera a multi_signal_count y multi_signal_flag en AUC y captura decil top (IC sin traslape) [GATE]", beats, "sí", "sí" if beats else "no"),
        ("C2 · AUC holdout: límite inferior IC95 > 0.65", lo_auc > 0.65, "> 0.65", f"{lo_auc:.3f}"),
        ("C3 · KS ≥ 0.25", pm["KS"] >= 0.25, "≥ 0.25", f"{pm['KS']:.3f}"),
        ("C4 · captura de eventos en decil top ≥ 30% (3× azar)", pm["captura eventos decil top"] >= 0.30, "≥ 30%", f"{100 * pm['captura eventos decil top']:.1f}%"),
        ("C5 · captura de valor (RV) en decil top ≥ 25%", pm["captura valor (RV) decil top"] >= 0.25, "≥ 25%", f"{100 * pm['captura valor (RV) decil top']:.1f}%"),
        ("C6 · tasa por decil monótona (Spearman decil vs tasa ≤ −0.90)", mono <= -0.90, "≤ −0.90", f"{mono:.3f}"),
        ("C7 · UHNW: AUC ≥ 0.60 (informativo, 24 eventos)", uh.AUC >= 0.60, "≥ 0.60", f"{uh.AUC:.3f} {uh['IC95 AUC']}"),
    ]


cr = []
for m in ("A", "A-lite"):
    for name, ok, exp, obs in crit_rows(m):
        cr.append({"modelo": m, "criterio": name, "umbral": exp, "observado": obs, "cumple": "sí" if ok else "NO"})
cr = pd.DataFrame(cr)
save_table(cr, "13_approval_criteria")

for m in ("A", "A-lite"):
    rows_m = cr[cr.modelo == m]
    for _, r in rows_m.iterrows():
        sev = "gate" if "[GATE]" in r.criterio else "warn"
        qc.check(f"{m}: {r.criterio}", r.cumple == "sí", r.umbral, r.observado, severity=sev)
for m, t in dec.items():
    qc.check(f"{m}: deciles suman 100% de eventos", abs(t["captura acumulada %"].iloc[-1] - 100) < 1e-9 and t.eventos.sum() == y.sum(), "100%", f"{t['captura acumulada %'].iloc[-1]:.4f}%")

# ── Figuras ─────────────────────────────────────────────────────────────────────────────
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
COL = {"A": "#2a78d6", "A-lite": "#eb6834", "multi_signal_count": "#1baf7a", "multi_signal_flag": "#a3a29c"}
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
xs = np.linspace(0, 1, 101)
for ax, (wname, w) in zip(axes, [("eventos", None), ("valor de churners (RV)", rv)]):
    for m, p in MODELS_.items():
        g = [0] + [top_capture_ties(y, p, w, q) for q in xs[1:]]
        ax.plot(100 * xs, 100 * np.array(g), color=COL[m], lw=2, label=m)
    ax.plot([0, 100], [0, 100], color=MUTED, ls="--", lw=1, label="azar")
    ax.axvline(10, color=GRID, lw=1)
    ax.set_xlabel("% de hogares contactados (ordenados por riesgo)", color=MUTED)
    ax.set_ylabel(f"% de {wname} capturado", color=MUTED)
    ax.set_title(f"Curva de ganancias · {wname}", loc="left", color=INK, fontsize=10)
    ax.grid(color=GRID, lw=0.8)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=MUTED, length=0)
axes[0].legend(frameon=False, labelcolor=INK, fontsize=8, loc="lower right")
fig.suptitle("Holdout: modelo vs reglas existentes [DATA-SINT]", x=0.01, ha="left", color=INK, fontsize=11)
fig.tight_layout()
fig.savefig(FIGURES / "13_gains.png", dpi=140)
plt.close(fig)

fig, ax = plt.subplots(figsize=(8, 3.6))
for i, (m, c) in enumerate([("A", COL["A"]), ("A-lite", COL["A-lite"])]):
    t = dec[m]
    ax.bar(t.decil + (i - 0.5) * 0.38, t["tasa %"], 0.36, color=c, label=m)
ax.axhline(100 * y.mean(), color=MUTED, ls="--", lw=1)
ax.set_xticks(range(1, 11), [f"D{i}" for i in range(1, 11)])
ax.set_xlabel("decil de probabilidad (D1 = mayor riesgo)", color=MUTED)
ax.set_ylabel("tasa hard %", color=MUTED)
ax.set_title("Tasa de churn por decil · holdout [DATA-SINT]", loc="left", color=INK, fontsize=10)
ax.legend(frameon=False, labelcolor=INK)
ax.grid(axis="y", color=GRID, lw=0.8)
ax.set_axisbelow(True)
for sp in ("top", "right", "left"):
    ax.spines[sp].set_visible(False)
ax.tick_params(colors=MUTED, length=0)
fig.tight_layout()
fig.savefig(FIGURES / "13_deciles.png", dpi=140)

print(met.round(3).to_string(index=False))
print("\n" + diff.round(3).to_string(index=False))
print("\n" + dec["A"].round(2).to_string(index=False))
print("\n" + fp.round(2).to_string(index=False))
print("\n" + sg.round(3).to_string(index=False))
print("\n" + cr.to_string(index=False))
qc.gate()
