"""UHNWI Churn Propensity Scorecard: target económico, binning monótono, WoE, selección, logística,
escalamiento de puntos (S0 / O0 / PDO), tramos, overrides, reason codes, calibración y estabilidad.

Convenciones (fijas en todo el módulo):
  * y = 1 es churn ("malo"); bueno = 1 − y.
  * WoE = ln(%buenos / %malos): WoE < 0 significa más riesgo que el promedio.
  * La logística modela ln(odds buenos) = β0 + Σ βj·WoEj, así que todos los βj deben ser > 0.
  * Score = Offset + Factor·ln(odds buenos): mayor score = menor churn. El score son puntos,
    no una probabilidad; la probabilidad calibrada sale de la capa de calibración.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy import special, stats
from sklearn.cluster import KMeans
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import adjusted_rand_score, average_precision_score, roc_auc_score, silhouette_score
from sklearn.model_selection import StratifiedKFold
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings("ignore", module="optbinning")

# ---------------------------------------------------------------------------
# Parámetros del escenario [SINT] (prompt) y del target
# ---------------------------------------------------------------------------
S0, O0, PDO = 600.0, 20.0, 40.0
FACTOR = PDO / np.log(2)
OFFSET = S0 - FACTOR * np.log(O0)
ECON_THRESHOLD = 0.25          # salida neta ex-mercado ≥ 25% en (T0, T0+6m]
INDET_LOW = 0.10               # 10% ≤ salida < 25% → indeterminado
SENSITIVITY = [0.20, 0.25, 0.35, 0.50]
MIN_TENURE_YEARS = 1.0
MIN_BIN_SHARE, MIN_BIN_EVENTS = 0.05, 30
MAX_PVALUE = 0.05             # bins contiguos deben diferir en tasa (z-test, p < 0.05): evita WoE de ruido
BANKS_PER_BANKER = {"HNW": 60, "UHNW": 25}   # config/params.yaml → step6.book_size
CRITICAL_PER_BANKER_MONTH = 2

# Diccionario analítico: dimensión, dirección esperada del riesgo ("+" = más valor, más churn),
# ventana y significado de negocio. El signo es hipótesis previa, no resultado.
VARS: dict[str, tuple[str, str, str, str]] = {
    "aum_outflow_pct_90d": ("Salida de activos", "+", "90d", "Retiros netos de inversión ÷ AUM"),
    "investment_redemption_pct": ("Salida de activos", "+", "90d", "Redenciones ÷ AUM"),
    "positions_liquidated_pct": ("Salida de activos", "+", "90d", "Posiciones liquidadas ÷ AUM"),
    "outflow_vs_baseline_pct": ("Salida de activos", "+", "90d vs 24m", "Salidas vs. baseline propio"),
    "fixed_income_maturity_not_reinvested": ("Salida de activos", "+", "90d", "Vencimientos RF no reinvertidos"),
    "cash_pct_of_portfolio_chg": ("Salida de activos", "+", "90d", "Δ % cash del portafolio (pre-transferencia)"),
    "aum_vs_baseline_pct": ("Deterioro de AUM", "−", "t vs meses −6..−1", "AUM ex-mercado vs. baseline"),
    "deposit_balance_change_pct_90d": ("Deterioro de AUM", "−", "3m vs 3m previos", "Δ saldo de depósitos"),
    "deposit_balance_vs_6m_avg_pct": ("Deterioro de AUM", "−", "1m vs 6m", "Depósitos vs. media 6m"),
    "net_deposit_flow_pct_90d": ("Deterioro de AUM", "−", "90d", "Flujo neto de depósitos ÷ saldo"),
    "external_transfer_pct_of_balance_60d": ("Externalización", "+", "60d", "Transferencias externas ÷ saldo"),
    "new_external_destinations_90d": ("Externalización", "+", "90d", "Nuevos destinos externos"),
    "transfer_to_competitor_pct_90d": ("Externalización", "+", "90d", "Transferencias a bancos competidores ÷ saldo"),
    "external_transfer_acceleration": ("Externalización", "+", "30d vs 90d", "Aceleración de transferencias externas"),
    "net_external_flow_pct_90d": ("Externalización", "−", "90d", "Flujo externo neto (entradas − salidas) ÷ saldo"),
    "external_destination_concentration": ("Externalización", "+", "90d", "Concentración (HHI) de destinos externos"),
    "salary_deposit_stopped_flag": ("Banco principal", "+", "45d", "Nómina detenida"),
    "recurring_deposit_stopped_flag": ("Banco principal", "+", "45d", "Depósito recurrente detenido"),
    "recurring_deposit_change_pct": ("Banco principal", "−", "90d", "Δ monto de depósitos recurrentes"),
    "pension_deposit_stopped_flag": ("Banco principal", "+", "45d", "Pensión detenida"),
    "business_payroll_stopped_flag": ("Banco principal", "+", "45d", "Nómina del negocio detenida"),
    "products_closed_180d": ("Pérdida de productos", "+", "180d", "Productos cerrados"),
    "accounts_closed_90d": ("Pérdida de productos", "+", "90d", "Cuentas cerradas"),
    "share_of_wallet": ("Pérdida de productos", "−", "t", "Share of wallet estimado"),
    "share_of_wallet_change": ("Pérdida de productos", "−", "6m", "Δ share of wallet"),
    "complaint_escalated_flag": ("Fricción de servicio", "+", "180d", "Queja escalada"),
    "complaint_age_days": ("Fricción de servicio", "+", "t", "Antigüedad de la queja abierta"),
    "repeat_complaint_flag": ("Fricción de servicio", "+", "180d", "Queja repetida"),
    "relationship_dissatisfaction_flag": ("Fricción de servicio", "+", "90d", "Insatisfacción / intención de salida"),
    "return_vs_benchmark": ("Fricción de servicio", "−", "12m", "Rendimiento vs. benchmark (valor percibido)"),
    "banker_change_6m_flag": ("Relación con banquero", "+", "6m", "Cambio de banquero"),
    "contact_gap_ratio": ("Relación con banquero", "+", "t", "Días sin contacto ÷ cadencia"),
    "client_reply_rate": ("Relación con banquero", "−", "180d", "Tasa de respuesta del cliente"),
    "meetings_cancelled_by_client": ("Relación con banquero", "+", "180d", "Reuniones canceladas por el cliente"),
    "trustee_change_flag": ("Evento de vida", "+", "12m", "Cambio de trustee (sucesión)"),
    "bureau_new_mortgage_elsewhere": ("Crédito / saldos", "+", "6m", "Hipoteca nueva en otro acreedor (buró)"),
    "multi_signal_count": ("Compuesta", "+", "t", "Nº de grupos en alerta (umbrales Excel)"),
    # Estructurales (no son comportamiento): candidatas a segmentación / contexto.
    "log_relationship_value": ("Estructural", "·", "t", "ln(relationship value)"),
    "tenure_years": ("Estructural", "−", "t", "Antigüedad"),
    "has_credit_anchor": ("Crédito / saldos", "−", "t", "Crédito ancla con el banco"),
    "has_trust": ("Estructural", "·", "t", "Tiene trust"),
    "has_linked_business": ("Estructural", "·", "t", "Negocio vinculado"),
    "age_primary": ("Estructural", "·", "t", "Edad del titular"),
}
PROHIBITED = {
    "age_primary": "Característica protegida (ECOA): no entra al modelo ni a la segmentación.",
    "bureau_new_mortgage_elsewhere": "Buró (FCRA): condicionada a propósito permisible; fuera del campeón hasta dictamen legal.",
    "multi_signal_count": "Compuesta de las demás con umbrales fijos: doble conteo; se usa como regla de EWS, no como predictor.",
    "log_relationship_value": "Tamaño no es comportamiento: se usa en priorización (p × AUM) y calibración por banda, no en el score.",
    "has_trust": "Estructural sin hipótesis de signo: va a pre-segmentación.",
    "has_linked_business": "Estructural sin hipótesis de signo: va a pre-segmentación.",
}
STRUCTURAL = ["log_relationship_value", "tenure_years", "deposit_share", "has_investments", "has_trust",
              "has_linked_business", "has_payroll_stream", "has_pension_stream", "has_dividend_stream", "has_credit_anchor"]


# ---------------------------------------------------------------------------
# Target
# ---------------------------------------------------------------------------
def build_target(base: pd.DataFrame, sim_o: dict, labels: pd.DataFrame) -> pd.DataFrame:
    """Target sobre (T0, T0+6m]: hard (valor ≤ 5% y no recupera) ∪ económico (salida neta ex-mercado
    ≥ 25% al cierre de la ventana). Ex-mercado: AUM deflactado por el retorno del propio portafolio."""
    D, A, twr = sim_o["deposit"], sim_o["aum"], sim_o["twr"]
    V, Vx = D + A, D + A / twr
    net_out = 1 - Vx[:, -1] / Vx[:, 0]
    hard = labels["churn_hard_6m"].fillna(0).astype(int).to_numpy() == 1
    excl = base["churn_excluded"].to_numpy()
    out = pd.DataFrame({"household_id": base["household_id"].to_numpy(), "excluded": excl,
                        "short_tenure": base["tenure_years"].to_numpy() < MIN_TENURE_YEARS,
                        "hard": hard, "net_outflow_ex_mkt": net_out,
                        "V0": V[:, 0], "V6": V[:, -1], "Vx0": Vx[:, 0], "Vx6": Vx[:, -1]})
    out["econ"] = ~hard & (net_out >= ECON_THRESHOLD)
    out["y"] = (out["hard"] | out["econ"]).astype(int)
    out["indeterminate"] = ~out["hard"] & (net_out >= INDET_LOW) & (net_out < ECON_THRESHOLD)
    # Valor perdido: bruto (incluye mercado) y neto (flujo ex-mercado).
    out["lost_gross"] = np.where(out["y"] == 1, np.maximum(out["V0"] - out["V6"], 0), 0.0)
    out["lost_net"] = np.where(out["y"] == 1, np.maximum(out["Vx0"] - out["Vx6"], 0), 0.0)
    # Mes del evento: primer mes con valor ≤ 5% (hard) o salida neta ≥ 25% (económico).
    rel = Vx[:, 1:] / Vx[:, :1]
    first_econ = np.where((rel <= 1 - ECON_THRESHOLD).any(1), np.argmax(rel <= 1 - ECON_THRESHOLD, axis=1) + 1, 6)
    out["event_month"] = np.where(hard, labels["churn_exit_month"].to_numpy(), np.where(out["econ"], first_econ, 0))
    return out


# ---------------------------------------------------------------------------
# Estadística descriptiva y univariada
# ---------------------------------------------------------------------------
def describe(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    q = [0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
    rows = {}
    for c in cols:
        x = df[c].astype(float)
        r = {"% missing": x.isna().mean() * 100, "media": x.mean(), "mediana": x.median(), "d.e.": x.std()}
        r.update({f"p{int(k * 100)}": x.quantile(k) for k in q})
        r.update({"mín": x.min(), "máx": x.max()})
        rows[c] = r
    return pd.DataFrame(rows).T


def univariate(df: pd.DataFrame, y: np.ndarray, cols: list[str]) -> pd.DataFrame:
    rows = {}
    for c in cols:
        x = df[c].astype(float).to_numpy()
        nn = ~np.isnan(x)
        a = roc_auc_score(y[nn], x[nn]) if len(np.unique(y[nn])) > 1 and len(np.unique(x[nn])) > 1 else 0.5
        exp = VARS[c][1]
        obs = "+" if a > 0.5 else "−"
        delta = 2 * a - 1  # Cliff's delta = efecto de rango (churn vs no-churn)
        rows[c] = {"dimensión": VARS[c][0], "mediana churn": np.nanmedian(x[y == 1]), "mediana no-churn": np.nanmedian(x[y == 0]),
                   "p25–p75 churn": f"{np.nanquantile(x[y == 1], .25):.3g} – {np.nanquantile(x[y == 1], .75):.3g}",
                   "p25–p75 no-churn": f"{np.nanquantile(x[y == 0], .25):.3g} – {np.nanquantile(x[y == 0], .75):.3g}",
                   "% missing churn": np.isnan(x[y == 1]).mean() * 100, "% missing no-churn": np.isnan(x[y == 0]).mean() * 100,
                   "Cliff δ": delta, "esperado": exp, "observado": obs,
                   "evidencia": ("consistente" if exp in ("·", obs) else "CONTRARIA") if abs(delta) >= 0.05 else "débil"}
    return pd.DataFrame(rows).T


# ---------------------------------------------------------------------------
# Binning y WoE
# ---------------------------------------------------------------------------
class Binner:
    """Binning óptimo monótono (optbinning, CP) con la dirección esperada forzada; missing como bin
    propio si tiene ≥ 5% de la población y ≥ 30 eventos; si no, se asigna al bin de tasa más cercana."""

    def __init__(self, name: str, x: np.ndarray, y: np.ndarray, trend: str | None = None, splits=None):
        from optbinning import OptimalBinning
        self.name = name
        x = np.asarray(x, float)
        if splits is None:
            trend = trend or "auto_asc_desc"
            ob = OptimalBinning(name=name, dtype="numerical", solver="cp", monotonic_trend=trend, max_n_prebins=20,
                                min_prebin_size=0.02, min_bin_size=MIN_BIN_SHARE, min_bin_n_event=MIN_BIN_EVENTS,
                                max_n_bins=8, max_pvalue=MAX_PVALUE, max_pvalue_policy="consecutive")
            ob.fit(x, y)
            splits = np.asarray(ob.splits, float)
        self.splits = np.asarray(splits, float)
        self.trend = trend
        self._fit_table(x, y)

    def codes(self, x) -> np.ndarray:
        x = np.asarray(x, float)
        c = np.searchsorted(self.splits, x, side="right").astype(float)
        c[np.isnan(x)] = -1
        return c.astype(int)

    def label(self, k: int) -> str:
        if k == -1:
            return "Missing"
        lo = "-inf" if k == 0 else f"{self.splits[k - 1]:.4g}"
        hi = "inf" if k == len(self.splits) else f"{self.splits[k]:.4g}"
        return f"[{lo}, {hi})"

    def _fit_table(self, x, y):
        c = self.codes(x)
        keys = list(range(len(self.splits) + 1)) + ([-1] if (c == -1).any() else [])
        t = pd.DataFrame({"code": keys})
        t["N"] = [int((c == k).sum()) for k in keys]
        t["malos"] = [int(y[c == k].sum()) for k in keys]
        t["buenos"] = t["N"] - t["malos"]
        G, B = t["buenos"].sum(), t["malos"].sum()
        t["% pob"] = t["N"] / t["N"].sum()
        t["tasa churn"] = t["malos"] / t["N"].where(t["N"] > 0)
        # Suavizado 0.5 solo para bins con 0 eventos o 0 buenos (evita ±inf).
        g = (t["buenos"] + 0.5 * ((t["buenos"] == 0) | (t["malos"] == 0))) / G
        b = (t["malos"] + 0.5 * ((t["buenos"] == 0) | (t["malos"] == 0))) / B
        t["WoE"] = np.log(g / b)
        t["IV bin"] = (g - b) * t["WoE"]
        self.missing_policy = "sin missing"
        if -1 in keys:
            m = t["code"] == -1
            ok = (t.loc[m, "% pob"].iloc[0] >= MIN_BIN_SHARE) and (t.loc[m, "malos"].iloc[0] >= MIN_BIN_EVENTS)
            if ok:
                self.missing_policy = "bin propio"
            else:
                r = t.loc[m, "tasa churn"].iloc[0]
                others = t[~m]
                j = (others["tasa churn"] - r).abs().idxmin()
                t.loc[m, "WoE"] = t.loc[j, "WoE"]
                self.missing_policy = f"asignado a {self.label(int(t.loc[j, 'code']))} (missing < 5% o < 30 eventos)"
        t["bin"] = [self.label(k) for k in t["code"]]
        self.table = t
        self.woe_map = dict(zip(t["code"], t["WoE"]))
        self.iv = float(t["IV bin"].sum())

    def woe(self, x) -> np.ndarray:
        c = self.codes(x)
        return np.array([self.woe_map.get(k, 0.0) for k in c])

    def is_monotone(self, x=None, y=None) -> bool:
        t = self.table if x is None else self.table_on(x, y)
        r = t[t["code"] >= 0]["tasa churn"].dropna().to_numpy()
        return len(r) < 3 or bool(np.all(np.diff(r) >= -1e-12) or np.all(np.diff(r) <= 1e-12))

    def table_on(self, x, y) -> pd.DataFrame:
        c = self.codes(x)
        rows = []
        for k in self.table["code"]:
            m = c == k
            rows.append({"code": k, "bin": self.label(k), "N": int(m.sum()), "malos": int(y[m].sum()),
                         "tasa churn": y[m].mean() if m.any() else np.nan})
        return pd.DataFrame(rows)


def bin_method_comparison(name, x, y, business_cuts) -> pd.DataFrame:
    """Compara 4 esquemas de binning sobre la misma variable."""
    x = np.asarray(x, float)
    nn = ~np.isnan(x)
    out = {}
    q = np.unique(np.nanquantile(x, [0.2, 0.4, 0.6, 0.8]))
    tree = DecisionTreeClassifier(max_leaf_nodes=6, min_samples_leaf=int(MIN_BIN_SHARE * nn.sum()), random_state=0)
    tree.fit(x[nn].reshape(-1, 1), y[nn])
    tsplits = np.sort(tree.tree_.threshold[tree.tree_.feature >= 0])
    schemes = {"Negocio (umbrales Excel/deck)": business_cuts, "Cuantiles (quintiles)": q,
               "Data-driven (árbol CART)": tsplits, "Óptimo (optbinning, monótono)": None}
    for k, s in schemes.items():
        b = Binner(name, x, y, splits=s)
        t = b.table[b.table["code"] >= 0]
        out[k] = {"bins (sin missing)": len(t), "IV": b.iv, "monótono": "sí" if b.is_monotone() else "no",
                  "bin mín % pob": t["% pob"].min() * 100, "bin mín eventos": int(t["malos"].min()),
                  "cortes": ", ".join(f"{v:.3g}" for v in b.splits)}
    return pd.DataFrame(out).T


# ---------------------------------------------------------------------------
# Correlación, VIF y diagnóstico PCA (solo diagnóstico)
# ---------------------------------------------------------------------------
def vif(M: pd.DataFrame) -> pd.Series:
    X = (M - M.mean()) / M.std(ddof=0)
    C = np.corrcoef(X.to_numpy().T)
    inv = np.linalg.pinv(C)
    return pd.Series(np.diag(inv), index=M.columns)


def pca_diagnostic(M: pd.DataFrame, k=6, top=4):
    X = ((M - M.mean()) / M.std(ddof=0)).to_numpy()
    C = np.cov(X.T)
    ev, V = np.linalg.eigh(C)
    o = np.argsort(ev)[::-1]
    ev, V = ev[o], V[:, o]
    summ = pd.DataFrame({"eigenvalue": ev[:k], "% varianza": ev[:k] / ev.sum() * 100,
                         "% acumulada": np.cumsum(ev)[:k] / ev.sum() * 100}, index=[f"PC{i + 1}" for i in range(k)])
    load = V[:, :k] * np.sqrt(ev[:k])
    tops = []
    for j in range(k):
        idx = np.argsort(-np.abs(load[:, j]))[:top]
        tops.append("; ".join(f"{M.columns[i]} ({load[i, j]:+.2f})" for i in idx))
    summ["variables dominantes (loading)"] = tops
    return summ, int((ev > 1).sum()), ev


# ---------------------------------------------------------------------------
# Clustering de variables (centroide, sin PCA) y selección
# ---------------------------------------------------------------------------
def variable_clusters(W: pd.DataFrame, iv: dict, rho_cut=0.6) -> pd.DataFrame:
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import squareform
    R = W.corr(method="spearman").abs().fillna(0).to_numpy()
    Dm = 1 - R
    np.fill_diagonal(Dm, 0)
    Z = linkage(squareform(Dm, checks=False), method="average")
    lab = fcluster(Z, t=1 - rho_cut, criterion="distance")
    Ws = (W - W.mean()) / W.std(ddof=0).replace(0, 1)
    cent = {k: Ws.loc[:, lab == k].mean(axis=1) for k in np.unique(lab)}
    rows = []
    for i, c in enumerate(W.columns):
        k = lab[i]
        r2_own = np.corrcoef(Ws[c], cent[k])[0, 1] ** 2
        r2_next = max([np.corrcoef(Ws[c], cent[j])[0, 1] ** 2 for j in cent if j != k] or [0.0])
        rows.append({"variable": c, "cluster": int(k), "R² propio": r2_own, "R² vecino": r2_next,
                     "ratio (1−R²p)/(1−R²v)": (1 - r2_own) / max(1 - r2_next, 1e-9), "IV": iv[c]})
    t = pd.DataFrame(rows)
    t["representante"] = False
    for k, g in t.groupby("cluster"):
        best = g["ratio (1−R²p)/(1−R²v)"].min()
        tie = g[g["ratio (1−R²p)/(1−R²v)"] <= best + 0.05]
        t.loc[tie["IV"].idxmax(), "representante"] = True
    return t.sort_values(["cluster", "ratio (1−R²p)/(1−R²v)"])


def l1_entry_order(W: pd.DataFrame, good: np.ndarray) -> list[str]:
    """Orden de entrada en el camino LASSO (logística L1 sobre WoE estandarizado)."""
    Ws = (W - W.mean()) / W.std(ddof=0).replace(0, 1)
    order = []
    for C in np.logspace(-4, 0, 60):
        m = LogisticRegression(penalty="l1", C=C, solver="liblinear", max_iter=5000).fit(Ws, good)
        for c, b in zip(W.columns, m.coef_[0]):
            if abs(b) > 1e-8 and c not in order:
                order.append(c)
    return order + [c for c in W.columns if c not in order]


def cv_auc(W: pd.DataFrame, good: np.ndarray, cols: list[str], seed: int, k=5) -> float:
    skf = StratifiedKFold(k, shuffle=True, random_state=seed)
    s = []
    for tr, te in skf.split(W, good):
        m = LogisticRegression(C=1e6, max_iter=3000).fit(W.iloc[tr][cols], good[tr])
        s.append(roc_auc_score(1 - good[te], -m.decision_function(W.iloc[te][cols])))
    return float(np.mean(s))


def forward_select(W, good, order, dim_of, seed, max_vars=8, min_vars=5, min_gain=0.002, max_per_dim=2):
    import statsmodels.api as sm
    chosen, log, base = [], [], 0.5
    for c in order:
        if len(chosen) >= max_vars:
            break
        if sum(dim_of[v] == dim_of[c] for v in chosen) >= max_per_dim:
            log.append({"variable": c, "decisión": f"descartada: ya hay {max_per_dim} de «{dim_of[c]}»"})
            continue
        trial = chosen + [c]
        fit = sm.Logit(good, sm.add_constant(W[trial])).fit(disp=0)
        betas = fit.params[trial]
        v = vif(W[trial]) if len(trial) > 1 else pd.Series({c: 1.0})
        auc = cv_auc(W, good, trial, seed)
        gain = auc - base
        if (betas <= 0).any():
            log.append({"variable": c, "AUC CV": auc, "Δ AUC": gain, "decisión": "descartada: β ≤ 0 sobre WoE (signo contra la lógica)"})
            continue
        if v.max() >= 5:
            log.append({"variable": c, "AUC CV": auc, "Δ AUC": gain, "decisión": f"descartada: VIF {v.max():.1f} ≥ 5"})
            continue
        if fit.pvalues[c] > 0.05:
            log.append({"variable": c, "AUC CV": auc, "Δ AUC": gain, "decisión": f"descartada: p-valor {fit.pvalues[c]:.3f}"})
            continue
        if len(chosen) >= min_vars and gain < min_gain:
            log.append({"variable": c, "AUC CV": auc, "Δ AUC": gain, "decisión": f"descartada: Δ AUC < {min_gain}"})
            continue
        chosen.append(c)
        base = auc
        log.append({"variable": c, "AUC CV": auc, "Δ AUC": gain, "decisión": "ENTRA"})
    return chosen, pd.DataFrame(log)


# ---------------------------------------------------------------------------
# Scorecard: puntos, score, reason codes
# ---------------------------------------------------------------------------
class Scorecard:
    def __init__(self, binners: dict[str, Binner], params: pd.Series, beta0: float):
        self.binners, self.vars = binners, list(params.index)
        self.beta = params
        self.beta0 = beta0            # intercepto ya corregido a la población de scoring
        self.n = len(self.vars)

    def woe_frame(self, X) -> pd.DataFrame:
        return pd.DataFrame({c: self.binners[c].woe(X[c]) for c in self.vars}, index=X.index)

    def ln_odds_good(self, X) -> np.ndarray:
        return self.beta0 + self.woe_frame(X).to_numpy() @ self.beta.to_numpy()

    def p_churn(self, X) -> np.ndarray:
        return special.expit(-self.ln_odds_good(X))

    def bin_points(self, var, woe) -> float:
        return (self.beta[var] * woe + self.beta0 / self.n) * FACTOR + OFFSET / self.n

    def points_frame(self, X) -> pd.DataFrame:
        W = self.woe_frame(X)
        return pd.DataFrame({c: self.bin_points(c, W[c].to_numpy()) for c in self.vars}, index=X.index)

    def score(self, X) -> np.ndarray:
        return self.points_frame(X).sum(axis=1).to_numpy()

    def lookup(self) -> pd.DataFrame:
        rows = []
        for c in self.vars:
            t = self.binners[c].table
            for _, r in t.iterrows():
                rows.append({"variable": c, "dimensión": VARS[c][0], "bin": r["bin"], "N dev": int(r["N"]),
                             "% pob": r["% pob"] * 100, "tasa churn dev": r["tasa churn"], "WoE": r["WoE"],
                             "β": self.beta[c], "puntos": self.bin_points(c, r["WoE"]),
                             "puntos vs neutral": self.beta[c] * r["WoE"] * FACTOR})
        return pd.DataFrame(rows)

    def reason_codes(self, X, k=3) -> pd.DataFrame:
        """Top k drivers: bins con mayor pérdida de puntos vs. neutral (WoE = 0)."""
        W = self.woe_frame(X)
        loss = -(W * self.beta) * FACTOR   # > 0: puntos perdidos vs. neutral
        out = {}
        L = loss.to_numpy()
        order = np.argsort(-L, axis=1)[:, :k]
        for j in range(k):
            if j >= L.shape[1]:          # menos variables que drivers pedidos
                out[f"driver_{j + 1}"], out[f"driver_{j + 1}_pts"] = "", 0.0
                continue
            idx = order[:, j]
            val = L[np.arange(len(L)), idx]
            names = np.array(self.vars)[idx]
            bins = [self.binners[v].label(int(self.binners[v].codes([X[v].iloc[i]])[0])) for i, v in enumerate(names)]
            out[f"driver_{j + 1}"] = np.where(val > 0, [f"{v} {b}" for v, b in zip(names, bins)], "")
            out[f"driver_{j + 1}_pts"] = np.where(val > 0, -val, 0.0)
        return pd.DataFrame(out, index=X.index)


# ---------------------------------------------------------------------------
# Métricas, calibración y estabilidad
# ---------------------------------------------------------------------------
def ks(y, risk):
    o = np.argsort(-risk)
    yy = y[o]
    return float(np.max(np.abs(np.cumsum(yy) / yy.sum() - np.cumsum(1 - yy) / (1 - yy).sum())))


def metrics(y, risk, value=None) -> dict:
    a = roc_auc_score(y, risk)
    r = {"N": len(y), "eventos": int(y.sum()), "tasa": y.mean(), "AUC": a, "Gini": 2 * a - 1,
         "PR-AUC": average_precision_score(y, risk), "PR-AUC base (tasa)": y.mean(), "KS": ks(y, risk) * 100}
    if value is not None:
        top = np.argsort(-risk)[: int(round(0.1 * len(y)))]
        r["captura AUM top 10%"] = (value[top] * y[top]).sum() / (value * y).sum()
    return r


def gains_table(y, risk, value, n=10) -> pd.DataFrame:
    d = pd.DataFrame({"y": y, "r": risk, "v": value})
    d["decil"] = pd.qcut(d["r"].rank(method="first", ascending=False), n, labels=range(1, n + 1))
    g = d.groupby("decil", observed=True).agg(N=("y", "size"), eventos=("y", "sum"), p_media=("r", "mean"),
                                              AUM_churn=("v", lambda s: (s * d.loc[s.index, "y"]).sum()))
    g["tasa churn"] = g["eventos"] / g["N"]
    g["lift"] = g["tasa churn"] / d["y"].mean()
    g["captura eventos acum."] = g["eventos"].cumsum() / g["eventos"].sum()
    g["captura AUM acum."] = g["AUM_churn"].cumsum() / g["AUM_churn"].sum()
    return g.drop(columns="AUM_churn")


def platt(y, p) -> tuple[float, float]:
    import statsmodels.api as sm
    lp = special.logit(np.clip(p, 1e-6, 1 - 1e-6))
    f = sm.Logit(y, sm.add_constant(lp)).fit(disp=0)
    return float(f.params[0]), float(f.params[1])


def apply_platt(p, a, b):
    return special.expit(a + b * special.logit(np.clip(p, 1e-6, 1 - 1e-6)))


def wilson(k, n, conf=0.90):
    if n == 0:
        return np.nan, np.nan
    z = stats.norm.ppf(0.5 + conf / 2)
    ph = k / n
    den = 1 + z**2 / n
    c = (ph + z**2 / (2 * n)) / den
    h = z * np.sqrt(ph * (1 - ph) / n + z**2 / (4 * n**2)) / den
    return c - h, c + h


def psi(expected, actual) -> float:
    e = pd.Series(expected).value_counts(normalize=True)
    a = pd.Series(actual).value_counts(normalize=True)
    idx = e.index.union(a.index)
    e, a = e.reindex(idx, fill_value=0) + 1e-6, a.reindex(idx, fill_value=0) + 1e-6
    return float(((a - e) * np.log(a / e)).sum())


def kmeans_select(Z: np.ndarray, ks=range(2, 8), seed=0, min_share=0.05, sample=5000):
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(Z), min(sample, len(Z)), replace=False)
    rows, models = [], {}
    for k in ks:
        km = KMeans(k, n_init=10, random_state=seed).fit(Z)
        lab = km.labels_
        sil = silhouette_score(Z[idx], lab[idx])
        aris = []
        for s in range(5):  # estabilidad: re-ajuste sobre submuestras del 80%
            b = np.random.default_rng(seed + 100 + s).choice(len(Z), int(0.8 * len(Z)), replace=False)
            kb = KMeans(k, n_init=5, random_state=seed + s).fit(Z[b])
            aris.append(adjusted_rand_score(lab, kb.predict(Z)))
        share = np.bincount(lab, minlength=k) / len(lab)
        rows.append({"K": k, "WCSS": km.inertia_, "silhouette": sil, "estabilidad (ARI medio)": np.mean(aris),
                     "tamaño mín %": share.min() * 100})
        models[k] = km
    t = pd.DataFrame(rows).set_index("K")
    ok = t[(t["tamaño mín %"] >= min_share * 100) & (t["estabilidad (ARI medio)"] >= 0.80)]
    best = int((ok if len(ok) else t)["silhouette"].idxmax())
    return t, best, models[best]
