# Paso 0 · Inventario [DATA-SINT]

- Fuente (solo lectura): `data/synthetic/client_pulse_synthetic.csv` · sha256 `44a1d18bfa4340d6…`
- Forma: 20,000 filas × 62 columnas · 20,000 `household_id` únicos · corte único 2025-12-31
- Entorno: python 3.11.15, pandas 3.0.6, numpy 2.4.6, scipy 1.17.1, sklearn 1.9.1, statsmodels 0.15.0, optbinning 1.0.0, matplotlib 3.11.2, openpyxl 3.1.5, lightgbm 4.7.0

## Verificación de hechos

| control                                                             | esperado                                                              | observado                                                                                                                                                                                                      | estado   |
|:--------------------------------------------------------------------|:----------------------------------------------------------------------|:---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|:---------|
| Filas                                                               | 20000                                                                 | 20000                                                                                                                                                                                                          | PASS     |
| household_id únicos                                                 | 20000                                                                 | 20000                                                                                                                                                                                                          | PASS     |
| Columnas                                                            | 62                                                                    | 62                                                                                                                                                                                                             | PASS     |
| snapshot_date único = 2025-12-31                                    | 2025-12-31                                                            | ['2025-12-31']                                                                                                                                                                                                 | PASS     |
| segment HNW / UHNW                                                  | HNW 18,897 / UHNW 1,103                                               | {'HNW': 18897, 'UHNW': 1103}                                                                                                                                                                                   | PASS     |
| churn_excluded = True                                               | 123                                                                   | 123                                                                                                                                                                                                            | PASS     |
| Excluidos con los 3 targets NaN                                     | todos NaN                                                             | 0                                                                                                                                                                                                              | PASS     |
| No excluidos con targets completos                                  | 0 NaN                                                                 | 0                                                                                                                                                                                                              | PASS     |
| hard_churn_6m eventos / base                                        | 1,200 / 19,877 (6.04%)                                                | 1,200 / 19,877 (6.04%)                                                                                                                                                                                         | PASS     |
| soft_churn_3m eventos                                               | 1,756 (8.83%)                                                         | 1,756 (8.83%)                                                                                                                                                                                                  | PASS     |
| hard y soft nunca coinciden                                         | 0                                                                     | 0                                                                                                                                                                                                              | PASS     |
| Unión hard ∪ soft                                                   | 2,956 (14.9%)                                                         | 2,956 (14.87%)                                                                                                                                                                                                 | PASS     |
| value_lost_6m > 0 solo con evento                                   | 0 hogares sin evento con valor perdido                                | 0                                                                                                                                                                                                              | PASS     |
| value_lost_6m > 0 en todo hogar con evento                          | 100%                                                                  | 100.0%                                                                                                                                                                                                         | PASS     |
| Eventos duros por segmento                                          | HNW 1,120 / UHNW 80                                                   | {'HNW': 1120, 'UHNW': 80}                                                                                                                                                                                      | PASS     |
| relationship_value mediana ≈ $4.8M                                  | $4.8M                                                                 | $4.84M                                                                                                                                                                                                         | PASS     |
| relationship_value p99 ≈ $92M                                       | $92M                                                                  | $92.5M                                                                                                                                                                                                         | PASS     |
| relationship_value máx ≈ $904M                                      | $904M                                                                 | $904.0M                                                                                                                                                                                                        | PASS     |
| Top 5% hogares = 37.5% del valor                                    | 37.5%                                                                 | 37.48%                                                                                                                                                                                                         | PASS     |
| aum: NaN cuando has_investments=False                               | 0 valores donde no aplica                                             | 0                                                                                                                                                                                                              | PASS     |
| aum_outflow_90d: NaN cuando has_investments=False                   | 0 valores donde no aplica                                             | 0                                                                                                                                                                                                              | PASS     |
| aum_outflow_pct_90d: NaN cuando has_investments=False               | 0 valores donde no aplica                                             | 0                                                                                                                                                                                                              | PASS     |
| investment_redemption_pct: NaN cuando has_investments=False         | 0 valores donde no aplica                                             | 0                                                                                                                                                                                                              | PASS     |
| positions_liquidated_pct: NaN cuando has_investments=False          | 0 valores donde no aplica                                             | 0                                                                                                                                                                                                              | PASS     |
| aum_vs_baseline_pct: NaN cuando has_investments=False               | 0 valores donde no aplica                                             | 0                                                                                                                                                                                                              | PASS     |
| cash_pct_of_portfolio_chg: NaN cuando has_investments=False         | 0 valores donde no aplica                                             | 0                                                                                                                                                                                                              | PASS     |
| pension_deposit_stopped_flag: NaN cuando has_pension_stream=False   | 0 valores donde no aplica                                             | 134                                                                                                                                                                                                            | WARN     |
| business_payroll_stopped_flag: NaN cuando has_linked_business=False | 0 valores donde no aplica                                             | 0                                                                                                                                                                                                              | PASS     |
| trustee_change_flag: NaN cuando has_trust=False                     | 0 valores donde no aplica                                             | 0                                                                                                                                                                                                              | PASS     |
| salary_deposit_stopped_flag: NaN cuando has_payroll_stream=False    | 0 valores donde no aplica                                             | 0                                                                                                                                                                                                              | PASS     |
| return_vs_benchmark: NaN cuando has_advisory=False                  | 0 valores donde no aplica                                             | 0                                                                                                                                                                                                              | PASS     |
| Bloque 40–74% missing                                               | 40–74%                                                                | salary_deposit_stopped_flag=47.3%, client_reply_rate=48.0%, return_vs_benchmark=41.0%, meetings_cancelled_by_client=60.7%, relationship_dissatisfaction_flag=70.4%, fixed_income_maturity_not_reinvested=73.9% | PASS     |
| history_months < 24                                                 | 1425                                                                  | 1425                                                                                                                                                                                                           | PASS     |
| aum_vs_baseline_pct ~24% missing en history<24                      | ~24%                                                                  | 23.7%                                                                                                                                                                                                          | PASS     |
| Compuestos presentes                                                | ['multi_signal_flag', 'multi_signal_count']                           | ['multi_signal_flag', 'multi_signal_count']                                                                                                                                                                    | PASS     |
| Outcomes presentes                                                  | ['hard_churn_6m', 'soft_churn_3m', 'value_lost_6m', 'churn_excluded'] | ['hard_churn_6m', 'soft_churn_3m', 'value_lost_6m', 'churn_excluded']                                                                                                                                          | PASS     |


## Mapa de missing estructural

| variable                             | condición                                                                   |   % missing |   NaN con has=False |   valor con has=False |   NaN extra con has=True |   NaN extra | history<24 |
|:-------------------------------------|:----------------------------------------------------------------------------|------------:|--------------------:|----------------------:|-------------------------:|-------------------------:|
| aum                                  | has_investments = False                                                     |       14.35 |                2870 |                     0 |                        0 |                        0 |
| aum_outflow_90d                      | has_investments = False                                                     |       14.49 |                2870 |                     0 |                       27 |                       27 |
| aum_outflow_pct_90d                  | has_investments = False                                                     |       14.49 |                2870 |                     0 |                       27 |                       27 |
| investment_redemption_pct            | has_investments = False                                                     |       14.49 |                2870 |                     0 |                       27 |                       27 |
| positions_liquidated_pct             | has_investments = False                                                     |       14.59 |                2870 |                     0 |                       48 |                       48 |
| aum_vs_baseline_pct                  | has_investments = False                                                     |       15    |                2870 |                     0 |                      131 |                      131 |
| cash_pct_of_portfolio_chg            | has_investments = False                                                     |       15    |                2870 |                     0 |                      131 |                      131 |
| pension_deposit_stopped_flag         | has_pension_stream = False                                                  |       65.74 |               13065 |                   134 |                       84 |                       23 |
| business_payroll_stopped_flag        | has_linked_business = False                                                 |       73.89 |               14713 |                     0 |                       64 |                       13 |
| trustee_change_flag                  | has_trust = False                                                           |       68.13 |               13626 |                     0 |                        0 |                        0 |
| salary_deposit_stopped_flag          | has_payroll_stream = False                                                  |       47.3  |                9228 |                     0 |                      232 |                       42 |
| return_vs_benchmark                  | has_advisory = False                                                        |       41    |                7948 |                     0 |                      251 |                      251 |
| client_reply_rate                    | operativa: < 3 contactos del banker en 90d                                  |       47.99 |                 nan |                   nan |                      nan |                      nan |
| meetings_cancelled_by_client         | operativa: el banker no registra el campo                                   |       60.72 |                 nan |                   nan |                      nan |                      nan |
| relationship_dissatisfaction_flag    | operativa: hogar fuera del piloto del Client Assistant                      |       70.45 |                 nan |                   nan |                      nan |                      nan |
| fixed_income_maturity_not_reinvested | operativa: sin vencimientos de renta fija en la ventana (o sin inversiones) |       73.91 |                 nan |                   nan |                      nan |                      nan |


## Missing en features vs baseline por historia

| variable                      |   % missing history<24 |   % missing history≥24 |
|:------------------------------|-----------------------:|-----------------------:|
| aum_vs_baseline_pct           |                   23.7 |                   14.3 |
| deposit_balance_vs_6m_avg_pct |                   10.7 |                    0   |
| outflow_vs_baseline_pct       |                   10.7 |                    0   |
| share_of_wallet_change        |                   10.7 |                    0   |


## Columnas

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

