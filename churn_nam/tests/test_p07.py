"""QC de la fase 7: benchmarks completos en validación (test sin abrir), pooled/HNW/UHNW, con y sin pesos."""
import json

import pandas as pd

from config import P


def test_benchmarks_completos():
    b = pd.read_csv(P.out(7) / "benchmarks_validation.csv")
    assert (b.groupby(["target", "modelo", "pesos de clase"]).segmento.nunique() == 3).all()
    assert set(b.modelo) == {"logística L2", "XGBoost", "LightGBM"} and set(b["pesos de clase"]) == {"ninguno", "balanced"}
    p = b[b.segmento == "pooled"]
    assert (p.hogares.groupby(p.target).nunique() == 1).all()
    assert json.load(open(P.out(7) / "summary.json"))["test abierto"] is False


def test_referencia_alite_mismos_hogares():
    r = pd.read_csv(P.out(7) / "alite_fair_validation.csv")
    assert (r.groupby("target").hogares.nunique() == 1).all() and "A-lite (congelado)" in set(r.modelo)
