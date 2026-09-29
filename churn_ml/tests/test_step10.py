"""QC del paso 10: matriz completa, capturas consistentes, regla de recomendación aplicada."""
import pandas as pd

from common import TABLES

T = lambda n: pd.read_csv(TABLES / f"{n}.csv")  # noqa: E731


def test_matriz():
    m = T("step10_matrix_counts").set_index("M1 \\ EBM")
    assert m.to_numpy().sum() == 5779


def test_capturas():
    c = T("step10_capture_options")
    for _, g in c.groupby("opción"):
        g = g.sort_values("K % hogares")
        assert (g["captura eventos %"].diff().dropna() >= 0).all() and (g["captura RV eventos %"].diff().dropna() >= 0).all()
        assert (g["captura eventos %"] <= 100).all()


def test_regla():
    s = T("step10_summary").set_index("opción")
    pol = [o for o in s.index if o.startswith("política") and "M1" in o or o == "política · EBM (tramo, luego p×RV)"]
    best = s.loc[pol, "RV capturado @10%"].max()
    order = ["política · M1 (tramo, luego p×RV)", "política · M1 tramo + orden EBM (b)", "política · M1 + alerta EBM (c)", "política · EBM (tramo, luego p×RV)"]
    rec = next(o for o in order if best - s.loc[o, "RV capturado @10%"] < 1.0)
    assert rec in open(TABLES.parent.parent / "reports" / "step10.md", encoding="utf-8").read()
