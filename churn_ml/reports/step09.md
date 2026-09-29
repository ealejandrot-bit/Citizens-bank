# Paso 9 · Validación en el holdout y tabla H-2

## Objetivo
- Medir el ML congelado una sola vez en validación y decidir con la tabla H-2 si reemplaza al M1.

## Método
- Mismos 5,779 hogares B de val para EBM, XGBoost y M1; ΔGini y ΔPR-AUC con IC bootstrap pareado (1,000).
- Probabilidad publicada de cada modelo (EBM y XGBoost calibrados en dev; M1 calibrado sobre val en su paso 14, lo que
  favorece su Brier y b aquí).

## Código
- `src/step09_validation.py` · `tests/test_step09.py` · `step09_*.csv`.

## Resultados

### Métricas globales dev y val [DATA]
| modelo   | muestra   |    AUC |   Gini |   PR-AUC |     KS |   Brier |   pendiente b |   media p % |   tasa % |   captura RV eventos decil 1 % |
|:---------|:----------|-------:|-------:|---------:|-------:|--------:|--------------:|------------:|---------:|-------------------------------:|
| EBM      | dev       | 0.7219 | 0.4438 |   0.3704 | 0.3195 |  0.1050 |        1.0083 |     13.7573 |  13.8778 |                        32.6843 |
| EBM      | val       | 0.7028 | 0.4055 |   0.3428 | 0.2955 |  0.1079 |        0.8784 |     13.8113 |  13.8951 |                        26.6729 |
| XGBoost  | dev       | 0.7307 | 0.4615 |   0.3790 | 0.3338 |  0.1043 |        1.0697 |     13.9201 |  13.8778 |                        31.8106 |
| XGBoost  | val       | 0.7014 | 0.4027 |   0.3435 | 0.2935 |  0.1078 |        0.8994 |     13.9787 |  13.8951 |                        26.5610 |
| M1       | dev       | 0.7219 | 0.4438 |   0.3490 | 0.3167 |  0.1066 |        1.1403 |     13.7945 |  13.8778 |                        28.8239 |
| M1       | val       | 0.6950 | 0.3900 |   0.3281 | 0.2824 |  0.1086 |        1.0000 |     13.8951 |  13.8951 |                        25.8429 |

### Diferencias contra M1 (val, pareado) [DATA]
| modelo   |   ΔGini vs M1 | ΔGini IC95         |   ΔPR-AUC vs M1 | ΔPR-AUC IC95       |   % réplicas ΔPR-AUC > 0 |
|:---------|--------------:|:-------------------|----------------:|:-------------------|-------------------------:|
| EBM      |        0.0156 | [-0.0003, +0.0304] |          0.0147 | [-0.0013, +0.0301] |                  96.7000 |
| XGBoost  |        0.0128 | [-0.0007, +0.0260] |          0.0154 | [+0.0004, +0.0291] |                  97.9000 |

### Precision@K (val) [DATA]
| modelo   |   K % |   Precision@K % |   Lift@K |   captura % |   captura RV eventos % |
|:---------|------:|----------------:|---------:|------------:|-----------------------:|
| EBM      |     1 |           75.86 |     5.46 |        5.48 |                   5.51 |
| EBM      |     5 |           50.52 |     3.64 |       18.18 |                  17.58 |
| EBM      |    10 |           39.97 |     2.88 |       28.77 |                  26.67 |
| EBM      |    20 |           30.36 |     2.19 |       43.71 |                  45.54 |
| XGBoost  |     1 |           77.59 |     5.58 |        5.60 |                   5.33 |
| XGBoost  |     5 |           52.25 |     3.76 |       18.80 |                  18.41 |
| XGBoost  |    10 |           39.62 |     2.85 |       28.52 |                  26.27 |
| XGBoost  |    20 |           30.54 |     2.20 |       43.96 |                  40.50 |
| M1       |     1 |           63.79 |     4.59 |        4.61 |                   4.88 |
| M1       |     5 |           51.56 |     3.71 |       18.56 |                  17.60 |
| M1       |    10 |           38.75 |     2.79 |       27.90 |                  25.84 |
| M1       |    20 |           30.02 |     2.16 |       43.21 |                  42.37 |

### Gains por decil · EBM (val) [DATA]
|   decil |   hogares |   eventos |   tasa % |   captura acumulada % |   captura RV eventos acumulada % |   lift |
|--------:|----------:|----------:|---------:|----------------------:|---------------------------------:|-------:|
|    1.00 |    578.00 |    231.00 |    39.97 |                 28.77 |                            26.67 |   2.88 |
|    2.00 |    578.00 |    120.00 |    20.76 |                 43.71 |                            45.54 |   1.49 |
|    3.00 |    578.00 |     87.00 |    15.05 |                 54.55 |                            56.02 |   1.08 |
|    4.00 |    578.00 |     80.00 |    13.84 |                 64.51 |                            67.23 |   1.00 |
|    5.00 |    578.00 |     63.00 |    10.90 |                 72.35 |                            73.29 |   0.78 |
|    6.00 |    577.00 |     64.00 |    11.09 |                 80.32 |                            78.28 |   0.80 |
|    7.00 |    578.00 |     52.00 |     9.00 |                 86.80 |                            86.15 |   0.65 |
|    8.00 |    578.00 |     45.00 |     7.79 |                 92.40 |                            91.57 |   0.56 |
|    9.00 |    578.00 |     29.00 |     5.02 |                 96.01 |                            96.34 |   0.36 |
|   10.00 |    578.00 |     32.00 |     5.54 |                100.00 |                           100.00 |   0.40 |

- Verificación: eventos suman 803 = 803; captura acumulada final 100% [DATA].

### Tramos en val (calibración y estabilidad) [DATA]
| modelo   | tramo      |   % val |   eventos |   esperada % |   observada % | Wilson 90%   | dentro de IC   |   tasa dev % |
|:---------|:-----------|--------:|----------:|-------------:|--------------:|:-------------|:---------------|-------------:|
| EBM      | Crítico    |    4.22 |       130 |        61.32 |         53.28 | [48.0, 58.5] | False          |        59.96 |
| EBM      | Alto       |   21.39 |       270 |        21.41 |         21.84 | [20.0, 23.8] | True           |        22.49 |
| EBM      | Vigilancia |   50.11 |       324 |        10.70 |         11.19 | [10.3, 12.2] | True           |        10.76 |
| EBM      | Estable    |   24.28 |        79 |         5.29 |          5.63 | [4.7, 6.7]   | True           |         4.57 |
| XGBoost  | Crítico    |    5.10 |       153 |        56.39 |         51.86 | [47.1, 56.6] | True           |        58.04 |
| XGBoost  | Alto       |   18.15 |       236 |        22.11 |         22.50 | [20.4, 24.7] | True           |        23.34 |
| XGBoost  | Vigilancia |   54.65 |       345 |        11.01 |         10.92 | [10.0, 11.9] | True           |        10.48 |
| XGBoost  | Estable    |   22.10 |        69 |         4.85 |          5.40 | [4.5, 6.5]   | True           |         4.02 |
| M1       | Crítico    |    4.33 |       139 |        52.19 |         55.60 | [50.4, 60.7] | True           |        56.62 |
| M1       | Alto       |   23.67 |       288 |        20.24 |         21.05 | [19.3, 22.9] | True           |        22.86 |
| M1       | Vigilancia |   43.88 |       281 |        11.59 |         11.08 | [10.1, 12.1] | True           |        10.98 |
| M1       | Estable    |   28.12 |        95 |         6.26 |          5.85 | [5.0, 6.9]   | True           |         4.74 |

- Verificación: % val suma 100% por modelo; PSI dev→val por tramo: EBM 0.0008, XGBoost 0.0003, M1 0.0003 [DATA].

### Confusión al corte de Crítico (val) [DATA]
| modelo   |   hogares Crítico |   TP |   FP |   precisión % |   recall % |   FP por evento capturado |
|:---------|------------------:|-----:|-----:|--------------:|-----------:|--------------------------:|
| EBM      |               244 |  130 |  114 |         53.28 |      16.19 |                      0.88 |
| XGBoost  |               295 |  153 |  142 |         51.86 |      19.05 |                      0.93 |
| M1       |               250 |  139 |  111 |         55.60 |      17.31 |                      0.80 |

### Tabla H-2 (reemplazo del M1) [DATA]
| modelo   | criterio H-2                                      | valor [DATA]                | cumple   |
|:---------|:--------------------------------------------------|:----------------------------|:---------|
| EBM      | ΔGini ≥ +0.05                                     | +0.0156 [-0.0003, +0.0304]  | no       |
| EBM      | ΔPR-AUC ≥ +0.03                                   | +0.0147 [-0.0013, +0.0301]  | no       |
| EBM      | Caída de Gini dev→val ≤ 15% y no peor que M1      | 8.6% vs M1 12.1%            | sí       |
| EBM      | Brier ≤ M1 con b ∈ [0.8, 1.2] (val)               | 0.1079 vs 0.1086; b = 0.878 | sí       |
| EBM      | Violaciones de monotonía = 0                      | 0                           | sí       |
| EBM      | Reason codes ≥ 70% (top 1) y signo coherente 100% | 85.0%; signo 100.00%        | sí       |
| EBM      | Captura RV de eventos decil 1 ≥ M1 (val)          | 26.7% vs 25.8%              | sí       |
| EBM      | PSI dev→val por tramo < 0.10                      | 0.0008                      | sí       |
| XGBoost  | ΔGini ≥ +0.05                                     | +0.0128 [-0.0007, +0.0260]  | no       |
| XGBoost  | ΔPR-AUC ≥ +0.03                                   | +0.0154 [+0.0004, +0.0291]  | no       |
| XGBoost  | Caída de Gini dev→val ≤ 15% y no peor que M1      | 12.7% vs M1 12.1%           | no       |
| XGBoost  | Brier ≤ M1 con b ∈ [0.8, 1.2] (val)               | 0.1078 vs 0.1086; b = 0.899 | sí       |
| XGBoost  | Violaciones de monotonía = 0                      | 0                           | sí       |
| XGBoost  | Reason codes ≥ 70% (top 1) y signo coherente 100% | 81.5%; signo 99.96%         | no       |
| XGBoost  | Captura RV de eventos decil 1 ≥ M1 (val)          | 26.6% vs 25.8%              | sí       |
| XGBoost  | PSI dev→val por tramo < 0.10                      | 0.0003                      | sí       |

- Criterios no cumplidos: EBM 2, XGBoost 4 [DATA]. Si hay alguno, el ML no reemplaza al M1 y el paso 10
  evalúa el uso conjunto (I-7).

## Tests
- `tests/test_step09.py` (ver pytest).

## Decisiones y preguntas abiertas
- D9.1 en `reports/decision_log.md`; preguntas G3 en `reports/gate_3.md`.
