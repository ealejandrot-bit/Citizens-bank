"""QC del paso 15: PSI dev→val < 0.10 en score, probabilidad, tramo y variables; contribuciones completas."""
import pandas as pd

from common import TABLES

T = lambda n: pd.read_csv(TABLES / f"{n}.csv")  # noqa: E731


def test_psi_global():
    p = T("step15_psi")
    assert len(p) == 3 + 8 and (p.PSI < 0.10).all() and (p.PSI >= 0).all()


def test_psi_subgrupos():
    s = T("step15_psi_subgroups")
    assert set(s.subgrupo) == {"segmento", "quintil RV", "banda antigüedad", "historia < 24m", "cluster"}
    assert (s[["PSI score", "PSI tramo"]] < 0.25).all().all()
    assert (T("step15_psi_mix")["PSI de la mezcla dev→val"] < 0.10).all()


def test_contribuciones():
    d = T("step15_contribution_drift")
    assert abs(d["participación media %"].sum() - 100) < 1e-6 and (d["mín %"] > 0).all()
