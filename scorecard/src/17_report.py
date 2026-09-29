"""Paso 17 · KPIs, gobernanza y cierre del documento de modelo.

- Línea base de KPIs (holdout, [DATA-SINT]) para el monitoreo: churn por valor, valor retenible en alertados,
  precisión de alertas, PSI, calibración por tramo. Tiempo alerta → contacto: sin dato (se mide en producción).
- Disparadores de gobierno: recalibración (b fuera de 0.8–1.2 dos ciclos seguidos), redesarrollo (PSI > 0.25
  sostenido o caída relativa de Gini ≥ 15%).
- QC del entregable: REPORT.md con secciones 0–17, toda figura y tabla referenciada existe, archivos obligatorios.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

from common import FIGURES, PARAMS, QC, ROOT, SCORED, TABLES, load_raw, save_table

T = PARAMS["target_primary"]
raw = load_raw()[["household_id", T, "value_lost_6m"]]
sc = pd.read_csv(SCORED / "scored_households.csv").merge(raw, on="household_id")
h = sc[(sc.muestra == "holdout") & ~sc.churn_excluded]
y, rv = h[T].astype(int).to_numpy(), h.relationship_value.to_numpy()
met = pd.read_csv(TABLES / "13_holdout_metrics.csv").set_index("modelo")
psi = pd.read_csv(TABLES / "15_psi.csv").set_index("objeto")
l1 = pd.read_csv(TABLES / "14_layer1_model.csv").set_index("modelo")
l2 = pd.read_csv(TABLES / "14_layer2_tramo.csv")

kpi = []
for m, tcol in (("A", "tramo"), ("A-lite", "tramo_lite")):
    al = h[tcol].isin(["Crítico", "Alto"]).to_numpy()
    cr = (h[tcol] == "Crítico").to_numpy()
    kpi += [
        {"modelo": m, "KPI": "Churn rate por hogares (hard 6m)", "línea base holdout": f"{100 * y.mean():.2f}%", "frecuencia": "mensual (ventana móvil 6m)", "responsable": "Analytics"},
        {"modelo": m, "KPI": "Churn rate por valor (RV de churners ÷ RV)", "línea base holdout": f"{100 * (y * rv).sum() / rv.sum():.2f}%", "frecuencia": "mensual", "responsable": "Analytics"},
        {"modelo": m, "KPI": "Valor de churners en hogares alertados (Crítico + Alto)", "línea base holdout": f"{100 * (y * rv)[al].sum() / (y * rv).sum():.1f}% del valor perdido", "frecuencia": "mensual", "responsable": "Head of PB"},
        {"modelo": m, "KPI": "Precisión de alertas Crítico / Alto", "línea base holdout": f"{100 * y[cr].mean():.1f}% / {100 * y[(h[tcol] == 'Alto').to_numpy()].mean():.1f}%", "frecuencia": "trimestral (madura a 6m)", "responsable": "Model Risk"},
        {"modelo": m, "KPI": "Tiempo alerta → primer contacto", "línea base holdout": "sin dato (se mide en producción; meta ≤ 5 / ≤ 15 días hábiles)", "frecuencia": "semanal", "responsable": "Head of PB"},
        {"modelo": m, "KPI": "PSI del score", "línea base holdout": f"{psi.loc[f'score {m}', 'PSI']:.4f}", "frecuencia": "mensual", "responsable": "Model Risk"},
        {"modelo": m, "KPI": "Pendiente de calibración b", "línea base holdout": f"{l1.loc[m, 'b holdout (diagnóstico)']:.3f}", "frecuencia": "trimestral", "responsable": "Model Risk"},
        {"modelo": m, "KPI": "Gini", "línea base holdout": f"{met.loc[m, 'Gini']:.3f}", "frecuencia": "trimestral", "responsable": "Model Risk"},
        {"modelo": m, "KPI": "Calibración por tramo (observado vs tasa oficial)", "línea base holdout": "; ".join(
            f"{r.tramo} {r['observado holdout %']:.1f}% vs {r['tasa oficial (shrinkage m=30) %']:.1f}%" for _, r in l2[l2.modelo == m].iterrows()),
         "frecuencia": "trimestral", "responsable": "Model Risk"},
    ]
kpi = pd.DataFrame(kpi)
save_table(kpi, "17_kpi_baseline")

gini_A = met.loc["A", "Gini"]
trig = pd.DataFrame([
    {"disparador": "Recalibración", "condición": "b de calibración fuera de [0.8, 1.2] en dos ciclos trimestrales seguidos, o tasa observada de Crítico fuera de su Wilson 90% dos ciclos",
     "acción": "re-estimar Platt (a, b) con la cohorte más reciente; comité aprueba", "umbral numérico (base A)": f"b ∉ [0.8, 1.2]; hoy {l1.loc['A', 'b holdout (diagnóstico)']:.2f}"},
    {"disparador": "Redesarrollo", "condición": "PSI del score > 0.25 sostenido (2 meses) o caída relativa de Gini ≥ 15%",
     "acción": "re-binning, selección y estimación completas (pasos 3–15); validación independiente", "umbral numérico (base A)": f"PSI > 0.25; Gini < {0.85 * gini_A:.3f} (hoy {gini_A:.3f})"},
    {"disparador": "Revisión de variable", "condición": "PSI de una variable > 0.25 o cambio en su definición / fuente", "acción": "revisar bins y aporte; decidir recalibrar o redesarrollar",
     "umbral numérico (base A)": "PSI variable > 0.25"},
    {"disparador": "Revisión de overrides", "condición": "precisión de una regla < tasa oficial de su tramo dos trimestres", "acción": "bajar de tramo o retirar la regla",
     "umbral numérico (base A)": "p. ej. pensión detenida (D14.5)"},
    {"disparador": "Capacidad", "condición": "casos Crítico/Alto sin contacto dentro de SLA > 20%", "acción": "revisar capacidad (3% / 10%) con Head of PB",
     "umbral numérico (base A)": "Crítico 3%, Alto 10% (supuestos)"},
])
save_table(trig, "17_governance_triggers")

# ── QC del entregable ───────────────────────────────────────────────────────────────────
qc = QC("17")
rep = (ROOT / "REPORT.md").read_text(encoding="utf-8")
secs = [int(n) for n in re.findall(r"^## (\d+)\. ", rep, flags=re.M)]
qc.check("REPORT.md con secciones 0–17 en orden", secs == list(range(18)), "0..17", secs)
figs = re.findall(r"\]\((outputs/figures/[^)]+)\)", rep)
missing_f = [f for f in figs if not (ROOT / f).exists()]
qc.check("Toda figura referenciada existe", not missing_f, "0 faltantes", missing_f)
tabs = set(re.findall(r"`(\d\d_[a-z0-9_{},]+\.csv)`", rep))
def expand(t):
    m_ = re.search(r"\{([^}]*)\}", t)
    if not m_:
        return [t]
    return [x for o in m_.group(1).split(",") for x in expand(t[:m_.start()] + o + t[m_.end():])]


exp_tabs = [x for t in tabs for x in expand(t)]
missing_t = [t for t in exp_tabs if not (TABLES / t).exists() and not (ROOT / "outputs" / "data" / t).exists()]
qc.check("Toda tabla referenciada existe", not missing_t, "0 faltantes", missing_t, severity="warn")
for f in ["README.md", "DECISIONS.md", "requirements.txt", "run_all.sh", "outputs/scored/scored_households.csv", "outputs/tables/12_scorecard_lookup.csv"]:
    qc.check(f"Entregable: {f}", (ROOT / f).exists(), "existe", (ROOT / f).exists())
qc.check("Scripts 00–17 presentes", len(list((ROOT / "src").glob("[0-9][0-9]_*.py"))) == 18, 18, len(list((ROOT / "src").glob("[0-9][0-9]_*.py"))))
qc.check("Sección de limitaciones en REPORT", "### Limitaciones" in rep, "presente", "### Limitaciones" in rep)
print(kpi.to_string(index=False))
print("\n" + trig.to_string(index=False))
qc.gate()
