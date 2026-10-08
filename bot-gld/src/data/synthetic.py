"""Datos sintéticos para pruebas y demo del reporte. NO representan a GLD."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.data.loader import TZ


def daily_bars(
    n: int = 1000,
    start: str = "2015-01-01",
    price0: float = 100.0,
    drift: float = 0.0,
    vol: float = 0.0,
    seed: int = 0,
) -> pd.DataFrame:
    """Barras diarias en días hábiles. drift/vol son log-rendimientos diarios."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range(start, periods=n, name="date")
    r = drift + vol * rng.standard_normal(n)
    close = price0 * np.exp(np.cumsum(r))
    gap = vol * 0.3 * rng.standard_normal(n)
    open_ = np.r_[price0, close[:-1]] * np.exp(gap)
    hi = np.maximum(open_, close) * (1 + abs(vol) * 0.5)
    lo = np.minimum(open_, close) * (1 - abs(vol) * 0.5)
    return pd.DataFrame(
        {"open": open_, "high": hi, "low": lo, "close": close, "volume": 1_000_000.0}, index=idx
    )


def intraday_bars(
    n_days: int = 20,
    start: str = "2024-01-02",
    price0: float = 200.0,
    vol: float = 0.0015,
    seed: int = 0,
) -> pd.DataFrame:
    """Barras de 5 min, 9:30–15:55 ET (78 por día), caminata aleatoria con reversión leve."""
    rng = np.random.default_rng(seed)
    days = pd.bdate_range(start, periods=n_days)
    frames = []
    price = price0
    for d in days:
        idx = pd.date_range(d + pd.Timedelta(hours=9, minutes=30), periods=78, freq="5min", tz=TZ)
        r = vol * rng.standard_normal(78)
        close = price * np.exp(np.cumsum(r))
        open_ = np.r_[price * np.exp(vol * rng.standard_normal()), close[:-1]]
        hi = np.maximum(open_, close) * (1 + vol / 2)
        lo = np.minimum(open_, close) * (1 - vol / 2)
        volm = rng.integers(5_000, 50_000, 78).astype(float)
        frames.append(pd.DataFrame({"open": open_, "high": hi, "low": lo, "close": close, "volume": volm}, index=idx))
        price = close[-1]
    out = pd.concat(frames)
    out.index.name = "date"
    return out
