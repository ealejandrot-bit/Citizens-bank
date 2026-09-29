"""QC del paso 5: calibración sin holdout, Platt dentro de 0.8–1.2, media alineada, regla de método aplicada."""
import pandas as pd

from common import PROC, TABLES

T = lambda n: pd.read_csv(TABLES / f"{n}.csv")  # noqa: E731


def test_platt_y_regla():
    d = T("step05_platt")
    for _, r in d.iterrows():
        assert (r["método elegido"] == "isotónica") == (r["IC95 sup"] < 0)
        if r["método elegido"] == "Platt":
            assert 0.8 <= r.b <= 1.2


def test_oof_solo_dev():
    o = pd.read_parquet(PROC / "step05_oof.parquet")
    val = set(pd.read_parquet(PROC.parent / "inherited" / "val.parquet").household_id)
    assert not set(o.household_id) & val


def test_alineacion():
    m = T("step05_methods")
    p = m[m["método"].str.startswith("Platt")]
    assert ((p["media p %"] - p["tasa %"]).abs() < 0.5).all()
