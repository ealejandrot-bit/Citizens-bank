"""Descarga de históricos de GLD vía ib_async (solo lectura) → data/GLD_1d.parquet y data/GLD_5m.parquet.

Bloqueado hasta que check_connection.py haya pasado completo (SPEC, regla 3).
Se conecta con readonly=True. Este módulo no importa ni usa funciones de órdenes.

Uso:  python -m src.data.ibkr_source [--solo diario|5m]
"""
from __future__ import annotations

import argparse
import os
import time as _time
from datetime import datetime, timezone

import pandas as pd
from dotenv import load_dotenv
from ib_async import IB, Stock, util

from src.config import ROOT, load_config, path_in_root, require_connection_check
from src.data.loader import TZ, save_bars


def connect() -> IB:
    load_dotenv(ROOT / ".env")
    ib = IB()
    ib.connect(
        os.getenv("IB_HOST", "127.0.0.1"),
        int(os.getenv("IB_PORT", "4001")),
        clientId=int(os.getenv("IB_CLIENT_ID", "1")),
        readonly=True,
        timeout=15,
    )
    return ib


def gld_contract(ib: IB, cfg: dict) -> Stock:
    c = Stock(cfg["simbolo"], cfg["ibkr"]["exchange"], cfg["moneda"], primaryExchange=cfg["ibkr"]["primary_exchange"])
    (q,) = ib.qualifyContracts(c)
    return q


def _to_frame(bars) -> pd.DataFrame:
    df = util.df(bars)
    if df is None or df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    return df.set_index("date")[["open", "high", "low", "close", "volume"]]


def download_daily(ib: IB, contract, cfg: dict) -> pd.DataFrame:
    bars = ib.reqHistoricalData(
        contract, endDateTime="", durationStr=cfg["ibkr"]["diario_duracion"], barSizeSetting="1 day",
        whatToShow=cfg["ibkr"]["what_to_show"], useRTH=True, formatDate=1, timeout=120,
    )
    df = _to_frame(bars)
    df.index = pd.DatetimeIndex(pd.to_datetime(df.index))
    return df


def download_5m(ib: IB, contract, cfg: dict) -> pd.DataFrame:
    """Descarga hacia atrás en bloques hasta `intradia_inicio`, respetando pausas de pacing."""
    k = cfg["ibkr"]
    since = pd.Timestamp(k["intradia_inicio"]).tz_localize(TZ)
    end: datetime | str = ""
    chunks = []
    while True:
        bars = ib.reqHistoricalData(
            contract, endDateTime=end, durationStr=k["intradia_bloque"], barSizeSetting="5 mins",
            whatToShow=k["what_to_show"], useRTH=True, formatDate=2, timeout=120,
        )
        df = _to_frame(bars)
        if df.empty:
            break
        df.index = pd.DatetimeIndex(df.index).tz_convert(TZ)
        chunks.append(df)
        first = df.index.min()
        print(f"  5 min: {first:%Y-%m-%d} → {df.index.max():%Y-%m-%d} ({len(df)} barras)")
        if first <= since:
            break
        end = first.tz_convert(timezone.utc).to_pydatetime()
        _time.sleep(float(k["pausa_entre_peticiones_s"]))
    if not chunks:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    out = pd.concat(chunks).sort_index()
    out = out[~out.index.duplicated(keep="last")]
    return out[out.index >= since]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--solo", choices=["diario", "5m"], default=None)
    args = ap.parse_args()

    require_connection_check()
    cfg = load_config()
    data_dir = path_in_root(cfg["rutas"]["datos"])
    ib = connect()
    try:
        contract = gld_contract(ib, cfg)
        if args.solo in (None, "diario"):
            d = download_daily(ib, contract, cfg)
            print(f"Diario: {len(d)} barras → {save_bars(d, data_dir, cfg['simbolo'], '1d')}")
        if args.solo in (None, "5m"):
            m = download_5m(ib, contract, cfg)
            print(f"5 min: {len(m)} barras → {save_bars(m, data_dir, cfg['simbolo'], '5m')}")
    finally:
        ib.disconnect()


if __name__ == "__main__":
    main()
