"""Construye el Paso 6 (Banker), lo valida y escribe salidas.

Uso: python scripts/build_step6.py
Salidas: data/synthetic/step6_banker.csv, step6_interactions.csv, step6_events.csv, step6_bankers.csv, step6_manifest.json
         docs/reports/step6_report.md
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
from synthetic.schema import STEP6_COLUMNS  # noqa: E402
from synthetic.validate_common import calibration  # noqa: E402
from synthetic.validate_step6 import check_step6  # noqa: E402

OUT = ROOT / "data" / "synthetic"
REPORT = ROOT / "docs" / "reports" / "step6_report.md"
N_REF_SEEDS = 20
STEP = 6


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    cfg_path = ROOT / "config" / "params.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    tg = cfg["step6"]["targets"]
    o = build(cfg, upto=STEP)
    refs = []
    for s in np.random.SeedSequence(cfg["master_seed"]).generate_state(N_REF_SEEDS):
        c = copy.deepcopy(cfg)
        c["master_seed"] = int(s)
        r = build(c, int(s), upto=STEP)
        refs.append(calibration(r["f6"], r["base"], tg).reset_index().assign(seed=int(s)))
    refs = pd.concat(refs, ignore_index=True)
    prev = [o[f"f{k}"][list(cfg[f"step{k}"]["targets"])] for k in range(1, STEP)]
    res, cal, extra = check_step6(o["f6"], o["sim6"], o["base"], o["truth"], o["exit"], prev, cfg, refs)

    base, feats, sim = o["base"], o["f6"], o["sim6"]
    OUT.mkdir(parents=True, exist_ok=True)
    f_feat, f_acc, f_ev = OUT / "step6_banker.csv", OUT / "step6_interactions.csv", OUT / "step6_events.csv"
    feats.to_csv(f_feat, index=False, float_format="%.8f", lineterminator="\n")
    lg = sim["log"].copy()
    lg.insert(0, "household_id", base["household_id"].to_numpy()[lg["hh"]])
    t0 = np.datetime64(pd.Timestamp(cfg["snapshot_date"]).date())
    lg["date"] = t0 + lg["day"].astype(int).to_numpy().astype("timedelta64[D]")
    lg.drop(columns=["hh", "day"]).to_csv(f_acc, index=False, lineterminator="\n")
    sim["events"].to_csv(f_ev, index=False, float_format="%.6f", lineterminator="\n")
    sim["bankers"].to_csv(OUT / "step6_bankers.csv", index=False, float_format="%.6f", lineterminator="\n")
    manifest = {"step": STEP, "master_seed": cfg["master_seed"], "currency": cfg["currency"],
                "params_sha256": sha256(cfg_path), "streams": o["seeds"].issued,
                "outputs": {p.name: {"sha256": sha256(p)} for p in (f_feat, f_acc, f_ev)},
                "checks_passed": bool(res["ok"].all())}
    (OUT / "step6_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    el = ~base["churn_excluded"].to_numpy()
    y = base["hard_churn_6m"].astype(float).to_numpy()
    lines = ["# Paso 6 · Banker", "",
             f"Semilla `{cfg['master_seed']}` · {len(base):,} hogares · {len(sim['bankers'])} bankers · {len(lg):,} interacciones · "
             f"**{int(res['ok'].sum())} de {len(res)} pruebas OK** (α = 0.01, Benjamini-Hochberg)", "",
             "## Calibración", "", cal.drop(columns=["rango_tasa", "banda_IV"]).to_markdown(floatfmt=",.3f"), "",
             f"AUC combinado de las variables de los Pasos 1–5 (logística): **{extra['AUC combinado']:.3f}**; "
             f"techo: {extra['AUC techo']:.3f}.", "",
             f"## Robustez en {N_REF_SEEDS} semillas de referencia", "",
             refs.groupby("variable")[["tasa_alerta", "IV", "lift_alerta"]].agg(["min", "median", "max"])
             .to_markdown(floatfmt=",.3f"), "",
             "## Interacciones por tipo", "", sim["log"]["kind"].value_counts().to_frame("n").to_markdown(), "",
             "## Motivo del cambio de banker", "", sim["events"]["change_reason"].value_counts().to_frame("hogares").to_markdown(), ""]
    for sec, g in res.groupby("sección"):
        lines += [f"## {sec}", "", "| Prueba | Detalle | p | p BH | OK |", "|---|---|---|---|---|"]
        for _, r in g.iterrows():
            p = "" if pd.isna(r["p"]) else f"{r['p']:.3g}"
            pb = "" if pd.isna(r.get("p_BH", np.nan)) else f"{r['p_BH']:.3g}"
            lines.append(f"| {r['prueba']} | {r['detalle']} | {p} | {pb} | {'OK' if r['ok'] else '**FALLA**'} |")
        lines.append("")
    num = feats.drop(columns=["household_id", "banker_change_reason"]).astype(float)
    lines += ["## Distribuciones", "", num.describe(percentiles=[.01, .05, .25, .5, .75, .95, .99]).T.to_markdown(floatfmt=",.4f"), ""]
    for var in tg:
        x = feats[var].astype(float).to_numpy()
        m = el & ~np.isnan(x)
        lines += [f"## WoE · {var}", "", woe_table(pd.Series(x[m]), y[m].astype(int)).to_markdown(floatfmt=",.4f"), ""]
    lines += ["## Diccionario", "", "| Columna | Unidad | Descripción |", "|---|---|---|"]
    lines += [f"| {c} | {u} | {d} |" for c, (u, d) in STEP6_COLUMNS.items()]
    REPORT.write_text("\n".join(lines) + "\n")
    print(cal[["tasa_alerta", "IV", "lift_alerta", "tendencia_z", "null_%"]].round(3).to_string())
    print(f"AUC combinado {extra['AUC combinado']:.3f} vs techo {extra['AUC techo']:.3f}")
    for _, r in res[~res["ok"]].iterrows():
        print(f"FALLA · {r['prueba']} · {r['detalle']}")
    print(f"{int(res['ok'].sum())}/{len(res)} OK")
    return 0 if res["ok"].all() else 1


if __name__ == "__main__":
    raise SystemExit(main())
