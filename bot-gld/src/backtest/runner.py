"""Corre cada estrategia y comprar y mantener por periodo (in-sample, out-of-sample, total).

Cada periodo es un backtest independiente que arranca con `capital_inicial` (mismo capital y mismo
periodo para la estrategia y el benchmark).
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from src.backtest.costs import CostModel
from src.backtest.engine import BacktestResult, buy_and_hold, run_backtest
from src.backtest.metrics import compute_metrics, day_trades_por_ventana, diff_vs_benchmark
from src.strategies import trend_daily, vwap_intraday

BENCHMARK = "Comprar y mantener"


@dataclass
class PeriodRun:
    periodo: str
    inicio: object
    fin: object
    resultados: dict[str, BacktestResult]  # nombre → resultado (incluye benchmark)
    metricas: dict[str, dict]
    diferencias: dict[str, dict]           # estrategia → diferencias vs benchmark


def periodos(fechas: dict, bars: pd.DataFrame) -> list[tuple[str, object, object]]:
    fin = fechas.get("fin") or bars.index[-1].strftime("%Y-%m-%d")
    return [
        ("In-sample", fechas["inicio"], fechas["in_sample_end"]),
        ("Out-of-sample", fechas["out_sample_start"], fin),
        ("Total", fechas["inicio"], fin),
    ]


def build_targets(estrategia: str, bars: pd.DataFrame, cfg: dict) -> dict[str, pd.Series]:
    p = cfg["estrategias"][estrategia]
    if estrategia == "trend_daily":
        return trend_daily.targets(bars, p)
    if estrategia == "vwap_intraday":
        t = vwap_intraday.targets(
            bars, p["sin_operar_hasta"], p["cierre_forzado"], int(p["max_operaciones_dia"])
        )
        return {f"VWAP intradía (máx. {p['max_operaciones_dia']}/día)": t}
    raise ValueError(f"Estrategia desconocida: {estrategia}")


def run_strategy(estrategia: str, bars: pd.DataFrame, cfg: dict) -> list[PeriodRun]:
    costs = CostModel.from_config(cfg, intradia=estrategia == "vwap_intraday")
    capital = float(cfg["capital_inicial"])
    frac = bool(cfg["fracciones"])
    dec = int(cfg.get("decimales_fraccion", 4))
    targets = build_targets(estrategia, bars, cfg)
    runs = []
    for nombre_p, ini, fin in periodos(cfg["fechas"][estrategia], bars):
        res = {
            n: run_backtest(bars, t, costs, capital, ini, fin, frac, dec, nombre=n)
            for n, t in targets.items()
        }
        res[BENCHMARK] = buy_and_hold(bars, costs, capital, ini, fin, frac, dec, nombre=BENCHMARK)
        met = {n: compute_metrics(r) for n, r in res.items()}
        diffs = {n: diff_vs_benchmark(met[n], met[BENCHMARK]) for n in targets}
        runs.append(PeriodRun(nombre_p, ini, fin, res, met, diffs))
    return runs


def pdt_resumen(res: BacktestResult) -> dict:
    """Day trades por ventana móvil de 5 días hábiles (regla de pattern day trader: ≥ 4)."""
    if not res.operable:
        return {}
    dias = pd.DatetimeIndex(res.daily_equity.index)
    w = day_trades_por_ventana(res.trades, dias, 5)
    return {
        "max_por_ventana": int(w.max()) if len(w) else 0,
        "ventanas_con_4_o_mas": int((w >= 4).sum()),
        "ventanas": int(len(w)),
        "day_trades_total": _n_day_trades(res.trades),
    }


def _n_day_trades(trades: pd.DataFrame) -> int:
    if not len(trades):
        return 0
    et = pd.DatetimeIndex(trades["entry_time"])
    xt = pd.DatetimeIndex(trades["exit_time"])
    return int((et.normalize() == xt.normalize()).sum())
