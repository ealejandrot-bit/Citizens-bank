"""Validación del Paso 7 · Complaints & voice of client."""
from __future__ import annotations

import numpy as np
from scipy import stats

from .metrics import logit_wald
from .schema import STEP7_COLUMNS
from .validate_common import Checks, calibration, combined_auc, simple_alert


def check_step7(f, sim7, base, truth, exit_ev, prev_frames, cfg, calib_refs=None):
    s7 = cfg["step7"]
    c, ev = sim7["complaints"], sim7["events"]
    n = len(base)
    ck = Checks()
    eps = truth["eps_idiosyncratic"].to_numpy()

    sec = "1 · Quejas, Assistant y reglas del Excel"
    ck.add(sec, "columnas declaradas con unidad", set(f.columns) == set(STEP7_COLUMNS))
    ck.add(sec, "volumen plausible para PB (10–25% de hogares con queja al año)", 0.10 <= (f["complaints_12m"] > 0).mean() <= 0.25,
           f"{(f['complaints_12m'] > 0).mean():.1%} de hogares; {len(c):,} quejas")
    ck.add(sec, "fechas coherentes (apertura ≤ cierre ≤ t)", ((c["close_day"].isna()) | ((c["close_day"] >= c["open_day"]) & (c["close_day"] <= 0))).all())
    ck.add(sec, "#15: 0 días ⇔ sin queja abierta", ((f["complaint_age_days"] == 0) | (f["open_complaint_flag"] == 1)).all()
           and (f.loc[f["open_complaint_flag"] == 0, "complaint_age_days"] == 0).all())
    ck.add(sec, "queja fuera de SLA ⇒ antigüedad > SLA mínimo", (f.loc[f["complaint_out_of_sla_flag"] == 1, "complaint_age_days"] >= min(s7["sla_days"].values())).all())
    esc_c = c[c["escalation_level"] != "none"]
    ck.add(sec, "escalamiento más frecuente fuera de SLA (regla del generador)",
           c.loc[c["out_of_sla"], "escalation_level"].ne("none").mean() > c.loc[~c["out_of_sla"], "escalation_level"].ne("none").mean(),
           f"{c.loc[c['out_of_sla'], 'escalation_level'].ne('none').mean():.2f} vs {c.loc[~c['out_of_sla'], 'escalation_level'].ne('none').mean():.2f}")
    ck.add(sec, "niveles de escalamiento del Excel (gerencia, ombudsman, regulador, legal)",
           set(esc_c["escalation_level"].unique()) <= set(s7["escalation_levels"]), str(esc_c["escalation_level"].value_counts().to_dict()))
    ck.add(sec, "#36 NULL ⇔ fuera del piloto del Assistant", (f["relationship_dissatisfaction_flag"].isna() == ~ev["assistant_pilot"]).all(),
           f"piloto {ev['assistant_pilot'].mean():.0%}")
    pil = ev["assistant_pilot"].to_numpy()
    conf = ev["human_confirmed"].to_numpy()[pil]
    prec = ev["dissatisfied_true"].to_numpy()[pil][conf].mean()
    ck.add(sec, "revisión humana: precisión de la señal confirmada ≥ 85%", prec >= 0.85, f"{prec:.1%}")
    mv = exit_ev["move"].to_numpy()
    ck.add(sec, "coherencia: quien se muda expresa más insatisfacción",
           f.loc[mv & pil, "relationship_dissatisfaction_flag"].astype(float).mean() > 3 * f.loc[~mv & pil, "relationship_dissatisfaction_flag"].astype(float).mean())

    sec = "2 · Calibración (tasa de alerta, IV, tendencia, lift)"
    cal = calibration(f, base, s7["targets"], simple_alert)
    ck.calibration_block(sec, cal, s7["targets"], s7.get("iv_tolerance", 0.0), calib_refs)

    sec = "3 · Fuga (generador) y AUC"
    k = c[c["source"] == "service"].groupby("hh").size().reindex(range(n), fill_value=0).to_numpy()
    X = np.column_stack([np.ones(n), truth["z_service"].to_numpy(), truth["z_neglect"].to_numpy(), eps])
    # Poisson por MCO sobre log(1 + k) como aproximación: ε no debe aportar dado z_S y z_N.
    yk = np.log1p(k)
    b, *_ = np.linalg.lstsq(X, yk, rcond=None)
    res_ = yk - X @ b
    se = np.sqrt(np.diag(np.linalg.inv(X.T @ X)) * res_.var(ddof=4))
    ck.add(sec, "nº de quejas ⟂ ε dado z_service y z_neglect", None, f"coef ε = {b[3]:+.4f} ± {se[3]:.4f}", p=2 * stats.norm.sf(abs(b[3] / se[3])))
    kn = c[c["source"] == "noise"].groupby("hh").size().reindex(range(n), fill_value=0)
    r, pv = stats.spearmanr(kn, truth["risk_index"])
    ck.add(sec, "ruido (fraude, estado de cuenta) ⟂ índice de riesgo", None, f"ρ = {r:+.4f}", p=pv)
    r, pv = stats.spearmanr(ev["assistant_pilot"].astype(float), truth["risk_index"])
    ck.add(sec, "piloto del Assistant ⟂ índice de riesgo (sin sesgo de selección)", None, f"ρ = {r:+.4f}", p=pv)
    a_comb, a_orc = combined_auc(prev_frames + [f[list(s7["targets"])]], base, truth)
    ck.add(sec, "AUC combinado (Pasos 1–7) < AUC techo", a_comb < a_orc, f"{a_comb:.3f} vs techo {a_orc:.3f}")
    return ck.frame(), cal, {"AUC combinado": a_comb, "AUC techo": a_orc}
