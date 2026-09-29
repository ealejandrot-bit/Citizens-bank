"""Pruebas estadísticas del Paso 0 y reporte.

Uso: python scripts/stats_step0.py [--quick]
  --quick : sin semillas de referencia ni estudio t (para tests rápidos).
Salida: docs/reports/step0_stats_report.md. Código de salida 1 si alguna prueba falla.
"""
import argparse
import copy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from synthetic import stats_tests as st  # noqa: E402
from synthetic.population import build_population  # noqa: E402
from synthetic.seeds import SeedManager  # noqa: E402

REPORT = ROOT / "docs" / "reports" / "step0_stats_report.md"


def run(quick: bool = False) -> tuple[pd.DataFrame, dict]:
    cfg = yaml.safe_load((ROOT / "config" / "params.yaml").read_text())
    vcfg = yaml.safe_load((ROOT / "config" / "validation.yaml").read_text())
    alpha = vcfg["alpha"]
    base, truth = build_population(cfg, SeedManager(cfg["master_seed"]))

    results = []
    results += st.goodness_of_fit(base, cfg)
    results += st.latent_tests(truth, cfg)
    results += st.target_tests(base, truth, cfg)
    results += st.kurtosis_tests(base, cfg, alpha)
    results += st.money_tests(base, cfg, vcfg)
    results += st.bias_tests(base, truth)
    dup_res, dup_info = st.duplicate_tests(base, truth)
    results += dup_res
    extras = {"colas": st.tail_table(base), "variedad": dup_info}

    if not quick:
        # Semillas de referencia derivadas de la maestra (distintas de ella, reproducibles).
        ref_seeds = np.random.SeedSequence(cfg["master_seed"]).generate_state(vcfg["reference_seeds"])
        rows, tails = [], []
        for s in ref_seeds:
            c = copy.deepcopy(cfg)
            c["master_seed"] = int(s)
            b, t = build_population(c, SeedManager(int(s)))
            rows.append(st.seed_metrics(b, t, c))
            tails.append(st.tail_table(b))
        refs = pd.DataFrame(rows)
        seed_res, seed_tab = st.seed_robustness(st.seed_metrics(base, truth, cfg), refs)
        results += seed_res
        extras["semillas"] = seed_tab
        # Estadísticos de cola: p-valor empírico bilateral de la semilla de producción frente
        # a las semillas de referencia; entra en la corrección BH junto con el resto.
        stack = pd.concat(tails, keys=range(len(tails)))
        extras["colas_ref"] = stack
        tc = vcfg["t_study"]
        extras["t"] = st.t_df_study(tc["nus"], tc["n"], tc["replicas"], cfg["master_seed"])

    df = pd.DataFrame(results)
    has_p = df["p"].notna()
    df.loc[has_p, "p_BH"] = st.bh_adjust(df.loc[has_p, "p"].to_numpy())
    df.loc[has_p, "ok"] = df.loc[has_p, "p_BH"] > alpha
    df["ok"] = df["ok"].astype(bool)

    if "colas_ref" in extras:
        tt, stack = extras["colas"], extras["colas_ref"]
        k = stack.index.get_level_values(0).nunique()
        rows = []
        for col in ["media", "curtosis_exceso", "curtosis_exceso_log", "L_curtosis", "hill_alpha_top1%"]:
            for var in tt.index:
                r = stack.xs(var, level=1)[col].to_numpy()
                v = tt.loc[var, col]
                rank = (np.sum(r < v) + 0.5 * np.sum(r == v) + 0.5) / (k + 1)
                rows.append({"sección": "D · Colas y curtosis", "prueba": f"{col} típico vs semillas: {var}",
                             "estadístico": v, "gl": None, "p": 2 * min(rank, 1 - rank),
                             "criterio": f"p empírico vs {k} semillas",
                             "detalle": f"percentil {100 * rank:.1f}", "ok": None})
        df = pd.concat([df.drop(columns=["p_BH"]), pd.DataFrame(rows)], ignore_index=True)
        has_p = df["p"].notna()
        df.loc[has_p, "p_BH"] = st.bh_adjust(df.loc[has_p, "p"].to_numpy())
        df.loc[has_p, "ok"] = df.loc[has_p, "p_BH"] > alpha
        df["ok"] = df["ok"].astype(bool)
    return df, extras


def fmt(x, nd=4):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return ""
    if isinstance(x, (int, np.integer)):
        return f"{x:,}"
    if isinstance(x, (float, np.floating)):
        return f"{x:.2e}" if (abs(x) < 1e-3 and x != 0) or abs(x) >= 1e6 else f"{x:,.{nd}f}"
    return str(x)


def write_report(df: pd.DataFrame, extras: dict) -> None:
    lines = ["# Paso 0 · Pruebas estadísticas", "",
             f"**{int(df['ok'].sum())} de {len(df)} pruebas OK.** α = 0.01 con corrección Benjamini-Hochberg "
             "sobre todas las pruebas con p-valor. Montos en USD.", "",
             "## Resumen por sección", "", "| Sección | Pruebas | OK |", "|---|---|---|"]
    for sec, g in df.groupby("sección"):
        lines.append(f"| {sec} | {len(g)} | {int(g['ok'].sum())} |")
    for sec, g in df.groupby("sección"):
        lines += ["", f"## {sec}", "", "| Prueba | Estadístico | gl | p | p BH | Criterio | Detalle | OK |",
                  "|---|---|---|---|---|---|---|---|"]
        for _, r in g.iterrows():
            gl = "" if r["gl"] is None or pd.isna(r["gl"]) else f"{int(r['gl'])}"
            lines.append(f"| {r['prueba']} | {fmt(r['estadístico'])} | {gl} | {fmt(r['p'])} | {fmt(r['p_BH'])} | "
                         f"{r['criterio']} | {r['detalle']} | {'OK' if r['ok'] else '**FALLA**'} |")
    lines += ["", "## Perfil de colas por columna (USD, valores > 0)", "",
              extras["colas"].to_markdown(floatfmt=",.3f")]
    if "t" in extras:
        lines += ["", "## Grados de libertad de la t-Student (estudio para los Pasos 1+)", "",
                  "Réplicas de n = 20,000. La curtosis de exceso teórica de t(ν) es 6/(ν−4): infinita para ν ≤ 4.", "",
                  extras["t"].to_markdown(floatfmt=",.3f")]
    if "semillas" in extras:
        lines += ["", f"## Semilla de producción vs {len(extras['colas_ref'].index.get_level_values(0).unique())} semillas de referencia", "",
                  extras["semillas"].to_markdown(floatfmt=",.4f")]
    lines += ["", "## Variedad", ""] + [f"- {k}: {fmt(v)}" for k, v in extras["variedad"].items()]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    df, extras = run(quick=args.quick)
    if not args.quick:
        write_report(df, extras)
    for sec, g in df.groupby("sección"):
        print(f"{sec}: {int(g['ok'].sum())}/{len(g)}")
    for _, r in df[~df["ok"]].iterrows():
        print(f"  FALLA · {r['prueba']} · stat={fmt(r['estadístico'])} p={fmt(r['p'])} p_BH={fmt(r['p_BH'])} · {r['detalle']}")
    return 0 if df["ok"].all() else 1


if __name__ == "__main__":
    raise SystemExit(main())
