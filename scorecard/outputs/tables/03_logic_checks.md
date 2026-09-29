| control                                                              |   n inconsistentes |   % hogares | nota                                                            |
|:---------------------------------------------------------------------|-------------------:|------------:|:----------------------------------------------------------------|
| relationship_value = aum + deposit_balance (±$1)                     |                  0 |       0     |                                                                 |
| segment = UHNW ⇔ relationship_value ≥ $30M                           |                  0 |       0     |                                                                 |
| HNW: relationship_value ≥ $1M                                        |                  0 |       0     |                                                                 |
| history_months = min(24, ⌊tenure_years·12⌋)                          |                 61 |       0.305 | diferencias de ±1 mes por redondeo de antigüedad; ver tabla     |
| history_months ≤ tenure_years·12 + 1                                 |                  0 |       0     |                                                                 |
| history_months = 0 (sin historia transaccional)                      |                  5 |       0.025 | hogares recién abiertos                                         |
| tenure_years ≤ age_primary − 18                                      |                  0 |       0     |                                                                 |
| SOW hace 6m = SOW − cambio ∈ [0, 1]                                  |                  0 |       0     |                                                                 |
| aum_outflow_90d > 0 ⇔ aum_outflow_pct_90d > 0                        |                  0 |       0     |                                                                 |
| transfer_to_competitor_amount > 0 ⇔ pct > 0                          |                  0 |       0     |                                                                 |
| salary_deposit_stopped_flag = 1 ⇒ recurring_deposit_stopped_flag = 1 |                 11 |       0.055 | la nómina puede ser < 10% del ingreso recurrente (umbral de #4) |
| pension_deposit_stopped_flag con valor sin has_pension_stream        |                134 |       0.67  | siempre 0; patrón detectado sin flag de estructura (D0.4)       |
| salary_deposit_stopped_flag NaN con has_payroll_stream               |                232 |       1.16  | patrón de nómina no detectado por el algoritmo                  |
| value_lost_6m ≤ relationship_value                                   |                  0 |       0     |                                                                 |
| tenure_years = 0                                                     |                  0 |       0     | no hay; mínimo 0.01 años                                        |
