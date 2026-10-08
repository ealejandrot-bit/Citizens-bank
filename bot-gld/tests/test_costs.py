import pytest

from src.backtest.costs import CostModel

C = CostModel(comision_por_accion=0.005, comision_minima=1.0, comision_maxima_pct=0.01, slippage=0.01)


def test_comision_minimo():
    # 10 acciones × 0.005 = 0.05 < 1.00 → mínimo 1.00 (valor 3,000 → tope 30 no aplica)
    assert C.commission(10, 300.0) == pytest.approx(1.00)


def test_comision_maximo():
    # 1 acción de 27 USD: mínimo 1.00 pero tope 1% = 0.27
    assert C.commission(1, 27.0) == pytest.approx(0.27)
    # 1000 acciones a 0.20: 5.00 por acción, tope 1% de 200 = 2.00
    assert C.commission(1000, 0.20) == pytest.approx(2.00)


def test_comision_por_accion():
    assert C.commission(1000, 300.0) == pytest.approx(5.00)
    assert C.commission(0, 300.0) == 0.0


def test_slippage_por_lado():
    assert C.fill_price(100.0, +1) == pytest.approx(100.01)
    assert C.fill_price(100.0, -1) == pytest.approx(99.99)
