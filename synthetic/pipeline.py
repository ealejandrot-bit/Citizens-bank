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
from .transfers import build_step3
from .investments import build_step4
from .relationship import build_step5
from .banker import build_step6
from .complaints import build_step7


def build(cfg: dict, seed: int | None = None, upto: int = 2) -> dict:
    seeds = SeedManager(cfg["master_seed"] if seed is None else seed)
    out = {"seeds": seeds}
    out["base"], out["truth"] = build_population(cfg, seeds)
    if upto >= 1:
        out["exit"] = draw_exit_move(out["base"], out["truth"], cfg, seeds)
        out["f1"], out["sim1"] = build_step1(out["base"], out["truth"], cfg, seeds, out["exit"])
    if upto >= 2:
        out["f2"], out["sim2"] = build_step2(out["base"], out["truth"], out["sim1"], cfg, seeds, out["exit"])
    if upto >= 3:
        out["f3"], out["sim3"] = build_step3(out["base"], out["truth"], cfg, seeds, out["exit"], out["sim1"], out["sim2"])
    if upto >= 4:
        out["f4"], out["sim4"] = build_step4(out["base"], out["truth"], cfg, seeds, out["exit"], out["sim1"], out["sim3"])
    if upto >= 5:
        out["f5"], out["sim5"] = build_step5(out["base"], out["truth"], cfg, seeds, out["exit"], out["sim1"])
    if upto >= 6:
        out["f6"], out["sim6"] = build_step6(out["base"], out["truth"], cfg, seeds, out["exit"])
    if upto >= 7:
        out["f7"], out["sim7"] = build_step7(out["base"], out["truth"], cfg, seeds, out["exit"])
    return out
