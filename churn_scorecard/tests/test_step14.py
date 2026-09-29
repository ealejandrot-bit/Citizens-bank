"""QC del paso 14: Platt con 0.8 ≤ b ≤ 1.2, media alineada, tramos dentro de Wilson 90%, salida calibrada completa."""
import numpy as np
import pandas as pd

from common import SCORES, TABLES

T = lambda n: pd.read_csv(TABLES / f"{n}.csv")  # noqa: E731


def test_platt():
    p = T("step14_platt").iloc[0]
    assert 0.8 <= p.b <= 1.2
    d = T("step14_iso_vs_platt_bootstrap").set_index("diferencia (isotónica − Platt)")
    assert (p["método elegido"] == "isotónica") == (d.loc["Brier", "IC 95% sup"] < 0)


def test_alineacion():
    a = T("step14_alignment").set_index("muestra")
    assert abs(a.loc["val", "media p calibrada %"] - a.loc["val", "tasa observada %"]) < 0.5
    assert abs(a.loc["dev", "media p calibrada %"] - a.loc["dev", "tasa observada %"]) < 0.5


def test_tramos_calibrados():
    t = T("step14_tramo_calibration")
    assert t["esperada dentro de IC"].astype(bool).all() and list(t.tramo) == ["Crítico", "Alto", "Vigilancia", "Estable"]
    assert (np.diff(t["esperada %"]) < 0).all()


def test_salida_calibrada():
    s = pd.read_csv(SCORES / "household_scores.csv")
    assert len(s) == 20000 and s.probabilidad_calibrada.between(0, 1).all()
    # calibración monótona: mismo orden que el score
    o = s.sort_values("score")
    assert (np.diff(o.probabilidad_calibrada.to_numpy()) <= 1e-12).all()
