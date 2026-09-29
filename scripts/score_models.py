"""Construye la variable de churn y compara el score de distintas metodologías.

Uso: python scripts/score_models.py
Salidas:
  data/synthetic/churn_labels.csv         -> etiquetas construidas sobre (t, t+6m]
  data/synthetic/model_scores.csv         -> score de cada metodología por hogar (train / test)
  docs/reports/model_comparison.md        -> resultados
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from synthetic import scoring as sc  # noqa: E402
from synthetic.metrics import information_value  # noqa: E402
from synthetic.outcome import construct_churn, simulate_outcome  # noqa: E402
from synthetic.pipeline import build  # noqa: E402
from synthetic.schema import EXCEL_PRIMARY  # noqa: E402

OUT = ROOT / "data" / "synthetic"
REPORT = ROOT / "docs" / "reports" / "model_comparison.md"
TARGETS = {"churn_hard_6m": "Hard churn 6 meses (target principal)", "churn_soft_3m": "Soft churn 3 meses (alerta temprana)"}


def bands(y, s):
    b = pd.cut(s, [-0.01, 39.999, 69.999, 100.01], labels=["Low 0–39", "Watch 40–69", "High 70–100"])
    return pd.DataFrame({"% hogares": pd.Series(y).groupby(b, observed=False).size() / len(y) * 100,
                         "churn %": pd.Series(y).groupby(b, observed=False).mean() * 100})


def main() -> int:
    cfg = yaml.safe_load((ROOT / "config" / "params.yaml").read_text())
    o = build(cfg, upto=8)
    sim_o = simulate_outcome(o["base"], o["truth"], cfg, o["seeds"], o["sim1"])
    labels = construct_churn(sim_o, o["base"], cfg)
    X, cols, seq = sc.model_frame(o, labels)
    X = X[~o["base"]["churn_excluded"].to_numpy()].reset_index(drop=True)
    seed = int(o["seeds"].rng("model.seed").integers(0, 2**31 - 1))

    lines = ["# Comparación de metodologías de score", "",
             f"{len(X):,} hogares (sin excluidos) · partición estratificada 70/30 · semilla derivada de `{cfg['master_seed']}` · "
             "montos en USD.", "",
             "## 1 · La variable de churn construida", "",
             "Se simulan los 6 meses posteriores al corte y la etiqueta se construye sobre lo observado (definiciones del deck):", "",
             "- **Hard churn 6m:** el valor de la relación cae a ≤ 5% del valor en t y no se recupera.",
             "- **Soft churn 3m:** caída del valor ex-mercado > 20% en 3 meses, sin salida total.", ""]
    el = ~o["base"]["churn_excluded"].to_numpy()
    b = o["base"][el].reset_index(drop=True)
    V = labels.loc[el, "relationship_value_t"].sum()
    lines += [pd.DataFrame({
        "construida": [X["churn_hard_6m"].astype(float).mean(), X["churn_soft_3m"].astype(float).mean(),
                       labels.loc[el & (labels["churn_hard_6m"] == 1).to_numpy(), "churn_value_lost"].sum() / V],
        "evento real (generador)": [b["hard_churn_6m"].astype(float).mean(), b["soft_churn_3m"].astype(float).mean(),
                                    b.loc[b["hard_churn_6m"] == 1, "relationship_value"].sum() / b["relationship_value"].sum()]},
        index=["hard churn 6m (logo)", "soft churn 3m", "AUM churn (hard, valor)"]).mul(100).to_markdown(floatfmt=".2f"), "",
        "Coincidencia etiqueta construida vs evento real:", "",
        pd.crosstab(b["soft_churn_3m"].astype(int), X["churn_soft_3m"].astype(int), rownames=["soft real"],
                    colnames=["soft construido"]).to_markdown(), "",
        "El hard churn coincide al 100%. El soft churn construido tiene **falsos positivos**: hogares que no se estaban "
        "contrayendo, pero cruzaron el −20% por una compra de casa o por la volatilidad del saldo; y algunas contracciones "
        "reales no llegan al umbral. Es el ruido de etiqueta que tendría el banco, y la razón por la que el deck pide validar el umbral.", ""]

    # IV de las 37 variables contra la etiqueta construida ("resetear resultados").
    ivs = []
    for vid, (name, col) in sorted(EXCEL_PRIMARY.items()):
        c = "multi_signal_count" if col == "multi_signal_flag" else col
        ivs.append({"#": vid, "variable": name, "IV hard (construida)": information_value(X[c], X["churn_hard_6m"].astype(int)),
                    "IV soft (construida)": information_value(X[c], X["churn_soft_3m"].astype(int))})
    ivt = pd.DataFrame(ivs).set_index("#")
    lines += ["## 2 · IV de las 37 variables contra la etiqueta construida", "", ivt.to_markdown(floatfmt=".3f"), ""]

    scores = X[["household_id", "segment"]].copy()
    summary = {}
    for target, title in TARGETS.items():
        y = X[target].astype(int).to_numpy()
        test = sc.split(X, target, o["seeds"].rng(f"model.split.{target}"))
        tr, te = X[~test], X[test]
        y_tr, y_te = y[~test], y[test]
        value = X["relationship_value_t"].to_numpy() * y  # AUM en riesgo solo de quienes churnean
        seg = X["segment"].to_numpy()

        card = sc.WoEScorecard().fit(tr, y_tr, cols + sc.CONTEXT)
        models = sc.fit_models(tr, y_tr, cols, seq, seed)
        pred = sc.predict(models, te)
        res, probs = {}, {}
        res["M0a · Reglas de negocio"] = sc.evaluate(y_te, sc.business_rules(te), value[test], seg[test])
        res["M0b · Scorecard experto (deck)"] = sc.evaluate(y_te, sc.expert_scorecard(te), value[test], seg[test])
        p_card = card.predict_proba(te)
        probs["M1 · Scorecard estadístico (WoE)"] = p_card
        res["M1 · Scorecard estadístico (WoE)"] = sc.evaluate(y_te, card.score(te), value[test], seg[test], p_card)
        for k, p in pred.items():
            probs[k] = p
            res[k] = sc.evaluate(y_te, p, value[test], seg[test], p)
        if target == "churn_hard_6m":
            res["Techo · probabilidad verdadera"] = sc.evaluate(y_te, te["p_true"].to_numpy(), value[test], seg[test],
                                                               te["p_true"].to_numpy())
        tab = pd.DataFrame(res).T
        summary[target] = tab
        all_scores = {"M0a · Reglas de negocio": sc.business_rules(te), "M0b · Scorecard experto (deck)": sc.expert_scorecard(te),
                      "M1 · Scorecard estadístico (WoE)": card.score(te), **pred}
        if target == "churn_hard_6m":
            all_scores["Techo · probabilidad verdadera"] = te["p_true"].to_numpy()
        boot = sc.bootstrap(y_te, all_scores, value[test], o["seeds"].rng(f"model.bootstrap.{target}"),
                            ref="M2 · Gradient Boosting")

        scores[f"{target}__split"] = np.where(test, "test", "train")
        scores[f"{target}__label"] = y
        scores[f"{target}__expert_score"] = sc.expert_scorecard(X)
        scores[f"{target}__woe_score"] = card.score(X)
        scores[f"{target}__woe_prob"] = card.predict_proba(X)
        for k, p in sc.predict(models, X).items():
            scores[f"{target}__{k.split('·')[1].strip().split(' ')[0].lower()}_prob"] = p

        main_cols = ["AUC", "Gini", "KS", "precisión top 10%", "recall top 10%", "lift top 10%", "captura AUM top 10%",
                     "AUC HNW", "AUC UHNW"]
        lines += [f"## 3 · {title}", "", f"Test: {len(te):,} hogares, churn {y_te.mean():.1%}.", "",
                  "### Discriminación y uso operativo (test)", "",
                  "*precisión / recall / lift top 10%*: qué tan bien funciona la lista del 10% más riesgoso que recibe el banker. "
                  "*captura AUM*: qué parte del valor de los que churnean queda en esa lista.", "",
                  tab[main_cols].to_markdown(floatfmt=".3f"), "",
                  "### Incertidumbre: IC 95% por bootstrap pareado (200 remuestras del test)", "",
                  "La captura de AUM depende de unos pocos hogares muy grandes (cola Pareto), por eso su intervalo es ancho. "
                  "'¿diferencia real?' = el IC de la diferencia de AUC contra el Gradient Boosting no incluye 0.", "",
                  boot.to_markdown(floatfmt=".3f"), "",
                  "### Calibración (test)", "", "Control del deck (slide 17): el promedio del score debe igualar al churn observado.", "",
                  tab[["prob. media", "churn observado", "Brier"]].dropna().to_markdown(floatfmt=".4f"), ""]
        best = max(probs, key=lambda k: res[k]["AUC"])
        lines += [f"Calibración por decil · {best}:", "", sc.calibration_deciles(y_te, probs[best]).to_markdown(floatfmt=".4f"), "",
                  "### Bandas de riesgo de los scorecards (test)", "",
                  "| Banda | Experto: % hogares | Experto: churn % | Estadístico: % hogares | Estadístico: churn % |",
                  "|---|---|---|---|---|"]
        be, bs = bands(y_te, sc.expert_scorecard(te)), bands(y_te, card.score(te))
        for band in be.index:
            lines.append(f"| {band} | {be.loc[band, '% hogares']:.1f} | {be.loc[band, 'churn %']:.1f} | "
                         f"{bs.loc[band, '% hogares']:.1f} | {bs.loc[band, 'churn %']:.1f} |")
        lines += ["", f"### Scorecard estadístico: {len(card.vars)} variables seleccionadas (IV ≥ 0.02, |ρ| entre WoE < 0.8)", "",
                  "Descartadas por redundancia: " + (", ".join(card.dropped_corr) or "ninguna") + ".", "",
                  pd.DataFrame({"IV": {c: card.specs[c]["iv"] for c in card.vars},
                                "coef": dict(zip(card.vars, card.lr.coef_[0])),
                                "puntos máx": {c: 100 * max(card.points[c].values()) / card.max_raw for c in card.vars}})
                  .sort_values("puntos máx", ascending=False).to_markdown(floatfmt=".3f"), ""]
        drv = sc.drivers(models["M2 · Gradient Boosting"], te, y_te, models["_tab"], seed).head(15)
        lines += ["### Principales drivers del Gradient Boosting (importancia por permutación, test)", "",
                  drv.to_markdown(floatfmt=".4f"), ""]
        if target == "churn_hard_6m":
            pts = card.points_table()
            pts.to_csv(OUT / "scorecard_points.csv", index=False, float_format="%.4f")

    OUT.mkdir(parents=True, exist_ok=True)
    labels.to_csv(OUT / "churn_labels.csv", index=False, float_format="%.2f", lineterminator="\n")
    scores.to_csv(OUT / "model_scores.csv", index=False, float_format="%.6f", lineterminator="\n")
    lines += ["## 4 · Cómo leer estos resultados", "",
              "- El **techo** (AUC con la probabilidad verdadera) es el máximo alcanzable: parte del churn es azar puro, que "
              "ningún modelo puede anticipar.",
              "- La base tiene un solo corte: la validación es una partición aleatoria, no out-of-time. Con el panel mensual "
              "se podría entrenar en meses viejos y probar en los últimos 6, como pide el deck (slide 20).",
              "- La red neuronal es un MLP con la secuencia de 12 meses como entrada; una LSTM / Transformer (deck slide 24) "
              "requeriría PyTorch y más historia.", ""]
    REPORT.write_text("\n".join(lines) + "\n")
    for t, tab in summary.items():
        print(f"\n== {TARGETS[t]}")
        print(tab[["AUC", "KS", "precisión top 10%", "lift top 10%", "captura AUM top 10%"] +
                  [c for c in ["prob. media", "churn observado"] if c in tab]].round(3).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
