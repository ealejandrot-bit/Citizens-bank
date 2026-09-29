"""Binning y WoE reutilizables (pasos 9–15).

Cada variable se bina con `optbinning` sobre los valores con dato ("ok"); el missing va a bins especiales
según su razón (paso 5): "no_aplica" y "sin_dato". Convención:
    WoE_b = ln(%buenos_b / %malos_b)    (WoE > 0 = menos churn que la media)
    IV    = Σ_b (%buenos_b − %malos_b) · WoE_b
Celdas con 0 buenos o 0 malos: +0.5 a ambos conteos (Laplace) para evitar ±∞.
Bins especiales con < MIN_EVENTS eventos: "sin_dato" se fusiona con "no_aplica" si existe; si el grupo
resultante sigue con < MIN_EVENTS eventos, WoE = 0 (neutral) — el dato no alcanza para estimar riesgo (D9.3).
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from optbinning import OptimalBinning

SPECIALS = ("no_aplica", "sin_dato")


def woe_iv(good: np.ndarray, bad: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    good, bad = np.asarray(good, float), np.asarray(bad, float)
    adj = (good == 0) | (bad == 0)
    g, b = np.where(adj, good + 0.5, good), np.where(adj, bad + 0.5, bad)
    pg, pb = g / g.sum(), b / b.sum()
    w = np.log(pg / pb)
    return w, (pg - pb) * w


@dataclass
class VarBinning:
    name: str
    dtype: str                         # "numerical" | "categorical"
    splits: list = field(default_factory=list)
    categories: list = field(default_factory=list)   # categorical: lista de grupos (listas de valores)
    special_map: dict = field(default_factory=dict)  # razón → etiqueta de bin especial ("no_aplica" / "sin_dato" / "missing")
    woe: dict = field(default_factory=dict)          # etiqueta de bin → WoE
    labels: list = field(default_factory=list)       # orden de bins
    neutral: set = field(default_factory=set)        # bins especiales con WoE forzado a 0

    # ── asignación de bin ─────────────────────────────────────────────────────────────
    def bin_labels(self, x: pd.Series, reason: pd.Series | None = None) -> np.ndarray:
        x = pd.Series(x).reset_index(drop=True)
        reason = pd.Series("ok", index=x.index) if reason is None else pd.Series(reason).reset_index(drop=True)
        reason = reason.where(~(x.isna() & (reason == "ok")), "sin_dato")   # NaN sin razón → sin_dato
        out = np.empty(len(x), dtype=object)
        ok = (reason == "ok").to_numpy()
        if self.dtype == "numerical":
            idx = np.searchsorted(np.asarray(self.splits, float), x[ok].to_numpy(float), side="right")
            out[ok] = [self.num_label(i) for i in idx]
        else:
            lut = {v: self.cat_label(g) for g in self.categories for v in g}
            out[ok] = [lut.get(v, self.cat_label(self.categories[0])) for v in x[ok]]
        for r in SPECIALS:
            m = (reason == r).to_numpy()
            out[m] = self.special_map.get(r, r)
        return out

    def num_label(self, i: int) -> str:
        e = [-np.inf] + list(self.splits) + [np.inf]
        return f"[{e[i]:.6g}, {e[i + 1]:.6g})"

    @staticmethod
    def cat_label(g) -> str:
        return "{" + ", ".join(str(v) for v in g) + "}"

    def transform(self, x, reason=None) -> np.ndarray:
        lab = self.bin_labels(x, reason)
        return np.array([self.woe.get(l, 0.0) for l in lab], dtype=float)

    # ── tabla de bins ─────────────────────────────────────────────────────────────────
    def table(self, x, reason, y) -> pd.DataFrame:
        lab = self.bin_labels(x, reason)
        df = pd.DataFrame({"bin": lab, "y": np.asarray(y, int)})
        t = df.groupby("bin", sort=False).agg(hogares=("y", "size"), eventos=("y", "sum"))
        t = t.reindex([l for l in self.labels if l in t.index])
        t["no_eventos"] = t.hogares - t.eventos
        w, iv = woe_iv(t.no_eventos, t.eventos)
        t["WoE"] = [0.0 if b in self.neutral else wi for b, wi in zip(t.index, w)]
        t["IV"] = [0.0 if b in self.neutral else v for b, v in zip(t.index, iv)]
        t["% hogares"] = 100 * t.hogares / t.hogares.sum()
        t["tasa %"] = 100 * t.eventos / t.hogares
        t["especial"] = [b in set(self.special_map.values()) | set(SPECIALS) for b in t.index]
        return t.reset_index()


def fit_binning(name: str, x: pd.Series, reason: pd.Series | None, y: np.ndarray, *, dtype: str,
                min_bin_size: float, min_events: int, min_event_rate_diff: float) -> VarBinning:
    x = pd.Series(x).reset_index(drop=True)
    y = np.asarray(y, int)
    reason = pd.Series("ok", index=x.index) if reason is None else pd.Series(reason).reset_index(drop=True)
    ok = (reason == "ok").to_numpy() & x.notna().to_numpy()
    # El pre-binning CART puede no encontrar cortes con muchos empates (p. ej. 87% en cero con min_prebin_size
    # = 1%). Se prueban 3 tamaños de pre-bin y se queda el de mayor IV (todas cumplen las restricciones; D9.5).
    best, best_iv = None, -1.0
    for mps in (0.01, 0.02, 0.05):
        ob = OptimalBinning(name=name, dtype=dtype, solver="cp",
                            monotonic_trend="auto_asc_desc" if dtype == "numerical" else None,
                            # el mínimo se expresa sobre la población total, no solo sobre los hogares con dato
                            min_bin_size=min(0.5, min_bin_size * len(x) / max(ok.sum(), 1)),
                            min_bin_n_event=min_events, min_event_rate_diff=min_event_rate_diff, max_n_prebins=20,
                            min_prebin_size=mps)
        ob.fit(x[ok].to_numpy(), y[ok])
        iv = float(ob.binning_table.build().loc["Totals", "IV"]) if ob.status == "OPTIMAL" else -1.0
        if iv > best_iv + 1e-9:
            best, best_iv = ob, iv
    ob = best
    vb = VarBinning(name=name, dtype=dtype)
    if dtype == "numerical":
        vb.splits = [float(s) for s in ob.splits]
        vb.labels = [vb.num_label(i) for i in range(len(vb.splits) + 1)]
    else:
        vb.categories = [list(g) for g in ob.splits] if len(ob.splits) else [sorted(x[ok].unique().tolist())]
        seen = {v for g in vb.categories for v in g}
        rest = [v for v in sorted(x[ok].unique().tolist()) if v not in seen]
        if rest:
            vb.categories.append(rest)
        vb.labels = [vb.cat_label(g) for g in vb.categories]

    # Bins especiales (D9.3)
    ev = {r: int(y[(reason == r).to_numpy()].sum()) for r in SPECIALS}
    n = {r: int((reason == r).sum()) for r in SPECIALS}
    present = [r for r in SPECIALS if n[r] > 0]
    vb.special_map = {r: r for r in present}
    if "sin_dato" in present and ev["sin_dato"] < min_events and "no_aplica" in present:
        vb.special_map["sin_dato"] = "no_aplica"
    groups = {}
    for r in present:
        groups.setdefault(vb.special_map[r], 0)
        groups[vb.special_map[r]] += ev[r]
    vb.neutral = {g for g, e in groups.items() if e < min_events}
    vb.labels += list(dict.fromkeys(vb.special_map[r] for r in present))
    t = vb.table(x, reason, y)
    vb.woe = dict(zip(t.bin, t.WoE))
    return vb


def woe_frame(df: pd.DataFrame, binnings: dict, cols: list[str]) -> pd.DataFrame:
    """Matriz WoE (una columna por variable) con los bins ajustados en desarrollo."""
    out = {}
    for c in cols:
        r = df[f"{c}__miss"] if f"{c}__miss" in df else None
        out[c] = binnings[c].transform(df[c], r)
    return pd.DataFrame(out, index=df.index)


def load_sample(out_dir, tables_dir, sample: str | None = "desarrollo") -> pd.DataFrame:
    """Matriz de features + cluster + muestra/folds; filtra por muestra si se indica."""
    X = pd.read_pickle(out_dir / "data" / "05_features.pkl").merge(pd.read_csv(out_dir / "data" / "07_clusters.csv"), on="household_id")
    split = pd.read_csv(tables_dir / "04_split.csv").drop(columns=["segment", "hard_churn_6m"])
    X = X.merge(split, on="household_id")
    return (X if sample is None else X[X.muestra == sample]).reset_index(drop=True)


def is_discrete(s: pd.Series) -> bool:
    """Binaria / conteo / ≤ 10 valores o ≥ 70% en su mínimo (regla D9.1)."""
    v = pd.Series(s).dropna()
    vals, cnt = np.unique(v, return_counts=True)
    return len(vals) <= 10 or (cnt.max() / len(v) >= 0.70 and vals[cnt.argmax()] == v.min())


def fit_project_binning(c: str, df: pd.DataFrame, y: np.ndarray, params: dict) -> VarBinning:
    """Binning con la configuración del paso 9 (para re-binnear dentro de cada fold de la CV)."""
    dtype = "categorical" if c == "cluster" else "numerical"
    mbs = 0.01 if (dtype == "categorical" or is_discrete(df[c])) else params["min_bin_pop"]
    r = df[f"{c}__miss"] if f"{c}__miss" in df else None
    return fit_binning(c, df[c], r, y, dtype=dtype, min_bin_size=mbs, min_events=params["min_bin_events"], min_event_rate_diff=0.005)
