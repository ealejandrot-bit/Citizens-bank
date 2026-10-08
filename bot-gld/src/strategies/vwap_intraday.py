"""Estrategia 2 — VWAP intradía (barras de 5 min, horario regular).

Decisión al cierre de cada barra t (solo datos del día hasta t); el motor ejecuta en la apertura de t+1.
- Entrada: la barra t cierra arriba del VWAP del día y la barra t−1 (mismo día) cerró abajo.
- Sin operaciones los primeros 30 min: la primera ejecución posible es en la barra de 10:00.
- Salida: la barra cierra abajo del VWAP, o cierre forzado: la decisión de la barra que termina a
  las 15:55 es salir, así que la venta ocurre en la apertura de la barra de 15:55 ET.
- Las dos últimas barras de cada día siempre deciden efectivo (cubre días de cierre anticipado),
  por lo que nunca queda posición de un día para otro.
- Máximo de entradas por día: `max_operaciones_dia`.
"""
from __future__ import annotations

from datetime import time

import numpy as np
import pandas as pd


def _minutes(t: time | str) -> int:
    if isinstance(t, str):
        h, m = t.split(":")
        return int(h) * 60 + int(m)
    return t.hour * 60 + t.minute


def session_vwap(bars: pd.DataFrame) -> pd.Series:
    """VWAP acumulado del día con precio típico (h+l+c)/3; en t usa solo barras ≤ t."""
    tp = (bars["high"] + bars["low"] + bars["close"]) / 3.0
    day = _day_key(bars.index)
    pv = (tp * bars["volume"]).groupby(day).cumsum()
    v = bars["volume"].groupby(day).cumsum()
    return (pv / v.replace(0, np.nan)).rename("vwap")


def _day_key(index: pd.DatetimeIndex) -> np.ndarray:
    return np.asarray(index.date)


def targets(
    bars: pd.DataFrame,
    sin_operar_hasta: str = "10:00",
    cierre_forzado: str = "15:55",
    max_operaciones_dia: int = 2,
    bar_minutes: int = 5,
) -> pd.Series:
    vwap = session_vwap(bars).to_numpy()
    close = bars["close"].to_numpy(dtype=float)
    mins = np.array([t.hour * 60 + t.minute for t in bars.index])
    days = _day_key(bars.index)
    first_exec = _minutes(sin_operar_hasta)
    exit_exec = _minutes(cierre_forzado)
    out = np.zeros(len(bars))

    # Límites de cada día (índices posicionales)
    starts = np.flatnonzero(np.r_[True, days[1:] != days[:-1]])
    ends = np.r_[starts[1:], len(bars)]
    for s, e in zip(starts, ends):
        pos = 0.0
        n_trades = 0
        last_decision = e - 3  # las dos últimas barras del día siempre deciden efectivo
        for i in range(s, e):
            exec_min = mins[i] + bar_minutes  # minuto en que se ejecutaría la decisión (apertura t+1)
            forced_flat = i > last_decision or exec_min >= exit_exec
            if pos > 0:
                if forced_flat or close[i] < vwap[i]:
                    pos = 0.0
            elif (
                not forced_flat
                and i > s
                and exec_min >= first_exec
                and n_trades < max_operaciones_dia
                and close[i] > vwap[i]
                and close[i - 1] < vwap[i - 1]
            ):
                pos = 1.0
                n_trades += 1
            out[i] = pos
    return pd.Series(out, index=bars.index, name="vwap_intraday")
