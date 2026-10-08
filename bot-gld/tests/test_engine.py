import numpy as np
import pandas as pd
import pytest

from src.backtest.costs import CostModel
from src.backtest.engine import buy_and_hold, run_backtest
from src.backtest.metrics import compute_metrics, max_drawdown
from src.data.synthetic import daily_bars
from src.strategies import trend_daily

COSTS = CostModel(slippage=0.01, datos_mensual=0.0)


def _gross_pnl(trades: pd.DataFrame) -> float:
    return float((trades["qty"] * (trades["exit_raw"] - trades["entry_raw"])).sum())


def test_tendencia_constante_largo_y_igual_a_bh():
    bars = daily_bars(n=700, drift=0.001, vol=0.0, price0=100)
    start = bars.index[300]
    sig = trend_daily.signal_sma(bars, 200)
    assert (sig.loc[start:] == 1).all()  # queda largo todo el periodo
    res = run_backtest(bars, sig, COSTS, 10_000, start=start, fracciones=False)
    bh = buy_and_hold(bars, COSTS, 10_000, start=start, fracciones=False)
    assert len(res.trades) == 1
    assert res.exposicion == pytest.approx(1.0)
    assert res.equity_final == pytest.approx(bh.equity_final, rel=1e-9)
    # ≈ comprar y mantener sin costos menos costos
    q = res.trades["qty"].iloc[0]
    sin_costos = 10_000 + q * (bars["close"].iloc[-1] - bars["open"].loc[start])
    assert res.equity_final == pytest.approx(sin_costos - res.costos["total"])


@pytest.mark.parametrize("fracciones", [False, True])
def test_serie_plana_con_ruido_costos_exactos(fracciones):
    bars = daily_bars(n=600, drift=0.0, vol=0.01, price0=100, seed=3)
    sig = trend_daily.signal_sma(bars, 20)  # cambia seguido → muchas operaciones
    costs = CostModel(slippage=0.01, conversion_mxn_usd=2.5, datos_mensual=1.5)
    res = run_backtest(bars, sig, costs, 5_000, start=bars.index[50], fracciones=fracciones)
    assert len(res.trades) > 10
    c = res.costos
    assert c["total"] == pytest.approx(c["comision"] + c["slippage"] + c["conversion"] + c["datos"])
    assert c["total"] > 0
    # equity final = capital + PnL bruto (precios sin slippage) − costos totales, exacto
    assert res.equity_final == pytest.approx(5_000 + _gross_pnl(res.trades) - c["total"], abs=1e-6)


def test_precio_constante_equity_pierde_exactamente_los_costos():
    bars = daily_bars(n=300, drift=0.0, vol=0.0, price0=50)
    sig = pd.Series(np.tile([1.0, 1.0, 0.0, 0.0], 75), index=bars.index)
    res = run_backtest(bars, sig, COSTS, 1_000, fracciones=False)
    assert len(res.trades) > 50
    assert res.equity_final == pytest.approx(1_000 - res.costos["total"], abs=1e-9)


def test_sin_lookahead_senal_y_equity():
    bars = daily_bars(n=500, drift=0.0003, vol=0.012, seed=1)
    t = 350
    altered = bars.copy()
    altered.iloc[t + 1 :, :4] *= 1.5  # alterar t+1 en adelante
    s1, s2 = trend_daily.signal_sma(bars), trend_daily.signal_sma(altered)
    pd.testing.assert_series_equal(s1.iloc[: t + 1], s2.iloc[: t + 1])
    c1, c2 = trend_daily.signal_cruce(bars), trend_daily.signal_cruce(altered)
    pd.testing.assert_series_equal(c1.iloc[: t + 1], c2.iloc[: t + 1])
    # La equity hasta el cierre de t tampoco cambia (mismo fin de periodo para no liquidar antes)
    r1 = run_backtest(bars, s1, COSTS, 10_000, start=bars.index[250], fracciones=True)
    r2 = run_backtest(altered, s2, COSTS, 10_000, start=bars.index[250], fracciones=True)
    e1 = r1.equity["equity"].loc[: bars.index[t]]
    e2 = r2.equity["equity"].loc[: bars.index[t]]
    pd.testing.assert_series_equal(e1, e2)


def test_ejecucion_en_apertura_siguiente():
    bars = daily_bars(n=10, drift=0.01, vol=0.0)
    sig = pd.Series(0.0, index=bars.index)
    sig.iloc[3] = 1.0  # señal al cierre del día 3
    res = run_backtest(bars, sig, COSTS, 10_000, fracciones=False)
    tr = res.trades.iloc[0]
    assert tr["entry_time"] == bars.index[4]
    assert tr["entry_raw"] == bars["open"].iloc[4]
    assert tr["exit_time"] == bars.index[5]


def test_no_operable_sin_fracciones():
    bars = daily_bars(n=50, price0=300)
    sig = pd.Series(1.0, index=bars.index)
    res = run_backtest(bars, sig, COSTS, 27, fracciones=False)
    assert not res.operable and "No operable" in res.nota
    assert compute_metrics(res) == {"operable": False, "nota": res.nota}
    # con fracciones sí opera
    assert run_backtest(bars, sig, COSTS, 27, fracciones=True).operable


def test_max_drawdown_y_duracion():
    idx = pd.bdate_range("2020-01-01", periods=6)
    eq = pd.Series([100, 110, 99, 88, 105, 111.0], index=idx)
    mdd, dias, rec = max_drawdown(eq, 100)
    assert mdd == pytest.approx(88 / 110 - 1)
    assert rec and dias == (idx[5] - idx[1]).days


def test_metricas_basicas():
    bars = daily_bars(n=600, drift=0.0005, vol=0.01, seed=2)
    bh = buy_and_hold(bars, COSTS, 10_000, start=bars.index[100], fracciones=True)
    m = compute_metrics(bh)
    assert m["n_operaciones"] == 1 and m["exposicion"] == pytest.approx(1.0)
    assert m["vol_anual"] > 0 and m["max_dd"] <= 0
    assert m["costo_pct_capital"] == pytest.approx(m["costo_total"] / 10_000)
