from pathlib import Path

import pandas as pd
import pytest
import yaml

from synthetic.pipeline import build
from synthetic.schema import EXCEL_PRIMARY

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "params.yaml").read_text())


@pytest.fixture(scope="module")
def built():
    return build(CFG, upto=8)


def test_step8_leaves_previous_steps_untouched(built):
    o7 = build(CFG, upto=7)
    for k in ["base", "f1", "f2", "f3", "f4", "f5", "f6", "f7"]:
        pd.testing.assert_frame_equal(built[k], o7[k])


def test_multi_signal_is_sum_of_group_alerts(built):
    ga = built["sim8"]["group_alerts"]
    assert (built["f8"]["multi_signal_count"] == ga.sum(axis=1).to_numpy()).all()
    assert (built["f8"]["multi_signal_flag"] == (built["f8"]["multi_signal_count"] >= 3).astype(int)).all()


def test_all_37_excel_variables_have_a_column(built):
    cols = set().union(*[built[f"f{k}"].columns for k in range(1, 9)])
    assert len(EXCEL_PRIMARY) == 37
    assert all(c in cols for _, c in EXCEL_PRIMARY.values())
