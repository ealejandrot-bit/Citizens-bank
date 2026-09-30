"""QC de la fase 12: base + Σ puntos = score del lookup, recorte al rango, escala maestra completa, completeness acotado."""
import numpy as np
import pandas as pd

from config import P, get


def test_rango_y_escala():
    s = pd.read_parquet(P.processed / "scores_p12.parquet")
    for m in ("EBM", "NAM"):
        assert s[f"score_{m}"].between(get("scorecard.score_min"), get("scorecard.score_max")).all()
        ms = pd.read_csv(P.out(12) / f"master_scale_{m}.csv")
        assert ms.hogares.sum() == (s.split == "test").sum() and abs(ms["% hogares"].sum() - 100) < 1e-9


def test_completeness():
    r = pd.read_csv(P.out(12) / "scorecard_summary.csv").set_index("modelo")
    assert r.loc["EBM", "residual: máx |r|"] <= (58 + 1) / 2 and r.loc["EBM", "corr(score exacto, lookup)"] > 0.99
    assert r.loc["NAM", "corr(score exacto, lookup)"] > 0.99
