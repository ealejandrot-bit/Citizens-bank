"""Carga config.yaml, expone rutas y parámetros, y detiene una fase que pide un parámetro en null.

Uso:
    from config import CFG, P, need
    theta = need("target.theta", fase=1)       # error claro si es null
"""
from __future__ import annotations

import os
import random
from pathlib import Path
from typing import Any

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
CFG: dict = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


class MissingParameterError(RuntimeError):
    """Un parámetro que la fase necesita está en null en config.yaml: lo decide el usuario."""


def get(key: str) -> Any:
    """Valor por clave con puntos ('gate.delta_pr_auc'). KeyError si la clave no existe."""
    node: Any = CFG
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"config.yaml no tiene la clave '{key}'")
        node = node[part]
    return node


def need(key: str, fase: int | str) -> Any:
    """Como get(), pero si el valor es null detiene la fase con un mensaje para el usuario."""
    v = get(key)
    if v is None or (isinstance(v, dict) and any(x is None for x in v.values())):
        raise MissingParameterError(
            f"La fase {fase} necesita '{key}' y está en null en config.yaml. "
            f"Es una decisión del usuario: llénalo en config.yaml y vuelve a ejecutar la fase."
        )
    return v


class _Paths:
    def __getattr__(self, name: str) -> Path:
        return (ROOT / get(f"paths.{name}")).resolve()

    def out(self, fase: int) -> Path:
        p = ROOT / get("paths.outputs") / f"p{fase:02d}"
        p.mkdir(parents=True, exist_ok=True)
        return p


P = _Paths()
SEED: int = get("project.seed")
HEADER: str = get("project.report_header")


def set_seed(seed: int = SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import torch
        torch.manual_seed(seed)
    except ImportError:
        pass
