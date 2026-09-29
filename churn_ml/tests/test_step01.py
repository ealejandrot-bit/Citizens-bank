"""QC del paso 1: pool sin fuga, sin constantes, un representante por grupo de duplicados."""
import pandas as pd

from common import PROC, TABLES


def test_pool():
    t = pd.read_csv(TABLES / "step01_screen.csv")
    p = pd.read_csv(PROC / "step01_pool.csv")
    assert set(p.variable) == set(t[t.pasa].variable)
    assert not t[t.pasa][["f1 casi constante", "f2 fuga", "f3 duplicado |ρ| > 0.95"]].any().any()
    assert "cluster" in set(p.variable)


def test_duplicados():
    d = pd.read_csv(TABLES / "step01_duplicate_pairs.csv")
    assert (d["Spearman con la que queda"].abs() > 0.95).all()
    assert not set(d["se queda"]) & set(d.sale)
