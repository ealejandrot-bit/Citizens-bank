"""QC del paso 7: importancias estables, sin dependencia de una sola variable, subgrupos con ≥ 30 eventos."""
import pandas as pd

from common import TABLES

T = lambda n: pd.read_csv(TABLES / f"{n}.csv")  # noqa: E731


def test_estabilidad():
    s = T("step07_importance_stability")
    assert abs(s["participación media %"].sum() - 100) < 1e-6 and (s["CV %"] < 50).all()


def test_sin_dependencia_de_una_variable():
    d = T("step07_drop_top")
    full, drop = d["PR-AUC CV"].iloc[0], d["PR-AUC CV"].iloc[1]
    assert drop > 0.9 * full


def test_subgrupos():
    s = T("step07_subgroups")
    assert (s.eventos >= 30).all() and set(s.subgrupo) == {"segment", "quintil RV", "antigüedad", "historia < 24m", "cluster"}
