"""QC del paso 13: criterios de aprobación del SPEC en validación y consistencia de las tablas."""
import pandas as pd

from common import TABLES

T = lambda n: pd.read_csv(TABLES / f"{n}.csv")  # noqa: E731


def test_aprobacion():
    a = T("step13_approval")
    assert len(a) == 9 and (a.cumple == "sí").all()


def test_gini_y_psi():
    g = T("step13_global").set_index("muestra")
    assert (g.loc["dev", "Gini"] - g.loc["val", "Gini"]) / g.loc["dev", "Gini"] <= 0.15
    t = T("step13_tramos_dev_val")
    assert (t.groupby("tramos")["PSI (contribución)"].sum() < 0.10).all()
    for _, s in t.groupby("tramos"):
        assert abs(s["% val"].sum() - 100) < 1e-9 and abs(s["% dev"].sum() - 100) < 1e-9


def test_gains_y_confusion():
    gn = T("step13_gains_val")
    g = T("step13_global").set_index("muestra")
    assert gn.eventos.sum() == g.loc["val", "eventos"] and abs(gn["captura %"].sum() - 100) < 1e-9
    c = T("step13_confusion_critico").iloc[0]
    assert c.TP + c.FP + c.FN + c.TN == g.loc["val", "hogares"]
    pk = T("step13_precision_at_k")
    assert (pk["captura %"].diff().dropna() > 0).all()


def test_eventos_minimos_val():
    assert (T("step13_bands_val").eventos >= 30).all()
    t = T("step13_tramos_dev_val")
    assert (t["eventos val"] >= 30).all()
