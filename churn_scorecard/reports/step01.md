# Paso 1 · Target y churn rate

## Objetivo
- Construir `y_B` (principal), `y_A` (sensibilidad), indeterminados y pesos, con exclusiones y churn rate de la
  población de modelado.

## Método
- `y_B` = hard ∪ (soft con `value_lost_6m / relationship_value` ≥ θ), θ = 0.25 [DEF-default]; soft con pérdida < θ =
  indeterminado (fuera de entrenamiento y métricas, dentro de scoring). `y_A` = `hard_churn_6m`.
- Exclusiones: `churn_excluded` [DEF-default I-4] y `tenure_years` < 1 [DEF-default I-8]; `history_months` < 24 se
  conserva con indicador `hist_lt24`.
- Pesos de clase balanceados: w = N / (2·n_clase); odds de población guardadas para corregir el intercepto (paso 11).
- Churn por hogares = eventos / hogares; RV bruto = Σ RV eventos / Σ RV; económico = Σ `value_lost_6m` eventos / Σ RV.
- Censura: no aplica (sin tiempo al evento). Supervivencia: no [DEF-default I-9]; solo descriptivo en el paso 14.

## Código
- `src/step01_target.py` · `tests/test_step01.py` · salida `data/processed/step01_population.parquet`.

## Resultados

### Sensibilidad a θ [DATA]
| población                |    θ |   eventos |   de ellos hard |   de ellos soft ≥ θ |   indeterminados (soft < θ) |   base |   tasa % |
|:-------------------------|-----:|----------:|----------------:|--------------------:|----------------------------:|-------:|---------:|
| elegibles                | 0.20 |      2956 |            1200 |                1756 |                           0 |  19877 |    14.87 |
| elegibles                | 0.25 |      2740 |            1200 |                1540 |                         216 |  19661 |    13.94 |
| elegibles                | 0.35 |      2306 |            1200 |                1106 |                         650 |  19227 |    11.99 |
| elegibles                | 0.50 |      1639 |            1200 |                 439 |                        1317 |  18560 |     8.83 |
| elegibles con tenure ≥ 1 | 0.20 |      2886 |            1168 |                1718 |                           0 |  19473 |    14.82 |
| elegibles con tenure ≥ 1 | 0.25 |      2674 |            1168 |                1506 |                         212 |  19261 |    13.88 |
| elegibles con tenure ≥ 1 | 0.35 |      2251 |            1168 |                1083 |                         635 |  18838 |    11.95 |
| elegibles con tenure ≥ 1 | 0.50 |      1596 |            1168 |                 428 |                        1290 |  18183 |     8.78 |

- θ = 0.20 equivale a C (hard ∪ soft) y no deja indeterminados: la pérdida mínima de soft es 0.2003 [DATA].
- Verificación: eventos = hard + soft ≥ θ en cada fila; base = población − indeterminados.

### Exclusiones acumuladas [DATA]
| paso                                         |   hogares |   salen |   eventos B |   eventos A (hard) |   RV $B |
|:---------------------------------------------|----------:|--------:|------------:|-------------------:|--------:|
| total archivo                                |     20000 |       0 |        2740 |               1200 |  207.64 |
| − churn_excluded (I-4)                       |     19877 |     123 |        2740 |               1200 |  206.27 |
| − tenure_years < 1 (I-8)                     |     19473 |     404 |        2674 |               1168 |  202.71 |
| − indeterminados B (soft con pérdida < 0.25) |     19261 |     212 |        2674 |               1168 |  200.55 |

- N final B = 19,261 hogares con 2,674 eventos [DATA]; N final A = 19,473 con
  1,168 eventos [DATA].
- Verificación: cada fila = anterior − salen.

Perfil de los excluidos por antigüedad < 1 año [DATA]:
| grupo excluido               |   hogares |   eventos A |   eventos B |   tasa A % |   tasa A % resto |   tasa B % |   tasa B % resto |
|:-----------------------------|----------:|------------:|------------:|-----------:|-----------------:|-----------:|-----------------:|
| tenure_years < 1 (elegibles) |       404 |          32 |          66 |       7.92 |             6.00 |      16.50 |            13.88 |

### Pesos [DATA]
| target   |     N |   eventos |   tasa % |   w eventos |   w no eventos |   odds población (malos:buenos) |   ln odds población |   odds muestra ponderada |
|:---------|------:|----------:|---------:|------------:|---------------:|--------------------------------:|--------------------:|-------------------------:|
| A        | 19473 |      1168 |   5.9980 |      8.3360 |         0.5319 |                          0.0638 |             -2.7519 |                   1.0000 |
| B        | 19261 |      2674 |  13.8830 |      3.6015 |         0.5806 |                          0.1612 |             -1.8250 |                   1.0000 |

- Con pesos balanceados la muestra ponderada tiene odds 1:1; el paso 11 corrige β₀ con ln odds de población.

### Churn rate de la población final [DATA]
| target   | segmento   |   hogares |   eventos |   churn hogares % |   churn RV bruto % |   churn económico % |
|:---------|:-----------|----------:|----------:|------------------:|-------------------:|--------------------:|
| A        | Total      |     19473 |      1168 |              6.00 |               6.40 |                6.40 |
| A        | HNW        |     18390 |      1089 |              5.92 |               5.95 |                5.95 |
| A        | UHNW       |      1083 |        79 |              7.29 |               7.11 |                7.11 |
| B        | Total      |     19261 |      2674 |             13.88 |              15.19 |               10.15 |
| B        | HNW        |     18187 |      2499 |             13.74 |              13.85 |                9.32 |
| B        | UHNW       |      1074 |       175 |             16.29 |              17.26 |               11.44 |

- Verificación Σ share × tasa: A 5.9980% = 5.9980%; B 13.8830% = 13.8830% [DATA].

### Historia corta (indicador) [DATA]
| target   |   hogares con history < 24 |   tasa con history < 24 % |   tasa con history = 24 % |
|:---------|---------------------------:|--------------------------:|--------------------------:|
| A        |                       1013 |                      6.52 |                      5.97 |
| B        |                       1001 |                     16.58 |                     13.73 |

## Tests
- `tests/test_step01.py` en verde; suite completa `python -m pytest -q`: 30 passed.

## Decisiones y preguntas abiertas
- D1.1–D1.3 en `reports/decision_log.md`.
