"""Validación del Paso 1 · Balances & AUM.

Cuatro bloques: estructura de las series, reglas de NULL y rangos, calibración
(tasa de alerta e IV por variable, en esta semilla y en semillas de referencia) y
pruebas estadísticas (ruido t(6) recuperado, sin fuga desde el riesgo no observable,
AUC combinado por debajo del techo).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import optimize, special, stats

from .metrics import cochran_armitage, information_value, woe_table
from .schema import STEP1_COLUMNS, USD
from .stats_tests import bh_adjust
from .validate import auc


def alert_mask(x: pd.Series, rule: str) -> pd.Series:
    op, th = rule.split()
    return x > float(th) if op == ">" else x <= float(th)


def calibration(feats: pd.DataFrame, base: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    el = ~base["churn_excluded"].to_numpy()
    y = base.loc[el, "hard_churn_6m"].astype(int).to_numpy()
    ys = base.loc[el, "soft_churn_3m"].astype(int).to_numpy()
    rows = []
    for var, t in cfg["step1"]["targets"].items():
        x = feats.loc[el, var].reset_index(drop=True)
        rate = alert_mask(x[x.notna()], t["alert"]).mean()
        wt = woe_table(x, y)
        direction = -1 if t["alert"].startswith("<") else 1
        # Tendencia (Cochran-Armitage) en la dirección esperada. Las señales de churn suelen tener
        # forma de palo de hockey (planas en el medio, fuertes en la cola), así que no se exige ρ ≈ 1.
        z_ca, _ = cochran_armitage(wt)
        z_ca *= direction
        dec = wt[wt.index != "NULL"].sort_index()["tasa_evento"].to_numpy()
        rho = stats.spearmanr(np.arange(len(dec)), dec)[0] * direction
        a = alert_mask(x, t["alert"]) & x.notna()
        yy = pd.Series(y)
        lift = yy[a].mean() / yy[x.notna() & ~a].mean()
        rows.append({"variable": var, "alerta": t["alert"], "tasa_alerta": rate, "rango_tasa": t["rate"],
                     "IV_hard": wt["iv"].sum(), "IV_soft": information_value(x, ys), "banda_IV": t["iv"],
                     "tendencia_z": z_ca, "tendencia_p": stats.norm.sf(z_ca), "lift_alerta": lift,
                     "spearman_tramos": rho, "null_%": 100 * x.isna().mean()})
    return pd.DataFrame(rows).set_index("variable")


def _fit_logit(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    Xc = np.column_stack([np.ones(len(X)), X])

    def nll(b):
        z = Xc @ b
        return np.sum(np.logaddexp(0, z) - y * z)

    def grad(b):
        return Xc.T @ (special.expit(Xc @ b) - y)

    b = optimize.minimize(nll, np.zeros(Xc.shape[1]), jac=grad, method="BFGS").x
    return special.expit(Xc @ b)


def check_step1(feats, sim, base, truth, cfg, calib_refs: pd.DataFrame | None = None):
    s1, nu = cfg["step1"], cfg["distributions"]["t_df"]
    M, floor = s1["months"], s1["min_balance_for_pct"]
    D, A, av, inv = sim["deposit"], sim["aum"], sim["avail"], sim["inv"]
    hist = np.maximum(base["history_months"].to_numpy(), 1)
    out = []

    def add(sec, name, ok, detail="", p=None):
        out.append({"sección": sec, "prueba": name, "ok": bool(ok) if p is None else None, "p": p, "detalle": detail})

    # --- Estructura -----------------------------------------------------------
    sec = "1 · Estructura de las series"
    add(sec, "depósitos mes 0 = Paso 0", np.allclose(D[:, -1], base["deposit_balance"], rtol=1e-12))
    add(sec, "AUM mes 0 = Paso 0", np.allclose(A[inv, -1], base.loc[inv, "aum"], rtol=1e-12))
    add(sec, "depósitos > 0 en toda la serie", (D > 0).all(), f"mín ${D.min():,.2f}")
    add(sec, "AUM > 0 con inversiones", (A[inv] > 0).all(), f"mín ${A[inv].min():,.2f}")
    add(sec, "flujos de AUM ≥ 0", (sim["contrib"] >= 0).all() and (sim["withdraw"] >= 0).all())
    add(sec, "índice TWR > 0", (sim["twr"] > 0).all())
    add(sec, "columnas declaradas con unidad", set(feats.columns) == set(STEP1_COLUMNS))

    # --- NULL y rangos --------------------------------------------------------
    sec = "2 · NULL, rangos y dinero"
    add(sec, "aum_outflow_90d NULL ⇔ sin inversiones o < 3 meses",
        (feats["aum_outflow_90d"].isna() == (~inv | (hist < 3))).all())
    add(sec, "aum_vs_baseline NULL ⇔ sin inversiones o < 7 meses",
        (feats["aum_vs_baseline_pct"].isna() == (~inv | (hist < 7))).all())
    prior = np.where(hist >= 6, D[:, M - 6:M - 3].mean(axis=1), np.nan)
    add(sec, "deposit_change_90d NULL ⇔ < 6 meses o base < $10k",
        (feats["deposit_balance_change_pct_90d"].isna() == ~(prior >= floor)).all(),
        f"NULL por base baja: {int(((hist >= 6) & (prior < floor)).sum())}")
    base6 = np.where(hist >= 7, D[:, M - 7:M - 1].mean(axis=1), np.nan)
    add(sec, "deposit_vs_6m NULL ⇔ < 7 meses o base < $10k",
        (feats["deposit_balance_vs_6m_avg_pct"].isna() == ~(base6 >= floor)).all())
    pct_cols = [c for c in feats if "pct" in c]
    add(sec, "cambios % > −100%", all((feats[c].dropna() > -1).all() for c in pct_cols if "outflow" not in c))
    add(sec, "aum_outflow_pct ≥ 0", all((feats[c].dropna() >= 0).all() for c in pct_cols if "outflow" in c),
        f"máx {feats['aum_outflow_pct_90d'].max():.3f}")
    for c, (u, _) in STEP1_COLUMNS.items():
        if u == USD:
            x = feats[c].dropna().to_numpy()
            add(sec, f"USD válido: {c}", (x >= 0).all() and np.isfinite(x).all()
                and (np.abs(x * 100 - np.round(x * 100)) < 1e-4).all(), f"máx ${x.max():,.0f}")

    # --- Calibración ----------------------------------------------------------
    sec = "3 · Calibración (tasa de alerta, IV, monotonía)"
    cal = calibration(feats, base, cfg)
    for var, r in cal.iterrows():
        lo, hi = r["rango_tasa"]
        add(sec, f"tasa de alerta {var}", lo <= r["tasa_alerta"] <= hi, f"{r['tasa_alerta']:.3f} en [{lo}, {hi}]")
        lo, hi = r["banda_IV"]
        add(sec, f"IV {var}", lo <= r["IV_hard"] <= hi, f"{r['IV_hard']:.3f} en [{lo}, {hi}]")
        add(sec, f"tendencia creciente del riesgo (Cochran-Armitage) {var}", None,
            f"z = {r['tendencia_z']:.1f} (ρ tramos {r['spearman_tramos']:.2f})", p=None)
        out[-1]["ok"] = bool(r["tendencia_p"] < 0.01)
        add(sec, f"lift del grupo en alerta ≥ 1.5: {var}", r["lift_alerta"] >= 1.5, f"lift = {r['lift_alerta']:.2f}")
    if calib_refs is not None:
        for var in cal.index:
            g = calib_refs[calib_refs["variable"] == var]
            lo, hi = cfg["step1"]["targets"][var]["iv"]
            add(sec, f"IV en banda en todas las semillas: {var}", g["IV_hard"].between(lo, hi).all(),
                f"IV {g['IV_hard'].min():.3f}–{g['IV_hard'].max():.3f} en {len(g)} semillas")
            lo, hi = cfg["step1"]["targets"][var]["rate"]
            add(sec, f"alerta en rango en todas las semillas: {var}", g["tasa_alerta"].between(lo, hi).all(),
                f"{g['tasa_alerta'].min():.3f}–{g['tasa_alerta'].max():.3f}")

    # --- Estadística ----------------------------------------------------------
    sec = "4 · Pruebas estadísticas"
    tr = sim["truth"]
    quiet = (~tr["s1_episode"] & ~tr["s1_shock"]).to_numpy() & (hist >= M)
    inc = np.diff(np.log(D[quiet]), axis=1)  # incrementos log = ruido de fondo exacto
    zt = ((inc - s1["deposit_drift_monthly"]) / s1["deposit_sigma_monthly"]).ravel()
    sub = zt[:: max(1, len(zt) // 200_000)]
    ks = stats.kstest(sub, stats.t(nu, scale=np.sqrt((nu - 2) / nu)).cdf)
    add(sec, f"KS ruido de depósitos ~ t({nu}) estandarizada", None, f"D = {ks.statistic:.4f}; n = {len(sub):,}",
        p=ks.pvalue)
    nu_hat, _, sc_hat = stats.t.fit(sub, floc=0)
    add(sec, f"ν recuperado por MLE ≈ {nu}", abs(nu_hat - nu) < 0.5, f"ν̂ = {nu_hat:.2f}; escala {sc_hat:.4f}")
    kt = stats.kurtosis(sub)
    add(sec, "curtosis del ruido ≈ 6/(ν−4)", abs(kt - 6 / (nu - 4)) < 0.6, f"{kt:.2f} vs {6 / (nu - 4):.2f}")
    eps = truth["eps_idiosyncratic"].to_numpy()
    for c in pct_cols:
        m = feats[c].notna().to_numpy()
        r, pv = stats.spearmanr(feats.loc[m, c], eps[m])
        add(sec, f"sin fuga del riesgo no observable: {c} ⟂ ε", None, f"ρ = {r:+.4f}", p=pv)
    # AUC combinado de las 4 variables (logística con indicadores de NULL) vs techo del Paso 0.
    el = ~base["churn_excluded"].to_numpy()
    y = base.loc[el, "hard_churn_6m"].astype(int).to_numpy()
    cols = list(cfg["step1"]["targets"])
    X = feats.loc[el, cols]
    Xf = np.column_stack([X.fillna(X.median()).clip(X.quantile(0.01), X.quantile(0.99), axis=1).to_numpy(),
                          X.isna().to_numpy().astype(float)])
    Xf = (Xf - Xf.mean(0)) / np.where(Xf.std(0) > 0, Xf.std(0), 1)
    a_comb = auc(y, _fit_logit(Xf, y))
    a_orc = auc(y, truth.loc[el, "p_hard_6m"].to_numpy())
    add(sec, "AUC combinado < AUC techo", a_comb < a_orc, f"{a_comb:.3f} vs techo {a_orc:.3f}")

    res = pd.DataFrame(out)
    has_p = res["p"].notna()
    res.loc[has_p, "p_BH"] = bh_adjust(res.loc[has_p, "p"].to_numpy())
    res.loc[has_p, "ok"] = res.loc[has_p, "p_BH"] > 0.01
    res["ok"] = res["ok"].astype(bool)
    return res, cal, {"AUC combinado": a_comb, "AUC techo": a_orc}
