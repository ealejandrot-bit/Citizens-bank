"""Métricas de desempeño sobre la equity diaria. Sharpe con rf = 0 (declarado)."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.backtest.engine import BacktestResult

DIAS_HABILES = 252
RF = 0.0  # tasa libre de riesgo usada en el Sharpe

ETIQUETAS = {
    "equity_final": "Equity final (USD)",
    "cagr": "CAGR",
    "vol_anual": "Volatilidad anual",
    "sharpe": "Sharpe (rf = 0)",
    "max_dd": "Drawdown máximo",
    "max_dd_dias": "Duración DD máx. (días naturales)",
    "n_operaciones": "# operaciones",
    "win_rate": "Win rate",
    "ganancia_prom": "Ganancia promedio (USD)",
    "perdida_prom": "Pérdida promedio (USD)",
    "exposicion": "Exposición (% del tiempo)",
    "costo_total": "Costo total (USD)",
    "costo_pct_capital": "Costo total (% capital inicial)",
}
PCT = {"cagr", "vol_anual", "max_dd", "win_rate", "exposicion", "costo_pct_capital"}


def daily_returns(daily_equity: pd.Series, capital: float) -> pd.Series:
    """Rendimientos diarios; el primero es contra el capital inicial (incluye costos de entrada)."""
    prev = daily_equity.shift(1)
    prev.iloc[0] = capital
    return daily_equity / prev - 1.0


def max_drawdown(daily_equity: pd.Series, capital: float) -> tuple[float, int, bool]:
    """(drawdown máximo ≤ 0, duración en días naturales pico→recuperación, recuperado?)."""
    eq = daily_equity.to_numpy(dtype=float)
    dates = daily_equity.index
    peak = np.maximum.accumulate(np.r_[capital, eq])[1:]
    dd = eq / peak - 1.0
    trough = int(np.argmin(dd))
    mdd = float(dd[trough])
    if mdd >= 0:
        return 0.0, 0, True
    peak_val = peak[trough]
    before = np.flatnonzero(eq[: trough + 1] >= peak_val - 1e-12)
    peak_date = dates[before[-1]] if len(before) else dates[0]
    after = np.flatnonzero(eq[trough:] >= peak_val - 1e-12)
    if len(after):
        return mdd, int((dates[trough + after[0]] - peak_date).days), True
    return mdd, int((dates[-1] - peak_date).days), False


def compute_metrics(res: BacktestResult) -> dict:
    if not res.operable:
        return {"operable": False, "nota": res.nota}
    de = res.daily_equity
    cap = res.capital_inicial
    r = daily_returns(de, cap)
    dias = max((de.index[-1] - de.index[0]).days, 1)
    final = float(de.iloc[-1])
    cagr = (final / cap) ** (365.25 / dias) - 1.0 if final > 0 else -1.0
    std = float(r.std(ddof=1)) if len(r) > 1 else float("nan")
    sharpe = (float(r.mean()) - RF / DIAS_HABILES) / std * math.sqrt(DIAS_HABILES) if std and std > 0 else float("nan")
    mdd, mdd_dias, recuperado = max_drawdown(de, cap)
    t = res.trades
    n = len(t)
    wins = t.loc[t["pnl"] > 0, "pnl"] if n else pd.Series(dtype=float)
    losses = t.loc[t["pnl"] <= 0, "pnl"] if n else pd.Series(dtype=float)
    return {
        "operable": True,
        "equity_final": final,
        "cagr": cagr,
        "vol_anual": std * math.sqrt(DIAS_HABILES) if std == std else float("nan"),
        "sharpe": sharpe,
        "max_dd": mdd,
        "max_dd_dias": mdd_dias,
        "max_dd_recuperado": recuperado,
        "n_operaciones": n,
        "win_rate": len(wins) / n if n else float("nan"),
        "ganancia_prom": float(wins.mean()) if len(wins) else float("nan"),
        "perdida_prom": float(losses.mean()) if len(losses) else float("nan"),
        "exposicion": res.exposicion,
        "costo_total": res.costos["total"],
        "costo_pct_capital": res.costos["total"] / cap,
    }


def diff_vs_benchmark(m: dict, bh: dict) -> dict:
    """Estrategia − comprar y mantener en CAGR, Sharpe y drawdown máximo."""
    if not (m.get("operable") and bh.get("operable")):
        return {}
    return {k: m[k] - bh[k] for k in ("cagr", "sharpe", "max_dd")}


def day_trades_por_ventana(trades: pd.DataFrame, dias: pd.DatetimeIndex, ventana: int = 5) -> pd.Series:
    """Day trades (entrada y salida el mismo día) en cada ventana móvil de `ventana` días hábiles."""
    if len(trades):
        et = pd.DatetimeIndex(trades["entry_time"])
        xt = pd.DatetimeIndex(trades["exit_time"])
        if et.tz is not None:
            et, xt = et.tz_localize(None), xt.tz_localize(None)
        same = et.normalize() == xt.normalize()
        por_dia = pd.Series(1, index=et.normalize()[same]).groupby(level=0).sum()
    else:
        por_dia = pd.Series(dtype=float)
    por_dia = por_dia.reindex(dias, fill_value=0)
    return por_dia.rolling(ventana, min_periods=1).sum().astype(int)
