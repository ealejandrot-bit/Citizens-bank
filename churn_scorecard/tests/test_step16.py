"""QC del paso 16: K en 3–4 con regla previa, arquetipos nombrados, cobertura de eventos y playbook completo."""
import pandas as pd

from common import TABLES

T = lambda n: pd.read_csv(TABLES / f"{n}.csv")  # noqa: E731


def test_k_y_tamanos():
    k = T("step16_k_selection")
    e = k[k.elegido == "◀"].iloc[0]
    assert e.K in (3, 4) and e["arquetipo mín %"] >= 10 and e["ARI bootstrap"] >= 0.80
    p = T("step16_archetype_profile")
    assert len(p) == e.K and abs(p["% eventos dev"].sum() - 100) < 1e-9 and abs(p["% eventos val"].sum() - 100) < 1e-9
    assert not p.nombre.str.startswith("arquetipo ").any()


def test_playbook_y_ews():
    pb = T("step16_playbook")
    assert len(pb) == 3 * len(T("step16_archetype_profile")) and not pb["acción"].str.contains("tras revisión").any()
    assert set(pb.loc[pb.tramo == "Crítico", "SLA"]) == {"≤ 5 días hábiles"} and set(pb.loc[pb.tramo == "Alto", "SLA"]) == {"≤ 15 días hábiles"}
    assert len(T("step16_ews")) >= 4
