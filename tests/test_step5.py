from pathlib import Path

import pandas as pd
import pytest
import yaml

from synthetic.pipeline import build
from synthetic.validate_step5 import check_step5

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "params.yaml").read_text())


@pytest.fixture(scope="module")
def built():
    return build(CFG, upto=5)


def test_step5_leaves_previous_steps_untouched(built):
    o4 = build(CFG, upto=4)
    for k in ["base", "f1", "f2", "f3", "f4"]:
        pd.testing.assert_frame_equal(built[k], o4[k])


def test_step5_validation_passes(built):
    o = built
    prev = [o[f"f{k}"][list(CFG[f"step{k}"]["targets"])] for k in (1, 2, 3, 4)]
    res, _, _ = check_step5(o["f5"], o["sim5"], o["base"], o["truth"], o["exit"], prev, CFG)
    assert res["ok"].all(), res.loc[~res["ok"], ["prueba", "detalle"]].to_string()
