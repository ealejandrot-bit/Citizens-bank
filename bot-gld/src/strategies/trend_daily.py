"""Estrategia 1 — Tendencia diaria.

Señal al cierre del día t (solo datos hasta t): largo si close > SMA(200); si no, efectivo.
El motor la ejecuta en la apertura de t+1. Variante de control (no optimización): cruce 50/200.
"""
from __future__ import annotations

import pandas as pd


def sma(close: pd.Series, n: int) -> pd.Series:
    return close.rolling(n, min_periods=n).mean()


def signal_sma(bars: pd.DataFrame, n: int = 200) -> pd.Series:
    close = bars["close"]
    s = (close > sma(close, n)).astype(float)
    return s.rename(f"sma{n}")


def signal_cruce(bars: pd.DataFrame, rapida: int = 50, lenta: int = 200) -> pd.Series:
    close = bars["close"]
    s = (sma(close, rapida) > sma(close, lenta)).astype(float)  # NaN → False → efectivo
    return s.rename(f"cruce{rapida}_{lenta}")


def targets(bars: pd.DataFrame, params: dict) -> dict[str, pd.Series]:
    """Señales de la estrategia y su variante de control, con el nombre para el reporte."""
    n = int(params.get("sma", 200))
    r, l = int(params.get("control_rapida", 50)), int(params.get("control_lenta", 200))
    return {
        f"Close > SMA({n})": signal_sma(bars, n),
        f"Cruce {r}/{l} (control)": signal_cruce(bars, r, l),
    }
