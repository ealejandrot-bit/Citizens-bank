"""QC del paso 9: bins completos, ≥ 30 eventos por bin con dato, monotonía, especiales neutrales, IV sin sospechosas."""
import pickle

import numpy as np
import pandas as pd
import pytest

from common import COMPOSITES, MODEL, TABLES, candidates, load_split

W = pd.read_csv(TABLES / "step09_woe_iv.csv")
S = pd.read_csv(TABLES / "step09_iv_summary.csv")


@pytest.fixture(scope="module")
def dev_B():
    d = load_split("dev")
    return d[d.in_pop_B]


def test_cobertura():
    exp = {c for c in candidates() if c not in COMPOSITES} | {"cluster"}
    assert set(S.variable) == exp and set(W.variable) == exp
    assert not set(S.variable) & set(COMPOSITES + ["age_primary", "bureau_new_mortgage_elsewhere"])


def test_bins_suman(dev_B):
    n, ev = len(dev_B), int(dev_B.y_B.sum())
    g = W.groupby("variable").agg(h=("hogares", "sum"), e=("eventos", "sum"), p=("% hogares", "sum"))
    assert (g.h == n).all() and (g.e == ev).all()
    assert np.allclose(g.p, 100.0)


def test_eventos_minimos():
    assert (W.loc[~W.especial, "eventos"] >= 30).all()


def test_especiales_neutrales():
    e = W[W.especial]
    g = e.groupby(["variable", "bin"]).eventos.sum()
    small = g[g < 30].index
    assert (e.set_index(["variable", "bin"]).loc[small, "WoE"] == 0).all() if len(small) else True


def test_monotonia_y_iv():
    assert (S.tendencia != "NO MONÓTONA").all()
    assert (S.IV <= 0.50).all()
    assert (S.clase == pd.cut(S.IV, [-np.inf, 0.02, 0.10, 0.30, 0.50, np.inf], right=False,
                              labels=["fuera", "débil", "medio", "fuerte", "SOSPECHOSO"]).astype(str)).all()


def test_iv_recalculado():
    for v, t in W.groupby("variable"):
        assert abs(t.IV.sum() - S.set_index("variable").loc[v, "IV"]) < 1e-9


def test_pickle_reproduce_woe(dev_B):
    B = pickle.load(open(MODEL / "step09_binning.pkl", "rb"))
    d = dev_B.reset_index(drop=True)
    for c in ["transfer_to_competitor_pct_90d", "aum_vs_baseline_pct", "products_closed_180d"]:
        r = d[f"{c}__miss"] if f"{c}__miss" in d else None
        t = B[c].table(d[c], r, d.y_B.astype(int))
        ref = W[W.variable == c].reset_index(drop=True)
        assert np.allclose(t.WoE.to_numpy(), ref.WoE.to_numpy())
