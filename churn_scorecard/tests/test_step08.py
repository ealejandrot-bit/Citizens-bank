"""QC del paso 8: matrices completas, pares con decisión, PCA solo diagnóstico."""
import pandas as pd

from common import TABLES, candidates


def test_matrices():
    for n in ("step08_spearman", "step08_pearson"):
        m = pd.read_csv(TABLES / f"{n}.csv").set_index("variable")
        assert set(m.index) == set(candidates(include_composites=True))


def test_pares():
    p = pd.read_csv(TABLES / "step08_pairs.csv")
    assert ((p.Spearman.abs() > 0.6) | (p.Pearson.abs() > 0.6)).all()
    assert p["decisión"].notna().all() and (p["mayor IV"].isin(p["var A"]) | p["mayor IV"].isin(p["var B"])).all()


def test_pca_diagnostico():
    b = pd.read_csv(TABLES / "step08_pca_blocks.csv")
    assert set(b.bloque) == {"depósitos", "salidas de AUM", "externalización"}
