"""QC del paso 4: aditividad exacta, monotonía sin violaciones, reason codes medidos."""
import pandas as pd

from common import TABLES

T = lambda n: pd.read_csv(TABLES / f"{n}.csv")  # noqa: E731


def test_aditividad():
    d = T("step04_diagnostics").set_index("modelo")
    assert d.loc["EBM", "error máx. aditividad"] < 1e-6 and d.loc["XGBoost", "error máx. aditividad"] < 1e-3
    assert d.loc["EBM", "% interacción global"] == 0


def test_monotonia():
    m = T("step04_monotonicity")
    for c in ["violaciones en f(x) EBM", "ICE EBM", "PDP EBM", "ICE XGBoost", "PDP XGBoost"]:
        assert (m[c].fillna(0) == 0).all(), c


def test_importancia_y_reason_codes():
    i = T("step04_importance")
    assert abs(i["% EBM"].sum() - 100) < 1e-6 and abs(i["% XGBoost"].sum() - 100) < 1e-6
    r = T("step04_reason_stability")
    assert set(r.modelo) == {"EBM", "XGBoost"} and (r["réplicas"] == 200).all()
