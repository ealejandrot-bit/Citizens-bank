"""QC del paso 1: target, exclusiones, pesos y churn rate."""
import numpy as np
import pandas as pd
import pytest

from common import PROC, TABLES, load_raw, loss_ratio


@pytest.fixture(scope="module")
def pop():
    return pd.read_parquet(PROC / "step01_population.parquet")


def test_poblaciones(pop):
    assert len(pop) == 20_000 and pop.household_id.is_unique
    assert pop.in_pop_A.sum() == 19_473 and pop.in_pop_B.sum() == 19_261 and pop.y_B_indet.sum() == 212
    assert (pop.excl_reason == "churn_excluded").sum() == 123 and (pop.excl_reason == "tenure_lt_1").sum() == 404
    assert not (pop.in_pop_B & pop.y_B_indet).any()                       # indeterminados fuera del modelado
    assert (pop.in_pop_B | pop.y_B_indet) .sum() == pop.in_pop_A.sum()    # B + indeterminados = población A


def test_targets(pop):
    df = load_raw()
    r = loss_ratio(df)
    assert pop.y_A.sum() == 1_168 and pop.y_B.sum() == 2_674
    hard, soft = df.hard_churn_6m == 1, df.soft_churn_3m == 1
    b = pop.y_B == 1
    assert (b == (pop.in_pop_B & (hard | (soft & (r >= 0.25))))).all()
    assert ((pop.y_A == 1) <= (pop.y_B == 1) | ~pop.in_pop_B).all()      # todo hard es evento B
    assert pop.loc[pop.y_B_indet, "household_id"].isin(df.loc[soft & (r < 0.25), "household_id"]).all()


def test_pesos(pop):
    for t in ("A", "B"):
        m = pop[f"in_pop_{t}"]
        y, w = pop.loc[m, f"y_{t}"], pop.loc[m, f"w_{t}"]
        assert np.isclose(w[y == 1].sum(), w[y == 0].sum())               # muestra ponderada balanceada
        assert np.isclose(w.sum(), m.sum())                               # los pesos preservan N
        assert pop.loc[~m, f"w_{t}"].isna().all()


def test_exclusiones_acumuladas():
    e = pd.read_csv(TABLES / "step01_exclusions.csv")
    assert (e.hogares.iloc[:-1].to_numpy() - e.salen.iloc[1:].to_numpy() == e.hogares.iloc[1:].to_numpy()).all()
    assert e.hogares.iloc[-1] == 19_261


def test_theta():
    t = pd.read_csv(TABLES / "step01_theta_sensitivity.csv")
    assert (t.eventos == t["de ellos hard"] + t["de ellos soft ≥ θ"]).all()
    el = t[t.población == "elegibles"].set_index("θ")
    assert el.loc[0.20, "eventos"] == 2_956 and el.loc[0.25, "eventos"] == 2_740 and el.loc[0.25, "indeterminados (soft < θ)"] == 216


def test_churn_rate_mezcla():
    c = pd.read_csv(TABLES / "step01_churn_rates.csv")
    for t in ("A", "B"):
        x = c[c.target == t].set_index("segmento")
        mix = (x.loc[["HNW", "UHNW"], "hogares"] / x.loc["Total", "hogares"] * x.loc[["HNW", "UHNW"], "churn hogares %"]).sum()
        assert abs(mix - x.loc["Total", "churn hogares %"]) < 1e-9
        assert x.loc["HNW", "eventos"] + x.loc["UHNW", "eventos"] == x.loc["Total", "eventos"]
