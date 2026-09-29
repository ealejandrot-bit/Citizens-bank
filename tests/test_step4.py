from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from synthetic.pipeline import build
from synthetic.validate_step4 import check_step4

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "params.yaml").read_text())


@pytest.fixture(scope="module")
def built():
    return build(CFG, upto=4)


def test_step4_leaves_previous_steps_untouched(built):
    o3 = build(CFG, upto=3)
    for k in ["base", "f1", "f2", "f3"]:
        pd.testing.assert_frame_equal(built[k], o3[k])


def test_return_matches_twr_index(built):
    s1 = built["sim1"]
    np.testing.assert_allclose(np.prod(1 + s1["returns"][:, -12:], axis=1) - 1, s1["twr"][:, -1] / s1["twr"][:, -13] - 1)


def test_step4_validation_passes(built):
    o = built
    prev = [o["f1"][list(CFG["step1"]["targets"])], o["f2"][list(CFG["step2"]["targets"])],
            o["f3"][list(CFG["step3"]["targets"])]]
    res, _, _ = check_step4(o["f4"], o["sim4"], o["sim1"], o["base"], o["truth"], o["exit"], prev, CFG)
    assert res["ok"].all(), res.loc[~res["ok"], ["prueba", "detalle"]].to_string()
