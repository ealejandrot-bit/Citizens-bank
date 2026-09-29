# Paso 13 · Validación

## Objetivo
- Medir el campeón final una sola vez en validación (30%) y aplicar los criterios de aprobación del SPEC.

## Método
- Métricas sobre la probabilidad pre-calibración del score (el orden no cambia con Platt). Gains por decil de score,
  Precision@K / Lift@K con captura ponderada por RV, matriz de confusión al corte de Crítico.
- Aprobación: monotonía por tramo (dev y val), caída de Gini ≤ 15% relativo, PSI dev→val de la distribución por tramo
  < 0.10, ≥ 30 eventos por tramo y banda en val, precisión de overrides en val. UHNW solo global. Sin OOT (L1).

## Código
- `src/step13_validation.py` · `tests/test_step13.py` · `step13_*.csv`.

## Resultados

### Discriminación global [DATA]
| muestra                       |   hogares |   eventos |   tasa % |    AUC |   Gini |   PR-AUC |     KS |
|:------------------------------|----------:|----------:|---------:|-------:|-------:|---------:|-------:|
| dev                           |     13482 |      1871 |  13.8778 | 0.7219 | 0.4438 |   0.3490 | 0.3167 |
| val                           |      5779 |       803 |  13.8951 | 0.6950 | 0.3900 |   0.3281 | 0.2824 |
| val · HNW                     |      5456 |       750 |  13.7463 | 0.6962 | 0.3923 |   0.3257 | 0.2846 |
| val · UHNW                    |       323 |        53 |  16.4087 | 0.6971 | 0.3943 |   0.3940 | 0.2925 |
| dev · target A (sensibilidad) |     13631 |       817 |   5.9937 | 0.7594 | 0.5188 |   0.2134 | 0.3953 |
| val · target A (sensibilidad) |      5842 |       351 |   6.0082 | 0.7430 | 0.4859 |   0.2003 | 0.3774 |

- Caída de Gini dev→val: (0.4438 − 0.3900) / 0.4438 = 12.1% relativo [DATA].
- UHNW: 53 eventos en val [DATA]; solo métricas globales (L5).

### Gains y lift por decil de score (val) [DATA]
|   decil |   hogares |   eventos |   score_mín |   score_máx |   tasa % |   captura % |   captura acumulada % |   captura RV eventos acumulada % |   lift |
|--------:|----------:|----------:|------------:|------------:|---------:|------------:|----------------------:|---------------------------------:|-------:|
|    1.00 |    578.00 |    224.00 |      311.00 |      484.00 |    38.75 |       27.90 |                 27.90 |                            25.84 |   2.79 |
|    2.00 |    578.00 |    123.00 |      484.00 |      514.00 |    21.28 |       15.32 |                 43.21 |                            42.37 |   1.53 |
|    3.00 |    578.00 |     86.00 |      514.00 |      531.00 |    14.88 |       10.71 |                 53.92 |                            50.49 |   1.07 |
|    4.00 |    578.00 |     61.00 |      531.00 |      540.00 |    10.55 |        7.60 |                 61.52 |                            55.98 |   0.76 |
|    5.00 |    578.00 |     72.00 |      540.00 |      549.00 |    12.46 |        8.97 |                 70.49 |                            64.30 |   0.90 |
|    6.00 |    577.00 |     66.00 |      549.00 |      559.00 |    11.44 |        8.22 |                 78.70 |                            76.71 |   0.82 |
|    7.00 |    578.00 |     61.00 |      559.00 |      572.00 |    10.55 |        7.60 |                 86.30 |                            86.33 |   0.76 |
|    8.00 |    578.00 |     48.00 |      572.00 |      584.00 |     8.30 |        5.98 |                 92.28 |                            91.25 |   0.60 |
|    9.00 |    578.00 |     37.00 |      584.00 |      596.00 |     6.40 |        4.61 |                 96.89 |                            96.15 |   0.46 |
|   10.00 |    578.00 |     25.00 |      596.00 |      640.00 |     4.33 |        3.11 |                100.00 |                           100.00 |   0.31 |

- Verificación: captura suma 100.0%; eventos suman 803 = 803 [DATA].

### Precision@K y Lift@K (val) [DATA]
|   K % |   hogares |   eventos |   Precision@K % |   Lift@K |   captura % |   captura RV eventos % |   % RV de la cartera |
|------:|----------:|----------:|----------------:|---------:|------------:|-----------------------:|---------------------:|
|  1.00 |     58.00 |     37.00 |           63.79 |     4.59 |        4.61 |                   4.88 |                 0.95 |
|  5.00 |    289.00 |    149.00 |           51.56 |     3.71 |       18.56 |                  17.60 |                 4.31 |
| 10.00 |    578.00 |    224.00 |           38.75 |     2.79 |       27.90 |                  25.84 |                 9.51 |
| 20.00 |  1,156.00 |    347.00 |           30.02 |     2.16 |       43.21 |                  42.37 |                19.15 |

### Matriz de confusión al corte de Crítico (val) [DATA]
|     TP |     FP |     FN |       TN |   precisión % |   recall % |   falsos positivos por evento capturado |
|-------:|-------:|-------:|---------:|--------------:|-----------:|----------------------------------------:|
| 139.00 | 111.00 | 664.00 | 4,865.00 |         55.60 |      17.31 |                                    0.80 |

- Verificación: TP + FP + FN + TN = 5,779 = 5,779 hogares de val [DATA].

### Tramos dev vs val y PSI [DATA]
| tramos                 | tramo      |   hogares dev |   % dev |   tasa dev % |   hogares val |   % val |   eventos val |   tasa val % |   PSI (contribución) |
|:-----------------------|:-----------|--------------:|--------:|-------------:|--------------:|--------:|--------------:|-------------:|---------------------:|
| final (con overrides)  | Crítico    |           544 |  4.0350 |      56.6176 |           250 |  4.3260 |           139 |      55.6000 |               0.0002 |
| final (con overrides)  | Alto       |          3184 | 23.6167 |      22.8643 |          1368 | 23.6719 |           288 |      21.0526 |               0.0000 |
| final (con overrides)  | Vigilancia |          5977 | 44.3332 |      10.9754 |          2536 | 43.8830 |           281 |      11.0804 |               0.0000 |
| final (con overrides)  | Estable    |          3777 | 28.0151 |       4.7392 |          1625 | 28.1191 |            95 |       5.8462 |               0.0000 |
| modelo (sin overrides) | Crítico    |           544 |  4.0350 |      56.6176 |           250 |  4.3260 |           139 |      55.6000 |               0.0002 |
| modelo (sin overrides) | Alto       |          2336 | 17.3268 |      25.6421 |          1013 | 17.5290 |           227 |      22.4087 |               0.0000 |
| modelo (sin overrides) | Vigilancia |          6731 | 49.9258 |      11.4990 |          2849 | 49.2992 |           332 |      11.6532 |               0.0001 |
| modelo (sin overrides) | Estable    |          3871 | 28.7124 |       4.9083 |          1667 | 28.8458 |           105 |       6.2987 |               0.0000 |

- Verificación: % dev y % val suman 100% por tipo de tramo; churn de cartera val = Σ share × tasa =
  13.90% = 13.90% [DATA].

### Bandas (val) [DATA]
| banda   |   hogares |   eventos |   tasa % |
|:--------|----------:|----------:|---------:|
| CCC/D   |       250 |    139.00 |    55.60 |
| B       |      1013 |    227.00 |    22.41 |
| BB      |      1265 |    161.00 |    12.73 |
| BBB     |      1584 |    171.00 |    10.80 |
| AA      |       688 |     52.00 |     7.56 |
| AAA     |       979 |     53.00 |     5.41 |

### Overrides (val) [DATA]
| regla                                | destino   |   movidos val |   eventos |   precisión val % | cumple umbral (12% Alto / 25% Crítico)   |
|:-------------------------------------|:----------|--------------:|----------:|------------------:|:-----------------------------------------|
| banker_change_6m_flag = 1            | Alto      |           167 |        24 |             14.37 | True                                     |
| complaint_escalated_flag = 1         | Alto      |           158 |        30 |             18.99 | True                                     |
| transfer_to_competitor_pct_90d ≥ 10% | Alto      |            41 |        10 |             24.39 | True                                     |

### Criterios de aprobación [DATA]
| criterio                                                   | cumple   |
|:-----------------------------------------------------------|:---------|
| Tasa monótona por tramo en dev (final)                     | sí       |
| Tasa monótona por tramo en val (final)                     | sí       |
| Tasa monótona por tramo en val (modelo)                    | sí       |
| Caída de Gini dev→val ≤ 15% relativo (12.1%)               | sí       |
| PSI dev→val por tramo < 0.10 (final 0.0003; modelo 0.0003) | sí       |
| ≥ 30 eventos por tramo en val (mín 95)                     | sí       |
| ≥ 30 eventos por banda en val (mín 52)                     | sí       |
| Overrides con precisión ≥ umbral en val                    | sí       |
| Lift Crítico/Estable ≥ 5x en val (9.5x)                    | sí       |

## Tests
- `tests/test_step13.py` (ver pytest).

## Decisiones y preguntas abiertas
- D13.1 en `reports/decision_log.md`.
