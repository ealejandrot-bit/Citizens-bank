"""Validación del Paso 8 · External & composite, y de la base final consolidada."""
from __future__ import annotations

import copy

import numpy as np
import pandas as pd
from scipy import stats

from .composite import build_step8
from .schema import EXCEL_PRIMARY, STEP8_COLUMNS
from .validate_common import Checks, calibration, combined_auc, simple_alert


def check_step8(o, cfg, core: pd.DataFrame, calib_refs=None):
    s8 = cfg["step8"]
    f, ga, bureau = o["f8"], o["sim8"]["group_alerts"], o["sim8"]["bureau"]
    base, truth = o["base"], o["truth"]
    ck = Checks()
    y = base["hard_churn_6m"].astype(float)

    sec = "1 · Multi-señal y buró"
    ck.add(sec, "columnas declaradas con unidad", set(f.columns) == set(STEP8_COLUMNS))
    ck.add(sec, "conteo = suma de las 7 alertas de grupo", (f["multi_signal_count"] == ga.sum(axis=1).to_numpy()).all())
    rates = y.groupby(f["multi_signal_count"]).mean()
    rho = stats.spearmanr(rates.index, rates.to_numpy())[0]
    ck.add(sec, "churn crece con el nº de grupos en alerta", rho > 0.9,
           " · ".join(f"{k}: {v:.1%}" for k, v in rates.items()))
    ck.add(sec, "#37 NULL ⇔ sin propósito permisible (o sin aprobación legal)",
           (f["bureau_new_mortgage_elsewhere"].isna() == ~(bureau["permissible_purpose"] & s8["legal_cleared"])).all(),
           f"NULL {f['bureau_new_mortgage_elsewhere'].isna().mean():.1%}")
    cfg_x = copy.deepcopy(cfg)
    cfg_x["step8"]["legal_cleared"] = False
    fx, _ = build_step8({**o, "seeds": _FreshSeeds(cfg)}, cfg_x, _FreshSeeds(cfg))
    ck.add(sec, "interruptor legal: sin aprobación, #37 queda NULL en todos", fx["bureau_new_mortgage_elsewhere"].isna().all())
    fin = bureau["financed"].to_numpy()
    ck.add(sec, "compras financiadas con Citizens no cuentan como 'elsewhere'",
           not (bureau["financed_with_citizens"] & ~bureau["mortgage_via_move"] & ~bureau["refinance_elsewhere"]
                & bureau["new_mortgage_elsewhere_true"]).any(), f"{int(fin.sum())} compras financiadas")
    mv = o["exit"]["move"].to_numpy()
    b37 = f["bureau_new_mortgage_elsewhere"].astype(float)
    ck.add(sec, "coherencia: quien se muda toma hipoteca en otro banco más seguido", b37[mv].mean() > 3 * b37[~mv].mean(),
           f"{b37[mv].mean():.1%} vs {b37[~mv].mean():.1%}")

    sec = "2 · Calibración (tasa de alerta, IV, tendencia, lift)"
    cal = calibration(f, base, s8["targets"], simple_alert)
    ck.calibration_block(sec, cal, s8["targets"], s8.get("iv_tolerance", 0.0), calib_refs)

    sec = "3 · Base final consolidada"
    ck.add(sec, "20,000 hogares únicos", len(core) == cfg["n_households"] and core["household_id"].is_unique)
    prim = [c for _, c in EXCEL_PRIMARY.values()]
    ck.add(sec, "las 37 variables del Excel presentes (columna principal)", all(c in core for c in prim) and len(EXCEL_PRIMARY) == 37)
    truth_cols = [c for c in core if c.startswith(("z_", "eps", "risk_index", "p_hard", "p_soft", "s1_", "p_move"))]
    ck.add(sec, "sin columnas de verdad latente en la base (sin fuga)", not truth_cols, ", ".join(truth_cols))
    ck.add(sec, "target presente y NULL solo en excluidos",
           (core["hard_churn_6m"].isna() == core["churn_excluded"]).all())
    frames = [core[prim].drop(columns=["multi_signal_flag"])]
    a_comb, a_orc = combined_auc(frames, base, truth)
    ck.add(sec, "AUC combinado de las 37 variables < AUC techo", a_comb < a_orc, f"{a_comb:.3f} vs techo {a_orc:.3f}")
    return ck.frame(), cal, {"AUC combinado": a_comb, "AUC techo": a_orc}


class _FreshSeeds:
    """SeedManager nuevo para recalcular el Paso 8 sin reutilizar flujos ya entregados."""

    def __init__(self, cfg):
        from .seeds import SeedManager
        self._s = SeedManager(cfg["master_seed"])

    def rng(self, name):
        return self._s.rng(name)
