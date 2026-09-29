"""QC del paso 11: β > 0, intercepto corregido, CV completa, monotonía del challenger, SHAP aditivo, H-2 completa."""
import pickle

import numpy as np
import pandas as pd

from common import MODEL, PROC, TABLES

T = lambda n: pd.read_csv(TABLES / f"{n}.csv")  # noqa: E731


def test_campeon_signos_e_intercepto():
    c = T("step11A_coefficients")
    assert (c["β (muestra ponderada)"].iloc[1:] > 0).all() and (c["p-valor"].iloc[1:] < 0.05).all()
    assert (c["VIF (WoE)"].iloc[1:] < 5).all()
    ch = pickle.load(open(MODEL / "step11A_champion.pkl", "rb"))
    assert list(c.variable.iloc[1:]) == ch["vars"] == pickle.load(open(MODEL / "step10_selection.pkl", "rb"))["champion"]
    pop = pd.read_parquet(PROC / "step01_population.parquet")
    r = pop.loc[pop.in_pop_B, "y_B"].mean()
    assert abs(ch["ln_odds_good_pop"] - np.log((1 - r) / r)) < 1e-9


def test_campeon_cv():
    f = T("step11A_cv_folds")
    assert len(f) == 25 and f["β > 0 todos"].astype(bool).all()
    assert 0.8 <= f["pendiente calibración b"].mean() <= 1.2
    assert T("step11A_reason_stability")["acuerdo top 1 %"].iloc[0] >= 70


def test_challenger_cv_y_optuna():
    assert len(T("step11B_cv_folds_xgb")) == 25
    d = T("step11B_diagnostics").iloc[0]
    assert d["trials completos"] + d["trials podados"] == 150
    assert d["param max_depth"] in (2, 3) and d["error máx. aditividad SHAP"] < 1e-3
    assert len(T("step11B_seeds")) == 3


def test_challenger_monotonia():
    m = T("step11B_monotonicity")
    assert (m["violaciones ICE"].fillna(0) == 0).all() and (m["violaciones PDP"].fillna(0) == 0).all()


def test_comparacion():
    h = T("step11_h2_table")
    assert len(h) == 8 and h.cumple.isin(["sí", "no", "pendiente"]).all()
    assert len(T("step11_comparison")) == 8


def test_vista_ajuste_11C():
    m = T("step11C_calibration_metrics")
    d = T("step11C_calibration_deciles")
    assert len(m) == 5 and (d.groupby("modelo").decil.nunique() == 10).all()
    assert (d.groupby("modelo").hogares.sum() == d.hogares.sum() / 5).all()
    assert m["tasa observada %"].nunique() == 1
