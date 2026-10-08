import pandas as pd

from src.backtest.costs import CostModel
from src.backtest.engine import run_backtest
from src.backtest.metrics import day_trades_por_ventana
from src.data.loader import rth_filter
from src.data.synthetic import intraday_bars
from src.strategies import vwap_intraday

COSTS = CostModel(slippage=0.02)


def _run(n_days=40, max_ops=2, seed=0):
    bars = intraday_bars(n_days=n_days, seed=seed)
    t = vwap_intraday.targets(bars, "10:00", "15:55", max_ops)
    return bars, t, run_backtest(bars, t, COSTS, 10_000, fracciones=True)


def test_nunca_posicion_al_cierre():
    for seed in range(3):
        bars, t, res = _run(seed=seed)
        assert len(res.trades) > 0
        last_bar = res.equity.groupby(res.equity.index.date).tail(1)
        assert (last_bar["qty"] == 0).all()
        # tampoco al quitar barras finales (día de cierre anticipado)
        assert (t.groupby(t.index.date).tail(2) == 0).all()


def test_dia_corto_sin_overnight():
    bars = intraday_bars(n_days=5, seed=4)
    d = bars.index[0].date()
    corto = bars[~((bars.index.date == d) & (bars.index.time >= pd.Timestamp("13:00").time()))]
    t = vwap_intraday.targets(corto)
    res = run_backtest(corto, t, COSTS, 10_000, fracciones=True)
    assert (res.equity.groupby(res.equity.index.date).tail(1)["qty"] == 0).all()


def test_ventanas_de_tiempo_y_maximo_por_dia():
    bars, t, res = _run(n_days=60, max_ops=2, seed=1)
    tr = res.trades
    entry_t = pd.DatetimeIndex(tr["entry_time"])
    exit_t = pd.DatetimeIndex(tr["exit_time"])
    assert (entry_t.time >= pd.Timestamp("10:00").time()).all()
    assert (exit_t.time <= pd.Timestamp("15:55").time()).all()
    assert (entry_t.date == exit_t.date).all()
    assert tr.groupby(entry_t.date).size().max() <= 2


def test_sin_lookahead_intradia():
    bars = intraday_bars(n_days=3, seed=2)
    t = 100
    altered = bars.copy()
    altered.iloc[t + 1 :, :4] *= 1.03
    altered.iloc[t + 1 :, 4] *= 5
    a = vwap_intraday.targets(bars)
    b = vwap_intraday.targets(altered)
    pd.testing.assert_series_equal(a.iloc[: t + 1], b.iloc[: t + 1])


def test_day_trades_ventana_5_dias():
    dias = pd.bdate_range("2024-01-01", periods=7)
    tr = pd.DataFrame({
        "entry_time": [dias[0], dias[0], dias[1], dias[3], dias[6]],
        "exit_time": [dias[0], dias[0], dias[1], dias[3], dias[6]],
    })
    w = day_trades_por_ventana(tr, dias, 5)
    assert w.max() == 4 and w.iloc[-1] == 2


def test_rth_filter():
    idx = pd.date_range("2024-01-02 09:00", "2024-01-02 16:30", freq="5min", tz="America/New_York")
    df = pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 1.0}, index=idx)
    out = rth_filter(df)
    assert out.index[0].strftime("%H:%M") == "09:30" and out.index[-1].strftime("%H:%M") == "15:55"
