"""Validación del Paso 5 · Relationship & closures."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import special, stats

from .metrics import logit_wald
from .relationship import EXCLUDED_ACCOUNT_REASONS, EXCLUDED_PRODUCT_REASONS
from .schema import STEP5_COLUMNS
from .validate_common import Checks, calibration, combined_auc, simple_alert


def check_step5(f, sim5, base, truth, exit_ev, prev_frames, cfg, calib_refs=None):
    s5 = cfg["step5"]
    acc, ev = sim5["accounts"], sim5["events"]
    n = len(base)
    ck = Checks()

    sec = "1 · Cuentas, cierres y reglas del Excel"
    ck.add(sec, "columnas declaradas con unidad", set(f.columns) == set(STEP5_COLUMNS))
    held = acc.groupby("hh")["product"].agg(set)
    ck.add(sec, "todo hogar tiene cuenta de cheques", held.apply(lambda s: "checking" in s).all() and len(held) == n)
    for prod, flag in [("brokerage", "has_investments"), ("advisory", "has_advisory"), ("trust", "has_trust"),
                       ("business_account", "has_linked_business")]:
        has = held.apply(lambda s, p=prod: p in s).reindex(range(n), fill_value=False).to_numpy()
        ck.add(sec, f"{prod} ⇔ {flag}", (has == base[flag].to_numpy()).all())
    ck.add(sec, "cierres con fecha ≤ t", (acc["close_day"].dropna() <= 0).all(), f"{acc['close_day'].notna().sum():,} cierres")
    ck.add(sec, "productos cerrados ≤ cuentas cerradas (90d)",
           (f["products_closed_90d"].fillna(0) <= f["accounts_closed_90d"].fillna(0)).all())
    c180 = acc[acc["close_day"] > -180]
    all_prod = c180.groupby("hh")["product"].nunique().reindex(range(n), fill_value=0).to_numpy()
    ck.add(sec, "exclusiones del Excel reducen productos cerrados (180d)",
           all_prod.sum() > f["products_closed_180d"].fillna(0).sum(),
           f"{int(f['products_closed_180d'].fillna(0).sum()):,} contados vs {int(all_prod.sum()):,} sin excluir "
           f"({', '.join(sorted(EXCLUDED_PRODUCT_REASONS))})")
    cons = c180[c180["close_reason"] == "consolidation"]
    ck.add(sec, "consolidación interna excluida de cuentas cerradas", len(cons) > 0, f"{len(cons):,} consolidaciones")
    mv = exit_ev["move"].to_numpy()
    ck.add(sec, "coherencia: quien se muda cierra más productos (180d)",
           f.loc[mv, "products_closed_180d"].astype(float).mean() > 3 * f.loc[~mv, "products_closed_180d"].astype(float).mean(),
           f"{f.loc[mv, 'products_closed_180d'].astype(float).mean():.2f} vs {f.loc[~mv, 'products_closed_180d'].astype(float).mean():.2f}")

    sec = "2 · Share of wallet y trustee"
    sow = f["share_of_wallet"]
    ck.add(sec, "SOW en (0, 1]", ((sow > 0) & (sow <= 1)).all(), f"mediana {sow.median():.2f}; tope en 1: {(sow == 1).mean():.1%}")
    ck.add(sec, "fuente de la estimación registrada", f["wealth_estimate_source"].isin(list(s5["wealth_sources"])).all(),
           str(f["wealth_estimate_source"].value_counts(normalize=True).round(2).to_dict()))
    ch = f["share_of_wallet_change"].dropna()
    ck.add(sec, "cambio de SOW en [−1, 1]", ((ch >= -1) & (ch <= 1)).all())
    ck.add(sec, "coherencia: quien se muda pierde share",
           f.loc[mv, "share_of_wallet_change"].median() < f.loc[~mv, "share_of_wallet_change"].median() - 0.05,
           f"mediana {f.loc[mv, 'share_of_wallet_change'].median():+.3f} vs {f.loc[~mv, 'share_of_wallet_change'].median():+.3f}")
    upd = ev["wealth_estimate_updated"].to_numpy()
    ck.add(sec, "reestimar el patrimonio agrega ruido al cambio de SOW (advertencia del Excel)",
           f.loc[upd, "share_of_wallet_change"].std() > f.loc[~upd, "share_of_wallet_change"].std(),
           f"d.e. {f.loc[upd, 'share_of_wallet_change'].std():.3f} vs {f.loc[~upd, 'share_of_wallet_change'].std():.3f}")
    err = np.abs(np.log(sim5["W_new"] / ev["total_wealth_true"]))
    by_src = pd.Series(err).groupby(ev["wealth_estimate_source"]).median()
    ck.add(sec, "error de estimación: declarado < proveedor < modelo", by_src["declared"] < by_src["vendor"] < by_src["model"],
           by_src.round(3).to_dict().__str__())
    tf = f["trustee_change_flag"]
    ck.add(sec, "trustee NULL ⇔ sin trust", (tf.isna() == ~base["has_trust"]).all())
    only_death = ev["trustee_death_succession"] & ~ev["trustee_move"] & ~ev["trustee_service"] & ~ev["trustee_noise"]
    ck.add(sec, "sucesión por muerte = exclusión (flag 0)", (tf[only_death] == 0).all(), f"n = {int(only_death.sum())}")

    sec = "3 · Calibración (tasa de alerta, IV, tendencia, lift)"
    cal = calibration(f, base, s5["targets"], simple_alert)
    ck.calibration_block(sec, cal, s5["targets"], s5.get("iv_tolerance", 0.0), calib_refs)

    sec = "4 · Fuga (generador) y AUC"
    eps = truth["eps_idiosyncratic"].to_numpy()
    lg = special.logit(ev["sow_true_6m_ago"].to_numpy())
    X = np.column_stack([np.ones(n), truth["z_outflow"].to_numpy(), eps])
    b, *_ = np.linalg.lstsq(X, lg, rcond=None)
    res_ = lg - X @ b
    se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * res_.var(ddof=3))
    ck.add(sec, "SOW verdadero ⟂ ε dado z_outflow (MCO)", None, f"coef ε = {b[2]:+.4f} ± {se[2]:.4f}; coef z = {b[1]:+.3f}",
           p=2 * stats.norm.sf(abs(b[2] / se[2])))
    tr = base["has_trust"].to_numpy()
    lw = logit_wald(ev["trustee_service"].to_numpy()[tr].astype(float),
                    np.column_stack([truth["z_service"].to_numpy()[tr], eps[tr]]), ["z", "eps"])
    ck.add(sec, "trustee por servicio ⟂ ε dado z_service (Wald)", None, f"coef ε = {lw.loc['eps', 'coef']:+.3f}", p=lw.loc["eps", "p"])
    risk = truth["risk_index"].to_numpy()
    # Se prueba el sorteo del ruido: el cierre efectivo está censurado (una cuenta ya cerrada por
    # mudanza no puede convertirse después), lo que induce correlación negativa aparente.
    for reason in ["cd_matured_not_renewed", "conversion", "consolidation", "loan_paid_at_term"]:
        r, pv = stats.spearmanr(sim5["draws"][reason], risk)
        ck.add(sec, f"ruido {reason} ⟂ índice de riesgo", None, f"ρ = {r:+.4f}", p=pv)
    a_comb, a_orc = combined_auc(prev_frames + [f[list(s5["targets"])]], base, truth)
    ck.add(sec, "AUC combinado (Pasos 1–5) < AUC techo", a_comb < a_orc, f"{a_comb:.3f} vs techo {a_orc:.3f}")
    return ck.frame(), cal, {"AUC combinado": a_comb, "AUC techo": a_orc}
