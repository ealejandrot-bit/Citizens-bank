"""Paso 14 · Calibración en cuatro capas (A y A-lite).

Principio (DM.1): todo parámetro de calibración se ajusta en desarrollo (OOF de la CV anidada); el holdout solo mide.
1. Modelo: Platt logit(p_cal) = a + b·logit(p) (ajustado en paso 12 sobre OOF). En holdout: pendiente b y
   intercepto de recalibración diagnósticos (0.8 ≤ b ≤ 1.2), Brier, esperado vs observado por decil (Wilson 95%),
   calibración en el agregado (media p_cal vs tasa observada). El shift de intercepto se decide con desarrollo.
2. Tramo: esperado (media p_cal) vs observado con Wilson 90%; tasa oficial por tramo con shrinkage beta-binomial
   p = (eventos + m·p_modelo) / (N + m), m = 30, estimada en desarrollo (OOF) y comparada con holdout.
3. Segmento y valor: HNW vs UHNW; Σ pᵢ·RVᵢ vs RV de churners por tramo y por quintil de RV; prueba de interacción con
   log RV en desarrollo (si descalibra la cola alta).
4. Overrides: precisión por regla (paso 12) vs la probabilidad que implica su tramo.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import brier_score_loss
from statsmodels.stats.proportion import proportion_confint

from common import FIGURES, OUT, PARAMS, QC, SCORED, TABLES, load_raw, save_table, set_seed

set_seed()
T = PARAMS["target_primary"]
M_SHRINK = 30
TRAMOS = ["Crítico", "Alto", "Vigilancia", "Estable"]
logit = lambda p: np.log(np.clip(p, 1e-9, 1 - 1e-9) / (1 - np.clip(p, 1e-9, 1 - 1e-9)))
expit = lambda z: 1 / (1 + np.exp(-z))
raw = load_raw()[["household_id", T]]
sc = pd.read_csv(SCORED / "scored_households.csv").merge(raw, on="household_id")
oof = pd.read_csv(OUT / "data" / "11_oof_dev.csv").merge(raw, on="household_id").merge(
    sc[["household_id", "segment", "relationship_value", "tramo", "tramo_lite"]], on="household_id")
hold = sc[(sc.muestra == "holdout") & ~sc.churn_excluded].reset_index(drop=True)
qc = QC("14")
SPEC = {"A": ("probabilidad", "oof_A", "tramo"), "A-lite": ("probabilidad_lite", "oof_A_lite", "tramo_lite")}
lb, ub = PARAMS["platt_b_range"]

L1, DEC, L2, L3s, L3v, L3q, INT = [], [], [], [], [], [], []
for m, (pcol, ocol, tcol) in SPEC.items():
    # ── Capa 1 · modelo ─────────────────────────────────────────────────────────────
    yd = oof[T].astype(int).to_numpy()
    platt = sm.Logit(yd, sm.add_constant(logit(oof[ocol].to_numpy()))).fit(disp=0)
    a, b = platt.params
    p_oof = expit(a + b * logit(oof[ocol].to_numpy()))
    yh, ph = hold[T].astype(int).to_numpy(), hold[pcol].to_numpy()
    rec = sm.Logit(yh, sm.add_constant(logit(ph))).fit(disp=0)          # diagnóstico: recalibración en holdout
    a_h, b_h = rec.params
    b_ci = rec.conf_int()[1]
    itl = sm.GLM(yh, np.ones((len(yh), 1)), family=sm.families.Binomial(), offset=logit(ph)).fit()   # calibración en el agregado
    shift = itl.params[0]
    shift_ci = itl.conf_int()[0]
    L1.append({"modelo": m, "Platt a (dev OOF)": a, "Platt b (dev OOF)": b, "b en [0.8, 1.2] (dev)": lb <= b <= ub,
               "b holdout (diagnóstico)": b_h, "IC95 b holdout": f"[{b_ci[0]:.3f}, {b_ci[1]:.3f}]", "b holdout en [0.8, 1.2]": lb <= b_h <= ub,
               "intercepto de ajuste holdout (logit)": shift, "IC95 intercepto": f"[{shift_ci[0]:.3f}, {shift_ci[1]:.3f}]",
               "media p_cal holdout %": 100 * ph.mean(), "tasa observada holdout %": 100 * yh.mean(),
               "media p_cal dev OOF %": 100 * p_oof.mean(), "tasa dev %": 100 * yd.mean(),
               "Brier holdout": brier_score_loss(yh, ph), "Brier sin modelo (tasa base)": brier_score_loss(yh, np.full_like(ph, yd.mean())),
               "shift de intercepto aplicado": "no (dev: media = tasa; holdout: IC incluye 0)" if shift_ci[0] < 0 < shift_ci[1] else "REVISAR"})
    r = pd.Series(ph).rank(method="first", ascending=False)
    d = np.ceil(r / len(ph) * 10).astype(int).to_numpy()
    for k in range(1, 11):
        msk = d == k
        lo, hi = proportion_confint(yh[msk].sum(), msk.sum(), alpha=0.05, method="wilson")
        DEC.append({"modelo": m, "decil": k, "hogares": int(msk.sum()), "esperado %": 100 * ph[msk].mean(), "observado %": 100 * yh[msk].mean(),
                    "Wilson 95% inf": 100 * lo, "Wilson 95% sup": 100 * hi, "esperado dentro del IC": lo <= ph[msk].mean() <= hi})
    # ── Capa 2 · tramo ──────────────────────────────────────────────────────────────
    to = oof[tcol].to_numpy()
    th = hold[tcol].to_numpy()
    for t in TRAMOS:
        md, mh = to == t, th == t
        n_d, e_d = int(md.sum()), int(yd[md].sum())
        p_mod = p_oof[md].mean()
        shrunk = (e_d + M_SHRINK * p_mod) / (n_d + M_SHRINK)
        lo, hi = proportion_confint(yh[mh].sum(), mh.sum(), alpha=0.10, method="wilson")
        L2.append({"modelo": m, "tramo": t, "N dev": n_d, "eventos dev": e_d, "p_modelo dev (media OOF) %": 100 * p_mod,
                   "observado dev %": 100 * e_d / n_d, "tasa oficial (shrinkage m=30) %": 100 * shrunk,
                   "N holdout": int(mh.sum()), "esperado holdout (media p_cal) %": 100 * ph[mh].mean(),
                   "observado holdout %": 100 * yh[mh].mean(), "Wilson 90% holdout": f"[{100 * lo:.1f}, {100 * hi:.1f}]",
                   "tasa oficial dentro del Wilson 90%": lo <= shrunk <= hi, "esperado dentro del Wilson 90%": lo <= ph[mh].mean() <= hi})
    # ── Capa 3 · segmento y valor ───────────────────────────────────────────────────
    for s_ in ("HNW", "UHNW"):
        mh = (hold.segment == s_).to_numpy()
        lo, hi = proportion_confint(yh[mh].sum(), mh.sum(), alpha=0.10, method="wilson")
        L3s.append({"modelo": m, "segmento": s_, "hogares": int(mh.sum()), "eventos": int(yh[mh].sum()), "esperado %": 100 * ph[mh].mean(),
                    "observado %": 100 * yh[mh].mean(), "Wilson 90%": f"[{100 * lo:.1f}, {100 * hi:.1f}]", "esperado dentro": lo <= ph[mh].mean() <= hi})
    rvh = hold.relationship_value.to_numpy()
    for t in TRAMOS + ["Total"]:
        mh = np.ones(len(th), bool) if t == "Total" else th == t
        idx = np.flatnonzero(mh)
        rng = np.random.default_rng(42)
        bs = []
        for _ in range(PARAMS["n_bootstrap"]):
            bi = rng.choice(idx, len(idx), replace=True)
            bs.append((yh[bi] * rvh[bi]).sum() / (ph[bi] * rvh[bi]).sum())
        top1 = (yh[mh] * rvh[mh]).max() / max((yh[mh] * rvh[mh]).sum(), 1)
        L3v.append({"modelo": m, "tramo": t, "valor esperado Σ p·RV $M": (ph[mh] * rvh[mh]).sum() / 1e6,
                    "RV de churners observado $M": (yh[mh] * rvh[mh]).sum() / 1e6,
                    "razón observado / esperado": (yh[mh] * rvh[mh]).sum() / (ph[mh] * rvh[mh]).sum(),
                    "IC95 razón (bootstrap hogares)": "[%.2f, %.2f]" % tuple(np.percentile(bs, [2.5, 97.5])),
                    "1 = dentro del IC": np.percentile(bs, 2.5) <= 1 <= np.percentile(bs, 97.5),
                    "% del valor observado en el mayor churner": 100 * top1})
    qv = pd.qcut(pd.Series(rvh).rank(method="first"), 5, labels=[f"Q{i}" for i in range(1, 6)]).to_numpy()
    top5 = rvh >= np.quantile(rvh, 0.95)
    for q, mh in [(q, qv == q) for q in [f"Q{i}" for i in range(1, 6)]] + [("top 5% RV", top5)]:
        lo, hi = proportion_confint(yh[mh].sum(), mh.sum(), alpha=0.10, method="wilson")
        L3q.append({"modelo": m, "banda RV": q, "RV mín–máx $M": f"{rvh[mh].min() / 1e6:.1f}–{rvh[mh].max() / 1e6:.1f}", "hogares": int(mh.sum()),
                    "eventos": int(yh[mh].sum()), "esperado %": 100 * ph[mh].mean(), "observado %": 100 * yh[mh].mean(),
                    "Wilson 90%": f"[{100 * lo:.1f}, {100 * hi:.1f}]", "esperado dentro": lo <= ph[mh].mean() <= hi,
                    "valor esperado $M": (ph[mh] * rvh[mh]).sum() / 1e6, "valor observado $M": (yh[mh] * rvh[mh]).sum() / 1e6})
    # Interacción con log RV (desarrollo): ¿la calibración depende del tamaño?
    Xi = sm.add_constant(np.column_stack([logit(p_oof), np.log10(oof.relationship_value.to_numpy()) - 6.7]))
    ri = sm.Logit(yd, Xi).fit(disp=0)
    INT.append({"modelo": m, "β log10 RV (centrado)": ri.params[2], "IC95": f"[{ri.conf_int()[2][0]:.3f}, {ri.conf_int()[2][1]:.3f}]",
                "p-valor": ri.pvalues[2], "decisión": "sin interacción (p ≥ 0.05)" if ri.pvalues[2] >= 0.05 else "REVISAR interacción con log valor"})

l1, dec, l2, l3s, l3v, l3q, it = map(pd.DataFrame, (L1, DEC, L2, L3s, L3v, L3q, INT))
# Capa 4 · overrides
ovs = []
for m, tag in (("A", "a"), ("A-lite", "alite")):
    ov = pd.read_csv(TABLES / f"12_overrides_{tag}.csv")
    off = l2[(l2.modelo == m)].set_index("tramo")["tasa oficial (shrinkage m=30) %"]
    for _, r in ov.iterrows():
        tgt = r["tramo asignado"]
        ovs.append({"modelo": m, "regla": r.regla, "tramo": tgt, "precisión dev %": r["precisión dev %"], "precisión holdout %": r["precisión holdout %"],
                    "tasa oficial del tramo %": off.get(tgt, np.nan),
                    "precisión ≥ tasa oficial del tramo (holdout)": (r["precisión holdout %"] >= off.get(tgt, np.inf)) if tgt != "eliminado" else None})
l4 = pd.DataFrame(ovs)
for df_, name in [(l1, "14_layer1_model"), (dec, "14_layer1_deciles"), (l2, "14_layer2_tramo"), (l3s, "14_layer3_segment"),
                  (l3v, "14_layer3_value_tramo"), (l3q, "14_layer3_value_quintile"), (it, "14_layer3_logrv_interaction"), (l4, "14_layer4_overrides")]:
    save_table(df_.round(4), name)

# ── QC ──────────────────────────────────────────────────────────────────────────────────
for _, r in l1.iterrows():
    qc.check(f"{r.modelo}: Platt b en [0.8, 1.2] (dev OOF)", bool(r["b en [0.8, 1.2] (dev)"]), "[0.8, 1.2]", f"{r['Platt b (dev OOF)']:.3f}")
    qc.check(f"{r.modelo}: b de recalibración en holdout en [0.8, 1.2]", bool(r["b holdout en [0.8, 1.2]"]), "[0.8, 1.2]",
             f"{r['b holdout (diagnóstico)']:.3f} {r['IC95 b holdout']}", severity="warn")
    qc.check(f"{r.modelo}: calibración en el agregado (IC del intercepto incluye 0)", r["shift de intercepto aplicado"].startswith("no"), "incluye 0",
             f"{r['intercepto de ajuste holdout (logit)']:+.3f} {r['IC95 intercepto']}", severity="warn")
    qc.check(f"{r.modelo}: Brier < Brier sin modelo", r["Brier holdout"] < r["Brier sin modelo (tasa base)"], f"< {r['Brier sin modelo (tasa base)']:.4f}", f"{r['Brier holdout']:.4f}")
for m in SPEC:
    bad = l2[(l2.modelo == m) & ~l2["tasa oficial dentro del Wilson 90%"]]
    qc.check(f"{m}: tasa oficial por tramo dentro de Wilson 90% del holdout", bad.empty, "4 de 4", f"{4 - len(bad)} de 4 (fuera: {bad.tramo.tolist()})", severity="warn")
    bs = l3s[(l3s.modelo == m) & ~l3s["esperado dentro"]]
    qc.check(f"{m}: calibración HNW y UHNW dentro de Wilson 90%", bs.empty, "2 de 2", f"{2 - len(bs)} de 2", severity="warn")
    dd = dec[(dec.modelo == m) & ~dec["esperado dentro del IC"]]
    qc.check(f"{m}: deciles con esperado dentro de Wilson 95%", len(dd) <= 1, "≥ 9 de 10", f"{10 - len(dd)} de 10", severity="warn")
    vv = l3v[(l3v.modelo == m) & ~l3v["1 = dentro del IC"]]
    qc.check(f"{m}: valor esperado vs observado por tramo (1 dentro del IC bootstrap)", vv.empty, "5 de 5", f"{5 - len(vv)} de 5 (fuera: {vv.tramo.tolist()})", severity="warn")
    iv_ = it[it.modelo == m].iloc[0]
    qc.check(f"{m}: sin descalibración por tamaño (interacción log RV, dev)", iv_["p-valor"] >= 0.05, "p ≥ 0.05", f"p = {iv_['p-valor']:.3f}", severity="warn")

# ── Figura: diagrama de fiabilidad ──────────────────────────────────────────────────────
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e6e5e0"
COL = {"A": "#2a78d6", "A-lite": "#eb6834"}
fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
for m in SPEC:
    t = dec[dec.modelo == m]
    axes[0].errorbar(t["esperado %"], t["observado %"], yerr=[t["observado %"] - t["Wilson 95% inf"], t["Wilson 95% sup"] - t["observado %"]],
                     fmt="o", color=COL[m], ms=6, capsize=3, label=m)
    t2 = l2[l2.modelo == m]
    axes[1].plot(range(4), t2["observado holdout %"], "o-", color=COL[m], lw=2, label=f"{m} · observado holdout")
    axes[1].plot(range(4), t2["tasa oficial (shrinkage m=30) %"], "s--", color=COL[m], lw=1, mfc="white", label=f"{m} · tasa oficial (dev)")
mx = dec["Wilson 95% sup"].max() * 1.05
axes[0].plot([0, mx], [0, mx], color=MUTED, ls="--", lw=1)
axes[0].set_xlabel("esperado (media p_cal) %", color=MUTED)
axes[0].set_ylabel("observado %", color=MUTED)
axes[0].set_title("Fiabilidad por decil · holdout (Wilson 95%)", loc="left", color=INK, fontsize=10)
axes[1].set_xticks(range(4), TRAMOS)
axes[1].set_yscale("log")
axes[1].set_yticks([2, 3, 5, 10, 20, 40], ["2", "3", "5", "10", "20", "40"])
axes[1].yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
axes[1].set_ylabel("tasa de churn % (escala log)", color=MUTED)
axes[1].set_title("Tasa oficial por tramo vs observado en holdout", loc="left", color=INK, fontsize=10)
for ax in axes:
    ax.grid(color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=MUTED, length=0)
    ax.legend(frameon=False, labelcolor=INK, fontsize=7.5)
fig.suptitle("Calibración [DATA-SINT]", x=0.01, ha="left", color=INK, fontsize=11)
fig.tight_layout()
fig.savefig(FIGURES / "14_calibration.png", dpi=140)

for df_ in (l1, dec, l2, l3s, l3v, l3q, it, l4):
    print("\n" + df_.round(3).to_string(index=False))
qc.gate()
