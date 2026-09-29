"""Construye el Paso 4 (Investments), lo valida y escribe salidas.

Uso: python scripts/build_step4.py
Salidas:
  data/synthetic/step4_investments.csv   -> variables 9, 26, 27, 28, 34 por hogar
  data/synthetic/step4_cash_monthly.csv  -> cash % mensual del portafolio (auditar #27)
  data/synthetic/step4_events.csv        -> eventos simulados (solo validación)
  data/synthetic/step4_manifest.json     -> semilla, flujos, hashes
  docs/reports/step4_report.md           -> pruebas, calibración y distribuciones
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

from synthetic.metrics import woe_table  # noqa: E402
from synthetic.pipeline import build  # noqa: E402
from synthetic.schema import STEP4_COLUMNS  # noqa: E402
from synthetic.validate_common import calibration  # noqa: E402
from synthetic.validate_step4 import check_step4  # noqa: E402

OUT = ROOT / "data" / "synthetic"
REPORT = ROOT / "docs" / "reports" / "step4_report.md"
N_REF_SEEDS = 20


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prev_frames(o, cfg):
    return [o["f1"][list(cfg["step1"]["targets"])], o["f2"][list(cfg["step2"]["targets"])],
            o["f3"][list(cfg["step3"]["targets"])]]


def main() -> int:
    cfg_path = ROOT / "config" / "params.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    o = build(cfg, upto=4)
    refs = []
    for s in np.random.SeedSequence(cfg["master_seed"]).generate_state(N_REF_SEEDS):
        c = copy.deepcopy(cfg)
        c["master_seed"] = int(s)
        r = build(c, int(s), upto=4)
        refs.append(calibration(r["f4"], r["base"], c["step4"]["targets"]).reset_index().assign(seed=int(s)))
    refs = pd.concat(refs, ignore_index=True)
    res, cal, extra = check_step4(o["f4"], o["sim4"], o["sim1"], o["base"], o["truth"], o["exit"], prev_frames(o, cfg),
                                  cfg, refs)

    base, feats, sim4 = o["base"], o["f4"], o["sim4"]
    M = cfg["step1"]["months"]
    OUT.mkdir(parents=True, exist_ok=True)
    f_feat, f_cash, f_ev = OUT / "step4_investments.csv", OUT / "step4_cash_monthly.csv", OUT / "step4_events.csv"
    feats.to_csv(f_feat, index=False, float_format="%.8f", lineterminator="\n")
    inv = o["sim1"]["inv"]
    pd.DataFrame({"household_id": np.repeat(base["household_id"].to_numpy()[inv], M),
                  "month": np.tile(np.arange(M) - (M - 1), inv.sum()),
                  "cash_pct": sim4["cash_pct"][inv].ravel()}).to_csv(f_cash, index=False, float_format="%.6f",
                                                                    lineterminator="\n")
    sim4["events"].to_csv(f_ev, index=False, float_format="%.6f", lineterminator="\n")
    manifest = {"step": 4, "master_seed": cfg["master_seed"], "currency": cfg["currency"],
                "params_sha256": sha256(cfg_path), "streams": o["seeds"].issued,
                "outputs": {p.name: {"sha256": sha256(p)} for p in (f_feat, f_cash, f_ev)},
                "checks_passed": bool(res["ok"].all())}
    (OUT / "step4_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    el = ~base["churn_excluded"].to_numpy()
    y = base["hard_churn_6m"].astype(float).to_numpy()
    lines = ["# Paso 4 · Investments", "",
             f"Semilla `{cfg['master_seed']}` · {len(base):,} hogares ({int(inv.sum()):,} con inversiones) · "
             f"montos en {cfg['currency']} · **{int(res['ok'].sum())} de {len(res)} pruebas OK** "
             "(α = 0.01, Benjamini-Hochberg)", "",
             "## Calibración", "", cal.drop(columns=["rango_tasa", "banda_IV"]).to_markdown(floatfmt=",.3f"), "",
             f"AUC combinado de las variables de los Pasos 1–4 (logística): **{extra['AUC combinado']:.3f}**; "
             f"techo: {extra['AUC techo']:.3f}.", "",
             f"## Robustez en {N_REF_SEEDS} semillas de referencia", "",
             refs.groupby("variable")[["tasa_alerta", "IV", "lift_alerta"]].agg(["min", "median", "max"])
             .to_markdown(floatfmt=",.3f"), "",
             "## Eventos simulados (% de hogares con inversiones)", "",
             sim4["events"].loc[inv, ["liquidation", "proprietary_sale", "advisor_derisk", "client_full_sale", "maturity"]]
             .mean().mul(100).to_frame("%").to_markdown(floatfmt=".2f"), ""]
    for sec, g in res.groupby("sección"):
        lines += [f"## {sec}", "", "| Prueba | Detalle | p | p BH | OK |", "|---|---|---|---|---|"]
        for _, r in g.iterrows():
            p = "" if pd.isna(r["p"]) else f"{r['p']:.3g}"
            pb = "" if pd.isna(r.get("p_BH", np.nan)) else f"{r['p_BH']:.3g}"
            lines.append(f"| {r['prueba']} | {r['detalle']} | {p} | {pb} | {'OK' if r['ok'] else '**FALLA**'} |")
        lines.append("")
    num = feats.drop(columns=["household_id"]).astype(float)
    lines += ["## Distribuciones", "", num.describe(percentiles=[.01, .05, .25, .5, .75, .95, .99]).T
              .to_markdown(floatfmt=",.4f"), ""]
    for var in cfg["step4"]["targets"]:
        x = feats[var].astype(float).to_numpy()
        m = el & ~np.isnan(x)
        lines += [f"## WoE · {var}", "", woe_table(pd.Series(x[m]), y[m].astype(int)).to_markdown(floatfmt=",.4f"), ""]
    lines += ["## Diccionario", "", "| Columna | Unidad | Descripción |", "|---|---|---|"]
    lines += [f"| {c} | {u} | {d} |" for c, (u, d) in STEP4_COLUMNS.items()]
    REPORT.write_text("\n".join(lines) + "\n")

    print(cal[["tasa_alerta", "IV", "lift_alerta", "tendencia_z", "null_%"]].round(3).to_string())
    print(f"AUC combinado {extra['AUC combinado']:.3f} vs techo {extra['AUC techo']:.3f}")
    for _, r in res[~res["ok"]].iterrows():
        print(f"FALLA · {r['prueba']} · {r['detalle']}")
    print(f"{int(res['ok'].sum())}/{len(res)} OK")
    return 0 if res["ok"].all() else 1


if __name__ == "__main__":
    raise SystemExit(main())
