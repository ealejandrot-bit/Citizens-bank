"""QC del paso 4: split estratificado, sin solapes, balance de tasas y folds completos."""
import pandas as pd
import pytest

from common import PROC


@pytest.fixture(scope="module")
def dv():
    return pd.read_parquet(PROC / "dev.parquet"), pd.read_parquet(PROC / "val.parquet")


def test_particion(dv):
    dev, val = dv
    assert len(dev) + len(val) == 19_473
    assert not set(dev.household_id) & set(val.household_id)
    assert abs(len(val) / 19_473 - 0.30) < 0.001


def test_balance(dv):
    dev, val = dv
    for t in ("A", "B"):
        m_d, m_v = dev[dev[f"in_pop_{t}"]], val[val[f"in_pop_{t}"]]
        assert abs(100 * m_d[f"y_{t}"].mean() - 100 * m_v[f"y_{t}"].mean()) <= 0.5
    assert abs(100 * (dev.segment == "UHNW").mean() - 100 * (val.segment == "UHNW").mean()) <= 0.5
    assert dev.y_B.sum() + val.y_B.sum() == 2_674 and dev.y_A.sum() + val.y_A.sum() == 1_168
    assert dev.y_B_indet.sum() + val.y_B_indet.sum() == 212


def test_folds(dv):
    dev, _ = dv
    for r in range(1, 6):
        c = dev[f"cv_r{r}"]
        assert c.between(0, 4).all() and c.nunique() == 5
