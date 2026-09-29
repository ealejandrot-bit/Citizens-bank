"""Invariantes del scorecard (escala de puntos, WoE, calibración, estabilidad) sobre datos pequeños."""
import numpy as np
import pandas as pd
from scipy import special

from synthetic import scorecard as sc


def _toy(n=4000, seed=0):
    rng = np.random.default_rng(seed)
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    x2[rng.random(n) < 0.1] = np.nan
    lin = -1.6 + 0.9 * x1 + 0.6 * np.nan_to_num(x2, nan=0.8)
    y = (rng.random(n) < special.expit(lin)).astype(int)
    return pd.DataFrame({"a": x1, "b": x2}), y


def test_scaling_constants():
    assert np.isclose(sc.FACTOR, 40 / np.log(2))
    assert np.isclose(sc.OFFSET + sc.FACTOR * np.log(20), 600)


def test_woe_sign_and_monotone():
    X, y = _toy()
    b = sc.Binner("a", X["a"], y, trend="ascending")
    t = b.table[b.table["code"] >= 0]
    assert b.is_monotone()
    # más riesgo (tasa creciente) → WoE = ln(%buenos/%malos) decreciente
    assert np.all(np.diff(t["WoE"].to_numpy()) < 0)
    assert b.iv > 0.1


def test_points_sum_to_score_and_probability():
    X, y = _toy()
    bins = {c: sc.Binner(c, X[c], y, trend="ascending") for c in X}
    W = pd.DataFrame({c: bins[c].woe(X[c]) for c in X})
    import statsmodels.api as sm
    f = sm.Logit(1 - y, sm.add_constant(W)).fit(disp=0)
    card = sc.Scorecard(bins, f.params[list(X)], float(f.params["const"]))
    assert (card.beta > 0).all()
    lo = card.ln_odds_good(X)
    assert np.allclose(card.score(X), sc.OFFSET + sc.FACTOR * lo)
    assert np.allclose(card.p_churn(X), 1 / (1 + np.exp(lo)))
    rc = card.reason_codes(X.head(50))
    assert (rc["driver_1_pts"] <= rc["driver_2_pts"]).all() or (rc["driver_2_pts"] == 0).any()


def test_wilson_and_psi():
    lo, hi = sc.wilson(30, 100)
    assert lo < 0.30 < hi
    assert sc.psi([1, 2, 3] * 100, [1, 2, 3] * 100) < 1e-9
    assert sc.psi([1] * 90 + [2] * 10, [1] * 50 + [2] * 50) > 0.25
