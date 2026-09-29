import copy
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from synthetic.pipeline import build
from synthetic.transfers import aba_checksum
from synthetic.validate_step3 import check_step3

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "params.yaml").read_text())


@pytest.fixture(scope="module")
def built():
    return build(CFG, upto=3)


def test_step3_leaves_previous_steps_untouched(built):
    o2 = build(CFG, upto=2)
    for k in ["base", "f1", "f2"]:
        pd.testing.assert_frame_equal(built[k], o2[k])


def test_step3_reproducible(built):
    pd.testing.assert_frame_equal(built["f3"], build(CFG, upto=3)["f3"])


def test_aba_checksum_known_valid_numbers():
    # Ejemplos de dígito verificador: 3·(d1+d4+d7) + 7·(d2+d5+d8) + (d3+d6+d9) ≡ 0 (mod 10).
    d8 = np.array([[0, 1, 1, 0, 0, 0, 0, 1], [1, 2, 1, 0, 0, 0, 3, 5]])
    full = np.column_stack([d8, aba_checksum(d8)])
    w = np.array([3, 7, 1, 3, 7, 1, 3, 7, 1])
    assert ((full @ w) % 10 == 0).all()


def test_step3_validation_passes(built):
    o = built
    res, _, _ = check_step3(o["f3"], o["sim3"], o["sim1"], o["sim2"], o["f1"], o["f2"], o["base"], o["truth"],
                            o["exit"], CFG)
    assert res["ok"].all(), res.loc[~res["ok"], ["prueba", "detalle"]].to_string()


def test_pb_floor_is_a_parameter(built):
    cfg2 = copy.deepcopy(CFG)
    cfg2["step3"]["new_destination_min_cumulative"] = 10_000
    from synthetic.transfers import compute_variables
    f_ex = compute_variables(built["sim3"], built["sim1"], built["base"], cfg2)
    assert f_ex["new_external_destinations_90d"].sum() > built["f3"]["new_external_destinations_90d"].sum()
