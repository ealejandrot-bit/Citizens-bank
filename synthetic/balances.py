"""Paso 1 · Balances & AUM.

1) Simula por hogar una serie mensual de 24 meses de depósitos y AUM, anclada al
   Paso 0 en t (mes 0) y construida hacia atrás, con:
   * ruido de fondo t(ν) estandarizado (ν = 6, decisiones D-11);
   * rendimiento de mercado común a todos + beta del portafolio (permite AUM ex-mercado);
   * aportes y retiros de fondo tipo hurdle;
   * episodios de salida de dinero (SEÑAL, P depende de z_outflow);
   * choques de liquidez ajenos al riesgo (RUIDO: impuestos, compra de casa);
   * traslado de saldos por la mudanza del banco principal (evento común, D-17).
2) Calcula las variables 1, 2, 17 y 18 con la lógica del Excel sobre esas series.

Aproximación: el Excel define ventanas en días sobre saldos diarios; aquí se usan
promedios mensuales (30d = 1 mes, 90d = 3, 180d = 6; línea base = meses −6..−1).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import special

from .seeds import SeedManager


def std_t(rng: np.random.Generator, nu: float, size) -> np.ndarray:
    """t-Student con varianza 1 (se divide por √(ν/(ν−2)))."""
    return rng.standard_t(nu, size) / np.sqrt(nu / (nu - 2))


def simulate_series(base: pd.DataFrame, truth: pd.DataFrame, cfg: dict, seeds: SeedManager,
                    exit_ev: pd.DataFrame) -> dict:
    s1 = cfg["step1"]
    nu = cfg["distributions"]["t_df"]
    n, M = len(base), s1["months"]
    inv = base["has_investments"].to_numpy()
    z_out = truth["z_outflow"].to_numpy()

    # --- Episodio de salida (señal) ------------------------------------------
    p_ep = special.expit(s1["episode_intercept"] + s1["episode_slope"] * z_out)
    episode = seeds.rng("s1.episode").random(n) < p_ep
    ep_len = seeds.rng("s1.episode_len").integers(1, s1["episode_max_months"] + 1, n)
    delta = seeds.rng("s1.episode_delta").lognormal(np.log(s1["episode_delta_median"]), s1["episode_delta_sigma"], n)
    k_dep = seeds.rng("s1.episode_k_dep").uniform(*s1["episode_channel_range_deposit"], n)
    k_aum = seeds.rng("s1.episode_k_aum").uniform(*s1["episode_channel_range_aum"], n)
    j = np.arange(M)
    in_ep = episode[:, None] & (j[None, :] >= M - ep_len[:, None])  # meses del episodio (hasta t)

    # --- Choque de liquidez (ruido, independiente de z) --------------------------
    shock = seeds.rng("s1.shock").random(n) < s1["shock_p_12m"]
    shock_month = seeds.rng("s1.shock_month").integers(M - 12, M, n)
    shock_size = np.minimum(seeds.rng("s1.shock_size").lognormal(
        np.log(s1["shock_size_median"]), s1["shock_size_sigma"], n), 0.9)
    shock_aum = shock & (seeds.rng("s1.shock_aum").random(n) < s1["shock_hits_aum_p"])
    is_shock = shock[:, None] & (j[None, :] == shock_month[:, None])

    # --- Depósitos: incrementos log y reconstrucción hacia atrás desde el mes 0 -----
    noise_dep = std_t(seeds.rng("s1.deposit_noise"), nu, (n, M))
    e = s1["deposit_drift_monthly"] + s1["deposit_sigma_monthly"] * noise_dep
    e -= np.where(in_ep, (delta * k_dep)[:, None], 0.0)
    e += np.where(is_shock, np.log1p(-shock_size)[:, None], 0.0)
    # Mudanza del banco principal (evento común, D-17): traslado de saldo en el mes del evento.
    # Convención de meses del Excel: el mes m ≤ 0 cubre (30.44·(m−1), 30.44·m]; el mes 0 = últimos 30 días.
    # Tramos mensuales iguales en log: Π(1 − s_t) = 1 − share.
    move_m = M - 1 + exit_ev["move_month"].to_numpy()
    k_tr = exit_ev["deposit_tranches"].to_numpy()
    dep_share = exit_ev["deposit_transfer_share"].fillna(0).to_numpy()
    is_move_dep = exit_ev["deposit_transfer"].to_numpy()[:, None] & (j[None, :] >= move_m[:, None]) & \
        (j[None, :] < (move_m + k_tr)[:, None])
    e += np.where(is_move_dep, (np.log1p(-dep_share) / np.maximum(k_tr, 1))[:, None], 0.0)
    e[:, 0] = 0.0  # el incremento j es el cambio de j−1 a j
    after = np.cumsum(e[:, ::-1], axis=1)[:, ::-1] - e  # Σ_{k>j} e_k
    deposit = base["deposit_balance"].to_numpy()[:, None] * np.exp(-after)

    # --- AUM: mercado + flujos, hacia atrás desde el mes 0 --------------------------
    mkt = s1["market_mu_monthly"] + s1["market_sigma_monthly"] * std_t(seeds.rng("s1.market"), nu, M)
    lo_e, hi_e = s1["equity_share_range"]
    beta = seeds.rng("s1.equity_share").uniform(lo_e, hi_e, n)
    idio = s1["idio_return_sigma"] * seeds.rng("s1.idio_return").standard_normal((n, M))
    ret = beta[:, None] * mkt[None, :] + (1 - beta[:, None]) * s1["non_equity_return_monthly"] + idio
    ret[:, 0] = 0.0

    def hurdle(name, p, median):
        occurs = seeds.rng(f"{name}.occurs").random((n, M)) < p
        size = seeds.rng(f"{name}.size").lognormal(np.log(median), s1["flow_sigma"], (n, M))
        return np.where(occurs, size, 0.0)

    c = hurdle("s1.contribution", s1["contribution_p"], s1["contribution_median"])
    w = hurdle("s1.withdrawal", s1["withdrawal_p"], s1["withdrawal_median"])
    w += np.where(in_ep, 1 - np.exp(-(delta * k_aum)[:, None]), 0.0)
    w += np.where(is_shock & shock_aum[:, None], shock_size[:, None], 0.0)
    acats_m = M - 1 + np.ceil(exit_ev["acats_day"].fillna(0).to_numpy() / 30.44).astype(int)
    aum_share = exit_ev["aum_transfer_share"].fillna(0).to_numpy()
    is_acats = exit_ev["aum_transfer"].to_numpy()[:, None] & (j[None, :] == acats_m[:, None])
    w += np.where(is_acats, aum_share[:, None], 0.0)
    w = np.minimum(w, 0.9)
    c[:, 0] = w[:, 0] = 0.0
    c[~inv] = w[~inv] = 0.0

    aum = np.zeros((n, M))
    aum[:, -1] = base["aum"].fillna(0).to_numpy()
    for jj in range(M - 1, 0, -1):  # A_{j−1} = A_j / ((1 + R_j)(1 + c_j − w_j))
        aum[:, jj - 1] = aum[:, jj] / ((1 + ret[:, jj]) * (1 + c[:, jj] - w[:, jj]))
    prev = np.concatenate([aum[:, :1], aum[:, :-1]], axis=1)
    contrib_usd, withdraw_usd = c * prev, w * prev
    twr = np.cumprod(1 + ret, axis=1)  # índice base 1 en el mes −23

    # Meses anteriores a la apertura de la relación: no hay dato.
    hist = np.maximum(base["history_months"].to_numpy(), 1)
    avail = j[None, :] >= M - hist[:, None]
    return {"deposit": deposit, "aum": aum, "contrib": contrib_usd, "withdraw": withdraw_usd,
            "twr": twr, "avail": avail, "inv": inv,
            "episode_k_dep": k_dep, "episode_k_aum": k_aum, "shock_aum": shock_aum,
            "truth": pd.DataFrame({"household_id": base["household_id"], "s1_p_episode": p_ep,
                                   "s1_episode": episode, "s1_episode_len": np.where(episode, ep_len, 0),
                                   "s1_episode_delta": np.where(episode, delta, np.nan),
                                   "s1_shock": shock, "s1_shock_month": np.where(shock, shock_month - (M - 1), np.nan),
                                   "s1_shock_size": np.where(shock, shock_size, np.nan),
                                   "s1_equity_share": beta})}


def _window_mean(x, avail, start, end):
    """Media de las columnas [start, end) si todos esos meses existen; si no, NaN."""
    ok = avail[:, start:end].all(axis=1)
    return np.where(ok, x[:, start:end].mean(axis=1), np.nan)


def compute_variables(sim: dict, cfg: dict) -> pd.DataFrame:
    s1 = cfg["step1"]
    M, floor = s1["months"], s1["min_balance_for_pct"]
    D, A, av, inv = sim["deposit"], sim["aum"], sim["avail"], sim["inv"]
    out = {}

    # 1 · aum_outflow (30d, 90d): max(0, Σ retiros − Σ aportes); % sobre AUM promedio de la ventana.
    for k, lab in [(1, "30d"), (3, "90d")]:
        ok = av[:, M - k:].all(axis=1) & inv
        net = sim["withdraw"][:, M - k:].sum(axis=1) - sim["contrib"][:, M - k:].sum(axis=1)
        amt = np.maximum(net, 0.0)
        avg = A[:, M - k:].mean(axis=1)
        out[f"aum_outflow_{lab}"] = np.where(ok, np.round(amt, 2), np.nan)
        out[f"aum_outflow_pct_{lab}"] = np.where(ok & (avg > 0), amt / np.where(avg > 0, avg, 1), np.nan)

    # 2 · deposit_balance_change_pct (30d, 90d, 180d): media últimos k ÷ media k previos − 1.
    for k, lab in [(1, "30d"), (3, "90d"), (6, "180d")]:
        cur = _window_mean(D, av, M - k, M)
        pri = _window_mean(D, av, M - 2 * k, M - k)
        out[f"deposit_balance_change_pct_{lab}"] = np.where(pri >= floor, cur / pri - 1, np.nan)

    # 17 · aum_vs_baseline_pct: AUMx_t ÷ media(AUMx, meses −6..−1) − 1, AUMx = AUM ÷ índice TWR.
    ax = A / sim["twr"]
    basex = _window_mean(ax, av, M - 7, M - 1)
    safe = np.where(basex > 0, basex, 1.0)
    out["aum_vs_baseline_pct"] = np.where(inv & (basex > 0), ax[:, -1] / safe - 1, np.nan)

    # 18 · deposit_balance_vs_6m_avg_pct: media último mes ÷ media meses −6..−1 − 1.
    bd = _window_mean(D, av, M - 7, M - 1)
    out["deposit_balance_vs_6m_avg_pct"] = np.where(bd >= floor, D[:, -1] / bd - 1, np.nan)
    return pd.DataFrame(out)


def build_step1(base, truth, cfg, seeds, exit_ev):
    sim = simulate_series(base, truth, cfg, seeds, exit_ev)
    feats = compute_variables(sim, cfg)
    feats.insert(0, "household_id", base["household_id"].to_numpy())
    return feats, sim
