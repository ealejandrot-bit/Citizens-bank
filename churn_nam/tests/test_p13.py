"""QC de la fase 13: curva EWS completa, umbral solo si ews.alerts_per_month existe, paquete MRM con su estructura."""
import json

import numpy as np
import pandas as pd

from config import HEADER, P, get


def test_ews_y_umbral():
    e = pd.read_csv(P.out(13) / "ews_curve.csv")
    assert set(e.segmento) == {"pooled", "UHNW"} and np.isclose(e["alertas por mes (muestra)"], e["hogares marcados"] / get("ews.horizon_months")).all()   # tolerancia de ida y vuelta del CSV
    s = json.load(open(P.out(13) / "summary.json"))
    assert (get("ews.alerts_per_month") is None) == isinstance(s["umbral"], str)


def test_paquete_mrm():
    t = (P.reports / "MRM_package.md").read_text(encoding="utf-8")
    lines = t.splitlines()
    assert lines[0] == HEADER
    sec = [l for l in lines if l.startswith("## ")]
    assert sec[0].startswith("## Limitaciones") and sec[-1].startswith("## Preguntas centrales")
    assert all(f"L{i}" in t for i in range(1, 7)) and t.count("**¿") == 3
