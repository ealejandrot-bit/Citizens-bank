"""Interfaz única de datos para el backtest: lee/escribe parquet en data/.

Formato: índice `date` (diario: fecha sin zona; 5 min: hora de inicio de barra en America/New_York),
columnas open, high, low, close, volume.
"""
from __future__ import annotations

from datetime import time
from pathlib import Path

import pandas as pd

TZ = "America/New_York"
COLUMNS = ["open", "high", "low", "close", "volume"]
TIMEFRAMES = {"1d": "diario", "5m": "5 min"}


def bars_path(data_dir: str | Path, symbol: str, timeframe: str) -> Path:
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"timeframe inválido: {timeframe}")
    return Path(data_dir) / f"{symbol}_{timeframe}.parquet"


def save_bars(df: pd.DataFrame, data_dir: str | Path, symbol: str, timeframe: str) -> Path:
    path = bars_path(data_dir, symbol, timeframe)
    path.parent.mkdir(parents=True, exist_ok=True)
    validate(df, timeframe).to_parquet(path)
    return path


def load_bars(data_dir: str | Path, symbol: str, timeframe: str, rth_only: bool = True) -> pd.DataFrame:
    path = bars_path(data_dir, symbol, timeframe)
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}. Descarga primero con `python -m src.data.ibkr_source`.")
    df = validate(pd.read_parquet(path), timeframe)
    if timeframe == "5m" and rth_only:
        df = rth_filter(df)
    return df


def rth_filter(df: pd.DataFrame, start: time = time(9, 30), end: time = time(16, 0)) -> pd.DataFrame:
    """Solo barras que inician dentro del horario regular 9:30–16:00 ET."""
    t = df.index.time
    return df[(t >= start) & (t < end)]


def validate(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    missing = [c for c in COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas: {missing}")
    df = df[COLUMNS].astype(float).sort_index()
    df = df[~df.index.duplicated(keep="last")]
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.DatetimeIndex(df.index)
    if timeframe == "5m":
        df.index = df.index.tz_localize(TZ) if df.index.tz is None else df.index.tz_convert(TZ)
    elif df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    df.index.name = "date"
    return df
