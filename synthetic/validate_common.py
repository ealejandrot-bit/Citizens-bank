"""Piezas de validación compartidas por los pasos 4+ (calibración, semillas, AUC combinado)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .metrics import cochran_armitage, woe_table
from .stats_tests import bh_adjust
from .validate import auc
from .validate_step1 import _fit_logit


def simple_alert(f: pd.DataFrame, var: str, rule: str) -> pd.Series:
    x = f[var].astype(float)
    op, th = rule.split()
    return {">": x > float(th), ">=": x >= float(th), "<": x < float(th), "<=": x <= float(th), "=": x == float(th)}[op]


def calibration(f, base, targets, alert_fn=simple_alert) -> pd.DataFrame:
    el = ~base["churn_excluded"].to_numpy()
    y_all = base["hard_churn_6m"].astype(float).to_numpy()
    rows = []
    for var, t in targets.items():
        x = f[var].astype(float).to_numpy()
        m = el & ~np.isnan(x) if t.get("iv_base", "applicable") == "applicable" else el
        xs, ys = pd.Series(x[m]), y_all[m].astype(int)
        a = (alert_fn(f.loc[m].reset_index(drop=True), var, t["alert"]) & xs.notna()).to_numpy()
        wt = woe_table(xs, ys)
        z_ca = cochran_armitage(wt)[0] * (-1 if t["alert"].startswith("<") else 1)
        rows.append({"variable": var, "fuerza_excel": t["strength"], "motor": t.get("driver"), "alerta": t["alert"],
                     "tasa_alerta": a[xs.notna().to_numpy()].mean(), "rango_tasa": t["rate"], "IV": wt["iv"].sum(),
                     "banda_IV": t["iv"], "lift_alerta": ys[a].mean() / ys[xs.notna().to_numpy() & ~a].mean(),
                     "tendencia_z": z_ca, "null_%": 100 * np.isnan(x[el]).mean()})
    return pd.DataFrame(rows).set_index("variable")


class Checks:
    def __init__(self):
        self.rows = []

    def add(self, sec, name, ok, detail="", p=None):
        self.rows.append({"sección": sec, "prueba": name, "ok": None if p is not None else bool(ok), "p": p,
                          "detalle": detail})

    def calibration_block(self, sec, cal, targets, tol=0.0, calib_refs=None):
        for var, r in cal.iterrows():
            lo, hi = r["rango_tasa"]
            self.add(sec, f"tasa de alerta {var}", lo <= r["tasa_alerta"] <= hi, f"{r['tasa_alerta']:.3f} en [{lo}, {hi}]")
            lo, hi = r["banda_IV"]
            self.add(sec, f"IV {var} ({r['fuerza_excel']})", lo - tol <= r["IV"] <= hi + tol, f"{r['IV']:.3f} en [{lo}, {hi}]")
            self.add(sec, f"lift del grupo en alerta ≥ 1.5: {var}", r["lift_alerta"] >= 1.5, f"lift = {r['lift_alerta']:.2f}")
            self.add(sec, f"tendencia en la dirección esperada: {var}", r["tendencia_z"] > stats.norm.ppf(0.99),
                     f"z = {r['tendencia_z']:.1f}")
        if calib_refs is not None:
            for var in cal.index:
                g = calib_refs[calib_refs["variable"] == var]
                lo, hi = targets[var]["iv"]
                q10, q50, q90 = g["IV"].quantile([0.1, 0.5, 0.9])
                self.add(sec, f"IV mediano entre semillas en banda: {var}", lo - tol <= q50 <= hi + tol,
                         f"mediana {q50:.3f} (p10–p90 {q10:.3f}–{q90:.3f}) en [{lo}, {hi}]")
                lo, hi = targets[var]["rate"]
                self.add(sec, f"alerta en rango en todas las semillas: {var}", g["tasa_alerta"].between(lo, hi).all(),
                         f"{g['tasa_alerta'].min():.3f}–{g['tasa_alerta'].max():.3f}")

    def frame(self) -> pd.DataFrame:
        res = pd.DataFrame(self.rows)
        has_p = res["p"].notna()
        if has_p.any():
            res.loc[has_p, "p_BH"] = bh_adjust(res.loc[has_p, "p"].to_numpy())
            res.loc[has_p, "ok"] = res.loc[has_p, "p_BH"] > 0.01
        res["ok"] = res["ok"].astype(bool)
        return res


def combined_auc(frames: list[pd.DataFrame], base, truth) -> tuple[float, float]:
    """AUC de una logística con todas las variables construidas (+ indicadores de NULL) vs el techo."""
    el = ~base["churn_excluded"].to_numpy()
    X = pd.concat([f.astype(float) for f in frames], axis=1).loc[el]
    Xf = np.column_stack([X.fillna(X.median()).clip(X.quantile(0.01), X.quantile(0.99), axis=1).to_numpy(),
                          X.isna().to_numpy().astype(float)])
    sd = Xf.std(0)
    Xf = (Xf[:, sd > 0] - Xf[:, sd > 0].mean(0)) / sd[sd > 0]
    y = base.loc[el, "hard_churn_6m"].astype(int).to_numpy()
    return auc(y, _fit_logit(Xf, y)), auc(y, truth.loc[el, "p_hard_6m"].to_numpy())
