"""Evento de salida común a los Pasos 1+: mudanza del banco principal (decisiones D-14, D-17).

Se sortea una sola vez por hogar y se pasa a cada paso, para que el mismo evento se vea
de forma coherente en saldos (Paso 1), ingresos recurrentes (Paso 2) y transferencias
(Paso 3). Depende de la propensión total a irse (índice de riesgo del Paso 0), no del target.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import special

from .seeds import SeedManager


def draw_exit_move(base: pd.DataFrame, truth: pd.DataFrame, cfg: dict, seeds: SeedManager) -> pd.DataFrame:
    em = cfg["exit_move"]
    n = len(base)
    p_move = special.expit(em["move_intercept"] + em["move_slope"] * truth["risk_index"].to_numpy())
    # Nombres "s2.*" conservados: el Paso 2 ya generado no cambia.
    move = seeds.rng("s2.move").random(n) < p_move
    day = np.floor(seeds.rng("s2.move_day").uniform(-em["move_window_days"], 0, n))
    inv = base["has_investments"].to_numpy()
    dep_t = move & (seeds.rng("exit.deposit_transfer").random(n) < em["deposit_transfer_p"])
    dep_share = seeds.rng("exit.deposit_share").uniform(*em["deposit_transfer_share"], n)
    aum_t = move & inv & (seeds.rng("exit.aum_transfer").random(n) < em["aum_transfer_p"])
    aum_share = seeds.rng("exit.aum_share").uniform(*em["aum_transfer_share"], n)
    lag = np.floor(seeds.rng("exit.acats_lag").uniform(*em["acats_lag_days"], n))
    # Traslado por tramos mensuales consecutivos desde el mes de la mudanza, sin pasar de t.
    lo, hi = em["deposit_tranches"]
    k = seeds.rng("exit.deposit_tranches").integers(lo, hi + 1, n)
    move_month = np.ceil(day / 30.44).astype(int)  # mes 0 = últimos 30 días
    k_eff = np.minimum(k, 1 - move_month)
    return pd.DataFrame({
        "household_id": base["household_id"].to_numpy(),
        "p_move": p_move, "move": move, "move_day": np.where(move, day, np.nan),
        "deposit_transfer": dep_t, "deposit_transfer_share": np.where(dep_t, dep_share, np.nan),
        "move_month": np.where(move, move_month, 0), "deposit_tranches": np.where(dep_t, k_eff, 0),
        "aum_transfer": aum_t, "aum_transfer_share": np.where(aum_t, aum_share, np.nan),
        "acats_day": np.where(aum_t, np.minimum(day + lag, 0), np.nan),
    })
