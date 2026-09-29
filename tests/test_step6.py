from pathlib import Path

import pandas as pd
import pytest
import yaml

from synthetic.pipeline import build
from synthetic.validate_step6 import check_step6

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "params.yaml").read_text())


@pytest.fixture(scope="module")
def built():
    return build(CFG, upto=6)


def test_step6_leaves_previous_steps_untouched(built):
    o5 = build(CFG, upto=5)
    for k in ["base", "f1", "f2", "f3", "f4", "f5"]:
        pd.testing.assert_frame_equal(built[k], o5[k])


def test_step6_validation_passes(built):
    o = built
    prev = [o[f"f{k}"][list(CFG[f"step{k}"]["targets"])] for k in range(1, 6)]
    res, _, _ = check_step6(o["f6"], o["sim6"], o["base"], o["truth"], o["exit"], prev, CFG)
    assert res["ok"].all(), res.loc[~res["ok"], ["prueba", "detalle"]].to_string()
