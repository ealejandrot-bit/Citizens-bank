"""Validación del Paso 2 · Recurring deposits & flows.

Bloques: transacciones, algoritmo de detección (falsos positivos, recall, reemplazo,
exclusiones, efecto de excluir el bono), NULL y dinero, calibración (tasa de alerta,
IV, tendencia, lift; en esta semilla y en semillas de referencia) y pruebas estadísticas
(sin fuga del riesgo no observable en variables de motor "factor", AUC bajo el techo).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .metrics import cochran_armitage, logit_wald, woe_table
import copy

from .recurring import compute_variables
from .schema import STEP2_COLUMNS, USD_SIGNED
from .stats_tests import bh_adjust
from .validate import auc
from .validate_step1 import _fit_logit


def alert(x: pd.Series, rule: str) -> pd.Series:
    op, th = rule.split()
    th = float(th)
    return {"=": x == th, ">": x > th, "<=": x <= th}[op]


def calibration(feats, base, targets) -> pd.DataFrame:
    el = ~base["churn_excluded"].to_numpy()
    y_all = base["hard_churn_6m"].astype(float).to_numpy()
    rows = []
    for var, t in targets.items():
        x = feats[var].astype(float).to_numpy()
        m = el & ~np.isnan(x) if t.get("iv_base") == "applicable" else el
        xs, ys = pd.Series(x[m]), y_all[m].astype(int)
        wt = woe_table(xs, ys)
        a = alert(xs, t["alert"]) & xs.notna()
        rate = a[xs.notna()].mean()
        lift = ys[a.to_numpy()].mean() / ys[(xs.notna() & ~a).to_numpy()].mean()
        direction = -1 if t["alert"].startswith("<") else 1
        z_ca = cochran_armitage(wt)[0] * direction
        rows.append({"variable": var, "fuerza_excel": t["strength"], "motor": t["driver"], "alerta": t["alert"],
                     "tasa_alerta": rate, "rango_tasa": t["rate"], "IV": wt["iv"].sum(), "base_IV": t["iv_base"],
                     "banda_IV": t["iv"], "lift_alerta": lift, "tendencia_z": z_ca,
                     "null_%": 100 * np.isnan(x[el]).mean()})
    return pd.DataFrame(rows).set_index("variable")


def check_step2(feats, sim2, sim1, feats1, base, truth, cfg, calib_refs=None):
    s2, det = cfg["step2"], cfg["step2"]["detection"]
    st, ev = sim2["streams"], sim2["events"]
    out = []

    def add(sec, name, ok, detail="", p=None):
        out.append({"sección": sec, "prueba": name, "ok": None if p is not None else bool(ok), "p": p,
                    "detalle": detail})

    # --- 1 · Transacciones ------------------------------------------------------
    sec = "1 · Transacciones"
    open_day = -np.floor(base["history_months"].to_numpy() * 30.44)
    full = base["history_months"].to_numpy() >= cfg["population"]["history_months_cap"]
    ok_range = ok_amt = ok_open = True
    ntx = 0
    for s in st.values():
        d, a = s["dates"], s["amount_m"]
        has = ~np.isnan(d)
        ntx += has.sum()
        ok_range &= bool(((d[has] > -s2["history_days"]) & (d[has] <= 0)).all())
        ok_amt &= bool((a[has] > 0).all()) and bool(np.isnan(a[~has]).all())
        ok_open &= bool((full[:, None] | np.isnan(d) | (d >= open_day[:, None])).all())
    add(sec, "fechas dentro de los 18 meses previos a t", ok_range, f"{ntx:,} transacciones")
    add(sec, "montos > 0 y solo donde hay pago", ok_amt)
    add(sec, "sin pagos antes de la apertura de la relación", ok_open)
    add(sec, "columnas declaradas con unidad", set(feats.columns) == set(STEP2_COLUMNS))

    # --- 2 · Algoritmo de detección ---------------------------------------------
    sec = "2 · Algoritmo de detección"
    sal = feats["salary_deposit_stopped_flag"].astype(float)
    quiet = ~(ev["move"] | ev["partial"] | ev["job_change"] | ev["retire"] | ev["leave"] | ev["death"])
    fp = sal[quiet & sal.notna()].mean()
    add(sec, "falsos positivos de nómina sin ningún evento < 0.5%", fp < 0.005, f"{100 * fp:.2f}%")
    sig = ev["move_stop_payroll"] & (ev["move_day"] <= -60) & sal.notna() & ~ev["death"]
    rec = sal[sig].mean()
    add(sec, "recall: nómina mudada hace > 60 días detectada ≥ 95%", rec >= 0.95, f"{100 * rec:.1f}% de {int(sig.sum())}")
    good_job = ev["job_change"] & (ev["job_change_ratio"] >= 0.55) & ~ev["move"] & (ev["job_change_day"] <= -60) & sal.notna()
    rj = (sal[good_job] == 0).mean()
    add(sec, "cambio de empleo con reemplazo ≥ 50% no se marca (≥ 95%)", rj >= 0.95, f"{100 * rj:.1f}% de {int(good_job.sum())}")
    for lab, m in [("retiro reportado", ev["retire_reported"]), ("licencia reportada", ev["leave_reported"]),
                   ("muerte reportada", ev["death_reported"])]:
        v = sal[m & sal.notna()]
        add(sec, f"exclusión: {lab} → flag 0", (v == 0).all(), f"n = {len(v)}")
    bsale = feats["business_payroll_stopped_flag"].astype(float)[ev["business_sale"]]
    add(sec, "exclusión: venta del negocio → flag 0", (bsale.dropna() == 0).all(), f"n = {bsale.notna().sum()}")
    # Efecto de excluir el bono: t = 31-dic, así que el bono de diciembre cae dentro de la
    # ventana de 30 días de #5. Sin la regla, ese pago anual inflaría el "ingreso recurrente".
    cfg_nb = copy.deepcopy(cfg)
    cfg_nb["step2"]["detection"]["bonus_multiple"] = 1e12  # regla desactivada
    nb = compute_variables(sim2, sim1, base, cfg_nb)["recurring_deposit_change_pct"]
    dec = (st["bonus"]["dates"] > -30).any(axis=1) & feats["recurring_deposit_change_pct"].notna().to_numpy()
    med_rule = feats["recurring_deposit_change_pct"][dec].median()
    med_nb = nb[dec].median()
    add(sec, "excluir el bono evita inflar el ingreso recurrente (bono de diciembre)",
        abs(med_rule) < 0.10 and med_nb > 0.30,
        f"mediana del cambio en {int(dec.sum())} hogares: {med_rule:+.3f} con la regla vs {med_nb:+.3f} sin ella")

    # --- 3 · NULL y dinero -----------------------------------------------------
    sec = "3 · NULL, rangos y dinero"
    add(sec, "sin nómina ⇒ salary_flag NULL", sal[~base["has_payroll_stream"] & ~ev["job_change"]].isna().all())
    add(sec, "sin pensión (ni retiro) ⇒ pension_flag NULL",
        feats["pension_deposit_stopped_flag"][~base["has_pension_stream"] & ~ev["retire"]].isna().all())
    add(sec, "sin negocio ⇒ business_flag NULL", feats["business_payroll_stopped_flag"][~base["has_linked_business"]].isna().all())
    cov = sal[base["has_payroll_stream"] & (base["history_months"] >= 12)].notna().mean()
    add(sec, "nómina con ≥ 12m de historia: patrón detectado ≥ 95%", cov >= 0.95, f"{100 * cov:.1f}%")
    rf = feats["recurring_deposit_stopped_flag"]
    add(sec, "tipo de flujo detenido ⇔ flag = 1", (feats["recurring_deposit_stopped_type"].notna() == (rf == 1).fillna(False)).all(),
        str(feats["recurring_deposit_stopped_type"].value_counts().to_dict()))
    add(sec, "recurring_deposit_change_pct ≥ −100%", (feats["recurring_deposit_change_pct"].dropna() >= -1).all(),
        f"mín {feats['recurring_deposit_change_pct'].min():.3f} (−100% = todos los flujos detenidos)")
    # El flujo neto ÷ saldo promedio puede ser < −100% (saldo de 100 a 10: flujo −90, promedio ≈ 40).
    add(sec, "net_deposit_flow_pct finito", np.isfinite(feats["net_deposit_flow_pct_90d"].dropna()).all(),
        f"mín {feats['net_deposit_flow_pct_90d'].min():.2f}, p1 {feats['net_deposit_flow_pct_90d'].quantile(0.01):.2f}")
    for c, (u, _) in STEP2_COLUMNS.items():
        if u == USD_SIGNED:
            x = feats[c].dropna().to_numpy()
            add(sec, f"USD± válido: {c}", np.isfinite(x).all() and (np.abs(x * 100 - np.round(x * 100)) < 1e-4).all(),
                f"rango ${x.min():,.0f} a ${x.max():,.0f}")
    # Coherencia con el Paso 1: el flujo neto es el cambio de saldo de la misma serie.
    D = sim1["deposit"]
    add(sec, "flujo neto 90d = cambio de saldo de la serie del Paso 1",
        np.allclose(feats["net_deposit_flow_90d"].dropna(), (D[:, -1] - D[:, -4])[feats["net_deposit_flow_90d"].notna()], atol=0.01))

    # --- 4 · Calibración -------------------------------------------------------
    sec = "4 · Calibración (tasa de alerta, IV, tendencia, lift)"
    cal = calibration(feats, base, s2["targets"])
    for var, r in cal.iterrows():
        lo, hi = r["rango_tasa"]
        add(sec, f"tasa de alerta {var}", lo <= r["tasa_alerta"] <= hi, f"{r['tasa_alerta']:.3f} en [{lo}, {hi}]")
        lo, hi = r["banda_IV"]
        add(sec, f"IV {var} ({r['fuerza_excel']}, base {r['base_IV']})", lo <= r["IV"] <= hi, f"{r['IV']:.3f} en [{lo}, {hi}]")
        add(sec, f"lift del grupo en alerta ≥ 1.5: {var}", r["lift_alerta"] >= 1.5, f"lift = {r['lift_alerta']:.2f}")
        add(sec, f"tendencia en la dirección esperada: {var}", r["tendencia_z"] > stats.norm.ppf(0.99),
            f"z = {r['tendencia_z']:.1f}")
    if calib_refs is not None:
        # Los flags de subpoblaciones pequeñas tienen IV muy variable por muestreo (~150 eventos
        # → ±0.08), así que se exige la MEDIANA entre semillas en banda y se reporta p10–p90.
        for var in cal.index:
            g = calib_refs[calib_refs["variable"] == var]
            lo, hi = s2["targets"][var]["iv"]
            q10, q50, q90 = g["IV"].quantile([0.1, 0.5, 0.9])
            add(sec, f"IV mediano entre semillas en banda: {var}", lo <= q50 <= hi,
                f"mediana {q50:.3f} (p10–p90 {q10:.3f}–{q90:.3f}) en [{lo}, {hi}]")
            lo, hi = s2["targets"][var]["rate"]
            add(sec, f"alerta en rango en todas las semillas: {var}", g["tasa_alerta"].between(lo, hi).all(),
                f"{g['tasa_alerta'].min():.3f}–{g['tasa_alerta'].max():.3f}")

    # --- 5 · Estadística -------------------------------------------------------
    sec = "5 · Pruebas estadísticas"
    eps = truth["eps_idiosyncratic"].to_numpy()
    for var, t in s2["targets"].items():
        x = feats[var].astype(float)
        m = x.notna().to_numpy()
        r, pv = stats.spearmanr(x[m], eps[m])
        if t["driver"] == "factor":
            add(sec, f"sin fuga del riesgo no observable: {var} ⟂ ε", None, f"ρ = {r:+.4f}", p=pv)
        else:
            out.append({"sección": sec, "prueba": f"ε por diseño ({t['driver']}): {var}", "ok": True, "p": None,
                        "detalle": f"ρ = {r:+.4f} (precursor directo de salida, D-14)"})
    # Generador: los eventos de motor "factor" dependen solo de z_outflow (coef ε ≈ 0).
    z = truth["z_outflow"].to_numpy()
    for evn, mask in [("partial", np.ones(len(base), bool)), ("business_move", base["has_linked_business"].to_numpy())]:
        lw = logit_wald(ev[evn].to_numpy()[mask].astype(float), np.column_stack([z[mask], eps[mask]]), ["z", "eps"])
        add(sec, f"evento {evn} ⟂ ε dado z_outflow (Wald)", None,
            f"coef ε = {lw.loc['eps', 'coef']:+.3f} ± {lw.loc['eps', 'se']:.3f}", p=lw.loc["eps", "p"])
    for evn in ["job_change", "retire", "leave", "business_sale"]:
        r, pv = stats.spearmanr(ev[evn].astype(float), truth["risk_index"])
        add(sec, f"ruido {evn} ⟂ índice de riesgo", None, f"ρ = {r:+.4f}", p=pv)
    el = ~base["churn_excluded"].to_numpy()
    y = base.loc[el, "hard_churn_6m"].astype(int).to_numpy()
    X = pd.concat([feats1[list(cfg["step1"]["targets"])], feats[list(s2["targets"])].astype(float)], axis=1).loc[el]
    Xf = np.column_stack([X.fillna(X.median()).clip(X.quantile(0.01), X.quantile(0.99), axis=1).to_numpy(),
                          X.isna().to_numpy().astype(float)])
    sd = Xf.std(0)
    Xf = (Xf[:, sd > 0] - Xf[:, sd > 0].mean(0)) / sd[sd > 0]
    a_comb = auc(y, _fit_logit(Xf, y))
    a_orc = auc(y, truth.loc[el, "p_hard_6m"].to_numpy())
    add(sec, "AUC combinado (Pasos 1 + 2) < AUC techo", a_comb < a_orc, f"{a_comb:.3f} vs techo {a_orc:.3f}")

    res = pd.DataFrame(out)
    has_p = res["p"].notna()
    if has_p.any():
        res.loc[has_p, "p_BH"] = bh_adjust(res.loc[has_p, "p"].to_numpy())
        res.loc[has_p, "ok"] = res.loc[has_p, "p_BH"] > 0.01
    res["ok"] = res["ok"].astype(bool)
    return res, cal, {"AUC combinado": a_comb, "AUC techo": a_orc}
