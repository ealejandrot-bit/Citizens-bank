"""Métricas de poder predictivo: WoE / IV (como las usaría el scorecard)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def woe_table(x: pd.Series, y: pd.Series, bins: int = 10, mass_point: float = 0.05) -> pd.DataFrame:
    """Tramos ordenados por valor: cada masa puntual (valor con > 5% de los no nulos, p. ej. el 0
    de una variable hurdle) va en su propio tramo; el resto por cuantiles; más un tramo NULL.
    Suavizado 0.5 por celda. El índice empieza con el número de orden del tramo."""
    x = pd.Series(np.asarray(x, dtype=float))
    y = pd.Series(np.asarray(y, dtype=int))
    b = pd.Series("NULL", index=x.index, dtype=object)
    nn = x.notna()
    if nn.sum() > 0:
        vc = x[nn].value_counts(normalize=True)
        masses = sorted(vc[vc > mass_point].index)
        rest = nn & ~x.isin(masses)
        n_q = max(1, bins - len(masses))
        q = pd.qcut(x[rest].rank(method="first"), n_q, labels=False) if rest.sum() >= n_q else pd.Series(0, index=x[rest].index)
        edges = x[rest].groupby(q).agg(["min", "max"])
        # Orden global por valor: tramos de cuantiles y masas puntuales intercalados.
        keys = [(edges.loc[k, "min"], f"[{edges.loc[k, 'min']:.4g}, {edges.loc[k, 'max']:.4g}]", ("q", k)) for k in edges.index]
        keys += [(m, f"= {m:.4g}", ("m", m)) for m in masses]
        keys.sort(key=lambda t: t[0])
        label = {key: f"{i:02d} {lab}" for i, (_, lab, key) in enumerate(keys)}
        b[rest] = q.map(lambda k: label[("q", k)])
        for m in masses:
            b[nn & (x == m)] = label[("m", m)]
    t = pd.crosstab(b, y).reindex(columns=[0, 1], fill_value=0)
    t.columns = ["no_evento", "evento"]
    good = (t["no_evento"] + 0.5) / (t["no_evento"].sum() + 0.5 * len(t))
    bad = (t["evento"] + 0.5) / (t["evento"].sum() + 0.5 * len(t))
    t["tasa_evento"] = t["evento"] / (t["evento"] + t["no_evento"])
    t["woe"] = np.log(bad / good)
    t["iv"] = (bad - good) * t["woe"]
    return t


def information_value(x, y, bins: int = 10) -> float:
    return float(woe_table(x, y, bins)["iv"].sum())


def cochran_armitage(t: pd.DataFrame) -> tuple[float, float]:
    """Tendencia lineal de la tasa de evento a lo largo de tramos ordenados (sin el tramo NULL).
    Devuelve (z, p unilateral para tendencia creciente)."""
    from scipy import stats
    t = t[t.index != "NULL"].sort_index()
    n = (t["evento"] + t["no_evento"]).to_numpy(float)
    r = t["evento"].to_numpy(float)
    s = np.arange(len(t), dtype=float)
    N, R = n.sum(), r.sum()
    pbar = R / N
    T = np.sum(s * (r - n * pbar))
    var = pbar * (1 - pbar) * (np.sum(n * s**2) - np.sum(n * s) ** 2 / N)
    z = T / np.sqrt(var)
    return z, stats.norm.sf(z)


def logit_wald(y: np.ndarray, X: np.ndarray, names: list[str]) -> pd.DataFrame:
    """Regresión logística por Newton-Raphson con errores estándar (Hessiano) y test de Wald."""
    from scipy import special, stats
    Xc = np.column_stack([np.ones(len(X)), X])
    b = np.zeros(Xc.shape[1])
    for _ in range(50):
        p = special.expit(Xc @ b)
        H = Xc.T @ (Xc * (p * (1 - p))[:, None])
        step = np.linalg.solve(H, Xc.T @ (y - p))
        b += step
        if np.max(np.abs(step)) < 1e-10:
            break
    se = np.sqrt(np.diag(np.linalg.inv(H)))
    z = b / se
    return pd.DataFrame({"coef": b, "se": se, "z": z, "p": 2 * stats.norm.sf(np.abs(z))},
                        index=["intercepto"] + names)
