"""Orden de construcción de la base: un solo lugar para scripts y tests.

Los flujos de semilla se piden por nombre, así que el orden no altera los valores; aun
así se centraliza para que todos construyan exactamente lo mismo.
"""
from __future__ import annotations

from .balances import build_step1
from .exit_events import draw_exit_move
from .population import build_population
from .recurring import build_step2
from .seeds import SeedManager


def build(cfg: dict, seed: int | None = None, upto: int = 2) -> dict:
    seeds = SeedManager(cfg["master_seed"] if seed is None else seed)
    out = {"seeds": seeds}
    out["base"], out["truth"] = build_population(cfg, seeds)
    if upto >= 1:
        out["exit"] = draw_exit_move(out["base"], out["truth"], cfg, seeds)
        out["f1"], out["sim1"] = build_step1(out["base"], out["truth"], cfg, seeds, out["exit"])
    if upto >= 2:
        out["f2"], out["sim2"] = build_step2(out["base"], out["truth"], out["sim1"], cfg, seeds, out["exit"])
    return out
