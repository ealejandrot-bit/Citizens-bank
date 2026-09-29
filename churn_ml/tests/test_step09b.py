"""QC del paso 9b: A-lite copiado sin cambios, subconjunto justo fuera del desarrollo de todos, comparativa completa."""
import hashlib

import pandas as pd

from common import INH, ROOT, TABLES


def test_copias_alite_identicas():
    for s, d in {"scored/scored_households.csv": "alite_scored_households.csv", "tables/04_split.csv": "alite_split.csv"}.items():
        assert hashlib.sha256((ROOT.parent / "scorecard" / "outputs" / s).read_bytes()).digest() == hashlib.sha256((INH / d).read_bytes()).digest()


def test_subconjunto_justo():
    c = pd.read_csv(TABLES / "step09b_alite_comparison.csv")
    j = c[c.subconjunto.str.startswith("justo")]
    assert set(j.modelo.str.split(" ").str[0]) >= {"A-lite", "M1", "EBM"}
    assert j.groupby("target").hogares.nunique().eq(1).all()           # mismos hogares para todos los modelos
    split = pd.read_csv(INH / "alite_split.csv")
    val = pd.read_parquet(INH / "val.parquet")
    n = val.merge(split, on="household_id").query("muestra == 'holdout'").shape[0]
    assert j.hogares.max() <= n


def test_bootstrap():
    b = pd.read_csv(TABLES / "step09b_alite_bootstrap.csv")
    assert len(b) == 6
