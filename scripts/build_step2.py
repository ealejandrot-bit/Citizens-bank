"""Construye el Paso 2 (Recurring deposits & flows), lo valida y escribe salidas.

Uso: python scripts/build_step2.py
Salidas:
  data/synthetic/step2_recurring.csv      -> variables 3, 4, 5, 6, 19, 20 por hogar
  data/synthetic/step2_transactions.csv   -> créditos y débitos recurrentes (auditar la detección)
  data/synthetic/step2_events.csv         -> eventos simulados (solo validación)
  data/synthetic/step2_manifest.json      -> semilla, flujos, hashes
  docs/reports/step2_report.md            -> pruebas, calibración y distribuciones
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

from synthetic.balances import build_step1  # noqa: E402
from synthetic.metrics import woe_table  # noqa: E402
from synthetic.population import build_population  # noqa: E402
from synthetic.recurring import build_step2, transactions_long  # noqa: E402
from synthetic.schema import STEP2_COLUMNS  # noqa: E402
from synthetic.seeds import SeedManager  # noqa: E402
from synthetic.validate_step2 import calibration, check_step2  # noqa: E402

OUT = ROOT / "data" / "synthetic"
REPORT = ROOT / "docs" / "reports" / "step2_report.md"
N_REF_SEEDS = 20


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(cfg, seed):
    seeds = SeedManager(seed)
    base, truth = build_population(cfg, seeds)
    f1, sim1 = build_step1(base, truth, cfg, seeds)
    f2, sim2 = build_step2(base, truth, sim1, cfg, seeds)
    return seeds, base, truth, f1, sim1, f2, sim2


def main() -> int:
    cfg_path = ROOT / "config" / "params.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    seeds, base, truth, f1, sim1, feats, sim2 = build(cfg, cfg["master_seed"])

    refs = []
    for s in np.random.SeedSequence(cfg["master_seed"]).generate_state(N_REF_SEEDS):
        c = copy.deepcopy(cfg)
        c["master_seed"] = int(s)
        _, b, _, _, _, f, _ = build(c, int(s))
        refs.append(calibration(f, b, c["step2"]["targets"]).reset_index().assign(seed=int(s)))
    refs = pd.concat(refs, ignore_index=True)

    res, cal, extra = check_step2(feats, sim2, sim1, f1, base, truth, cfg, refs)

    OUT.mkdir(parents=True, exist_ok=True)
    f_feat, f_tx, f_ev = OUT / "step2_recurring.csv", OUT / "step2_transactions.csv", OUT / "step2_events.csv"
    feats.to_csv(f_feat, index=False, float_format="%.8f", lineterminator="\n")
    tx = transactions_long(sim2, base, cfg["snapshot_date"])
    tx.to_csv(f_tx, index=False, lineterminator="\n")
    sim2["events"].to_csv(f_ev, index=False, float_format="%.8f", lineterminator="\n")
    manifest = {
        "step": 2, "master_seed": cfg["master_seed"], "currency": cfg["currency"],
        "params_sha256": sha256(cfg_path), "streams": seeds.issued,
        "outputs": {p.name: {"rows": n, "sha256": sha256(p)}
                    for p, n in [(f_feat, len(feats)), (f_tx, len(tx)), (f_ev, len(sim2["events"]))]},
        "checks_passed": bool(res["ok"].all()),
    }
    (OUT / "step2_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    el = ~base["churn_excluded"].to_numpy()
    y = base["hard_churn_6m"].astype(float).to_numpy()
    ev = sim2["events"]
    lines = ["# Paso 2 · Recurring deposits & flows", "",
             f"Semilla `{cfg['master_seed']}` · {len(base):,} hogares · {len(tx):,} transacciones en 18 meses · "
             f"montos en {cfg['currency']} · **{int(res['ok'].sum())} de {len(res)} pruebas OK** "
             "(α = 0.01, Benjamini-Hochberg)", "",
             "## Calibración", "", cal.drop(columns=["rango_tasa", "banda_IV"]).to_markdown(floatfmt=",.3f"), "",
             f"AUC combinado de las variables de los Pasos 1 + 2 (logística): **{extra['AUC combinado']:.3f}**; "
             f"techo: {extra['AUC techo']:.3f}.", "",
             f"## Robustez en {N_REF_SEEDS} semillas de referencia", "",
             refs.groupby("variable")[["tasa_alerta", "IV", "lift_alerta"]].agg(["min", "median", "max"])
             .to_markdown(floatfmt=",.3f"), "",
             "## Eventos simulados", "",
             pd.Series({"mudanza del banco principal (propensión)": ev["move"].mean(),
                        "redirección parcial (z_outflow)": ev["partial"].mean(),
                        "negocio muda su operación": ev["business_move"].mean(),
                        "cambio de empleo": ev["job_change"].mean(), "retiro": ev["retire"].mean(),
                        "licencia": ev["leave"].mean(), "muerte / excluidos": ev["death"].mean(),
                        "venta del negocio": ev["business_sale"].mean()}).to_frame("% hogares").mul(100)
             .to_markdown(floatfmt=".2f"), ""]
    for sec, g in res.groupby("sección"):
        lines += [f"## {sec}", "", "| Prueba | Detalle | p | p BH | OK |", "|---|---|---|---|---|"]
        for _, r in g.iterrows():
            p = "" if pd.isna(r["p"]) else f"{r['p']:.3g}"
            pb = "" if pd.isna(r.get("p_BH", np.nan)) else f"{r['p_BH']:.3g}"
            lines.append(f"| {r['prueba']} | {r['detalle']} | {p} | {pb} | {'OK' if r['ok'] else '**FALLA**'} |")
        lines.append("")
    num = feats.drop(columns=["household_id", "recurring_deposit_stopped_type"]).astype(float)
    lines += ["## Distribuciones", "", num.describe(percentiles=[.01, .05, .25, .5, .75, .95, .99]).T
              .to_markdown(floatfmt=",.4f"), "",
              "## Correlación de Spearman (Pasos 1 + 2)", "",
              pd.concat([f1[list(cfg["step1"]["targets"])], num[list(cfg["step2"]["targets"])]], axis=1)
              .corr(method="spearman").to_markdown(floatfmt=".2f"), ""]
    for var, t in cfg["step2"]["targets"].items():
        x = feats[var].astype(float).to_numpy()
        m = el & ~np.isnan(x) if t["iv_base"] == "applicable" else el
        lines += [f"## WoE · {var}", "", woe_table(pd.Series(x[m]), y[m].astype(int)).to_markdown(floatfmt=",.4f"), ""]
    lines += ["## Diccionario", "", "| Columna | Unidad | Descripción |", "|---|---|---|"]
    lines += [f"| {c} | {u} | {d} |" for c, (u, d) in STEP2_COLUMNS.items()]
    REPORT.write_text("\n".join(lines) + "\n")

    print(cal[["tasa_alerta", "IV", "lift_alerta", "tendencia_z", "null_%"]].round(3).to_string())
    print(f"AUC combinado {extra['AUC combinado']:.3f} vs techo {extra['AUC techo']:.3f}")
    for _, r in res[~res["ok"]].iterrows():
        print(f"FALLA · {r['prueba']} · {r['detalle']}")
    print(f"{int(res['ok'].sum())}/{len(res)} OK")
    return 0 if res["ok"].all() else 1


if __name__ == "__main__":
    raise SystemExit(main())
