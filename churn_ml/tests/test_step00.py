"""QC del paso 0: herencia idéntica, hechos de la sección B, modelos anteriores intactos."""
import hashlib
import json

import pandas as pd

from common import INH, INHERIT, M1, ROOT, TABLES


def test_hechos():
    f = pd.read_csv(TABLES / "step00_facts.csv")
    assert f.coincide.all(), f[~f.coincide]


def test_copias_identicas_al_origen():
    for src, dst in INHERIT:
        assert hashlib.sha256((M1 / src).read_bytes()).digest() == hashlib.sha256((INH / dst).read_bytes()).digest()


def test_modelos_anteriores_intactos():
    prev = json.loads((INH / "previous_models_sha256.json").read_text(encoding="utf-8"))
    assert len(prev) > 0
    for f, h in prev.items():
        p = ROOT.parent / f
        assert p.exists(), f"se borró {f}"
        assert hashlib.sha256(p.read_bytes()).hexdigest() == h, f"cambió {f}"


def test_candidatas():
    c = pd.read_csv(TABLES / "step00_candidates.csv").variable
    assert not set(c) & {"hard_churn_6m", "soft_churn_3m", "value_lost_6m", "churn_excluded", "age_primary", "bureau_new_mortgage_elsewhere", "household_id"}
    assert c.is_unique
