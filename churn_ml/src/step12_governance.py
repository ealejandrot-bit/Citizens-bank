"""Paso 12 · Monitoreo, gobernanza, manifiesto y `reports/model_document.md` (termina en G4).

- Comparativa final M1 · EBM · A-lite · XGBoost desde las tablas de los pasos 9, 9b y 10.
- KPIs del EBM como challenger en monitoreo (el M1 sigue como modelo operativo; D9.1/D10.1) y disparadores del SPEC.
- Manifiesto con versión y sha256 de los modelos del ML; verificación de que los modelos anteriores siguen intactos.
"""
from __future__ import annotations

import hashlib
import json
import platform
from importlib.metadata import version

import pandas as pd

from common import INH, MODEL, REPORTS, ROOT, SEED, TABLES, md_table, save_table

T = lambda n: pd.read_csv(TABLES / f"{n}.csv")  # noqa: E731
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731

G, DL, H, TT = T("step09_global"), T("step09_delta_vs_m1"), T("step09_h2"), T("step09_tramos_val")
AL, ALB, SUMM, AR = T("step09b_alite_comparison"), T("step09b_alite_bootstrap"), T("step10_summary"), T("step11_archetypes")
g = G[G.muestra == "val"].set_index("modelo")
fair = AL[AL.subconjunto.str.startswith("justo") & AL.target.str.startswith("B")].set_index("modelo")
nH = H.groupby("modelo").cumple.apply(lambda s: int((s == "sí").sum()))

FINAL = pd.DataFrame([
    ("Variables", "8", "12", "5", "12"),
    ("Forma", "puntos por bin (WoE)", "puntos por bin (EBM aditivo)", "puntos por bin (WoE)", "árboles + SHAP"),
    ("Gini · val completo (5,779)", f"{g.loc['M1', 'Gini']:.3f}", f"{g.loc['EBM', 'Gini']:.3f}", "— (70% en su desarrollo)", f"{g.loc['XGBoost', 'Gini']:.3f}"),
    ("PR-AUC · val completo", f"{g.loc['M1', 'PR-AUC']:.3f}", f"{g.loc['EBM', 'PR-AUC']:.3f}", "—", f"{g.loc['XGBoost', 'PR-AUC']:.3f}"),
    ("PR-AUC · subconjunto justo (1,737)", f"{fair.loc['M1 · scorecard (8 variables)', 'PR-AUC']:.3f}", f"{fair.loc['EBM (12 variables)', 'PR-AUC']:.3f}",
     f"{fair.loc['A-lite (5 variables)', 'PR-AUC']:.3f}", f"{fair.loc['XGBoost (retirado, referencia)', 'PR-AUC']:.3f}"),
    ("Precisión top 5% · justo", f"{fair.loc['M1 · scorecard (8 variables)', 'Precision@5% %']:.1f}%", f"{fair.loc['EBM (12 variables)', 'Precision@5% %']:.1f}%",
     f"{fair.loc['A-lite (5 variables)', 'Precision@5% %']:.1f}%", f"{fair.loc['XGBoost (retirado, referencia)', 'Precision@5% %']:.1f}%"),
    ("Criterios H-2 de reemplazo cumplidos", "— (referencia)", f"{nH['EBM']} de 8", "no evaluado (otro target)", f"{nH['XGBoost']} de 8"),
    ("Razones por cliente estables (top 1)", "91.7% (M1 paso 11)", "85.0%", "—", "81.5%"),
    ("Rol recomendado", "modelo operativo", "challenger en monitoreo", "comunicación ejecutiva", "retirado"),
], columns=["", "M1 · scorecard", "EBM (ML)", "A-lite", "XGBoost"])
save_table(FINAL, "step12_final_comparison")

KPI = pd.DataFrame([
    ("Challenger vs operativo", "ΔPR-AUC EBM − M1 en cada snapshot con resultados", f"{DL.set_index('modelo').loc['EBM', 'ΔPR-AUC vs M1']:+.3f} (val)",
     "≥ +0.03 sostenido en 2 ciclos ⟹ reabrir la decisión de reemplazo (tabla H-2)", "semestral"),
    ("Discriminación EBM", "Gini", f"{g.loc['EBM', 'Gini']:.3f}", "caída > 15% relativo ⟹ redesarrollo", "mensual"),
    ("Calibración EBM", "pendiente Platt b en el último snapshot con resultados", f"{g.loc['EBM', 'pendiente b']:.3f} (val)", "fuera de 0.8–1.2 dos ciclos ⟹ recalibración", "mensual"),
    ("Crítico EBM (G3-3)", "esperada vs observada en Crítico", f"{TT[(TT.modelo == 'EBM') & (TT.tramo == 'Crítico')]['esperada %'].iloc[0]:.1f}% vs {TT[(TT.modelo == 'EBM') & (TT.tramo == 'Crítico')]['observada %'].iloc[0]:.1f}%",
     "re-calibrar con el próximo snapshot; publicar la tasa observada", "mensual"),
    ("Estabilidad", "PSI dev→val por tramo", f"{T('step09_psi').set_index('modelo').loc['EBM', 'PSI dev→val por tramo']:.4f}", "> 0.25 sostenido ⟹ redesarrollo", "mensual"),
    ("Deriva de explicación", "participación de |f_j| por variable", "ver step07_importance_stability.csv", "cambio de puesto de las 3 primeras ⟹ revisión", "trimestral"),
    ("Prioridad (hallazgo D10.1)", "captura de RV de eventos al 10%: tramo primero vs p×RV global", "48.9% vs 58.8% (M1)", "decisión de negocio; medir con el control 12.5% del M1", "trimestral"),
], columns=["dimensión", "KPI", "línea base [DATA]", "umbral / acción [DEF]", "frecuencia"])
save_table(KPI, "step12_kpis")

LIM = pd.DataFrame([
    ("L1–L7", "Heredadas del M1: sin OOT; señales sin timestamps; compuestos sin regla; dataset sintético; UHNW pequeño; sin digital ni eventos de vida; causalidad no identificable."),
    ("L8", "El EBM sobrestima Crítico en val (61% esperado vs 53% observado); se corrige con el próximo snapshot (no se reusa val)."),
    ("L9", "A-lite se desarrolló con otro split y otro target: comparación justa solo en 1,737 hogares (IC amplios)."),
    ("L10", "El paso 10 usa val después de validar: la elección entre reglas de uso conjunto tiene un leve optimismo (regla fijada antes, D10.1)."),
    ("L11", "La probabilidad del M1 fue calibrada sobre val (paso 14 del M1): su Brier y b en val le favorecen en la comparación."),
], columns=["id", "limitación"])
save_table(LIM, "step12_limitations")

# Manifiesto y verificación de modelos anteriores
prev = json.loads((INH / "previous_models_sha256.json").read_text(encoding="utf-8"))
intact = all((ROOT.parent / f).exists() and sha(ROOT.parent / f) == h for f, h in prev.items())
man = {"versión": "ML 1.0.0", "modelo": "EBM monotónico sin interacciones (12 variables, sin compuestos)", "rol": "challenger en monitoreo; M1 1.0.0 operativo",
       "semilla": SEED, "python": platform.python_version(),
       "librerías": {k: version(k) for k in ("pandas", "numpy", "scikit-learn", "interpret-core", "xgboost", "lightgbm", "shap", "optuna")},
       "archivos": {f.name: sha(f) for f in sorted(MODEL.glob("step*"))}, "modelos anteriores intactos": intact}
(MODEL / "MANIFEST.json").write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8")

steps = [("00", "Herencia y verificación"), ("01", "Conjunto de variables"), ("02", "Selección de variables"), ("03", "Algoritmo e hiperparámetros"),
         ("04", "Explicabilidad"), ("05", "Calibración"), ("06", "Escalamiento, tramos, salida"), ("07", "Robustez"), ("08", "Equidad"),
         ("09", "Validación y tabla H-2"), ("09b", "Comparativa con A-lite"), ("10", "Uso conjunto"), ("11", "Arquetipos y acción"), ("12", "Monitoreo y gobierno")]
IDX = "\n".join(f"{i + 1}. [Paso {n} · {t}](step{n}.md)" for i, (n, t) in enumerate(steps))
ANEXO = "\n\n".join("\n".join(("#" + ln) if ln.startswith("#") else ln for ln in (REPORTS / f"step{n}.md").read_text(encoding="utf-8").splitlines())
                    for n, _ in steps if n != "12")
DLOG = (REPORTS / "decision_log.md").read_text(encoding="utf-8").split("\n", 1)[1]
REAL = pd.DataFrame([
    ("Panel temporal", "OOT real y deriva mensual del challenger vs el operativo; la decisión de reemplazo se reabre con 2 ciclos de evidencia."),
    ("Más eventos", "con más eventos (o UHNW ≥ 100) el EBM podría usar interacciones de a pares sin perder estabilidad."),
    ("Resultado de la acción", "el control 12.5% en Alto permitiría separar predicción de efecto de la gestión (L7)."),
    ("Señales nuevas", "digital y eventos de vida: el desgaste silencioso (47.6% de los eventos) no tiene hoy señales que lo distingan."),
], columns=["con datos reales / panel", "qué cambiaría"])

doc = f"""# Documento del modelo · Modelo 2 (ML) · churn propensity

Dataset sintético `client_pulse_synthetic.xlsx` (20,000 households, snapshot 2025-12-31) [DATA]. Marco MRM (SR 11-7 o
equivalente). Mismo target (B), split y holdout que el Modelo 1. Gates: [G0](gate_0.md) · [G1](gate_1.md) · [G2](gate_2.md) ·
[G3](gate_3.md) · [G4](gate_4.md). Versión ML 1.0.0 (`outputs/model/MANIFEST.json`).

## 1. Índice
{IDX}

## 2. Comparativa final [DATA]
{md_table(FINAL)}

- Recomendación: el M1 sigue como modelo operativo (el EBM mejora +0.015 de PR-AUC en val, por debajo del umbral de
  reemplazo, y no agrega en uso conjunto a igual capacidad); el EBM queda como challenger en monitoreo; A-lite como
  versión para comunicación ejecutiva (detecta menos: −0.04 de PR-AUC). La regla de prioridad (tramo primero vs p×RV)
  cambia más la captura de valor que el modelo (D10.1).

## 3. KPIs y disparadores
{md_table(KPI)}

## 4. Limitaciones
{md_table(LIM)}

## 5. Qué cambiaría con datos reales y panel temporal
{md_table(REAL)}

## 6. Preguntas para el equipo de datos
- Las del M1 (regla de `multi_signal_count`, motivo de `churn_excluded`, definición de RV y `value_lost_6m`, fecha
  as-of de cada señal) siguen abiertas; el ML no las necesita (sin compuestos), salvo la fecha as-of (L2).

## 7. Registro de decisiones final
{DLOG}

## Anexo · reportes de paso consolidados (0–11)
{ANEXO}
"""
(REPORTS / "model_document.md").write_text(doc, encoding="utf-8")

rep = f"""# Paso 12 · Monitoreo, gobierno, documento

## Objetivo
- Cerrar el Modelo 2 con su rol definido, KPIs, limitaciones, manifiesto y documento consolidado.

## Método
- Comparativa final desde las tablas de los pasos 9, 9b, 10 y 11; KPIs del EBM como challenger; manifiesto con sha256.

## Código
- `src/step12_governance.py` · `tests/test_step12.py` · `step12_*.csv`, `outputs/model/MANIFEST.json`, `reports/model_document.md`.

## Resultados

### Comparativa final [DATA]
{md_table(FINAL)}

### KPIs [DATA / DEF]
{md_table(KPI)}

### Limitaciones
{md_table(LIM)}

- Modelos anteriores intactos: {'sí' if intact else 'NO'} ({len(prev)} archivos verificados por sha256) [DATA].

## Tests
- `tests/test_step12.py` (ver pytest).

## Decisiones y preguntas abiertas
- D12.1 en `reports/decision_log.md`; preguntas G4 en `reports/gate_4.md`.
"""
(REPORTS / "step12.md").write_text(rep, encoding="utf-8")
print(FINAL.to_string(index=False)); print("intactos", intact)
