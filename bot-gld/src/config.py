"""Carga de config.yaml y rutas del proyecto."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.yaml"
# Archivo que escribe check_connection.py cuando los 9 puntos pasan (regla 3).
CHECK_OK_PATH = ROOT / "logs" / "check_connection_ok.json"


def load_config(path: str | Path = CONFIG_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def path_in_root(rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else ROOT / p


def require_connection_check() -> dict:
    """Bloquea cualquier uso de datos reales si check_connection.py no ha pasado completo."""
    import json

    if not CHECK_OK_PATH.exists():
        raise RuntimeError(
            "check_connection.py no ha pasado completo: no se descargan datos reales ni se corre "
            "backtest con ellos (SPEC, regla 3). Ejecuta `python check_connection.py` primero."
        )
    with open(CHECK_OK_PATH, encoding="utf-8") as f:
        return json.load(f)
