"""Validación del Paso 3 · Transfers.

Bloques: transacciones y catálogo (ABA válidas, varias por institución), identidad contable con
el saldo del Paso 1, reglas del Excel (exclusiones, destino nuevo, HHI por institución, pisos PB),
NULL y dinero, calibración (con tolerancia ±0.03 a las bandas expertas, D-18) y pruebas de fuga.
"""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd
from scipy import stats

from .metrics import cochran_armitage, woe_table
from .schema import STEP3_COLUMNS, USD, USD_SIGNED
from .stats_tests import bh_adjust
from .transfers import EXCLUDED, EXTERNAL_OUT, aba_checksum, compute_variables
from .validate import auc
from .validate_step1 import _fit_logit


def alert(f: pd.DataFrame, var: str, rule: str) -> pd.Series:
    x = f[var].astype(float)
    if rule == "accel":  # Excel: > 0 y A1 > 5% del saldo
        return (x > 0) & (f["external_outflow_pct_30d"] > 0.05)
    if rule == "hhi":  # Excel: > 0.7 con salidas > 10% del saldo
        return (x > 0.7) & (f["external_outflow_pct_90d"] > 0.10)
    op, th = rule.split()
    return {">": x > float(th), ">=": x >= float(th), "<=": x <= float(th)}[op]


def calibration(f, base, targets) -> pd.DataFrame:
    el = ~base["churn_excluded"].to_numpy()
    y_all = base["hard_churn_6m"].astype(float).to_numpy()
    rows = []
    for var, t in targets.items():
        x = f[var].astype(float).to_numpy()
        m = el & ~np.isnan(x)
        xs, ys = pd.Series(x[m]), y_all[m].astype(int)
        a = alert(f.loc[m].reset_index(drop=True), var, t["alert"]).to_numpy()
        wt = woe_table(xs, ys)
        z_ca = cochran_armitage(wt)[0] * (-1 if t["alert"].startswith("<") else 1)
        rows.append({"variable": var, "fuerza_excel": t["strength"], "alerta": t["alert"], "tasa_alerta": a.mean(),
                     "rango_tasa": t["rate"], "IV": wt["iv"].sum(), "banda_IV": t["iv"],
                     "lift_alerta": ys[a].mean() / ys[~a].mean(), "tendencia_z": z_ca,
                     "null_%": 100 * np.isnan(x[el]).mean()})
    return pd.DataFrame(rows).set_index("variable")


def check_step3(f, sim3, sim1, sim2, f1, f2, base, truth, exit_ev, cfg, calib_refs=None):
    s3 = cfg["step3"]
    tol = s3["iv_tolerance"]
    tx, inst, abas, idn = sim3["tx"], sim3["inst"], sim3["abas"], sim3["identity"]
    n = len(base)
    out = []

    def add(sec, name, ok, detail="", p=None):
        out.append({"sección": sec, "prueba": name, "ok": None if p is not None else bool(ok), "p": p, "detalle": detail})

    # --- 1 · Transacciones y catálogo ----------------------------------------------
    sec = "1 · Transacciones y catálogo"
    open_day = np.where(base["history_months"] >= cfg["population"]["history_months_cap"], -s3["history_days"],
                        -np.floor(base["history_months"].to_numpy() * 30.44))
    add(sec, "fechas en (t − 548d, t] y después de la apertura",
        ((tx["day"] > -s3["history_days"]) & (tx["day"] <= 0) & (tx["day"] >= open_day[tx["hh"]])).all(),
        f"{len(tx):,} transacciones")
    c100 = tx["amount"].to_numpy() * 100
    add(sec, "montos > 0 al centavo", (tx["amount"] > 0).all() and np.allclose(c100, np.round(c100), rtol=0, atol=1e-3))
    d = np.array([[int(c) for c in a] for a in abas["aba"]])
    add(sec, "ABA con dígito verificador válido", (aba_checksum(d[:, :8]) == d[:, 8]).all(), f"{len(abas)} ABA")
    add(sec, "cada ABA pertenece a una sola institución", abas["aba"].is_unique)
    multi = (abas.groupby("inst_id").size() > 1).sum()
    add(sec, "hay instituciones con varias ABA (prueba el agrupado de #24)", multi > 0, f"{multi} de {len(inst)}")
    ext = tx[tx["category"].isin(EXTERNAL_OUT)]
    add(sec, "toda transferencia externa tiene institución y ABA", (ext["inst_id"] >= 0).all() and ext["aba"].notna().all())
    add(sec, "catálogo sin nombres reales (etiquetas sintéticas)", inst["inst_name"].str.contains("sintética").all())
    add(sec, "columnas declaradas con unidad", set(f.columns) == set(STEP3_COLUMNS))

    # --- 2 · Coherencia con los Pasos 1 y 2 ------------------------------------------
    sec = "2 · Identidad contable y coherencia"
    months = idn["months"]
    inc_tx = tx[tx["category"] == "incoming"].groupby(["hh", "month"])["amount"].sum()
    inc_m = np.zeros((n, len(months)))
    inc_m[inc_tx.index.get_level_values(0), inc_tx.index.get_level_values(1) - months[0]] = inc_tx.to_numpy()
    v = idn["valid"]
    add(sec, "entradas externas de las transacciones = las que cierran la identidad",
        np.allclose(inc_m[v], idn["incoming"][v], atol=0.05 * 3 + 1e-6),
        f"máx desvío ${np.abs(inc_m[v] - idn['incoming'][v]).max():,.2f}")
    lhs = idn["dD"]
    rhs = idn["inc"] + idn["internal_in"] - idn["internal_out"] + idn["incoming"] - idn["dep_out"] - idn["card"] - idn["other_debits"]
    add(sec, "ΔD = ingresos + internos + entradas − salidas − tarjeta − otros (cada mes)", np.allclose(lhs[v], rhs[v], atol=1e-6))
    oth = idn["other_debits"][v] > 0
    add(sec, "meses con débitos no explicados (tarjeta extra, cheques) < 60%", oth.mean() < 0.60, f"{100 * oth.mean():.1f}%")
    mv = exit_ev["deposit_transfer"].to_numpy()
    got = tx[tx["category"] == "move_deposit"].groupby("hh").size().reindex(range(n), fill_value=0).to_numpy()
    add(sec, "toda mudanza con traslado tiene envíos al banco nuevo", (got[mv] >= 1).all() and (got[~mv] == 0).all(),
        f"{mv.sum()} hogares")
    comp = set(inst.loc[inst["competitor_bank"], "inst_id"])
    add(sec, "el traslado por mudanza va a un banco competidor", tx.loc[tx["category"] == "move_deposit", "inst_id"].isin(comp).all())
    sal = f2["salary_deposit_stopped_flag"].astype(float)
    x7 = f["external_transfer_pct_of_balance_60d"]
    r = stats.spearmanr(sal[sal.notna() & x7.notna()], x7[sal.notna() & x7.notna()])[0]
    add(sec, "coherencia: nómina detenida ↔ transferencias externas (ρ > 0)", r > 0, f"ρ = {r:.3f}")

    # --- 3 · Reglas del Excel ---------------------------------------------------------
    sec = "3 · Reglas del Excel (exclusiones, destino nuevo, HHI, pisos)"
    # Exclusiones: si se contaran billers / IRS / donaciones / préstamos, #7 alertaría mucho más.
    sim_x = copy.copy(sim3)
    tx_x = tx.copy()
    tx_x.loc[tx_x["category"].isin(EXCLUDED), "inst_id"] = 0
    tx_x["category"] = tx_x["category"].where(~tx_x["category"].isin(EXCLUDED), "background")
    sim_x["tx"] = tx_x
    fx = compute_variables(sim_x, sim1, base, cfg)
    a_ok = (f["external_transfer_pct_of_balance_60d"] > 0.15).mean()
    a_no = (fx["external_transfer_pct_of_balance_60d"] > 0.15).mean()
    add(sec, "las exclusiones evitan falsas alertas (IRS, billers, donaciones, préstamos)", a_no > a_ok,
        f"alerta #7: {100 * a_ok:.1f}% con exclusiones vs {100 * a_no:.1f}% sin ellas")
    # HHI por institución ≥ HHI por ABA (juntar ABA de una misma institución solo puede concentrar).
    e90 = ext[ext["day"] > -90]
    h_aba = e90.groupby(["hh", "aba"])["amount"].sum()
    h_aba = ((h_aba / h_aba.groupby(level=0).transform("sum")) ** 2).groupby(level=0).sum()
    h_inst = f["external_destination_concentration"].to_numpy()[h_aba.index.to_numpy()]
    ok_h = ~np.isnan(h_inst)
    add(sec, "HHI por institución ≥ HHI por ABA", (h_inst[ok_h] >= h_aba.to_numpy()[ok_h] - 1e-9).all(),
        f"{int((h_inst[ok_h] > h_aba.to_numpy()[ok_h] + 1e-9).sum())} hogares cambian al agrupar por institución")
    # Piso PB en destinos nuevos: con el piso del Excel ($10k) los esporádicos inflarían el conteo.
    cfg_x = copy.deepcopy(cfg)
    cfg_x["step3"]["new_destination_min_cumulative"] = 10_000
    cfg_x["step3"]["outflow_baseline_floor_monthly"] = 1_000
    fe = compute_variables(sim3, sim1, base, cfg_x)
    el = ~base["churn_excluded"].to_numpy()
    y = base["hard_churn_6m"].astype(float).to_numpy()
    for var, lab in [("new_external_destinations_90d", "destino nuevo ≥ $50k vs $10k"),
                     ("outflow_vs_baseline_pct", "piso de línea base $10k vs $1k")]:
        rule = s3["targets"][var]["alert"]
        a_pb, a_ex = alert(f, var, rule) & el, alert(fe, var, rule) & el
        lift_pb = y[a_pb].mean() / y[el & ~a_pb].mean()
        lift_ex = y[a_ex].mean() / y[el & ~a_ex].mean()
        add(sec, f"piso PB mejora la precisión: {lab}", lift_pb >= lift_ex,
            f"alerta {100 * a_pb.mean():.1f}% (lift {lift_pb:.2f}) vs Excel {100 * a_ex.mean():.1f}% (lift {lift_ex:.2f})")

    # --- 4 · NULL y dinero -------------------------------------------------------------
    sec = "4 · NULL, rangos y dinero"
    for c, (u, _) in STEP3_COLUMNS.items():
        if u not in (USD, USD_SIGNED):
            continue
        x = f[c].dropna().astype(float).to_numpy()
        if u == USD:
            add(sec, f"USD válido: {c}", (x >= 0).all() and np.isfinite(x).all(), f"máx ${x.max():,.0f}")
        elif u == USD_SIGNED:
            add(sec, f"USD± válido: {c}", np.isfinite(x).all(), f"${x.min():,.0f} a ${x.max():,.0f}")
    hh_ = f["external_destination_concentration"].dropna()
    add(sec, "HHI en (0, 1]", ((hh_ > 0) & (hh_ <= 1 + 1e-12)).all())
    add(sec, "HHI NULL ⇔ sin salidas en 90d (o < 3 meses)",
        (f["external_destination_concentration"].isna() == ((f["external_outflow_pct_90d"].fillna(0) == 0) &
                                                             f["external_outflow_pct_90d"].notna() | (base["history_months"] < 3)))
        .mean() > 0.99)
    add(sec, "destinos nuevos: enteros ≥ 0; NULL con < 16 meses de historia",
        (f["new_external_destinations_90d"].dropna() >= 0).all()
        and f["new_external_destinations_90d"].isna().equals(base["history_months"] < 16))

    # --- 5 · Calibración ---------------------------------------------------------------
    sec = "5 · Calibración (tasa de alerta, IV con tolerancia ±0.03, tendencia, lift)"
    cal = calibration(f, base, s3["targets"])
    for var, r in cal.iterrows():
        lo, hi = r["rango_tasa"]
        add(sec, f"tasa de alerta {var}", lo <= r["tasa_alerta"] <= hi, f"{r['tasa_alerta']:.3f} en [{lo}, {hi}]")
        lo, hi = r["banda_IV"]
        inside = lo <= r["IV"] <= hi
        add(sec, f"IV {var} ({r['fuerza_excel']})", lo - tol <= r["IV"] <= hi + tol,
            f"{r['IV']:.3f} en [{lo}, {hi}]" + ("" if inside else f" · fuera de la banda estricta, dentro de ±{tol}"))
        add(sec, f"lift del grupo en alerta ≥ 1.5: {var}", r["lift_alerta"] >= 1.5, f"lift = {r['lift_alerta']:.2f}")
        if s3["targets"][var].get("shape") == "u":
            wt = woe_table(f.loc[el, var].reset_index(drop=True).astype(float).where(lambda z: z.notna()),
                           pd.Series(y[el]).fillna(0).astype(int))
            q = wt[wt.index != "NULL"].sort_index()["tasa_evento"].to_numpy()
            mid = q[2:-2].mean()
            add(sec, f"forma en U (ambas colas > centro): {var}", q[0] > mid and q[-1] > mid,
                f"tasa extremos {q[0]:.3f} / {q[-1]:.3f} vs centro {mid:.3f} (tendencia lineal z = {r['tendencia_z']:.1f})")
        else:
            add(sec, f"tendencia en la dirección esperada: {var}", r["tendencia_z"] > stats.norm.ppf(0.99), f"z = {r['tendencia_z']:.1f}")
    if calib_refs is not None:
        for var in cal.index:
            g = calib_refs[calib_refs["variable"] == var]
            lo, hi = s3["targets"][var]["iv"]
            q10, q50, q90 = g["IV"].quantile([0.1, 0.5, 0.9])
            add(sec, f"IV mediano entre semillas en banda (±{tol}): {var}", lo - tol <= q50 <= hi + tol,
                f"mediana {q50:.3f} (p10–p90 {q10:.3f}–{q90:.3f}) en [{lo}, {hi}]")
            lo, hi = s3["targets"][var]["rate"]
            add(sec, f"alerta en rango en todas las semillas: {var}", g["tasa_alerta"].between(lo, hi).all(),
                f"{g['tasa_alerta'].min():.3f}–{g['tasa_alerta'].max():.3f}")

    # --- 6 · Fuga y AUC ------------------------------------------------------------------
    sec = "6 · Fuga (generador) y AUC"
    risk = truth["risk_index"].to_numpy()
    # Se prueban los parámetros sorteados (no montos ÷ saldo en t, que ya bajó en quienes se mudan).
    for lab, x in [("fracción de fondo sorteada", pd.Series(sim3["background_share"])),
                   ("nº de destinos esporádicos", tx[tx["category"] == "one_off"].groupby("hh").size().reindex(range(n), fill_value=0)),
                   ("nº de destinos habituales", tx[tx["category"] == "background"].groupby("hh")["dest_id"].nunique().reindex(range(n), fill_value=0))]:
        m = x.notna().to_numpy()
        rr, pv = stats.spearmanr(x[m], risk[m])
        add(sec, f"ruido ⟂ índice de riesgo: {lab}", None, f"ρ = {rr:+.4f}", p=pv)
    X = pd.concat([f1[list(cfg["step1"]["targets"])], f2[list(cfg["step2"]["targets"])].astype(float),
                   f[list(s3["targets"])].astype(float)], axis=1).loc[el]
    Xf = np.column_stack([X.fillna(X.median()).clip(X.quantile(0.01), X.quantile(0.99), axis=1).to_numpy(),
                          X.isna().to_numpy().astype(float)])
    sd = Xf.std(0)
    Xf = (Xf[:, sd > 0] - Xf[:, sd > 0].mean(0)) / sd[sd > 0]
    yy = base.loc[el, "hard_churn_6m"].astype(int).to_numpy()
    a_comb = auc(yy, _fit_logit(Xf, yy))
    a_orc = auc(yy, truth.loc[el, "p_hard_6m"].to_numpy())
    add(sec, "AUC combinado (Pasos 1–3) < AUC techo", a_comb < a_orc, f"{a_comb:.3f} vs techo {a_orc:.3f}")

    res = pd.DataFrame(out)
    has_p = res["p"].notna()
    if has_p.any():
        res.loc[has_p, "p_BH"] = bh_adjust(res.loc[has_p, "p"].to_numpy())
        res.loc[has_p, "ok"] = res.loc[has_p, "p_BH"] > 0.01
    res["ok"] = res["ok"].astype(bool)
    return res, cal, {"AUC combinado": a_comb, "AUC techo": a_orc}
