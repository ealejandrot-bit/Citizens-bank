"""Falla si una columna de resultado o prohibida aparece en cualquier matriz de features guardada en data/processed/.

Lista de prohibidas = leakage.forbidden de config.yaml ∪ columnas con decisión "prohibida" en
outputs/p03/leakage_table.csv (fase 3). Matriz de features = .parquet / .csv de data/processed/ cuyo nombre empieza
con "X_" o contiene "features". Las columnas de resultado solo viven en archivos de target (population*, y_*).
"""
from __future__ import annotations

import pandas as pd
import pytest

from config import P, get

OUTCOMES = ["value_lost_6m", "hard_churn_6m", "soft_churn_3m", "churn_excluded"]
TABLE = P.out(3) / "leakage_table.csv"


def prohibited() -> set[str]:
    s = set(OUTCOMES) | set(get("leakage.forbidden"))
    if TABLE.exists():
        t = pd.read_csv(TABLE)
        s |= set(t.loc[t["decisión"] == "prohibida", "columna"])
    return s - {"household_id"}                       # la llave del hogar puede acompañar a la matriz, nunca como feature


def feature_files():
    d = P.processed
    return [f for f in sorted(d.rglob("*")) if f.suffix in (".parquet", ".csv") and (f.name.startswith("X_") or "features" in f.name)] if d.exists() else []


def columns(f):
    return pd.read_parquet(f).columns if f.suffix == ".parquet" else pd.read_csv(f, nrows=0).columns


def test_tabla_cubre_resultados():
    if TABLE.exists():
        t = pd.read_csv(TABLE).set_index("columna")
        assert all(t.loc[c, "decisión"] == "prohibida" for c in OUTCOMES)


def test_forbidden_list_matches_config():
    assert set(OUTCOMES) <= set(get("leakage.forbidden"))


@pytest.mark.parametrize("f", feature_files(), ids=lambda f: f.name)
def test_no_prohibited_columns(f):
    bad = sorted(c for c in columns(f) if c in prohibited())
    assert not bad, f"{f.name} contiene columnas prohibidas: {bad}"
