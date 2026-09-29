# Paso 2 · Selección de variables

## Objetivo
- Quedarse con las variables que aportan de forma estable al ML y decidir si entran los compuestos (I-2).

## Método
- Permutation importance OOF en los 25 folds (GBM base monotónico, prof. 3); pasa si ΔPR-AUC > 0 en ≥ 80% de los folds.
- Eliminación hacia atrás (menor importancia primero): se acepta quitar si la PR-AUC CV no cae más de 1 error estándar
  de la diferencia pareada (D2.1); mínimo 12 variables.
- Variante sin compuestos elegida si la diferencia de PR-AUC < 1 sd de los folds [DEF-default I-2].

## Código
- `src/step02_selection.py` · `tests/test_step02.py` · `step02_permutation.csv`, `step02_backward.csv`, `step02_variants.csv`.

## Resultados

### Variantes [DATA]
| variante       |   variables |   PR-AUC CV media |   sd folds | elegida   | variables seleccionadas                                                                                                                                                                                                                                                                                                |
|:---------------|------------:|------------------:|-----------:|:----------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| con compuestos |          12 |            0.3584 |     0.0198 | False     | banker_change_6m_flag, client_reply_rate, share_of_wallet, repeat_complaint_flag, contact_gap_ratio, recurring_deposit_change_pct, cash_pct_of_portfolio_chg, complaint_age_days, meetings_cancelled_by_client, complaint_escalated_flag, fixed_income_maturity_not_reinvested, transfer_to_competitor_bank_amount_90d |
| sin compuestos |          12 |            0.3584 |     0.0195 | True      | banker_change_6m_flag, client_reply_rate, share_of_wallet, transfer_to_competitor_pct_90d, repeat_complaint_flag, contact_gap_ratio, recurring_deposit_change_pct, return_vs_benchmark, cash_pct_of_portfolio_chg, complaint_age_days, meetings_cancelled_by_client, positions_liquidated_pct                          |

- Diferencia con − sin compuestos: +0.0000 vs 1 sd = 0.0198 ⟹ **sin compuestos** [DATA].

### Eliminación hacia atrás [DATA]
| variante       |   paso | quita                                  |   variables |   PR-AUC CV |   Δ vs actual |     1-SE | acepta   |
|:---------------|-------:|:---------------------------------------|------------:|------------:|--------------:|---------:|:---------|
| con compuestos |      0 | —                                      |          18 |      0.3590 |        0.0000 | nan      | True     |
| con compuestos |      1 | transfer_to_competitor_bank_amount_90d |          17 |      0.3585 |       -0.0005 |   0.0004 | False    |
| con compuestos |      2 | outflow_x_contact_gap                  |          17 |      0.3590 |        0.0001 |   0.0006 | True     |
| con compuestos |      3 | positions_liquidated_pct               |          16 |      0.3589 |       -0.0001 |   0.0005 | True     |
| con compuestos |      4 | multi_signal_flag                      |          15 |      0.3586 |       -0.0003 |   0.0003 | True     |
| con compuestos |      5 | fixed_income_maturity_not_reinvested   |          14 |      0.3572 |       -0.0014 |   0.0005 | False    |
| con compuestos |      6 | complaint_escalated_flag               |          14 |      0.3581 |       -0.0005 |   0.0005 | False    |
| con compuestos |      7 | meetings_cancelled_by_client           |          14 |      0.3571 |       -0.0015 |   0.0008 | False    |
| con compuestos |      8 | complaint_age_days                     |          14 |      0.3577 |       -0.0009 |   0.0007 | False    |
| con compuestos |      9 | return_vs_benchmark                    |          14 |      0.3590 |        0.0004 |   0.0006 | True     |
| con compuestos |     10 | cash_pct_of_portfolio_chg              |          13 |      0.3579 |       -0.0010 |   0.0009 | False    |
| con compuestos |     11 | transfer_to_competitor_pct_90d         |          13 |      0.3586 |       -0.0003 |   0.0005 | True     |
| con compuestos |     12 | recurring_deposit_change_pct           |          12 |      0.3555 |       -0.0032 |   0.0009 | False    |
| con compuestos |     13 | contact_gap_ratio                      |          12 |      0.3567 |       -0.0020 |   0.0008 | False    |
| con compuestos |     14 | repeat_complaint_flag                  |          12 |      0.3559 |       -0.0028 |   0.0006 | False    |
| con compuestos |     15 | share_of_wallet                        |          12 |      0.3577 |       -0.0009 |   0.0007 | False    |
| con compuestos |     16 | multi_signal_count                     |          12 |      0.3584 |       -0.0002 |   0.0006 | True     |
| sin compuestos |      0 | —                                      |          14 |      0.3588 |        0.0000 | nan      | True     |
| sin compuestos |      1 | fixed_income_maturity_not_reinvested   |          13 |      0.3585 |       -0.0002 |   0.0005 | True     |
| sin compuestos |      2 | positions_liquidated_pct               |          12 |      0.3578 |       -0.0007 |   0.0006 | False    |
| sin compuestos |      3 | complaint_escalated_flag               |          12 |      0.3584 |       -0.0001 |   0.0004 | True     |

### Permutation importance [DATA]
| variante       | variable                                          |   ΔPR-AUC medio |   % folds > 0 | pasa (≥ 80% folds)   |
|:---------------|:--------------------------------------------------|----------------:|--------------:|:---------------------|
| con compuestos | banker_change_6m_flag                             |          0.0343 |      100.0000 | True                 |
| con compuestos | client_reply_rate                                 |          0.0135 |      100.0000 | True                 |
| con compuestos | multi_signal_count                                |          0.0067 |       96.0000 | True                 |
| con compuestos | share_of_wallet                                   |          0.0057 |      100.0000 | True                 |
| con compuestos | repeat_complaint_flag                             |          0.0048 |       96.0000 | True                 |
| con compuestos | contact_gap_ratio                                 |          0.0044 |       92.0000 | True                 |
| con compuestos | recurring_deposit_change_pct                      |          0.0032 |       84.0000 | True                 |
| con compuestos | transfer_to_competitor_pct_90d                    |          0.0032 |       96.0000 | True                 |
| con compuestos | cash_pct_of_portfolio_chg                         |          0.0027 |       88.0000 | True                 |
| con compuestos | return_vs_benchmark                               |          0.0025 |       80.0000 | True                 |
| con compuestos | complaint_age_days                                |          0.0023 |       80.0000 | True                 |
| con compuestos | meetings_cancelled_by_client                      |          0.0022 |       84.0000 | True                 |
| con compuestos | streams_stopped_count                             |          0.0020 |       76.0000 | False                |
| con compuestos | complaint_escalated_flag                          |          0.0016 |       84.0000 | True                 |
| con compuestos | tenure_years                                      |          0.0015 |       72.0000 | False                |
| con compuestos | fixed_income_maturity_not_reinvested              |          0.0014 |       80.0000 | True                 |
| con compuestos | multi_signal_flag                                 |          0.0012 |       88.0000 | True                 |
| con compuestos | positions_liquidated_pct                          |          0.0012 |       88.0000 | True                 |
| con compuestos | outflow_x_contact_gap                             |          0.0011 |       80.0000 | True                 |
| con compuestos | external_transfer_pct_of_balance_60d              |          0.0009 |       68.0000 | False                |
| con compuestos | transfer_to_competitor_bank_amount_90d            |          0.0007 |       84.0000 | True                 |
| con compuestos | business_payroll_stopped_flag                     |          0.0003 |       72.0000 | False                |
| con compuestos | net_external_flow_pct_90d                         |          0.0003 |       76.0000 | False                |
| con compuestos | outflow_vs_baseline_pct                           |          0.0002 |       52.0000 | False                |
| con compuestos | investment_redemption_pct                         |          0.0002 |       60.0000 | False                |
| con compuestos | ind_sin_dato_client_reply_rate                    |          0.0002 |       52.0000 | False                |
| con compuestos | deposit_balance_vs_6m_avg_pct                     |          0.0002 |       52.0000 | False                |
| con compuestos | external_destination_concentration                |          0.0002 |       68.0000 | False                |
| con compuestos | aum                                               |          0.0001 |       64.0000 | False                |
| con compuestos | deposit_balance_change_pct_90d                    |          0.0001 |       60.0000 | False                |
| con compuestos | has_linked_business                               |          0.0001 |       60.0000 | False                |
| con compuestos | ind_sin_dato_relationship_dissatisfaction_flag    |          0.0001 |       52.0000 | False                |
| con compuestos | pension_deposit_stopped_flag                      |          0.0000 |       60.0000 | False                |
| con compuestos | has_pension_stream                                |          0.0000 |       44.0000 | False                |
| con compuestos | has_trust                                         |          0.0000 |       44.0000 | False                |
| con compuestos | has_investments                                   |          0.0000 |        0.0000 | False                |
| con compuestos | accounts_closed_90d                               |         -0.0000 |       28.0000 | False                |
| con compuestos | new_external_destinations_90d                     |         -0.0000 |       40.0000 | False                |
| con compuestos | has_credit_anchor                                 |         -0.0000 |       60.0000 | False                |
| con compuestos | ind_sin_dato_fixed_income_maturity_not_reinvested |         -0.0000 |       48.0000 | False                |
| con compuestos | segment_uhnw                                      |         -0.0000 |       16.0000 | False                |
| con compuestos | has_advisory                                      |         -0.0000 |       24.0000 | False                |
| con compuestos | n_streams_eligible                                |         -0.0000 |       32.0000 | False                |
| con compuestos | external_transfer_acceleration                    |         -0.0000 |       68.0000 | False                |
| con compuestos | history_months                                    |         -0.0001 |       44.0000 | False                |
| con compuestos | ind_sin_dato_meetings_cancelled_by_client         |         -0.0001 |       48.0000 | False                |
| con compuestos | has_dividend_stream                               |         -0.0001 |       36.0000 | False                |
| con compuestos | trustee_change_flag                               |         -0.0001 |       44.0000 | False                |
| con compuestos | aum_outflow_pct_90d                               |         -0.0001 |       40.0000 | False                |
| con compuestos | recurring_deposit_stopped_flag                    |         -0.0001 |       28.0000 | False                |
| con compuestos | cluster                                           |         -0.0001 |       32.0000 | False                |
| con compuestos | recurring_income_monthly                          |         -0.0001 |       64.0000 | False                |
| con compuestos | has_payroll_stream                                |         -0.0001 |       48.0000 | False                |
| con compuestos | products_closed_180d                              |         -0.0002 |       40.0000 | False                |
| con compuestos | net_deposit_flow_pct_90d                          |         -0.0002 |       48.0000 | False                |
| con compuestos | relationship_dissatisfaction_flag                 |         -0.0002 |       36.0000 | False                |
| con compuestos | salary_deposit_stopped_flag                       |         -0.0002 |       36.0000 | False                |
| con compuestos | share_of_wallet_change                            |         -0.0003 |       48.0000 | False                |
| con compuestos | n_products_held                                   |         -0.0003 |       40.0000 | False                |
| con compuestos | aum_vs_baseline_pct                               |         -0.0005 |       36.0000 | False                |
| con compuestos | deposit_balance                                   |         -0.0008 |       44.0000 | False                |
| con compuestos | aum_share                                         |         -0.0015 |       20.0000 | False                |
| sin compuestos | banker_change_6m_flag                             |          0.0416 |      100.0000 | True                 |
| sin compuestos | client_reply_rate                                 |          0.0132 |      100.0000 | True                 |
| sin compuestos | share_of_wallet                                   |          0.0083 |      100.0000 | True                 |
| sin compuestos | transfer_to_competitor_pct_90d                    |          0.0061 |      100.0000 | True                 |
| sin compuestos | repeat_complaint_flag                             |          0.0057 |      100.0000 | True                 |
| sin compuestos | contact_gap_ratio                                 |          0.0049 |       92.0000 | True                 |
| sin compuestos | recurring_deposit_change_pct                      |          0.0048 |       88.0000 | True                 |
| sin compuestos | return_vs_benchmark                               |          0.0036 |       88.0000 | True                 |
| sin compuestos | cash_pct_of_portfolio_chg                         |          0.0033 |       84.0000 | True                 |
| sin compuestos | complaint_age_days                                |          0.0027 |       92.0000 | True                 |
| sin compuestos | meetings_cancelled_by_client                      |          0.0025 |       88.0000 | True                 |
| sin compuestos | streams_stopped_count                             |          0.0025 |       76.0000 | False                |
| sin compuestos | complaint_escalated_flag                          |          0.0023 |      100.0000 | True                 |
| sin compuestos | tenure_years                                      |          0.0018 |       72.0000 | False                |
| sin compuestos | positions_liquidated_pct                          |          0.0012 |       84.0000 | True                 |
| sin compuestos | fixed_income_maturity_not_reinvested              |          0.0012 |       84.0000 | True                 |
| sin compuestos | external_transfer_pct_of_balance_60d              |          0.0009 |       68.0000 | False                |
| sin compuestos | outflow_x_contact_gap                             |          0.0007 |       76.0000 | False                |
| sin compuestos | deposit_balance_vs_6m_avg_pct                     |          0.0004 |       76.0000 | False                |
| sin compuestos | recurring_income_monthly                          |          0.0004 |       52.0000 | False                |
| sin compuestos | transfer_to_competitor_bank_amount_90d            |          0.0004 |       72.0000 | False                |
| sin compuestos | business_payroll_stopped_flag                     |          0.0003 |       68.0000 | False                |
| sin compuestos | external_transfer_acceleration                    |          0.0003 |       60.0000 | False                |
| sin compuestos | net_external_flow_pct_90d                         |          0.0003 |       68.0000 | False                |
| sin compuestos | has_credit_anchor                                 |          0.0002 |       68.0000 | False                |
| sin compuestos | investment_redemption_pct                         |          0.0002 |       64.0000 | False                |
| sin compuestos | aum                                               |          0.0001 |       60.0000 | False                |
| sin compuestos | deposit_balance_change_pct_90d                    |          0.0001 |       60.0000 | False                |
| sin compuestos | ind_sin_dato_client_reply_rate                    |          0.0001 |       60.0000 | False                |
| sin compuestos | external_destination_concentration                |          0.0001 |       56.0000 | False                |
| sin compuestos | recurring_deposit_stopped_flag                    |          0.0001 |       56.0000 | False                |
| sin compuestos | has_advisory                                      |          0.0000 |       40.0000 | False                |
| sin compuestos | has_linked_business                               |          0.0000 |       52.0000 | False                |
| sin compuestos | new_external_destinations_90d                     |          0.0000 |       28.0000 | False                |
| sin compuestos | has_pension_stream                                |          0.0000 |       24.0000 | False                |
| sin compuestos | has_investments                                   |          0.0000 |        0.0000 | False                |
| sin compuestos | has_dividend_stream                               |         -0.0000 |       40.0000 | False                |
| sin compuestos | accounts_closed_90d                               |         -0.0000 |       48.0000 | False                |
| sin compuestos | products_closed_180d                              |         -0.0000 |       56.0000 | False                |
| sin compuestos | history_months                                    |         -0.0000 |       48.0000 | False                |
| sin compuestos | aum_outflow_pct_90d                               |         -0.0000 |       44.0000 | False                |
| sin compuestos | ind_sin_dato_relationship_dissatisfaction_flag    |         -0.0000 |       28.0000 | False                |
| sin compuestos | n_products_held                                   |         -0.0000 |       52.0000 | False                |
| sin compuestos | segment_uhnw                                      |         -0.0000 |       20.0000 | False                |
| sin compuestos | has_trust                                         |         -0.0001 |       36.0000 | False                |
| sin compuestos | outflow_vs_baseline_pct                           |         -0.0001 |       44.0000 | False                |
| sin compuestos | ind_sin_dato_fixed_income_maturity_not_reinvested |         -0.0001 |       24.0000 | False                |
| sin compuestos | n_streams_eligible                                |         -0.0001 |       56.0000 | False                |
| sin compuestos | pension_deposit_stopped_flag                      |         -0.0001 |       48.0000 | False                |
| sin compuestos | salary_deposit_stopped_flag                       |         -0.0001 |       40.0000 | False                |
| sin compuestos | ind_sin_dato_meetings_cancelled_by_client         |         -0.0001 |       36.0000 | False                |
| sin compuestos | cluster                                           |         -0.0001 |       36.0000 | False                |
| sin compuestos | net_deposit_flow_pct_90d                          |         -0.0001 |       40.0000 | False                |
| sin compuestos | trustee_change_flag                               |         -0.0001 |       40.0000 | False                |
| sin compuestos | has_payroll_stream                                |         -0.0002 |       28.0000 | False                |
| sin compuestos | share_of_wallet_change                            |         -0.0002 |       56.0000 | False                |
| sin compuestos | relationship_dissatisfaction_flag                 |         -0.0003 |       36.0000 | False                |
| sin compuestos | deposit_balance                                   |         -0.0004 |       40.0000 | False                |
| sin compuestos | aum_vs_baseline_pct                               |         -0.0009 |       36.0000 | False                |
| sin compuestos | aum_share                                         |         -0.0010 |       28.0000 | False                |

## Tests
- `tests/test_step02.py` (ver pytest).

## Decisiones y preguntas abiertas
- D2.1–D2.2 en `reports/decision_log.md`.
