"""QC de la fase 4: mapa de monotonía confirmado y consistente con SPEC §4; app_ fuera de la matriz; sin prohibidas."""
import json

import pandas as pd

from config import P


def test_mapa_y_matriz():
    m = json.load(open(P.out(4) / "monotonicity_map.json"))
    x = pd.read_parquet(P.processed / "X_features.parquet")
    assert set(m) == set(x.columns) - {"household_id"}
    assert not any(c.startswith("app_") for c in x.columns)
    assert all(v["restricción"] == ("libre" if v["signo"] == "?" else "dura") for v in m.values())
    assert m["has_investments"]["signo"] == "?" and m["has_credit_anchor"]["signo"] == "−" and m["banker_change_6m_flag"]["signo"] == "+"


def test_mascaras():
    k = pd.read_parquet(P.processed / "masks_app.parquet")
    assert k.shape[1] == 13 and len(k) == len(pd.read_parquet(P.processed / "X_features.parquet"))
