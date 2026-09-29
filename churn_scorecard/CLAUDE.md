# Churn Propensity Scorecard — `client_pulse_synthetic.xlsx`

## Qué es este repo

Scorecard de propensión a churn para households de banca privada: campeón interpretable (binning → WoE → logística) y
challenger ML (EBM, XGBoost/LightGBM monotónico con TreeSHAP), sobre `data/raw/client_pulse_synthetic.xlsx` (20,000
households, un solo snapshot 2025-12-31, dataset sintético). El método completo está en `docs/SPEC.md`; se ejecuta un
paso a la vez con `/step NN`. Tú diseñas, ejecutas y documentas como Senior Quantitative Risk Architect bajo Model Risk
Management (SR 11-7 o equivalente).

## Comandos del proyecto

- `/step NN` — ejecuta el paso NN (00–17) según `docs/SPEC.md`: script, tablas, tests, reporte, decision_log.
- `/gate N` — cierra un bloque: escribe `reports/gate_N.md` y se detiene a esperar respuesta del usuario.
- `/status` — dónde vamos, qué está en verde, qué preguntas siguen abiertas.
- `python -m pytest -q` — debe estar en verde antes de cada gate.

## Inicio de cada sesión

1. Lee `reports/decision_log.md` si existe (parámetros vigentes, decisiones, preguntas abiertas). Es la memoria del
   proyecto; nada se decide fuera de él.
2. No repitas pasos completados. No adelantes pasos posteriores a un gate no aprobado.

## Reglas duras (detalle en `.claude/rules/`)

- Modo DATA: toda cifra sale del archivo y lleva `[DATA]`; parámetros del usuario `[DEF]`; defaults aplicados
  `[DEF-default]`. Cifra sin etiqueta = error. Nada inventado, nada "a ojo", ningún benchmark de industria ni cifra de
  bancos reales.
- Columnas de resultado (`hard_churn_6m`, `soft_churn_3m`, `value_lost_6m`, `churn_excluded`) nunca son predictores.
- Missing estructural ("no aplica") es categoría propia; prohibido imputar por media/mediana.
- PCA solo diagnóstico. Clustering nunca causal. Sin Basilea ni IFRS 9.
- Score único = puntos escala PDO (S₀ = 600 @ 20:1, PDO = 40 ⟹ Factor 57.71, Offset 427.12). Churn rate, score y
  probabilidad son tres cosas distintas.
- No hay dimensión temporal en los datos: no existe OOT ni PSI temporal; se declara como limitación L1, no se maquilla.
- Si falta un parámetro que cambia el resultado: detente y pregunta. No asumas en silencio.

## Convenciones de código

- Python ≥ 3.11, `SEED = 42` en todo (`src/common.py`), `requirements.txt` instalado y congelado en `requirements.lock`.
- Un script por paso: `src/stepNN_<nombre>.py`, ejecutable con `python src/stepNN_<nombre>.py`; usa `src/common.py` para
  carga, rutas y utilidades.
- Salidas por paso: `outputs/tables/stepNN_*.csv`, `outputs/figs/stepNN_*.png`, `data/processed/*.parquet`,
  `reports/stepNN.md`.
- Controles de calidad = asserts en `tests/test_stepNN.py`. Un assert que falla detiene el paso; no se relaja el umbral
  para pasar.
- Los reportes se redactan a partir de las tablas generadas, nunca al revés. Estructura fija en
  `.claude/rules/reporting.md`.
- `data/raw/` es de solo lectura.

## Estructura

```
CLAUDE.md  docs/SPEC.md  requirements.txt
.claude/{settings.json, commands/, rules/}
data/raw/client_pulse_synthetic.xlsx   data/processed/
src/common.py  src/stepNN_*.py          tests/test_stepNN.py
outputs/{tables,figs,model,scores}/     reports/{stepNN.md, gate_N.md, decision_log.md, model_document.md}
```

## Protocolo de gates

Pasos que cierran bloque: 0 → G0, 4 → G1, 11 → G2, 14 → G3, 17 → G4. Al terminar uno de esos pasos ejecuta `/gate N`,
y detente: no ejecutes ningún paso posterior hasta que el usuario responda en el chat. Si responde "usa defaults",
aplica los defaults declarados en `docs/SPEC.md` (sección I) y márcalos `[DEF-default]` en el decision_log.

## Idioma y formato

Español en reportes y decision_log. Tablas markdown, bullets densos, sin introducciones ni resúmenes ejecutivos. Bajo
cada tabla, la verificación aritmética (tramos suman 100%; churn de cartera = Σ share × tasa; captura suma 100%;
Σ puntos + base = score).
