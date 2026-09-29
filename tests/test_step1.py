import copy
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from synthetic.balances import build_step1
from synthetic.population import build_population
from synthetic.seeds import SeedManager
from synthetic.validate_step1 import check_step1

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "params.yaml").read_text())


def _build(cfg):
    s = SeedManager(cfg["master_seed"])
    base, truth = build_population(cfg, s)
    feats, sim = build_step1(base, truth, cfg, s)
    return base, truth, feats, sim


def test_step1_reproducible_and_does_not_touch_step0():
    b1, t1, f1, _ = _build(CFG)
    b0, t0 = build_population(CFG, SeedManager(CFG["master_seed"]))  # Paso 0 solo
    pd.testing.assert_frame_equal(b1, b0)
    pd.testing.assert_frame_equal(t1, t0)
    _, _, f2, _ = _build(CFG)
    pd.testing.assert_frame_equal(f1, f2)


def test_step1_series_anchor_to_step0():
    base, _, _, sim = _build(CFG)
    np.testing.assert_allclose(sim["deposit"][:, -1], base["deposit_balance"])
    inv = sim["inv"]
    np.testing.assert_allclose(sim["aum"][inv, -1], base.loc[inv, "aum"])


def test_step1_validation_passes_on_production_seed():
    base, truth, feats, sim = _build(CFG)
    res, _, _ = check_step1(feats, sim, base, truth, CFG)
    assert res["ok"].all(), res.loc[~res["ok"], ["prueba", "detalle"]].to_string()


def test_changing_step1_params_leaves_other_streams():
    cfg2 = copy.deepcopy(CFG)
    cfg2["step1"]["episode_slope"] += 0.5
    _, _, f1, s1 = _build(CFG)
    _, _, f2, s2 = _build(cfg2)
    # La tasa de episodios cambia, pero el mercado y los choques de liquidez (flujos propios) no.
    np.testing.assert_array_equal(s1["twr"], s2["twr"])
    pd.testing.assert_series_equal(s1["truth"]["s1_shock"], s2["truth"]["s1_shock"])
    assert not s1["truth"]["s1_episode"].equals(s2["truth"]["s1_episode"])
