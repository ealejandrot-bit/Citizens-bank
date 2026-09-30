"""Neural Additive Model monótono.

logit(p) = β₀ + Σ_j f_j(x_j), con una subred por variable:
    f_j(x) = m_j · s_j · g_j(u_j)  +  (1 − m_j) · b_j^miss
  u_j ∈ [0, 1] = transformación por cuantiles de x_j (ajustada en train; monótona creciente, preserva el orden);
  m_j = 1 si x_j tiene dato, 0 si falta (no aplica / sin dato): el faltante recibe un valor propio aprendido b_j^miss,
        sin imputar;
  g_j(u) = Σ_k v_k · tanh(w_k u + c_k) + d.
Monotonía dura (signo s_j = ±1): w_k = softplus(ŵ_k) ≥ 0 y v_k = softplus(v̂_k) ≥ 0 ⟹ g_j no decreciente ⟹ s_j·g_j
monótona en la dirección del signo, por construcción (violación = 0). Variables libres: w y v sin restricción, s_j = 1.
El dropout multiplica activaciones por factores ≥ 0, así que no rompe la monotonía; en evaluación no se aplica.
"""
from __future__ import annotations

import numpy as np
import torch
from torch import nn
from torch.nn import functional as Fn


class FeatureNet(nn.Module):
    def __init__(self, hidden: int, sign: int, dropout: float):
        super().__init__()
        self.sign = sign                                  # +1, −1 (duras) o 0 (libre)
        self.w = nn.Parameter(torch.randn(hidden) * 0.5)
        self.c = nn.Parameter(torch.randn(hidden) * 0.5)
        self.v = nn.Parameter(torch.randn(hidden) * 0.1)
        self.d = nn.Parameter(torch.zeros(1))
        self.b_miss = nn.Parameter(torch.zeros(1))
        self.drop = nn.Dropout(dropout)

    def shape(self, u: torch.Tensor) -> torch.Tensor:
        """g_j(u) con la dirección ya aplicada (s_j · g_j para duras)."""
        if self.sign != 0:
            w, v = Fn.softplus(self.w), Fn.softplus(self.v)
        else:
            w, v = self.w, self.v
        h = self.drop(torch.tanh(u.unsqueeze(-1) * w + self.c))
        g = h @ v + self.d
        return g * (self.sign if self.sign != 0 else 1)

    def forward(self, u: torch.Tensor, m: torch.Tensor) -> torch.Tensor:
        return m * self.shape(torch.nan_to_num(u, nan=0.0)) + (1 - m) * self.b_miss


class MonotoneNAM(nn.Module):
    def __init__(self, signs: list[int], hidden: int, dropout: float):
        super().__init__()
        self.nets = nn.ModuleList([FeatureNet(hidden, s, dropout) for s in signs])
        self.bias = nn.Parameter(torch.zeros(1))

    def contributions(self, U: torch.Tensor, M: torch.Tensor) -> torch.Tensor:
        return torch.stack([net(U[:, j], M[:, j]) for j, net in enumerate(self.nets)], dim=1)

    def forward(self, U: torch.Tensor, M: torch.Tensor) -> torch.Tensor:
        return self.bias + self.contributions(U, M).sum(1)


class QuantileInput:
    """Transformación por cuantiles ajustada en train: u = rango empírico en [0, 1]; NaN → máscara 0."""

    def __init__(self, n_q: int = 1001):
        self.n_q = n_q

    def fit(self, X: np.ndarray) -> "QuantileInput":
        self.q = [np.unique(np.nanquantile(X[:, j], np.linspace(0, 1, self.n_q))) if np.isfinite(X[:, j]).any() else np.array([0.0]) for j in range(X.shape[1])]
        return self

    def transform(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        U = np.zeros_like(X, dtype=np.float32)
        M = np.isfinite(X).astype(np.float32)
        for j, q in enumerate(self.q):
            x = X[:, j]
            u = np.interp(x, q, np.linspace(0, 1, len(q))) if len(q) > 1 else np.zeros_like(x)
            U[:, j] = np.where(M[:, j] > 0, u, 0.0)
        return U, M
