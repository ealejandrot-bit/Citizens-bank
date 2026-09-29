"""Paso 8 · External & composite (variables 16, 37) y base final consolidada.

* #16 multi_signal: por grupo del Excel, ¿alguna variable supera su umbral de alerta (columna
  "Alert threshold")? Se cuentan los grupos activos (0–7) y el flag es ≥ 3.
* #37 buró: hipoteca / HELOC nueva con otro acreedor en 6 meses. Fuentes: mudanza (propensión),
  compra de casa del Paso 3 financiada fuera de Citizens, refinanciamiento (ruido). Requiere
  propósito permisible (FCRA) y aprobación legal (interruptor en config).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .seeds import SeedManager
from .validate_step3 import alert as alert3


def group_alerts(o: dict, cfg: dict) -> pd.DataFrame:
    """Alerta por variable (umbral del Excel) → alerta por grupo."""
    f1, f2, f3, f4, f5, f6, f7 = (o[f"f{k}"] for k in range(1, 8))
    mat = cfg["step8"]["material_not_reinvested_usd"]
    rules = {
        "Balances & AUM": [f1["aum_outflow_pct_90d"] > 0.10, f1["deposit_balance_change_pct_90d"] <= -0.25,
                           f1["aum_vs_baseline_pct"] <= -0.20, f1["deposit_balance_vs_6m_avg_pct"] <= -0.30],
        "Recurring deposits & flows": [f2["salary_deposit_stopped_flag"] == 1, f2["recurring_deposit_stopped_flag"] == 1,
                                       f2["recurring_deposit_change_pct"] <= -0.40, f2["net_deposit_flow_pct_90d"] <= -0.15,
                                       f2["pension_deposit_stopped_flag"] == 1, f2["business_payroll_stopped_flag"] == 1],
        "Transfers": [f3["external_transfer_pct_of_balance_60d"] > 0.15, f3["new_external_destinations_30d"] >= 1,
                      f3["transfer_to_competitor_pct_90d"] > 0.10, alert3(f3, "external_transfer_acceleration", "accel"),
                      f3["net_external_flow_pct_90d"] <= -0.15, alert3(f3, "external_destination_concentration", "hhi"),
                      f3["outflow_vs_baseline_pct"] > 1.0],
        "Investments": [f4["investment_redemption_pct"] > 0.20,
                        (f4["fixed_income_maturity_not_reinvested"] > 0.50) & (f4["fixed_income_not_reinvested_amount"] >= mat),
                        f4["cash_pct_of_portfolio_chg"] > 0.10, f4["return_vs_benchmark"] <= -0.03,
                        f4["positions_liquidated_pct"] > 0.15],
        "Relationship & closures": [f5["products_closed_90d"] >= 1, f5["accounts_closed_90d"] >= 1,
                                    f5["share_of_wallet"] < 0.30, f5["share_of_wallet_change"] <= -0.10,
                                    f5["trustee_change_flag"] == 1],
        "Banker": [f6["banker_change_6m_flag"] == 1, f6["contact_gap_ratio"] > 2.0, f6["client_reply_rate"] < 0.5,
                   (f6["meetings_cancelled_by_client"] >= 2) | (f6["meetings_cancelled_pct"] >= 0.5)],
        "Complaints & voice of client": [f7["complaint_escalated_flag"] == 1,
                                         (f7["complaint_age_days"] > 30) | (f7["complaint_out_of_sla_flag"] == 1),
                                         f7["repeat_complaint_flag"] == 1, f7["relationship_dissatisfaction_flag"] == 1],
    }
    out = pd.DataFrame(index=o["base"].index)
    for g, conds in rules.items():
        out[g] = np.logical_or.reduce([pd.Series(c).fillna(False).astype(bool).to_numpy() for c in conds])
    return out


def simulate_bureau(base, cfg, seeds: SeedManager, exit_ev, sim3) -> pd.DataFrame:
    s8 = cfg["step8"]
    n = len(base)
    r = seeds.rng("s8.bureau")
    anchor = base["has_credit_anchor"].to_numpy()
    move = exit_ev["move"].to_numpy() & (r.random(n) < s8["move_mortgage_elsewhere_p"])
    tx = sim3["tx"]
    buy = tx[(tx["category"] == "real_estate") & (tx["day"] > -180)]["hh"].unique()
    purchase = np.zeros(n, bool)
    purchase[buy] = True
    financed = purchase & (r.random(n) < s8["home_purchase_financed_p"])
    p_cit = np.where(anchor, s8["citizens_lender_p"]["anchor"], s8["citizens_lender_p"]["no_anchor"])
    with_citizens = financed & (r.random(n) < p_cit)
    refi = r.random(n) < s8["refinance_elsewhere_p_6m"]
    elsewhere = move | (financed & ~with_citizens) | refi
    pp = r.random(n) < s8["permissible_purpose_p"]
    return pd.DataFrame({"household_id": base["household_id"].to_numpy(), "mortgage_via_move": move,
                         "home_purchase_6m": purchase, "financed": financed, "financed_with_citizens": with_citizens,
                         "refinance_elsewhere": refi, "new_mortgage_elsewhere_true": elsewhere, "permissible_purpose": pp})


def build_step8(o: dict, cfg: dict, seeds: SeedManager):
    s8 = cfg["step8"]
    ga = group_alerts(o, cfg)
    bureau = simulate_bureau(o["base"], cfg, seeds, o["exit"], o["sim3"])
    out = pd.DataFrame({"household_id": o["base"]["household_id"].to_numpy()})
    out["multi_signal_count"] = ga.sum(axis=1).to_numpy().astype(int)
    out["multi_signal_flag"] = (out["multi_signal_count"] >= s8["multi_signal_min_groups"]).astype(int)
    for g in ga:
        out[f"group_alert_{g.split(' ')[0].lower()}"] = ga[g].astype(int).to_numpy()
    ok = bureau["permissible_purpose"].to_numpy() & s8["legal_cleared"]
    out["bureau_new_mortgage_elsewhere"] = pd.array(np.where(ok, bureau["new_mortgage_elsewhere_true"].astype(int), pd.NA),
                                                    dtype="Int8")
    return out, {"group_alerts": ga, "bureau": bureau}
