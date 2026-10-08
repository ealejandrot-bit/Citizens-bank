"""Costos de transacción: comisión IBKR Pro fija y slippage por acción."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostModel:
    comision_por_accion: float = 0.005
    comision_minima: float = 1.00
    comision_maxima_pct: float = 0.01
    slippage: float = 0.01          # USD por acción por lado
    conversion_mxn_usd: float = 0.0  # costo fijo único al inicio
    datos_mensual: float = 0.0       # USD por mes

    @classmethod
    def from_config(cls, cfg: dict, intradia: bool) -> "CostModel":
        c = cfg["costos"]
        return cls(
            comision_por_accion=float(c["comision_por_accion"]),
            comision_minima=float(c["comision_minima"]),
            comision_maxima_pct=float(c["comision_maxima_pct"]),
            slippage=float(c["slippage_intradia"] if intradia else c["slippage_diario"]),
            conversion_mxn_usd=float(c.get("conversion_mxn_usd", 0.0)),
            datos_mensual=float(c.get("datos_mensual", 0.0)),
        )

    def commission(self, qty: float, price: float) -> float:
        """Comisión por orden: 0.005/acción, mínimo 1.00, tope 1% del valor (el tope manda)."""
        qty = abs(qty)
        if qty == 0:
            return 0.0
        base = max(qty * self.comision_por_accion, self.comision_minima)
        cap = self.comision_maxima_pct * qty * price
        return min(base, cap)

    def fill_price(self, price: float, side: int) -> float:
        """Precio ejecutado con slippage: compra (+1) más caro, venta (-1) más barato."""
        return price + side * self.slippage
