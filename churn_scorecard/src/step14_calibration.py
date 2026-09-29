"""Paso 14 · Calibración del campeón sobre validación (target B).

- Platt: y ~ a + b·logit(p_score) en val; aceptación 0.8 ≤ b ≤ 1.2. Isotónica permitida (val tiene ≥ 300 eventos):
  se compara con Platt por Brier y ECE en OOF de 5 folds dentro de val, con IC bootstrap 95% (1,000 réplicas) de la
  diferencia. Regla fijada antes de ver resultados: isotónica solo si mejora Brier con IC de la diferencia < 0; si no,
  Platt (D14.1). Calibrador final ajustado en todo val.
- Alineación media p vs tasa observada (dev y val). Tramo: esperado vs observado con Wilson 90% y shrinkage
  beta-binomial m = 30 hacia lo esperado. Por segmento y por banda de RV: Σ p·RV vs Σ RV de eventos y Σ value_lost.
  Cola alta de RV: prueba de razón de verosimilitud de agregar log_rv a la calibración.
- Diseño de control aleatorio 10–15% en Alto (sin cohortes pre/post: solo diseño). Proporción de churn a 3M vs 6M
  por tramo (descriptivo).
"""
from __future__ import annotations

import pickle

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import chi2, norm
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss
from sklearn.model_selection import StratifiedKFold
from statsmodels.stats.proportion import proportion_confint

from common import FIGS, MODEL, PROC, REPORTS, SCORES, SEED, load_split, md_table, save_table, set_seed

set_seed()
SC = pd.read_parquet(PROC / "step12_scores.parquet")
TR = ["Crítico", "Alto", "Vigilancia", "Estable"]


def part(p):
    d = load_split(p).merge(SC, on="household_id")
    return d[d.in_pop_B].reset_index(drop=True)


dev, val = part("dev"), part("val")
lg = lambda p: np.log(p / (1 - p))  # noqa: E731
y = val.y_B.astype(int).to_numpy()
x = lg(val.probabilidad.to_numpy())


def platt_fit(xx, yy):
    return sm.GLM(yy, sm.add_constant(xx), family=sm.families.Binomial()).fit()


def platt_pred(m, xx):
    return m.predict(sm.add_constant(xx, has_constant="add"))


def ece(yy, p, k=10):
    d = pd.qcut(pd.Series(p).rank(method="first"), k, labels=False)
    g = pd.DataFrame({"d": d, "p": p, "y": yy}).groupby("d").agg(n=("y", "size"), p=("p", "mean"), y=("y", "mean"))
    return float((g.n / g.n.sum() * (g.p - g.y).abs()).sum())


# OOF dentro de val
oof_p, oof_i = np.zeros(len(y)), np.zeros(len(y))
for tr, te in StratifiedKFold(5, shuffle=True, random_state=SEED).split(x, y):
    oof_p[te] = platt_pred(platt_fit(x[tr], y[tr]), x[te])
    oof_i[te] = IsotonicRegression(out_of_bounds="clip", y_min=1e-4, y_max=1 - 1e-4).fit(x[tr], y[tr]).predict(x[te])
rng = np.random.default_rng(SEED)
bs = []
for _ in range(1000):
    i = rng.choice(len(y), len(y), replace=True)
    bs.append((brier_score_loss(y[i], oof_i[i]) - brier_score_loss(y[i], oof_p[i]), ece(y[i], oof_i[i]) - ece(y[i], oof_p[i])))
bs = np.array(bs)
p_raw = val.probabilidad.to_numpy()
CMP = pd.DataFrame([
    {"método": "sin calibrar (score)", "Brier": brier_score_loss(y, p_raw), "ECE (pp)": 100 * ece(y, p_raw), "media p %": 100 * p_raw.mean()},
    {"método": "Platt (OOF 5 folds en val)", "Brier": brier_score_loss(y, oof_p), "ECE (pp)": 100 * ece(y, oof_p), "media p %": 100 * oof_p.mean()},
    {"método": "isotónica (OOF 5 folds en val)", "Brier": brier_score_loss(y, oof_i), "ECE (pp)": 100 * ece(y, oof_i), "media p %": 100 * oof_i.mean()}])
CMP["tasa observada %"] = 100 * y.mean()
DIFF = pd.DataFrame([{"diferencia (isotónica − Platt)": "Brier", "media": bs[:, 0].mean(), "IC 95% inf": np.quantile(bs[:, 0], 0.025), "IC 95% sup": np.quantile(bs[:, 0], 0.975)},
                     {"diferencia (isotónica − Platt)": "ECE", "media": bs[:, 1].mean(), "IC 95% inf": np.quantile(bs[:, 1], 0.025), "IC 95% sup": np.quantile(bs[:, 1], 0.975)}])
use_iso = np.quantile(bs[:, 0], 0.975) < 0
M = platt_fit(x, y)
a_, b_ = float(M.params[0]), float(M.params[1])
b_ci = np.asarray(M.conf_int())[1]
save_table(CMP, "step14_method_comparison")
save_table(DIFF, "step14_iso_vs_platt_bootstrap")
PL = pd.DataFrame([{"a": a_, "b": b_, "b IC95 inf": b_ci[0], "b IC95 sup": b_ci[1], "0.8 ≤ b ≤ 1.2": 0.8 <= b_ <= 1.2,
                    "método elegido": "isotónica" if use_iso else "Platt"}])
save_table(PL, "step14_platt")
ISO = IsotonicRegression(out_of_bounds="clip", y_min=1e-4, y_max=1 - 1e-4).fit(x, y)


def calibrate(p):
    xx = lg(np.clip(p, 1e-9, 1 - 1e-9))
    return ISO.predict(xx) if use_iso else 1 / (1 + np.exp(-(a_ + b_ * xx)))


with open(MODEL / "step14_calibrator.pkl", "wb") as fh:
    pickle.dump({"method": "isotonic" if use_iso else "platt", "a": a_, "b": b_, "isotonic": ISO if use_iso else None}, fh)
for d in (dev, val):
    d["p_cal"] = calibrate(d.probabilidad.to_numpy())

# Alineación
AL = pd.DataFrame([{"muestra": n_, "media p score %": 100 * d.probabilidad.mean(), "media p calibrada %": 100 * d.p_cal.mean(), "tasa observada %": 100 * d.y_B.mean()}
                   for n_, d in (("dev", dev), ("val", val))])
save_table(AL, "step14_alignment")


# Tramo: esperado vs observado (val), Wilson 90%, shrinkage m = 30
def tramo_tab(d, key="tramo", keys=TR, label="tramo"):
    rows = []
    for t in keys:
        g = d[d[key] == t]
        if len(g) == 0:
            continue
        e, n_ = int(g.y_B.sum()), len(g)
        lo, hi = proportion_confint(e, n_, alpha=0.10, method="wilson")
        pe = g.p_cal.mean()
        rows.append({label: t, "hogares": n_, "eventos": e, "esperada %": 100 * pe, "observada %": 100 * e / n_, "Wilson 90% inf": 100 * lo,
                     "Wilson 90% sup": 100 * hi, "esperada dentro de IC": lo <= pe <= hi, "shrinkage m=30 %": 100 * (e + 30 * pe) / (n_ + 30)})
    return pd.DataFrame(rows)


TT = tramo_tab(val)
save_table(TT, "step14_tramo_calibration")
SEG = pd.concat([tramo_tab(val[val.segment == s_], keys=TR).assign(segmento=s_) for s_ in ("HNW", "UHNW")], ignore_index=True)
save_table(SEG, "step14_segment_calibration")

# Por banda de RV (quintiles de val): Σ p·RV vs Σ RV de eventos y value_lost
val["banda RV"] = pd.qcut(val.relationship_value, 5, labels=["Q1 (menor)", "Q2", "Q3", "Q4", "Q5 (mayor)"])
RVt = val.groupby("banda RV", observed=True).apply(lambda g: pd.Series({
    "hogares": len(g), "eventos": int(g.y_B.sum()), "p calibrada media %": 100 * g.p_cal.mean(), "tasa observada %": 100 * g.y_B.mean(),
    "Σ p·RV $M": (g.p_cal * g.relationship_value).sum() / 1e6, "Σ RV de eventos $M": (g.y_B * g.relationship_value).sum() / 1e6,
    "Σ value_lost observado $M": g.value_lost_6m.fillna(0).sum() / 1e6})).reset_index()
RVt["Σ p·RV / Σ RV eventos"] = RVt["Σ p·RV $M"] / RVt["Σ RV de eventos $M"]
save_table(RVt, "step14_rv_calibration")
TRV = val.groupby("tramo").apply(lambda g: pd.Series({"Σ p·RV $M": (g.p_cal * g.relationship_value).sum() / 1e6,
                                                     "Σ RV de eventos $M": (g.y_B * g.relationship_value).sum() / 1e6,
                                                     "Σ value_lost observado $M": g.value_lost_6m.fillna(0).sum() / 1e6})).reindex(TR).reset_index()
save_table(TRV, "step14_tramo_rv")
# LR test: ¿log_rv mejora la calibración?
m0 = sm.GLM(y, sm.add_constant(lg(val.p_cal.clip(1e-6, 1 - 1e-6).to_numpy())), family=sm.families.Binomial()).fit()
m1 = sm.GLM(y, sm.add_constant(np.column_stack([lg(val.p_cal.clip(1e-6, 1 - 1e-6).to_numpy()), val.log_rv.to_numpy()])), family=sm.families.Binomial()).fit()
LR = 2 * (m1.llf - m0.llf)
LRt = pd.DataFrame([{"prueba": "agregar log_rv a la calibración", "LR": LR, "gl": 1, "p-valor": float(chi2.sf(LR, 1)), "coef log_rv": float(m1.params[2])}])
save_table(LRt, "step14_logrv_test")

# Diseño de control aleatorio en Alto
alto_n = int((SC.tramo == "Alto").sum())
p_alto = TT.set_index("tramo").loc["Alto", "p_cal" if False else "esperada %"] / 100
des = []
for frac in (0.10, 0.125, 0.15):
    nc = int(round(alto_n * frac))
    nt = alto_n - nc
    se = np.sqrt(p_alto * (1 - p_alto) * (1 / nc + 1 / nt))
    mde = (norm.ppf(0.975) + norm.ppf(0.80)) * se
    des.append({"% control": 100 * frac, "hogares control": nc, "hogares tratados": nt, "tasa base (p calibrada Alto) %": 100 * p_alto,
                "efecto mínimo detectable (pp, α 5%, potencia 80%)": 100 * mde, "reducción relativa mínima detectable %": 100 * mde / p_alto})
DES = pd.DataFrame(des)
save_table(DES, "step14_control_design")

# 3M vs 6M por tramo (descriptivo; sobre población A)
dA = load_split("val").merge(SC, on="household_id")
dA = dA[dA.in_pop_A.astype(bool)]
H3 = dA.groupby("tramo").agg(hogares=("hard_churn_6m", "size"), soft_3m=("soft_churn_3m", "sum"), hard_6m=("hard_churn_6m", "sum")).reindex(TR).reset_index()
H3["% soft 3M"] = 100 * H3.soft_3m / H3.hogares
H3["% hard 6M"] = 100 * H3.hard_6m / H3.hogares
H3["soft / (soft + hard) %"] = 100 * H3.soft_3m / (H3.soft_3m + H3.hard_6m)
save_table(H3, "step14_3m_vs_6m")

# Figura: calibración por decil, antes y después
fig, ax = plt.subplots(figsize=(6.2, 5))
for p, lab, col in ((val.probabilidad.to_numpy(), "score (pre-calibración)", "#a3a29c"), (val.p_cal.to_numpy(), f"calibrada ({'isotónica' if use_iso else 'Platt'})", "#2a78d6")):
    d = pd.qcut(pd.Series(p).rank(method="first"), 10, labels=False)
    g = pd.DataFrame({"d": d, "p": p, "y": y}).groupby("d").mean()
    ax.plot(g.p, g.y, marker="o", ms=5, lw=2, color=col, label=lab, markeredgecolor="white", markeredgewidth=1.5)
lim = 0.65
ax.plot([0, lim], [0, lim], ls="--", lw=1, color="#52514e")
ax.set_xlim(0, lim); ax.set_ylim(0, lim)
ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0)); ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
ax.set_xlabel("probabilidad (media del decil)", fontsize=8, color="#52514e"); ax.set_ylabel("tasa de churn B observada", fontsize=8, color="#52514e")
ax.grid(color="#e6e5df", lw=0.6); ax.set_axisbelow(True)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.tick_params(length=0, labelsize=7.5, colors="#52514e")
ax.legend(frameon=False, fontsize=8, loc="upper left")
ax.set_title("Calibración por decil · validación · target B [DATA]", fontsize=10, loc="left")
fig.tight_layout()
fig.savefig(FIGS / "step14_calibration_val.png", dpi=120)

# Salida por household: probabilidad calibrada
out = pd.read_csv(SCORES / "household_scores.csv")
out["probabilidad_calibrada"] = calibrate(out["probabilidad_pre_calibración"].to_numpy())
out.to_csv(SCORES / "household_scores.csv", index=False)
ES = out.groupby("tramo").probabilidad_calibrada.agg(["size", "mean", "min", "max"]).reindex(TR).reset_index()
ES.columns = ["tramo", "hogares (20,000)", "p calibrada media", "p mín", "p máx"]
save_table(ES, "step14_master_probability")

rep = f"""# Paso 14 · Calibración

## Objetivo
- Que la probabilidad publicada coincida con la tasa observada, en total, por tramo, por segmento y por valor.

## Método
- Platt sobre validación: y ~ a + b·logit(p_score); aceptación 0.8 ≤ b ≤ 1.2 [DEF SPEC]. Isotónica comparada por
  Brier y ECE en OOF de 5 folds dentro de val con IC bootstrap 95% (1,000 réplicas); regla previa: isotónica solo si el
  IC de la diferencia de Brier queda < 0 (D14.1).
- Tramo: esperado vs observado con Wilson 90%; shrinkage beta-binomial m = 30 hacia lo esperado.
- Valor: Σ p·RV vs Σ RV de eventos y Σ value_lost por quintil de RV y tramo; prueba LR de log_rv.
- Control aleatorio 10–15% en Alto: solo diseño (sin cohortes pre/post, L7). 3M vs 6M: descriptivo.

## Código
- `src/step14_calibration.py` · `tests/test_step14.py` · `step14_*.csv`, `outputs/model/step14_calibrator.pkl`;
  `household_scores.csv` gana la columna `probabilidad_calibrada`.

## Resultados

### Platt [DATA]
{md_table(PL, floatfmt=",.4f")}

### Platt vs isotónica (OOF en val) [DATA]
{md_table(CMP, floatfmt=",.4f")}

{md_table(DIFF, floatfmt=",.5f")}

- Método elegido: **{'isotónica' if use_iso else 'Platt'}** [DATA].

### Alineación de la media [DATA]
{md_table(AL, floatfmt=",.2f")}

### Tramo: esperado vs observado (val) [DATA]
{md_table(TT, floatfmt=",.2f")}

- Verificación: hogares suman {int(TT.hogares.sum()):,} = {len(val):,}; Σ share × observada = {(TT.hogares * TT['observada %']).sum() / TT.hogares.sum():.2f}% = {100 * y.mean():.2f}% [DATA].

![Calibración](../outputs/figs/step14_calibration_val.png)

### Por segmento (val) [DATA]
{md_table(SEG, floatfmt=",.2f")}

- UHNW: pocos eventos por tramo; se lee como descriptivo (L5).

### Por quintil de RV (val) [DATA]
{md_table(RVt, floatfmt=",.2f")}

### Por tramo en valor (val) [DATA]
{md_table(TRV, floatfmt=",.2f")}

- `value_lost_6m` mide pérdida (no el RV completo): Σ value_lost ≤ Σ RV de eventos por construcción [DATA].

### ¿log_rv mejora la calibración? [DATA]
{md_table(LRt, floatfmt=",.4f")}

### Probabilidad calibrada por tramo (20,000 hogares) [DATA]
{md_table(ES, floatfmt=",.4f")}

### Diseño del control aleatorio en Alto [DEF SPEC 10–15%; tasas DATA]
{md_table(DES, floatfmt=",.2f")}

### Churn a 3M (soft) vs 6M (hard) por tramo (val, población A; descriptivo) [DATA]
{md_table(H3, floatfmt=",.2f")}

## Tests
- `tests/test_step14.py` (ver pytest).

## Decisiones y preguntas abiertas
- D14.1–D14.3 en `reports/decision_log.md`.
"""
(REPORTS / "step14.md").write_text(rep, encoding="utf-8")
for t in (PL, CMP, DIFF, AL, TT, SEG, RVt, TRV, LRt, ES, DES, H3):
    print(t.round(4).to_string(index=False))
