"""QC del paso 7: K por regla, asignación a toda la base, sin edad, Σ share × tasa."""
import pandas as pd

from common import PROC, TABLES


def test_k_y_asignacion():
    s = pd.read_csv(TABLES / "step07_k_selection.csv")
    k = s.loc[s.elegido == "◀"].iloc[0]
    assert k["cluster mín %"] >= 5 and k["ARI bootstrap"] >= 0.80
    c = pd.read_parquet(PROC / "step07_clusters.parquet")
    assert len(c) == 20_000 and c.cluster.nunique() == int(k.K)


def test_perfil():
    p = pd.read_csv(TABLES / "step07_cluster_profile.csv")
    assert abs(p["% dev"].sum() - 100) < 1e-9
    assert "age" not in " ".join(p.columns)
