"""Gestión de semillas: un flujo aleatorio independiente por componente.

Reglas (ver docs/decisiones.md, D-01):
  * Nunca se usa np.random.seed() global ni random.seed().
  * Nunca se usa hash() de Python (está salado por proceso -> no reproducible).
  * Cada componente (población, latentes, target, cada variable) pide su propio
    generador por NOMBRE. El generador depende solo de (semilla maestra, nombre),
    no del orden en que se construyen los componentes. Así, agregar, quitar o
    reordenar variables en pasos futuros NO cambia los valores ya generados.
"""
from __future__ import annotations

import hashlib

import numpy as np


def _stable_key(name: str) -> tuple[int, ...]:
    """Convierte un nombre en una spawn_key estable (SHA-256, 4 palabras de 32 bits)."""
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    return tuple(int.from_bytes(digest[i : i + 4], "little") for i in range(0, 16, 4))


class SeedManager:
    """Entrega generadores numpy independientes y reproducibles por nombre."""

    def __init__(self, master_seed: int):
        if not isinstance(master_seed, int) or master_seed < 0:
            raise ValueError("master_seed debe ser un entero >= 0")
        self.master_seed = master_seed
        self._issued: dict[str, tuple[int, ...]] = {}

    def rng(self, name: str) -> np.random.Generator:
        """Generador para el componente `name`.

        Pedir dos veces el mismo nombre es un error: dos componentes compartiendo
        flujo quedarían correlacionados de forma accidental.
        """
        if name in self._issued:
            raise KeyError(f"El flujo '{name}' ya fue entregado; usa un nombre único.")
        key = _stable_key(name)
        if key in self._issued.values():  # colisión SHA-256: prácticamente imposible
            raise RuntimeError(f"Colisión de spawn_key para '{name}'")
        self._issued[name] = key
        ss = np.random.SeedSequence(entropy=self.master_seed, spawn_key=key)
        return np.random.Generator(np.random.PCG64(ss))

    @property
    def issued(self) -> list[str]:
        """Nombres de flujos entregados (para auditar en el manifiesto)."""
        return sorted(self._issued)
