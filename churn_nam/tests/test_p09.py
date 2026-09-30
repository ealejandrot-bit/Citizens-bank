"""QC de la fase 9: NAM entrenado y evaluado en validación (test sin abrir), monotonía 0, convergencia reportada."""
import json

import pandas as pd

from config import P


def test_resumen():
    s = json.load(open(P.out(9) / "summary.json"))
    assert s["violaciones totales en variables duras"] == 0 and s["test abierto"] is False
    assert "convergió (early stopping antes de epochs_max)" in s


def test_metricas():
    c = pd.read_csv(P.out(9) / "nam_validation.csv")
    assert (c.groupby(["target", "modelo"]).segmento.nunique() == 3).all()
