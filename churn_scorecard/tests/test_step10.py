"""QC del paso 10: campeón 6–10 variables no redundantes con signo correcto; challenger 15–30 sin fuga."""
import pickle

import pandas as pd

from common import COMPOSITES, EXCLUDED_G13, MODEL, TABLES

S = pickle.load(open(MODEL / "step10_selection.pkl", "rb"))
F = pd.read_csv(TABLES / "step10_champion_vars.csv")
VC = pd.read_csv(TABLES / "step10_varclus.csv")
CH = pd.read_csv(TABLES / "step10_challenger_prescreen.csv")


def test_campeon_tamano_y_exclusiones():
    v = S["champion"]
    assert 6 <= len(v) <= 10 and list(F.variable) == v
    assert not set(v) & set(COMPOSITES + EXCLUDED_G13 + ["cluster"])


def test_campeon_no_redundante():
    assert (F["VIF (WoE)"] < 5).all()
    assert F.cluster.is_unique
    assert (VC.groupby("cluster")["2º autovalor del cluster"].first() <= 1.0).all()


def test_campeon_signo_e_iv():
    iv = pd.read_csv(TABLES / "step09_iv_summary.csv").set_index("variable")
    assert (F.IV >= 0.02).all() and F["signo esperado"].isin(["+", "−"]).all()
    trend = {"+": "ascendente", "−": "descendente"}
    assert all(iv.loc[r.variable, "tendencia"] == trend[r["signo esperado"]] for _, r in F.iterrows())


def test_campeon_diversidad():
    assert F["dimensión"].nunique() >= 3


def test_adicion_cumple_regla():
    fw = pd.read_csv(TABLES / "step10_forward.csv")
    e = fw[fw.entra.astype(bool)]
    assert list(e.variable) == S["champion"]
    assert (e["% folds ΔGini > 0"] >= 80).all() and (e["VIF máx"] < 5).all() and e["signos β correctos"].astype(bool).all()


def test_challenger():
    v = S["challenger"]
    assert 15 <= len(v) <= 30
    assert not set(v) & set(EXCLUDED_G13)
    p = CH[CH.pasa.astype(bool)]
    assert set(p.variable) == set(v)
    assert (p["% folds > 0"] >= 80).all() and not p["f2 fuga"].astype(bool).any() and not p["f1 casi constante"].astype(bool).any()
    assert not p["f3 redundante (|ρ| > 0.75)"].astype(bool).any()
