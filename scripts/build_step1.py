"""Construye el Paso 1 (Balances & AUM), lo valida y escribe salidas.

Uso: python scripts/build_step1.py
Salidas:
  data/synthetic/step1_balances.csv    -> variables 1, 2, 17, 18 por hogar
  data/synthetic/step1_series.csv      -> series mensuales (formato largo, para auditar)
  data/synthetic/step1_truth.csv       -> episodios y choques simulados (solo validación)
  data/synthetic/step1_manifest.json   -> semilla, flujos, hashes
  docs/reports/step1_report.md         -> calibración, pruebas y distribuciones
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
from synthetic.schema import STEP1_COLUMNS  # noqa: E402
from synthetic.seeds import SeedManager  # noqa: E402
from synthetic.validate_step1 import calibration, check_step1  # noqa: E402

OUT = ROOT / "data" / "synthetic"
REPORT = ROOT / "docs" / "reports" / "step1_report.md"
N_REF_SEEDS = 20


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(cfg, seed):
    seeds = SeedManager(seed)
    base, truth = build_population(cfg, seeds)
    feats, sim = build_step1(base, truth, cfg, seeds)
    return seeds, base, truth, feats, sim


def main() -> int:
    cfg_path = ROOT / "config" / "params.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    seeds, base, truth, feats, sim = build(cfg, cfg["master_seed"])

    # Robustez: la calibración debe sostenerse en otras semillas, no solo en la de producción.
    refs = []
    for s in np.random.SeedSequence(cfg["master_seed"]).generate_state(N_REF_SEEDS):
        c = copy.deepcopy(cfg)
        c["master_seed"] = int(s)
        _, b, _, f, _ = build(c, int(s))
        refs.append(calibration(f, b, c).reset_index().assign(seed=int(s)))
    refs = pd.concat(refs, ignore_index=True)

    res, cal, extra = check_step1(feats, sim, base, truth, cfg, refs)

    OUT.mkdir(parents=True, exist_ok=True)
    f_feat, f_ser, f_tr = OUT / "step1_balances.csv", OUT / "step1_series.csv", OUT / "step1_truth.csv"
    feats.to_csv(f_feat, index=False, float_format="%.8f", lineterminator="\n")
    M = cfg["step1"]["months"]
    months = np.arange(M) - (M - 1)
    ser = pd.DataFrame({
        "household_id": np.repeat(base["household_id"].to_numpy(), M),
        "month": np.tile(months, len(base)),
        "deposit_avg_balance": sim["deposit"].ravel().round(2),
        "aum_month_end": np.where(sim["inv"][:, None], sim["aum"], np.nan).ravel().round(2),
        "aum_contributions": sim["contrib"].ravel().round(2),
        "aum_withdrawals": sim["withdraw"].ravel().round(2),
        "twr_index": sim["twr"].ravel(),
        "available": sim["avail"].ravel(),
    })
    ser.to_csv(f_ser, index=False, float_format="%.6f", lineterminator="\n")
    sim["truth"].to_csv(f_tr, index=False, float_format="%.8f", lineterminator="\n")

    manifest = {
        "step": 1, "master_seed": cfg["master_seed"], "currency": cfg["currency"],
        "params_sha256": sha256(cfg_path), "streams": seeds.issued,
        "outputs": {p.name: {"rows": n, "sha256": sha256(p)}
                    for p, n in [(f_feat, len(feats)), (f_ser, len(ser)), (f_tr, len(sim["truth"]))]},
        "checks_passed": bool(res["ok"].all()),
    }
    (OUT / "step1_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    # --- Reporte --------------------------------------------------------------
    el = ~base["churn_excluded"].to_numpy()
    y = base.loc[el, "hard_churn_6m"].astype(int).to_numpy()
    lines = ["# Paso 1 · Balances & AUM", "",
             f"Semilla `{cfg['master_seed']}` · {len(base):,} hogares × {M} meses · montos en {cfg['currency']} · "
             f"**{int(res['ok'].sum())} de {len(res)} pruebas OK** (α = 0.01, Benjamini-Hochberg)", "",
             "## Calibración", "", cal.to_markdown(floatfmt=",.3f"), "",
             f"AUC combinado de las 4 variables (logística): **{extra['AUC combinado']:.3f}**; "
             f"techo con la probabilidad verdadera: {extra['AUC techo']:.3f}.", "",
             f"## Robustez en {N_REF_SEEDS} semillas de referencia", "",
             refs.groupby("variable")[["tasa_alerta", "IV_hard", "lift_alerta"]].agg(["min", "median", "max"])
             .to_markdown(floatfmt=",.3f"), ""]
    for sec, g in res.groupby("sección"):
        lines += [f"## {sec}", "", "| Prueba | Detalle | p | p BH | OK |", "|---|---|---|---|---|"]
        for _, r in g.iterrows():
            p = "" if pd.isna(r["p"]) else f"{r['p']:.3g}"
            pb = "" if pd.isna(r.get("p_BH")) else f"{r['p_BH']:.3g}"
            lines.append(f"| {r['prueba']} | {r['detalle']} | {p} | {pb} | {'OK' if r['ok'] else '**FALLA**'} |")
        lines.append("")
    desc = feats.drop(columns="household_id").describe(percentiles=[.01, .05, .25, .5, .75, .95, .99]).T
    lines += ["## Distribuciones", "", desc.to_markdown(floatfmt=",.4f"), "",
              "## Correlación de Spearman entre variables", "",
              feats[list(cfg["step1"]["targets"])].corr(method="spearman").to_markdown(floatfmt=".3f"), ""]
    for var in cfg["step1"]["targets"]:
        wt = woe_table(feats.loc[el, var].reset_index(drop=True), y)
        lines += [f"## WoE · {var}", "", wt.to_markdown(floatfmt=",.4f"), ""]
    lines += ["## Diccionario", "", "| Columna | Unidad | Descripción |", "|---|---|---|"]
    lines += [f"| {c} | {u} | {d} |" for c, (u, d) in STEP1_COLUMNS.items()]
    REPORT.write_text("\n".join(lines) + "\n")

    print(cal[["tasa_alerta", "IV_hard", "tendencia_z", "lift_alerta", "null_%"]].round(3).to_string())
    print(f"AUC combinado {extra['AUC combinado']:.3f} vs techo {extra['AUC techo']:.3f}")
    for _, r in res[~res["ok"]].iterrows():
        print(f"FALLA · {r['prueba']} · {r['detalle']}")
    print(f"{int(res['ok'].sum())}/{len(res)} OK")
    return 0 if res["ok"].all() else 1


if __name__ == "__main__":
    raise SystemExit(main())
