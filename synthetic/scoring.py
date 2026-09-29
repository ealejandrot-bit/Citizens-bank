"""Scores de attrition con distintas metodologías (deck: Section 3) y su evaluación.

Metodologías:
  M0a · Reglas de negocio (deck slide 20): intención de salida, queja fuera de SLA, brecha de contacto.
  M0b · Scorecard experto (deck slide 22): puntos fijos por comportamiento, tope 100.
  M1  · Scorecard estadístico: WoE por tramos + regresión logística → puntos 0–100.
  M2  · Machine learning: Gradient Boosting (champion) y logística (challenger).
  M3  · Red neuronal: MLP sobre variables tabulares + secuencia mensual de 12 meses (depósitos y AUM
        ex-mercado). Aproximación a la LSTM del deck (requeriría PyTorch).
  Techo · probabilidad verdadera del generador (no es un modelo: marca el máximo alcanzable).

Validación: partición estratificada 70/30 con semilla derivada de la maestra. No hay out-of-time
porque la base tiene un solo corte (el panel mensual es el siguiente paso natural).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .schema import EXCEL_PRIMARY

CONTEXT = ["log_relationship_value", "tenure_years", "age_primary", "is_uhnw", "has_investments", "has_trust",
           "has_credit_anchor", "has_linked_business"]


# ---------------------------------------------------------------------------
# Datos
# ---------------------------------------------------------------------------
def model_frame(o: dict, labels: pd.DataFrame) -> tuple[pd.DataFrame, list[str], list[str]]:
    feats = pd.concat([o[f"f{k}"].drop(columns="household_id") for k in range(1, 9)], axis=1)
    cols = [c for _, c in EXCEL_PRIMARY.values() if c != "multi_signal_flag"] + ["multi_signal_count"]
    X = feats[cols].astype(float).copy()
    b = o["base"]
    X["log_relationship_value"] = np.log(b["relationship_value"])
    X["tenure_years"] = b["tenure_years"]
    X["age_primary"] = b["age_primary"]
    X["is_uhnw"] = (b["segment"] == "UHNW").astype(float)
    for c in ["has_investments", "has_trust", "has_credit_anchor", "has_linked_business"]:
        X[c] = b[c].astype(float)
    # Secuencia mensual (12 meses) para la red: log del saldo relativo al mes −12.
    s1 = o["sim1"]
    D, A, twr = s1["deposit"], np.where(s1["inv"][:, None], s1["aum"], np.nan), s1["twr"]
    seq = []
    for name, M_ in [("dep", D), ("aumx", A / twr)]:
        rel = np.log(np.maximum(M_[:, -12:], 1.0) / np.maximum(M_[:, -12:-11], 1.0))
        for j in range(12):
            X[f"seq_{name}_m{j - 11}"] = np.where(s1["avail"][:, -12:][:, j], rel[:, j], np.nan)
            seq.append(f"seq_{name}_m{j - 11}")
    X.insert(0, "household_id", b["household_id"].to_numpy())
    X = X.join(labels.drop(columns="household_id"))
    X["segment"] = b["segment"].to_numpy()
    X["p_true"] = o["truth"]["p_hard_6m"].to_numpy()
    return X, cols, seq


def split(X: pd.DataFrame, target: str, rng: np.random.Generator, test_share=0.30) -> np.ndarray:
    """Máscara de test estratificada por el target."""
    y = X[target].astype(int).to_numpy()
    test = np.zeros(len(X), bool)
    for v in (0, 1):
        idx = np.nonzero(y == v)[0]
        test[rng.choice(idx, int(round(len(idx) * test_share)), replace=False)] = True
    return test


# ---------------------------------------------------------------------------
# Scorecards
# ---------------------------------------------------------------------------
def business_rules(X: pd.DataFrame) -> np.ndarray:
    exit_intent = X["relationship_dissatisfaction_flag"] == 1
    sla = X["complaint_age_days"] > 30
    cadence = X["contact_gap_ratio"] > 2.0
    return (exit_intent | sla | cadence).astype(float).to_numpy()


EXPERT_POINTS = [  # deck slide 22 (la "desconexión digital" no existe en la base: 0 puntos)
    ("Intención de salida (Assistant)", 30, lambda X: X["relationship_dissatisfaction_flag"] == 1),
    ("Transferencias externas > 15% en 60d", 25, lambda X: X["external_transfer_pct_of_balance_60d"] > 0.15),
    ("Depósitos recurrentes detenidos o −40%", 15,
     lambda X: (X["recurring_deposit_stopped_flag"] == 1) | (X["recurring_deposit_change_pct"] <= -0.40)),
    ("Retiros grandes (redención > 20% o salida AUM > 10%)", 10,
     lambda X: (X["investment_redemption_pct"] > 0.20) | (X["aum_outflow_pct_90d"] > 0.10)),
    ("Queja fuera de SLA", 10, lambda X: X["complaint_age_days"] > 30),
    ("Brecha de contacto > 2× cadencia", 10, lambda X: X["contact_gap_ratio"] > 2.0),
    ("Cambio de banker en 6m", 10, lambda X: X["banker_change_6m_flag"] == 1),
]


def expert_scorecard(X: pd.DataFrame) -> np.ndarray:
    s = sum(p * cond(X).fillna(False).astype(float).to_numpy() for _, p, cond in EXPERT_POINTS)
    return np.minimum(s, 100.0)


class WoEScorecard:
    """Scorecard estadístico: tramos (masas puntuales + cuantiles + NULL), WoE, selección por IV y
    correlación, logística sobre WoE, y puntos escalados a 0–100."""

    def __init__(self, bins=10, min_iv=0.02, max_corr=0.80, mass=0.05):
        self.bins, self.min_iv, self.max_corr, self.mass = bins, min_iv, max_corr, mass

    def _fit_var(self, x: pd.Series, y: np.ndarray):
        nn = x.notna().to_numpy()
        vc = x[nn].value_counts(normalize=True)
        masses = sorted(vc[vc > self.mass].index)
        rest = x[nn & ~x.isin(masses).to_numpy()]
        edges = np.unique(np.quantile(rest, np.linspace(0, 1, self.bins + 1))) if len(rest) else np.array([])
        spec = {"masses": masses, "edges": edges}
        codes = self._codes(x, spec)
        tab = pd.crosstab(codes, y).reindex(columns=[0, 1], fill_value=0)
        good = (tab[0] + 0.5) / (tab[0].sum() + 0.5 * len(tab))
        bad = (tab[1] + 0.5) / (tab[1].sum() + 0.5 * len(tab))
        woe = np.log(bad / good)
        spec["woe"] = woe.to_dict()
        spec["iv"] = float(((bad - good) * woe).sum())
        spec["counts"] = tab
        return spec

    @staticmethod
    def _codes(x: pd.Series, spec) -> pd.Series:
        v = x.to_numpy(dtype=float)
        out = np.full(len(v), "NULL", dtype=object)
        nn = ~np.isnan(v)
        for m in spec["masses"]:
            out[nn & (v == m)] = f"={m:.4g}"
        rest = nn & ~np.isin(v, spec["masses"])
        if len(spec["edges"]) > 1:
            k = np.clip(np.searchsorted(spec["edges"], v[rest], side="right") - 1, 0, len(spec["edges"]) - 2)
            out[rest] = [f"[{spec['edges'][i]:.4g}, {spec['edges'][i + 1]:.4g}]" for i in k]
        elif rest.any():
            out[rest] = "otro"
        return pd.Series(out, index=x.index)

    def _woe(self, X: pd.DataFrame, var: str) -> np.ndarray:
        spec = self.specs[var]
        codes = self._codes(X[var], spec)
        return codes.map(spec["woe"]).fillna(0.0).to_numpy()

    def fit(self, X: pd.DataFrame, y: np.ndarray, cols: list[str]):
        self.specs = {c: self._fit_var(X[c], y) for c in cols}
        cand = sorted([c for c in cols if self.specs[c]["iv"] >= self.min_iv], key=lambda c: -self.specs[c]["iv"])
        W = pd.DataFrame({c: self._woe(X, c) for c in cand})
        keep = []
        for c in cand:  # correlación entre WoE: se queda la de mayor IV
            if all(abs(np.corrcoef(W[c], W[k])[0, 1]) < self.max_corr for k in keep):
                keep.append(c)
        self.vars = keep
        self.dropped_corr = [c for c in cand if c not in keep]
        self.lr = LogisticRegression(C=1.0, max_iter=2000).fit(W[keep], y)
        # Puntos: −β·WoE por tramo, desplazados para que el mínimo de cada variable sea 0; total a 0–100.
        self.points = {}
        for c, b in zip(keep, self.lr.coef_[0]):
            p = {k: b * w for k, w in self.specs[c]["woe"].items()}
            lo = min(p.values())
            self.points[c] = {k: v - lo for k, v in p.items()}
        self.max_raw = sum(max(p.values()) for p in self.points.values())
        return self

    def predict_proba(self, X):
        W = pd.DataFrame({c: self._woe(X, c) for c in self.vars})
        return self.lr.predict_proba(W)[:, 1]

    def score(self, X):
        raw = np.zeros(len(X))
        for c in self.vars:
            raw += self._codes(X[c], self.specs[c]).map(self.points[c]).fillna(0.0).to_numpy()
        return 100 * raw / self.max_raw

    def points_table(self) -> pd.DataFrame:
        rows = []
        for c in self.vars:
            for k, v in self.points[c].items():
                n = self.specs[c]["counts"].loc[k].sum() if k in self.specs[c]["counts"].index else 0
                rows.append({"variable": c, "tramo": k, "puntos (0–100)": 100 * v / self.max_raw, "n_train": n,
                             "WoE": self.specs[c]["woe"][k]})
        return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# ML y red neuronal
# ---------------------------------------------------------------------------
def fit_models(X_tr, y_tr, cols, seq, seed: int) -> dict:
    tab = cols + CONTEXT
    m = {}
    m["M2 · Gradient Boosting"] = HistGradientBoostingClassifier(
        max_iter=400, learning_rate=0.05, max_leaf_nodes=31, min_samples_leaf=40, l2_regularization=1.0,
        early_stopping=True, validation_fraction=0.15, random_state=seed).fit(X_tr[tab], y_tr)
    lin = make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(),
                        LogisticRegression(C=0.5, max_iter=3000))
    m["M2 · Logística (challenger)"] = lin.fit(X_tr[tab].clip(X_tr[tab].quantile(0.01), X_tr[tab].quantile(0.99), axis=1), y_tr)
    mlp = make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler(),
                        MLPClassifier(hidden_layer_sizes=(64, 32), alpha=1e-3, learning_rate_init=1e-3, max_iter=300,
                                      early_stopping=True, validation_fraction=0.15, n_iter_no_change=15, random_state=seed))
    m["M3 · Red neuronal (tabular + secuencia)"] = mlp.fit(
        X_tr[tab + seq].clip(X_tr[tab + seq].quantile(0.01), X_tr[tab + seq].quantile(0.99), axis=1), y_tr)
    m["_tab"], m["_seq"] = tab, seq
    m["_clip"] = (X_tr[tab + seq].quantile(0.01), X_tr[tab + seq].quantile(0.99))
    return m


def predict(models, X) -> dict[str, np.ndarray]:
    tab, seq = models["_tab"], models["_seq"]
    lo, hi = models["_clip"]
    Xc = X[tab + seq].clip(lo, hi, axis=1)
    return {"M2 · Gradient Boosting": models["M2 · Gradient Boosting"].predict_proba(X[tab])[:, 1],
            "M2 · Logística (challenger)": models["M2 · Logística (challenger)"].predict_proba(Xc[tab])[:, 1],
            "M3 · Red neuronal (tabular + secuencia)": models["M3 · Red neuronal (tabular + secuencia)"].predict_proba(Xc)[:, 1]}


# ---------------------------------------------------------------------------
# Métricas
# ---------------------------------------------------------------------------
def ks_stat(y, s):
    o = np.argsort(-s)
    yy = y[o]
    tpr = np.cumsum(yy) / yy.sum()
    fpr = np.cumsum(1 - yy) / (1 - yy).sum()
    return float(np.max(np.abs(tpr - fpr)))


def top_k(y, s, value, frac):
    k = int(round(len(y) * frac))
    o = np.argsort(-s + 1e-12 * np.arange(len(s)))[:k]  # desempate estable
    return {"precisión": y[o].mean(), "recall": y[o].sum() / y.sum(), "lift": y[o].mean() / y.mean(),
            "captura AUM": value[o].sum() / value.sum()}


def evaluate(y, s, value, seg, prob=None) -> dict:
    r = {"AUC": roc_auc_score(y, s)}
    r["Gini"] = 2 * r["AUC"] - 1
    r["KS"] = ks_stat(y, s)
    for f in (0.05, 0.10):
        t = top_k(y, s, value, f)
        for k, v in t.items():
            r[f"{k} top {int(f * 100)}%"] = v
    for sg in ("HNW", "UHNW"):
        m = seg == sg
        r[f"AUC {sg}"] = roc_auc_score(y[m], s[m]) if y[m].sum() > 0 else np.nan
    if prob is not None:
        r["prob. media"] = prob.mean()
        r["churn observado"] = y.mean()
        r["Brier"] = brier_score_loss(y, prob)
    return r


def calibration_deciles(y, prob) -> pd.DataFrame:
    q = pd.qcut(pd.Series(prob).rank(method="first"), 10, labels=range(1, 11))
    return pd.DataFrame({"prob. media": pd.Series(prob).groupby(q).mean(), "churn observado": pd.Series(y).groupby(q).mean(),
                         "n": pd.Series(y).groupby(q).size()})


def drivers(model, X, y, cols, seed) -> pd.DataFrame:
    pi = permutation_importance(model, X[cols], y, scoring="roc_auc", n_repeats=3, random_state=seed, n_jobs=1)
    return pd.DataFrame({"caída de AUC al permutar": pi.importances_mean, "d.e.": pi.importances_std},
                        index=cols).sort_values("caída de AUC al permutar", ascending=False)


def bootstrap(y, scores: dict[str, np.ndarray], value, rng: np.random.Generator, B=200, ref=None) -> pd.DataFrame:
    """IC 95% por bootstrap pareado (mismas remuestras para todos los modelos) de AUC y captura de AUM
    top 10%, y diferencia de AUC contra el modelo de referencia."""
    n = len(y)
    aucs = {k: [] for k in scores}
    caps = {k: [] for k in scores}
    for _ in range(B):
        i = rng.integers(0, n, n)
        if y[i].sum() == 0:
            continue
        for k, s in scores.items():
            aucs[k].append(roc_auc_score(y[i], s[i]))
            caps[k].append(top_k(y[i], s[i], value[i], 0.10)["captura AUM"])
    rows = {}
    for k in scores:
        a, c = np.array(aucs[k]), np.array(caps[k])
        r = {"AUC p2.5": np.quantile(a, 0.025), "AUC p97.5": np.quantile(a, 0.975),
             "captura AUM p2.5": np.quantile(c, 0.025), "captura AUM p97.5": np.quantile(c, 0.975)}
        if ref is not None and k != ref:
            d = a - np.array(aucs[ref])
            r[f"Δ AUC vs {ref.split('·')[0].strip()}"] = d.mean()
            r["Δ p2.5"], r["Δ p97.5"] = np.quantile(d, 0.025), np.quantile(d, 0.975)
            r["¿diferencia real?"] = "sí" if (np.quantile(d, 0.025) > 0 or np.quantile(d, 0.975) < 0) else "no"
        rows[k] = r
    return pd.DataFrame(rows).T
