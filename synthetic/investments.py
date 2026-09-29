"""Paso 4 · Investments (variables 9, 26, 27, 28, 34).

Se apoya en las series del Paso 1 (AUM, aportes, retiros, rendimientos con alpha) y en las
transferencias del Paso 3 (qué salió en especie por ACATS). Lo nuevo cambia la COMPOSICIÓN del
portafolio, no los dólares que entran o salen del AUM:
  * SEÑAL factor: venta a cash sin reinvertir (z_outflow), paso previo a transferir;
  * SEÑAL propensión: liquidación de fondos propietarios antes del ACATS de la mudanza;
  * RUIDO: de-risking recomendado por el banker, rebalanceos del asesor (excluidos), venta completa
    ocasional de una posición, RMD de diciembre (excluida), vencimientos de renta fija con
    reinversión normal;
  * rendimiento vs benchmark con el alpha del Paso 1 (D-19) y un benchmark por perfil.
Meses: el mes m ≤ 0 cubre (30.44·(m−1), 30.44·m]; ventanas de 90 días = meses −2..0.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import special

from .seeds import SeedManager

AVG_MONTH = 30.44


def month_of(day):
    return np.ceil(np.asarray(day, dtype=float) / AVG_MONTH).astype(int)


def simulate_portfolio(base, truth, cfg, seeds: SeedManager, exit_ev, sim1, sim3) -> dict:
    s4, s1 = cfg["step4"], cfg["step1"]
    n, M = len(base), s1["months"]
    A, inv = sim1["aum"], sim1["inv"]
    t1 = sim1["truth"]
    z_out = truth["z_outflow"].to_numpy()

    def rng(name):
        return seeds.rng(name)

    def A_at(i, m):
        return A[i, M - 1 + m]

    ev = pd.DataFrame({"household_id": base["household_id"].to_numpy()})
    # --- Venta a cash (señal factor) ---------------------------------------------------
    p_liq = special.expit(s4["liquidation_intercept"] + s4["liquidation_slope"] * z_out)
    liq = inv & (rng("s4.liquidation").random(n) < p_liq)
    liq_day = np.floor(rng("s4.liquidation_day").uniform(-s4["liquidation_window_days"], 0, n))
    liq_share = rng("s4.liquidation_share").uniform(*s4["liquidation_share"], n)
    full_share = rng("s4.liquidation_full").beta(*s4["liquidation_full_position_share_beta"], n)
    liq_amt = np.where(liq, liq_share * A_at(np.arange(n), month_of(liq_day)), 0.0)
    # --- Fondos propietarios antes del ACATS (señal propensión) ----------------------
    acats = exit_ev["aum_transfer"].to_numpy()
    has_prop = acats & (rng("s4.has_proprietary").random(n) < s4["proprietary_p"])
    acats_day = exit_ev["acats_day"].fillna(0).to_numpy()
    lead = np.floor(rng("s4.proprietary_lead").uniform(*s4["proprietary_sale_lead_days"], n))
    prop_day = np.maximum(acats_day - lead, -540)
    prop_share = rng("s4.proprietary_share").uniform(*s4["proprietary_share"], n)
    prop_amt = np.where(has_prop, prop_share * A_at(np.arange(n), month_of(prop_day) - 1), 0.0)
    # --- Ruido --------------------------------------------------------------------------
    derisk = inv & (rng("s4.derisk").random(n) < s4["advisor_derisk_p"])
    derisk_day = np.floor(rng("s4.derisk_day").uniform(-180, 0, n))
    derisk_pp = rng("s4.derisk_pp").uniform(*s4["advisor_derisk_pp"], n)
    fsale = inv & (rng("s4.client_full_sale").random(n) < s4["client_full_sale_p_90d"])
    fsale_day = np.floor(rng("s4.client_full_sale_day").uniform(-90, 0, n))
    fsale_amt = np.where(fsale, rng("s4.client_full_sale_share").uniform(*s4["client_full_sale_share"], n)
                         * A_at(np.arange(n), month_of(fsale_day)), 0.0)
    reb = inv[:, None] & (rng("s4.rebalance").random((n, M)) < s4["rebalance_p_month"])
    reb_amt = np.where(reb, rng("s4.rebalance_share").uniform(*s4["rebalance_share"], (n, M)) * A, 0.0)

    # --- Renta fija: vencimiento y reinversión ------------------------------------------
    fi_share = 1 - t1["s1_equity_share"].to_numpy()
    mat = inv & (rng("s4.maturity").random(n) < s4["maturity_p_90d_given_fi"])
    mat_day = np.floor(rng("s4.maturity_day").uniform(-90, 0, n))
    mat_amt = np.where(mat, rng("s4.maturity_share").uniform(*s4["maturity_share_of_fi"], n) * fi_share
                       * A_at(np.arange(n), month_of(mat_day)), 0.0)
    leaving = liq | exit_ev["move"].to_numpy()
    u = rng("s4.reinvest").random(n)
    partial = rng("s4.reinvest_partial").beta(*s4["reinvest_partial_beta"], n)
    ratio = np.where(leaving & (u < s4["nonreinvest_liquidation_p"]), 0.0,
                     np.where(u < s4["reinvest_full_p"], 1.0, partial))
    reinv_lag = np.floor(rng("s4.reinvest_lag").uniform(1, 30, n))
    reinv_day = mat_day + reinv_lag
    reinv_amt = np.where(mat & (reinv_day <= 0), ratio * mat_amt, 0.0)  # si cae después de t, aún no ocurrió

    # --- Retiros que se financian vendiendo (no ACATS) y RMD ----------------------------
    tx = sim3["tx"]
    acats_tx = tx[tx["category"].isin({"episode_acats", "move_acats"})]
    acats_m = np.zeros((n, M))
    g = acats_tx.groupby(["hh", "month"])["amount"].sum()
    acats_m[g.index.get_level_values(0), M - 1 + g.index.get_level_values(1)] = g.to_numpy()
    sell_for_withdrawal = np.maximum(sim1["withdraw"] - acats_m, 0.0)
    rmd = np.zeros((n, M))
    dec = M - 1  # t = 31-dic: el mes 0 contiene diciembre
    old = base["age_primary"].to_numpy() >= s4["rmd_age"]
    rmd[:, dec] = np.where(old & inv, np.minimum(sell_for_withdrawal[:, dec], s4["rmd_rate"] * A[:, dec - 1]), 0.0)

    # --- Cash % mensual -----------------------------------------------------------------
    j = np.arange(M)
    m_idx = j - (M - 1)
    base_cash = sim3["cash_share"]
    noise = s4["cash_noise_pp_monthly"] * rng("s4.cash_noise").standard_normal((n, M))
    safeA = np.where(A > 0, A, 1.0)
    liq_m, prop_m, der_m, mat_m, fs_m = (month_of(x) for x in (liq_day, prop_day, derisk_day, mat_day, fsale_day))
    acats_mm = month_of(acats_day)
    add = np.zeros((n, M))
    add += np.where(liq[:, None] & (m_idx[None, :] >= liq_m[:, None]), (liq_amt[:, None] / safeA), 0.0)
    add += np.where(has_prop[:, None] & (m_idx[None, :] >= month_of(prop_day)[:, None]) & (m_idx[None, :] < acats_mm[:, None]),
                    prop_amt[:, None] / safeA, 0.0)
    add += np.where(derisk[:, None] & (m_idx[None, :] >= der_m[:, None]), derisk_pp[:, None], 0.0)
    add += np.where(mat[:, None] & (m_idx[None, :] >= mat_m[:, None]), ((1 - ratio) * mat_amt)[:, None] / safeA, 0.0)
    add += np.where(fsale[:, None] & (m_idx[None, :] >= fs_m[:, None]), fsale_amt[:, None] / safeA, 0.0)
    cash_pct = np.clip(base_cash[:, None] + noise + add, 0.0, 0.95)

    for c, v in dict(p_liquidation=p_liq, liquidation=liq, liquidation_day=np.where(liq, liq_day, np.nan),
                     liquidation_amount=liq_amt, proprietary_sale=has_prop, proprietary_amount=prop_amt,
                     advisor_derisk=derisk, client_full_sale=fsale, maturity=mat,
                     maturity_amount=mat_amt, reinvest_ratio=np.where(mat, ratio, np.nan)).items():
        ev[c] = v
    return {"events": ev, "cash_pct": cash_pct, "rebalance": reb_amt, "sell_for_withdrawal": sell_for_withdrawal,
            "rmd": rmd, "days": dict(liq=liq_day, prop=prop_day, fsale=fsale_day, mat=mat_day, reinv=reinv_day),
            "amounts": dict(liq=liq_amt, prop=prop_amt, fsale=fsale_amt, mat=mat_amt, reinv=reinv_amt),
            "full_share": full_share}


def compute_variables(sim4, sim1, base, cfg) -> pd.DataFrame:
    s4 = cfg["step4"]
    n, M = len(base), cfg["step1"]["months"]
    A, inv, av = sim1["aum"], sim1["inv"], sim1["avail"]
    hist = base["history_months"].to_numpy()
    d, a = sim4["days"], sim4["amounts"]
    out = pd.DataFrame({"household_id": base["household_id"].to_numpy()})
    in90 = {k: v > -90 for k, v in d.items()}
    ok3 = inv & av[:, M - 3:].all(axis=1)
    avgA90 = A[:, M - 3:].mean(axis=1)

    # #9 ventas y redenciones del cliente − compras, 90d (sin rebalanceos del asesor ni RMD).
    sales = (sim4["sell_for_withdrawal"][:, M - 3:] - sim4["rmd"][:, M - 3:]).sum(axis=1)
    sales += sum(np.where(in90[k], a[k], 0.0) for k in ("liq", "prop", "fsale", "mat"))
    purchases = sim1["contrib"][:, M - 3:].sum(axis=1) + np.where(in90["reinv"], a["reinv"], 0.0)
    net = np.maximum(sales - purchases, 0.0)
    out["investment_redemption_pct"] = np.where(ok3 & (avgA90 > 0), net / np.where(avgA90 > 0, avgA90, 1), np.nan)

    # #26 principal vencido no reinvertido en 30 días ÷ principal vencido (vencimientos en 90d).
    has_mat = a["mat"] > 0
    out["fixed_income_maturity_not_reinvested"] = np.where(inv & has_mat, 1 - a["reinv"] / np.where(has_mat, a["mat"], 1), np.nan)
    out["fixed_income_not_reinvested_amount"] = np.where(inv & has_mat, np.round(a["mat"] - a["reinv"], 2), np.nan)

    # #27 cash % en t − promedio de cash % en los meses −6..−1 (puntos porcentuales como fracción).
    c = sim4["cash_pct"]
    ok7 = inv & av[:, M - 7:].all(axis=1)
    out["cash_pct_of_portfolio_chg"] = np.where(ok7, c[:, -1] - c[:, M - 7:M - 1].mean(axis=1), np.nan)

    # #28 rendimiento TWR del portafolio (neto, con alpha) − benchmark por perfil, 12 meses.
    ret = sim1["returns"][:, M - 12:]
    beta = sim1["truth"]["s1_equity_share"].to_numpy()
    beta_b = np.clip(beta + s4["benchmark_tilt_sigma"] * sim4["benchmark_noise"], 0.2, 1.0)
    rb = beta_b[:, None] * sim1["market"][None, M - 12:] + (1 - beta_b[:, None]) * cfg["step1"]["non_equity_return_monthly"]
    port = np.prod(1 + ret, axis=1) - 1
    bench = np.prod(1 + rb, axis=1) - 1
    ok12 = base["has_advisory"].to_numpy() & (hist >= 12)
    out["return_vs_benchmark"] = np.where(ok12, port - bench, np.nan)

    # #34 valor de posiciones vendidas completas y no reemplazadas (90d) ÷ valor del portafolio hace 90 días.
    full = np.where(in90["liq"], a["liq"] * sim4["full_share"], 0.0) + np.where(in90["prop"], a["prop"], 0.0) \
        + np.where(in90["fsale"], a["fsale"], 0.0)
    A_start = A[:, M - 4]
    out["positions_liquidated_pct"] = np.where(inv & av[:, M - 4:].all(axis=1) & (A_start > 0),
                                               full / np.where(A_start > 0, A_start, 1), np.nan)
    return out


def build_step4(base, truth, cfg, seeds, exit_ev, sim1, sim3):
    sim4 = simulate_portfolio(base, truth, cfg, seeds, exit_ev, sim1, sim3)
    sim4["benchmark_noise"] = seeds.rng("s4.benchmark_tilt").standard_normal(len(base))
    return compute_variables(sim4, sim1, base, cfg), sim4
