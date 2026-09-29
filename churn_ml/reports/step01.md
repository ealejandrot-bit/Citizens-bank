# Paso 1 · Conjunto de variables

## Objetivo
- Dejar un pool de candidatas crudas sin constantes, sin fuga y sin duplicados casi exactos.

## Método
- Casi constante: valor modal (con NaN) ≥ 99%; fuga: AUC > 0.85 o IV > 0.50 (univariado B heredado); duplicado:
  grupos con |ρ Spearman| > 0.95 en todos sus pares (enlace completo) ⟹ queda el de mayor IV (D1.1). NaN nativo; `cluster` categórica; compuestos incluidos (I-2).

## Código
- `src/step01_features.py` · `tests/test_step01.py` · `step01_screen.csv`, `step01_duplicate_pairs.csv`, `step01_funnel.csv`.

## Resultados

### Embudo [DATA]
| etapa                   |   variables |
|:------------------------|------------:|
| candidatas              |          70 |
| − casi constantes       |           0 |
| − fuga                  |           0 |
| − duplicados |ρ| > 0.95 |           8 |
| = pool                  |          62 |

- Verificación: 70 − 0 − 0 − 8 = 62 (sin solapes entre filtros: True) [DATA].

### Grupos de duplicados [DATA]
|   grupo | se queda                      | sale                          |   Spearman con la que queda |
|--------:|:------------------------------|:------------------------------|----------------------------:|
|      12 | new_external_destinations_90d | competitor_x_new_destinations |                       0.966 |
|      18 | aum_outflow_pct_90d           | aum_outflow_90d               |                       0.979 |
|      18 | aum_outflow_pct_90d           | aum_outflow_pct_90d_peer      |                       1.000 |
|      23 | net_deposit_flow_pct_90d      | net_deposit_flow_pct_90d_peer |                       1.000 |
|      30 | aum_share                     | deposit_share                 |                      -1.000 |
|      39 | contact_gap_ratio             | contact_gap_ratio_peer        |                       0.998 |
|      53 | aum                           | relationship_value            |                       0.966 |
|      53 | aum                           | log_rv                        |                       0.966 |

### Cribado completo [DATA]
| variable                                          |   modal % |   % missing |    IV |   AUC univariada | signo      | f1 casi constante   | f2 fuga   | f3 duplicado |ρ| > 0.95   | pasa   |
|:--------------------------------------------------|----------:|------------:|------:|-----------------:|:-----------|:--------------------|:----------|:--------------------------|:-------|
| segment_uhnw                                      |    94.430 |       0.000 | 0.002 |            0.506 | ?          | False               | False     | False                     | True   |
| relationship_value                                |     0.007 |       0.000 | 0.005 |            0.504 | ?          | False               | False     | True                      | False  |
| deposit_balance                                   |     0.007 |       0.000 | 0.003 |            0.502 | ?          | False               | False     | False                     | True   |
| aum                                               |    14.256 |      14.256 | 0.011 |            0.505 | ?          | False               | False     | False                     | True   |
| has_investments                                   |    85.744 |       0.000 | 0.001 |            0.506 | −          | False               | False     | False                     | True   |
| has_advisory                                      |    60.295 |       0.000 | 0.000 |            0.501 | −          | False               | False     | False                     | True   |
| has_linked_business                               |    73.706 |       0.000 | 0.000 |            0.501 | −          | False               | False     | False                     | True   |
| has_trust                                         |    68.209 |       0.000 | 0.000 |            0.501 | −          | False               | False     | False                     | True   |
| has_credit_anchor                                 |    65.895 |       0.000 | 0.002 |            0.509 | −          | False               | False     | False                     | True   |
| has_payroll_stream                                |    53.976 |       0.000 | 0.000 |            0.500 | −          | False               | False     | False                     | True   |
| has_pension_stream                                |    65.665 |       0.000 | 0.000 |            0.501 | −          | False               | False     | False                     | True   |
| has_dividend_stream                               |    52.974 |       0.000 | 0.002 |            0.511 | −          | False               | False     | False                     | True   |
| tenure_years                                      |     0.156 |       0.000 | 0.012 |            0.530 | −          | False               | False     | False                     | True   |
| history_months                                    |    94.852 |       0.000 | 0.006 |            0.505 | ?          | False               | False     | False                     | True   |
| recurring_income_monthly                          |     6.460 |       0.000 | 0.008 |            0.509 | ?          | False               | False     | False                     | True   |
| aum_outflow_pct_90d                               |    48.531 |      14.256 | 0.137 |            0.571 | +          | False               | False     | False                     | True   |
| deposit_balance_change_pct_90d                    |     0.030 |       0.030 | 0.138 |            0.576 | −          | False               | False     | False                     | True   |
| salary_deposit_stopped_flag                       |    51.113 |      47.070 | 0.122 |            0.529 | +          | False               | False     | False                     | True   |
| recurring_deposit_stopped_flag                    |    89.482 |       6.705 | 0.144 |            0.545 | +          | False               | False     | False                     | True   |
| recurring_deposit_change_pct                      |     6.772 |       6.772 | 0.099 |            0.563 | −          | False               | False     | False                     | True   |
| net_deposit_flow_pct_90d                          |     0.030 |       0.030 | 0.149 |            0.580 | −          | False               | False     | False                     | True   |
| external_transfer_pct_of_balance_60d              |     0.045 |       0.000 | 0.191 |            0.582 | +          | False               | False     | False                     | True   |
| new_external_destinations_90d                     |    92.694 |       1.498 | 0.160 |            0.555 | +          | False               | False     | False                     | True   |
| investment_redemption_pct                         |    40.743 |      14.256 | 0.123 |            0.572 | +          | False               | False     | False                     | True   |
| products_closed_180d                              |    90.484 |       0.000 | 0.217 |            0.561 | +          | False               | False     | False                     | True   |
| banker_change_6m_flag                             |    85.336 |       0.000 | 0.289 |            0.608 | +          | False               | False     | False                     | True   |
| contact_gap_ratio                                 |     3.123 |       0.000 | 0.131 |            0.602 | +          | False               | False     | False                     | True   |
| client_reply_rate                                 |    48.072 |      48.072 | 0.218 |            0.529 | −          | False               | False     | False                     | True   |
| complaint_escalated_flag                          |    94.704 |       0.000 | 0.093 |            0.540 | +          | False               | False     | False                     | True   |
| complaint_age_days                                |    96.588 |       0.000 | 0.033 |            0.528 | +          | False               | False     | False                     | True   |
| aum_vs_baseline_pct                               |    14.256 |      14.256 | 0.182 |            0.582 | −          | False               | False     | False                     | True   |
| deposit_balance_vs_6m_avg_pct                     |     0.037 |       0.037 | 0.178 |            0.585 | −          | False               | False     | False                     | True   |
| pension_deposit_stopped_flag                      |    66.007 |      66.007 | 0.050 |            0.511 | +          | False               | False     | False                     | True   |
| business_payroll_stopped_flag                     |    74.017 |      74.017 | 0.031 |            0.512 | +          | False               | False     | False                     | True   |
| transfer_to_competitor_pct_90d                    |    15.658 |       0.000 | 0.163 |            0.569 | +          | False               | False     | False                     | True   |
| external_transfer_acceleration                    |     0.022 |       0.000 | 0.128 |            0.515 | +          | False               | False     | False                     | True   |
| net_external_flow_pct_90d                         |     0.015 |       0.000 | 0.166 |            0.578 | −          | False               | False     | False                     | True   |
| external_destination_concentration                |    20.657 |       0.000 | 0.102 |            0.533 | +          | False               | False     | False                     | True   |
| outflow_vs_baseline_pct                           |     1.899 |       0.000 | 0.055 |            0.529 | +          | False               | False     | False                     | True   |
| fixed_income_maturity_not_reinvested              |    74.054 |      74.054 | 0.044 |            0.534 | +          | False               | False     | False                     | True   |
| cash_pct_of_portfolio_chg                         |    14.256 |      14.256 | 0.090 |            0.548 | +          | False               | False     | False                     | True   |
| return_vs_benchmark                               |    39.705 |      39.705 | 0.057 |            0.560 | −          | False               | False     | False                     | True   |
| accounts_closed_90d                               |    85.410 |       0.000 | 0.061 |            0.540 | +          | False               | False     | False                     | True   |
| share_of_wallet                                   |     5.926 |       0.000 | 0.173 |            0.610 | −          | False               | False     | False                     | True   |
| share_of_wallet_change                            |     4.065 |       0.000 | 0.131 |            0.584 | −          | False               | False     | False                     | True   |
| trustee_change_flag                               |    68.209 |      68.209 | 0.038 |            0.513 | +          | False               | False     | False                     | True   |
| repeat_complaint_flag                             |    96.254 |       0.000 | 0.097 |            0.536 | +          | False               | False     | False                     | True   |
| positions_liquidated_pct                          |    74.789 |      14.256 | 0.083 |            0.548 | +          | False               | False     | False                     | True   |
| meetings_cancelled_by_client                      |    61.015 |      61.015 | 0.066 |            0.537 | +          | False               | False     | False                     | True   |
| relationship_dissatisfaction_flag                 |    70.257 |      70.257 | 0.027 |            0.511 | +          | False               | False     | False                     | True   |
| aum_outflow_90d                                   |    48.531 |      14.256 | 0.135 |            0.571 | +          | False               | False     | True                      | False  |
| transfer_to_competitor_bank_amount_90d            |    15.658 |       0.000 | 0.173 |            0.571 | +          | False               | False     | False                     | True   |
| log_rv                                            |     0.007 |       0.000 | 0.005 |            0.504 | ?          | False               | False     | True                      | False  |
| aum_share                                         |    14.256 |       0.000 | 0.003 |            0.510 | ?          | False               | False     | False                     | True   |
| deposit_share                                     |    14.256 |       0.000 | 0.003 |            0.510 | ?          | False               | False     | True                      | False  |
| streams_stopped_count                             |    94.838 |       0.000 | 0.200 |            0.556 | +          | False               | False     | False                     | True   |
| n_streams_eligible                                |    62.061 |       0.000 | 0.003 |            0.500 | −          | False               | False     | False                     | True   |
| n_products_held                                   |    29.372 |       0.000 | 0.005 |            0.504 | −          | False               | False     | False                     | True   |
| outflow_x_contact_gap                             |    63.848 |       0.000 | 0.161 |            0.580 | +          | False               | False     | False                     | True   |
| competitor_x_new_destinations                     |    93.057 |       1.498 | 0.112 |            0.555 | +          | False               | False     | True                      | False  |
| ind_sin_dato_client_reply_rate                    |    51.928 |       0.000 | 0.160 |            0.599 | +          | False               | False     | False                     | True   |
| ind_sin_dato_meetings_cancelled_by_client         |    61.015 |       0.000 | 0.008 |            0.521 | ?          | False               | False     | False                     | True   |
| ind_sin_dato_relationship_dissatisfaction_flag    |    70.257 |       0.000 | 0.000 |            0.501 | ?          | False               | False     | False                     | True   |
| ind_sin_dato_fixed_income_maturity_not_reinvested |    74.054 |       0.000 | 0.001 |            0.508 | ?          | False               | False     | False                     | True   |
| aum_outflow_pct_90d_peer                          |    48.531 |      14.256 | 0.137 |            0.571 | +          | False               | False     | True                      | False  |
| net_deposit_flow_pct_90d_peer                     |     0.037 |       0.030 | 0.148 |            0.580 | −          | False               | False     | True                      | False  |
| contact_gap_ratio_peer                            |     1.943 |       0.000 | 0.131 |            0.602 | +          | False               | False     | True                      | False  |
| multi_signal_flag                                 |    76.317 |       0.000 | 0.252 |            0.615 | +          | False               | False     | False                     | True   |
| multi_signal_count                                |    32.213 |       0.000 | 0.463 |            0.659 | +          | False               | False     | False                     | True   |
| cluster                                           |    52.885 |       0.000 | 0.003 |          nan     | categórica | False               | False     | False                     | True   |

## Tests
- `tests/test_step01.py` (ver pytest).

## Decisiones y preguntas abiertas
- D1.1 en `reports/decision_log.md`.
