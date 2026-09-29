"""Chequeos de la base sintética. Cada paso agrega los suyos.

Un chequeo devuelve (nombre, ok, detalle). El build falla si alguno no pasa,
para que ningún paso quede publicado con una distribución fuera de lo esperado.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def auc(y: np.ndarray, score: np.ndarray) -> float:
    """AUC por rangos (Mann-Whitney), sin dependencias externas."""
    y = np.asarray(y, dtype=bool)
    ranks = pd.Series(score).rank(method="average").to_numpy()
    n1, n0 = y.sum(), (~y).sum()
    return (ranks[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def check_step0(base: pd.DataFrame, truth: pd.DataFrame, cfg: dict) -> list[tuple[str, bool, str]]:
    p, tg = cfg["population"], cfg["target"]
    out = []

    def add(name, ok, detail):
        out.append((name, bool(ok), detail))

    add("filas", len(base) == cfg["n_households"], f"{len(base):,}")
    add("household_id único", base["household_id"].is_unique, "")
    add("piso de relación", (base["relationship_value"] >= p["relationship_value_min"]).all(),
        f"min = {base['relationship_value'].min():,.0f}")
    comp = base["deposit_balance"] + base["aum"].fillna(0) - base["relationship_value"]
    add("depósitos + AUM = relación", comp.abs().max() < 0.05, f"máx desvío {comp.abs().max():.4f}")

    # NULL vs cero: AUM es NULL exactamente cuando no hay inversiones.
    add("AUM NULL ⇔ sin inversiones", (base["aum"].isna() == ~base["has_investments"]).all(), "")
    add("advisory ⊂ inversiones", (~base["has_advisory"] | base["has_investments"]).all(), "")
    add("dividendos ⊂ inversiones", (~base["has_dividend_stream"] | base["has_investments"]).all(), "")

    dep_only = 1 - base["has_investments"].mean()
    add("share deposit-only", abs(dep_only - p["share_deposit_only"]) < 0.015,
        f"{dep_only:.3f} vs {p['share_deposit_only']}")
    uhnw = (base["segment"] == "UHNW").mean()
    add("share UHNW en [2%, 10%]", 0.02 <= uhnw <= 0.10, f"{uhnw:.3%}")
    add("antigüedad < edad adulta", (base["tenure_years"] <= base["age_primary"] - 18 + 1e-9).all(), "")
    add("history_months ≤ tope", base["history_months"].max() <= p["history_months_cap"], "")

    # Ingresos (Private Banking: ingresos altos)
    inc = cfg["income"]
    for col, flag in [("salary_base_annual", "has_payroll_stream"), ("pension_monthly", "has_pension_stream"),
                      ("dividend_annual", "has_dividend_stream"),
                      ("business_distribution_annual", "has_linked_business")]:
        add(f"{col} NULL ⇔ sin flujo", (base[col].isna() == ~base[flag]).all(), "")
    sal = base["salary_base_annual"].dropna()
    add("sueldo ≥ piso PB", (sal >= inc["salary_min"]).all(), f"min = {sal.min():,.0f}")
    add("mediana sueldo base en [$300k, $500k]", 300_000 <= sal.median() <= 500_000, f"{sal.median():,.0f}")
    rho = np.corrcoef(np.log(sal), np.log(base.loc[sal.index, "relationship_value"]))[0, 1]
    add("corr(log sueldo, log patrimonio) en [0.30, 0.60]", 0.30 <= rho <= 0.60, f"{rho:.3f}")
    add("pensión ≥ piso", (base["pension_monthly"].dropna() >= inc["pension_monthly_min"]).all(), "")
    rim = base["recurring_income_monthly"]
    add("ingreso recurrente > 0 ⇔ algún flujo", ((rim > 0) == base["has_any_recurring_stream"]).all(), "")
    freq = base["pay_frequency"].dropna().value_counts(normalize=True)
    dev_f = max(abs(freq.get(k, 0) - v) for k, v in inc["pay_frequency"].items())
    add("frecuencias de pago ≈ config", dev_f < 0.02, f"máx desvío {dev_f:.3f}")

    # Target
    eligible = ~base["churn_excluded"]
    add("target NULL ⇔ excluido", (base["hard_churn_6m"].isna() == base["churn_excluded"]).all(), "")
    hard = base.loc[eligible, "hard_churn_6m"].astype(int)
    soft = base.loc[eligible, "soft_churn_3m"].astype(int)
    add("hard y soft excluyentes", ((hard + soft) <= 1).all(), "")
    # Tolerancia de 3 errores estándar binomiales.
    se = np.sqrt(tg["hard_churn_6m_rate"] * (1 - tg["hard_churn_6m_rate"]) / eligible.sum())
    add("tasa hard churn 6m", abs(hard.mean() - tg["hard_churn_6m_rate"]) < 3 * se,
        f"{hard.mean():.3%} vs {tg['hard_churn_6m_rate']:.1%} (±{3*se:.2%})")
    se_s = np.sqrt(tg["soft_churn_3m_rate"] * (1 - tg["soft_churn_3m_rate"]) / eligible.sum())
    add("tasa soft churn 3m", abs(soft.mean() - tg["soft_churn_3m_rate"]) < 3 * se_s,
        f"{soft.mean():.3%} vs {tg['soft_churn_3m_rate']:.1%} (±{3*se_s:.2%})")
    add("antigüedad ≤ tope", base["tenure_years"].max() <= p["tenure_max_years"], "")
    tr = truth.loc[eligible.to_numpy()]
    add("calibración E[p_hard] = tasa", abs(tr["p_hard_6m"].mean() - tg["hard_churn_6m_rate"]) < 1e-6,
        f"{tr['p_hard_6m'].mean():.4%}")

    # Techo del score: AUC usando la probabilidad VERDADERA. Si fuese ~1, cualquier
    # modelo sobre esta base saldría irrealmente bueno. Rango objetivo: 0.75–0.90.
    oracle = auc(hard.to_numpy(), tr["p_hard_6m"].to_numpy())
    add("AUC techo (oráculo) en [0.75, 0.90]", 0.75 <= oracle <= 0.90, f"{oracle:.3f}")

    # Correlación empírica de latentes vs configurada.
    zc = truth[[c for c in truth if c.startswith("z_")]].corr().to_numpy()
    dev = np.abs(zc - np.asarray(cfg["latent"]["correlation"])).max()
    add("correlación latentes ≈ config", dev < 0.03, f"máx desvío {dev:.3f}")
    return out


def summarize_step0(base: pd.DataFrame, truth: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Tablas descriptivas para el reporte."""
    el = base[~base["churn_excluded"]].copy()
    el["hard"] = el["hard_churn_6m"].astype(int)
    el["soft"] = el["soft_churn_3m"].astype(int)
    tr = truth.set_index("household_id").loc[el["household_id"]]

    num = base[["relationship_value", "deposit_balance", "aum", "age_primary", "tenure_years",
                "history_months"]].describe(percentiles=[.05, .25, .5, .75, .95]).T
    flags = base[[c for c in base if c.startswith("has_")]].mean().to_frame("share")
    inc_cols = ["salary_base_annual", "bonus_annual", "pension_monthly", "dividend_annual",
                "business_distribution_annual", "recurring_income_monthly"]
    income = base[inc_cols].describe(percentiles=[.05, .25, .5, .75, .95]).T
    income_seg = base.groupby("segment")[inc_cols].median().T

    by_seg = el.groupby("segment").agg(households=("hard", "size"), hard_churn=("hard", "mean"),
                                       soft_churn=("soft", "mean"))
    start_value = el["relationship_value"].sum()
    churn = pd.DataFrame({
        "logo": [el["hard"].mean()],
        "aum_value": [el.loc[el["hard"] == 1, "relationship_value"].sum() / start_value],
        "soft_contraction_value": [el.loc[el["soft"] == 1, "value_lost_6m"].sum() / start_value],
    }, index=["6m"])
    deciles = pd.qcut(tr["risk_index"].to_numpy(), 10, labels=range(1, 11))
    by_decile = el.groupby(deciles, observed=True).agg(hard_churn=("hard", "mean"), soft_churn=("soft", "mean"))
    by_decile.index.name = "decil_riesgo_latente"
    drivers = tr.groupby("primary_driver").size().to_frame("households")
    drivers["hard_churn"] = el.groupby(tr["primary_driver"].to_numpy())["hard"].mean()
    return {"numéricas": num, "flags": flags, "ingresos (USD)": income,
            "mediana de ingresos por segmento (USD)": income_seg, "churn por segmento": by_seg,
            "logo vs AUM churn": churn, "churn por decil de riesgo latente": by_decile,
            "trayectoria principal": drivers}
