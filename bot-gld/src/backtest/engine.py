"""Motor de backtest por barras, long-only, sin look-ahead.

Convención: `targets` es la decisión tomada al CIERRE de cada barra (1 = largo, 0 = efectivo),
calculada solo con datos hasta esa barra. El motor ejecuta la decisión de la barra t en la
APERTURA de la barra t+1. Nunca se ejecuta al mismo cierre que generó la señal.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.backtest.costs import CostModel


@dataclass
class BacktestResult:
    nombre: str
    operable: bool
    nota: str
    capital_inicial: float
    equity: pd.DataFrame = field(default_factory=pd.DataFrame)  # por barra: cash, qty, close, equity
    daily_equity: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    trades: pd.DataFrame = field(default_factory=pd.DataFrame)
    costos: dict = field(default_factory=dict)
    exposicion: float = float("nan")

    @property
    def equity_final(self) -> float:
        return float(self.equity["equity"].iloc[-1]) if self.operable else float("nan")


TRADE_COLUMNS = [
    "entry_time", "entry_raw", "entry_fill", "exit_time", "exit_raw", "exit_fill",
    "qty", "comision", "slippage", "pnl",
]


def _unit(fracciones: bool, decimales: int) -> float:
    return 10.0 ** (-decimales) if fracciones else 1.0


def _floor_to(q: float, unit: float) -> float:
    if q <= 0:
        return 0.0
    n = math.floor(q / unit + 1e-9)
    return round(n * unit, 10)


def max_qty(cash: float, price: float, costs: CostModel, fracciones: bool, decimales: int = 4) -> float:
    """Máximo de acciones comprables con `cash` a `price` (ya con slippage), incluyendo comisión."""
    if cash <= 0 or price <= 0:
        return 0.0
    unit = _unit(fracciones, decimales)
    q = _floor_to((cash - costs.commission(cash / price, price)) / price, unit)
    while q > 0 and q * price + costs.commission(q, price) > cash + 1e-9:
        q = _floor_to(q - unit, unit)
    return q


def is_operable(cash: float, price: float, costs: CostModel, fracciones: bool, decimales: int = 4) -> bool:
    return max_qty(cash, costs.fill_price(price, +1), costs, fracciones, decimales) > 0


def _period_slice(index: pd.DatetimeIndex, start, end) -> tuple[int, int]:
    mask = np.ones(len(index), dtype=bool)
    if start is not None:
        mask &= index >= _as_ts(start, index)
    if end is not None:
        mask &= index < _as_ts(end, index) + pd.Timedelta(days=1)  # fin inclusivo (día completo)
    pos = np.flatnonzero(mask)
    if len(pos) == 0:
        raise ValueError(f"No hay barras entre {start} y {end}")
    return int(pos[0]), int(pos[-1])


def _as_ts(x, index: pd.DatetimeIndex) -> pd.Timestamp:
    ts = pd.Timestamp(x).normalize()
    if index.tz is not None and ts.tz is None:
        ts = ts.tz_localize(index.tz)
    return ts


def run_backtest(
    bars: pd.DataFrame,
    targets: pd.Series,
    costs: CostModel,
    capital: float,
    start=None,
    end=None,
    fracciones: bool = False,
    decimales: int = 4,
    nombre: str = "estrategia",
    initial_target: float = 0.0,
    cobrar_datos: bool = True,
) -> BacktestResult:
    """Simula la estrategia sobre las barras del periodo [start, end].

    `bars` y `targets` pueden incluir historia previa a `start` (calentamiento): la decisión de la
    última barra previa al periodo se ejecuta en la apertura de la primera barra del periodo.
    `initial_target` se usa solo si no existe barra previa.
    """
    targets = targets.reindex(bars.index).fillna(0.0).clip(0.0, 1.0)
    p0, p1 = _period_slice(bars.index, start, end)
    idx = bars.index[p0 : p1 + 1]
    opens = bars["open"].to_numpy(dtype=float)
    closes = bars["close"].to_numpy(dtype=float)
    tgt = targets.to_numpy(dtype=float)

    cash = float(capital) - costs.conversion_mxn_usd
    c_conv = costs.conversion_mxn_usd

    if not is_operable(cash, opens[p0], costs, fracciones, decimales):
        nota = (
            f"No operable: con {cash:.2f} USD no alcanza para 1 acción a {opens[p0]:.2f} USD más costos"
            + ("" if fracciones else " (fracciones: false)")
        )
        return BacktestResult(nombre, False, nota, float(capital), costos={"conversion": c_conv})

    qty = 0.0
    c_com = c_slip = c_datos = 0.0
    trades: list[dict] = []
    open_trade: dict | None = None
    rec_cash = np.empty(len(idx))
    rec_qty = np.empty(len(idx))
    rec_held = np.zeros(len(idx), dtype=bool)
    last_month = None

    def sell(i: int, raw: float, when) -> None:
        nonlocal cash, qty, c_com, c_slip, open_trade
        px = costs.fill_price(raw, -1)
        com = costs.commission(qty, px)
        cash += qty * px - com
        c_com += com
        c_slip += qty * costs.slippage
        ot = open_trade
        ot.update(exit_time=when, exit_raw=raw, exit_fill=px)
        ot["comision"] += com
        ot["slippage"] += qty * costs.slippage
        ot["pnl"] = qty * (px - ot["entry_fill"]) - ot["comision"]
        trades.append(ot)
        open_trade = None
        qty = 0.0

    for k, i in enumerate(range(p0, p1 + 1)):
        t = bars.index[i]
        month = (t.year, t.month)
        if cobrar_datos and month != last_month and costs.datos_mensual:
            cash -= costs.datos_mensual
            c_datos += costs.datos_mensual
        last_month = month

        desired = tgt[i - 1] if i > 0 else initial_target
        if desired > 0 and qty == 0:
            px = costs.fill_price(opens[i], +1)
            q = max_qty(cash, px, costs, fracciones, decimales)
            if q > 0:
                com = costs.commission(q, px)
                cash -= q * px + com
                c_com += com
                c_slip += q * costs.slippage
                qty = q
                open_trade = dict(
                    entry_time=t, entry_raw=opens[i], entry_fill=px, qty=q,
                    comision=com, slippage=q * costs.slippage,
                )
        elif desired == 0 and qty > 0:
            sell(i, opens[i], t)

        rec_held[k] = qty > 0
        if k == len(idx) - 1 and qty > 0:
            # Fin del periodo: se liquida al cierre de la última barra, con costos.
            sell(i, closes[i], t)
        rec_cash[k] = cash
        rec_qty[k] = qty

    eq = pd.DataFrame({"cash": rec_cash, "qty": rec_qty, "close": closes[p0 : p1 + 1]}, index=idx)
    eq["equity"] = eq["cash"] + eq["qty"] * eq["close"]
    costos = {
        "comision": c_com,
        "slippage": c_slip,
        "conversion": c_conv,
        "datos": c_datos,
    }
    costos["total"] = sum(costos.values())
    trades_df = pd.DataFrame(trades, columns=TRADE_COLUMNS)
    # Exposición: fracción de barras con posición abierta al cierre de la barra
    # (la barra de liquidación final cuenta como invertida).
    return BacktestResult(
        nombre=nombre,
        operable=True,
        nota="",
        capital_inicial=float(capital),
        equity=eq,
        daily_equity=to_daily(eq["equity"]),
        trades=trades_df,
        costos=costos,
        exposicion=float(rec_held.mean()),
    )


def buy_and_hold(
    bars: pd.DataFrame,
    costs: CostModel,
    capital: float,
    start=None,
    end=None,
    fracciones: bool = False,
    decimales: int = 4,
    nombre: str = "Comprar y mantener",
) -> BacktestResult:
    """Compra en la apertura de la primera barra del periodo con todo el capital y vende al cierre
    de la última, con comisión y slippage. No paga datos de mercado (no los necesita)."""
    ones = pd.Series(1.0, index=bars.index)
    return run_backtest(
        bars, ones, costs, capital, start, end, fracciones, decimales,
        nombre=nombre, initial_target=1.0, cobrar_datos=False,
    )


def to_daily(series: pd.Series) -> pd.Series:
    """Último valor de cada día (índice de fechas sin zona horaria)."""
    idx = series.index
    days = idx.tz_localize(None).normalize() if idx.tz is not None else idx.normalize()
    out = series.groupby(days).last()
    out.index.name = "date"
    return out
