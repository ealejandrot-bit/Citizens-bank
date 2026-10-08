"""Genera reports/<fecha>_<estrategia>.md con métricas vs. comprar y mantener y curva de equity (PNG).

Uso:
  python -m src.report trend_daily             # datos reales (requiere check_connection.py OK y data/*.parquet)
  python -m src.report vwap_intraday
  python -m src.report trend_daily --sintetico # demo con datos sintéticos (NO es GLD)
"""
from __future__ import annotations

import argparse
import math
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from src.backtest.costs import CostModel  # noqa: E402
from src.backtest.metrics import ETIQUETAS, PCT, RF  # noqa: E402
from src.backtest.runner import BENCHMARK, PeriodRun, pdt_resumen, run_strategy  # noqa: E402
from src.config import load_config, path_in_root, require_connection_check  # noqa: E402
from src.data import synthetic  # noqa: E402
from src.data.loader import load_bars  # noqa: E402

TIMEFRAME = {"trend_daily": "1d", "vwap_intraday": "5m"}


def fmt(key: str, v) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    if key in PCT:
        return f"{v * 100:.2f}%"
    if key in ("n_operaciones", "max_dd_dias"):
        return f"{int(v)}"
    return f"{v:,.2f}" if key != "sharpe" else f"{v:.2f}"


def metrics_table(run: PeriodRun) -> str:
    names = list(run.metricas)
    lines = ["| Métrica | " + " | ".join(names) + " |", "|---|" + "---:|" * len(names)]
    if not all(m.get("operable") for m in run.metricas.values()):
        lines.append("| Estado | " + " | ".join(
            "operable" if run.metricas[n].get("operable") else "**no operable**" for n in names) + " |")
    for key, label in ETIQUETAS.items():
        cells = []
        for n in names:
            m = run.metricas[n]
            if not m.get("operable"):
                cells.append("—")
                continue
            c = fmt(key, m[key])
            if key == "max_dd_dias" and not m["max_dd_recuperado"]:
                c += " (sin recuperar)"
            cells.append(c)
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def diff_table(run: PeriodRun) -> str:
    lines = ["| Estrategia | Δ CAGR | Δ Sharpe | Δ Drawdown máx. |", "|---|---:|---:|---:|"]
    for n, d in run.diferencias.items():
        if not d:
            lines.append(f"| {n} | — | — | — |")
        else:
            lines.append(f"| {n} | {d['cagr'] * 100:+.2f} pp | {d['sharpe']:+.2f} | {d['max_dd'] * 100:+.2f} pp |")
    return "\n".join(lines)


def plot_equity(run: PeriodRun, path: Path, titulo: str) -> bool:
    ops = {n: r for n, r in run.resultados.items() if r.operable}
    if not ops:
        return False
    fig, ax = plt.subplots(figsize=(10, 5))
    for n, r in ops.items():
        style = {"color": "#555555", "linestyle": "--", "linewidth": 1.4} if n == BENCHMARK else {"linewidth": 1.6}
        ax.plot(r.daily_equity.index, r.daily_equity.values, label=n, **style)
    ax.set_title(titulo)
    ax.set_ylabel("Equity (USD)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return True


def supuestos(estrategia: str, cfg: dict, costs: CostModel, sintetico: bool, check: dict | None) -> list[str]:
    s = []
    if sintetico:
        s.append("**DATOS SINTÉTICOS.** Este reporte es una demostración del motor; no representa a GLD.")
    s += [
        "Señal con datos hasta el cierre de la barra t; ejecución en la apertura de la barra t+1.",
        "Cada periodo (in-sample, out-of-sample, total) es un backtest independiente que arranca con el "
        "capital inicial; los datos previos al inicio solo calientan indicadores.",
        "Comprar y mantener: compra en la apertura de la primera barra del periodo y vende al cierre de "
        "la última, con comisión y slippage. Las estrategias también liquidan al cierre de la última barra.",
        f"Comisión IBKR Pro fija: {costs.comision_por_accion} USD/acción, mínimo {costs.comision_minima:.2f} USD, "
        f"tope {costs.comision_maxima_pct * 100:.1f}% del valor. Verificar contra la tabla vigente de IBKR.",
        f"Slippage fijo de {costs.slippage:.2f} USD por acción por lado.",
        f"Conversión MXN→USD: {costs.conversion_mxn_usd:.2f} USD único al inicio (estrategia y benchmark).",
        f"Datos de mercado: {costs.datos_mensual:.2f} USD/mes, solo a la estrategia (el benchmark no los necesita).",
        f"Sharpe con rf = {RF:.0%}; volatilidad y Sharpe anualizados con 252 días hábiles; CAGR en días naturales.",
        "Win rate y ganancia/pérdida promedio por operación cerrada, netas de comisión y slippage.",
        "GLD no paga dividendos; no se modelan impuestos ni intereses sobre el efectivo.",
    ]
    if cfg["fracciones"]:
        s.append(f"Acciones fraccionarias permitidas (hasta {cfg.get('decimales_fraccion', 4)} decimales).")
    else:
        s.append("Solo acciones enteras (fracciones: false). Si el capital no alcanza 1 acción, el periodo se "
                 "reporta como «no operable» y no se simula.")
    if float(cfg["capital_inicial"]) < 1000:
        s.append("Con capital tan pequeño la comisión mínima (o su tope de 1%) pesa mucho en cada operación.")
    if estrategia == "vwap_intraday":
        s += [
            "Solo horario regular (9:30–16:00 ET); primera ejecución posible a las 10:00; salida forzada en la "
            "apertura de la barra de 15:55 ET; las dos últimas barras del día siempre deciden efectivo.",
            "VWAP del día con precio típico (h+l+c)/3 de cada barra de 5 min (aproximación).",
            "Regla de pattern day trader: 4 o más day trades en 5 días hábiles en cuenta de margen con menos de "
            "25,000 USD restringe la cuenta.",
        ]
    if check and check.get("marketDataType") not in (None, 1):
        s.append(f"La cuenta usó marketDataType={check['marketDataType']} (datos con retraso) en el snapshot; "
                 "los históricos no dependen de ello, pero la operación en vivo sí.")
    return s


def build_report(estrategia: str, cfg: dict, bars: pd.DataFrame, out_dir: Path,
                 sintetico: bool = False, check: dict | None = None, hoy: date | None = None) -> Path:
    hoy = hoy or date.today()
    out_dir.mkdir(parents=True, exist_ok=True)
    base = f"{hoy:%Y-%m-%d}_{estrategia}" + ("_sintetico" if sintetico else "")
    runs = run_strategy(estrategia, bars, cfg)
    costs = CostModel.from_config(cfg, intradia=estrategia == "vwap_intraday")
    total = runs[-1]
    png = out_dir / f"{base}.png"
    has_png = plot_equity(total, png, f"{cfg['simbolo']} · {estrategia} · periodo total"
                          + (" (sintético)" if sintetico else ""))

    md = [f"# Reporte {estrategia} — {cfg['simbolo']}" + (" (DATOS SINTÉTICOS)" if sintetico else ""), ""]
    md.append(f"Generado: {hoy:%Y-%m-%d}. Datos: {bars.index[0]:%Y-%m-%d} → {bars.index[-1]:%Y-%m-%d} "
              f"({len(bars)} barras).")
    md += ["", "## Configuración", "",
           f"- Capital inicial: {float(cfg['capital_inicial']):.2f} {cfg['moneda']}",
           f"- Fracciones: {cfg['fracciones']}",
           f"- Comisión: {costs.comision_por_accion} USD/acción, mín. {costs.comision_minima:.2f}, "
           f"máx. {costs.comision_maxima_pct * 100:.1f}% del valor",
           f"- Slippage: {costs.slippage:.2f} USD/acción/lado",
           f"- Conversión MXN→USD: {costs.conversion_mxn_usd:.2f} USD · Datos: {costs.datos_mensual:.2f} USD/mes",
           f"- Parámetros: `{cfg['estrategias'][estrategia]}`",
           "- Periodos: " + "; ".join(f"{r.periodo} {r.inicio} → {r.fin}" for r in runs)]

    for r in runs:
        md += ["", f"## {r.periodo} ({r.inicio} → {r.fin})", "", metrics_table(r), "",
               "**Diferencia vs. comprar y mantener** (estrategia − benchmark):", "", diff_table(r)]
        notas = [res.nota for res in r.resultados.values() if not res.operable]
        if notas:
            md += [""] + [f"> {n}" for n in dict.fromkeys(notas)]
        if estrategia == "vwap_intraday":
            for n, res in r.resultados.items():
                if n == BENCHMARK or not res.operable:
                    continue
                p = pdt_resumen(res)
                md += ["", f"**Day trades ({n})**: total {p['day_trades_total']}; máximo en una ventana de 5 días "
                       f"hábiles: {p['max_por_ventana']}; ventanas con ≥ 4: {p['ventanas_con_4_o_mas']} de "
                       f"{p['ventanas']}."]

    md += ["", "## Curva de equity (periodo total)", ""]
    md.append(f"![Equity]({png.name})" if has_png else "_Sin curva: ninguna serie fue operable._")
    md += ["", "## Supuestos y advertencias", ""]
    md += [f"- {x}" for x in supuestos(estrategia, cfg, costs, sintetico, check)]
    path = out_dir / f"{base}.md"
    path.write_text("\n".join(md) + "\n", encoding="utf-8")
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("estrategia", choices=list(TIMEFRAME))
    ap.add_argument("--sintetico", action="store_true", help="demo con datos sintéticos")
    args = ap.parse_args()
    cfg = load_config()
    out_dir = path_in_root(cfg["rutas"]["reportes"])
    check = None
    if args.sintetico:
        if args.estrategia == "trend_daily":
            bars = synthetic.daily_bars(n=5300, start="2005-01-03", price0=50, drift=0.0003, vol=0.011, seed=7)
        else:
            bars = synthetic.intraday_bars(n_days=700, start="2023-01-02", price0=170, seed=7)
    else:
        check = require_connection_check()
        bars = load_bars(path_in_root(cfg["rutas"]["datos"]), cfg["simbolo"], TIMEFRAME[args.estrategia])
    print(build_report(args.estrategia, cfg, bars, out_dir, args.sintetico, check))


if __name__ == "__main__":
    main()
