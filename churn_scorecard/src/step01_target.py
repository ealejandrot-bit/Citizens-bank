"""Paso 1 · Target y churn rate.

- y_B (principal [DEF-default] I-1), y_A (sensibilidad), y_B_indet (soft con pérdida < θ), pesos de clase w.
- Sensibilidad de eventos a θ = 0.20 / 0.25 / 0.35 / 0.50 sobre value_lost_6m / relationship_value.
- Exclusiones acumuladas: churn_excluded (I-4), tenure_years < 1 (I-8); history_months < 24 se conserva con indicador.
- Churn por hogares, por RV bruto (Σ RV eventos / Σ RV) y económico (Σ value_lost eventos / Σ RV), por segmento.
- Pesos de clase balanceados: w = N / (2·n_clase) en la población de modelado; se guardan las odds de población para
  corregir el intercepto (β₀ = β₀* − ln(odds muestra ponderada) + ln(odds población)) en el paso 11.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from common import PROC, REPORTS, THETA_B, eligible, load_raw, loss_ratio, md_table, save_table, set_seed

set_seed()
df = load_raw()
el = eligible(df)
hard, soft = df.hard_churn_6m == 1, df.soft_churn_3m == 1
r = loss_ratio(df)
ten_lt1 = df.tenure_years < 1
hist_lt24 = df.history_months < 24

# ── Sensibilidad a θ (elegibles y población final) ──────────────────────────────────────
rows = []
for base_lab, base in (("elegibles", el), ("elegibles con tenure ≥ 1", el & ~ten_lt1)):
    for th in (0.20, 0.25, 0.35, 0.50):
        ev = base & (hard | (soft & (r >= th)))
        ind = base & soft & (r < th)
        n = int((base & ~ind).sum())
        rows.append({"población": base_lab, "θ": th, "eventos": int(ev.sum()), "de ellos hard": int((base & hard).sum()),
                     "de ellos soft ≥ θ": int((base & soft & (r >= th)).sum()), "indeterminados (soft < θ)": int(ind.sum()),
                     "base": n, "tasa %": 100 * ev.sum() / n})
theta = pd.DataFrame(rows)
save_table(theta, "step01_theta_sensitivity")

# ── Exclusiones acumuladas ──────────────────────────────────────────────────────────────
indet = soft & (r < THETA_B)
steps = [("total archivo", pd.Series(True, index=df.index)),
         ("− churn_excluded (I-4)", el),
         ("− tenure_years < 1 (I-8)", el & ~ten_lt1),
         ("− indeterminados B (soft con pérdida < 0.25)", el & ~ten_lt1 & ~indet)]
ex = []
prev = None
for lab, m in steps:
    ex.append({"paso": lab, "hogares": int(m.sum()), "salen": 0 if prev is None else int((prev & ~m).sum()),
               "eventos B": int((m & (hard | (soft & (r >= THETA_B)))).sum()), "eventos A (hard)": int((m & hard).sum()),
               "RV $B": df.relationship_value[m].sum() / 1e9})
    prev = m
exc = pd.DataFrame(ex)
lost = pd.DataFrame([{"grupo excluido": "tenure_years < 1 (elegibles)", "hogares": int((el & ten_lt1).sum()),
                      "eventos A": int((el & ten_lt1 & hard).sum()), "eventos B": int((el & ten_lt1 & (hard | (soft & (r >= THETA_B)))).sum()),
                      "tasa A %": 100 * (el & ten_lt1 & hard).sum() / (el & ten_lt1).sum(),
                      "tasa A % resto": 100 * (el & ~ten_lt1 & hard).sum() / (el & ~ten_lt1).sum(),
                      "tasa B %": 100 * (el & ten_lt1 & (hard | (soft & (r >= THETA_B)))).sum() / (el & ten_lt1 & ~indet).sum(),
                      "tasa B % resto": 100 * (el & ~ten_lt1 & (hard | (soft & (r >= THETA_B)))).sum() / (el & ~ten_lt1 & ~indet).sum()}])
save_table(exc, "step01_exclusions")
save_table(lost, "step01_excluded_tenure_profile")

# ── Población, targets y pesos ─────────────────────────────────────────────────────────
pop = pd.DataFrame({"household_id": df.household_id, "segment": df.segment})
pop["excl_reason"] = np.select([~el, ten_lt1], ["churn_excluded", "tenure_lt_1"], "")
pop["in_pop_A"] = el & ~ten_lt1
pop["in_pop_B"] = el & ~ten_lt1 & ~indet
pop["y_B_indet"] = el & ~ten_lt1 & indet
pop["y_A"] = np.where(pop.in_pop_A, hard.astype(float), np.nan)
pop["y_B"] = np.where(pop.in_pop_B, (hard | (soft & (r >= THETA_B))).astype(float), np.nan)
pop["hist_lt24"] = hist_lt24
wt = []
for t in ("A", "B"):
    m = pop[f"in_pop_{t}"]
    y = pop.loc[m, f"y_{t}"]
    n, n1 = len(y), y.sum()
    w1, w0 = n / (2 * n1), n / (2 * (n - n1))
    pop[f"w_{t}"] = np.where(m, np.where(pop[f"y_{t}"] == 1, w1, w0), np.nan)
    wt.append({"target": t, "N": int(n), "eventos": int(n1), "tasa %": 100 * n1 / n, "w eventos": w1, "w no eventos": w0,
               "odds población (malos:buenos)": n1 / (n - n1), "ln odds población": np.log(n1 / (n - n1)),
               "odds muestra ponderada": (w1 * n1) / (w0 * (n - n1))})
wtab = pd.DataFrame(wt)
save_table(wtab, "step01_weights")
PROC.mkdir(parents=True, exist_ok=True)
pop.to_parquet(PROC / "step01_population.parquet", index=False)

# ── Churn rate de la población final ────────────────────────────────────────────────────
cr = []
for t in ("A", "B"):
    for s_ in ("Total", "HNW", "UHNW"):
        m = pop[f"in_pop_{t}"] & ((pop.segment == s_) if s_ != "Total" else True)
        y = pop.loc[m, f"y_{t}"]
        rv, vl = df.relationship_value[m], df.value_lost_6m[m]
        cr.append({"target": t, "segmento": s_, "hogares": int(m.sum()), "eventos": int(y.sum()), "churn hogares %": 100 * y.mean(),
                   "churn RV bruto %": 100 * (rv * y).sum() / rv.sum(), "churn económico %": 100 * (vl * y).sum() / rv.sum()})
crt = pd.DataFrame(cr)
save_table(crt, "step01_churn_rates")
h24 = pd.DataFrame([{"target": t, "hogares con history < 24": int((pop[f"in_pop_{t}"] & pop.hist_lt24).sum()),
                     "tasa con history < 24 %": 100 * pop.loc[pop[f"in_pop_{t}"] & pop.hist_lt24, f"y_{t}"].mean(),
                     "tasa con history = 24 %": 100 * pop.loc[pop[f"in_pop_{t}"] & ~pop.hist_lt24, f"y_{t}"].mean()} for t in ("A", "B")])
save_table(h24, "step01_history_indicator")


def mix_check(t):
    x = crt[crt.target == t].set_index("segmento")
    return (x.loc[["HNW", "UHNW"], "hogares"] / x.loc["Total", "hogares"] * x.loc[["HNW", "UHNW"], "churn hogares %"]).sum(), x.loc["Total", "churn hogares %"]


mA, tA = mix_check("A")
mB, tB = mix_check("B")
fin = exc.iloc[-1]
rep = f"""# Paso 1 · Target y churn rate

## Objetivo
- Construir `y_B` (principal), `y_A` (sensibilidad), indeterminados y pesos, con exclusiones y churn rate de la
  población de modelado.

## Método
- `y_B` = hard ∪ (soft con `value_lost_6m / relationship_value` ≥ θ), θ = 0.25 [DEF-default]; soft con pérdida < θ =
  indeterminado (fuera de entrenamiento y métricas, dentro de scoring). `y_A` = `hard_churn_6m`.
- Exclusiones: `churn_excluded` [DEF-default I-4] y `tenure_years` < 1 [DEF-default I-8]; `history_months` < 24 se
  conserva con indicador `hist_lt24`.
- Pesos de clase balanceados: w = N / (2·n_clase); odds de población guardadas para corregir el intercepto (paso 11).
- Churn por hogares = eventos / hogares; RV bruto = Σ RV eventos / Σ RV; económico = Σ `value_lost_6m` eventos / Σ RV.
- Censura: no aplica (sin tiempo al evento). Supervivencia: no [DEF-default I-9]; solo descriptivo en el paso 14.

## Código
- `src/step01_target.py` · `tests/test_step01.py` · salida `data/processed/step01_population.parquet`.

## Resultados

### Sensibilidad a θ [DATA]
{md_table(theta, floatfmt=",.2f")}

- θ = 0.20 equivale a C (hard ∪ soft) y no deja indeterminados: la pérdida mínima de soft es 0.2003 [DATA].
- Verificación: eventos = hard + soft ≥ θ en cada fila; base = población − indeterminados.

### Exclusiones acumuladas [DATA]
{md_table(exc, floatfmt=",.2f")}

- N final B = {int(fin['hogares']):,} hogares con {int(fin['eventos B']):,} eventos [DATA]; N final A = {int(exc.iloc[2]['hogares']):,} con
  {int(exc.iloc[2]['eventos A (hard)']):,} eventos [DATA].
- Verificación: cada fila = anterior − salen.

Perfil de los excluidos por antigüedad < 1 año [DATA]:
{md_table(lost, floatfmt=",.2f")}

### Pesos [DATA]
{md_table(wtab, floatfmt=",.4f")}

- Con pesos balanceados la muestra ponderada tiene odds 1:1; el paso 11 corrige β₀ con ln odds de población.

### Churn rate de la población final [DATA]
{md_table(crt, floatfmt=",.2f")}

- Verificación Σ share × tasa: A {mA:.4f}% = {tA:.4f}%; B {mB:.4f}% = {tB:.4f}% [DATA].

### Historia corta (indicador) [DATA]
{md_table(h24, floatfmt=",.2f")}

## Tests
- `tests/test_step01.py` (ver pytest).

## Decisiones y preguntas abiertas
- D1.1–D1.3 en `reports/decision_log.md`.
"""
(REPORTS / "step01.md").write_text(rep, encoding="utf-8")
print(theta.round(2).to_string(index=False)); print(exc.round(2).to_string(index=False)); print(lost.round(2).to_string(index=False))
print(wtab.round(4).to_string(index=False)); print(crt.round(2).to_string(index=False)); print(h24.round(2).to_string(index=False))
