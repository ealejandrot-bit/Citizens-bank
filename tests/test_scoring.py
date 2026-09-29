from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from synthetic import scoring as sc
from synthetic.outcome import construct_churn, simulate_outcome
from synthetic.pipeline import build

CFG = yaml.safe_load((Path(__file__).resolve().parents[1] / "config" / "params.yaml").read_text())


def test_constructed_churn_matches_events():
    o = build(CFG, upto=1)
    lab = construct_churn(simulate_outcome(o["base"], o["truth"], CFG, o["seeds"], o["sim1"]), o["base"], CFG)
    el = ~o["base"]["churn_excluded"]
    assert (lab.loc[el, "churn_hard_6m"].astype(int) == o["base"].loc[el, "hard_churn_6m"].astype(int)).all()
    assert lab.loc[~el, "churn_hard_6m"].isna().all()
    assert ((lab["churn_hard_6m"].fillna(0) + lab["churn_soft_3m"].fillna(0)) <= 1).all()


def test_ks_and_topk_on_perfect_score():
    y = np.array([0, 0, 1, 1, 0, 1, 0, 0, 0, 0])
    assert sc.ks_stat(y, y.astype(float)) == 1.0
    t = sc.top_k(y, y.astype(float), np.ones(10) * y, 0.3)
    assert t["precisión"] == 1.0 and t["recall"] == 1.0


def test_expert_scorecard_capped_at_100():
    X = pd.DataFrame({c: [1.0] for c in ["relationship_dissatisfaction_flag", "recurring_deposit_stopped_flag",
                                          "banker_change_6m_flag"]})
    X["external_transfer_pct_of_balance_60d"] = 0.5
    X["recurring_deposit_change_pct"] = -0.9
    X["investment_redemption_pct"] = 0.5
    X["aum_outflow_pct_90d"] = 0.5
    X["complaint_age_days"] = 90
    X["contact_gap_ratio"] = 5
    assert sc.expert_scorecard(X)[0] == 100
