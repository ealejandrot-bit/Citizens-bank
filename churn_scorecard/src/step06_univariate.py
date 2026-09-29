"""Paso 6 · Análisis univariado vs y_B en dev (y_A como sensibilidad).

Por candidata: mediana y p25/p75 por grupo, % missing por grupo, effect size (Cliff's δ; risk ratio con IC 95% en
binarias e infladas en su mínimo, donde |δ| ≤ prevalencia subestima), AUC univariada (missing → mediana solo para esta
métrica), IV preliminar (10 cuantiles + bins de missing por razón), tasa por decil / categoría, dirección observada vs
esperada. Marca candidatas (IV ≥ 0.02 o RR significativo) y sospechosas de fuga (AUC > 0.85 o IV > 0.50).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu
from sklearn.metrics import roc_auc_score

from common import COMPOSITES, REPORTS, TABLES, candidates, load_split, md_table, save_table, set_seed

set_seed()
dev = load_split("dev")
dic = pd.read_csv(TABLES / "step05_features.csv").set_index("variable")
CANDS = candidates(include_composites=True)
res = {}
for tgt in ("B", "A"):
    m = dev[f"in_pop_{tgt}"]
    D = dev[m].reset_index(drop=True)
    y = D[f"y_{tgt}"].astype(int).to_numpy()
    base = y.mean()
    rows, dec = [], []
    for c in CANDS:
        x = D[c].astype(float)
        xv = x.dropna().to_numpy()
        yv = y[x.notna().to_numpy()]
        a1, a0 = xv[yv == 1], xv[yv == 0]
        delta = np.nan
        if len(a1) > 5 and len(a0) > 5 and np.std(xv) > 0:
            u, _ = mannwhitneyu(a1, a0)
            delta = 2 * u / (len(a1) * len(a0)) - 1
        auc = roc_auc_score(y, x.fillna(x.median())) if x.nunique() > 1 else np.nan
        auc = max(auc, 1 - auc) if auc == auc else np.nan
        vals, cnt = np.unique(xv, return_counts=True)
        binary = set(vals) <= {0.0, 1.0} and len(vals) == 2
        zinfl = not binary and len(vals) > 2 and cnt.max() / len(xv) >= 0.70 and vals[cnt.argmax()] == xv.min()
        rr = lo = hi = np.nan
        if binary or zinfl:
            hi_m = x.notna().to_numpy() & ((x > vals.min()).to_numpy() if zinfl else (x == 1).to_numpy())
            lo_m = x.notna().to_numpy() & ~hi_m
            e1, n1, e0, n0 = y[hi_m].sum(), hi_m.sum(), y[lo_m].sum(), lo_m.sum()
            if e1 > 0 and e0 > 0:
                rr = (e1 / n1) / (e0 / n0)
                se = np.sqrt(1 / e1 - 1 / n1 + 1 / e0 - 1 / n0)
                lo, hi = rr * np.exp(-1.96 * se), rr * np.exp(1.96 * se)
        # IV preliminar y tasa por decil/categoría
        reason = D[f"{c}__miss"] if f"{c}__miss" in D else pd.Series(np.where(x.isna(), "sin_dato", "ok"))
        if x.nunique() <= 10:
            g = x.round(6).astype("string")
        else:
            g = pd.qcut(x.rank(method="first"), 10, labels=False).astype("string")
        g = g.where(reason == "ok", "NaN:" + reason)
        t = pd.DataFrame({"g": g, "y": y}).groupby("g").y.agg(["sum", "size"])
        b_, g_ = t["sum"] + 0.5, t["size"] - t["sum"] + 0.5
        iv = float(((g_ / g_.sum() - b_ / b_.sum()) * np.log((g_ / g_.sum()) / (b_ / b_.sum()))).sum())
        t = t.reset_index().rename(columns={"sum": "eventos", "size": "hogares"})
        t["tasa %"] = 100 * t.eventos / t.hogares
        t.insert(0, "variable", c)
        dec.append(t)
        exp = dic.loc[c, "signo esperado"] if c in dic.index else "+"
        obs = "+" if delta > 0 else "−" if delta < 0 else "?"
        rr_sig = rr == rr and (lo > 1 or hi < 1)
        agree = ("coincide" if str(exp)[:1] == obs else "DISCREPANCIA") if str(exp)[:1] in "+−" and (abs(delta) >= 0.147 or rr_sig) else "sin evidencia / sin hipótesis"
        q = lambda arr, p: np.percentile(arr, p) if len(arr) else np.nan
        rows.append({"variable": c, "compuesto": c in COMPOSITES, "mediana evento": q(a1, 50), "p25–p75 evento": f"{q(a1, 25):.4g} – {q(a1, 75):.4g}",
                     "mediana no evento": q(a0, 50), "p25–p75 no evento": f"{q(a0, 25):.4g} – {q(a0, 75):.4g}",
                     "% missing evento": 100 * x[y == 1].isna().mean(), "% missing no evento": 100 * x[y == 0].isna().mean(),
                     "δ Cliff": delta, "RR": rr, "IC95 RR": f"[{lo:.2f}, {hi:.2f}]" if rr == rr else "", "AUC univariada": auc, "IV preliminar": iv,
                     "signo esperado": exp, "signo observado": obs, "evaluación": agree,
                     "candidata (IV ≥ 0.02 o RR sig.)": iv >= 0.02 or rr_sig, "sospecha de fuga (AUC > 0.85 o IV > 0.50)": auc > 0.85 or iv > 0.50})
    U = pd.DataFrame(rows).sort_values("IV preliminar", ascending=False)
    save_table(U, f"step06_univariate_{tgt}")
    save_table(pd.concat(dec, ignore_index=True), f"step06_rate_by_bin_{tgt}")
    res[tgt] = U

UB, UA = res["B"], res["A"]
disc = UB[UB["evaluación"] == "DISCREPANCIA"]
cmp_ = UB[["variable", "IV preliminar", "AUC univariada"]].merge(UA[["variable", "IV preliminar", "AUC univariada"]], on="variable", suffixes=(" B", " A"))
save_table(cmp_, "step06_A_vs_B")
rep = f"""# Paso 6 · Análisis univariado

## Objetivo
- Medir en dev cuánto separa cada candidata a eventos de no eventos (target B; A como sensibilidad), en qué dirección y
  si hay sospecha de fuga.

## Método
- {len(CANDS)} candidatas [DATA] = proveedor (sin `age_primary` ni buró, G1-3) + derivadas + compuestos (solo challenger).
- δ de Cliff (continuas); RR con IC 95% (binarias e infladas en su mínimo); AUC univariada (missing → mediana solo para
  la métrica); IV preliminar con 10 cuantiles y bins de missing por razón (no aplica / sin dato).
- Candidata: IV ≥ 0.02 o RR significativo. Sospecha de fuga: AUC > 0.85 o IV > 0.50.

## Código
- `src/step06_univariate.py` · `tests/test_step06.py` · tablas `step06_univariate_B.csv`, `step06_univariate_A.csv`,
  `step06_rate_by_bin_*.csv`.

## Resultados

### Top 20 por IV preliminar, target B [DATA]
{md_table(UB.head(20)[['variable', 'compuesto', 'δ Cliff', 'RR', 'IC95 RR', 'AUC univariada', 'IV preliminar', 'signo esperado', 'signo observado', 'evaluación']], floatfmt=",.3f")}

- Candidatas: {int(UB['candidata (IV ≥ 0.02 o RR sig.)'].sum())} de {len(UB)} [DATA]. Sospecha de fuga: {int(UB['sospecha de fuga (AUC > 0.85 o IV > 0.50)'].sum())} ({', '.join(UB.loc[UB['sospecha de fuga (AUC > 0.85 o IV > 0.50)'], 'variable']) or 'ninguna'}) [DATA].
- Discrepancias de signo (efecto relevante y signo contrario al esperado): {len(disc)} ({', '.join(disc.variable) or 'ninguna'}) [DATA].
- AUC univariada máxima B: {UB['AUC univariada'].max():.3f} (`{UB.sort_values('AUC univariada', ascending=False).variable.iloc[0]}`) [DATA].

### A vs B (IV y AUC; top 15 por IV B) [DATA]
{md_table(cmp_.head(15), floatfmt=",.3f")}

- Correlación de rangos del IV entre targets: {cmp_['IV preliminar B'].corr(cmp_['IV preliminar A'], method='spearman'):.3f} [DATA]: las mismas señales
  ordenan ambos targets.

## Tests
- `tests/test_step06.py` (ver pytest).

## Decisiones y preguntas abiertas
- D6.1 en `reports/decision_log.md`.
"""
(REPORTS / "step06.md").write_text(rep, encoding="utf-8")
print(UB.head(25)[["variable", "δ Cliff", "RR", "AUC univariada", "IV preliminar", "signo esperado", "signo observado", "evaluación"]].round(3).to_string(index=False))
print("disc:", disc.variable.tolist()); print("fuga:", UB.loc[UB['sospecha de fuga (AUC > 0.85 o IV > 0.50)'], 'variable'].tolist())
