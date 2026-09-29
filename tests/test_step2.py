import copy
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from synthetic.balances import build_step1
from synthetic.population import build_population
from synthetic.recurring import build_step2, detect
from synthetic.seeds import SeedManager
from synthetic.validate_step2 import check_step2

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "params.yaml").read_text())


def _build(cfg):
    s = SeedManager(cfg["master_seed"])
    base, truth = build_population(cfg, s)
    f1, sim1 = build_step1(base, truth, cfg, s)
    f2, sim2 = build_step2(base, truth, sim1, cfg, s)
    return base, truth, f1, sim1, f2, sim2


def test_step2_reproducible_and_leaves_previous_steps_untouched():
    b, t, f1, _, f2, _ = _build(CFG)
    s = SeedManager(CFG["master_seed"])
    b0, t0 = build_population(CFG, s)
    f1_only, _ = build_step1(b0, t0, CFG, s)
    pd.testing.assert_frame_equal(b, b0)
    pd.testing.assert_frame_equal(f1, f1_only)
    pd.testing.assert_frame_equal(f2, _build(CFG)[4])


def test_detect_regular_and_irregular_patterns():
    d = np.array([[-140.0, -126, -112, -98, -84, -70, -56], [-140.0, -130, -60, -58, -20, np.nan, np.nan]])
    a = np.full(d.shape, 1000.0)
    ex, interval, _ = detect(d, a, 0, 180, 0.25, 3)
    assert ex.tolist() == [True, False] and interval[0] == 14


def test_bonus_is_excluded_from_regularity():
    d = np.array([[-150.0, -120, -90, -85, -60, -30]])
    a = np.array([[1000.0, 1000, 1000, 9000, 1000, 1000]])  # bono en −85
    assert not detect(d, a, 0, 180, 0.25, 3)[0][0]
    assert detect(d, a, 0, 180, 0.25, 3, bonus_multiple=2.0)[0][0]


def test_step2_validation_passes_on_production_seed():
    base, truth, f1, sim1, f2, sim2 = _build(CFG)
    res, _, _ = check_step2(f2, sim2, sim1, f1, base, truth, CFG)
    assert res["ok"].all(), res.loc[~res["ok"], ["prueba", "detalle"]].to_string()


def test_changing_move_slope_leaves_noise_events():
    cfg2 = copy.deepcopy(CFG)
    cfg2["step2"]["move_slope"] += 1.0
    e1 = _build(CFG)[5]["events"]
    e2 = _build(cfg2)[5]["events"]
    for c in ["job_change", "retire", "leave", "business_sale", "partial"]:
        pd.testing.assert_series_equal(e1[c], e2[c])
    assert not e1["move"].equals(e2["move"])
