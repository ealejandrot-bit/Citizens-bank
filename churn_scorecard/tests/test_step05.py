"""QC del paso 5: derivadas, razones de missing, peer-relative con celdas ≥ 100, sin prohibidas."""
import numpy as np
import pandas as pd
import pytest

from common import PROC, TABLES


@pytest.fixture(scope="module")
def F():
    return pd.read_parquet(PROC / "features.parquet")


def test_filas(F):
    assert len(F) == 20_000 and F.household_id.is_unique


def test_derivadas(F):
    assert np.allclose(F.log_rv, np.log10(F.relationship_value))
    assert np.allclose(F.aum_share + F.deposit_share, 1.0, atol=1e-6)          # RV = AUM + depósitos (G0-a)
    assert F.streams_stopped_count.between(0, 4).all() and F.n_products_held.between(0, 8).all()
    assert (F.loc[~F.has_investments, "outflow_x_contact_gap"] == 0).all()


def test_missing(F):
    assert (F.pension_deposit_stopped_flag.notna() & ~F.has_pension_stream).sum() == 0
    for c in [c for c in F.columns if c.endswith("__miss")]:
        base = c[:-6]
        assert F[c].isin(["ok", "no_aplica", "sin_dato"]).all()
        assert ((F[c] == "ok") == F[base].notna()).all() or base.endswith("_peer"), c
    assert (F.loc[~F.has_investments, "aum__miss"] == "no_aplica").all()


def test_peer():
    p = pd.read_csv(TABLES / "step05_peer_cells.csv")
    assert (p["hogares dev"] >= 100).all()
