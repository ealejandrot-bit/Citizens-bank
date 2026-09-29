"""QC de p00: config detiene fases con parámetros en null; report pone la primera línea fija."""
import json

import pandas as pd
import pytest

import config
from config import HEADER, MissingParameterError, P, get, need
from report import render


def test_need_null_detiene():
    with pytest.raises(MissingParameterError, match="gate.delta_pr_auc"):
        need("gate.delta_pr_auc", fase=6)


def test_need_valor_y_clave_inexistente():
    assert need("project.seed", fase=0) == 42
    with pytest.raises(KeyError):
        get("no.existe")


def test_rutas():
    assert P.raw.exists() and P.raw.name == "client_pulse_synthetic.xlsx"


def test_report_primera_linea(tmp_path, monkeypatch):
    out = P.out(99)
    pd.DataFrame({"a": [1, 2]}).to_csv(out / "t.csv", index=False)
    (out / "k.json").write_text(json.dumps({"x": 1}), encoding="utf-8")
    rp = render(99)
    try:
        assert rp.read_text(encoding="utf-8").splitlines()[0] == HEADER
        assert HEADER.startswith("Dataset sintético, corte transversal")
    finally:
        for f in out.iterdir():
            f.unlink()
        out.rmdir()
        rp.unlink()
