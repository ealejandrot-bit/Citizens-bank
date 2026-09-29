"""Construye el Paso 8 (multi-señal y buró), la base final consolidada y el reporte final.

Uso: python scripts/build_step8.py
Salidas:
  data/synthetic/client_pulse_synthetic.csv       -> base final: atributos + 37 variables (columna principal) + target
  data/synthetic/client_pulse_synthetic_full.csv  -> todas las columnas de todos los pasos (ventanas y montos extra)
  data/synthetic/step8_manifest.json
  docs/reports/step8_report.md                    -> pruebas del Paso 8
  docs/reports/final_report.md                    -> las 37 variables: IV, alerta, NULL, lift, motor
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from synthetic.pipeline import build  # noqa: E402
from synthetic.schema import (COLUMNS, EXCEL_PRIMARY, STEP1_COLUMNS, STEP2_COLUMNS, STEP3_COLUMNS, STEP4_COLUMNS,  # noqa: E402
                              STEP5_COLUMNS, STEP6_COLUMNS, STEP7_COLUMNS, STEP8_COLUMNS)
from synthetic.validate_common import calibration  # noqa: E402
from synthetic.validate_step2 import calibration as cal2  # noqa: E402
from synthetic.validate_step3 import calibration as cal3  # noqa: E402
from synthetic.validate_step8 import check_step8  # noqa: E402
from synthetic.validate_step1 import calibration as cal1  # noqa: E402

OUT = ROOT / "data" / "synthetic"
N_REF_SEEDS = 10
ATTRS = ["household_id", "snapshot_date", "segment", "relationship_value", "deposit_balance", "aum", "has_investments",
         "has_advisory", "has_linked_business", "has_trust", "has_credit_anchor", "has_payroll_stream", "has_pension_stream",
         "has_dividend_stream", "age_primary", "tenure_years", "history_months", "recurring_income_monthly"]
TARGET = ["churn_excluded", "hard_churn_6m", "soft_churn_3m", "value_lost_6m"]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assemble(o):
    feats = [o["base"]]
    for k in range(1, 9):
        feats.append(o[f"f{k}"].drop(columns=["household_id"]))
    full = pd.concat(feats, axis=1)
    prim = [c for _, c in EXCEL_PRIMARY.values()]
    extra = ["multi_signal_count", "aum_outflow_90d", "transfer_to_competitor_bank_amount_90d"]
    core = full[ATTRS + prim + extra + TARGET]
    return core, full


def all_calibration(o, cfg):
    b = o["base"]
    t1 = {k: {**v, "strength": "High", "iv_base": "all", "driver": "mixed"} for k, v in cfg["step1"]["targets"].items()}
    c = [cal1(o["f1"], b, cfg).rename(columns={"IV_hard": "IV"}).assign(fuerza_excel="High"),
         cal2(o["f2"], b, cfg["step2"]["targets"]), cal3(o["f3"], b, cfg["step3"]["targets"])]
    for k in range(4, 9):
        c.append(calibration(o[f"f{k}"], b, cfg[f"step{k}"]["targets"]))
    del t1
    return pd.concat([x[["tasa_alerta", "IV", "lift_alerta", "null_%"]] for x in c])


def main() -> int:
    cfg_path = ROOT / "config" / "params.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    o = build(cfg, upto=8)
    core, full = assemble(o)
    refs = []
    for s in np.random.SeedSequence(cfg["master_seed"]).generate_state(N_REF_SEEDS):
        c = copy.deepcopy(cfg)
        c["master_seed"] = int(s)
        r = build(c, int(s), upto=8)
        refs.append(calibration(r["f8"], r["base"], c["step8"]["targets"]).reset_index().assign(seed=int(s)))
    refs = pd.concat(refs, ignore_index=True)
    res, cal, extra = check_step8(o, cfg, core, refs)

    OUT.mkdir(parents=True, exist_ok=True)
    f_core, f_full = OUT / "client_pulse_synthetic.csv", OUT / "client_pulse_synthetic_full.csv"
    core.to_csv(f_core, index=False, float_format="%.8f", lineterminator="\n")
    full.to_csv(f_full, index=False, float_format="%.8f", lineterminator="\n")
    o["f8"].to_csv(OUT / "step8_composite.csv", index=False, lineterminator="\n")
    manifest = {"step": 8, "master_seed": cfg["master_seed"], "currency": cfg["currency"],
                "params_sha256": sha256(cfg_path), "streams": o["seeds"].issued,
                "outputs": {p.name: {"rows": len(core), "columns": n, "sha256": sha256(p)}
                            for p, n in [(f_core, core.shape[1]), (f_full, full.shape[1])]},
                "checks_passed": bool(res["ok"].all())}
    (OUT / "step8_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    # --- Reporte del Paso 8 -------------------------------------------------------------
    y = o["base"]["hard_churn_6m"].astype(float)
    lines = ["# Paso 8 · External & composite", "",
             f"**{int(res['ok'].sum())} de {len(res)} pruebas OK** (α = 0.01, Benjamini-Hochberg)", "",
             "## Calibración", "", cal.drop(columns=["rango_tasa", "banda_IV"]).to_markdown(floatfmt=",.3f"), "",
             f"## Robustez en {N_REF_SEEDS} semillas de referencia", "",
             refs.groupby("variable")[["tasa_alerta", "IV", "lift_alerta"]].agg(["min", "median", "max"]).to_markdown(floatfmt=",.3f"), "",
             "## Multi-señal: activación por grupo", "", o["sim8"]["group_alerts"].mean().mul(100).to_frame("% hogares").to_markdown(floatfmt=".1f"), "",
             "## Multi-señal: churn por nº de grupos en alerta", "",
             pd.DataFrame({"hogares_%": o["f8"]["multi_signal_count"].value_counts(normalize=True).sort_index() * 100,
                           "churn_6m_%": y.groupby(o["f8"]["multi_signal_count"]).mean() * 100}).to_markdown(floatfmt=".1f"), ""]
    for sec, g in res.groupby("sección"):
        lines += [f"## {sec}", "", "| Prueba | Detalle | p | p BH | OK |", "|---|---|---|---|---|"]
        for _, r in g.iterrows():
            p = "" if pd.isna(r["p"]) else f"{r['p']:.3g}"
            pb = "" if pd.isna(r.get("p_BH", np.nan)) else f"{r['p_BH']:.3g}"
            lines.append(f"| {r['prueba']} | {r['detalle']} | {p} | {pb} | {'OK' if r['ok'] else '**FALLA**'} |")
        lines.append("")
    lines += ["## Diccionario", "", "| Columna | Unidad | Descripción |", "|---|---|---|"]
    lines += [f"| {c} | {u} | {d} |" for c, (u, d) in STEP8_COLUMNS.items()]
    (ROOT / "docs" / "reports" / "step8_report.md").write_text("\n".join(lines) + "\n")

    # --- Reporte final: las 37 variables --------------------------------------------------
    cat = pd.read_csv(ROOT / "data" / "catalog" / "variables_catalog.csv").set_index("id")
    allcal = all_calibration(o, cfg)
    rows = []
    for vid, (name, col) in sorted(EXCEL_PRIMARY.items()):
        key = "multi_signal_count" if col == "multi_signal_flag" else col
        r = allcal.loc[key] if key in allcal.index else None
        rows.append({"#": vid, "variable (Excel)": name, "grupo": cat.loc[vid, "group"], "prioridad": cat.loc[vid, "priority"],
                     "fuerza Excel": cat.loc[vid, "predictive_strength"], "factibilidad": cat.loc[vid, "feasibility"],
                     "columna": col, "NULL %": core[col].isna().mean() * 100,
                     "alerta %": None if r is None else r["tasa_alerta"] * 100, "IV": None if r is None else r["IV"],
                     "lift": None if r is None else r["lift_alerta"]})
    tab = pd.DataFrame(rows).set_index("#")
    prim = [c for _, c in EXCEL_PRIMARY.values()]
    corr = core[prim].astype(float).corr(method="spearman")
    pairs = corr.where(np.triu(np.ones(corr.shape, bool), 1)).stack()
    top = pairs[pairs.abs() >= 0.6].sort_values(key=abs, ascending=False).round(2)
    all_dict = {**COLUMNS, **STEP1_COLUMNS, **STEP2_COLUMNS, **STEP3_COLUMNS, **STEP4_COLUMNS, **STEP5_COLUMNS,
                **STEP6_COLUMNS, **STEP7_COLUMNS, **STEP8_COLUMNS}
    el = ~core["churn_excluded"]
    fin = ["# Client Pulse · Base sintética final", "",
           f"{len(core):,} hogares · corte {cfg['snapshot_date']} · montos en {cfg['currency']} · semilla `{cfg['master_seed']}`", "",
           f"- **Base principal:** `data/synthetic/client_pulse_synthetic.csv` ({core.shape[1]} columnas: atributos del hogar, "
           f"las 37 variables del Excel en su columna principal y el target).",
           f"- **Base completa:** `data/synthetic/client_pulse_synthetic_full.csv` ({full.shape[1]} columnas: todas las ventanas y montos).",
           f"- **Target:** hard churn 6m {core.loc[el, 'hard_churn_6m'].astype(float).mean():.1%} · soft churn 3m "
           f"{core.loc[el, 'soft_churn_3m'].astype(float).mean():.1%} · excluidos {core['churn_excluded'].mean():.1%}.",
           f"- **AUC combinado de las 37 variables** (logística simple): **{extra['AUC combinado']:.3f}**; techo con la probabilidad "
           f"verdadera: {extra['AUC techo']:.3f}. La base es predictiva sin ser irreal.", "",
           "## Las 37 variables", "", tab.to_markdown(floatfmt=",.2f"), "",
           "## Pares más correlacionados (|ρ de Spearman| ≥ 0.6)", "",
           "Son los pares redundantes que anticipa el Excel; el scorecard debe quedarse con uno de cada par (por IV).", "",
           top.rename("ρ").to_frame().to_markdown(), "",
           "## Diccionario de la base principal", "", "| Columna | Unidad | Descripción |", "|---|---|---|"]
    fin += [f"| {c} | {all_dict.get(c, ('', ''))[0]} | {all_dict.get(c, ('', ''))[1]} |" for c in core.columns]
    (ROOT / "docs" / "reports" / "final_report.md").write_text("\n".join(fin) + "\n")

    print(cal[["tasa_alerta", "IV", "lift_alerta", "tendencia_z"]].round(3).to_string())
    print(f"AUC 37 variables {extra['AUC combinado']:.3f} vs techo {extra['AUC techo']:.3f}")
    for _, r in res[~res["ok"]].iterrows():
        print(f"FALLA · {r['prueba']} · {r['detalle']}")
    print(f"{int(res['ok'].sum())}/{len(res)} OK · base {core.shape} · completa {full.shape}")
    return 0 if res["ok"].all() else 1


if __name__ == "__main__":
    raise SystemExit(main())
