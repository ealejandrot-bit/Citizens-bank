"""Paso 9 · Binning, WoE e IV del campeón (dev, target B).

- Principal (D9.1): continuas → optbinning `auto_asc_desc`, min_bin_size 5%, ≥ 30 eventos por bin, missing como bins
  propios (no aplica / sin dato); binarias → bins de negocio {0, 1} si ambos tienen ≥ 30 eventos (el 5% del SPEC
  fusionaría flags raros con riesgo alto; se somete a G2).
- Comparación: cuantiles (≤ 10 bins, ≥ 30 eventos) y business-defined (umbrales de alerta del Excel de 37 variables).
- WoE = ln(%buenos / %malos); IV = Σ (%buenos − %malos)·WoE; clases 0.02 / 0.10 / 0.30 / 0.50.
- Estabilidad: WoE por bin en los 25 conjuntos de entrenamiento de la CV 5×5 (bins fijos): sd y % de folds con el mismo signo.
- Monotonía en bins con dato (QC).
"""
from __future__ import annotations

import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import COMPOSITES, FIGS, MODEL, PROC, REPORTS, candidates, load_split, md_table, save_table, set_seed
from woe import fit_main, fit_quantile, is_binary, make_binning, woe_iv

set_seed()
dev = load_split("dev").merge(pd.read_parquet(PROC / "step07_clusters.parquet"), on="household_id")
D = dev[dev.in_pop_B].reset_index(drop=True)
y = D.y_B.astype(int).to_numpy()
C = [c for c in candidates() if c not in COMPOSITES] + ["cluster"]
BUS = {"aum_outflow_pct_90d": 0.10, "deposit_balance_change_pct_90d": -0.25, "aum_vs_baseline_pct": -0.20, "deposit_balance_vs_6m_avg_pct": -0.30,
       "recurring_deposit_change_pct": -0.40, "net_deposit_flow_pct_90d": -0.15, "external_transfer_pct_of_balance_60d": 0.15,
       "transfer_to_competitor_pct_90d": 0.10, "net_external_flow_pct_90d": -0.15, "outflow_vs_baseline_pct": 1.0, "investment_redemption_pct": 0.20,
       "fixed_income_maturity_not_reinvested": 0.50, "cash_pct_of_portfolio_chg": 0.10, "return_vs_benchmark": -0.03, "positions_liquidated_pct": 0.15,
       "share_of_wallet": 0.30, "share_of_wallet_change": -0.10, "contact_gap_ratio": 2.0, "client_reply_rate": 0.5, "complaint_age_days": 30,
       "meetings_cancelled_by_client": 1.5}
COUNTS = ["new_external_destinations_90d", "products_closed_180d", "accounts_closed_90d", "streams_stopped_count"]
FOLDS = [(r, k) for r in range(1, 6) for k in range(5)]


def _zinfl(x, r):
    xv = pd.Series(x).astype(float)
    ok = xv.notna() if r is None else (pd.Series(r).reset_index(drop=True) == "ok") & xv.notna()
    v, n = np.unique(xv[ok], return_counts=True)
    return len(v) > 2 and n.max() / n.sum() >= 0.70 and v[n.argmax()] == v.min()


def iv_of(vb, c):
    r = D[f"{c}__miss"] if f"{c}__miss" in D else None
    return vb.table(D[c], r, y).IV.sum()


def iv_class(v):
    return "fuera" if v < 0.02 else "débil" if v < 0.10 else "medio" if v < 0.30 else "fuerte" if v < 0.50 else "SOSPECHOSO"


B, tabs, summ = {}, [], []
for c in C:
    vb = fit_main(c, D, y)
    r = D[f"{c}__miss"] if f"{c}__miss" in D else None
    t = vb.table(D[c], r, y)
    lab = vb.bin_labels(D[c], r)
    W = []
    for rr, k in FOLDS:
        tr = D[f"cv_r{rr}"].to_numpy() != k
        tt = pd.DataFrame({"b": lab[tr], "y": y[tr]}).groupby("b").y.agg(["size", "sum"]).reindex(vb.labels).fillna(0)
        W.append(pd.Series(woe_iv(tt["size"] - tt["sum"], tt["sum"])[0], index=vb.labels))
    W = pd.concat(W, axis=1)
    t["sd WoE folds"] = [0.0 if b in vb.neutral else W.loc[b].std() for b in t.bin]
    t["% folds mismo signo"] = [100.0 if b in vb.neutral else 100 * (np.sign(W.loc[b]) == np.sign(w)).mean() for b, w in zip(t.bin, t.WoE)]
    t.insert(0, "variable", c)
    tabs.append(t)
    B[c] = vb
    reg = t[~t.especial]
    rates = reg["tasa %"].to_numpy()
    mono = "n/a" if c == "cluster" or len(rates) < 2 else ("ascendente" if np.all(np.diff(rates) >= -1e-9) else "descendente" if np.all(np.diff(rates) <= 1e-9) else "NO MONÓTONA")
    ivm = t.IV.sum()
    iv_q = iv_of(fit_quantile(c, D, y), c) if c != "cluster" and not is_binary(D[c]) else np.nan
    if c in BUS:
        iv_b = iv_of(make_binning(c, [BUS[c]], D[c], r, y), c)
    elif c in COUNTS:
        iv_b = iv_of(make_binning(c, [0.5, 1.5], D[c], r, y), c)
    elif is_binary(D[c]):
        iv_b = iv_of(make_binning(c, [0.5], D[c], r, y), c)
    else:
        iv_b = np.nan
    summ.append({"variable": c, "IV": ivm, "clase": iv_class(ivm), "bins con dato": len(reg), "bins especiales": int(t.especial.sum()),
                 "tendencia": mono, "tasa mín–máx %": f"{rates.min():.1f}–{rates.max():.1f}" if len(rates) else "",
                 "IV cuantiles": iv_q, "IV business": iv_b, "sd WoE máx": reg["sd WoE folds"].max() if len(reg) else np.nan,
                 "binaria con bins de negocio (D9.1)": is_binary(D[c]) and c != "cluster",
                 "regla de bins": "categórica" if c == "cluster" else "negocio {0,1} (D9.1)" if is_binary(D[c]) else ("negocio inflada en mínimo (D9.1b)" if vb.dtype == "numerical" and len(vb.splits) <= 2 and not hasattr(vb, "_ob") and _zinfl(D[c], r) else "optbinning 5%")})
woe_t = pd.concat(tabs, ignore_index=True)
iv_t = pd.DataFrame(summ).sort_values("IV", ascending=False).reset_index(drop=True)
save_table(woe_t, "step09_woe_iv")
save_table(iv_t, "step09_iv_summary")
with open(MODEL / "step09_binning.pkl", "wb") as fh:
    pickle.dump(B, fh)

# Flags que el 5% fusionaría (evidencia de D9.1)
fl = []
for c in C:
    if c != "cluster" and is_binary(D[c]):
        x = D[c]
        p1 = (x == 1).mean()
        fl.append({"variable": c, "% hogares con 1": 100 * p1, "eventos con 1": int(y[(x == 1).to_numpy()].sum()),
                   "tasa con 1 %": 100 * y[(x == 1).to_numpy()].mean() if p1 > 0 else np.nan,
                   "bajo 5% (el SPEC lo fusionaría)": p1 < 0.05, "IV con bins de negocio": iv_t.set_index("variable").loc[c, "IV"]})
flags = pd.DataFrame(fl).sort_values("IV con bins de negocio", ascending=False)
save_table(flags, "step09_flags_min5")

# Figura: tasa por bin de las 20 de mayor IV
top = iv_t.head(20).variable.tolist()
fig, axes = plt.subplots(4, 5, figsize=(18, 12), sharey=True)
for ax, v in zip(axes.flat, top):
    t = woe_t[woe_t.variable == v].reset_index(drop=True)
    ax.bar(range(len(t)), t["tasa %"], color=["#a3a29c" if e else "#2a78d6" for e in t.especial], width=0.8)
    ax.axhline(100 * y.mean(), color="#52514e", lw=1, ls="--")
    ax.set_xticks(range(len(t)), [str(b)[:14] for b in t.bin], rotation=60, ha="right", fontsize=6, color="#52514e")
    ax.set_title(f"{v}\nIV = {iv_t.set_index('variable').loc[v, 'IV']:.3f}", fontsize=8, loc="left")
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(length=0, labelsize=7)
fig.suptitle("Tasa de evento B por bin · 20 variables de mayor IV · dev [DATA] (gris = no aplica / sin dato; línea = tasa base)", x=0.01, ha="left", fontsize=11)
fig.tight_layout(rect=(0, 0, 1, 0.97))
FIGS.mkdir(parents=True, exist_ok=True)
fig.savefig(FIGS / "step09_bins_top20.png", dpi=110)

top3 = iv_t.head(3).variable.tolist()
rep = f"""# Paso 9 · Binning, WoE, IV (campeón)

## Objetivo
- Transformar cada candidata en bins monótonos y estables con missing como bin propio, y medir su IV.

## Método
- Principal (D9.1): continuas → `optbinning` `auto_asc_desc`, `min_bin_size` = 0.05 [DEF], ≥ 30 eventos por bin [DEF];
  binarias → bins de negocio {{0, 1}}; infladas en su mínimo (≥ 70%) → "= mínimo" / "> mínimo" (+ "≥ 2" en conteos)
  (D9.1b); siempre ≥ 30 eventos por bin (desvíos sometidos a G2); missing: "no aplica" y "sin dato".
- Comparación: cuantiles (≤ 10 bins) y business-defined (umbral de alerta del Excel; conteos 0 / 1 / 2+).
- WoE = ln(%buenos / %malos); IV = Σ (%buenos − %malos)·WoE; clases 0.02 / 0.10 / 0.30 / 0.50 [DEF].
- Estabilidad: WoE por bin en los 25 entrenamientos de la CV 5×5 (bins fijos).

## Código
- `src/step09_binning.py`, `src/woe.py` · `tests/test_step09.py` · `step09_woe_iv.csv` (completa), `step09_iv_summary.csv`,
  `outputs/model/step09_binning.pkl`.

## Resultados

### Resumen de IV (todas las candidatas) [DATA]
{md_table(iv_t[['variable', 'IV', 'clase', 'regla de bins', 'bins con dato', 'bins especiales', 'tendencia', 'tasa mín–máx %', 'IV cuantiles', 'IV business', 'sd WoE máx']], floatfmt=",.3f")}

- {int((iv_t.IV >= 0.02).sum())} de {len(iv_t)} con IV ≥ 0.02; sospechosas (> 0.50): {int((iv_t.IV > 0.5).sum())} [DATA].
- Monotonía: {int((iv_t.tendencia == 'NO MONÓTONA').sum())} variables no monótonas [DATA].

### Tabla WoE / IV completa de las 3 variables de mayor IV [DATA]
{md_table(woe_t[woe_t.variable.isin(top3)][['variable', 'bin', 'hogares', 'eventos', '% hogares', 'tasa %', 'WoE', 'IV', 'sd WoE folds', '% folds mismo signo']], floatfmt=",.3f")}

- Verificación: por variable, % hogares suma 100 y eventos suman {int(y.sum()):,} [DATA].

### Flags que la regla de 5% fusionaría (evidencia de D9.1) [DATA]
{md_table(flags, floatfmt=",.3f")}

![Tasa por bin](../outputs/figs/step09_bins_top20.png)

## Tests
- `tests/test_step09.py` (ver pytest).

## Decisiones y preguntas abiertas
- D9.1 (bins de negocio en binarias) y D9.1b (infladas en su mínimo) → pregunta en G2. D9.2 (razón de missing de
  `competitor_x_new_destinations`), D9.3 (especiales con < 30 eventos neutrales), D9.5 (pre-bin) en `reports/decision_log.md`.
"""
(REPORTS / "step09.md").write_text(rep, encoding="utf-8")
print(iv_t.head(30).round(3).to_string(index=False)); print(flags.round(3).to_string(index=False))
