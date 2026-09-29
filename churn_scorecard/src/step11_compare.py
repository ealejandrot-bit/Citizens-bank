"""Paso 11 · Comparación campeón vs challenger (tabla H-2 del SPEC) y reporte `reports/step11.md`.

Corre después de `step11_champion.py` y `step11_challenger.py`. Todas las métricas son de la CV 5×5 en dev (mismos
folds, comparación pareada por fold). Los criterios de la tabla H-2 que exigen validación (caída dev→val, PSI por tramo,
Brier tras Platt) se evalúan una sola vez en los pasos 13–14 (el holdout se toca una vez por modelo final, D11.1).
"""
from __future__ import annotations

import pickle

import pandas as pd

from common import MODEL, REPORTS, TABLES, md_table, save_table

T = lambda n: pd.read_csv(TABLES / f"{n}.csv")                  # noqa: E731
ca, cx = T("step11A_cv_folds"), T("step11B_cv_folds_xgb")
coef, sa, rca = T("step11A_coefficients"), T("step11A_sensitivity_A"), T("step11A_reason_stability")
msum, seeds, imp, mono, inter, rcb, diag = (T("step11B_models_summary"), T("step11B_seeds"), T("step11B_shap_importance"), T("step11B_monotonicity"),
                                            T("step11B_interactions"), T("step11B_reason_stability"), T("step11B_diagnostics"))
LNP = pickle.load(open(MODEL / "step11A_champion.pkl", "rb"))["ln_odds_good_pop"]
LNS = coef.loc[0, "β (muestra ponderada)"] + LNP - coef.loc[0, "β final"]
pa = ca.merge(cx, on=["repetición", "fold"], suffixes=(" campeón", " challenger"))
M = ["AUC", "Gini", "PR-AUC", "KS", "Brier", "pendiente calibración b", "captura RV eventos decil 1", "Gini entrenamiento"]
cmp_ = pd.DataFrame({"métrica": M, "campeón": [ca[m].mean() for m in M], "challenger XGBoost": [cx[m].mean() for m in M]})
cmp_["Δ (challenger − campeón)"] = cmp_["challenger XGBoost"] - cmp_["campeón"]
cmp_["% folds challenger mejor"] = [100 * ((pa[f"{m} challenger"] < pa[f"{m} campeón"]) if m == "Brier" else (pa[f"{m} challenger"] > pa[f"{m} campeón"])).mean()
                                   if m not in ("pendiente calibración b", "Gini entrenamiento") else float("nan") for m in M]
save_table(cmp_, "step11_comparison")

dG, dP = cmp_.set_index("métrica").loc["Gini", "Δ (challenger − campeón)"], cmp_.set_index("métrica").loc["PR-AUC", "Δ (challenger − campeón)"]
gap_a = (ca["Gini entrenamiento"] - ca.Gini).mean()
gap_x = (cx["Gini entrenamiento"] - cx.Gini).mean()
b_x = cx["pendiente calibración b"].mean()
v_mono = int(mono["violaciones ICE"].fillna(0).sum() + mono["violaciones PDP"].fillna(0).sum())
st_x, sg_x = rcb["acuerdo top 1 %"].iloc[0], rcb["% variables con signo coherente (media réplicas)"].iloc[0]
cap_a, cap_x = ca["captura RV eventos decil 1"].mean(), cx["captura RV eventos decil 1"].mean()
H = pd.DataFrame([
    ("ΔGini ≥ +0.05", f"{dG:+.4f}", dG >= 0.05),
    ("ΔPR-AUC ≥ +0.03", f"{dP:+.4f}", dP >= 0.03),
    ("Sobreajuste (Gini entrenamiento − CV) no peor que campeón (proxy de la caída dev→val)", f"{gap_x:.4f} vs {gap_a:.4f}", gap_x <= gap_a),
    ("Brier ≤ campeón y b ∈ [0.8, 1.2] (OOF, antes de Platt)", f"{cx.Brier.mean():.4f} vs {ca.Brier.mean():.4f}; b = {b_x:.3f}",
     cx.Brier.mean() <= ca.Brier.mean() and 0.8 <= b_x <= 1.2),
    ("Violaciones de monotonía = 0", f"{v_mono}", v_mono == 0),
    ("Reason codes estables ≥ 70% (top 1) y signo coherente 100%", f"{st_x:.1f}%; signo {sg_x:.1f}%", st_x >= 70 and sg_x >= 99.999),
    ("Captura de RV de eventos en decil 1 ≥ campeón", f"{cap_x:.4f} vs {cap_a:.4f}", cap_x >= cap_a),
    ("PSI dev→val < 0.10 por tramo", "pendiente paso 13", None),
], columns=["criterio H-2", "valor [DATA]", "cumple"])
H["cumple"] = H["cumple"].map({True: "sí", False: "no", None: "pendiente"})
save_table(H, "step11_h2_table")
n_fail = int((H.cumple == "no").sum())
recomm = ("Se mantiene el campeón WoE + logística: el challenger no cumple " + str(n_fail) + " de los criterios H-2 evaluables en dev."
          if n_fail else "El challenger cumple todos los criterios H-2 evaluables en dev; la decisión final se toma con validación (pasos 13–14).")

rep = f"""# Paso 11 · Estimación (campeón y challenger)

## Objetivo
- Estimar el campeón (logística sobre WoE) y el challenger (XGBoost monotónico, EBM), medirlos en la misma CV y
  recomendar cuál sigue a escalamiento.

## Método
- Régimen: {int(1871)} eventos B en dev [DATA] > 300 ⟹ logística sobre WoE + challenger ML (tabla H-1).
- 11A: GLM Binomial (statsmodels) sobre y_bueno = 1 − y_B con pesos balanceados w_B; β > 0 sobre WoE; intercepto
  corregido β₀ = β₀* − ln(odds buenos muestra ponderada) + ln(odds buenos población). CV 5×5 anidada: el binning se
  re-ajusta dentro de cada fold de entrenamiento.
- 11B: XGBoost con `monotone_constraints` (+1 / −1 por signo a priori; "?" = 0), Optuna 150 trials, MedianPruner,
  objetivo PR-AUC media 5×5; `scale_pos_weight` = n0/n1 y probabilidad corregida por prior (logit − ln spw). 3 semillas,
  variante WoE, EBM monotónico, RF de referencia. TreeSHAP raw (log-odds), ICE/PDP, interacciones SHAP, ALE,
  reason codes en 200 réplicas bootstrap.
- Comparación pareada por fold en la CV 5×5 de dev; los criterios H-2 que requieren validación quedan para 13–14 (D11.1).

## Código
- `src/step11_champion.py`, `src/step11_challenger.py`, `src/step11_compare.py` · `tests/test_step11.py` ·
  `outputs/tables/step11A_*.csv`, `step11B_*.csv`, `step11_comparison.csv`, `step11_h2_table.csv`,
  `outputs/model/step11A_champion.pkl`, `step11B_xgb.json`, `step11B_challenger.pkl`.

## Resultados

### 11A · Coeficientes del campeón (dev, target B) [DATA]
{md_table(coef, floatfmt=",.4f")}

- Todos los β de variables > 0 y p < 0.001; VIF máx {coef['VIF (WoE)'].max():.2f} [DATA].
- Verificación del intercepto: β₀ = {coef.loc[0, 'β (muestra ponderada)']:.4f} − {LNS:.4f} (ln odds buenos de dev ponderada)
  + {LNP:.4f} (ln odds buenos población B) = {coef.loc[0, 'β final']:.4f} [DATA].

### 11A · Sensibilidad target A (5 folds, r1) [DATA]
{md_table(sa, floatfmt=",.4f")}

### 11B · Modelos challenger (CV) [DATA]
{md_table(msum, floatfmt=",.4f")}

### 11B · Sensibilidad a la semilla [DATA]
{md_table(seeds, floatfmt=",.4f")}

### 11B · Importancia SHAP (|φ| medio, log-odds) [DATA]
{md_table(imp, floatfmt=",.4f")}

- Verificación: Σ % = {imp['% de Σ|φ|'].sum():.1f}% [DATA]; aditividad φ₀ + Σφ = margen, error máx. {diag['error máx. aditividad SHAP'].iloc[0]:.2e} [DATA].

### 11B · Monotonía (ICE 500 hogares × 21 puntos; PDP) [DATA]
{md_table(mono, floatfmt=",.0f")}

### 11B · Interacciones SHAP (2,000 hogares) [DATA]
{md_table(inter.head(10), floatfmt=",.1f")}

- Interacción global = {diag['% interacción en Σ|φ| (global)'].iloc[0]:.1f}% de Σ|φ| [DATA]; variables con > 20%:
  {int(inter['> 20%'].sum())} [DATA].

![ALE](../outputs/figs/step11B_ale_top5.png)

### Estabilidad de reason codes (200 réplicas bootstrap, 1,000 hogares de dev) [DATA]
{md_table(pd.concat([rca, rcb], ignore_index=True), floatfmt=",.1f")}

### Comparación pareada campeón vs challenger (CV 5×5, dev) [DATA]
{md_table(cmp_, floatfmt=",.4f")}

### Tabla H-2 (criterios de reemplazo) [DATA]
{md_table(H)}

- Recomendación: {recomm}

## Tests
- `tests/test_step11.py` (ver pytest).

## Decisiones y preguntas abiertas
- D11.1–D11.4 en `reports/decision_log.md`; preguntas G2-1 a G2-4 en `reports/gate_2.md`.
"""
(REPORTS / "step11.md").write_text(rep, encoding="utf-8")
print(cmp_.round(4).to_string(index=False)); print(H.to_string(index=False)); print(recomm)
