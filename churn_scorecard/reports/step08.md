# Paso 8 · Correlación y diagnóstico de estructura

## Objetivo
- Identificar redundancias entre candidatas y decidir cuál aporta información incremental, antes de seleccionar.

## Método
- Pearson y Spearman en dev (target B); pares con |ρ| > 0.6 en cualquiera de las dos.
- Información incremental: ΔAUC (CV 5 folds, logística sobre rangos normalizados + indicador de missing) de agregar la
  otra variable; < 0.005 = redundantes. IV del paso 6 como desempate.
- VIF sobre rangos normalizados (diagnóstico; el VIF que decide es sobre WoE, paso 10). PCA por bloque: solo diagnóstico.

## Código
- `src/step08_structure.py` · `tests/test_step08.py` · `step08_spearman.csv`, `step08_pearson.csv`, `step08_pairs.csv`,
  `step08_vif.csv`, `step08_pca_blocks.csv`, `step08_pca_loadings.csv`.

## Resultados

### Pares con |ρ| > 0.6 y decisión [DATA]
| var A                                | var B                                  |   Spearman |   Pearson |   IV A |   IV B |   ΔAUC por agregar la otra | mayor IV                               | decisión                                                       |
|:-------------------------------------|:---------------------------------------|-----------:|----------:|-------:|-------:|---------------------------:|:---------------------------------------|:---------------------------------------------------------------|
| relationship_value                   | log_rv                                 |      1.000 |     0.618 |  0.005 |  0.005 |                     -0.000 | relationship_value                     | redundantes: queda la de mayor IV                              |
| aum_outflow_pct_90d                  | aum_outflow_pct_90d_peer               |      1.000 |     1.000 |  0.137 |  0.137 |                     -0.000 | aum_outflow_pct_90d                    | redundantes: queda la de mayor IV                              |
| aum_share                            | deposit_share                          |     -1.000 |    -1.000 |  0.003 |  0.003 |                     -0.000 | aum_share                              | redundantes: queda la de mayor IV                              |
| net_deposit_flow_pct_90d             | net_deposit_flow_pct_90d_peer          |      0.999 |     1.000 |  0.149 |  0.148 |                     -0.000 | net_deposit_flow_pct_90d               | redundantes: queda la de mayor IV                              |
| contact_gap_ratio                    | contact_gap_ratio_peer                 |      0.998 |     1.000 |  0.131 |  0.131 |                     -0.000 | contact_gap_ratio                      | redundantes: queda la de mayor IV                              |
| aum_outflow_90d                      | aum_outflow_pct_90d_peer               |      0.979 |     0.336 |  0.135 |  0.137 |                     -0.000 | aum_outflow_pct_90d_peer               | redundantes: queda la de mayor IV                              |
| aum_outflow_pct_90d                  | aum_outflow_90d                        |      0.979 |     0.336 |  0.137 |  0.135 |                     -0.000 | aum_outflow_pct_90d                    | redundantes: queda la de mayor IV                              |
| new_external_destinations_90d        | competitor_x_new_destinations          |      0.966 |     0.568 |  0.160 |  0.112 |                     -0.000 | new_external_destinations_90d          | redundantes: queda la de mayor IV                              |
| aum                                  | log_rv                                 |      0.966 |     0.604 |  0.011 |  0.005 |                     -0.001 | aum                                    | redundantes: queda la de mayor IV                              |
| relationship_value                   | aum                                    |      0.966 |     0.964 |  0.005 |  0.011 |                     -0.001 | aum                                    | redundantes: queda la de mayor IV                              |
| outflow_x_contact_gap                | aum_outflow_pct_90d_peer               |      0.952 |     0.689 |  0.161 |  0.137 |                      0.006 | outflow_x_contact_gap                  | información incremental: ambas pasan al paso 10                |
| aum_outflow_pct_90d                  | outflow_x_contact_gap                  |      0.952 |     0.689 |  0.137 |  0.161 |                      0.006 | outflow_x_contact_gap                  | información incremental: ambas pasan al paso 10                |
| aum_outflow_90d                      | outflow_x_contact_gap                  |      0.940 |     0.233 |  0.135 |  0.161 |                      0.006 | outflow_x_contact_gap                  | información incremental: ambas pasan al paso 10                |
| net_deposit_flow_pct_90d             | deposit_balance_vs_6m_avg_pct          |      0.905 |     0.849 |  0.149 |  0.178 |                     -0.000 | deposit_balance_vs_6m_avg_pct          | redundantes: queda la de mayor IV                              |
| deposit_balance_vs_6m_avg_pct        | net_deposit_flow_pct_90d_peer          |      0.904 |     0.849 |  0.178 |  0.148 |                     -0.000 | deposit_balance_vs_6m_avg_pct          | redundantes: queda la de mayor IV                              |
| deposit_balance_change_pct_90d       | deposit_balance_vs_6m_avg_pct          |      0.881 |     0.888 |  0.138 |  0.178 |                     -0.000 | deposit_balance_vs_6m_avg_pct          | redundantes: queda la de mayor IV                              |
| recurring_deposit_stopped_flag       | streams_stopped_count                  |      0.860 |     0.891 |  0.144 |  0.200 |                     -0.001 | streams_stopped_count                  | redundantes: queda la de mayor IV                              |
| transfer_to_competitor_pct_90d       | transfer_to_competitor_bank_amount_90d |      0.813 |     0.379 |  0.163 |  0.173 |                     -0.001 | transfer_to_competitor_bank_amount_90d | redundantes: queda la de mayor IV                              |
| deposit_balance_change_pct_90d       | net_deposit_flow_pct_90d               |      0.802 |     0.768 |  0.138 |  0.149 |                     -0.000 | net_deposit_flow_pct_90d               | redundantes: queda la de mayor IV                              |
| deposit_balance_change_pct_90d       | net_deposit_flow_pct_90d_peer          |      0.801 |     0.768 |  0.138 |  0.148 |                     -0.000 | net_deposit_flow_pct_90d_peer          | redundantes: queda la de mayor IV                              |
| business_payroll_stopped_flag        | streams_stopped_count                  |      0.773 |     0.634 |  0.031 |  0.200 |                      0.007 | streams_stopped_count                  | información incremental: ambas pasan al paso 10                |
| recurring_deposit_stopped_flag       | pension_deposit_stopped_flag           |      0.772 |     0.772 |  0.144 |  0.050 |                     -0.005 | recurring_deposit_stopped_flag         | redundantes: queda la de mayor IV                              |
| aum_outflow_pct_90d                  | aum_vs_baseline_pct                    |     -0.767 |    -0.859 |  0.137 |  0.182 |                     -0.001 | aum_vs_baseline_pct                    | redundantes: queda la de mayor IV                              |
| aum_vs_baseline_pct                  | aum_outflow_pct_90d_peer               |     -0.767 |    -0.859 |  0.182 |  0.137 |                     -0.001 | aum_vs_baseline_pct                    | redundantes: queda la de mayor IV                              |
| multi_signal_flag                    | multi_signal_count                     |      0.758 |     0.818 |  0.252 |  0.463 |                     -0.000 | multi_signal_count                     | redundantes: queda la de mayor IV (compuesto: solo challenger) |
| net_deposit_flow_pct_90d             | net_external_flow_pct_90d              |      0.755 |     0.806 |  0.149 |  0.166 |                      0.001 | net_external_flow_pct_90d              | redundantes: queda la de mayor IV                              |
| net_external_flow_pct_90d            | net_deposit_flow_pct_90d_peer          |      0.755 |     0.806 |  0.166 |  0.148 |                      0.001 | net_external_flow_pct_90d              | redundantes: queda la de mayor IV                              |
| salary_deposit_stopped_flag          | recurring_deposit_stopped_flag         |      0.754 |     0.754 |  0.122 |  0.144 |                      0.010 | recurring_deposit_stopped_flag         | información incremental: ambas pasan al paso 10                |
| aum_vs_baseline_pct                  | aum_outflow_90d                        |     -0.745 |    -0.345 |  0.182 |  0.135 |                     -0.001 | aum_vs_baseline_pct                    | redundantes: queda la de mayor IV                              |
| relationship_value                   | deposit_balance                        |      0.729 |     0.817 |  0.005 |  0.003 |                      0.003 | relationship_value                     | redundantes: queda la de mayor IV                              |
| deposit_balance                      | log_rv                                 |      0.729 |     0.514 |  0.003 |  0.005 |                      0.003 | log_rv                                 | redundantes: queda la de mayor IV                              |
| aum_vs_baseline_pct                  | outflow_x_contact_gap                  |     -0.723 |    -0.574 |  0.182 |  0.161 |                      0.004 | aum_vs_baseline_pct                    | redundantes: queda la de mayor IV                              |
| deposit_balance_vs_6m_avg_pct        | share_of_wallet_change                 |      0.717 |     0.610 |  0.178 |  0.131 |                      0.004 | deposit_balance_vs_6m_avg_pct          | redundantes: queda la de mayor IV                              |
| has_linked_business                  | n_streams_eligible                     |      0.713 |     0.693 |  0.000 |  0.003 |                     -0.012 | n_streams_eligible                     | redundantes: queda la de mayor IV                              |
| salary_deposit_stopped_flag          | streams_stopped_count                  |      0.711 |     0.883 |  0.122 |  0.200 |                      0.010 | streams_stopped_count                  | información incremental: ambas pasan al paso 10                |
| recurring_income_monthly             | n_streams_eligible                     |      0.695 |     0.454 |  0.008 |  0.003 |                     -0.007 | recurring_income_monthly               | redundantes: queda la de mayor IV                              |
| deposit_balance_vs_6m_avg_pct        | net_external_flow_pct_90d              |      0.689 |     0.663 |  0.178 |  0.166 |                     -0.001 | deposit_balance_vs_6m_avg_pct          | redundantes: queda la de mayor IV                              |
| pension_deposit_stopped_flag         | streams_stopped_count                  |      0.682 |     0.832 |  0.050 |  0.200 |                     -0.003 | streams_stopped_count                  | redundantes: queda la de mayor IV                              |
| deposit_balance_change_pct_90d       | share_of_wallet_change                 |      0.673 |     0.567 |  0.138 |  0.131 |                      0.003 | deposit_balance_change_pct_90d         | redundantes: queda la de mayor IV                              |
| deposit_balance                      | aum                                    |      0.670 |     0.665 |  0.003 |  0.011 |                     -0.000 | aum                                    | redundantes: queda la de mayor IV                              |
| investment_redemption_pct            | aum_outflow_pct_90d_peer               |      0.661 |     0.412 |  0.123 |  0.137 |                      0.009 | aum_outflow_pct_90d_peer               | información incremental: ambas pasan al paso 10                |
| aum_outflow_pct_90d                  | investment_redemption_pct              |      0.661 |     0.412 |  0.137 |  0.123 |                      0.009 | aum_outflow_pct_90d                    | información incremental: ambas pasan al paso 10                |
| investment_redemption_pct            | aum_outflow_90d                        |      0.647 |     0.125 |  0.123 |  0.135 |                      0.010 | aum_outflow_90d                        | información incremental: ambas pasan al paso 10                |
| investment_redemption_pct            | fixed_income_maturity_not_reinvested   |      0.635 |     0.421 |  0.123 |  0.044 |                      0.011 | investment_redemption_pct              | información incremental: ambas pasan al paso 10                |
| investment_redemption_pct            | outflow_x_contact_gap                  |      0.626 |     0.230 |  0.123 |  0.161 |                      0.012 | outflow_x_contact_gap                  | información incremental: ambas pasan al paso 10                |
| deposit_balance_change_pct_90d       | net_external_flow_pct_90d              |      0.625 |     0.592 |  0.138 |  0.166 |                      0.002 | net_external_flow_pct_90d              | redundantes: queda la de mayor IV                              |
| salary_deposit_stopped_flag          | pension_deposit_stopped_flag           |      0.621 |     0.621 |  0.122 |  0.050 |                      0.006 | salary_deposit_stopped_flag            | información incremental: ambas pasan al paso 10                |
| has_investments                      | aum_share                              |      0.606 |     0.859 |  0.001 |  0.003 |                     -0.001 | aum_share                              | redundantes: queda la de mayor IV                              |
| has_investments                      | deposit_share                          |     -0.606 |    -0.859 |  0.001 |  0.003 |                     -0.001 | deposit_share                          | redundantes: queda la de mayor IV                              |
| investment_redemption_pct            | positions_liquidated_pct               |      0.484 |     0.643 |  0.123 |  0.083 |                     -0.001 | investment_redemption_pct              | redundantes: queda la de mayor IV                              |
| products_closed_180d                 | accounts_closed_90d                    |      0.469 |     0.714 |  0.217 |  0.061 |                     -0.001 | products_closed_180d                   | redundantes: queda la de mayor IV                              |
| cash_pct_of_portfolio_chg            | positions_liquidated_pct               |      0.426 |     0.618 |  0.090 |  0.083 |                      0.015 | cash_pct_of_portfolio_chg              | información incremental: ambas pasan al paso 10                |
| segment_uhnw                         | relationship_value                     |      0.397 |     0.620 |  0.002 |  0.005 |                     -0.012 | relationship_value                     | redundantes: queda la de mayor IV                              |
| investment_redemption_pct            | cash_pct_of_portfolio_chg              |      0.342 |     0.692 |  0.123 |  0.090 |                      0.003 | investment_redemption_pct              | redundantes: queda la de mayor IV                              |
| new_external_destinations_90d        | aum_vs_baseline_pct                    |     -0.292 |    -0.622 |  0.160 |  0.182 |                      0.006 | aum_vs_baseline_pct                    | información incremental: ambas pasan al paso 10                |
| transfer_to_competitor_pct_90d       | competitor_x_new_destinations          |      0.277 |     0.752 |  0.163 |  0.112 |                      0.002 | transfer_to_competitor_pct_90d         | redundantes: queda la de mayor IV                              |
| aum_outflow_90d                      | transfer_to_competitor_bank_amount_90d |      0.150 |     0.735 |  0.135 |  0.173 |                      0.016 | transfer_to_competitor_bank_amount_90d | información incremental: ambas pasan al paso 10                |
| external_transfer_pct_of_balance_60d | aum_vs_baseline_pct                    |     -0.149 |    -0.641 |  0.191 |  0.182 |                      0.014 | external_transfer_pct_of_balance_60d   | información incremental: ambas pasan al paso 10                |

- 58 pares [DATA]; 42 redundantes y 16 con información incremental.
- El par RV–AUM (G0-a) aparece por construcción: RV = AUM + depósitos.

### VIF (top 12, rangos normalizados) [DATA]
| variable                      |   VIF (rangos normalizados) |
|:------------------------------|----------------------------:|
| relationship_value            |    1,000,799,917,193,443.50 |
| aum_outflow_pct_90d_peer      |    1,000,799,917,193,443.50 |
| aum_outflow_pct_90d           |    1,000,799,917,193,443.50 |
| log_rv                        |    1,000,799,917,193,443.50 |
| aum_share                     |                  138,788.76 |
| deposit_share                 |                  138,576.26 |
| n_streams_eligible            |                    1,763.01 |
| net_deposit_flow_pct_90d      |                    1,537.99 |
| net_deposit_flow_pct_90d_peer |                    1,529.68 |
| has_payroll_stream            |                    1,203.44 |
| has_pension_stream            |                    1,099.88 |
| has_linked_business           |                      887.70 |

### PCA por bloque (diagnóstico) [DATA]
| bloque          |   variables |   PC1 % |   PC1+PC2 % |   componentes para 80% |   autovalores > 1 |
|:----------------|------------:|--------:|------------:|-----------------------:|------------------:|
| depósitos       |           5 |    74.0 |        93.8 |                      2 |                 1 |
| salidas de AUM  |           7 |    60.0 |        82.6 |                      2 |                 2 |
| externalización |           9 |    38.3 |        53.8 |                      5 |                 3 |

- VIF infinito o muy alto por identidades exactas de construcción [DATA]: `log_rv` y `relationship_value` (mismo orden),
  `aum_share` + `deposit_share` = 1 (RV = AUM + depósitos), `n_streams_eligible` = suma de 3 `has_*`, variables base y su
  `_peer` dentro de celda. Se resuelve en el paso 10 (un representante por cluster de variables; VIF < 5 sobre WoE).
- PCA no entra en selección ni en modelo (SPEC D.5).

## Tests
- `tests/test_step08.py` (ver pytest).

## Decisiones y preguntas abiertas
- D8.1 en `reports/decision_log.md`.
