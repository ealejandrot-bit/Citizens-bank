| columna                                | dtype   |   n_missing |   % missing |   n_únicos |              mín |            máx |
|:---------------------------------------|:--------|------------:|------------:|-----------:|-----------------:|---------------:|
| household_id                           | str     |           0 |        0    |      20000 |                  |                |
| snapshot_date                          | str     |           0 |        0    |          1 |                  |                |
| segment                                | str     |           0 |        0    |          2 |                  |                |
| relationship_value                     | float64 |           0 |        0    |      19999 |      1.00006e+06 |    9.03973e+08 |
| deposit_balance                        | float64 |           0 |        0    |      19998 |   1358.28        |    4.19924e+08 |
| aum                                    | float64 |        2870 |       14.35 |      17130 | 113383           |    7.73011e+08 |
| has_investments                        | bool    |           0 |        0    |          2 |                  |                |
| has_advisory                           | bool    |           0 |        0    |          2 |                  |                |
| has_linked_business                    | bool    |           0 |        0    |          2 |                  |                |
| has_trust                              | bool    |           0 |        0    |          2 |                  |                |
| has_credit_anchor                      | bool    |           0 |        0    |          2 |                  |                |
| has_payroll_stream                     | bool    |           0 |        0    |          2 |                  |                |
| has_pension_stream                     | bool    |           0 |        0    |          2 |                  |                |
| has_dividend_stream                    | bool    |           0 |        0    |          2 |                  |                |
| age_primary                            | int64   |           0 |        0    |         67 |     28           |   94           |
| tenure_years                           | float64 |           0 |        0    |       2674 |      0.01        |   50           |
| history_months                         | int64   |           0 |        0    |         25 |      0           |   24           |
| recurring_income_monthly               | float64 |           0 |        0    |      18639 |      0           |    2.00023e+06 |
| aum_outflow_pct_90d                    | float64 |        2897 |       14.49 |       7477 |      0           |    7.68412     |
| deposit_balance_change_pct_90d         | float64 |         110 |        0.55 |      19887 |     -0.97554     |    1.83937     |
| salary_deposit_stopped_flag            | float64 |        9460 |       47.3  |          2 |      0           |    1           |
| recurring_deposit_stopped_flag         | float64 |        1493 |        7.46 |          2 |      0           |    1           |
| recurring_deposit_change_pct           | float64 |        1479 |        7.4  |      17705 |     -1           |    3.56075     |
| net_deposit_flow_pct_90d               | float64 |          57 |        0.29 |      19942 |     -6.94222     |    1.71008     |
| external_transfer_pct_of_balance_60d   | float64 |          16 |        0.08 |      19875 |      0           |   30.2216      |
| new_external_destinations_90d          | float64 |         696 |        3.48 |          4 |      0           |    3           |
| investment_redemption_pct              | float64 |        2897 |       14.49 |       8983 |      0           |    1.66927     |
| products_closed_180d                   | float64 |         106 |        0.53 |          7 |      0           |    6           |
| banker_change_6m_flag                  | float64 |         106 |        0.53 |          2 |      0           |    1           |
| contact_gap_ratio                      | float64 |           0 |        0    |        349 |     -0           |   12.1667      |
| client_reply_rate                      | float64 |        9598 |       47.99 |        194 |      0           |    1           |
| complaint_escalated_flag               | int64   |           0 |        0    |          2 |      0           |    1           |
| complaint_age_days                     | int64   |           0 |        0    |        211 |      0           |  364           |
| multi_signal_flag                      | int64   |           0 |        0    |          2 |      0           |    1           |
| aum_vs_baseline_pct                    | float64 |        3001 |       15    |      15192 |     -0.944906    |    0.350829    |
| deposit_balance_vs_6m_avg_pct          | float64 |         158 |        0.79 |      19837 |     -0.99669     |    4.53167     |
| pension_deposit_stopped_flag           | float64 |       13149 |       65.74 |          2 |      0           |    1           |
| business_payroll_stopped_flag          | float64 |       14777 |       73.89 |          2 |      0           |    1           |
| transfer_to_competitor_pct_90d         | float64 |          32 |        0.16 |      16763 |      0           |   18.5834      |
| external_transfer_acceleration         | float64 |          32 |        0.16 |      19891 |    -30.7082      |   22.5968      |
| net_external_flow_pct_90d              | float64 |          32 |        0.16 |      19963 |     -6.2912      |    3.97701     |
| external_destination_concentration     | float64 |          32 |        0.16 |      15833 |      0.171008    |    1           |
| outflow_vs_baseline_pct                | float64 |         153 |        0.76 |      19446 |     -1           | 6390.5         |
| fixed_income_maturity_not_reinvested   | float64 |       14782 |       73.91 |       1447 |      0           |    1           |
| cash_pct_of_portfolio_chg              | float64 |        3001 |       15    |      16976 |     -0.0547819   |    0.812934    |
| return_vs_benchmark                    | float64 |        8199 |       41    |      11797 |     -0.15896     |    0.155698    |
| accounts_closed_90d                    | float64 |          32 |        0.16 |         13 |      0           |   12           |
| share_of_wallet                        | float64 |           0 |        0    |      18816 |      7.702e-05   |    1           |
| share_of_wallet_change                 | float64 |         153 |        0.76 |      19045 |     -0.972558    |    0.894517    |
| trustee_change_flag                    | float64 |       13626 |       68.13 |          2 |      0           |    1           |
| repeat_complaint_flag                  | int64   |           0 |        0    |          2 |      0           |    1           |
| positions_liquidated_pct               | float64 |        2918 |       14.59 |       2193 |      0           |    0.426655    |
| meetings_cancelled_by_client           | float64 |       12145 |       60.72 |         10 |      0           |    9           |
| relationship_dissatisfaction_flag      | float64 |       14089 |       70.45 |          2 |      0           |    1           |
| bureau_new_mortgage_elsewhere          | float64 |        1008 |        5.04 |          2 |      0           |    1           |
| multi_signal_count                     | int64   |           0 |        0    |          8 |      0           |    7           |
| aum_outflow_90d                        | float64 |        2897 |       14.49 |       7483 |      0           |    4.63748e+08 |
| transfer_to_competitor_bank_amount_90d | float64 |          32 |        0.16 |      16797 |      0           |    5.85608e+08 |
| churn_excluded                         | bool    |           0 |        0    |          2 |                  |                |
| hard_churn_6m                          | float64 |         123 |        0.62 |          2 |      0           |    1           |
| soft_churn_3m                          | float64 |         123 |        0.62 |          2 |      0           |    1           |
| value_lost_6m                          | float64 |         123 |        0.62 |       2957 |      0           |    6.60692e+08 |
