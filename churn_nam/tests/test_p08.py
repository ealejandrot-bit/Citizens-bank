"""QC de la fase 8: challenger monótono sin violaciones, regla de champion aplicada, test sin abrir."""
import json

import pandas as pd

from config import P


def test_monotonia_y_regla():
    c = pd.read_csv(P.out(8) / "challenger_validation.csv")
    a = c[(c.target == "A") & (c.segmento == "pooled")]
    assert (a["violaciones ICE"] == 0).all() and (a["violaciones PDP"] == 0).all()
    d = json.load(open(P.out(8) / "champion_decision.json"))
    exp = ("LightGBM monótono" if d["ΔPR-AUC LightGBM − EBM"] > 0 else "EBM monótono") if abs(d["ΔPR-AUC LightGBM − EBM"]) >= d["sd bootstrap"] else "EBM monótono"
    assert d["champion provisional"] == exp and d["test abierto"] is False
