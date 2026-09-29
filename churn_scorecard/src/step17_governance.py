"""Paso 17 · KPIs, monitoreo, gobernanza, limitaciones y `reports/model_document.md`.

- Línea base de KPIs = valores de validación (pasos 13–15) [DATA]; umbrales = los del SPEC [DEF] o de las decisiones G3 [DEF].
- Disparadores (SPEC): recalibración si b fuera de 0.8–1.2 dos ciclos; redesarrollo si PSI > 0.25 sostenido o Gini −15%.
- El documento del modelo se arma desde las tablas generadas y enlaza todos los reportes de paso.
"""
from __future__ import annotations

import hashlib
import json
import pickle
import platform
from importlib.metadata import version

import pandas as pd

from common import MODEL, REPORTS, S0, O0, PDO, SEED, TABLES, md_table, save_table

T = lambda n: pd.read_csv(TABLES / f"{n}.csv")  # noqa: E731
G, AP, TT, PK, CM = T("step13_global").set_index("muestra"), T("step13_approval"), T("step13_tramos_dev_val"), T("step13_precision_at_k"), T("step13_confusion_critico")
PL, AL, TC, RV, SEG = T("step14_platt").iloc[0], T("step14_alignment").set_index("muestra"), T("step14_tramo_calibration"), T("step14_rv_calibration"), T("step14_segment_calibration")
PSI, DES, ARQ, COEF, MS = T("step15_psi"), T("step14_control_design"), T("step16_archetype_profile"), T("step11A_coefficients"), T("step12_master_scale")
K12 = pickle.load(open(MODEL / "step12_scaling.pkl", "rb"))
fin = TT[TT.tramos == "final (con overrides)"].set_index("tramo")
q5 = RV.set_index("banda RV").loc["Q5 (mayor)"]
ua = SEG[(SEG.segmento == "UHNW") & (SEG.tramo == "Alto")].iloc[0]

KPI = pd.DataFrame([
    ("Discriminación", "Gini (val)", f"{G.loc['val', 'Gini']:.3f}", "caída > 15% relativo vs línea base ⟹ redesarrollo", "mensual"),
    ("Discriminación", "PR-AUC (val)", f"{G.loc['val', 'PR-AUC']:.3f}", "seguimiento", "mensual"),
    ("Calibración", "pendiente Platt b", f"{PL.b:.3f}", "fuera de 0.8–1.2 dos ciclos ⟹ recalibración", "mensual"),
    ("Calibración", "media p calibrada vs tasa observada", f"{AL.loc['val', 'media p calibrada %']:.2f}% vs {AL.loc['val', 'tasa observada %']:.2f}%", "brecha > 1 pp dos ciclos ⟹ recalibración", "mensual"),
    ("Estabilidad", "PSI del score", f"{PSI.set_index('objeto').loc['score (deciles de dev)', 'PSI']:.4f}", "0.10–0.25 vigilar; > 0.25 sostenido ⟹ redesarrollo", "mensual"),
    ("Estabilidad", "PSI de variables (máx.)", f"{PSI[PSI.objeto.str.startswith('variable')].PSI.max():.4f}", "> 0.25 en una variable ⟹ revisar su fuente", "mensual"),
    ("Tramos", "tasa Crítico / Alto / Vigilancia / Estable (val)", " / ".join(f"{fin.loc[t, 'tasa val %']:.1f}%" for t in ["Crítico", "Alto", "Vigilancia", "Estable"]),
     "pérdida de monotonía o lift Crítico/Estable < 5x ⟹ revisar cortes", "trimestral"),
    ("Operación", "precisión en Crítico (val)", f"{CM['precisión %'].iloc[0]:.1f}%", "seguimiento; FP por evento capturado " + f"{CM['falsos positivos por evento capturado'].iloc[0]:.2f}", "mensual"),
    ("Operación", "captura top 10% (val)", f"{PK.set_index('K %').loc[10, 'captura %']:.1f}% eventos · {PK.set_index('K %').loc[10, 'captura RV eventos %']:.1f}% RV", "seguimiento", "mensual"),
    ("Valor (G3-2)", "Σ p·RV / Σ RV de eventos, quintil superior de RV", f"{q5['Σ p·RV / Σ RV eventos']:.2f}", "< 0.85 dos ciclos ⟹ probar ajuste por log_rv", "trimestral"),
    ("Segmento (G3-3)", "UHNW en Alto: observada vs esperada", f"{ua['observada %']:.1f}% vs {ua['esperada %']:.1f}% ({int(ua.eventos)} eventos)", "revisión prioritaria del banquero; recalibrar UHNW si ≥ 100 eventos acumulados", "trimestral"),
    ("Efecto de la acción (G3-4)", "churn tratados vs control en Alto", f"control 12.5% = {int(DES.set_index('% control').loc[12.5, 'hogares control'])} hogares", f"efecto mínimo detectable {DES.set_index('% control').loc[12.5, 'efecto mínimo detectable (pp, α 5%, potencia 80%)']:.1f} pp", "a 6 meses"),
], columns=["dimensión", "KPI", "línea base [DATA]", "umbral / acción [DEF]", "frecuencia"])
save_table(KPI, "step17_kpis")

TRIG = pd.DataFrame([
    ("Recalibración", "b fuera de 0.8–1.2 en dos ciclos, o media p vs tasa > 1 pp en dos ciclos", "re-estimar Platt con el último snapshot con outcome; cortes de score sin cambio"),
    ("Redesarrollo", "PSI del score > 0.25 sostenido, o Gini −15% relativo vs línea base", "repetir pasos 5–14 con nuevos datos (y OOT si ya hay 2+ snapshots)"),
    ("Revisión de variable", "PSI > 0.25 en una variable o cambio de definición del proveedor", "revisar la fuente; bin neutral temporal si la variable se cae"),
    ("Revisión de overrides", "precisión de una regla < 12% en dos ciclos", "eliminar la regla"),
    ("Cola de valor", "quintil superior de RV con Σ p·RV / Σ RV de eventos < 0.85 dos ciclos", "probar interacción con log_rv (paso 14)"),
], columns=["disparador", "condición [DEF SPEC / G3]", "acción"])
save_table(TRIG, "step17_triggers")

GOV = pd.DataFrame([
    ("Dueño del modelo", "Wealth / banca privada (negocio)", "aprueba cortes, overrides y playbook"),
    ("Desarrollo", "equipo de modelos", "código, tablas, reportes, recalibración"),
    ("Validación independiente", "MRM (SR 11-7 o equivalente)", "revisa este documento antes del uso; revalidación anual"),
    ("Monitoreo", "equipo de modelos + MRM", "tablero mensual de KPIs y disparadores"),
    ("Cumplimiento", "legal / fair lending", "confirma exclusión de edad y buró (G1-3) y uso de datos"),
    ("Cambios", "comité de modelos", "cambios de variables o cortes = cambio material; recalibración Platt = cambio no material documentado"),
], columns=["rol", "responsable (propuesto)", "responsabilidad"])
save_table(GOV, "step17_governance")

LIM = pd.DataFrame([
    ("L1", "Sin OOT ni cohortes ni PSI temporal: un solo snapshot 2025-12-31. La validación es una partición aleatoria del mismo periodo."),
    ("L2", "Señales pre-ingenierizadas por el proveedor sin timestamps auditables; se asume que todas son as-of T0."),
    ("L3", "`multi_signal_count` / `_flag` sin regla documentada: fuera del campeón; solo en el challenger de referencia."),
    ("L4", "Dataset sintético: no representa una cartera real; nada de lo estimado se presenta como resultado de un banco."),
    ("L5", f"UHNW sub-representado: {int(G.loc['val · UHNW', 'eventos'])} eventos B en val; solo métricas globales y lectura descriptiva por tramo."),
    ("L6", "Sin dimensión digital ni eventos de vida (fallecimiento, liquidity event): no hay overrides por esas causas."),
    ("L7", "Causalidad y efecto de la propia intervención no identificables: arquetipos descriptivos; efecto solo medible con el control aleatorio."),
    ("L8", "Pesos de clase balanceados con intercepto corregido; la probabilidad publicada depende de la calibración Platt sobre val."),
], columns=["id", "limitación"])
save_table(LIM, "step17_limitations")

# Manifiesto de modelos serializados con versión (SPEC J)
MODEL_VERSION = "1.0.0"
man = {"versión del modelo": MODEL_VERSION, "fecha de snapshot": "2025-12-31", "semilla": SEED, "python": platform.python_version(),
       "librerías": {k: version(k) for k in ("pandas", "numpy", "scikit-learn", "statsmodels", "optbinning", "xgboost", "interpret-core", "shap", "optuna")},
       "archivos": {f.name: {"sha256": hashlib.sha256(f.read_bytes()).hexdigest(), "rol": ("campeón" if f.name.startswith(("step09", "step11A", "step12", "step14")) else
                                                                                         "challenger (referencia)" if f.name.startswith("step11B") else "auxiliar")}
                    for f in sorted(MODEL.glob("step*")) }}
(MODEL / "MANIFEST.json").write_text(json.dumps(man, indent=2, ensure_ascii=False), encoding="utf-8")
MAN = pd.DataFrame([{"archivo": k, "rol": v["rol"], "sha256 (12)": v["sha256"][:12]} for k, v in man["archivos"].items()])

FICHA = T("step00_ficha")
DL = (REPORTS / "decision_log.md").read_text(encoding="utf-8").split("\n", 1)[1]   # sin el título
REAL = pd.DataFrame([
    ("Panel temporal (≥ 2 snapshots)", "OOT real, cohortes, PSI temporal, placebo temporal y la regla de migración del EWS pasan a ser evaluables (hoy L1)."),
    ("Series de señales", "velocidad y aceleración de salidas y depósitos calculadas por el banco en vez de señales pre-ingenierizadas (L2)."),
    ("Regla de `multi_signal_count`", "si el proveedor la entrega, se prueba su aporte incremental en el campeón (L3, I-3)."),
    ("Datos reales", "todas las cifras se re-estiman; los cortes, la calibración y los arquetipos se rehacen (L4)."),
    ("Más UHNW", "con ≥ 100 eventos UHNW acumulados se evalúa calibración o scorecard propio (L5, G3-3)."),
    ("Dimensión digital y eventos de vida", "nuevas señales y overrides (fallecimiento, liquidity event) (L6)."),
    ("Control aleatorio", "estimación del efecto de la acción y separación entre predicción e intervención (L7, G3-4)."),
], columns=["con datos reales / panel", "qué cambiaría"])
QDATA = pd.DataFrame([
    ("I-3", "Regla de construcción de `multi_signal_count` / `multi_signal_flag`."),
    ("I-4", "Motivo de `churn_excluded` (123 hogares)."),
    ("I-5", "Definición de `relationship_value` (en el archivo = AUM + depósitos al centavo, G0-a) y denominador de `share_of_wallet`."),
    ("D-3.1", "134 valores de `pension_deposit_stopped_flag` sin `has_pension_stream`: ¿error de carga o flujo no registrado?"),
    ("D-12.5", "Hogares con antigüedad < 1 sin dato en `banker_change_6m_flag`, `return_vs_benchmark` y otras: ¿ventana de observación?"),
    ("D-1.1", "Definición exacta de `value_lost_6m` (qué pérdida mide y en qué ventana) para la calibración por valor."),
    ("L2", "Fecha de corte (as-of) de cada señal del proveedor, para confirmar que no hay información posterior a T0."),
], columns=["ref.", "pregunta para el equipo de datos"])
PARAMS = pd.DataFrame([("Modo", "DATA: toda cifra sale del archivo [DATA]; parámetros [DEF] / [DEF-default]"),
                       ("Escala", f"S₀ = {S0} @ {O0:.0f}:1, PDO = {PDO}"), ("Semilla", str(SEED)), ("Target", "B (θ = 0.25), A como sensibilidad"),
                       ("Split", "70/30 estratificado por clase × segmento; CV 5×5 en dev"), ("Versión del modelo", MODEL_VERSION)],
                      columns=["parámetro / supuesto", "valor"])

def _demote(t):
    return "\n".join(("#" + ln) if ln.startswith("#") else ln for ln in t.splitlines())


steps = [("00", "Verificación y definición del problema"), ("01", "Target y churn rate"), ("02", "Diccionario de datos"), ("03", "Calidad de datos"),
         ("04", "Muestra"), ("05", "Ingeniería de señales"), ("06", "Análisis univariado"), ("07", "Pre-segmentación"), ("08", "Correlación y estructura"),
         ("09", "Binning, WoE, IV"), ("10", "Selección"), ("11", "Estimación (campeón y challenger)"), ("12", "Escalamiento, tramos, salida"),
         ("13", "Validación"), ("14", "Calibración"), ("15", "Estabilidad"), ("16", "Acción, arquetipos, EWS"), ("17", "KPIs, monitoreo, gobernanza")]
ANEXO = "\n\n".join(_demote((REPORTS / f"step{n}.md").read_text(encoding="utf-8")) for n, _ in steps if n != "17")
IDX = "\n".join(f"{i + 1}. [Paso {n} · {t}](step{n}.md)" for i, (n, t) in enumerate(steps))
coef = COEF[["variable", "β final", "p-valor", "VIF (WoE)"]]
doc = f"""# Documento del modelo · Churn Propensity Scorecard (campeón WoE + logística)

Dataset sintético `client_pulse_synthetic.xlsx` (20,000 households, snapshot 2025-12-31) [DATA]. Marco: Model Risk
Management (SR 11-7 o equivalente). Gates: [G0](gate_0.md) · [G1](gate_1.md) · [G2](gate_2.md) · [G3](gate_3.md) · [G4](gate_4.md).

## Modo, parámetros y supuestos
{md_table(PARAMS)}

## Ficha del dataset (verificada en el paso 0) [DATA]
{md_table(FICHA)}

## 1. Índice de pasos
{IDX}

## 2. Definición
- Target B: hard churn 6M ∪ soft churn con pérdida ≥ 25% del RV; soft con pérdida menor = indeterminado [DEF-default I-1].
  Tasa B 13.88% (19,261 hogares) [DATA]. Sensibilidad: target A (hard 6M).
- Población: elegibles con antigüedad ≥ 1 año [DEF-default I-8]; 70/30 estratificado; CV 5×5 en desarrollo.

## 3. Modelo
- Logística sobre WoE, 8 variables, pesos balanceados e intercepto corregido; bins de negocio para señales raras [DEF G2-1];
  selección uno por cluster de variables [DEF G2-3]; un solo modelo con `segment_uhnw` [DEF G2-2].

{md_table(coef, floatfmt=",.4f")}

- Escala PDO: S₀ = 600 @ 20:1, PDO = 40 (Factor 57.71, Offset 427.12) [DEF-default I-6]; base {K12['base']} puntos [DATA].
  Lookup: `outputs/tables/step12_lookup.csv`; score por hogar: `outputs/scores/household_scores.csv`.
- Challenger (XGBoost monotónico, EBM, RF): referencia; no cumple la tabla H-2 y queda fuera por decisión G2-4 [DEF].

## 4. Tramos y escala maestra (dev) [DATA]
{md_table(MS[['tramo', 'score mín', 'score máx', '% hogares', '% RV', 'tasa observada %', 'captura eventos %', 'lift']], floatfmt=",.2f")}

- Overrides → Alto: cambio de banquero, queja escalada, transferencia a competidor ≥ 10% [DEF G3-1].

## 5. Validación (holdout, una vez) [DATA]
{md_table(G.reset_index()[['muestra', 'hogares', 'eventos', 'AUC', 'Gini', 'PR-AUC', 'KS']], floatfmt=",.4f")}

{md_table(AP)}

## 6. Calibración (val) [DATA]
- Platt a = {PL.a:.3f}, b = {PL.b:.3f}; isotónica no mejora. Tramos dentro de Wilson 90%:

{md_table(TC[['tramo', 'hogares', 'eventos', 'esperada %', 'observada %', 'Wilson 90% inf', 'Wilson 90% sup']], floatfmt=",.2f")}

## 7. Estabilidad [DATA]
{md_table(PSI, floatfmt=",.4f")}

## 8. Arquetipos y acción [DATA]
{md_table(ARQ[['nombre', '% eventos dev', '% eventos val', '% Crítico', '% Alto', '% Vigilancia', '% Estable']], floatfmt=",.1f")}

- Playbook y EWS: [paso 16](step16.md). Control aleatorio 12.5% en Alto [DEF G3-4].

## 9. KPIs y monitoreo
{md_table(KPI)}

{md_table(TRIG)}

## 10. Gobernanza
{md_table(GOV)}

## 11. Limitaciones
{md_table(LIM)}

## 12. Qué cambiaría con datos reales del banco y con panel temporal
{md_table(REAL)}

## 13. Preguntas para el equipo de datos
{md_table(QDATA)}

## 14. Artefactos y versión
- `outputs/tables/step12_lookup.csv`, `outputs/tables/step12_master_scale_households.csv`, `outputs/tables/step12_master_scale_rv.csv`,
  `outputs/scores/household_scores.csv`, `outputs/model/` con `MANIFEST.json` (versión {MODEL_VERSION}, sha256, librerías).

{md_table(MAN)}

## 15. Reproducibilidad
- Python ≥ 3.11, `SEED = 42`, `requirements.lock`; `python src/stepNN_*.py` en orden (paso 11: `step11_champion`,
  `step11_challenger`, `step11_calibration_view`, `step11_compare`); `python -m pytest -q` en verde.

## 16. Registro de decisiones final
{DL}

## Anexo · reportes de paso consolidados (0–17)
{ANEXO}
"""
(REPORTS / "model_document.md").write_text(doc, encoding="utf-8")

rep = f"""# Paso 17 · KPIs, monitoreo, gobernanza, limitaciones

## Objetivo
- Dejar el modelo operable y auditable: qué se mide, cuándo se actúa, quién decide y qué no puede afirmar.

## Método
- Línea base de KPIs = resultados de validación (pasos 13–15); umbrales del SPEC y de las decisiones G3 [DEF].
- `reports/model_document.md` armado desde las tablas generadas, con índice de todos los pasos.

## Código
- `src/step17_governance.py` · `tests/test_step17.py` · `step17_*.csv`, `reports/model_document.md`.

## Resultados

### KPIs
{md_table(KPI)}

### Disparadores
{md_table(TRIG)}

### Gobernanza
{md_table(GOV)}

### Limitaciones
{md_table(LIM)}

## Tests
- `tests/test_step17.py` (ver pytest).

## Decisiones y preguntas abiertas
- D17.1 en `reports/decision_log.md`; preguntas G4 en `reports/gate_4.md`.
"""
(REPORTS / "step17.md").write_text(rep, encoding="utf-8")
print(KPI.to_string(index=False))
