"""QC de la fase 1: exclusiones cuadran, tasas por segmento suman al total, targets disjuntos, población guardada."""
import json

import pandas as pd

from config import P


def test_exclusiones():
    e = pd.read_csv(P.out(1) / "exclusions.csv")
    assert e["quedan"].iloc[-1] == 20000 - e["salen (secuencial)"].sum()


def test_tasas_y_poblacion():
    r = pd.read_csv(P.out(1) / "rates_by_segment.csv").set_index("segmento")
    seg = r.drop(index="total")
    for c in ["hogares", "hard (A) n", "soft n", "any_churn n", "B n", "indeterminados B"]:
        assert seg[c].sum() == r.loc["total", c]
    p = pd.read_parquet(P.processed / "population.parquet")
    assert len(p) == r.loc["total", "hogares"] and p.household_id.is_unique
    assert ((p.y_A + p.y_soft) == p.y_any).all()
    assert json.load(open(P.out(1) / "checks.json"))["any_churn = hard + soft (disjuntos)"]
