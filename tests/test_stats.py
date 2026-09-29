import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import stats_step0  # noqa: E402
from synthetic.stats_tests import bh_adjust, mardia  # noqa: E402


def test_quick_statistical_suite_passes():
    df, _ = stats_step0.run(quick=True)
    failed = df.loc[~df["ok"], "prueba"].tolist()
    assert not failed, failed


def test_mardia_fast_identity_matches_brute_force():
    x = np.random.default_rng(0).standard_normal((800, 3))
    xc = x - x.mean(0)
    d = xc @ np.linalg.inv(np.cov(xc, rowvar=False, bias=True)) @ xc.T
    assert np.isclose(mardia(x)[0], len(x) * np.mean(d**3) / 6)


def test_bh_adjust_monotone_and_bounded():
    p = np.array([0.001, 0.02, 0.03, 0.5, 0.9])
    adj = bh_adjust(p)
    assert np.all(adj >= p) and np.all(adj <= 1) and np.all(np.diff(adj[np.argsort(p)]) >= 0)
