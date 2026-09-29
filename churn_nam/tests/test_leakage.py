"""Falla si una columna de resultado aparece en cualquier matriz de features guardada en data/processed/.

Matriz de features = todo archivo .parquet / .csv de data/processed/ cuyo nombre empieza con "X_" o contiene
"features". Las columnas de resultado solo pueden vivir en archivos de target ("y_*", "target*", "population*").
"""
from __future__ import annotations

import pandas as pd
import pytest

from config import P, get

FORBIDDEN = ["value_lost_6m", "hard_churn_6m", "soft_churn_3m", "churn_excluded"]


def feature_files():
    d = P.processed
    if not d.exists():
        return []
    return [f for f in sorted(d.rglob("*")) if f.suffix in (".parquet", ".csv") and (f.name.startswith("X_") or "features" in f.name)]


def columns(f):
    return pd.read_parquet(f).columns if f.suffix == ".parquet" else pd.read_csv(f, nrows=0).columns


def test_forbidden_list_matches_config():
    assert set(FORBIDDEN) <= set(get("leakage.forbidden"))


@pytest.mark.parametrize("f", feature_files(), ids=lambda f: f.name)
def test_no_outcome_columns(f):
    bad = [c for c in columns(f) if c in FORBIDDEN]
    assert not bad, f"{f.name} contiene columnas de resultado: {bad}"
