# Churn Propensity · Modelo 2 (ML) — `client_pulse_synthetic.xlsx`

## Qué es este repo

Modelo 2 de propensión a churn para households de banca privada: gradient boosting monotónico (XGBoost / LightGBM) con
TreeSHAP, calibración y escala PDO, desarrollado de punta a punta hasta monitoreo y comparado formalmente contra el
Modelo 1 (scorecard WoE + logística, `../churn_scorecard/`, versión 1.0.0). Mismo dataset sintético (20,000 households,
un snapshot 2025-12-31), mismo target, mismo split y mismo holdout, para que la comparación sea limpia. El método
completo está en `docs/SPEC.md`; se ejecuta un paso a la vez con `/step NN`. Tú diseñas, ejecutas y documentas como
Senior Quantitative Risk Architect bajo Model Risk Management (SR 11-7 o equivalente).

## Comandos del proyecto

- `/step NN` — ejecuta el paso NN (00–12) según `docs/SPEC.md`: script, tablas, tests, reporte, decision_log.
- `/gate N` — cierra un bloque: escribe `reports/gate_N.md` y se detiene a esperar respuesta del usuario.
- `/status` — dónde vamos, qué está en verde, qué preguntas siguen abiertas.
- `python -m pytest -q` — debe estar en verde antes de cada gate.

## Inicio de cada sesión

1. Lee `reports/decision_log.md` si existe (parámetros vigentes, decisiones, preguntas abiertas). Es la memoria del
   proyecto; nada se decide fuera de él.
2. No repitas pasos completados. No adelantes pasos posteriores a un gate no aprobado.

## Reglas duras (detalle en `.claude/rules/`)

- Modo DATA: toda cifra sale del archivo y lleva `[DATA]`; parámetros del usuario `[DEF]`; defaults aplicados
  `[DEF-default]`. Cifra sin etiqueta = error. Nada inventado, ningún benchmark de industria ni cifra de bancos reales.
- Columnas de resultado (`hard_churn_6m`, `soft_churn_3m`, `value_lost_6m`, `churn_excluded`) nunca son predictores.
- Missing estructural = NaN nativo del GBM; prohibido imputar por media/mediana.
- Monotonía por signo de negocio (heredado de G1-1 del Modelo 1); "?" sin restricción. Profundidad ≤ 3.
- SHAP explica; no vuelve aditivo al modelo. Los reason codes se reportan con su estabilidad.
- Calibración ajustada sin tocar el holdout (OOF cruzado en dev). El holdout se usa una sola vez, con el modelo final.
- Score único = puntos escala PDO (S₀ = 600 @ 20:1, PDO = 40 ⟹ Factor 57.71, Offset 427.12). Score, probabilidad y churn
  rate son tres cosas distintas.
- Sin OOT ni PSI temporal (L1). Sin Basilea ni IFRS 9. Clustering nunca causal.
- Si falta un parámetro que cambia el resultado: detente y pregunta.

## Convenciones de código

- Python ≥ 3.11, `SEED = 42`, `requirements.txt` + `requirements.lock` (mismas versiones que `../churn_scorecard/`).
- Un script por paso: `src/stepNN_<nombre>.py`; utilidades en `src/common.py`. Entradas heredadas en
  `data/inherited/` (copiadas con sha256 en el paso 0, solo lectura).
- Salidas: `outputs/tables/stepNN_*.csv`, `outputs/figs/stepNN_*.png`, `outputs/model/`, `outputs/scores/`,
  `reports/stepNN.md`.
- Controles = asserts en `tests/test_stepNN.py`; un assert que falla detiene el paso; no se relaja el umbral.
- Reportes redactados desde las tablas (`.claude/rules/reporting.md`).

## Protocolo de gates

Pasos que cierran bloque: 0 → G0, 3 → G1, 6 → G2, 9 → G3, 12 → G4. Al terminar uno de esos pasos ejecuta `/gate N` y
detente hasta que el usuario responda. Si responde "usa defaults", aplica los defaults de `docs/SPEC.md` (sección I) y
márcalos `[DEF-default]`. Las preguntas se explican en lenguaje simple (el usuario lo pidió en el Modelo 1).

## Idioma y formato

Español. Tablas markdown, bullets densos, sin introducciones. Bajo cada tabla, la verificación aritmética (tramos suman
100%; Σ share × tasa = churn de cartera; captura suma 100%; base + Σ puntos = score).
