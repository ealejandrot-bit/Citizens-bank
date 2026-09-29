from pathlib import Path

import pandas as pd
import pytest
import yaml

from synthetic.pipeline import build
from synthetic.validate_step7 import check_step7

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "params.yaml").read_text())


@pytest.fixture(scope="module")
def built():
    return build(CFG, upto=7)


def test_step7_leaves_previous_steps_untouched(built):
    o6 = build(CFG, upto=6)
    for k in ["base", "f1", "f2", "f3", "f4", "f5", "f6"]:
        pd.testing.assert_frame_equal(built[k], o6[k])


def test_step7_validation_passes(built):
    o = built
    prev = [o[f"f{k}"][list(CFG[f"step{k}"]["targets"])] for k in range(1, 7)]
    res, _, _ = check_step7(o["f7"], o["sim7"], o["base"], o["truth"], o["exit"], prev, CFG)
    assert res["ok"].all(), res.loc[~res["ok"], ["prueba", "detalle"]].to_string()
