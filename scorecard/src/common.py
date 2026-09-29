"""Rutas, semilla, parámetros y utilidades compartidas por los scripts 00–17.

Todo script importa desde aquí: un solo lugar para la ruta de datos, la semilla y los
parámetros del scorecard (confirmados en el paso 0).
"""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]          # scorecard/
REPO = ROOT.parent                                  # raíz del repositorio

# Fuente: solo lectura. El brief pedía ./data/client_pulse_synthetic.xlsx; en el repo la base
# está en CSV (mismo contenido, 20,000 × 62). Ver DECISIONS.md, paso 0.
DATA_PATH = Path(os.environ.get("DATA_PATH", REPO / "data" / "synthetic" / "client_pulse_synthetic.csv"))

OUT = ROOT / "outputs"
TABLES, FIGURES, MODELS, SCORED = (OUT / d for d in ("tables", "figures", "models", "scored"))

SEED = 42

# Parámetros (defaults del brief; se confirman en el paso 0)
PARAMS = {
    "target_primary": "hard_churn_6m",
    "target_secondary": "soft_churn_3m",
    "value_weight": "relationship_value",
    "holdout_frac": 0.30,
    "cv_folds": 5,
    "cv_repeats": 5,
    "n_bootstrap": 500,
    "S0": 600, "O0": 15.0, "PDO": 40,
    "critical_capacity_pct": 0.03,
    "iv_min": 0.02, "iv_suspect": 0.50, "vif_max": 5.0,
    "min_bin_pop": 0.05, "min_bin_events": 30,
    "platt_b_range": (0.8, 1.2), "psi_max": 0.10,
}

ID = "household_id"
OUTCOMES = ["hard_churn_6m", "soft_churn_3m", "value_lost_6m", "churn_excluded"]
COMPOSITES = ["multi_signal_flag", "multi_signal_count"]
FORBIDDEN = OUTCOMES + COMPOSITES + ["snapshot_date", ID]


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def load_raw() -> pd.DataFrame:
    """Lee la base fuente sin modificarla (nunca se escribe sobre DATA_PATH)."""
    if not DATA_PATH.exists():
        sys.exit(f"[QC FAIL] No existe la base en {DATA_PATH}. Indica la ruta con DATA_PATH=...")
    if DATA_PATH.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(DATA_PATH)
    return pd.read_csv(DATA_PATH)


class QC:
    """Registro de controles de calidad. `gate()` detiene la ejecución si alguno falla."""

    def __init__(self, step: str):
        self.step, self.rows = step, []

    def check(self, name: str, ok: bool, expected="", observed="", severity: str = "gate") -> bool:
        status = "PASS" if ok else ("FAIL" if severity == "gate" else "WARN")
        self.rows.append({"control": name, "esperado": str(expected), "observado": str(observed), "estado": status})
        print(f"  [{status}] {name} | esperado: {expected} | observado: {observed}")
        return ok

    def table(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)

    def gate(self) -> None:
        fails = [r for r in self.rows if r["estado"] == "FAIL"]
        n_warn = sum(r["estado"] == "WARN" for r in self.rows)
        print(f"\n[{self.step}] QC: {len(self.rows) - len(fails) - n_warn} PASS · {n_warn} WARN · {len(fails)} FAIL")
        if fails:
            sys.exit(f"[{self.step}] QC gate fallido: {', '.join(r['control'] for r in fails)}. Detente y revisa.")


def save_table(df: pd.DataFrame, name: str, index: bool = False) -> None:
    """Guarda CSV + MD con el mismo nombre en outputs/tables/."""
    TABLES.mkdir(parents=True, exist_ok=True)
    df.to_csv(TABLES / f"{name}.csv", index=index)
    (TABLES / f"{name}.md").write_text(df.to_markdown(index=index) + "\n", encoding="utf-8")
