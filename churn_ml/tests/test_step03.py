"""QC del paso 3: 150 trials por algoritmo, espacio del SPEC, CV completa, regla de elección aplicada."""
import pickle

import pandas as pd

from common import MODEL, TABLES


def test_optuna():
    t = pd.read_csv(TABLES / "step03_optuna_trials.csv")
    assert (t.groupby("algoritmo").size() == 150).all()
    b = pd.read_csv(TABLES / "step03_best_params.csv")
    assert b["param max_depth"].isin([2, 3]).all() and b["param min_child_weight"].between(5, 50).all()
    assert b["param learning_rate"].between(0.01, 0.1).all()


def test_cv_y_eleccion():
    c = pd.read_csv(TABLES / "step03_cv_folds.csv")
    assert (c.groupby(["algoritmo", "semilla"]).size() == 25).all()
    s = pd.read_csv(TABLES / "step03_algorithms.csv").sort_values("PR-AUC media", ascending=False).reset_index(drop=True)
    ch = pickle.load(open(MODEL / "step03_choice.pkl", "rb"))["algo"]
    if s.loc[0, "PR-AUC media"] - s.loc[1, "PR-AUC media"] <= s.loc[0, "PR-AUC sd"]:
        assert ch == s.sort_values("complejidad (árboles × prof.)").algoritmo.iloc[0]
    else:
        assert ch == s.algoritmo.iloc[0]
