# Paso 4 · Explicabilidad

## Objetivo
- Verificar que el EBM (principal) y el XGBoost (segundo) se explican por hogar, respetan el signo de negocio y dan
  reason codes estables.

## Método
- EBM sin interacciones: logit = intercepto + Σ f_j(x_j) (exacto). XGBoost: TreeSHAP raw. ICE (500 hogares × 21
  puntos) y PDP por variable restringida; interacciones SHAP (2,000 hogares); ALE top 5 del EBM.
- Reason codes = top 3 contribuciones positivas; estabilidad en 200 réplicas bootstrap sobre 1,000 hogares.

## Código
- `src/step04_explain.py` · `tests/test_step04.py` · `step04_*.csv`, `outputs/model/step04_ebm.pkl`, `step04_xgb.json`.

## Resultados

### Aditividad e interacciones [DATA]
| modelo   |   error máx. aditividad |   % interacción global |
|:---------|------------------------:|-----------------------:|
| EBM      |                1.78e-15 |               0.00e+00 |
| XGBoost  |                9.46e-07 |               1.79e+01 |

### Importancia [DATA]
| variable                       |   |contribución| media EBM |   |φ| medio XGBoost | signo   |   % EBM |   % XGBoost |
|:-------------------------------|---------------------------:|--------------------:|:--------|--------:|------------:|
| client_reply_rate              |                      0.248 |               0.270 | −       |  20.885 |      23.893 |
| banker_change_6m_flag          |                      0.212 |               0.245 | +       |  17.895 |      21.740 |
| share_of_wallet                |                      0.129 |               0.112 | −       |  10.833 |       9.912 |
| contact_gap_ratio              |                      0.109 |               0.098 | +       |   9.197 |       8.668 |
| return_vs_benchmark            |                      0.097 |               0.080 | −       |   8.204 |       7.094 |
| transfer_to_competitor_pct_90d |                      0.094 |               0.115 | +       |   7.913 |      10.167 |
| recurring_deposit_change_pct   |                      0.071 |               0.032 | −       |   6.012 |       2.854 |
| positions_liquidated_pct       |                      0.059 |               0.023 | +       |   4.949 |       2.047 |
| repeat_complaint_flag          |                      0.051 |               0.041 | +       |   4.297 |       3.602 |
| cash_pct_of_portfolio_chg      |                      0.051 |               0.059 | +       |   4.257 |       5.188 |
| meetings_cancelled_by_client   |                      0.044 |               0.038 | +       |   3.718 |       3.346 |
| complaint_age_days             |                      0.022 |               0.017 | +       |   1.840 |       1.488 |

- Verificación: % EBM y % XGBoost suman 100.0% y 100.0% [DATA].

### Monotonía (violaciones) [DATA]
| variable                       |   restricción |   bins |   violaciones en f(x) EBM |   ICE EBM |   PDP EBM |   ICE XGBoost |   PDP XGBoost |
|:-------------------------------|--------------:|-------:|--------------------------:|----------:|----------:|--------------:|--------------:|
| banker_change_6m_flag          |             1 |      2 |                         0 |         0 |         0 |             0 |             0 |
| client_reply_rate              |            -1 |    159 |                         0 |         0 |         0 |             0 |             0 |
| share_of_wallet                |            -1 |   1022 |                         0 |         0 |         0 |             0 |             0 |
| transfer_to_competitor_pct_90d |             1 |   1022 |                         0 |         0 |         0 |             0 |             0 |
| repeat_complaint_flag          |             1 |      2 |                         0 |         0 |         0 |             0 |             0 |
| contact_gap_ratio              |             1 |    293 |                         0 |         0 |         0 |             0 |             0 |
| recurring_deposit_change_pct   |            -1 |   1022 |                         0 |         0 |         0 |             0 |             0 |
| return_vs_benchmark            |            -1 |   1022 |                         0 |         0 |         0 |             0 |             0 |
| cash_pct_of_portfolio_chg      |             1 |   1022 |                         0 |         0 |         0 |             0 |             0 |
| complaint_age_days             |             1 |    121 |                         0 |         0 |         0 |             0 |             0 |
| meetings_cancelled_by_client   |             1 |      9 |                         0 |         0 |         0 |             0 |             0 |
| positions_liquidated_pct       |             1 |   1022 |                         0 |         0 |         0 |             0 |             0 |

### Funciones de forma del EBM
![EBM](../outputs/figs/step04_ebm_shapes.png)

- Tabla completa por bin: `step04_ebm_shape.csv` [DATA].

### Interacciones XGBoost [DATA]
| variable                       |   % interacción en |φ| XGBoost | > 20%   |
|:-------------------------------|-------------------------------:|:--------|
| recurring_deposit_change_pct   |                           41.7 | True    |
| share_of_wallet                |                           23.5 | True    |
| cash_pct_of_portfolio_chg      |                           23.1 | True    |
| meetings_cancelled_by_client   |                           20.8 | True    |
| positions_liquidated_pct       |                           17.5 | False   |
| transfer_to_competitor_pct_90d |                           17.1 | False   |
| complaint_age_days             |                           16.7 | False   |
| return_vs_benchmark            |                           16.0 | False   |
| banker_change_6m_flag          |                           15.8 | False   |
| contact_gap_ratio              |                           14.1 | False   |
| repeat_complaint_flag          |                           13.7 | False   |
| client_reply_rate              |                           13.5 | False   |

### Estabilidad de reason codes [DATA]
| modelo   |   réplicas |   hogares referencia |   con reason code |   acuerdo top 1 % |   acuerdo top 3 % |   % hogares con acuerdo top 1 ≥ 70% |   % variables con signo coherente |
|:---------|-----------:|---------------------:|------------------:|------------------:|------------------:|------------------------------------:|----------------------------------:|
| EBM      |        200 |                 1000 |               980 |              85.0 |              89.5 |                                78.0 |                             100.0 |
| XGBoost  |        200 |                 1000 |               953 |              81.5 |              82.5 |                                72.7 |                             100.0 |

## Tests
- `tests/test_step04.py` (ver pytest).

## Decisiones y preguntas abiertas
- D4.1 en `reports/decision_log.md`.
