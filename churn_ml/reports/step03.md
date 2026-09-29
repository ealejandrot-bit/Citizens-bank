# Paso 3 · Algoritmo e hiperparámetros

## Objetivo
- Elegir algoritmo e hiperparámetros del ML con la CV 5×5 de dev y compararlo con las referencias.

## Método
- XGBoost y LightGBM monotónicos, Optuna 150 trials cada uno (TPE semilla 42, MedianPruner), objetivo PR-AUC media 5×5;
  early stopping en 15% interno; probabilidad corregida por prior. 3 semillas. Referencias en r1: EBM, RF, campeón M1.
- Regla de elección (D3.1): mayor PR-AUC; si la diferencia ≤ 1 sd, el más simple.

## Código
- `src/step03_tuning.py` · `tests/test_step03.py` · `step03_*.csv`, `outputs/model/step03_choice.pkl`.

## Resultados

### Mejores hiperparámetros [DATA]
| algoritmo   |   árboles |   trials completos |   podados |   PR-AUC Optuna |   param max_depth |   param min_child_weight |   param learning_rate |   param subsample |   param colsample_bytree |   param reg_lambda |   param reg_alpha |   param gamma |
|:------------|----------:|-------------------:|----------:|----------------:|------------------:|-------------------------:|----------------------:|------------------:|-------------------------:|-------------------:|------------------:|--------------:|
| xgboost     |       110 |                150 |         0 |          0.3615 |                 2 |                  40.6895 |                0.0513 |            0.7375 |                   0.8845 |            13.2309 |            4.7366 |        0.1476 |
| lightgbm    |       115 |                150 |         0 |          0.3634 |                 3 |                   6.8544 |                0.0585 |            0.7135 |                   0.5007 |            15.3674 |            4.4363 |        3.7104 |

### Algoritmos (CV 5×5, semilla 42) [DATA]
| algoritmo   |   AUC media |   Gini media |   PR-AUC media |   KS media |   Brier media |   pendiente b media |   captura RV eventos decil 1 media |   Gini entrenamiento media |   PR-AUC sd |   árboles |   profundidad |   complejidad (árboles × prof.) | elegido   |
|:------------|------------:|-------------:|---------------:|-----------:|--------------:|--------------------:|-----------------------------------:|---------------------------:|------------:|----------:|--------------:|--------------------------------:|:----------|
| lightgbm    |      0.7157 |       0.4314 |         0.3645 |     0.3241 |        0.1059 |              1.0414 |                             0.3106 |                     0.4709 |      0.0191 |       115 |             3 |                             345 | False     |
| xgboost     |      0.7156 |       0.4312 |         0.3630 |     0.3196 |        0.1063 |              1.1444 |                             0.2930 |                     0.4649 |      0.0206 |       110 |             2 |                             220 | True      |

- Elegido: **xgboost** (diferencia ≤ 1 sd ⟹ el más simple) [DATA].

### Sensibilidad a la semilla (PR-AUC media) [DATA]
| algoritmo   |     42 |     43 |     44 |
|:------------|-------:|-------:|-------:|
| lightgbm    | 0.3645 | 0.3650 | 0.3646 |
| xgboost     | 0.3630 | 0.3637 | 0.3629 |

### Referencias (5 folds de r1, mismos hogares) [DATA]
| modelo                     |   AUC media |   Gini media |   PR-AUC media |   Brier media |   pendiente b media |   captura RV eventos decil 1 media |
|:---------------------------|------------:|-------------:|---------------:|--------------:|--------------------:|-----------------------------------:|
| campeón M1 (logística WoE) |      0.7128 |       0.4256 |         0.3424 |        0.1074 |              0.9348 |                             0.2691 |
| EBM monotónico             |      0.7143 |       0.4286 |         0.3645 |        0.1058 |              1.0154 |                             0.3212 |
| RF (corregido por prior)   |      0.7113 |       0.4225 |         0.3570 |        0.1075 |              1.1018 |                             0.3091 |
| XGBoost                    |      0.7143 |       0.4286 |         0.3617 |        0.1064 |              1.1338 |                             0.2805 |
| LightGBM                   |      0.7145 |       0.4290 |         0.3647 |        0.1060 |              1.0356 |                             0.3122 |

## Tests
- `tests/test_step03.py` (ver pytest).

## Decisiones y preguntas abiertas
- D3.1–D3.2 en `reports/decision_log.md`; preguntas G1 en `reports/gate_1.md`.
