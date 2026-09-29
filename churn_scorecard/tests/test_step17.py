"""QC del paso 17: KPIs con línea base, disparadores del SPEC, limitaciones L1–L7 y documento del modelo completo."""
import pandas as pd

from common import REPORTS, TABLES

T = lambda n: pd.read_csv(TABLES / f"{n}.csv")  # noqa: E731


def test_kpis_y_disparadores():
    k = T("step17_kpis")
    assert k["línea base [DATA]"].notna().all() and len(k) >= 10
    t = T("step17_triggers")
    assert t["condición [DEF SPEC / G3]"].str.contains("0.8–1.2").any() and t["condición [DEF SPEC / G3]"].str.contains("0.25").any()


def test_limitaciones():
    assert {f"L{i}" for i in range(1, 8)} <= set(T("step17_limitations").id)


def test_documento():
    d = (REPORTS / "model_document.md").read_text(encoding="utf-8")
    for n in range(18):
        assert f"(step{n:02d}.md)" in d
        assert (REPORTS / f"step{n:02d}.md").exists()
    assert "Basilea" not in d and "IFRS" not in d


def test_manifiesto_y_artefactos():
    import hashlib
    import json

    from common import MODEL, SCORES
    m = json.loads((MODEL / "MANIFEST.json").read_text(encoding="utf-8"))
    for f, v in m["archivos"].items():
        assert hashlib.sha256((MODEL / f).read_bytes()).hexdigest() == v["sha256"]
    for a in ("step12_lookup", "step12_master_scale_households", "step12_master_scale_rv"):
        assert (TABLES / f"{a}.csv").exists()
    assert (SCORES / "household_scores.csv").exists()
