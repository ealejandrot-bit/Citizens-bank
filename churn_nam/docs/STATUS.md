# STATUS · Modelo 3 (NAM)

## Estado
- Paso actual: **10 · fase 8 (challenger interpretable)** terminada: champion provisional = EBM monótono. Siguiente: PASO 11 =
  fase 9 (NAM), bloqueada hasta llenar nam.* en config.yaml.
- Tests: 25 passed.

## Decisiones del usuario
| fecha | decisión |
|---|---|
| 2026-09-29 | Modelo 3 = redes neuronales (NAM monótono); protocolo paso a paso con "go" |
| 2026-09-29 | Los 4 archivos del proyecto los redacta Claude para aprobación |
| 2026-09-29 | Push a la rama de trabajo al cerrar cada fase |
| 2026-09-29 | Mismo split que M1/M2 (test ya mirado 2 veces: se declara tercera mirada) |
| 2026-09-29 | "go" al PASO 1 = aprobación de los borradores y de PyTorch (torch 2.14.0 instalado en .venv) |
| 2026-09-29 | Objetivo: todos los métodos en la forma más consistente posible y comparados; el más importante es A-lite |
| 2026-09-29 | multi_signal_count / multi_signal_flag: exclude (fuera de todos los modelos) |
| 2026-09-29 | Target principal A (hard 6M, el de A-lite); B se reporta siempre |
| 2026-09-29 | A-lite: solo el original congelado (comparación justa en test ∩ holdout de A-lite) |
| 2026-09-29 | Aceptadas: decisiones de la fase 2; gate final NAM vs A-lite; escala 600 @ 20:1, PDO 40, odds buenos:malos |
| 2026-09-29 | Signos (fase 4): 27 duros +, 12 duros −, 19 libres (7 has_* pasan a libres); app_* solo como máscara del NAM; 58 features |
| 2026-09-29 | Gate: ΔPR-AUC ≥ 0.03 y Δlift@5% ≥ 0.25 (NAM − A-lite, target A); validación = 20% del dev |

## Parámetros en null (config.yaml) y fase que bloquean
| parámetro | fase |
|---|---|
| nam.hidden_units, epochs_max, learning_rate, weight_decay, dropout, ensemble_members | 9 |
| scorecard.score_min, score_max | 12 |
| ews.alerts_per_month | 13 (umbral) |

## Decisiones de la fase 2 (aceptadas por el usuario el 2026-09-29; se aplican al construir features en la fase 4)
- Rangos extremos (23 variables, 0 con valores imposibles): conservar todas las filas; para el NAM, transformación por
  cuantiles de las entradas (sin recorte).
- Excepciones al gatillo: pension (60 faltan aunque aplica; 130 con dato aunque no aplica), salary (200 faltan aunque
  aplica), business payroll (52): propuesta = "dato aunque no aplica" → no aplica (como M1); "falta aunque aplica" → sin dato.
- Missing "sin regla" (6 variables): indicador de missing propio (p. ej. client_reply_rate faltante tiene +9.7 pp de churn).
- Missing "ruido" (4 variables, ≤ 1.5%): valor neutro sin indicador.

## Propuestas de la fase 5 (pendientes; nada entra al modelo sin evidencia)
- miss_recurring_deposit_stopped_flag y miss_recurring_deposit_change_pct son casi idénticos (|ρ| 0.991): dejar uno.
- 6 clusters de redundancia (|ρ| ≥ 0.70): la redundancia se resuelve en la selección de cada método (fases 7–9), no aquí.

## Preguntas abiertas al usuario
- Potencia del gate: con ≈ 106 eventos A en test ∩ holdout de A-lite, el IC de lift@5% tiene ancho ≈ ±1.3 (en validación
  con 164 eventos fue [4.2, 6.8]); exigir Δlift@5% ≥ 0.25 con IC > 0 es prácticamente inalcanzable. ¿Se mantiene?
- Criterio UHNW del gate ("sin deterioro"): en test ∩ holdout de A-lite hay 7 eventos A en UHNW; el criterio es de
  potencia casi nula. ¿Se mantiene como criterio del gate o pasa a solo reportado? `tabulate` (lo pide pandas.to_markdown) no se instaló: report.py tiene su propio renderizador markdown.

## Preguntas abiertas al dueño del dato
1. ¿Por qué 123 hogares tienen `churn_excluded` = True y targets vacíos? (se excluyen; motivo desconocido)
2. ¿Qué mide exactamente `value_lost_6m` en los soft (pérdida 20–60% del RV) y en qué ventana? Define el umbral θ de B.
3. Los 404 hogares con antigüedad < 1 año, excluidos del desarrollo, tienen más churn (M1: A 7.92% vs 6.00%): ¿hay un
   proceso de onboarding que explique su salida?
4. ¿Cuál es la regla de construcción de `multi_signal_count` / `multi_signal_flag`?
5. ¿Cuál es la fecha de corte (as-of) de cada señal pre-ingenierizada respecto del 2025-12-31?
6. ¿Soft (3M) y hard (6M) son excluyentes por diseño (0 solapes) o un hogar soft puede volverse hard después?

## Observaciones sobre el plan (a decidir por el usuario)
- EWS "alertas por mes" (fase 13): con un solo snapshot no hay flujo mensual; la curva se construiría repartiendo las
  alertas del corte en el horizonte de 6 meses (supuesto a aprobar).
- "Regla multi-señal reconstruida" (fase 13): `multi_signal_count` no se reconstruye con los flags visibles (ρ 0.59);
  la regla sería una aproximación (suma de flags visibles ≥ k), no la del proveedor.
