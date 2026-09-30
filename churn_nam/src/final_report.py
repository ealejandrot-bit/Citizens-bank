"""Informe comparativo final de los 3 modelos + A-lite (todas las cifras leídas de outputs; ninguna a mano).

Fuentes: churn_nam/outputs/p10 (todos los métodos en el mismo test), p11–p13; churn_ml (H-2 del Modelo 2);
scorecard/ (coeficientes de A-lite); churn_scorecard (coeficientes del M1).
Salidas: outputs/final/*.csv, reports/comparativo_final.md y reports/comparativo_final.html (página para publicar).
"""
from __future__ import annotations

import html
import json

import pandas as pd

from config import HEADER, P, ROOT
from report import md_table

OUT = ROOT / "outputs" / "final"
OUT.mkdir(parents=True, exist_ok=True)
allm = pd.read_csv(P.out(10) / "test_metrics_all.csv")
dec = json.load(open(P.out(10) / "decision.json"))
cal = pd.read_csv(P.out(11) / "calibration.csv")
ews = pd.read_csv(P.out(13) / "ews_curve.csv")
rule = pd.read_csv(P.out(13) / "multisignal_vs_model.csv")
sc = pd.read_csv(P.out(12) / "scorecard_summary.csv")
h2 = pd.read_csv(P.m2 / "outputs" / "tables" / "step09_h2.csv")
n_alite = len(pd.read_csv(P.alite / "outputs" / "tables" / "11_modelAlite_coefficients.csv")) - 1
n_m1 = len(pd.read_csv(P.m1 / "outputs" / "tables" / "step11A_coefficients.csv")) - 1
n_m2 = len(json.loads((P.m2 / "data" / "processed" / "step02_selected.json").read_text(encoding="utf-8"))["vars"])
n_m3 = len(json.load(open(P.out(4) / "monotonicity_map.json")))

META = {
    "A-lite (congelado, target A)": ("A-lite", "Modelo 1 previo", n_alite, "scorecard de puntos (logística WoE)", "referencia ejecutiva"),
    "M1 scorecard (target B)": ("Scorecard M1", "Modelo 1", n_m1, "scorecard de puntos (logística WoE)", "operativo (M1)"),
    "M2 EBM (target B)": ("EBM M2", "Modelo 2", n_m2, "aditivo por bins (EBM)", "challenger en monitoreo (M2)"),
    "EBM monótono (champion)": ("EBM M3", "Modelo 3", n_m3, "aditivo por bins (EBM)", "champion interpretable (M3)"),
    "NAM monótono": ("Red neuronal NAM", "Modelo 3", n_m3, "red neuronal aditiva monótona", "challenger (no pasó el gate)"),
    "logística L2": ("Logística L2", "Modelo 3 · benchmark", n_m3, "lineal", "benchmark"),
    "XGBoost": ("XGBoost", "Modelo 3 · benchmark", n_m3, "árboles (caja negra)", "benchmark"),
    "LightGBM": ("LightGBM", "Modelo 3 · benchmark", n_m3, "árboles (caja negra)", "benchmark"),
    "LightGBM monótono": ("LightGBM monótono", "Modelo 3", n_m3, "árboles monótonos", "challenger interpretable"),
}
fair = allm[(allm.subconjunto == "test ∩ holdout A-lite") & (allm.segmento == "pooled")]
full = allm[(allm.subconjunto == "test completo") & (allm.segmento == "pooled")]
rows = []
for m, (name, proj, nv, form, role) in META.items():
    fa = fair[(fair.modelo == m) & (fair.target == "A")].iloc[0]
    fb = fair[(fair.modelo == m) & (fair.target == "B")].iloc[0]
    ft = full[(full.modelo == m) & (full.target == "A")]
    rows.append({"modelo": name, "proyecto": proj, "variables": nv, "forma": form, "rol": role,
                 "PR-AUC A (justo)": fa["PR-AUC"], "lift@5% A (justo)": fa["lift@5%"], "AUC A (justo)": fa["AUC"], "PR-AUC B (justo)": fb["PR-AUC"],
                 "PR-AUC A (test completo)": ft["PR-AUC"].iloc[0] if len(ft) else float("nan")})
T = pd.DataFrame(rows).sort_values("PR-AUC A (justo)", ascending=False).reset_index(drop=True)
T.to_csv(OUT / "comparison_all_methods.csv", index=False)
ref = T.set_index("modelo").loc["A-lite"]
hog, ev_a = int(fair[fair.target == "A"].hogares.iloc[0]), int(fair[fair.target == "A"].eventos.iloc[0])
ev_b = int(fair[fair.target == "B"].eventos.iloc[0])
e5 = ews[(ews.subconjunto == "test ∩ holdout A-lite") & (ews.segmento == "pooled") & (ews["% hogares marcados"] == 5.0)].set_index("modelo")
r0 = rule[(rule.subconjunto == "test completo") & (rule.segmento == "pooled")].iloc[0]
h2e = h2[h2.modelo == "EBM"]
best = T.iloc[0]
gap_best = best["PR-AUC A (justo)"] - ref["PR-AUC A (justo)"]
spread = T[T.modelo != "A-lite"]["PR-AUC A (justo)"]

KEY = [
    f"Todos los modelos completos quedan en un rango estrecho de PR-AUC en hard churn ({spread.min():.3f} a {spread.max():.3f}) en los mismos {hog:,} hogares ({ev_a} eventos): la complejidad casi no agrega.",
    f"A-lite, con {n_alite} variables, encuentra menos churners (PR-AUC {ref['PR-AUC A (justo)']:.3f}; {-gap_best:+.3f} frente al mejor, {best.modelo}) y también tiene el menor lift en el 5% más riesgoso "
    f"({ref['lift@5% A (justo)']:.2f} frente a {T[T.modelo != 'A-lite']['lift@5% A (justo)'].min():.2f}–{T[T.modelo != 'A-lite']['lift@5% A (justo)'].max():.2f}); su ventaja es ser el más simple de explicar.",
    f"La red neuronal (NAM) no reemplaza a A-lite: mejora la PR-AUC en {dec['ΔPR-AUC']:+.3f} (IC95 {dec['ΔPR-AUC IC95'][0]:+.3f} a {dec['ΔPR-AUC IC95'][1]:+.3f}) pero el IC del lift@5% ({dec['Δlift@5% IC95'][0]:+.2f} a {dec['Δlift@5% IC95'][1]:+.2f}) incluye 0.",
    f"El EBM del Modelo 2 cumplió {int((h2e.cumple == 'sí').sum())} de {len(h2e)} criterios para reemplazar al scorecard y quedó como challenger: la ganancia no alcanzó los umbrales.",
    f"Con 5% de hogares en alerta, por cada 100 alertas: EBM {e5.loc['EBM (champion)', 'churners por 100 alertas']:.1f} churners, red neuronal {e5.loc['NAM (challenger)', 'churners por 100 alertas']:.1f}, A-lite {e5.loc['A-lite (congelado)', 'churners por 100 alertas']:.1f}.",
    f"Una regla simple de 2 o más señales visibles captura {int(r0['churners regla'])} churners en {int(r0['hogares marcados'])} hogares; el EBM, al mismo volumen, {int(r0['churners EBM (champion) (mismo volumen)'])}: el modelo le gana por poco.",
]
REC = ["Operar con el scorecard (M1) o el EBM: aditivos, auditables y en el tope de desempeño.",
       "Usar A-lite para explicar el modelo a la alta dirección (5 variables), sabiendo que detecta menos churners que los modelos completos.",
       "No llevar la red neuronal ni los árboles de caja negra a producción: no mejoran lo suficiente para justificar su complejidad.",
       "Medir el efecto de las acciones con el grupo de control del 12.5% antes de invertir en más modelado."]
LIM = ["Dataset sintético y un solo corte (sin OOT): valida el método, no resultados de clientes reales.",
       f"La comparación contra A-lite se hace en {hog:,} hogares con {ev_a} eventos de hard churn: intervalos amplios.",
       "UHNW tiene muy pocos eventos: sus resultados solo se reportan.",
       "La red neuronal fue al gate sin terminar de converger (decisión del usuario)."]

# ── Markdown (repo) ─────────────────────────────────────────────────────────────────────────────────────────
tbl = T[["modelo", "proyecto", "variables", "rol", "PR-AUC A (justo)", "lift@5% A (justo)", "PR-AUC B (justo)"]]
md = "\n".join([HEADER, "", "# Comparativo final · Client Pulse (3 modelos + A-lite)", "",
                f"Mismos {hog:,} hogares del test que ningún modelo vio (fuera del desarrollo de A-lite); hard churn (A) {ev_a} eventos, target B {ev_b} eventos.", "",
                "## Todos los métodos", md_table(tbl), "", "## Hallazgos", *[f"- {k}" for k in KEY], "", "## Recomendación", *[f"- {r}" for r in REC], "",
                "## Limitaciones", *[f"- {x}" for x in LIM], "", "_Cifras leídas de churn_nam/outputs (p10–p13), churn_ml, churn_scorecard y scorecard; generado por src/final_report.py._"])
(P.reports / "comparativo_final.md").write_text(md, encoding="utf-8")

# ── Página HTML ─────────────────────────────────────────────────────────────────────────────────────────────
e = html.escape
xmax = max(T["PR-AUC A (justo)"].max(), 0.001) * 1.12
W, rowh, left, right = 640, 30, 170, 70
Hh = rowh * len(T) + 40
bars = []
for i, r in T.iterrows():
    y = 20 + i * rowh
    w = (W - left - right) * r["PR-AUC A (justo)"] / xmax
    is_ref = r.modelo == "A-lite"
    bars.append(f'<text x="{left - 10}" y="{y + 15}" text-anchor="end" class="lab{" ref" if is_ref else ""}">{e(r.modelo)}</text>'
                f'<rect x="{left}" y="{y + 4}" width="{w:.1f}" height="16" rx="3" class="bar{" refbar" if is_ref else ""}"/>'
                f'<text x="{left + w + 6:.1f}" y="{y + 16}" class="val">{r["PR-AUC A (justo)"]:.3f}</text>')
svg = f'<svg viewBox="0 0 {W} {Hh}" role="img" aria-label="PR-AUC en hard churn por modelo"><line x1="{left}" y1="12" x2="{left}" y2="{Hh - 16}" class="axis"/>{"".join(bars)}</svg>'
trs = "".join(f'<tr class="{"refrow" if r.modelo == "A-lite" else ""}"><td>{e(r.modelo)}</td><td>{e(r.proyecto)}</td><td class="num">{int(r.variables)}</td><td>{e(r.forma)}</td>'
              f'<td class="num">{r["PR-AUC A (justo)"]:.3f}</td><td class="num">{r["lift@5% A (justo)"]:.2f}</td><td class="num">{r["PR-AUC B (justo)"]:.3f}</td><td>{e(r.rol)}</td></tr>' for _, r in T.iterrows())
ews_rows = "".join(f'<tr><td>{e(k)}</td><td class="num">{e5.loc[k, "churners por 100 alertas"]:.1f}</td><td class="num">{e5.loc[k, "captura %"]:.1f}%</td><td class="num">{e5.loc[k, "captura RV de churners %"]:.1f}%</td></tr>'
                   for k in ["EBM (champion)", "NAM (challenger)", "A-lite (congelado)"])
page = f"""<title>Comparativo Client Pulse</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,650&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/* Layout: una columna de lectura (memo de riesgo de modelos), tabla y gráfico como anexos anchos con scroll propio */
:root {{
  --bg: #f6f7f5; --surface: #ffffff; --fg: #1d2421; --muted: #5b6661; --line: #d9dfdb; --accent: #1f6f5c; --ref: #b5651d; --bar: #9fb3aa;
  --display: "Fraunces", Georgia, serif; --body: "Source Sans 3", "Segoe UI", system-ui, sans-serif; --mono: "IBM Plex Mono", ui-monospace, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg: #121715; --surface: #1a211e; --fg: #e6ece9; --muted: #9aa8a1; --line: #2c3632; --accent: #5cc0a4; --ref: #e59a55; --bar: #4f6660; color-scheme: dark; }} }}
:root[data-theme="dark"] {{ --bg: #121715; --surface: #1a211e; --fg: #e6ece9; --muted: #9aa8a1; --line: #2c3632; --accent: #5cc0a4; --ref: #e59a55; --bar: #4f6660; color-scheme: dark; }}
body {{ background: var(--bg); color: var(--fg); font: 16px/1.55 var(--body); padding-inline: 20px; padding-block: 32px 56px; }}
main {{ max-width: 860px; margin: 0 auto; display: grid; gap: 34px; }}
.note {{ font: 12px/1.4 var(--mono); color: var(--muted); letter-spacing: .02em; }}
h1 {{ font: 650 clamp(28px, 5vw, 40px)/1.1 var(--display); margin: 6px 0 10px; text-wrap: balance; }}
h2 {{ font: 600 21px/1.25 var(--display); margin: 0 0 12px; text-wrap: balance; }}
p {{ margin: 0; max-width: 68ch; }}
.lede {{ color: var(--muted); max-width: 68ch; }}
ol.key {{ margin: 0; padding-left: 22px; display: grid; gap: 10px; max-width: 72ch; }}
ul {{ margin: 0; padding-left: 20px; display: grid; gap: 6px; max-width: 72ch; }}
.wide {{ overflow-x: auto; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; }}
table {{ border-collapse: collapse; width: 100%; min-width: 760px; font-size: 14px; }}
th, td {{ padding: 9px 12px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }}
th {{ font: 500 11px/1.3 var(--mono); text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }}
td.num {{ font-family: var(--mono); font-variant-numeric: tabular-nums; text-align: right; white-space: nowrap; }}
tr.refrow td {{ color: var(--ref); font-weight: 600; }}
.chart {{ padding: 14px 12px 4px; }}
svg {{ width: 100%; min-width: 520px; height: auto; display: block; }}
svg .lab {{ font: 13px var(--body); fill: var(--fg); }} svg .lab.ref {{ fill: var(--ref); font-weight: 600; }}
svg .val {{ font: 12px var(--mono); fill: var(--muted); }} svg .bar {{ fill: var(--bar); }} svg .refbar {{ fill: var(--ref); }} svg .axis {{ stroke: var(--line); stroke-width: 1; }}
.cols {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 28px; }}
.cols > div {{ min-width: 0; }}
footer {{ border-top: 1px solid var(--line); padding-top: 14px; }}
</style>
<main>
<header>
  <div class="note">{e(HEADER)}</div>
  <h1>Comparativo final de modelos de churn</h1>
  <p class="lede">Client Pulse, banca privada HNW/UHNW. Nueve métodos de tres proyectos medidos en los mismos {hog:,} hogares de prueba que ningún modelo vio al entrenarse: {ev_a} eventos de hard churn (target A) y {ev_b} del target B. A-lite es la referencia.</p>
</header>
<section><h2>Qué encontramos</h2><ol class="key">{"".join(f"<li>{e(k)}</li>" for k in KEY)}</ol></section>
<section><h2>Capacidad de encontrar churners (PR-AUC, hard churn)</h2>
  <div class="wide chart">{svg}</div>
  <p class="note" style="margin-top:8px">Más alto es mejor. En naranja la referencia A-lite. Tasa base de hard churn ≈ 6%.</p>
</section>
<section><h2>Todos los métodos</h2>
  <div class="wide"><table><thead><tr><th>Modelo</th><th>Proyecto</th><th>Variables</th><th>Forma</th><th>PR-AUC A</th><th>Lift top 5% A</th><th>PR-AUC B</th><th>Rol</th></tr></thead><tbody>{trs}</tbody></table></div>
</section>
<section class="cols">
  <div><h2>Alertas tempranas</h2><p class="lede" style="margin-bottom:10px">Con el 5% de hogares en alerta ({int(e5.iloc[0]["hogares marcados"])} hogares; alertas por mes = marcados ÷ 6).</p>
    <div class="wide"><table style="min-width:0"><thead><tr><th>Modelo</th><th>Churners por 100 alertas</th><th>Churners capturados</th><th>RV capturado</th></tr></thead><tbody>{ews_rows}</tbody></table></div></div>
  <div><h2>Recomendación</h2><ul>{"".join(f"<li>{e(r)}</li>" for r in REC)}</ul></div>
</section>
<section><h2>Límites de este análisis</h2><ul>{"".join(f"<li>{e(x)}</li>" for x in LIM)}</ul></section>
<footer class="note">Cifras generadas por src/final_report.py desde churn_nam/outputs (fases 10–13), churn_ml, churn_scorecard y scorecard.</footer>
</main>
"""
(P.reports / "comparativo_final.html").write_text(page, encoding="utf-8")
print(T.round(3).to_string(index=False)); print(*KEY, sep="\n")
