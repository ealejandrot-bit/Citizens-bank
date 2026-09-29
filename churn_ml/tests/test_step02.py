"""QC del paso 2: selección estable, 12–30 variables, regla de variante aplicada, sin prohibidas."""
import json

import pandas as pd

from common import COMPOSITES, PROC, TABLES


def test_seleccion():
    s = json.loads((PROC / "step02_selected.json").read_text(encoding="utf-8"))
    assert 12 <= len(s["vars"]) <= 30
    assert not set(s["vars"]) & {"age_primary", "bureau_new_mortgage_elsewhere", "hard_churn_6m", "soft_churn_3m", "value_lost_6m"}
    pi = pd.read_csv(TABLES / "step02_permutation.csv")
    p = pi[pi.variante == s["variant"]].set_index("variable")
    assert (p.loc[s["vars"], "% folds > 0"] >= 80).all()
    if s["variant"] == "sin compuestos":
        assert not set(s["vars"]) & set(COMPOSITES)


def test_regla_variante():
    v = pd.read_csv(TABLES / "step02_variants.csv").set_index("variante")
    diff = v.loc["con compuestos", "PR-AUC CV media"] - v.loc["sin compuestos", "PR-AUC CV media"]
    exp = "sin compuestos" if diff < v.loc["con compuestos", "sd folds"] else "con compuestos"
    assert v[v.elegida.astype(bool)].index[0] == exp


def test_backward_1se():
    b = pd.read_csv(TABLES / "step02_backward.csv")
    acc = b[(b.paso > 0) & b.acepta.astype(bool)]
    assert (acc["Δ vs actual"] >= -acc["1-SE"] - 1e-12).all()
