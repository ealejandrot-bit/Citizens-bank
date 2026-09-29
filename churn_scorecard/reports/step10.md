# Paso 10 · Selección

## Objetivo
- Campeón: 6–10 variables WoE no redundantes, con signo de negocio y aporte incremental. Challenger: 15–30 variables.

## Método
- Campeón: elegibles (IV ≥ 0.02, signo esperado definido y tendencia coincidente, sin compuestos / edad / buró) →
  VarClus sobre WoE (partir si 2º autovalor > 1) → representante = menor (1−R²propio)/(1−R²vecino), desempate IV →
  adición hacia adelante sobre todos los miembros, a lo sumo uno por cluster (D10.2): entra la de mayor ΔGini medio en los 25 folds (5×5) si ΔGini > 0 en ≥ 80% de los folds
  [DEF-default D10.1], VIF(WoE) < 5 y todos los β con signo correcto; tope 10 → ElasticNet (l1_ratio 0.5, C por CV y
  regla 1-SE) como control.
- Challenger: casi constantes (modal ≥ 99%) → fuga (AUC > 0.85 o IV > 0.50) → un representante (mayor IV) por cluster
  de |ρ Spearman| > 0.75 (enlace completo) → permutation importance OOF (XGBoost prof. 3, ΔPR-AUC en el fold de
  prueba, 3 permutaciones) > 0 en ≥ 80% de los folds → signo (a priori, o "?" sin restricción por G1-1). Tope 30.

## Código
- `src/step10_selection.py` · `tests/test_step10.py` · `step10_*.csv`, `outputs/model/step10_selection.pkl`.

## Resultados

### Embudo del campeón [DATA]
| etapa                     |   variables |
|:--------------------------|------------:|
| candidatas paso 9         |          68 |
| elegibles campeón         |          44 |
| clusters VarClus          |          11 |
| seleccionadas por adición |           8 |

- Excluidas por motivo [DATA]: IV < 0.02: 24.

### VarClus: representantes [DATA]
|   cluster | variable                          |   R² propio |   R² vecino |   1−R² ratio |    IV | dimensión     |   2º autovalor del cluster |
|----------:|:----------------------------------|------------:|------------:|-------------:|------:|:--------------|---------------------------:|
|         1 | competitor_x_new_destinations     |       0.772 |       0.297 |        0.325 | 0.155 | transaccional |                      0.958 |
|         2 | net_deposit_flow_pct_90d          |       0.888 |       0.348 |        0.172 | 0.184 | transaccional |                      0.815 |
|         3 | cash_pct_of_portfolio_chg         |       0.699 |       0.039 |        0.313 | 0.107 | transaccional |                      0.935 |
|         4 | aum_outflow_pct_90d               |       0.937 |       0.383 |        0.103 | 0.168 | transaccional |                      0.278 |
|         5 | complaint_escalated_flag          |       0.637 |       0.021 |        0.370 | 0.092 | servicio      |                      0.969 |
|         6 | business_payroll_stopped_flag     |       1.000 |       0.018 |        0.000 | 0.031 | transaccional |                      0.000 |
|         7 | streams_stopped_count             |       0.927 |       0.237 |        0.096 | 0.199 | transaccional |                      0.953 |
|         8 | client_reply_rate                 |       0.926 |       0.222 |        0.095 | 0.216 | relación      |                      0.983 |
|         9 | contact_gap_ratio                 |       0.993 |       0.228 |        0.010 | 0.139 | relación      |                      0.015 |
|        10 | relationship_dissatisfaction_flag |       0.552 |       0.018 |        0.456 | 0.027 | servicio      |                      0.897 |
|        11 | accounts_closed_90d               |       0.816 |       0.200 |        0.230 | 0.120 | producto      |                      0.941 |

- 11 clusters, todos con 2º autovalor ≤ 1 [DATA]. Composición completa en `step10_varclus.csv`.

### Adición hacia adelante (variables que entran) [DATA]
|   paso | variable                  |   cluster | representante 1−R²   |   Gini CV |   ΔGini medio |   % folds ΔGini > 0 |   VIF máx |
|-------:|:--------------------------|----------:|:---------------------|----------:|--------------:|--------------------:|----------:|
|      1 | client_reply_rate         |         8 | True                 |    0.2339 |        0.2339 |            100.0000 |    1.0000 |
|      2 | banker_change_6m_flag     |        10 | False                |    0.3576 |        0.1237 |            100.0000 |    1.0071 |
|      3 | share_of_wallet           |         2 | False                |    0.3970 |        0.0394 |            100.0000 |    1.0339 |
|      4 | outflow_x_contact_gap     |         4 | False                |    0.4127 |        0.0156 |            100.0000 |    1.1335 |
|      5 | return_vs_benchmark       |         5 | False                |    0.4246 |        0.0120 |             96.0000 |    1.1344 |
|      6 | streams_stopped_count     |         7 | True                 |    0.4322 |        0.0076 |             92.0000 |    1.1829 |
|      7 | cash_pct_of_portfolio_chg |         3 | True                 |    0.4385 |        0.0063 |             92.0000 |    1.1989 |
|      8 | contact_gap_ratio_peer    |         9 | False                |    0.4413 |        0.0028 |             80.0000 |    1.3822 |

- La adición se detiene en 8 variables: ninguna otra cumple las tres condiciones [DATA].
- Verificación: Gini CV final = 0.4413 = Σ ΔGini (0.4413) [DATA].

### Regla del representante: literal vs D10.2 [DATA]
| variante                                   |   variables |   Gini CV |   sd folds | selección                                                                                                                                                                       |   % folds D10.2 > literal |
|:-------------------------------------------|------------:|----------:|-----------:|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------:|
| SPEC literal (solo representantes 1−R²)    |           7 |    0.3861 |     0.0311 | client_reply_rate, net_deposit_flow_pct_90d, cash_pct_of_portfolio_chg, complaint_escalated_flag, streams_stopped_count, contact_gap_ratio, aum_outflow_pct_90d                 |                  nan      |
| D10.2 (uno por cluster, cualquier miembro) |           8 |    0.4413 |     0.0269 | client_reply_rate, banker_change_6m_flag, share_of_wallet, outflow_x_contact_gap, return_vs_benchmark, streams_stopped_count, cash_pct_of_portfolio_chg, contact_gap_ratio_peer |                  100.0000 |

- La regla literal elige por (1−R²propio)/(1−R²vecino) y deja fuera variables fuertes cuando el cluster agrupa señales
  de negocio distintas (p. ej. cluster 10: `banker_change_6m_flag` IV 0.289 pierde contra
  `relationship_dissatisfaction_flag` IV 0.027) [DATA]. D10.2 mantiene la no redundancia (una por cluster, VIF < 5)
  y deja que el aporte incremental elija el miembro. Pregunta G2-3.

### Variables del campeón [DATA]
| variable                  |    IV | dimensión     | signo esperado   |   VIF (WoE) | β EN 1-SE ≠ 0   | regla de bins                     |   cluster | representante 1−R² del cluster    |
|:--------------------------|------:|:--------------|:-----------------|------------:|:----------------|:----------------------------------|----------:|:----------------------------------|
| client_reply_rate         | 0.216 | relación      | −                |       1.302 | True            | optbinning 5%                     |         8 | client_reply_rate                 |
| banker_change_6m_flag     | 0.289 | relación      | +                |       1.074 | True            | negocio {0,1} (D9.1)              |        10 | relationship_dissatisfaction_flag |
| share_of_wallet           | 0.196 | patrimonial   | −                |       1.137 | True            | optbinning 5%                     |         2 | net_deposit_flow_pct_90d          |
| outflow_x_contact_gap     | 0.205 | transaccional | +                |       1.278 | True            | optbinning 5%                     |         4 | aum_outflow_pct_90d               |
| return_vs_benchmark       | 0.061 | economía      | −                |       1.011 | True            | optbinning 5%                     |         5 | complaint_escalated_flag          |
| streams_stopped_count     | 0.199 | transaccional | +                |       1.141 | True            | negocio inflada en mínimo (D9.1b) |         7 | streams_stopped_count             |
| cash_pct_of_portfolio_chg | 0.107 | transaccional | +                |       1.058 | True            | optbinning 5%                     |         3 | cash_pct_of_portfolio_chg         |
| contact_gap_ratio_peer    | 0.139 | relación      | +                |       1.382 | True            | optbinning 5%                     |         9 | contact_gap_ratio                 |

- Dimensiones [DATA]: relación 3, transaccional 3, patrimonial 1, economía 1.
- ElasticNet 1-SE (C = 0.006952) sobre las 44 elegibles conserva 8 de 8 seleccionadas [DATA].

### Embudo del challenger [DATA]
| etapa                                 |   variables |
|:--------------------------------------|------------:|
| candidatas (con compuestos y cluster) |          70 |
| − casi constantes                     |           0 |
| − fuga                                |           0 |
| − redundantes |ρ| > 0.75              |          14 |
| − permutación < 80% folds             |          40 |
| = challenger                          |          16 |

### Challenger: variables que pasan [DATA]
| variable                               | signo   |   IV (paso 6) |   ΔPR-AUC medio |   % folds > 0 |
|:---------------------------------------|:--------|--------------:|----------------:|--------------:|
| banker_change_6m_flag                  | +       |        0.2894 |          0.0352 |      100.0000 |
| client_reply_rate                      | −       |        0.2181 |          0.0191 |      100.0000 |
| multi_signal_count                     | ?       |        0.4634 |          0.0180 |      100.0000 |
| share_of_wallet                        | −       |        0.1733 |          0.0080 |       92.0000 |
| fixed_income_maturity_not_reinvested   | +       |        0.0437 |          0.0063 |      100.0000 |
| transfer_to_competitor_bank_amount_90d | +       |        0.1726 |          0.0052 |       96.0000 |
| recurring_deposit_change_pct           | −       |        0.0987 |          0.0036 |       80.0000 |
| contact_gap_ratio                      | +       |        0.1310 |          0.0033 |       80.0000 |
| cash_pct_of_portfolio_chg              | +       |        0.0899 |          0.0030 |       88.0000 |
| repeat_complaint_flag                  | +       |        0.0968 |          0.0027 |       80.0000 |
| streams_stopped_count                  | +       |        0.1996 |          0.0027 |       84.0000 |
| net_external_flow_pct_90d              | −       |        0.1659 |          0.0023 |       80.0000 |
| meetings_cancelled_by_client           | +       |        0.0665 |          0.0022 |       88.0000 |
| complaint_escalated_flag               | +       |        0.0927 |          0.0016 |       84.0000 |
| share_of_wallet_change                 | −       |        0.1309 |          0.0014 |       80.0000 |
| business_payroll_stopped_flag          | +       |        0.0309 |          0.0006 |       84.0000 |

- Verificación: 70 − 0 − 0 − 14 − 40 − 0 (tope 30) = 16 [DATA].

## Tests
- `tests/test_step10.py` (ver pytest).

## Decisiones y preguntas abiertas
- D10.1–D10.4 en `reports/decision_log.md`.
