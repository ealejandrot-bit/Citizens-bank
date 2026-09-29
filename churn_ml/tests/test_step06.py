"""QC del paso 6: base + Σ puntos = score, tramos H-3, salida completa con M1 al lado."""
import json
import pickle

import numpy as np
import pandas as pd

from common import FACTOR, INH, MODEL, OFFSET, PROC, SCORES, TABLES

O = pd.read_csv(SCORES / "household_scores_ml.csv")
K = pickle.load(open(MODEL / "step06_scaling.pkl", "rb"))


def test_suma_puntos():
    E = pickle.load(open(MODEL / "step04_ebm.pkl", "rb"))
    V = json.loads((PROC / "step02_selected.json").read_text(encoding="utf-8"))["vars"]
    F = pd.read_parquet(INH / "features.parquet").set_index("household_id").loc[O.household_id]
    pts = np.round(-FACTOR * K["b"] * E.eval_terms(F[V])).astype(int)
    assert (K["base"] + pts.sum(1) == O.score_ebm.to_numpy()).all()
    assert np.allclose(1 / (1 + np.exp((O.score_ebm - OFFSET) / FACTOR)), O.p_ebm_calibrada)


def test_tramos_h3():
    c = pd.read_csv(TABLES / "step06_tramos_comparison.csv")
    for m in ("EBM (modelo)", "EBM (final, con overrides)", "XGBoost (modelo)"):
        t = c[c.modelo == m]
        r = t["tasa %"].to_numpy()
        assert r[0] >= 2 * r[1] and r[1] >= 2 * r[2] and r[2] >= 1.5 * r[3] and r[0] >= 5 * r[3], m
        assert (t.eventos >= K["min_ev_dev"]).all() and abs(t["% hogares"].sum() - 100) < 1e-9


def test_salida():
    assert len(O) == 20000 and O.household_id.is_unique
    assert O[["score_ebm", "tramo_ebm", "score_xgb", "tramo_xgb", "tramo_m1"]].notna().all().all()


def test_lookup_compacto():
    lk = pd.read_csv(TABLES / "step06_lookup.csv")
    lc = pd.read_csv(TABLES / "step06_lookup_compact.csv")
    for v, t in lk.groupby("variable"):
        c = lc[lc.variable == v]
        assert c["bins EBM unidos"].sum() == len(t)
        assert set(c.puntos) == set(t.puntos)
