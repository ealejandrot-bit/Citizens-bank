# Client Pulse · Modelo 3 (redes neuronales: NAM monótono) — `client_pulse_synthetic.xlsx`

## Qué es este repo

Modelo 3 de propensión a churn (HNW/UHNW): Neural Additive Model (NAM) monótono comparado contra un champion
interpretable (LightGBM monótono / EBM) y contra los modelos ya cerrados (M1 scorecard 1.0.0 en `../churn_scorecard/`,
M2 ML 1.0.0 en `../churn_ml/`, A-lite en `../scorecard/`), con el mismo split que M1/M2. Rol: Lead Quantitative
Scientist & Model Risk Architect. Método en `docs/SPEC.md`; estado vivo en `docs/STATUS.md`; parámetros en `config.yaml`.

## Protocolo de trabajo (del usuario)

- Un paso a la vez. Cada paso termina con un resumen de 6 puntos: qué hice, resultados, qué aprendimos, problemas,
  go/no-go, qué falta. Me detengo; no paso al siguiente hasta que el usuario escriba "go".
- Si un paso está mal planteado, lo digo antes de ejecutarlo; no lo corrijo en silencio.
- Si falta un dato, parámetro o archivo: pregunto; nunca lo relleno con un supuesto. Un parámetro en `null` detiene la
  fase que lo necesita (error claro de `src/config.py`).
- Ningún número de un reporte se escribe a mano: todo sale de `outputs/pNN/`.
- Si un test falla, se corrige el código, nunca el test.
- Paquete fuera de `requirements.txt`: preguntar antes de instalar.
- Un commit por fase, con push a la rama de trabajo al cerrar la fase (decisión del usuario, 2026-09-29).
- Si algo del plan no aplica a los datos, se dice en el resumen de la fase y se espera decisión.

## Reglas duras (detalle en `docs/SPEC.md` §3)

- Primera línea fija de todo reporte: "Dataset sintético, corte transversal: valida pipeline y metodología, no
  conclusiones sobre clientes reales."
- `value_lost_6m`, `hard_churn_6m`, `soft_churn_3m`, `churn_excluded` nunca son features (`tests/test_leakage.py`).
- Monotonía dura (violación = 0) en las variables con signo de negocio; nunca se relaja una restricción para que el
  NAM converja.
- El test se abre una sola vez en este proyecto (fase 10), con el gate pre-registrado en `config.yaml`.
- Modelos anteriores (`../churn_scorecard`, `../churn_ml`, `../scorecard`) son de solo lectura.

## Comandos

- `/fase N` — ejecuta la fase N (0–13) de `docs/SPEC.md` §5.
- `python -m pytest -q` — en verde antes de cerrar cada fase.

## Convenciones

- Python ≥ 3.11 en `.venv`; `requirements.txt` + `requirements.lock`; `outputs/env.json` con versiones.
- `src/config.py` (parámetros y rutas), `src/report.py` (renderiza `reports/pNN.md` desde `outputs/pNN/`),
  `src/pNN_<nombre>.py` por fase, `src/nam/` (modelo NAM).
- Salidas por fase en `outputs/pNN/` (json, csv, png); reporte en `reports/pNN.md`.
- Español en reportes y STATUS.
