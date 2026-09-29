"""QC del paso 12: comparativa final completa, manifiesto con sha256 correctos, modelos anteriores intactos, documento."""
import hashlib
import json

import pandas as pd

from common import MODEL, REPORTS, TABLES


def test_manifiesto():
    m = json.loads((MODEL / "MANIFEST.json").read_text(encoding="utf-8"))
    assert m["modelos anteriores intactos"] is True
    for f, h in m["archivos"].items():
        assert hashlib.sha256((MODEL / f).read_bytes()).hexdigest() == h


def test_comparativa_y_documento():
    f = pd.read_csv(TABLES / "step12_final_comparison.csv")
    assert list(f.columns[1:]) == ["M1 · scorecard", "EBM (ML)", "A-lite", "XGBoost"]
    d = (REPORTS / "model_document.md").read_text(encoding="utf-8")
    for n in ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09", "09b", "10", "11", "12"]:
        assert f"(step{n}.md)" in d and (REPORTS / f"step{n}.md").exists()
    assert "Basilea" not in d and "IFRS" not in d
