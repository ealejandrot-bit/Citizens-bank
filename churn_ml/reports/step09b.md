# Paso 9b · Comparativa con A-lite

## Objetivo
- Poner el scorecard ejecutivo A-lite (5 variables) en la misma comparación que el M1 y el EBM, sin re-ajustarlo.

## Método
- Scores de A-lite ya asignados en `scorecard/` (copiados con sha256; nada se modifica). A-lite usó otro split: la
  comparación justa es el subconjunto de val fuera del desarrollo de todos los modelos (D9b.1); el val completo se
  muestra como referencia favorable a A-lite.
- Targets B y A; calibración solo para el target con que se calibró cada modelo. Bootstrap pareado (1,000).

## Código
- `src/step09b_alite.py` · `tests/test_step09b.py` · `step09b_*.csv`.

## Resultados

### Modelos comparados
| modelo         |   variables | detalle                                                                                                  | target de desarrollo   | forma                          |
|:---------------|------------:|:---------------------------------------------------------------------------------------------------------|:-----------------------|:-------------------------------|
| A-lite         |           5 | segment, banker_change_6m_flag, client_reply_rate, external_transfer_pct_of_balance_60d, share_of_wallet | A (hard churn 6M)      | puntos por bin (logística WoE) |
| M1 · scorecard |           8 | ver churn_scorecard/reports/step11.md                                                                    | B                      | puntos por bin (logística WoE) |
| EBM            |          12 | ver reports/step02.md                                                                                    | B                      | puntos por bin (EBM aditivo)   |

### Subconjunto justo (fuera del desarrollo de todos) [DATA]
| target                | modelo                         |   hogares |   eventos |   AUC |   Gini |   PR-AUC |    KS |   Precision@1% % |   Precision@5% % |   Precision@10% % |   captura RV eventos top 10% % |   Brier |   pendiente b |
|:----------------------|:-------------------------------|----------:|----------:|------:|-------:|---------:|------:|-----------------:|-----------------:|------------------:|-------------------------------:|--------:|--------------:|
| B (hard ∪ soft ≥ 25%) | A-lite (5 variables)           |      1737 |       238 | 0.656 |  0.312 |    0.262 | 0.242 |           52.941 |           40.230 |            33.908 |                         21.351 | nan     |       nan     |
| B (hard ∪ soft ≥ 25%) | M1 · scorecard (8 variables)   |      1737 |       238 | 0.661 |  0.321 |    0.304 | 0.274 |           58.824 |           49.425 |            35.057 |                         20.258 |   0.110 |         0.874 |
| B (hard ∪ soft ≥ 25%) | EBM (12 variables)             |      1737 |       238 | 0.663 |  0.327 |    0.305 | 0.263 |           70.588 |           49.425 |            36.207 |                         19.557 |   0.111 |         0.732 |
| B (hard ∪ soft ≥ 25%) | XGBoost (retirado, referencia) |      1737 |       238 | 0.660 |  0.320 |    0.297 | 0.256 |           64.706 |           45.977 |            35.057 |                         19.829 |   0.111 |         0.736 |
| A (hard churn 6M)     | A-lite (5 variables)           |      1764 |       106 | 0.692 |  0.383 |    0.153 | 0.275 |           22.222 |           25.000 |            21.023 |                         36.435 |   0.054 |         0.780 |
| A (hard churn 6M)     | M1 · scorecard (8 variables)   |      1764 |       106 | 0.714 |  0.428 |    0.191 | 0.334 |           38.889 |           28.409 |            18.750 |                         21.564 | nan     |       nan     |
| A (hard churn 6M)     | EBM (12 variables)             |      1764 |       106 | 0.716 |  0.432 |    0.209 | 0.333 |           38.889 |           31.818 |            20.455 |                         27.664 | nan     |       nan     |
| A (hard churn 6M)     | XGBoost (retirado, referencia) |      1764 |       106 | 0.716 |  0.432 |    0.192 | 0.333 |           38.889 |           29.545 |            21.023 |                         31.286 | nan     |       nan     |

### Diferencias pareadas (subconjunto justo) [DATA]
| target   | comparación                                         |   ΔGini | ΔGini IC95       |   ΔPR-AUC | ΔPR-AUC IC95     |   % réplicas ΔPR-AUC > 0 |
|:---------|:----------------------------------------------------|--------:|:-----------------|----------:|:-----------------|-------------------------:|
| B        | EBM (12 variables) − A-lite (5 variables)           |   0.015 | [-0.025, +0.052] |     0.042 | [+0.013, +0.069] |                   99.900 |
| B        | M1 · scorecard (8 variables) − A-lite (5 variables) |   0.010 | [-0.034, +0.047] |     0.041 | [+0.013, +0.069] |                   99.600 |
| B        | EBM (12 variables) − M1 · scorecard (8 variables)   |   0.005 | [-0.022, +0.036] |     0.001 | [-0.028, +0.030] |                   52.300 |
| A        | EBM (12 variables) − A-lite (5 variables)           |   0.049 | [-0.003, +0.101] |     0.056 | [+0.018, +0.097] |                   99.800 |
| A        | M1 · scorecard (8 variables) − A-lite (5 variables) |   0.045 | [-0.008, +0.099] |     0.037 | [+0.002, +0.088] |                   98.300 |
| A        | EBM (12 variables) − M1 · scorecard (8 variables)   |   0.004 | [-0.033, +0.041] |     0.019 | [-0.027, +0.061] |                   74.100 |

### Tramos en el subconjunto justo [DATA]
| modelo   | tramo      |   % hogares |   eventos B |   tasa B % |   tasa A % |
|:---------|:-----------|------------:|------------:|-----------:|-----------:|
| A-lite   | Crítico    |        3.22 |          29 |      51.79 |      32.14 |
| A-lite   | Alto       |       10.19 |          40 |      22.60 |      13.56 |
| A-lite   | Vigilancia |       51.64 |         120 |      13.38 |       5.24 |
| A-lite   | Estable    |       34.95 |          49 |       8.07 |       2.80 |
| M1       | Crítico    |        4.43 |          39 |      50.65 |      32.47 |
| M1       | Alto       |       23.78 |          81 |      19.61 |       7.99 |
| M1       | Vigilancia |       46.00 |          86 |      10.76 |       4.76 |
| M1       | Estable    |       25.79 |          32 |       7.14 |       2.23 |
| EBM      | Crítico    |        4.72 |          39 |      47.56 |      31.71 |
| EBM      | Alto       |       21.07 |          65 |      17.76 |       7.65 |
| EBM      | Vigilancia |       52.10 |         104 |      11.49 |       4.97 |
| EBM      | Estable    |       22.11 |          30 |       7.81 |       1.82 |

- Verificación: % hogares suma 100% por modelo [DATA]. A-lite define Crítico como top 3% (Modelo 1 previo).

### Val completo (referencia; favorable a A-lite) [DATA]
| target                | modelo                         |   hogares |   eventos |   AUC |   Gini |   PR-AUC |    KS |   Precision@1% % |   Precision@5% % |   Precision@10% % |   captura RV eventos top 10% % |   Brier |   pendiente b |
|:----------------------|:-------------------------------|----------:|----------:|------:|-------:|---------:|------:|-----------------:|-----------------:|------------------:|-------------------------------:|--------:|--------------:|
| B (hard ∪ soft ≥ 25%) | A-lite (5 variables)           |      5779 |       803 | 0.694 |  0.388 |    0.309 | 0.284 |           67.241 |           47.059 |            38.754 |                         27.902 | nan     |       nan     |
| B (hard ∪ soft ≥ 25%) | M1 · scorecard (8 variables)   |      5779 |       803 | 0.695 |  0.390 |    0.328 | 0.282 |           63.793 |           51.557 |            38.754 |                         25.843 |   0.109 |         1.000 |
| B (hard ∪ soft ≥ 25%) | EBM (12 variables)             |      5779 |       803 | 0.703 |  0.406 |    0.343 | 0.295 |           75.862 |           50.519 |            39.965 |                         26.673 |   0.108 |         0.878 |
| B (hard ∪ soft ≥ 25%) | XGBoost (retirado, referencia) |      5779 |       803 | 0.701 |  0.403 |    0.344 | 0.294 |           77.586 |           52.249 |            39.619 |                         26.273 |   0.108 |         0.899 |
| A (hard churn 6M)     | A-lite (5 variables)           |      5842 |       351 | 0.749 |  0.498 |    0.200 | 0.368 |           39.655 |           29.110 |            22.774 |                         44.935 |   0.052 |         0.962 |
| A (hard churn 6M)     | M1 · scorecard (8 variables)   |      5842 |       351 | 0.743 |  0.486 |    0.200 | 0.377 |           39.655 |           28.767 |            20.205 |                         34.566 | nan     |       nan     |
| A (hard churn 6M)     | EBM (12 variables)             |      5842 |       351 | 0.747 |  0.495 |    0.220 | 0.372 |           50.000 |           30.137 |            21.404 |                         37.162 | nan     |       nan     |
| A (hard churn 6M)     | XGBoost (retirado, referencia) |      5842 |       351 | 0.748 |  0.496 |    0.223 | 0.378 |           55.172 |           30.822 |            22.260 |                         40.509 | nan     |       nan     |

## Tests
- `tests/test_step09b.py` (ver pytest).

## Decisiones y preguntas abiertas
- D9b.1 en `reports/decision_log.md`.
