"""QC de la fase 10: el test se abrió una sola vez (guarda activa), gate evaluado con los criterios pre-registrados."""
import json
import subprocess
import sys

from config import P, ROOT, get


def test_guarda_no_reabre():
    r = subprocess.run([sys.executable, str(ROOT / "src" / "p10_gate.py")], capture_output=True, text=True, cwd=ROOT)
    assert r.returncode != 0 and "ya fue abierto" in (r.stderr + r.stdout)


def test_decision_segun_gate():
    d = json.load(open(P.out(10) / "decision.json"))
    c = d["criterios"]
    assert c["ΔPR-AUC ≥ 0.03"] == (d["ΔPR-AUC"] >= get("gate.delta_pr_auc"))
    assert c["IC95 Δlift@5% inf > 0"] == (d["Δlift@5% IC95"][0] > 0)
    assert d["decisión"].startswith("NAM reemplaza") == all(c.values())
