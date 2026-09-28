"""Paso 0 · Población de hogares, estructura latente de riesgo y target.

Salidas (dos tablas, a propósito separadas):
  * base  : atributos observables del hogar + etiquetas (target). Es lo que ve el modelo.
  * truth : factores latentes, índice de riesgo y probabilidades verdaderas. NUNCA
            entra como feature; solo sirve para validar (p. ej. AUC techo).

Las variables del Excel (pasos 1+) se generarán desde `truth` (latentes) más
ruido propio de cada variable, jamás desde el target.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import optimize, special, stats

from .seeds import SeedManager


def _calibrate_intercept(slope_x: np.ndarray, target_rate: float) -> float:
    """Intercepto `a` tal que mean(sigmoid(a + slope_x)) == target_rate."""
    f = lambda a: special.expit(a + slope_x).mean() - target_rate
    return optimize.brentq(f, -30.0, 30.0, xtol=1e-12)


def build_population(cfg: dict, seeds: SeedManager) -> tuple[pd.DataFrame, pd.DataFrame]:
    n = int(cfg["n_households"])
    p = cfg["population"]
    lat = cfg["latent"]
    tg = cfg["target"]

    hh_id = np.array([f"HH{i:06d}" for i in range(1, n + 1)])

    # --- Valor de la relación y composición -------------------------------
    rng = seeds.rng("pop.relationship_value")
    mu = np.log(p["relationship_value_median"])
    value = rng.lognormal(mu, p["relationship_value_sigma"], n)
    # Piso de Private Bank por remuestreo (no por recorte: recortar apila masa en el piso).
    below = value < p["relationship_value_min"]
    while below.any():
        value[below] = rng.lognormal(mu, p["relationship_value_sigma"], below.sum())
        below = value < p["relationship_value_min"]

    has_investments = seeds.rng("pop.deposit_only").random(n) >= p["share_deposit_only"]
    a, b = p["deposit_share_beta"]
    dep_share = seeds.rng("pop.deposit_share").beta(a, b, n)
    dep_share = np.where(has_investments, dep_share, 1.0)
    deposits = value * dep_share
    aum = np.where(has_investments, value - deposits, np.nan)  # NULL si no aplica
    is_uhnw = value >= p["uhnw_threshold"]
    segment = np.where(is_uhnw, "UHNW", "HNW")

    # --- Demografía y antigüedad -----------------------------------------
    lo, hi = p["age_bounds"]
    m, s = p["age_mean"], p["age_sd"]
    age = stats.truncnorm.rvs((lo - m) / s, (hi - m) / s, loc=m, scale=s, size=n,
                              random_state=seeds.rng("pop.age"))
    age = np.floor(age).astype(int)

    k, theta = p["tenure_gamma"]
    tenure_years = seeds.rng("pop.tenure").gamma(k, theta, n)
    # Coherente con la edad y con tope de cola (la Gamma genera colas de 60+ años).
    tenure_years = np.minimum(tenure_years, np.minimum(np.maximum(age - 18, 0.5), p["tenure_max_years"]))
    history_months = np.minimum(np.floor(tenure_years * 12), p["history_months_cap"]).astype(int)

    # --- Entidades y productos ancla ---------------------------------------
    def bern(name, prob):
        return seeds.rng(name).random(n) < prob

    has_business = bern("pop.business", np.where(is_uhnw, p["p_linked_business_uhnw"], p["p_linked_business"]))
    has_trust = bern("pop.trust", np.where(is_uhnw, p["p_trust_uhnw"], p["p_trust"]))
    has_advisory = has_investments & bern("pop.advisory", p["p_advisory_given_investments"])
    has_credit_anchor = bern("pop.credit", p["p_credit_anchor"])

    # --- Flujos de ingreso recurrentes (definen aplicabilidad de variables) ----
    retired = age >= p["retirement_age"]
    has_payroll = bern("pop.payroll", np.where(retired, p["p_payroll_if_retired"], p["p_payroll_if_working"]))
    has_pension = bern("pop.pension", np.where(retired, p["p_pension_if_retired"], p["p_pension_if_working"]))
    has_dividend = has_investments & bern("pop.dividend", p["p_dividend_stream_given_investments"])

    # --- Factores latentes correlacionados ---------------------------------
    names = lat["factors"]
    corr = np.asarray(lat["correlation"], dtype=float)
    L = np.linalg.cholesky(corr)  # falla si la matriz no es definida positiva
    z = seeds.rng("latent.factors").standard_normal((n, len(names))) @ L.T
    w = np.array([lat["risk_weights"][f] for f in names])
    contrib = z * w
    eps = seeds.rng("latent.idiosyncratic").standard_normal(n) * lat["idiosyncratic_sd"]
    structural = (lat["tenure_effect_per_log_year"] * np.log1p(tenure_years)
                  + lat["credit_anchor_effect"] * has_credit_anchor
                  + lat["uhnw_effect"] * is_uhnw)
    risk_raw = contrib.sum(axis=1) + structural + eps
    risk_index = (risk_raw - risk_raw.mean()) / risk_raw.std()
    primary_driver = np.array(names)[contrib.argmax(axis=1)]

    # --- Exclusiones (muerte / reubicación): target NULL ---------------------
    excluded = seeds.rng("target.exclusion").random(n) < tg["exclusion_rate"]

    # --- Hard churn 6m -----------------------------------------------------
    x_h = tg["hard_churn_slope"] * risk_index
    a_h = _calibrate_intercept(x_h[~excluded], tg["hard_churn_6m_rate"])
    p_hard = special.expit(a_h + x_h)
    hard = seeds.rng("target.hard").random(n) < p_hard

    # --- Soft churn 3m (solo entre quienes no salen del todo) ---------------
    x_s = tg["soft_churn_slope"] * risk_index
    eligible_soft = ~excluded & ~hard
    # La tasa configurada es sobre TODOS los hogares elegibles (no excluidos), igual
    # que hard churn; se reescala porque solo los que no hacen hard pueden hacer soft.
    soft_rate_among_eligible_soft = tg["soft_churn_3m_rate"] * (~excluded).sum() / eligible_soft.sum()
    a_s = _calibrate_intercept(x_s[eligible_soft], soft_rate_among_eligible_soft)
    p_soft = special.expit(a_s + x_s)
    soft = eligible_soft & (seeds.rng("target.soft").random(n) < p_soft)
    lo_l, hi_l = tg["soft_churn_loss_range"]
    soft_loss_frac = seeds.rng("target.soft_loss").uniform(lo_l, hi_l, n)

    value_lost = np.where(hard, value, np.where(soft, value * soft_loss_frac, 0.0))

    def label(x):
        return pd.array(np.where(excluded, pd.NA, x.astype(int)), dtype="Int8")

    base = pd.DataFrame({
        "household_id": hh_id,
        "snapshot_date": pd.Timestamp(cfg["snapshot_date"]),
        "segment": segment,
        "relationship_value": value.round(2),
        "deposit_balance": deposits.round(2),
        "aum": np.round(aum, 2),
        "has_investments": has_investments,
        "has_advisory": has_advisory,
        "has_linked_business": has_business,
        "has_trust": has_trust,
        "has_credit_anchor": has_credit_anchor,
        "has_payroll_stream": has_payroll,
        "has_pension_stream": has_pension,
        "has_dividend_stream": has_dividend,
        "has_any_recurring_stream": has_payroll | has_pension | has_dividend,
        "age_primary": age,
        "tenure_years": tenure_years.round(2),
        "history_months": history_months,
        "churn_excluded": excluded,
        "hard_churn_6m": label(hard),
        "soft_churn_3m": label(soft),
        "value_lost_6m": np.where(excluded, np.nan, value_lost.round(2)),
    })

    truth = pd.DataFrame({"household_id": hh_id})
    for j, f in enumerate(names):
        truth[f"z_{f}"] = z[:, j]
    truth["eps_idiosyncratic"] = eps
    truth["risk_index"] = risk_index
    truth["primary_driver"] = primary_driver
    truth["p_hard_6m"] = p_hard
    truth["p_soft_3m"] = np.where(eligible_soft, p_soft, np.nan)
    truth.attrs["intercepts"] = {"hard": a_h, "soft": a_s}
    return base, truth
