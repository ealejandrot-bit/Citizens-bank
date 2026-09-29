# Paso 3 · Calidad de datos

## Objetivo
- Perfilar las variables, detectar imposibles e inconsistencias y clasificar las colas, sin eliminar ni recortar.

## Método
- Perfil sobre los 19,877 elegibles [DATA]; controles lógicos sobre las 20,000 filas.
- Outliers: error (rompe identidad o rango) / extraordinario (log₁₀ > Q3 + 3·IQR sobre valores > 0) / real. Sin capping (SPEC D.13).

## Código
- `src/step03_quality.py` · `tests/test_step03.py` · perfil completo en `outputs/tables/step03_profile.csv`.

## Resultados

### Controles lógicos [DATA]
| control                                                   |   n [DATA] | nota                        |
|:----------------------------------------------------------|-----------:|:----------------------------|
| household_id duplicados                                   |          0 |                             |
| filas duplicadas (sin id)                                 |          0 |                             |
| saldos negativos (RV, depósitos, AUM)                     |          0 |                             |
| montos negativos (salidas, transferencias, valor perdido) |          0 |                             |
| fracciones acotadas fuera de [0, 1]                       |          0 |                             |
| cambios % < −100%                                         |          0 |                             |
| conteos negativos o no enteros                            |          0 |                             |
| edad fuera de 18–110                                      |          0 |                             |
| tenure_years < 0                                          |          0 |                             |
| history_months fuera de 0–24                              |          0 |                             |
| history_months > tenure·12 + 1                            |          0 |                             |
| segment ≠ (RV ≥ $30M)                                     |          0 |                             |
| has_investments = False con aum no nulo                   |          0 |                             |
| has_investments = True con aum nulo                       |          0 |                             |
| |RV − (AUM + depósitos)| > $0.01                          |          0 | identidad al centavo (G0-a) |
| value_lost_6m > RV                                        |          0 |                             |

- Ningún imposible ni duplicado. RV = AUM + depósitos al centavo en las 20,000 filas (G0-a).

### Excepciones al missing estructural (elegibles) [DATA]
| variable                      | gatillo             |   valor sin gatillo |   NaN con gatillo |   de ellos con history < 24 |   % excepciones |
|:------------------------------|:--------------------|--------------------:|------------------:|----------------------------:|----------------:|
| aum                           | has_investments     |                   0 |                 0 |                           0 |            0.00 |
| aum_outflow_90d               | has_investments     |                   0 |                27 |                          27 |            0.14 |
| aum_outflow_pct_90d           | has_investments     |                   0 |                27 |                          27 |            0.14 |
| investment_redemption_pct     | has_investments     |                   0 |                27 |                          27 |            0.14 |
| positions_liquidated_pct      | has_investments     |                   0 |                48 |                          48 |            0.24 |
| cash_pct_of_portfolio_chg     | has_investments     |                   0 |               131 |                         131 |            0.66 |
| aum_vs_baseline_pct           | has_investments     |                   0 |               131 |                         131 |            0.66 |
| pension_deposit_stopped_flag  | has_pension_stream  |                 134 |                83 |                          23 |            1.09 |
| business_payroll_stopped_flag | has_linked_business |                   0 |                64 |                          13 |            0.32 |
| salary_deposit_stopped_flag   | has_payroll_stream  |                   0 |               230 |                          42 |            1.16 |
| trustee_change_flag           | has_trust           |                   0 |                 0 |                           0 |            0.00 |
| return_vs_benchmark           | has_advisory        |                   0 |               251 |                         251 |            1.26 |

- Todas ≤ 3% [DATA]. Valores sin gatillo solo en `pension_deposit_stopped_flag`; los NaN con gatillo presente son
  historia corta o patrón no detectado: se tratan como "sin dato", distinto de "no aplica" (paso 5).

### Colas [DATA]
| variable                               |   n > 0 |   p99 $M |   máx $M |   cerca extraordinario $M (log Q3 + 3·IQR) |   error |   extraordinario |   real |   % del total en extraordinarios |
|:---------------------------------------|--------:|---------:|---------:|-------------------------------------------:|--------:|-----------------:|-------:|---------------------------------:|
| relationship_value                     |   19877 |    92.36 |   903.97 |                                     709.69 |       0 |                2 |  19875 |                             0.79 |
| value_lost_6m                          |    2956 |    20.11 |   660.69 |                                     679.30 |       0 |                0 |   2956 |                             0.00 |
| aum_outflow_90d                        |    7444 |    12.08 |   463.75 |                                     465.39 |       0 |                0 |   7444 |                             0.00 |
| transfer_to_competitor_bank_amount_90d |   16721 |     8.08 |   585.61 |                                      27.52 |       0 |               63 |  16658 |                            52.26 |

Casos extraordinarios de mayor valor [DATA]:
| variable                               | household_id   | segment   |     valor |   relationship_value |   hard_churn_6m |   soft_churn_3m |
|:---------------------------------------|:---------------|:----------|----------:|---------------------:|----------------:|----------------:|
| relationship_value                     | HH008291       | UHNW      | 9.04e+08  |            9.04e+08  |               0 |               1 |
| relationship_value                     | HH016047       | UHNW      | 7.267e+08 |            7.267e+08 |               0 |               0 |
| transfer_to_competitor_bank_amount_90d | HH004766       | UHNW      | 5.856e+08 |            2.722e+08 |               0 |               1 |
| transfer_to_competitor_bank_amount_90d | HH000541       | UHNW      | 4.72e+08  |            8.751e+07 |               0 |               0 |
| transfer_to_competitor_bank_amount_90d | HH016272       | UHNW      | 3.051e+08 |            8.896e+07 |               0 |               0 |
| transfer_to_competitor_bank_amount_90d | HH014461       | HNW       | 2.039e+08 |            6.675e+06 |               0 |               0 |
| transfer_to_competitor_bank_amount_90d | HH014519       | HNW       | 1.784e+08 |            2.488e+07 |               0 |               1 |

- 0 errores: las colas son reales o extraordinarias y se conservan sin capping.

## Tests
- `tests/test_step03.py` en verde; suite completa `python -m pytest -q`: 30 passed.

## Decisiones y preguntas abiertas
- D3.1 en `reports/decision_log.md`.
