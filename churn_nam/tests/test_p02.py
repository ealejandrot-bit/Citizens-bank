"""QC de la fase 2: missingness clasificada, indicadores app_ consistentes, ninguna fila eliminada."""
import json

import pandas as pd

from config import P


def test_clasificacion():
    m = pd.read_csv(P.out(2) / "missingness.csv")
    assert m.clase.isin(["estructural", "ruido", "sin regla"]).all()
    e = m[m.clase == "estructural"]
    assert (e["% faltantes con gatillo False"] >= 97).all() and (e["% gatillo False que faltan"] >= 97).all()
    assert (m.loc[m.clase == "ruido", "% missing"] <= 5).all()


def test_app_y_filas():
    x = pd.read_parquet(P.processed / "features_p02.parquet")
    pop = pd.read_parquet(P.processed / "population.parquet")
    assert len(x) == len(pop) and json.load(open(P.out(2) / "summary.json"))["filas eliminadas"] == 0
    a = pd.read_csv(P.out(2) / "app_indicators.csv")
    assert set(a.indicador) <= set(x.columns) and x[a.indicador].isin([0, 1]).all().all()
