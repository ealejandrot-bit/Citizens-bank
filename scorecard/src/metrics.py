"""Métricas de discriminación y calibración, con IC bootstrap (pasos 11–15)."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


def ks(y, p) -> float:
    o = np.argsort(-p)
    y = np.asarray(y)[o]
    cb = np.cumsum(y) / y.sum()
    cg = np.cumsum(1 - y) / (1 - y).sum()
    return float(np.max(np.abs(cb - cg)))


def all_metrics(y, p) -> dict:
    y, p = np.asarray(y, int), np.asarray(p, float)
    auc = roc_auc_score(y, p)
    return {"AUC": auc, "Gini": 2 * auc - 1, "PR-AUC": average_precision_score(y, p), "KS": ks(y, p),
            "Brier": brier_score_loss(y, p), "p media": p.mean(), "tasa observada": y.mean()}


def top_capture(y, p, w=None, q=0.10) -> float:
    """Captura de eventos (o de valor w) en el top q por score de riesgo."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    w = np.ones_like(y) if w is None else np.asarray(w, float)
    n = int(np.ceil(q * len(y)))
    top = np.argsort(-p, kind="stable")[:n]
    return float((y[top] * w[top]).sum() / (y * w).sum())


def bootstrap(y, preds: dict, fn, n=500, seed=42, strata=None) -> dict:
    """Bootstrap pareado: mismas réplicas para todos los modelos. Devuelve {modelo: array de n valores}."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y)
    idx_all = np.arange(len(y))
    groups = [idx_all] if strata is None else [idx_all[np.asarray(strata) == s] for s in np.unique(strata)]
    out = {k: np.empty(n) for k in preds}
    for b in range(n):
        bi = np.concatenate([rng.choice(g, len(g), replace=True) for g in groups])
        for k, p in preds.items():
            out[k][b] = fn(y[bi], np.asarray(p)[bi], bi)
    return out


def ci(a, level=0.95) -> tuple[float, float]:
    lo, hi = np.percentile(a, [100 * (1 - level) / 2, 100 * (1 + level) / 2])
    return float(lo), float(hi)
