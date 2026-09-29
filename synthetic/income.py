"""Paso 0 · Montos de ingreso recurrente (Private Banking: ingresos altos).

Los montos dependen del patrimonio (log-valor de la relación) pero NO de los
factores latentes de riesgo: el nivel de ingreso es estructura, no señal de churn.
Las señales (cortes de nómina, caídas de ingreso) se generan en el Paso 2 sobre
estos niveles.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .seeds import SeedManager


def _wealth_linked_lognormal(rng, lv, median, sigma, corr, floor=None):
    """ln(x) = ln(median) + corr·sigma·lv + sigma·sqrt(1−corr²)·ε, con piso por remuestreo de ε."""
    idio = sigma * np.sqrt(1.0 - corr**2)
    loc = np.log(median) + corr * sigma * lv
    eps = rng.standard_normal(len(lv))
    x = np.exp(loc + idio * eps)
    if floor is not None:
        below = x < floor
        while below.any():
            eps[below] = rng.standard_normal(below.sum())
            x = np.exp(loc + idio * eps)
            below = x < floor
    return x


def build_income(base: pd.DataFrame, cfg: dict, seeds: SeedManager) -> pd.DataFrame:
    inc, pop = cfg["income"], cfg["population"]
    n = len(base)
    value = base["relationship_value"].to_numpy()
    lv = (np.log(value) - np.log(pop["relationship_value_median"])) / pop["relationship_value_sigma"]

    has_pay = base["has_payroll_stream"].to_numpy()
    has_pen = base["has_pension_stream"].to_numpy()
    has_div = base["has_dividend_stream"].to_numpy()
    has_bus = base["has_linked_business"].to_numpy()

    salary = _wealth_linked_lognormal(seeds.rng("income.salary"), lv, inc["salary_base_median"],
                                      inc["salary_sigma"], inc["salary_wealth_corr"], inc["salary_min"])
    a, b = inc["bonus_share_beta"]
    lo_b, hi_b = inc["bonus_share_min"], inc["bonus_share_max"]
    bonus_share = lo_b + (hi_b - lo_b) * seeds.rng("income.bonus").beta(a, b, n)
    no_bonus = seeds.rng("income.no_bonus").random(n) < inc["p_no_bonus"]
    bonus_share = np.where(no_bonus, 0.0, bonus_share)  # aplica y vale 0: cero, no NULL
    freqs = list(inc["pay_frequency"])
    probs = np.array([inc["pay_frequency"][f] for f in freqs])
    pay_freq = seeds.rng("income.pay_frequency").choice(freqs, size=n, p=probs / probs.sum())

    pension = _wealth_linked_lognormal(seeds.rng("income.pension"), lv, inc["pension_monthly_median"],
                                       inc["pension_sigma"], inc["pension_wealth_corr"], inc["pension_monthly_min"])
    a, b = inc["dividend_yield_beta"]
    div_yield = seeds.rng("income.dividend_yield").beta(a, b, n)
    dividends = base["aum"].fillna(0).to_numpy() * div_yield

    business = _wealth_linked_lognormal(seeds.rng("income.business"), lv, inc["business_distribution_median"],
                                        inc["business_distribution_sigma"], inc["business_distribution_wealth_corr"])

    def only(mask, x):
        return np.where(mask, np.round(x, 2), np.nan)  # NULL si el flujo no existe

    out = pd.DataFrame({
        "salary_base_annual": only(has_pay, salary),
        "bonus_annual": only(has_pay, salary * bonus_share),
        "pay_frequency": np.where(has_pay, pay_freq, None),
        "pension_monthly": only(has_pen, pension),
        "dividend_annual": only(has_div, dividends),
        "business_distribution_annual": only(has_bus, business),
    })
    # Ingreso recurrente mensual "normal" (sin bono, que es un pago anual aparte).
    out["recurring_income_monthly"] = (np.nan_to_num(out["salary_base_annual"]) / 12
                                       + np.nan_to_num(out["pension_monthly"])
                                       + np.nan_to_num(out["dividend_annual"]) / 12
                                       + np.nan_to_num(out["business_distribution_annual"]) / 12).round(2)
    return out
