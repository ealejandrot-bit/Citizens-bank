"""Construye el Paso 0 (población + latentes + target), lo valida y escribe salidas.

Uso: python scripts/build_step0.py
Salidas:
  data/synthetic/step0_households.csv  -> observables + target (lo que ve el modelo)
  data/synthetic/step0_truth.csv       -> latentes y probabilidades (solo validación)
  data/synthetic/step0_manifest.json   -> semilla, hash de parámetros, flujos, hash de salidas
  docs/reports/step0_report.md         -> chequeos y distribuciones
"""
import hashlib
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from synthetic.population import build_population  # noqa: E402
from synthetic.schema import COLUMNS  # noqa: E402
from synthetic.seeds import SeedManager  # noqa: E402
from synthetic.validate import check_step0, summarize_step0  # noqa: E402

OUT = ROOT / "data" / "synthetic"
REPORT = ROOT / "docs" / "reports" / "step0_report.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    cfg_path = ROOT / "config" / "params.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    seeds = SeedManager(cfg["master_seed"])
    base, truth = build_population(cfg, seeds)

    checks = check_step0(base, truth, cfg)
    tables = summarize_step0(base, truth)

    OUT.mkdir(parents=True, exist_ok=True)
    f_base, f_truth = OUT / "step0_households.csv", OUT / "step0_truth.csv"
    base.to_csv(f_base, index=False, float_format="%.6f", lineterminator="\n")
    truth.to_csv(f_truth, index=False, float_format="%.8f", lineterminator="\n")

    manifest = {
        "step": 0,
        "master_seed": cfg["master_seed"],
        "currency": cfg["currency"],
        "params_sha256": sha256(cfg_path),
        "streams": seeds.issued,
        "intercepts": truth.attrs["intercepts"],
        "outputs": {p.name: {"rows": n, "sha256": sha256(p)}
                    for p, n in [(f_base, len(base)), (f_truth, len(truth))]},
        "checks_passed": all(ok for _, ok, _ in checks),
    }
    (OUT / "step0_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    lines = ["# Paso 0 · Reporte de población, latentes y target", "",
             f"Semilla maestra `{cfg['master_seed']}` · {len(base):,} hogares · corte {cfg['snapshot_date']}"
             f" · montos en {cfg['currency']}", "",
             "## Chequeos", "", "| Chequeo | Resultado | Detalle |", "|---|---|---|"]
    lines += [f"| {n} | {'OK' if ok else '**FALLA**'} | {d} |" for n, ok, d in checks]
    for title, df in tables.items():
        lines += ["", f"## {title[0].upper() + title[1:]}", "", df.to_markdown(floatfmt=",.4f")]
    lines += ["", "## Diccionario de columnas", "", "| Columna | Unidad | Descripción |", "|---|---|---|"]
    lines += [f"| {c} | {COLUMNS[c][0]} | {COLUMNS[c][1]} |" for c in base.columns]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")

    for n, ok, d in checks:
        print(f"[{'OK ' if ok else 'FAIL'}] {n} {d}")
    return 0 if manifest["checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
