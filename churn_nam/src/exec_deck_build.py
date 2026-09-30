"""Reporte ejecutivo (4 diapositivas, formato Slides 1920×1080): base sintética, variables, comparación de modelos y
arquetipos por modelo. Los números salen de outputs/final/ y outputs/p10/ (exec_deck_data.py, fase 10) y, para la base
sintética, de los documentos del generador (../docs/decisiones.md, ../README.md). Escribe reports/exec_deck/project/.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone

import pandas as pd

from config import P, ROOT

OUT = ROOT / "reports" / "exec_deck" / "project"
(OUT / "slides").mkdir(parents=True, exist_ok=True)
FIN = P.out(0).parent / "final"
FONT = "font-family:'Inter',sans-serif"
INK, MUTED, LINE, ACCENT, ALITE, SOFT = "#14213D", "#5B6475", "#D9DEE7", "#0F766E", "#B45309", "#F4F6F9"
e = html.escape


def section(sid, title, kicker, body, notes, foot=""):
    head = (f'<div style="display:flex;flex-direction:column;gap:8px">'
            f'<div style="font-size:22px;font-weight:600;letter-spacing:2px;color:{ACCENT};text-transform:uppercase">{e(kicker)}</div>'
            f'<div style="font-size:52px;font-weight:700;color:{INK};line-height:1.1">{e(title)}</div></div>')
    ft = f'<div style="font-size:17px;color:{MUTED};line-height:1.35">{foot}</div>' if foot else ""
    return (f'<section id="{sid}" style="background:#FFFFFF;padding:56px 80px 44px 80px;display:flex;flex-direction:column;gap:28px;'
            f'width:1920px;height:1080px;box-sizing:border-box;{FONT};color:{INK}">{head}'
            f'<div style="flex:1;display:flex;gap:40px;min-height:0">{body}</div>{ft}<aside>{e(notes)}</aside></section>')


# ── 1 · Base sintética ───────────────────────────────────────────────────────────────────────────────────────
DEC = (ROOT.parent / "docs" / "decisiones.md").read_text(encoding="utf-8")
ceiling = re.search(r"techo sigue en (0\.\d+)", DEC).group(1)
auc37 = re.search(r"AUC combinado de las 37 variables es (0\.\d+)", DEC).group(1)
steps = [("0", "Población", "20,000 hogares · RV lognormal (mediana $4M, piso $1M) · cola Pareto sobre $30M (UHNW ≈ 5.5%)"),
         ("1", "Saldos y AUM", "24 meses de depósitos y AUM · beta de mercado · episodios de salida y choques de liquidez"),
         ("2", "Depósitos recurrentes", "≈ 520 mil transacciones en calendario EE. UU. · algoritmo de detección del Excel"),
         ("3", "Transferencias", "≈ 3.2 millones de transferencias que cuadran al centavo con los saldos · 111 instituciones"),
         ("4", "Inversiones", "Rendimiento vs benchmark ligado al servicio · ventas a cash · vencimientos no reinvertidos"),
         ("5", "Relación y cierres", "≈ 90 mil cuentas con fecha y motivo de cierre · share of wallet con 3 fuentes de estimación"),
         ("6", "Banquero", "Libros de ~60 HNW / ~25 UHNW · salida del banquero por libro · ≈ 300 mil interacciones"),
         ("7", "Quejas", "≈ 5,500 quejas con ciclo de vida (SLA, escalamiento, reapertura) · Assistant solo en piloto"),
         ("8", "Externas y compuestas", "Multi-señal desde umbrales del Excel · buró con interruptor legal (FCRA)")]
rows = "".join(f'<div style="display:flex;gap:20px;align-items:baseline;padding:10px 0;border-bottom:1px solid {LINE}">'
               f'<div style="font-size:26px;font-weight:700;color:{ACCENT};width:36px">{n}</div>'
               f'<div style="font-size:25px;font-weight:600;width:300px">{e(t)}</div>'
               f'<div style="font-size:22px;color:{MUTED};flex:1;line-height:1.3">{e(d)}</div></div>' for n, t, d in steps)
facts = [("Diseño causal", "3 factores latentes correlacionados (salida, desatención, servicio). Las variables salen de los factores, nunca del target."),
         ("Target", "Se simulan los 6 meses posteriores al corte (31-dic-2025). Hard churn 6M ≈ 6%; soft churn 3M = caída > 20% sin salida total."),
         ("Realismo", "NULL ≠ 0 según a quién aplica cada variable; ruido t(6); señales raras con alto lift; umbrales del Excel recalibrables."),
         ("Techo", f"AUC máximo alcanzable {ceiling} (probabilidad verdadera); las 37 variables juntas llegan a {auc37}."),
         ("Validación", "Cada paso con 20 semillas y 200 pruebas estadísticas (α 0.01, Benjamini-Hochberg).")]
fx = "".join(f'<div style="display:flex;flex-direction:column;gap:4px"><div style="font-size:24px;font-weight:700;color:{INK}">{e(a)}</div>'
             f'<div style="font-size:22px;color:{MUTED};line-height:1.3">{e(b)}</div></div>' for a, b in facts)
body1 = (f'<div style="flex:1.45;display:flex;flex-direction:column">{rows}</div>'
         f'<div style="flex:1;display:flex;flex-direction:column;gap:22px;background:{SOFT};padding:32px 36px;border-radius:16px">'
         f'<div style="font-size:30px;font-weight:700;color:{ACCENT}">20,000 hogares × 62 columnas</div>{fx}</div>')
s1 = section("base", "Cómo se construyó la base sintética", "1 · Datos",
             body1, "Fuente: docs/decisiones.md (D-01 a D-25) y README del generador. Cada paso se especificó, construyó y validó antes del siguiente.",
             "Generador reproducible con semillas por nombre (SHA-256). Una sola foto al 31-dic-2025: valida pipeline y metodología, no conclusiones sobre clientes reales.")

# ── 2 · Variables ────────────────────────────────────────────────────────────────────────────────────────────
V = pd.read_csv(FIN / "deck_variables.csv")
META = json.load(open(FIN / "deck_archetypes_meta.json"))


def num(x, unit):
    v = float(x)
    if unit.startswith("USD"):
        a = abs(v)
        s = f"${a / 1e6:.0f}M" if a >= 1e7 else f"${a / 1e6:.1f}M" if a >= 1e6 else f"${a / 1e3:.0f}k" if a >= 1e3 else f"${a:.0f}"
        return ("−" if v < 0 else "") + s
    if abs(v) >= 100:
        return f"{v:,.0f}"
    return f"{v:.2f}".rstrip("0").rstrip(".") if v != int(v) else f"{int(v)}"


def rng(r, unit, tipo):
    if tipo == "bool" or r.strip() in ("0 – 1", "2 valores") and unit in ("0/1", "bool", "categoría"):
        return "HNW / UHNW" if unit == "categoría" else "0 / 1"
    m = re.match(r"\s*(-?[\d.e+]+)\s*–\s*(-?[\d.e+]+)", r)
    return f"{num(m.group(1), unit)} a {num(m.group(2), unit)}" if m else r


BLOCKS = ["estructural", "patrimonial", "producto", "relación", "transaccional", "economía", "servicio"]
pred = V[V.estado == "predictor"].copy()
pred["o"] = pred.bloque.map({b: i for i, b in enumerate(BLOCKS)})
pred = pred.sort_values(["o"], kind="stable")
items = []
for b, g in pred.groupby("bloque", sort=False):
    items.append(("h", f"{b} ({len(g)})"))
    for _, r in g.iterrows():
        unit = str(r.unidad)
        det = [unit, rng(str(r["rango [DATA]"]), unit, r.tipo)]
        if r["% missing [DATA]"] > 0:
            det.append(f"falta {r['% missing [DATA]']:.0f}%" if r["% missing [DATA]"] >= 1 else f"falta {r['% missing [DATA]']:.1f}%")
        d = str(r["dirección esperada"])
        det.append({"+": "↑ riesgo", "−": "↓ riesgo"}.get(d, "sin signo"))
        tags = " ".join(t for t, c in (("L", "A-lite"), ("1", "M1"), ("2", "M2 EBM")) if r[c])
        items.append(("r", r.columna, " · ".join(det), tags))
per = -(-len(items) // 3)
cols = [items[i * per:(i + 1) * per] for i in range(3)]


def render_item(it):
    if it[0] == "h":
        return f'<div style="font-size:15px;font-weight:700;color:{ACCENT};text-transform:uppercase;letter-spacing:1px;padding:6px 0 2px 0">{e(it[1])}</div>'
    tag = f' <span style="color:{ALITE};font-weight:700">[{e(it[3])}]</span>' if it[3] else ""
    return f'<div style="font-size:15px;line-height:1.3;color:{MUTED}"><b style="color:{INK};font-weight:600">{e(it[1])}</b>{tag} {e(it[2])}</div>'


body2 = "".join(f'<div style="flex:1;display:flex;flex-direction:column;gap:3px">{"".join(render_item(i) for i in c)}</div>' for c in cols)
nv = META["n variables"]
excl = V[V.estado != "predictor"].groupby("estado").columna.apply(lambda s: ", ".join(s))
foot2 = (f'<b style="color:{INK}">{len(pred)} predictores.</b> [L] A-lite ({nv["A-lite"]}) · [1] Scorecard M1 ({nv["M1"]}; además 3 derivadas: {e(", ".join(META["M1 derivadas"]))}) · '
         f'[2] EBM M2 ({nv["M2 EBM"]}) · M3 (EBM, LightGBM, XGBoost, NAM) usa las {len(pred)} + {len(META["M3 indicadores de missing"])} indicadores de missing = {nv["M3"]}. '
         f'Excluidas: {e(excl.get("excluida (regulatorio)", ""))} (regulatorio); {e(excl.get("excluida (compuesta, regla no documentada)", ""))} (compuesta, regla no documentada). '
         f'Resultados (nunca predictores): {e(excl.get("resultado / id (nunca predictor)", ""))}.')
s2 = section("variables", "Qué variables se usaron: límites y detalles", "2 · Variables", body2,
             "Fuente: diccionario del M1 (step02_dictionary.csv) y listas de variables de cada modelo. Rango = mínimo y máximo observados; 'falta' = % de hogares sin dato (muchos por diseño: la variable no aplica).",
             foot2)

# ── 3 · Comparación de modelos ───────────────────────────────────────────────────────────────────────────────
C = pd.read_csv(FIN / "comparison_all_methods.csv")
DEC10 = json.load(open(P.out(10) / "decision.json"))
FAM = {"A-lite": "Scoring", "Scorecard M1": "Scoring", "Logística L2": "Scoring", "EBM M2": "ML", "EBM M3": "ML", "LightGBM": "ML",
       "XGBoost": "ML", "LightGBM monótono": "ML", "Red neuronal NAM": "Red neuronal"}
C["familia"] = C.modelo.map(FAM)
assert C.familia.notna().all()
C["o"] = C.familia.map({"Scoring": 0, "ML": 1, "Red neuronal": 2}) + (C.modelo != "A-lite") * 0.5
C = C.sort_values(["o", "PR-AUC A (justo)"], ascending=[True, False])
base_rate = DEC10["eventos A"] / DEC10["hogares"]
pmax = C["PR-AUC A (justo)"].max()
hdr = [("Modelo", 330), ("Variables", 120), ("PR-AUC hard 6M", 420), ("Lift top 5%", 150), ("AUC", 110), ("PR-AUC churn B", 170)]
H = "".join(f'<div style="width:{w}px;font-size:18px;font-weight:700;color:{MUTED};text-transform:uppercase;letter-spacing:1px">{e(t)}</div>' for t, w in hdr)
R, fam_prev = [], None
for _, r in C.iterrows():
    if r.familia != fam_prev:
        R.append(f'<div style="font-size:19px;font-weight:700;color:{ACCENT};text-transform:uppercase;letter-spacing:1.5px;padding:10px 0 2px 0">{e(r.familia)}</div>')
        fam_prev = r.familia
    al = r.modelo == "A-lite"
    col = ALITE if al else ACCENT
    w = int(300 * r["PR-AUC A (justo)"] / pmax)
    R.append(f'<div style="display:flex;align-items:center;padding:7px 0;border-bottom:1px solid {LINE}{";background:#FFF7ED" if al else ""}">'
             f'<div style="width:330px;font-size:24px;font-weight:{700 if al else 600}">{e(r.modelo)}</div>'
             f'<div style="width:120px;font-size:24px">{int(r.variables)}</div>'
             f'<div style="width:420px;display:flex;align-items:center;gap:14px"><div style="width:{w}px;height:20px;background:{col};border-radius:4px"></div>'
             f'<div style="font-size:24px;font-weight:700">{r["PR-AUC A (justo)"]:.3f}</div></div>'
             f'<div style="width:150px;font-size:24px">{r["lift@5% A (justo)"]:.2f}</div>'
             f'<div style="width:110px;font-size:24px">{r["AUC A (justo)"]:.3f}</div>'
             f'<div style="width:170px;font-size:24px">{r["PR-AUC B (justo)"]:.3f}</div></div>')
oth = C[C.modelo != "A-lite"]
alr = C[C.modelo == "A-lite"].iloc[0]
lo_ci, hi_ci = DEC10["ΔPR-AUC IC95"]
ll, lh = DEC10["Δlift@5% IC95"]
pts = [("Todos los modelos ricos empatan", f"Con {int(oth.variables.min())} a {int(oth.variables.max())} variables, PR-AUC entre {oth['PR-AUC A (justo)'].min():.3f} y {oth['PR-AUC A (justo)'].max():.3f} "
        f"(azar = {base_rate:.3f}). Más complejidad no compra más señal en esta base."),
       ("A-lite: el más simple", f"{int(alr.variables)} variables, PR-AUC {alr['PR-AUC A (justo)']:.3f} y lift {alr['lift@5% A (justo)']:.2f}: el más bajo, pero explicable en una página y congelado."),
       ("Gate NAM vs A-lite: no pasa", f"ΔPR-AUC +{DEC10['ΔPR-AUC']:.3f} (IC 95% {lo_ci:+.3f} a {hi_ci:+.3f}) sí; Δlift top 5% {DEC10['Δlift@5%']:+.2f} (IC {ll:+.2f} a {lh:+.2f}) no. "
        f"La red neuronal no reemplaza a A-lite.")]
P3 = "".join(f'<div style="display:flex;flex-direction:column;gap:6px"><div style="font-size:26px;font-weight:700;color:{INK}">{e(a)}</div>'
             f'<div style="font-size:22px;color:{MUTED};line-height:1.35">{e(b)}</div></div>' for a, b in pts)
body3 = (f'<div style="width:1300px;display:flex;flex-direction:column"><div style="display:flex;padding-bottom:6px;border-bottom:2px solid {INK}">{H}</div>{"".join(R)}</div>'
         f'<div style="flex:1;display:flex;flex-direction:column;gap:26px;background:{SOFT};padding:30px 32px;border-radius:16px">{P3}</div>')
s3 = section("modelos", "Comparación de modelos: scoring, ML y red neuronal", "3 · Resultados", body3,
             "Fuente: outputs/final/comparison_all_methods.csv y outputs/p10/decision.json. Test abierto una sola vez con el gate pre-registrado.",
             f"Test ∩ holdout de A-lite (fuera del desarrollo de todos): {DEC10['hogares']:,} hogares, {DEC10['eventos A']} eventos hard 6M. PR-AUC = precisión promedio para encontrar a quien se va; "
             f"lift top 5% = cuántas veces la tasa base se concentra en el 5% más riesgoso. Churn B = hard ∪ soft con pérdida ≥ 25% del RV.")

# ── 4 · Arquetipos por modelo ────────────────────────────────────────────────────────────────────────────────
A = pd.read_csv(FIN / "deck_archetypes.csv")
ACT = pd.read_csv(P.m2 / "outputs" / "tables" / "step11_actions.csv").set_index("arquetipo")["acción (playbook M1)"]
MOD = ["A-lite", "Scorecard M1", "EBM M2", "LightGBM", "XGBoost", "EBM M3", "Red neuronal NAM"]
LAB = {"A-lite": "A-lite", "Scorecard M1": "Scorecard M1", "EBM M2": "EBM M2", "LightGBM": "LightGBM", "XGBoost": "XGBoost", "EBM M3": "EBM M3", "Red neuronal NAM": "Red neuronal"}
FAMC = {"A-lite": "Scoring", "Scorecard M1": "Scoring", "EBM M2": "ML", "LightGBM": "ML", "XGBoost": "ML", "EBM M3": "ML", "Red neuronal NAM": "RN"}
CW, LW = 150, 560
hd = (f'<div style="display:flex;align-items:flex-end;padding-bottom:8px;border-bottom:2px solid {INK}"><div style="width:{LW}px;font-size:18px;font-weight:700;color:{MUTED};'
      f'text-transform:uppercase;letter-spacing:1px">Arquetipo (eventos)</div>'
      + "".join(f'<div style="width:{CW}px;display:flex;flex-direction:column;align-items:center;gap:2px"><div style="font-size:15px;font-weight:700;color:{ACCENT}">{FAMC[m]}</div>'
                f'<div style="font-size:21px;font-weight:700;color:{ALITE if m == "A-lite" else INK};text-align:center">{e(LAB[m])}</div></div>' for m in MOD) + "</div>")
rows4 = []
for _, r in A.iterrows():
    tot = r.arquetipo == "total"
    name = "Todos los eventos" if tot else r.arquetipo.capitalize()
    sub = f"{int(r['eventos B'])} eventos · {r['% de eventos B']:.0f}%" + ("" if tot else f" · {ACT[r.arquetipo]}")
    cells = ""
    for m in MOD:
        v = r[m]
        a = min(1.0, v / 100)
        bg = f"rgba(15,118,110,{0.08 + 0.72 * a:.2f})"
        fg = "#FFFFFF" if a > 0.5 else INK
        cells += (f'<div style="width:{CW - 10}px;height:84px;display:flex;align-items:center;justify-content:center;background:{bg};border-radius:10px;'
                  f'font-size:30px;font-weight:700;color:{fg}">{v:.0f}%</div>')
    rows4.append(f'<div style="display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid {LINE}">'
                 f'<div style="width:{LW - 10}px;display:flex;flex-direction:column;gap:4px"><div style="font-size:28px;font-weight:700">{e(name)}</div>'
                 f'<div style="font-size:19px;color:{MUTED};line-height:1.3">{e(sub)}</div></div>{cells}</div>')
S = A.set_index("arquetipo")
sil, act, neg = S.loc["desgaste silencioso"], S.loc["salida activa a competidor"], S.loc["relación desatendida"]
ml = ["EBM M2", "LightGBM", "XGBoost", "EBM M3", "Red neuronal NAM"]
msgs = [("Salida activa: todos la ven", f"{min(act[m] for m in MOD):.0f}% a {max(act[m] for m in MOD):.0f}% capturado. El dinero moviéndose es la señal más fuerte; A-lite ya basta."),
        ("Relación desatendida: el ML suma", f"ML y RN {min(neg[m] for m in ml):.0f}% a {max(neg[m] for m in ml):.0f}% vs A-lite {neg['A-lite']:.0f}%: las variables de contacto y banquero que A-lite no tiene."),
        ("Desgaste silencioso: punto ciego común", f"{sil['% de eventos B']:.0f}% de los eventos y ningún modelo pasa de {max(sil[m] for m in MOD):.0f}%. Se atiende con revisión proactiva, no con más modelo.")]
M4 = "".join(f'<div style="flex:1;display:flex;flex-direction:column;gap:6px;background:{SOFT};padding:20px 24px;border-radius:14px">'
             f'<div style="font-size:24px;font-weight:700">{e(a)}</div><div style="font-size:21px;color:{MUTED};line-height:1.3">{e(b)}</div></div>' for a, b in msgs)
body4 = f'<div style="flex:1;display:flex;flex-direction:column;gap:22px"><div style="display:flex;flex-direction:column">{hd}{"".join(rows4)}</div><div style="display:flex;gap:20px">{M4}</div></div>'
s4 = section("arquetipos", "Arquetipos: a quién detecta cada modelo", "4 · Arquetipos", body4,
             "Fuente: outputs/final/deck_archetypes.csv (exec_deck_data.py). Arquetipos del M1 (K = 3) asignados sin reajuste; acción = playbook del M1.",
             f"% de eventos de churn B de cada arquetipo que cae en el {META['capacidad'] * 100:.0f}% de hogares más riesgoso según cada modelo (misma capacidad: {META['hogares marcados por modelo']} "
             f"de {META['hogares']:,} hogares, test ∩ holdout de A-lite). Scorecard M1 y EBM M2 se entrenaron para churn B; el resto para hard 6M.")

# ── deck.json ────────────────────────────────────────────────────────────────────────────────────────────────
SL = {"base": s1, "variables": s2, "modelos": s3, "arquetipos": s4}
for k, v in SL.items():
    (OUT / "slides" / f"{k}.html").write_text(v, encoding="utf-8")
json.dump({"v": 4, "createdOnFiles": {"v": 1, "at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}, "lists": "css",
           "title": "Client Pulse · Reporte ejecutivo", "order": list(SL), "sections": {"start": "base"},
           "faces": {"inter": {"family": "Inter", "href": "https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap"}},
           "designSystems": []}, open(OUT / "deck.json", "w"), ensure_ascii=False, indent=1)
for k, v in SL.items():
    print(k, v.count("<div") + v.count("<span") + v.count("<b "), "elementos")
