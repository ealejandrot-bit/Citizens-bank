"""Entrenamiento del NAM monótono: BCE, AdamW, early stopping en un 15% interno del train (estratificado), ensamble de
N semillas (promedio de logits). Devuelve los modelos, el transformador de entradas y la curva de entrenamiento."""
from __future__ import annotations

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import average_precision_score
from sklearn.model_selection import train_test_split

from .model import MonotoneNAM, QuantileInput

torch.set_num_threads(4)


def fit_one(U, M, y, signs, cfg, seed):
    torch.manual_seed(seed)
    np.random.seed(seed)
    idx = np.arange(len(y))
    tr, es = train_test_split(idx, test_size=0.15, stratify=y, random_state=seed)
    Ut, Mt, yt = (torch.tensor(a[tr]) for a in (U, M, y.astype(np.float32)))
    Ue, Me, ye = (torch.tensor(a[es]) for a in (U, M, y.astype(np.float32)))
    model = MonotoneNAM(signs, cfg["hidden_units"], cfg["dropout"])
    with torch.no_grad():
        model.bias.fill_(float(np.log(yt.mean() / (1 - yt.mean()))))
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["learning_rate"], weight_decay=cfg["weight_decay"])
    lossf = torch.nn.BCEWithLogitsLoss()
    best, best_state, wait, curve = np.inf, None, 0, []
    g = torch.Generator().manual_seed(seed)
    for ep in range(cfg["epochs_max"]):
        model.train()
        perm = torch.randperm(len(yt), generator=g)
        tl = []
        for i in range(0, len(yt), cfg["batch_size"]):
            b = perm[i:i + cfg["batch_size"]]
            opt.zero_grad()
            loss = lossf(model(Ut[b], Mt[b]), yt[b])
            loss.backward()
            opt.step()
            tl.append(loss.item() * len(b))
        model.eval()
        with torch.no_grad():
            le = model(Ue, Me)
            el = lossf(le, ye).item()
            ap = average_precision_score(ye.numpy(), le.numpy())
        curve.append({"semilla": seed, "época": ep + 1, "pérdida train": sum(tl) / len(yt), "pérdida early-stop": el, "PR-AUC early-stop": ap})
        if el < best - 1e-5:
            best, wait = el, 0
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
        else:
            wait += 1
            if wait >= cfg["patience"]:
                break
    model.load_state_dict(best_state)
    model.eval()
    return model, curve


class NAMEnsemble:
    def __init__(self, signs, cfg, seed):
        self.signs, self.cfg, self.seed = signs, cfg, seed

    def fit(self, X: np.ndarray, y: np.ndarray) -> "NAMEnsemble":
        self.qi = QuantileInput().fit(X)
        U, M = self.qi.transform(X)
        self.models, curves = [], []
        for k in range(self.cfg["ensemble_members"]):
            m, c = fit_one(U, M, y, self.signs, self.cfg, self.seed + k)
            self.models.append(m)
            curves += c
        self.curve = pd.DataFrame(curves)
        return self

    def logit(self, X: np.ndarray) -> np.ndarray:
        U, M = self.qi.transform(X)
        U, M = torch.tensor(U), torch.tensor(M)
        with torch.no_grad():
            return np.mean([m(U, M).numpy() for m in self.models], axis=0)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-self.logit(X)))

    def contributions(self, X: np.ndarray) -> np.ndarray:
        U, M = self.qi.transform(X)
        U, M = torch.tensor(U), torch.tensor(M)
        with torch.no_grad():
            return np.mean([m.contributions(U, M).numpy() for m in self.models], axis=0)

    def shape_grid(self, j: int, n: int = 201) -> np.ndarray:
        """Función de forma s_j·g_j de la variable j en una grilla de u ∈ [0, 1], por miembro (filas) del ensamble."""
        u = torch.linspace(0, 1, n)
        with torch.no_grad():
            return np.stack([m.nets[j].shape(u).numpy() for m in self.models])
