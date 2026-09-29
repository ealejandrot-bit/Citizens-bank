"""QC de la fase 0: los 14 hechos de SPEC §2 evaluados; toda discrepancia queda marcada (no se oculta)."""
import pandas as pd

from config import P


def test_hechos_completos():
    f = pd.read_csv(P.out(0) / "facts.csv")
    assert list(f["#"]) == list(range(1, 15))
    assert f.coincide.dtype == bool and f.observado.notna().all()


def test_reporte():
    r = (P.reports / "p00.md").read_text(encoding="utf-8").splitlines()
    assert r[0].startswith("Dataset sintético, corte transversal")
