"""Construcción de la variable de churn sobre la ventana de resultado (t, t+6m].

El Paso 0 decide QUIÉN sale (hard) o se contrae (soft), a partir de la propensión. Aquí se
simulan los saldos y el AUM de los 6 meses siguientes y la etiqueta se CONSTRUYE sobre lo
observado, con las definiciones del deck:
  * hard churn 6m: el valor de la relación cae a ≤ 5% del valor en t y no se recupera;
  * soft churn 3m: caída del valor ex-mercado > 20% en 3 meses, sin salida total;
  * logo churn = clientes que salen ÷ activos; AUM churn = valor perdido ÷ valor inicial.
Hay ruido realista: un retiro grande (compra de casa) puede cruzar el umbral de soft churn sin
serlo, y una contracción pequeña con ruido puede no cruzarlo.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .balances import std_t
from .seeds import SeedManager


def simulate_outcome(base, truth, cfg, seeds: SeedManager, sim1) -> dict:
    oc, s1 = cfg["outcome"], cfg["step1"]
    nu = cfg["distributions"]["t_df"]
    n, K = len(base), oc["months"]
    D0 = base["deposit_balance"].to_numpy()
    A0 = base["aum"].fillna(0).to_numpy()
    inv = base["has_investments"].to_numpy()
    hard = base["hard_churn_6m"].fillna(0).astype(int).to_numpy().astype(bool)
    soft = base["soft_churn_3m"].fillna(0).astype(int).to_numpy().astype(bool)
    excl = base["churn_excluded"].to_numpy()
    loss = np.where(soft, base["value_lost_6m"].fillna(0).to_numpy() / base["relationship_value"].to_numpy(), 0.0)

    mkt = s1["market_mu_monthly"] + s1["market_sigma_monthly"] * std_t(seeds.rng("out.market"), nu, K)
    beta = sim1["truth"]["s1_equity_share"].to_numpy()
    ret = beta[:, None] * mkt[None, :] + (1 - beta[:, None]) * s1["non_equity_return_monthly"] \
        + s1["idio_return_sigma"] * seeds.rng("out.idio").standard_normal((n, K)) + sim1["alpha"][:, None] / 12
    e_dep = s1["deposit_drift_monthly"] + oc["deposit_sigma_monthly"] * std_t(seeds.rng("out.deposit_noise"), nu, (n, K))
    f_aum = oc["aum_net_flow_sigma_monthly"] * seeds.rng("out.aum_flow").standard_normal((n, K))
    r = seeds.rng("out.shock")
    shock = r.random((n, K)) < oc["liquidity_shock_p_month"]
    shock_size = np.minimum(r.lognormal(np.log(oc["liquidity_shock_size_median"]), oc["liquidity_shock_size_sigma"], (n, K)), 0.9)
    exit_m = seeds.rng("out.exit_month").integers(1, K + 1, n)
    resid = seeds.rng("out.residual").uniform(*oc["hard_churn_residual_share"], n)
    contr_m = seeds.rng("out.contraction_month").integers(1, oc["soft_churn_window_months"] + 1, n)

    D = np.zeros((n, K + 1))
    A = np.zeros((n, K + 1))
    D[:, 0], A[:, 0] = D0, A0
    twr = np.ones((n, K + 1))
    for k in range(1, K + 1):
        d = D[:, k - 1] * np.exp(e_dep[:, k - 1])
        a = np.where(inv, A[:, k - 1] * (1 + ret[:, k - 1]) * (1 + f_aum[:, k - 1]), 0.0)
        twr[:, k] = twr[:, k - 1] * (1 + ret[:, k - 1])
        s = shock[:, k - 1]
        d = np.where(s, d * (1 - shock_size[:, k - 1]), d)
        c = soft & (contr_m == k)                      # contracción: se va una fracción de la relación
        d, a = np.where(c, d * (1 - loss), d), np.where(c, a * (1 - loss), a)
        x = hard & (exit_m == k)                        # salida total: queda un residual
        d, a = np.where(x, D0 * resid, d), np.where(x, A0 * resid, a)
        after = hard & (exit_m < k)
        d, a = np.where(after, D[:, k - 1], d), np.where(after, A[:, k - 1], a)
        D[:, k], A[:, k] = d, a
    return {"deposit": D, "aum": A, "twr": twr, "market": mkt, "exit_month": np.where(hard, exit_m, 0),
            "contraction_month": np.where(soft, contr_m, 0), "shock": shock, "excluded": excl,
            "hard_latent": hard, "soft_latent": soft}


def construct_churn(sim_o, base, cfg) -> pd.DataFrame:
    oc = cfg["outcome"]
    D, A, twr = sim_o["deposit"], sim_o["aum"], sim_o["twr"]
    V = D + A
    V0 = V[:, 0]
    hard = (V[:, 1:] / V0[:, None]).min(axis=1) <= oc["hard_churn_max_share"]
    hard &= V[:, -1] / V0 <= oc["hard_churn_max_share"]
    W = oc["soft_churn_window_months"]
    Vx = D[:, :W + 1] + A[:, :W + 1] / twr[:, :W + 1]  # ex-mercado
    soft = ~hard & ((Vx[:, 1:] / Vx[:, :1]).min(axis=1) - 1 <= -oc["soft_churn_threshold"])
    excl = sim_o["excluded"]
    lost_hard = np.where(hard, V0 - V[:, -1], 0.0)
    lost_soft = np.where(soft, np.maximum(Vx[:, 0] - Vx[:, 1:].min(axis=1), 0.0), 0.0)

    def lab(x):
        return pd.array(np.where(excl, pd.NA, x.astype(int)), dtype="Int8")

    return pd.DataFrame({
        "household_id": base["household_id"].to_numpy(),
        "churn_hard_6m": lab(hard), "churn_soft_3m": lab(soft), "churn_any": lab(hard | soft),
        "churn_value_lost": np.where(excl, np.nan, np.round(lost_hard + lost_soft, 2)),
        "relationship_value_t": np.round(V0, 2), "relationship_value_t6": np.round(V[:, -1], 2),
        "churn_exit_month": np.where(hard & ~excl, np.argmax(V[:, 1:] / V0[:, None] <= oc["hard_churn_max_share"], axis=1) + 1, 0),
    })
