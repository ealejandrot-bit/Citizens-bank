# STATUS · Modelo 3 (NAM)

## Estado
- Paso actual: **1 · Entorno y utilidades** (terminado). Siguiente: PASO 2 = fase 0 (perfil) tras "go".
- Tests: 5 passed, 1 skipped (test_leakage sin matrices de features todavía).

## Decisiones del usuario
| fecha | decisión |
|---|---|
| 2026-09-29 | Modelo 3 = redes neuronales (NAM monótono); protocolo paso a paso con "go" |
| 2026-09-29 | Los 4 archivos del proyecto los redacta Claude para aprobación |
| 2026-09-29 | Push a la rama de trabajo al cerrar cada fase |
| 2026-09-29 | Mismo split que M1/M2 (test ya mirado 2 veces: se declara tercera mirada) |
| 2026-09-29 | "go" al PASO 1 = aprobación de los borradores y de PyTorch (torch 2.14.0 instalado en .venv) |

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
- Ninguna nueva. `tabulate` (lo pide pandas.to_markdown) no se instaló: report.py tiene su propio renderizador markdown.

## Preguntas abiertas al dueño del dato (heredadas de M1/M2)
- Regla de `multi_signal_count`; motivo de `churn_excluded`; definición de `value_lost_6m`; fecha as-of de cada señal.

## Observaciones sobre el plan (a decidir por el usuario)
- EWS "alertas por mes" (fase 13): con un solo snapshot no hay flujo mensual; la curva se construiría repartiendo las
  alertas del corte en el horizonte de 6 meses (supuesto a aprobar).
- "Regla multi-señal reconstruida" (fase 13): `multi_signal_count` no se reconstruye con los flags visibles (ρ 0.59);
  la regla sería una aproximación (suma de flags visibles ≥ k), no la del proveedor.
