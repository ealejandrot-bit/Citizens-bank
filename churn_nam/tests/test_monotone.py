"""Monotonía del NAM: violación = 0 en las variables duras.

1. Por construcción: redes recién creadas con pesos aleatorios (sin entrenar) son monótonas en la dirección del signo.
2. En el modelo entrenado (fase 9): funciones de forma de cada miembro y del ensamble, y ICE del modelo completo.
"""
from __future__ import annotations

import pickle

import numpy as np
import pandas as pd
import pytest
import torch

from config import P
from nam import FeatureNet

MODELS = P.out(9) / "nam_models.pkl"


@pytest.mark.parametrize("sign", [1, -1])
@pytest.mark.parametrize("seed", range(20))
def test_monotonia_por_construccion(sign, seed):
    torch.manual_seed(seed)
    net = FeatureNet(hidden=16, sign=sign, dropout=0.1).eval()
    with torch.no_grad():
        for p in (net.w, net.c, net.v):
            p.normal_(0, 3)                                # pesos crudos arbitrarios, también negativos
        g = net.shape(torch.linspace(0, 1, 501)).numpy()
    assert (np.diff(g) * sign >= -1e-9).all()


@pytest.mark.skipif(not MODELS.exists(), reason="fase 9 no ejecutada")
def test_formas_entrenadas_sin_violaciones():
    d = pickle.load(open(MODELS, "rb"))
    for t, nam in d["models"].items():
        for j, s in enumerate(d["signs"]):
            if s == 0:
                continue
            g = nam.shape_grid(j, n=1001)
            assert (np.diff(g, axis=1) * s >= -1e-9).all(), (t, d["features"][j])


@pytest.mark.skipif(not MODELS.exists(), reason="fase 9 no ejecutada")
def test_ice_modelo_completo():
    d = pickle.load(open(MODELS, "rb"))
    X = pd.read_parquet(P.processed / "X_features.parquet")[d["features"]].to_numpy(float)
    rng = np.random.default_rng(0)
    Xi = X[rng.choice(len(X), 200, replace=False)]
    for t, nam in d["models"].items():
        for j, s in enumerate(d["signs"]):
            if s == 0:
                continue
            grid = np.unique(np.nanquantile(X[:, j], np.linspace(0, 1, 41)))
            L = []
            for v in grid:
                Z = Xi.copy()
                Z[:, j] = v
                L.append(nam.logit(Z))
            assert (np.diff(np.array(L).T, axis=1) * s >= -1e-7).all(), (t, d["features"][j])
