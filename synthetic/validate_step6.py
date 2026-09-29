"""Validación del Paso 6 · Banker."""
from __future__ import annotations

import numpy as np
from scipy import stats

from .metrics import logit_wald
from .schema import STEP6_COLUMNS
from .validate_common import Checks, calibration, combined_auc, simple_alert


def check_step6(f, sim6, base, truth, exit_ev, prev_frames, cfg, calib_refs=None):
    s6 = cfg["step6"]
    log, ev, bk = sim6["log"], sim6["events"], sim6["bankers"]
    n = len(base)
    ck = Checks()
    eps = truth["eps_idiosyncratic"].to_numpy()

    sec = "1 · Carteras, bitácora y reglas del Excel"
    ck.add(sec, "columnas declaradas con unidad", set(f.columns) == set(STEP6_COLUMNS))
    sizes = ev.groupby("banker_id").size()
    ck.add(sec, "tamaño de cartera razonable", sizes.between(15, 90).all(), f"{len(bk)} bankers; {sizes.min()}–{sizes.max()} hogares")
    ck.add(sec, "cada cartera es de un solo segmento", (base.groupby(ev["banker_id"])["segment"].nunique() == 1).all())
    dep = ev["banker_departed"].to_numpy()
    same = (ev.loc[dep].groupby("banker_id")["change_reason"].apply(lambda s: (s == "banker_departure").all())).all()
    ck.add(sec, "si el banker se va, cambia todo su libro", same, f"{int(bk['departed'].sum())} bankers se fueron")
    only_tmp = ev["temporary_coverage"] & ev["change_day"].isna()
    ck.add(sec, "cobertura temporal (< 30d) no cuenta como cambio", (f.loc[only_tmp, "banker_change_6m_flag"].fillna(0) == 0).all(),
           f"n = {int(only_tmp.sum())}")
    ck.add(sec, "envíos masivos fuera de la tasa de respuesta y del contacto significativo",
           (log["kind"] == "mass_mailing").sum() > 0, f"{int((log['kind'] == 'mass_mailing').sum()):,} envíos masivos")
    short = (log["kind"] == "call") & (log["minutes"] > 0) & (log["minutes"] < 5)
    ck.add(sec, "llamadas < 5 min no son contacto significativo", short.sum() > 0, f"{int(short.sum()):,} llamadas cortas")
    ck.add(sec, "#13 NULL ⇔ < 3 contactos en 90d", f["client_reply_rate"].dropna().between(0, 1).all(),
           f"NULL {f['client_reply_rate'].isna().mean():.1%}")
    ck.add(sec, "#35 NULL ⇔ el banker no registra 'cancelado por'",
           (f["meetings_cancelled_by_client"].isna() == ~ev["cancelled_by_captured"]).all(),
           f"capturado en {ev['cancelled_by_captured'].mean():.0%} de los hogares")
    g = f["contact_gap_ratio"]
    ck.add(sec, "brecha de contacto ≥ 0 y cadencia UHNW 30d / HNW 90d", (g >= 0).all() and
           set(ev["cadence_days"].unique()) == set(s6["cadence_days"].values()))
    mv = exit_ev["move"].to_numpy()
    ck.add(sec, "coherencia: quien se muda contesta menos", f.loc[mv, "client_reply_rate"].mean() < f.loc[~mv, "client_reply_rate"].mean(),
           f"{f.loc[mv, 'client_reply_rate'].mean():.2f} vs {f.loc[~mv, 'client_reply_rate'].mean():.2f}")
    ch = ev["change_day"].notna().to_numpy()
    wc = ev["welcome_call"].to_numpy()
    ck.add(sec, "coherencia: entre quienes cambiaron de banker, la bienvenida reduce la brecha",
           np.median(g[ch & wc]) < np.median(g[ch & ~wc]), f"mediana {np.median(g[ch & wc]):.2f} con bienvenida vs {np.median(g[ch & ~wc]):.2f} sin ella")

    sec = "2 · Calibración (tasa de alerta, IV, tendencia, lift)"
    cal = calibration(f, base, s6["targets"], simple_alert)
    ck.calibration_block(sec, cal, s6["targets"], s6.get("iv_tolerance", 0.0), calib_refs)

    sec = "3 · Fuga (generador) y AUC"
    lw = logit_wald(ev["client_request"].to_numpy().astype(float),
                    np.column_stack([truth["z_service"].to_numpy(), eps]), ["z", "eps"])
    ck.add(sec, "cambio pedido por el cliente ⟂ ε dado z_service (Wald)", None, f"coef ε = {lw.loc['eps', 'coef']:+.3f}",
           p=lw.loc["eps", "p"])
    r, pv = stats.spearmanr(bk["diligence"], bk["book_risk_z"])
    ck.add(sec, "diligencia del banker ⟂ calidad del libro", None, f"ρ = {r:+.3f}", p=pv)
    r, pv = stats.spearmanr(ev["book_rebalancing"].astype(float), truth["risk_index"])
    ck.add(sec, "ruido: rebalanceo de carteras ⟂ índice de riesgo", None, f"ρ = {r:+.4f}", p=pv)
    a_comb, a_orc = combined_auc(prev_frames + [f[list(s6["targets"])]], base, truth)
    ck.add(sec, "AUC combinado (Pasos 1–6) < AUC techo", a_comb < a_orc, f"{a_comb:.3f} vs techo {a_orc:.3f}")
    return ck.frame(), cal, {"AUC combinado": a_comb, "AUC techo": a_orc}
