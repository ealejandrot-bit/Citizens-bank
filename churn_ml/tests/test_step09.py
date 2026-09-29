"""QC del paso 9: holdout completo y pareado, métricas consistentes, tabla H-2 completa para EBM y XGBoost."""
import pandas as pd

from common import TABLES

T = lambda n: pd.read_csv(TABLES / f"{n}.csv")  # noqa: E731


def test_global_pareado():
    g = T("step09_global")
    v = g[g.muestra == "val"]
    assert set(v.modelo) == {"EBM", "XGBoost", "M1"} and v["tasa %"].nunique() == 1
    m1 = v.set_index("modelo").loc["M1"]
    assert round(m1.Gini, 3) == 0.390 and round(m1["PR-AUC"], 3) == 0.328      # igual a la validación de M1 (paso 13)


def test_h2_y_tramos():
    h = T("step09_h2")
    assert (h.groupby("modelo").size() == 8).all() and h.cumple.isin(["sí", "no"]).all()
    t = T("step09_tramos_val")
    for m, s in t.groupby("modelo"):
        assert abs(s["% val"].sum() - 100) < 1e-9
    assert (T("step09_psi")["PSI dev→val por tramo"] < 0.10).all()


def test_gains():
    gn = T("step09_gains_ebm")
    assert abs(gn["captura acumulada %"].iloc[-1] - 100) < 1e-9
