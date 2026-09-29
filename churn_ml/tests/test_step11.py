"""QC del paso 11: arquetipos del M1 asignados sin reajuste, cobertura completa de eventos de val."""
import pandas as pd

from common import TABLES


def test_arquetipos():
    a = pd.read_csv(TABLES / "step11_archetypes.csv")
    assert len(a) == 3 and a["eventos val"].sum() == 803 and abs(a["% eventos"].sum() - 100) < 1e-9
    assert set(a.arquetipo) == {"relación desatendida", "salida activa a competidor", "desgaste silencioso"}
