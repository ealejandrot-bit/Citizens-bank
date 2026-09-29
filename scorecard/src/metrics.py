"""Métricas de discriminación y calibración, con IC bootstrap (pasos 11–15)."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score, roc_curve


def ks(y, p) -> float:
    """KS = máx(TPR − FPR) sobre umbrales únicos (correcto con empates)."""
    fpr, tpr, _ = roc_curve(np.asarray(y, int), np.asarray(p, float))
    return float(np.max(tpr - fpr))


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


def top_capture_ties(y, p, w=None, q=0.10) -> float:
    """Captura esperada en el top q con desempate aleatorio: el grupo empatado en el corte aporta su parte proporcional."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    w = np.ones_like(y) if w is None else np.asarray(w, float)
    n = q * len(y)
    o = np.argsort(-p, kind="stable")
    ps = p[o]
    v = ps[int(np.ceil(n)) - 1]
    above, equal = p > v, p == v
    frac = (n - above.sum()) / equal.sum()
    num = (y * w)[above].sum() + frac * (y * w)[equal].sum()
    return float(num / (y * w).sum())


def decile_table(y, p, w=None, lv=None, n=10) -> "pd.DataFrame":
    import pandas as pd
    y, p = np.asarray(y, float), np.asarray(p, float)
    w = np.ones_like(y) if w is None else np.asarray(w, float)
    lv = np.zeros_like(y) if lv is None else np.asarray(lv, float)
    r = pd.Series(p).rank(method="first", ascending=False)
    d = np.ceil(r / len(p) * n).astype(int).to_numpy()
    df = pd.DataFrame({"decil": d, "y": y, "w": w, "yw": y * w, "lv": lv * y})
    t = df.groupby("decil").agg(hogares=("y", "size"), eventos=("y", "sum"), valor=("w", "sum"), valor_churners=("yw", "sum"), value_lost=("lv", "sum"))
    t["tasa %"] = 100 * t.eventos / t.hogares
    t["lift"] = t["tasa %"] / (100 * y.mean())
    t["captura acumulada %"] = 100 * t.eventos.cumsum() / y.sum()
    t["captura valor acumulada %"] = 100 * t.valor_churners.cumsum() / (y * w).sum()
    t["captura value_lost acumulada %"] = 100 * t.value_lost.cumsum() / max((lv * y).sum(), 1e-9)
    return t.reset_index()
