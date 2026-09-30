"""Fase 13 · EWS y paquete MRM (target A).

EWS: curva alertas-por-mes vs churners capturados en test. Alertas por mes = hogares marcados en el corte ÷ horizonte
(ews.horizon_months = 6), supuesto aprobado por el usuario (un solo snapshot, L1). Modelos: EBM (champion), NAM
(challenger) en todo el test; los dos y A-lite en test ∩ holdout de A-lite. Pooled y UHNW. Umbral solo si
ews.alerts_per_month está informado; si no, se entrega la curva y se pregunta.
Regla multi-señal reconstruida: Σ de los 9 *_flag visibles (sin buró, G1-3; NaN = no disparado) ≥ k, con k elegido en
validación por F1; comparada con el modelo al mismo volumen de alertas en test (no es la regla del proveedor).
Paquete MRM: reports/MRM_package.md generado desde outputs/ (abre con las 6 limitaciones de SPEC §8 y cierra con las
3 preguntas de SPEC §9 respondidas con números del pipeline).
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

from config import HEADER, P, get, set_seed
from report import md_table, render

warnings.filterwarnings("ignore")
set_seed()
H = get("ews.horizon_months")
cap = get("ews.alerts_per_month")
raw = pd.read_excel(P.raw, sheet_name=get("paths.sheet"))
FLAGS = [c for c in raw.columns if c.endswith("_flag") and c != "multi_signal_flag"]
SC = pd.read_parquet(P.processed / "scores_p12.parquet")
X = pd.read_parquet(P.processed / "X_features.parquet")
SC = SC.merge(raw[["household_id", "relationship_value"] + FLAGS], on="household_id")
al = pd.read_csv(P.alite / "outputs" / "scored" / "scored_households.csv")[["household_id", "probabilidad_lite"]]
SC = SC.merge(al, on="household_id", how="left")
SC["n_flags"] = SC[FLAGS].fillna(0).sum(axis=1)
te, va = SC[SC.split == "test"].reset_index(drop=True), SC[SC.split == "validation"].reset_index(drop=True)
out = P.out(13)
RISK = {"EBM (champion)": "p_EBM", "NAM (challenger)": "p_NAM", "A-lite (congelado)": "probabilidad_lite"}
book = int(len(SC))


def curve(d, col, sub, seg):
    y = d.y_A.astype(int).to_numpy()
    rv = d.relationship_value.to_numpy()
    o = np.argsort(-d[col].to_numpy(), kind="stable")
    rows = []
    for frac in (0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30):
        k = int(round(frac * len(d)))
        t = o[:k]
        rows.append({"subconjunto": sub, "segmento": seg, "% hogares marcados": 100 * frac, "hogares marcados": k, "alertas por mes (muestra)": k / H,
                     "alertas por mes (equivalente cartera)": k / H * book / len(SC[SC.split == "test"]) if sub == "test completo" else np.nan,
                     "churners capturados": int(y[t].sum()), "captura %": 100 * y[t].sum() / max(y.sum(), 1), "precisión %": 100 * y[t].mean() if k else np.nan,
                     "churners por 100 alertas": 100 * y[t].mean() if k else np.nan,
                     "captura RV de churners %": 100 * (rv * y)[t].sum() / max((rv * y).sum(), 1)})
    return rows


rows = []
for name, col in RISK.items():
    subs = [("test ∩ holdout A-lite", te[te.test_alite])] + ([("test completo", te)] if not name.startswith("A-lite") else [])
    for sub, d in subs:
        for seg in ("pooled", "UHNW"):
            dd = d if seg == "pooled" else d[d.segment == "UHNW"]
            rows += [{"modelo": name, **r} for r in curve(dd.reset_index(drop=True), col, sub, seg)]
EWS = pd.DataFrame(rows)
EWS.to_csv(out / "ews_curve.csv", index=False)
thr = None
if cap is not None:
    c = EWS[(EWS.modelo == "EBM (champion)") & (EWS.subconjunto == "test completo") & (EWS.segmento == "pooled")]
    thr = c.iloc[(c["alertas por mes (equivalente cartera)"] - cap).abs().argmin()].to_dict()

# Regla multi-señal reconstruida
yv = va.y_A.astype(int).to_numpy()
f1 = {}
for k in range(1, 6):
    pred = (va.n_flags >= k).to_numpy()
    tp = (pred & (yv == 1)).sum()
    prec, rec = tp / max(pred.sum(), 1), tp / yv.sum()
    f1[k] = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
K = max(f1, key=f1.get)
rule = []
for sub, d in (("test completo", te), ("test ∩ holdout A-lite", te[te.test_alite])):
    for seg in ("pooled", "UHNW"):
        dd = (d if seg == "pooled" else d[d.segment == "UHNW"]).reset_index(drop=True)
        y = dd.y_A.astype(int).to_numpy()
        flag = (dd.n_flags >= K).to_numpy()
        n = int(flag.sum())
        r = {"subconjunto": sub, "segmento": seg, "k": K, "hogares marcados": n, "churners regla": int(y[flag].sum()), "precisión regla %": 100 * y[flag].mean() if n else np.nan}
        for name, col in RISK.items():
            if name.startswith("A-lite") and sub == "test completo":
                continue
            top = np.argsort(-dd[col].to_numpy(), kind="stable")[:n]
            r[f"churners {name} (mismo volumen)"] = int(y[top].sum())
            r[f"precisión {name} %"] = 100 * y[top].mean() if n else np.nan
        rule.append(r)
RULE = pd.DataFrame(rule)
RULE.to_csv(out / "multisignal_vs_model.csv", index=False)
F1 = pd.DataFrame({"k": list(f1), "F1 validación": list(f1.values())})
F1.to_csv(out / "multisignal_k_selection.csv", index=False)

# Figura
fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
cols = {"EBM (champion)": "#2a78d6", "NAM (challenger)": "#eb6834", "A-lite (congelado)": "#1baf7a"}
for ax, seg in zip(axes, ("pooled", "UHNW")):
    for name in RISK:
        c = EWS[(EWS.modelo == name) & (EWS.subconjunto == "test ∩ holdout A-lite") & (EWS.segmento == seg)]
        ax.plot(c["alertas por mes (muestra)"], c["captura %"], marker="o", ms=4, lw=2, color=cols[name], label=name, markeredgecolor="white", markeredgewidth=1)
    ax.set_title(f"{seg} · test ∩ holdout A-lite · captura de hard churners vs alertas/mes", fontsize=9, loc="left")
    ax.set_xlabel(f"alertas por mes (hogares marcados ÷ {H})", fontsize=8)
    ax.set_ylabel("churners capturados (%)", fontsize=8)
    ax.grid(color="#e6e5df", lw=0.6)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(labelsize=7.5)
axes[0].legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(out / "ews_curve.png", dpi=110)
plt.close(fig)
SUM = {"horizonte (meses)": H, "ews.alerts_per_month": cap, "umbral": thr if thr else "no definido: ews.alerts_per_month en null (se pregunta al usuario)",
       "regla multi-señal": f"Σ de {len(FLAGS)} flags visibles ≥ {K} (k por F1 en validación)", "flags": FLAGS}
json.dump(SUM, open(out / "summary.json", "w"), ensure_ascii=False, indent=1)
json.dump({"title": "Fase 13 · EWS (target A)", "order": ["summary.json", "ews_curve.png", "ews_curve.csv", "multisignal_vs_model.csv", "multisignal_k_selection.csv"],
           "notes": {"ews_curve.csv": "Alertas por mes = marcados ÷ 6 (supuesto: un solo snapshot). Equivalente cartera = escala del test a los 19,473 hogares."}},
          open(out / "_meta.json", "w"), ensure_ascii=False)
render(13)

# ── Paquete MRM (todo leído de outputs/) ──────────────────────────────────────────────────────────────────────
spec = (P.reports.parent / "docs" / "SPEC.md").read_text(encoding="utf-8")
lims = spec[spec.index("## 8."):spec.index("## 9.")].split("\n", 1)[1].strip()
dec = json.load(open(P.out(10) / "decision.json"))
allm = pd.read_csv(P.out(10) / "test_metrics_all.csv")
fa = allm[(allm.target == "A") & (allm.segmento == "pooled") & (allm.subconjunto == "test ∩ holdout A-lite")][["modelo", "hogares", "eventos", "PR-AUC", "lift@5%", "AUC"]].sort_values("PR-AUC", ascending=False)
cal = pd.read_csv(P.out(11) / "calibration.csv")[["modelo", "elegido", "ECE test sin calibrar (pp)", "ECE test calibrado (pp)"]]
sc = pd.read_csv(P.out(12) / "scorecard_summary.csv")[["modelo", "filas lookup compacto", "% recortados", "residual completeness: media |r|", "corr(score exacto, lookup)"]]
e5 = EWS[(EWS.subconjunto == "test ∩ holdout A-lite") & (EWS.segmento == "pooled") & (EWS["% hogares marcados"] == 5.0)][["modelo", "hogares marcados", "alertas por mes (muestra)", "churners capturados", "captura %", "churners por 100 alertas", "captura RV de churners %"]]
ef = EWS[(EWS.subconjunto == "test completo") & (EWS.segmento == "pooled") & (EWS["% hogares marcados"] == 5.0)][["modelo", "alertas por mes (equivalente cartera)", "churners por 100 alertas", "captura %"]]
rp = RULE[(RULE.subconjunto == "test completo") & (RULE.segmento == "pooled")].iloc[0]
q1 = (f"No. En el gate pre-registrado (NAM vs A-lite, target A, {dec['hogares']:,} hogares, {dec['eventos A']} eventos), el NAM mejora la PR-AUC en "
      f"{dec['ΔPR-AUC']:+.3f} (IC95 {dec['ΔPR-AUC IC95'][0]:+.3f} a {dec['ΔPR-AUC IC95'][1]:+.3f}) y el lift@5% en {dec['Δlift@5%']:+.2f} "
      f"(IC95 {dec['Δlift@5% IC95'][0]:+.2f} a {dec['Δlift@5% IC95'][1]:+.2f}); el segundo IC incluye 0 ⟹ {dec['decisión']}. Frente al champion EBM el NAM empata "
      f"(ver gate_bootstrap.csv) y su scorecard requiere binning (residual medio {sc.set_index('modelo').loc['NAM', 'residual completeness: media |r|']:.1f} puntos vs "
      f"{sc.set_index('modelo').loc['EBM', 'residual completeness: media |r|']:.1f} del EBM).")
e = e5.set_index("modelo")
q2 = ("Con el 5% de hogares marcados (subconjunto justo, " + ", ".join(f"{m}: {e.loc[m, 'churners por 100 alertas']:.1f} churners por 100 alertas, captura {e.loc[m, 'captura %']:.1f}% de los churners y {e.loc[m, 'captura RV de churners %']:.1f}% de su RV" for m in e.index)
      + f"). En todo el test, el EBM al 5% equivale a {ef.set_index('modelo').loc['EBM (champion)', 'alertas por mes (equivalente cartera)']:.0f} alertas/mes en la cartera con "
      f"{ef.set_index('modelo').loc['EBM (champion)', 'churners por 100 alertas']:.1f} churners por 100 alertas.")
q3 = (f"Sí. La regla Σ flags visibles ≥ {int(rp.k)} marca {int(rp['hogares marcados']):,} hogares del test con {int(rp['churners regla'])} churners (precisión "
      f"{rp['precisión regla %']:.1f}%); al mismo volumen el EBM captura {int(rp['churners EBM (champion) (mismo volumen)'])} (precisión {rp['precisión EBM (champion) %']:.1f}%) "
      f"y el NAM {int(rp['churners NAM (challenger) (mismo volumen)'])} (precisión {rp['precisión NAM (challenger) %']:.1f}%). Margen pequeño y sin IC: "
      f"la regla simple de flags visibles captura casi lo mismo que el modelo a ese volumen.")
if rp["churners EBM (champion) (mismo volumen)"] <= rp["churners regla"]:
    q3 = q3.replace("Sí.", "No.")
doc = f"""{HEADER}

# Paquete MRM · Client Pulse · Modelo 3 (NAM monótono)

## Limitaciones (SPEC §8)
{lims}

## Decisión del gate (fase 10, única apertura del test)
{md_table(pd.DataFrame([{"clave": k, "valor": json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v} for k, v in dec.items()]))}

## Todos los métodos en el mismo subconjunto (target A, test ∩ holdout A-lite)
{md_table(fa)}

## Calibración (fase 11)
{md_table(cal)}

## Scorecard (fase 12)
{md_table(sc)}

## EWS (fase 13, alertas por mes = marcados ÷ {H})
{md_table(e5)}

- Umbral: {"definido con ews.alerts_per_month" if thr else "no definido (ews.alerts_per_month en null): se entrega la curva completa en outputs/p13/ews_curve.csv"}.

## Preguntas centrales (SPEC §9)
1. **¿El NAM monótono supera al champion interpretable lo suficiente para justificar su complejidad?** {q1}
2. **¿Cuántos churners (y cuánto RV) captura el EWS por cada 100 alertas?** {q2}
3. **¿El modelo supera a la regla multi-señal reconstruida con los flags visibles?** {q3}

_Todas las cifras provienen de outputs/p10–p13 (generado por src/p13_ews_mrm.py)._
"""
(P.reports / "MRM_package.md").write_text(doc, encoding="utf-8")
print(json.dumps(SUM, ensure_ascii=False)); print(e5.round(2).to_string(index=False)); print(RULE.round(2).to_string(index=False)); print(F1.round(3).to_string(index=False)); print(q1); print(q2); print(q3)
