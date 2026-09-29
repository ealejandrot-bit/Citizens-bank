| variable                               | regla                                         | tipo              |   n |   % no nulos |
|:---------------------------------------|:----------------------------------------------|:------------------|----:|-------------:|
| share_of_wallet                        | [0, 1]                                        | imposible         |   0 |        0     |
| client_reply_rate                      | [0, 1]                                        | imposible         |   0 |        0     |
| positions_liquidated_pct               | [0, 1]                                        | imposible         |   0 |        0     |
| fixed_income_maturity_not_reinvested   | [0, 1]                                        | imposible         |   0 |        0     |
| external_destination_concentration     | [0, 1]                                        | imposible         |   0 |        0     |
| deposit_balance_change_pct_90d         | [-1, inf]                                     | imposible         |   0 |        0     |
| deposit_balance_vs_6m_avg_pct          | [-1, inf]                                     | imposible         |   0 |        0     |
| aum_vs_baseline_pct                    | [-1, inf]                                     | imposible         |   0 |        0     |
| recurring_deposit_change_pct           | [-1, inf]                                     | imposible         |   0 |        0     |
| outflow_vs_baseline_pct                | [-1, inf]                                     | imposible         |   0 |        0     |
| relationship_value                     | [0, inf]                                      | imposible         |   0 |        0     |
| deposit_balance                        | [0, inf]                                      | imposible         |   0 |        0     |
| aum                                    | [0, inf]                                      | imposible         |   0 |        0     |
| recurring_income_monthly               | [0, inf]                                      | imposible         |   0 |        0     |
| aum_outflow_90d                        | [0, inf]                                      | imposible         |   0 |        0     |
| aum_outflow_pct_90d                    | [0, inf]                                      | imposible         |   0 |        0     |
| investment_redemption_pct              | [0, inf]                                      | imposible         |   0 |        0     |
| external_transfer_pct_of_balance_60d   | [0, inf]                                      | imposible         |   0 |        0     |
| transfer_to_competitor_bank_amount_90d | [0, inf]                                      | imposible         |   0 |        0     |
| transfer_to_competitor_pct_90d         | [0, inf]                                      | imposible         |   0 |        0     |
| contact_gap_ratio                      | [0, inf]                                      | imposible         |   0 |        0     |
| value_lost_6m                          | [0, inf]                                      | imposible         |   0 |        0     |
| tenure_years                           | [0, inf]                                      | imposible         |   0 |        0     |
| new_external_destinations_90d          | [0, inf]                                      | imposible         |   0 |        0     |
| products_closed_180d                   | [0, inf]                                      | imposible         |   0 |        0     |
| accounts_closed_90d                    | [0, inf]                                      | imposible         |   0 |        0     |
| meetings_cancelled_by_client           | [0, inf]                                      | imposible         |   0 |        0     |
| multi_signal_count                     | [0, inf]                                      | imposible         |   0 |        0     |
| complaint_age_days                     | [0, inf]                                      | imposible         |   0 |        0     |
| history_months                         | [0, 24]                                       | imposible         |   0 |        0     |
| share_of_wallet_change                 | [-1, 1]                                       | imposible         |   0 |        0     |
| cash_pct_of_portfolio_chg              | [-1, 1]                                       | imposible         |   0 |        0     |
| return_vs_benchmark                    | [-1, 1]                                       | imposible         |   0 |        0     |
| age_primary                            | [18, 110]                                     | imposible         |   0 |        0     |
| salary_deposit_stopped_flag            | {0, 1}                                        | imposible         |   0 |        0     |
| recurring_deposit_stopped_flag         | {0, 1}                                        | imposible         |   0 |        0     |
| banker_change_6m_flag                  | {0, 1}                                        | imposible         |   0 |        0     |
| complaint_escalated_flag               | {0, 1}                                        | imposible         |   0 |        0     |
| multi_signal_flag                      | {0, 1}                                        | imposible         |   0 |        0     |
| pension_deposit_stopped_flag           | {0, 1}                                        | imposible         |   0 |        0     |
| business_payroll_stopped_flag          | {0, 1}                                        | imposible         |   0 |        0     |
| trustee_change_flag                    | {0, 1}                                        | imposible         |   0 |        0     |
| repeat_complaint_flag                  | {0, 1}                                        | imposible         |   0 |        0     |
| relationship_dissatisfaction_flag      | {0, 1}                                        | imposible         |   0 |        0     |
| bureau_new_mortgage_elsewhere          | {0, 1}                                        | imposible         |   0 |        0     |
| hard_churn_6m                          | {0, 1}                                        | imposible         |   0 |        0     |
| soft_churn_3m                          | {0, 1}                                        | imposible         |   0 |        0     |
| new_external_destinations_90d          | entero                                        | imposible         |   0 |        0     |
| products_closed_180d                   | entero                                        | imposible         |   0 |        0     |
| accounts_closed_90d                    | entero                                        | imposible         |   0 |        0     |
| meetings_cancelled_by_client           | entero                                        | imposible         |   0 |        0     |
| multi_signal_count                     | entero                                        | imposible         |   0 |        0     |
| complaint_age_days                     | entero                                        | imposible         |   0 |        0     |
| history_months                         | entero                                        | imposible         |   0 |        0     |
| aum_outflow_pct_90d                    | salida 90d > 100% del AUM promedio            | extremo plausible | 168 |        0.982 |
| investment_redemption_pct              | redención > 100% del AUM promedio             | extremo plausible |  22 |        0.129 |
| external_transfer_pct_of_balance_60d   | transferencias 60d > 100% del saldo promedio  | extremo plausible | 628 |        3.143 |
| transfer_to_competitor_pct_90d         | a competidores > 100% del saldo promedio      | extremo plausible | 373 |        1.868 |
| net_deposit_flow_pct_90d               | salida neta > 100% del saldo promedio         | extremo plausible | 479 |        2.402 |
| net_external_flow_pct_90d              | salida externa neta > 100% del saldo promedio | extremo plausible | 188 |        0.942 |
| outflow_vs_baseline_pct                | salidas > 11× la base                         | extremo plausible | 428 |        2.156 |
| contact_gap_ratio                      | > 6 cadencias sin contacto                    | extremo plausible |   1 |        0.005 |
| complaint_age_days                     | queja abierta > 180 días                      | extremo plausible |  67 |        0.335 |
| age_primary                            | titular < 30 años                             | extremo plausible |  30 |        0.15  |
| contact_gap_ratio                      | cero con signo negativo (−0.0)                | cosmético         | 561 |        2.805 |
