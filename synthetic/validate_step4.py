"""Validación del Paso 4 · Investments."""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd
from scipy import stats

from .investments import compute_variables
from .metrics import logit_wald
from .schema import STEP4_COLUMNS, USD
from .validate_common import Checks, calibration, combined_auc, simple_alert


def check_step4(f, sim4, sim1, base, truth, exit_ev, prev_frames, cfg, calib_refs=None):
    s4 = cfg["step4"]
    inv = sim1["inv"]
    ev = sim4["events"]
    ck = Checks()
    el = ~base["churn_excluded"].to_numpy()
    y = base["hard_churn_6m"].astype(float).to_numpy()

    # --- 1 · NULL, rangos y dinero -----------------------------------------------------
    sec = "1 · NULL, rangos y dinero"
    ck.add(sec, "columnas declaradas con unidad", set(f.columns) == set(STEP4_COLUMNS))
    for c in ["investment_redemption_pct", "cash_pct_of_portfolio_chg", "positions_liquidated_pct"]:
        ck.add(sec, f"{c} NULL sin inversiones", f.loc[~inv, c].isna().all())
    ck.add(sec, "#26 NULL ⇔ sin vencimientos en 90d",
           (f["fixed_income_maturity_not_reinvested"].isna() == ~(inv & (sim4["amounts"]["mat"] > 0))).all(),
           f"con vencimiento: {int((sim4['amounts']['mat'] > 0).sum()):,}")
    ck.add(sec, "#28 NULL ⇔ sin advisory o < 12 meses",
           (f["return_vs_benchmark"].isna() == ~(base["has_advisory"] & (base["history_months"] >= 12))).all())
    nr = f["fixed_income_maturity_not_reinvested"].dropna()
    ck.add(sec, "#26 en [0, 1]", ((nr >= -1e-12) & (nr <= 1 + 1e-12)).all(), f"masa en 0: {(nr.abs() < 1e-12).mean():.2f}")
    ck.add(sec, "#9 y #34 ≥ 0", (f["investment_redemption_pct"].dropna() >= 0).all() and (f["positions_liquidated_pct"].dropna() >= 0).all())
    c = sim4["cash_pct"][inv]
    ck.add(sec, "cash % del portafolio en [0, 95%]", ((c >= 0) & (c <= 0.95)).all(), f"mediana {np.median(c[:, -1]):.3f}")
    for col, (u, _) in STEP4_COLUMNS.items():
        if u == USD:
            x = f[col].dropna().to_numpy()
            ck.add(sec, f"USD válido: {col}", (x >= -0.01).all() and np.isfinite(x).all(), f"máx ${x.max():,.0f}")

    # --- 2 · Reglas del Excel y coherencia -------------------------------------------------
    sec = "2 · Reglas del Excel y coherencia"
    ret = sim1["returns"][:, -12:]
    port = np.prod(1 + ret, axis=1) - 1
    twr = sim1["twr"][:, -1] / sim1["twr"][:, -13] - 1
    ck.add(sec, "rendimiento de #28 = índice TWR del Paso 1 (12 meses)", np.allclose(port, twr, atol=1e-12))
    # RMD excluida: si contara, los hogares ≥ 73 con RMD en diciembre alertarían más.
    sim_x = copy.copy(sim4)
    sim_x["rmd"] = np.zeros_like(sim4["rmd"])
    fx = compute_variables(sim_x, sim1, base, cfg)
    old = (base["age_primary"] >= s4["rmd_age"]).to_numpy() & inv & (sim4["rmd"][:, -1] > 0)
    a_ok = (f.loc[old, "investment_redemption_pct"] > 0.20).mean()
    a_no = (fx.loc[old, "investment_redemption_pct"] > 0.20).mean()
    ck.add(sec, "RMD excluida de #9", fx.loc[old, "investment_redemption_pct"].sum() > f.loc[old, "investment_redemption_pct"].sum(),
           f"{old.sum():,} hogares ≥ 73 con RMD: alerta {100 * a_ok:.2f}% vs {100 * a_no:.2f}% si contara")
    # Rebalanceos del asesor: venta y compra por igual, no cuentan (se mide venta NETA del cliente).
    reb3 = sim4["rebalance"][:, -3:].sum(axis=1)
    ck.add(sec, "informativo: rebalanceos del asesor (no entran en #9, que mide venta neta del cliente)", True,
           f"{int((reb3 > 0).sum()):,} hogares rebalancearon en 90d (${reb3.sum() / 1e9:,.1f}B vendidos y recomprados)")
    # De-risking del asesor: sube el cash (#27) pero no la venta del cliente (#9).
    only_d = ev["advisor_derisk"].to_numpy() & ~ev["liquidation"].to_numpy() & ~ev["proprietary_sale"].to_numpy() & \
        (ev["advisor_derisk"].to_numpy())
    rise = (f.loc[only_d, "cash_pct_of_portfolio_chg"] > 0.05).mean()
    red = (f.loc[only_d, "investment_redemption_pct"] > 0.20).mean()
    ck.add(sec, "de-risking del asesor sube el cash sin contar como venta del cliente", rise > red,
           f"hogares con solo de-risking: cash +5pp {100 * rise:.1f}% vs alerta #9 {100 * red:.1f}%")
    # Vencimientos fuera de #34.
    only_mat = inv & (sim4["amounts"]["mat"] > 0) & ~ev["liquidation"].to_numpy() & ~ev["proprietary_sale"].to_numpy() \
        & ~ev["client_full_sale"].to_numpy()
    ck.add(sec, "vencimientos de renta fija no cuentan en #34", (f.loc[only_mat, "positions_liquidated_pct"].fillna(0) == 0).all(),
           f"{only_mat.sum():,} hogares solo con vencimiento")
    mv = exit_ev["move"].to_numpy() & inv
    ck.add(sec, "coherencia: quien se muda o liquida reinvierte menos (#26)",
           f.loc[mv, "fixed_income_maturity_not_reinvested"].mean() > f.loc[~mv, "fixed_income_maturity_not_reinvested"].mean(),
           f"{f.loc[mv, 'fixed_income_maturity_not_reinvested'].mean():.2f} vs {f.loc[~mv, 'fixed_income_maturity_not_reinvested'].mean():.2f}")

    # --- 3 · Calibración -----------------------------------------------------------------
    sec = "3 · Calibración (tasa de alerta, IV, tendencia, lift)"
    cal = calibration(f, base, s4["targets"], simple_alert)
    ck.calibration_block(sec, cal, s4["targets"], s4.get("iv_tolerance", 0.0), calib_refs)

    # --- 4 · Fuga (generador) y AUC ---------------------------------------------------------
    sec = "4 · Fuga (generador) y AUC"
    eps = truth["eps_idiosyncratic"].to_numpy()
    lw = logit_wald(ev["liquidation"].to_numpy()[inv].astype(float),
                    np.column_stack([truth["z_outflow"].to_numpy()[inv], eps[inv]]), ["z", "eps"])
    ck.add(sec, "venta a cash ⟂ ε dado z_outflow (Wald)", None, f"coef ε = {lw.loc['eps', 'coef']:+.3f} ± {lw.loc['eps', 'se']:.3f}",
           p=lw.loc["eps", "p"])
    m = f["return_vs_benchmark"].notna().to_numpy()
    X = np.column_stack([np.ones(m.sum()), truth["z_service"].to_numpy()[m], eps[m]])
    b, *_ = np.linalg.lstsq(X, f.loc[m, "return_vs_benchmark"].to_numpy(), rcond=None)
    resid = f.loc[m, "return_vs_benchmark"].to_numpy() - X @ b
    se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * resid.var(ddof=3))
    ck.add(sec, "#28 ⟂ ε dado z_service (MCO)", None, f"coef ε = {b[2]:+.4f} ± {se[2]:.4f}", p=2 * stats.norm.sf(abs(b[2] / se[2])))
    ck.add(sec, "#28: pendiente sobre z_service ≈ −κ (alpha del Paso 1)",
           abs(b[1] + cfg["step1"]["alpha_service_loading_annual"]) < 0.004, f"{b[1]:+.4f} vs −{cfg['step1']['alpha_service_loading_annual']}")
    risk = truth["risk_index"].to_numpy()
    for evn in ["advisor_derisk", "client_full_sale", "maturity"]:
        r, pv = stats.spearmanr(ev[evn].to_numpy()[inv].astype(float), risk[inv])
        ck.add(sec, f"ruido {evn} ⟂ índice de riesgo", None, f"ρ = {r:+.4f}", p=pv)
    a_comb, a_orc = combined_auc(prev_frames + [f[list(s4["targets"])]], base, truth)
    ck.add(sec, "AUC combinado (Pasos 1–4) < AUC techo", a_comb < a_orc, f"{a_comb:.3f} vs techo {a_orc:.3f}")
    return ck.frame(), cal, {"AUC combinado": a_comb, "AUC techo": a_orc}
