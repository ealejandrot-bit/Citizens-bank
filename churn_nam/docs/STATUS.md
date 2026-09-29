# STATUS · Modelo 3 (NAM)

## Estado
- Paso actual: **3 · fase 1 (target y población)** terminada: 19,473 hogares tras exclusiones (123 churn_excluded + 404
  antigüedad < 1). Siguiente: PASO 4 = fase 2 tras "go".
- Tests: 9 passed, 1 skipped.

## Decisiones del usuario
| fecha | decisión |
|---|---|
| 2026-09-29 | Modelo 3 = redes neuronales (NAM monótono); protocolo paso a paso con "go" |
| 2026-09-29 | Los 4 archivos del proyecto los redacta Claude para aprobación |
| 2026-09-29 | Push a la rama de trabajo al cerrar cada fase |
| 2026-09-29 | Mismo split que M1/M2 (test ya mirado 2 veces: se declara tercera mirada) |
| 2026-09-29 | "go" al PASO 1 = aprobación de los borradores y de PyTorch (torch 2.14.0 instalado en .venv) |
| 2026-09-29 | Objetivo: todos los métodos en la forma más consistente posible y comparados; el más importante es A-lite |

## Parámetros en null (config.yaml) y fase que bloquean
| parámetro | fase |
|---|---|
| splits.validation_frac_of_dev | 6 |
| leakage.multi_signal_count | 3 |
| nam.hidden_units, epochs_max, learning_rate, weight_decay, dropout, ensemble_members | 9 |
| gate.delta_pr_auc, gate.delta_lift_at_5 | 6 (pre-registro) y 10 |
| scorecard.pdo, s0, o0, odds_convention, score_min, score_max | 12 |
| ews.alerts_per_month | 13 (umbral) |

## Preguntas abiertas al usuario
- Marco de comparación consistente con A-lite como referencia (ver resumen de la fase 0): target principal, forma de
  A-lite (congelado vs re-estimado con su receta), referencia del gate y escala del scorecard.
- Ninguna otra. `tabulate` (lo pide pandas.to_markdown) no se instaló: report.py tiene su propio renderizador markdown.

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
