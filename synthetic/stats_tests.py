"""Pruebas estadísticas de la base sintética (Paso 0).

Principios:
  * Cada columna se contrasta contra la distribución CON LA QUE SE GENERÓ, con los
    parámetros de config (no estimados). Así los grados de libertad de las pruebas
    son los nominales (no se resta nada por parámetros estimados).
  * Para distribuciones con parámetros que cambian por fila (p. ej. el sueldo depende
    del patrimonio) se usa la transformada integral de probabilidad (PIT):
    u_i = F_i(x_i) debe ser Uniforme(0, 1) si la generación es correcta.
  * Con muchas pruebas, algunas fallarían por azar: se corrige con Benjamini-Hochberg.
  * Las colas pesadas se miden con estadísticos robustos (L-momentos, Hill) además de la
    curtosis clásica, que en colas LogNormales es muy inestable.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import special, stats
from scipy.spatial import cKDTree

from .schema import COLUMNS, USD


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def bh_adjust(p: np.ndarray) -> np.ndarray:
    """p-valores ajustados por Benjamini-Hochberg (FDR)."""
    p = np.asarray(p, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.minimum(adj, 1.0)
    return out


def l_moment_ratios(x: np.ndarray) -> tuple[float, float]:
    """L-asimetría (τ3) y L-curtosis (τ4): finitas y robustas aun con colas pesadas."""
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    i = np.arange(1, n + 1)
    b0 = x.mean()
    b1 = np.sum((i - 1) / (n - 1) * x) / n
    b2 = np.sum((i - 1) * (i - 2) / ((n - 1) * (n - 2)) * x) / n
    b3 = np.sum((i - 1) * (i - 2) * (i - 3) / ((n - 1) * (n - 2) * (n - 3)) * x) / n
    l2 = 2 * b1 - b0
    l3 = 6 * b2 - 6 * b1 + b0
    l4 = 20 * b3 - 30 * b2 + 12 * b1 - b0
    return l3 / l2, l4 / l2


def hill_alpha(x: np.ndarray, top: float = 0.01) -> float:
    """Índice de cola de Hill sobre el top `top` de la muestra (menor = cola más pesada)."""
    x = np.sort(np.asarray(x, dtype=float))[::-1]
    k = max(int(len(x) * top), 10)
    return 1.0 / np.mean(np.log(x[:k]) - np.log(x[k]))


def pareto_trunc_mle(x: np.ndarray, lo: float, hi: float) -> tuple[float, float]:
    """MLE de α para Pareto truncada en [lo, hi]; error estándar por información observada."""
    from scipy import optimize
    n, sl = len(x), np.sum(np.log(x))
    r = lo / hi

    def nll(a):
        return -(n * np.log(a) + n * a * np.log(lo) - n * np.log1p(-r**a) - (a + 1) * sl)

    a_hat = optimize.minimize_scalar(nll, bounds=(0.05, 10), method="bounded").x
    h = 1e-4
    info = (nll(a_hat + h) - 2 * nll(a_hat) + nll(a_hat - h)) / h**2
    return a_hat, 1 / np.sqrt(info)


def tail_profile(x: np.ndarray) -> dict[str, float]:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    lx = np.log(x[x > 0])
    t3, t4 = l_moment_ratios(x)
    return {
        "n": len(x), "media": x.mean(), "mediana": np.median(x), "sd": x.std(ddof=1),
        "asimetría": stats.skew(x), "curtosis_exceso": stats.kurtosis(x),
        "curtosis_exceso_log": stats.kurtosis(lx), "L_asimetría": t3, "L_curtosis": t4,
        "p99/p50": np.quantile(x, 0.99) / np.median(x), "hill_alpha_top1%": hill_alpha(x),
    }


def _res(section, test, stat, df, p, criterion, detail="", passed=None):
    return {"sección": section, "prueba": test, "estadístico": stat, "gl": df, "p": p,
            "criterio": criterion, "detalle": detail, "ok": passed}


# ---------------------------------------------------------------------------
# A · Bondad de ajuste contra la distribución generadora
# ---------------------------------------------------------------------------
def _trunc_normal_pit(x, loc, scale, lower=None):
    z = (x - loc) / scale
    if lower is None:
        return stats.norm.cdf(z)
    a = (lower - loc) / scale
    return (stats.norm.cdf(z) - stats.norm.cdf(a)) / stats.norm.sf(a)


def relationship_value_cdf(v: np.ndarray, p: dict) -> np.ndarray:
    """CDF empalmada: LogNormal truncada en [mín, T) y Pareto truncada en [T, tope]."""
    mu, sig = np.log(p["relationship_value_median"]), p["relationship_value_sigma"]
    T, H, a = p["uhnw_threshold"], p["pareto_tail_max"], p["pareto_tail_alpha"]
    body = _trunc_normal_pit(np.log(np.minimum(v, T)), mu, sig, np.log(p["relationship_value_min"]))
    f_T = _trunc_normal_pit(np.log(T), mu, sig, np.log(p["relationship_value_min"]))
    tail = (1 - (T / np.maximum(v, T)) ** a) / (1 - (T / H) ** a)
    return np.where(v < T, body, f_T + (1 - f_T) * tail)


def pit_columns(base: pd.DataFrame, cfg: dict) -> dict[str, np.ndarray]:
    """PIT de cada columna continua con su distribución y parámetros de config."""
    p, inc = cfg["population"], cfg["income"]
    mu, sig = np.log(p["relationship_value_median"]), p["relationship_value_sigma"]
    out = {}
    v = base["relationship_value"].to_numpy()
    out["relationship_value · LogNormal truncada + cola Pareto"] = relationship_value_cdf(v, p)

    inv = base["has_investments"].to_numpy()
    share = (base["deposit_balance"] / base["relationship_value"]).to_numpy()[inv]
    a, b = p["deposit_share_beta"]
    out["proporción depósitos · Beta(2,5)"] = stats.beta.cdf(share, a, b)

    old = base["age_primary"].to_numpy() >= 18 + p["tenure_max_years"]  # tope de antigüedad = 50
    k, th = p["tenure_gamma"]
    out["tenure_years (edad ≥ 68) · Gamma(2, 4.5)"] = stats.gamma.cdf(
        base.loc[old, "tenure_years"].to_numpy(), k, scale=th)

    lv = (np.log(v) - mu) / sig

    def wealth_pit(col, median, sigma, corr, floor):
        m = base[col].notna().to_numpy()
        x = np.log(base.loc[m, col].to_numpy())
        loc = np.log(median) + corr * sigma * lv[m]
        return _trunc_normal_pit(x, loc, sigma * np.sqrt(1 - corr**2),
                                 None if floor is None else np.log(floor))

    out["salary_base_annual · LogNormal ligada, piso $150k"] = wealth_pit(
        "salary_base_annual", inc["salary_base_median"], inc["salary_sigma"], inc["salary_wealth_corr"],
        inc["salary_min"])
    out["pension_monthly · LogNormal ligada, piso $2.5k"] = wealth_pit(
        "pension_monthly", inc["pension_monthly_median"], inc["pension_sigma"], inc["pension_wealth_corr"],
        inc["pension_monthly_min"])
    out["business_distribution_annual · LogNormal ligada"] = wealth_pit(
        "business_distribution_annual", inc["business_distribution_median"], inc["business_distribution_sigma"],
        inc["business_distribution_wealth_corr"], None)

    m = base["bonus_annual"] > 0
    lo_b, hi_b = inc["bonus_share_min"], inc["bonus_share_max"]
    bshare = ((base.loc[m, "bonus_annual"] / base.loc[m, "salary_base_annual"] - lo_b) / (hi_b - lo_b)).to_numpy()
    a, b = inc["bonus_share_beta"]
    out["bono / sueldo (con bono) · 0.1 + 1.4·Beta(1.5,3)"] = stats.beta.cdf(np.clip(bshare, 0, 1), a, b)

    m = base["dividend_annual"].notna() & (base["aum"] > 0)
    y = (base.loc[m, "dividend_annual"] / base.loc[m, "aum"]).to_numpy()
    a, b = inc["dividend_yield_beta"]
    out["rendimiento dividendos · Beta(4,196)"] = stats.beta.cdf(y, a, b)
    return out


def _merge_small_bins(obs, exp, min_exp=5.0):
    """Une celdas con frecuencia esperada < 5 (requisito de la χ²)."""
    o, e = [], []
    acc_o = acc_e = 0.0
    for oi, ei in zip(obs, exp):
        acc_o += oi
        acc_e += ei
        if acc_e >= min_exp:
            o.append(acc_o)
            e.append(acc_e)
            acc_o = acc_e = 0.0
    if acc_e > 0:
        o[-1] += acc_o
        e[-1] += acc_e
    return np.array(o), np.array(e)


def goodness_of_fit(base: pd.DataFrame, cfg: dict) -> list[dict]:
    res = []
    for name, u in pit_columns(base, cfg).items():
        ks = stats.kstest(u, "uniform")
        res.append(_res("A · Bondad de ajuste", f"KS sobre PIT: {name}", ks.statistic, None, ks.pvalue,
                        "PIT ~ U(0,1)", f"n = {len(u):,}"))
        # Cramér-von Mises sobre Φ⁻¹(PIT): complementa a KS, que es poco sensible en las colas.
        z = stats.norm.ppf(np.clip(u, 1e-12, 1 - 1e-12))
        cvm = stats.cramervonmises(z, "norm")
        res.append(_res("A · Bondad de ajuste", f"Cramér-von Mises (colas): {name}", cvm.statistic, None,
                        cvm.pvalue, "Φ⁻¹(PIT) ~ N(0,1)"))

    # Edad: entera (piso de una Normal truncada) → χ² con gl = celdas − 1 (0 parámetros estimados).
    p = cfg["population"]
    lo, hi = p["age_bounds"]
    m, s = p["age_mean"], p["age_sd"]
    dist = stats.truncnorm((lo - m) / s, (hi - m) / s, loc=m, scale=s)
    ks_ = np.arange(lo, hi)
    pmf = dist.cdf(ks_ + 1) - dist.cdf(ks_)
    obs = base["age_primary"].value_counts().reindex(ks_, fill_value=0).to_numpy()
    o, e = _merge_small_bins(obs, pmf * len(base))
    chi = stats.chisquare(o, e)
    res.append(_res("A · Bondad de ajuste", "χ² edad entera · Normal truncada discretizada", chi.statistic,
                    len(o) - 1, chi.pvalue, "gl = celdas − 1", f"{len(o)} celdas tras unir esperadas < 5"))

    # Frecuencia de pago: χ² con gl = 3 − 1 = 2.
    freq = cfg["income"]["pay_frequency"]
    obs = base["pay_frequency"].value_counts().reindex(list(freq), fill_value=0).to_numpy()
    probs = np.array(list(freq.values()))
    chi = stats.chisquare(obs, probs / probs.sum() * obs.sum())
    res.append(_res("A · Bondad de ajuste", "χ² frecuencia de pago", chi.statistic, len(obs) - 1, chi.pvalue,
                    "gl = categorías − 1"))

    # Solo depósitos: p_i depende del patrimonio y se recalcula aquí desde config (no se estima
    # nada), así que Hosmer-Lemeshow usa gl = g (no g − 2).
    lv = (np.log(base["relationship_value"]) - np.log(p["relationship_value_median"])) / p["relationship_value_sigma"]
    p_dep = special.expit(special.logit(p["deposit_only_p_at_median"]) + p["deposit_only_slope"] * lv).to_numpy()
    y_dep = (~base["has_investments"]).to_numpy().astype(int)
    hl, dof, pv = hosmer_lemeshow(y_dep, p_dep, n_estimated=0)
    res.append(_res("A · Bondad de ajuste", "Hosmer-Lemeshow solo depósitos (p_i conocida)", hl, dof, pv,
                    "gl = g (0 parámetros estimados)", f"obs {y_dep.mean():.4f} vs E[p] {p_dep.mean():.4f}"))

    # Banderas Bernoulli por estrato: prueba binomial exacta.
    uhnw = base["segment"] == "UHNW"
    retired = base["age_primary"] >= p["retirement_age"]
    inv = base["has_investments"]
    checks = [
        ("has_linked_business · HNW", ~uhnw, p["p_linked_business"]),
        ("has_linked_business · UHNW", uhnw, p["p_linked_business_uhnw"]),
        ("has_trust · HNW", ~uhnw, p["p_trust"]),
        ("has_trust · UHNW", uhnw, p["p_trust_uhnw"]),
        ("has_advisory | inversiones", inv, p["p_advisory_given_investments"]),
        ("has_credit_anchor", slice(None), p["p_credit_anchor"]),
        ("has_payroll_stream · activos", ~retired, p["p_payroll_if_working"]),
        ("has_payroll_stream · retirados", retired, p["p_payroll_if_retired"]),
        ("has_pension_stream · activos", ~retired, p["p_pension_if_working"]),
        ("has_pension_stream · retirados", retired, p["p_pension_if_retired"]),
        ("has_dividend_stream | inversiones", inv, p["p_dividend_stream_given_investments"]),
        ("churn_excluded", slice(None), cfg["target"]["exclusion_rate"]),
    ]
    has_sal = base["salary_base_annual"].notna()
    checks.append(("sin_bono | nómina", has_sal, cfg["income"]["p_no_bonus"]))
    base = base.assign(sin_bono=base["bonus_annual"] == 0)
    for label, mask, prob in checks:
        col = label.split(" ")[0]
        x = base.loc[mask, col]
        bt = stats.binomtest(int(x.sum()), len(x), prob)
        res.append(_res("A · Bondad de ajuste", f"Binomial exacta: {label}", x.mean(), None, bt.pvalue,
                        f"p = {prob}", f"n = {len(x):,}"))
    return res


# ---------------------------------------------------------------------------
# B · Factores latentes: normal multivariada
# ---------------------------------------------------------------------------
def mardia(x: np.ndarray) -> tuple[float, float, int, float, float]:
    """Mardia: asimetría (χ² con gl = p(p+1)(p+2)/6) y curtosis (N(0,1)).

    b1 = (1/n²) Σ_ij (y_iᵀ y_j)³ se calcula sin la matriz n×n, con la identidad exacta
    Σ_ij (y_iᵀ y_j)³ = Σ_abc (Σ_i y_ia y_ib y_ic)², donde y son los datos blanqueados.
    """
    n, p = x.shape
    xc = x - x.mean(axis=0)
    cov = np.cov(xc, rowvar=False, bias=True)
    y = xc @ np.linalg.inv(np.linalg.cholesky(cov)).T  # y_iᵀ y_j = x_iᵀ S⁻¹ x_j
    t = np.einsum("ia,ib,ic->abc", y, y, y)
    b1 = np.sum(t**2) / n**2
    b2 = np.mean(np.sum(y**2, axis=1) ** 2)
    df = p * (p + 1) * (p + 2) // 6
    skew_stat = n * b1 / 6
    kurt_z = (b2 - p * (p + 2)) / np.sqrt(8 * p * (p + 2) / n)
    return skew_stat, stats.chi2.sf(skew_stat, df), df, kurt_z, 2 * stats.norm.sf(abs(kurt_z))


def latent_tests(truth: pd.DataFrame, cfg: dict) -> list[dict]:
    res = []
    names = cfg["latent"]["factors"]
    z = truth[[f"z_{f}" for f in names]].to_numpy()
    n = len(z)
    for j, f in enumerate(names):
        ks = stats.kstest(z[:, j], "norm")
        res.append(_res("B · Latentes", f"KS z_{f} ~ N(0,1)", ks.statistic, None, ks.pvalue, "N(0,1)"))
        kt = stats.kurtosistest(z[:, j])
        res.append(_res("B · Latentes", f"Curtosis (Anscombe-Glynn) z_{f}", kt.statistic, None, kt.pvalue,
                        "exceso = 0", f"exceso = {stats.kurtosis(z[:, j]):+.4f}"))
    corr = np.asarray(cfg["latent"]["correlation"])
    r = np.corrcoef(z, rowvar=False)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            zstat = (np.arctanh(r[i, j]) - np.arctanh(corr[i, j])) * np.sqrt(n - 3)
            res.append(_res("B · Latentes", f"Fisher z: ρ({names[i]}, {names[j]})", zstat, None,
                            2 * stats.norm.sf(abs(zstat)), f"ρ = {corr[i, j]}", f"r = {r[i, j]:.4f}"))
    sk, psk, df, ku, pku = mardia(z)
    res.append(_res("B · Latentes", "Mardia asimetría multivariada", sk, df, psk, "gl = p(p+1)(p+2)/6"))
    res.append(_res("B · Latentes", "Mardia curtosis multivariada", ku, None, pku, "b2 = p(p+2) = 15"))
    ks = stats.kstest(truth["eps_idiosyncratic"] / cfg["latent"]["idiosyncratic_sd"], "norm")
    res.append(_res("B · Latentes", "KS riesgo idiosincrático ~ N(0, 0.6)", ks.statistic, None, ks.pvalue, "N(0,σ)"))
    return res


# ---------------------------------------------------------------------------
# C · Target: calibración
# ---------------------------------------------------------------------------
def hosmer_lemeshow(y: np.ndarray, p: np.ndarray, g: int = 10, n_estimated: int = 2) -> tuple[float, int, float]:
    """HL con g grupos por deciles de p; gl = g − (parámetros estimados en esta muestra).

    g − 2 es el caso clásico de una logística ajustada (intercepto + pendiente). Aquí el
    target usa la pendiente de config y solo calibra el intercepto en la muestra → gl = g − 1.
    """
    bins = pd.qcut(p, g, labels=False, duplicates="drop")
    df_ = pd.DataFrame({"y": y, "p": p, "b": bins}).groupby("b").agg(o=("y", "sum"), e=("p", "sum"), n=("y", "size"))
    hl = np.sum((df_.o - df_.e) ** 2 / (df_.e * (1 - df_.e / df_.n)))
    dof = len(df_) - n_estimated
    return hl, dof, stats.chi2.sf(hl, dof)


def target_tests(base: pd.DataFrame, truth: pd.DataFrame, cfg: dict) -> list[dict]:
    res = []
    el = ~base["churn_excluded"].to_numpy()
    y = base.loc[el, "hard_churn_6m"].astype(int).to_numpy()
    p = truth.loc[el, "p_hard_6m"].to_numpy()
    hl, dof, pv = hosmer_lemeshow(y, p, n_estimated=1)
    res.append(_res("C · Target", "Hosmer-Lemeshow hard churn 6m", hl, dof, pv, "gl = g − 1 (intercepto calibrado)"))
    soft_el = truth["p_soft_3m"].notna().to_numpy()
    ys = base.loc[soft_el, "soft_churn_3m"].astype(int).to_numpy()
    hl, dof, pv = hosmer_lemeshow(ys, truth.loc[soft_el, "p_soft_3m"].to_numpy(), n_estimated=1)
    res.append(_res("C · Target", "Hosmer-Lemeshow soft churn 3m", hl, dof, pv, "gl = g − 1 (intercepto calibrado)"))
    # Cada evento es Bernoulli(p_i) independiente: el total observado vs Σp_i (Poisson-binomial ≈ normal).
    zs = (y.sum() - p.sum()) / np.sqrt(np.sum(p * (1 - p)))
    res.append(_res("C · Target", "Eventos hard observados vs Σ p_i", zs, None, 2 * stats.norm.sf(abs(zs)),
                    "E[eventos] = Σp", f"{y.sum()} vs {p.sum():.1f}"))
    return res


# ---------------------------------------------------------------------------
# D · Colas pesadas y curtosis
# ---------------------------------------------------------------------------
MONEY_TAIL_COLS = ["relationship_value", "deposit_balance", "aum", "salary_base_annual", "bonus_annual",
                   "pension_monthly", "dividend_annual", "business_distribution_annual", "recurring_income_monthly"]


def tail_table(base: pd.DataFrame) -> pd.DataFrame:
    rows = {}
    for c in MONEY_TAIL_COLS:
        x = base[c].dropna().to_numpy()
        rows[c] = tail_profile(x[x > 0])
    return pd.DataFrame(rows).T


def kurtosis_tests(base: pd.DataFrame, cfg: dict, alpha: float) -> list[dict]:
    """(1) Escala original: se exige cola pesada (exceso de curtosis > 0 significativo).
    (2) Φ⁻¹(PIT): debe ser normal; se prueban curtosis, asimetría y Jarque-Bera (gl = 2)."""
    res = []
    for c in MONEY_TAIL_COLS:
        x = base[c].dropna().to_numpy()
        x = x[x > 0]
        kt = stats.kurtosistest(x, alternative="greater")
        res.append(_res("D · Colas y curtosis", f"Cola pesada en escala USD: {c}", kt.statistic, None, None,
                        "exceso > 0 (p < α)", f"exceso = {stats.kurtosis(x):,.1f}; p = {kt.pvalue:.1e}",
                        passed=bool(kt.pvalue < alpha)))
    for name, u in pit_columns(base, cfg).items():
        z = stats.norm.ppf(np.clip(u, 1e-12, 1 - 1e-12))
        kt = stats.kurtosistest(z)
        res.append(_res("D · Colas y curtosis", f"Curtosis de Φ⁻¹(PIT): {name}", kt.statistic, None, kt.pvalue,
                        "exceso = 0", f"exceso = {stats.kurtosis(z):+.4f}"))
        jb = stats.jarque_bera(z)
        res.append(_res("D · Colas y curtosis", f"Jarque-Bera de Φ⁻¹(PIT): {name}", jb.statistic, 2, jb.pvalue,
                        "gl = 2"))
    # Cuerpo: log del patrimonio en [mín, T) es Normal doblemente truncada → curtosis exacta.
    p = cfg["population"]
    mu, sig = np.log(p["relationship_value_median"]), p["relationship_value_sigma"]
    T, H, alpha = p["uhnw_threshold"], p["pareto_tail_max"], p["pareto_tail_alpha"]
    lo = (np.log(p["relationship_value_min"]) - mu) / sig
    hi = (np.log(T) - mu) / sig
    k_theo = float(stats.truncnorm.stats(lo, hi, moments="k"))
    v = base["relationship_value"].to_numpy()
    lx = np.log(v[v < T])
    k_obs = stats.kurtosis(lx)
    se = np.sqrt(24 / len(lx))
    zk = (k_obs - k_theo) / se
    res.append(_res("D · Colas y curtosis", "Curtosis log(patrimonio) del cuerpo vs teórica", zk, None,
                    2 * stats.norm.sf(abs(zk)), "Normal doblemente truncada", f"obs {k_obs:+.4f} vs teo {k_theo:+.4f}"))
    # Cola: α de la Pareto truncada por máxima verosimilitud; debe recuperar el α configurado.
    xt = v[v >= T]
    a_hat, se_a = pareto_trunc_mle(xt, T, H)
    za = (a_hat - alpha) / se_a
    res.append(_res("D · Colas y curtosis", "α Pareto de la cola UHNW (MLE truncada)", za, None,
                    2 * stats.norm.sf(abs(za)), f"α = {alpha}", f"α̂ = {a_hat:.3f} ± {se_a:.3f}; n = {len(xt):,}"))
    return res


# ---------------------------------------------------------------------------
# E · Grados de libertad de la t-Student (para los cambios % de los Pasos 1+)
# ---------------------------------------------------------------------------
def t_df_study(nus, n, replicas, seed_root) -> pd.DataFrame:
    """Para cada ν: variabilidad de la curtosis muestral y recuperación de ν por máxima verosimilitud."""
    rows = []
    for nu in nus:
        ss = np.random.SeedSequence(entropy=seed_root, spawn_key=(nu,))
        kurts, nu_hat = [], []
        for child in ss.spawn(replicas):
            x = np.random.default_rng(child).standard_t(nu, n)
            kurts.append(stats.kurtosis(x))
            nu_hat.append(stats.t.fit(x, floc=0)[0])
        kurts, nu_hat = np.array(kurts), np.array(nu_hat)
        theo = 6 / (nu - 4) if nu > 4 else np.inf
        rows.append({
            "ν": nu, "curtosis_exceso_teórica": theo,
            "curtosis_muestral_mediana": np.median(kurts),
            "curtosis_muestral_p5": np.quantile(kurts, 0.05), "curtosis_muestral_p95": np.quantile(kurts, 0.95),
            "CV_curtosis": kurts.std() / kurts.mean(),
            "ν_MLE_media": nu_hat.mean(), "ν_MLE_sesgo_%": 100 * (nu_hat.mean() / nu - 1),
            "ν_MLE_p5": np.quantile(nu_hat, 0.05), "ν_MLE_p95": np.quantile(nu_hat, 0.95),
        })
    return pd.DataFrame(rows).set_index("ν")


# ---------------------------------------------------------------------------
# F · Dinero y medias
# ---------------------------------------------------------------------------
def money_tests(base: pd.DataFrame, cfg: dict, vcfg: dict) -> list[dict]:
    res = []
    money = [c for c, (u, _) in COLUMNS.items() if u == USD and c in base]
    for c in money:
        x = base[c].dropna().to_numpy()
        neg = int((x < 0).sum())
        nonfinite = int((~np.isfinite(x)).sum())
        cents = np.abs(x * 100 - np.round(x * 100)) < 1e-4
        mx = vcfg["max_plausible_usd"].get(c)
        ok = neg == 0 and nonfinite == 0 and cents.all() and (mx is None or x.max() <= mx)
        res.append(_res("F · Dinero y medias", f"USD válido: {c}", x.max(), None, None,
                        "≥ 0, finito, centavos, ≤ máx plausible",
                        f"negativos {neg}, no finitos {nonfinite}, máx ${x.max():,.0f}", passed=ok))

    # Medias vs valor teórico de la distribución generadora.
    p = cfg["population"]
    mu, sig = np.log(p["relationship_value_median"]), p["relationship_value_sigma"]
    a = (np.log(p["relationship_value_min"]) - mu) / sig
    T, H, al = p["uhnw_threshold"], p["pareto_tail_max"], p["pareto_tail_alpha"]
    b_ = (np.log(T) - mu) / sig
    body_mean = np.exp(mu + sig**2 / 2) * (stats.norm.cdf(b_ - sig) - stats.norm.cdf(a - sig)) / (
        stats.norm.cdf(b_) - stats.norm.cdf(a))
    tail_mean = al * T**al / (1 - (T / H) ** al) * (H ** (1 - al) - T ** (1 - al)) / (1 - al)
    f_T = (stats.norm.cdf(b_) - stats.norm.cdf(a)) / stats.norm.sf(a)
    theo = {"relationship_value": f_T * body_mean + (1 - f_T) * tail_mean}
    k, th = p["tenure_gamma"]
    old = base["age_primary"] >= 18 + p["tenure_max_years"]
    sh_a, sh_b = p["deposit_share_beta"]
    inv = base["has_investments"]
    samples = {
        "relationship_value": base["relationship_value"].to_numpy(),
        "proporción depósitos (inversión)": (base.loc[inv, "deposit_balance"] / base.loc[inv, "relationship_value"]).to_numpy(),
        "tenure_years (edad ≥ 68)": base.loc[old, "tenure_years"].to_numpy(),
    }
    theo["proporción depósitos (inversión)"] = sh_a / (sh_a + sh_b)
    theo["tenure_years (edad ≥ 68)"] = k * th  # el tope en 50 mueve la media en < 0.01
    lo, hi = p["age_bounds"]
    m_, s_ = p["age_mean"], p["age_sd"]
    dist = stats.truncnorm((lo - m_) / s_, (hi - m_) / s_, loc=m_, scale=s_)
    ks_ = np.arange(lo, hi)
    theo["age_primary"] = float(np.sum(ks_ * (dist.cdf(ks_ + 1) - dist.cdf(ks_))))
    samples["age_primary"] = base["age_primary"].to_numpy()
    for c, x in samples.items():
        z = (x.mean() - theo[c]) / (x.std(ddof=1) / np.sqrt(len(x)))
        res.append(_res("F · Dinero y medias", f"Media = teórica: {c}", z, None, 2 * stats.norm.sf(abs(z)),
                        "t de una muestra", f"obs {x.mean():,.4f} vs teo {theo[c]:,.4f}"))

    # Bandas de negocio (Private Banking, USD).
    el = ~base["churn_excluded"]
    sal = base["salary_base_annual"].dropna()
    vals = {
        "relationship_value_mean": base["relationship_value"].mean(),
        "relationship_value_median": base["relationship_value"].median(),
        "deposit_share_mean": samples["proporción depósitos (inversión)"].mean(),
        "salary_base_annual_median": sal.median(),
        "bonus_to_salary_mean": (base["bonus_annual"] / base["salary_base_annual"]).mean(),
        "pension_monthly_median": base["pension_monthly"].median(),
        "dividend_yield_mean": (base["dividend_annual"] / base["aum"]).mean(),
        "recurring_income_monthly_median": base.loc[base["recurring_income_monthly"] > 0, "recurring_income_monthly"].median(),
        "age_primary_mean": base["age_primary"].mean(),
        "tenure_years_mean": base["tenure_years"].mean(),
        "hard_churn_6m_rate": base.loc[el, "hard_churn_6m"].astype(float).mean(),
        "soft_churn_3m_rate": base.loc[el, "soft_churn_3m"].astype(float).mean(),
    }
    for k_, v in vals.items():
        lo_, hi_ = vcfg["business_bands"][k_]
        res.append(_res("F · Dinero y medias", f"Banda de negocio: {k_}", v, None, None, f"[{lo_:,}, {hi_:,}]",
                        passed=bool(lo_ <= v <= hi_)))
    return res


# ---------------------------------------------------------------------------
# G · Sesgo: independencias que deben cumplirse y efectos diseñados
# ---------------------------------------------------------------------------
def bias_tests(base: pd.DataFrame, truth: pd.DataFrame) -> list[dict]:
    res = []
    df = base.join(truth.drop(columns="household_id"))
    df["bonus_share"] = df["bonus_annual"] / df["salary_base_annual"]
    df["div_yield"] = df["dividend_annual"] / df["aum"]
    indep = [
        ("relationship_value", "age_primary"), ("relationship_value", "tenure_years"),
        ("bonus_share", "salary_base_annual"), ("div_yield", "aum"),
        ("has_credit_anchor", "relationship_value"), ("age_primary", "has_credit_anchor"),
    ]
    for f in ["z_outflow", "z_neglect", "z_service", "eps_idiosyncratic"]:
        indep += [(f, "relationship_value"), (f, "age_primary"), (f, "tenure_years"),
                  (f, "salary_base_annual"), (f, "has_investments"), (f, "has_trust")]
    for a, b in indep:
        m = df[a].notna() & df[b].notna()
        r, pv = stats.spearmanr(df.loc[m, a].astype(float), df.loc[m, b].astype(float))
        res.append(_res("G · Sesgo", f"Independencia Spearman: {a} ⟂ {b}", r, None, pv, "ρ = 0",
                        f"n = {m.sum():,}"))

    el = df[~df["churn_excluded"]].copy()
    el["hard"] = el["hard_churn_6m"].astype(int)
    hnw = el["segment"] == "HNW"
    for label, sub, col in [
        ("frecuencia de pago (con nómina)", el["has_payroll_stream"], "pay_frequency"),
        ("advisory (con inversiones)", el["has_investments"], "has_advisory"),
        ("dividendos (con inversiones)", el["has_investments"], "has_dividend_stream"),
        ("trust (HNW)", hnw, "has_trust"),
        ("negocio vinculado (HNW)", hnw, "has_linked_business"),
    ]:
        tab = pd.crosstab(el.loc[sub, col], el.loc[sub, "hard"])
        chi, pv, dof, _ = stats.chi2_contingency(tab, correction=False)
        res.append(_res("G · Sesgo", f"Target ⟂ {label}", chi, dof, pv, "gl = (r−1)(c−1)"))

    # Efectos diseñados: deben existir y tener el signo configurado.
    for label, mask, sign in [("crédito ancla reduce riesgo", el["has_credit_anchor"], -1),
                              ("UHNW aumenta riesgo", el["segment"] == "UHNW", +1)]:
        d = el.loc[mask, "risk_index"].mean() - el.loc[~mask, "risk_index"].mean()
        t = stats.ttest_ind(el.loc[mask, "risk_index"], el.loc[~mask, "risk_index"], equal_var=False)
        res.append(_res("G · Sesgo", f"Efecto diseñado: {label}", d, None, None, "signo correcto y p < α",
                        f"Δ índice = {d:+.3f}; p = {t.pvalue:.1e}", passed=bool(np.sign(d) == sign and t.pvalue < 0.01)))
    r, pv = stats.spearmanr(el["tenure_years"], el["risk_index"])
    res.append(_res("G · Sesgo", "Efecto diseñado: antigüedad reduce riesgo", r, None, None, "ρ < 0 y p < α",
                    f"p = {pv:.1e}", passed=bool(r < 0 and pv < 0.01)))
    return res


# ---------------------------------------------------------------------------
# H · Variedad y duplicados
# ---------------------------------------------------------------------------
def duplicate_tests(base: pd.DataFrame, truth: pd.DataFrame) -> tuple[list[dict], dict]:
    res = []
    cols = [c for c in base.columns if c != "household_id"]
    ndup = int(base.duplicated(subset=cols).sum())
    res.append(_res("H · Variedad y duplicados", "Filas duplicadas exactas (sin id)", ndup, None, None, "= 0",
                    passed=ndup == 0))
    zdup = int(truth.duplicated(subset=["z_outflow", "z_neglect", "z_service"]).sum())
    res.append(_res("H · Variedad y duplicados", "Vectores latentes duplicados", zdup, None, None, "= 0",
                    passed=zdup == 0))
    # Repeticiones de montos: al redondear al centavo, algunas coincidencias son inevitables
    # (paradoja del cumpleaños). Esperadas: λ = n(n−1)/2 · Σ p_k² ≈ n(n−1)/2 · 0.01 · E[f(X)],
    # con f estimada por KDE sobre log(X). Se exige que lo observado no exceda Poisson(λ) al 99.9%.
    for c in ["relationship_value", "salary_base_annual", "pension_monthly", "business_distribution_annual"]:
        x = base[c].dropna().to_numpy()
        d = len(x) - len(np.unique(x))
        lx = np.log(x)
        sub = lx[:: max(1, len(lx) // 4000)]
        f_x = stats.gaussian_kde(sub)(lx[:: max(1, len(lx) // 4000)]) / np.exp(sub)
        lam = len(x) * (len(x) - 1) / 2 * 0.01 * f_x.mean()
        upper = stats.poisson.ppf(0.999, lam)
        res.append(_res("H · Variedad y duplicados", f"Repeticiones de monto por redondeo: {c}", d, None, None,
                        "≤ Poisson(λ) p99.9", f"obs {d} vs esperadas λ = {lam:.1f} (máx {upper:.0f})",
                        passed=bool(d <= upper)))

    # Casi-duplicados: mismas banderas y segmento, y distancia euclídea mínima en variables
    # continuas estandarizadas. Umbral 0.01 d.e. ≈ dos hogares prácticamente idénticos.
    feats = pd.DataFrame({
        "log_valor": np.log(base["relationship_value"]),
        "prop_dep": base["deposit_balance"] / base["relationship_value"],
        "tenure": base["tenure_years"], "edad": base["age_primary"],
        "log_ingreso": np.log1p(base["recurring_income_monthly"]),
        "log_sueldo": np.log1p(base["salary_base_annual"].fillna(0)),
        "log_bono": np.log1p(base["bonus_annual"].fillna(0)),
        "log_pension": np.log1p(base["pension_monthly"].fillna(0)),
        "log_negocio": np.log1p(base["business_distribution_annual"].fillna(0)),
    })
    feats = (feats - feats.mean()) / feats.std()
    flags = base[[c for c in base if c.startswith("has_")] + ["segment"]].astype(str).agg("|".join, axis=1)
    nn = np.full(len(base), np.inf)
    for idx in flags.groupby(flags).indices.values():
        if len(idx) < 2:
            continue
        d, _ = cKDTree(feats.iloc[idx].to_numpy()).query(feats.iloc[idx].to_numpy(), k=2)
        nn[idx] = d[:, 1]
    finite = nn[np.isfinite(nn)]
    near = int((finite < 0.01).sum() // 2)
    res.append(_res("H · Variedad y duplicados", "Pares casi idénticos (dist < 0.01 d.e., mismas banderas)", near,
                    None, None, "= 0", f"distancia mínima al vecino = {finite.min():.4f}", passed=near == 0))
    combos = flags.value_counts()
    info = {"combinaciones de banderas": len(combos), "la más común (%)": 100 * combos.iloc[0] / len(base),
            "distancia al vecino p1": np.quantile(finite, 0.01), "distancia al vecino mediana": np.median(finite)}
    return res, info


# ---------------------------------------------------------------------------
# I · Robustez de la semilla
# ---------------------------------------------------------------------------
def seed_metrics(base: pd.DataFrame, truth: pd.DataFrame, cfg: dict) -> dict[str, float]:
    from .validate import auc
    el = ~base["churn_excluded"].to_numpy()
    y = base.loc[el, "hard_churn_6m"].astype(int).to_numpy()
    v = base["relationship_value"].to_numpy()
    t3, t4 = l_moment_ratios(v)
    pits = pit_columns(base, cfg)
    return {
        "tasa hard 6m": y.mean(),
        "tasa soft 3m": base.loc[el, "soft_churn_3m"].astype(int).mean(),
        "AUC techo": auc(y, truth.loc[el, "p_hard_6m"].to_numpy()),
        "media relationship_value": v.mean(),
        "mediana relationship_value": np.median(v),
        "share UHNW": (base["segment"] == "UHNW").mean(),
        "mediana sueldo": base["salary_base_annual"].median(),
        "curtosis log valor": stats.kurtosis(np.log(v)),
        "L-curtosis valor": t4,
        "Hill α valor": hill_alpha(v),
        "KS p relationship_value": stats.kstest(pits["relationship_value · LogNormal truncada + cola Pareto"], "uniform").pvalue,
        "KS p sueldo": stats.kstest(pits["salary_base_annual · LogNormal ligada, piso $150k"], "uniform").pvalue,
    }


def seed_robustness(prod: dict[str, float], refs: pd.DataFrame) -> tuple[list[dict], pd.DataFrame]:
    """La semilla de producción no debe ser atípica frente a las semillas de referencia."""
    res, rows = [], []
    k = len(refs)
    for m, v in prod.items():
        r = refs[m].to_numpy()
        rank = (np.sum(r < v) + 0.5 * np.sum(r == v) + 0.5) / (k + 1)
        p_emp = 2 * min(rank, 1 - rank)
        rows.append({"métrica": m, "semilla producción": v, "ref p5": np.quantile(r, 0.05),
                     "ref mediana": np.median(r), "ref p95": np.quantile(r, 0.95), "percentil": 100 * rank})
        if not m.startswith("KS p"):
            res.append(_res("I · Semilla", f"Semilla no atípica: {m}", v, None, p_emp, "percentil en rango",
                            f"percentil {100 * rank:.0f}"))
    for m in ["KS p relationship_value", "KS p sueldo"]:
        ks = stats.kstest(refs[m], "uniform")
        res.append(_res("I · Semilla", f"p-valores entre semillas ~ U(0,1): {m}", ks.statistic, None, ks.pvalue,
                        "generador sin sesgo sistemático"))
    return res, pd.DataFrame(rows).set_index("métrica")
