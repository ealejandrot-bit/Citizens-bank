"""Paso 1 · Target y churn rate.

Churn rate por hogares (logo) y por valor, por target (hard, soft, unión) y por segmento:
  (i)  valor en riesgo  = Σ relationship_value de hogares con evento ÷ Σ relationship_value
  (ii) valor perdido    = Σ value_lost_6m de hogares con evento ÷ Σ relationship_value
relationship_value se usa crudo (sin capping): la concentración es parte del fenómeno.
IC 95% por bootstrap de hogares (500 réplicas, estratificado por segmento): no altera el
estimador puntual, solo mide cuánto depende de pocos hogares grandes.
"""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import FIGURES, PARAMS, QC, SEED, TABLES, load_raw, save_table, set_seed

set_seed()
raw = load_raw()
excl = raw["churn_excluded"].astype(bool)
df = raw.loc[~excl].copy()
df["union_churn"] = ((df["hard_churn_6m"] == 1) | (df["soft_churn_3m"] == 1)).astype(int)
TARGETS = {"hard_churn_6m": "hard 6m", "soft_churn_3m": "soft 3m", "union_churn": "unión"}

qc = QC("01")
print("Exclusiones y definición")
qc.check("Excluidos fuera de la base de métricas", len(df) == 19_877, 19_877, len(df))
qc.check("hard y soft mutuamente excluyentes", int(((df.hard_churn_6m == 1) & (df.soft_churn_3m == 1)).sum()) == 0, 0,
         int(((df.hard_churn_6m == 1) & (df.soft_churn_3m == 1)).sum()))
qc.check("value_lost_6m = 0 sin evento", bool((df.loc[df.union_churn == 0, "value_lost_6m"] == 0).all()), "100% = 0",
         f"{(df.loc[df.union_churn == 0, 'value_lost_6m'] == 0).mean():.2%}")
qc.check("value_lost_6m ≤ relationship_value", bool((df.value_lost_6m <= df.relationship_value * (1 + 1e-9)).all()), "100%",
         f"{(df.value_lost_6m <= df.relationship_value * (1 + 1e-9)).mean():.2%}", severity="warn")

rv, vl = df["relationship_value"].to_numpy(), df["value_lost_6m"].to_numpy()
seg = df["segment"].to_numpy()


def rates(y: np.ndarray, idx: np.ndarray) -> tuple[float, float, float]:
    yy, r, v = y[idx], rv[idx], vl[idx]
    return yy.mean(), (r * yy).sum() / r.sum(), (v * yy).sum() / r.sum()


rng = np.random.default_rng(SEED)
B = PARAMS["n_bootstrap"]
seg_idx = {s: np.flatnonzero(seg == s) for s in ("HNW", "UHNW")}
# Réplicas estratificadas por segmento (preserva la mezcla HNW/UHNW)
boots = [np.concatenate([rng.choice(ix, len(ix), replace=True) for ix in seg_idx.values()]) for _ in range(B)]

rows = []
for t, lab in TARGETS.items():
    y = df[t].to_numpy().astype(int)
    for s, ix in [("Total", np.arange(len(df))), ("HNW", seg_idx["HNW"]), ("UHNW", seg_idx["UHNW"])]:
        logo, vrisk, vlost = rates(y, ix)
        # bootstrap: dentro del segmento se remuestrea solo ese segmento
        if s == "Total":
            bs = np.array([rates(y, b) for b in boots])
        else:
            bs = np.array([rates(y, rng.choice(ix, len(ix), replace=True)) for _ in range(B)])
        lo, hi = np.percentile(bs, [2.5, 97.5], axis=0)
        rows.append({
            "target": lab, "segmento": s, "hogares": len(ix), "eventos": int(y[ix].sum()),
            "churn hogares %": 100 * logo, "IC95 hogares": f"[{100 * lo[0]:.2f}, {100 * hi[0]:.2f}]",
            "RV total $M": rv[ix].sum() / 1e6, "RV con evento $M": (rv[ix] * y[ix]).sum() / 1e6,
            "churn valor (i) %": 100 * vrisk, "IC95 (i)": f"[{100 * lo[1]:.2f}, {100 * hi[1]:.2f}]",
            "value_lost $M": (vl[ix] * y[ix]).sum() / 1e6,
            "churn valor (ii) %": 100 * vlost, "IC95 (ii)": f"[{100 * lo[2]:.2f}, {100 * hi[2]:.2f}]",
            "brecha valor(i) − hogares pp": 100 * (vrisk - logo),
        })
tab = pd.DataFrame(rows)

# Consistencia aritmética: tasa de cartera = Σ share × tasa por segmento
print("\nConsistencia aritmética (cartera = Σ share × tasa)")
for lab in TARGETS.values():
    t = tab[tab.target == lab].set_index("segmento")
    logo_mix = (t.loc[["HNW", "UHNW"], "hogares"] / t.loc["Total", "hogares"] * t.loc[["HNW", "UHNW"], "churn hogares %"]).sum()
    val_mix = (t.loc[["HNW", "UHNW"], "RV total $M"] / t.loc["Total", "RV total $M"] * t.loc[["HNW", "UHNW"], "churn valor (i) %"]).sum()
    qc.check(f"{lab}: hogares Σ share×tasa", abs(logo_mix - t.loc["Total", "churn hogares %"]) < 1e-9,
             f"{t.loc['Total', 'churn hogares %']:.4f}", f"{logo_mix:.4f}")
    qc.check(f"{lab}: valor (i) Σ share_RV×tasa", abs(val_mix - t.loc["Total", "churn valor (i) %"]) < 1e-9,
             f"{t.loc['Total', 'churn valor (i) %']:.4f}", f"{val_mix:.4f}")
    qc.check(f"{lab}: eventos HNW + UHNW = total", t.loc[["HNW", "UHNW"], "eventos"].sum() == t.loc["Total", "eventos"],
             t.loc["Total", "eventos"], t.loc[["HNW", "UHNW"], "eventos"].sum())
u, h, s_ = (tab[(tab.target == k) & (tab.segmento == "Total")].iloc[0] for k in ("unión", "hard 6m", "soft 3m"))
qc.check("unión = hard + soft (eventos)", u["eventos"] == h["eventos"] + s_["eventos"], h["eventos"] + s_["eventos"], u["eventos"])
qc.check("unión = hard + soft (valor perdido)", abs(u["value_lost $M"] - h["value_lost $M"] - s_["value_lost $M"]) < 1e-6,
         f"{h['value_lost $M'] + s_['value_lost $M']:.3f}", f"{u['value_lost $M']:.3f}")

# Concentración del valor perdido (se reporta, no se corrige)
conc = []
for t, lab in TARGETS.items():
    y = df[t].to_numpy().astype(int)
    lost = np.sort(vl * y)[::-1]
    tot = lost.sum()
    ev = int(y.sum())
    conc.append({"target": lab, "eventos": ev, "value_lost $M": tot / 1e6,
                 "top 1 hogar %": 100 * lost[0] / tot, "top 10 hogares %": 100 * lost[:10].sum() / tot,
                 "top 5% de eventos %": 100 * lost[: max(1, round(0.05 * ev))].sum() / tot,
                 "mediana value_lost por evento $M": np.median(lost[:ev]) / 1e6})
conc = pd.DataFrame(conc)

# Pérdida parcial vs total en los eventos
part = []
for t, lab in TARGETS.items():
    m = df[t] == 1
    ratio = df.loc[m, "value_lost_6m"] / df.loc[m, "relationship_value"]
    part.append({"target": lab, "value_lost ÷ RV mediana": ratio.median(), "p10": ratio.quantile(0.10), "p90": ratio.quantile(0.90)})
part = pd.DataFrame(part)

# Excluidos: se mantienen en scoring con bandera
ex = raw.loc[excl]
excl_tab = pd.DataFrame([{"hogares excluidos": len(ex), "HNW": int((ex.segment == "HNW").sum()), "UHNW": int((ex.segment == "UHNW").sum()),
                          "RV $M": ex.relationship_value.sum() / 1e6, "% del RV total": 100 * ex.relationship_value.sum() / raw.relationship_value.sum()}])

save_table(tab.round(4), "01_churn_rates")
save_table(conc.round(3), "01_value_concentration")
save_table(part.round(3), "01_partial_loss")
save_table(excl_tab.round(3), "01_excluded")

# ── Figura: churn por hogares vs por valor (i), por segmento, target primario ───────────────
BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e6e5e0"
fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
for ax, lab in zip(axes, TARGETS.values()):
    t = tab[tab.target == lab].set_index("segmento").loc[["Total", "HNW", "UHNW"]]
    x = np.arange(3)
    w = 0.36
    b1 = ax.bar(x - w / 2 - 0.01, t["churn hogares %"], w, color=BLUE, label="por hogares")
    b2 = ax.bar(x + w / 2 + 0.01, t["churn valor (i) %"], w, color=ORANGE, label="por valor (RV con evento)")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.15, f"{b.get_height():.1f}", ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_xticks(x, t.index, color=INK)
    ax.set_title(lab, color=INK, fontsize=11, loc="left")
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(colors=MUTED, length=0)
axes[0].set_ylabel("churn rate (%)", color=MUTED)
axes[0].legend(frameon=False, fontsize=8, labelcolor=INK, loc="upper left")
fig.suptitle("Churn rate por hogares vs por valor, por segmento [DATA-SINT]", x=0.01, ha="left", color=INK, fontsize=12)
fig.tight_layout()
fig.savefig(FIGURES / "01_churn_rates.png", dpi=150)
print(f"\nFigura {FIGURES / '01_churn_rates.png'}")

print("\n" + tab[["target", "segmento", "eventos", "churn hogares %", "churn valor (i) %", "churn valor (ii) %", "IC95 (ii)"]].round(2).to_string(index=False))
print("\n" + conc.round(2).to_string(index=False))
qc.gate()
