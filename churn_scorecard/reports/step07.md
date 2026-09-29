# Paso 7 · Pre-segmentación

## Objetivo
- Ver si hay perfiles estructurales con riesgo distinto; decidir si justifican variable o modelo propio.

## Método
- K-means (n_init = 20) y GMM diagonal sobre `segment_uhnw`, `tenure_years`, `log_rv`, `has_investments`, `has_advisory`, `has_linked_business`, `has_trust`, `has_credit_anchor`, `has_payroll_stream`, `has_pension_stream`, `has_dividend_stream`, estandarizadas en dev. Sin `age_primary` (D7.1).
- Regla (antes de ver resultados): tamaño ≥ 5% y ARI bootstrap ≥ 0.80 → mayor silhouette. Ajuste en dev; asignación a
  val y a toda la base sin reajuste. Tasas descriptivas, sin causalidad.

## Código
- `src/step07_presegment.py` · `tests/test_step07.py` · `data/processed/step07_clusters.parquet`, `outputs/model/step07_kmeans.pkl`.

## Resultados

### Selección de K [DATA]
|   K |   silhouette |        WCSS |   ARI bootstrap |   cluster mín % |      BIC GMM |   ARI K-means vs GMM | elegido   |
|----:|-------------:|------------:|----------------:|----------------:|-------------:|---------------------:|:----------|
|   2 |        0.203 | 130,267.278 |           0.513 |          14.254 |  181,645.713 |                0.562 |           |
|   3 |        0.235 | 112,027.178 |           0.281 |           5.561 |  -29,620.067 |                0.396 |           |
|   4 |        0.194 |  97,588.042 |           0.869 |           5.561 | -168,416.668 |                1.000 | ◀         |
|   5 |        0.176 |  90,215.185 |           0.773 |           5.561 | -266,003.584 |                0.604 |           |
|   6 |        0.174 |  85,040.033 |           0.704 |           5.561 | -332,178.191 |                0.422 |           |
|   7 |        0.162 |  80,887.951 |           0.658 |           5.561 | -348,761.635 |                0.299 |           |
|   8 |        0.168 |  78,049.904 |           0.584 |           5.561 | -427,363.952 |                0.439 |           |

### Perfil de clusters (dev) [DATA]
|   cluster |   hogares dev |   % dev |   % UHNW |   antigüedad mediana |   RV mediano $M |   % investments |   % advisory |   % linked_business |   % trust |   % credit_anchor |   % payroll_stream |   % pension_stream |   % dividend_stream |   eventos B |   tasa B % | Wilson 90% B   |   tasa A % |
|----------:|--------------:|--------:|---------:|---------------------:|----------------:|----------------:|-------------:|--------------------:|----------:|------------------:|-------------------:|-------------------:|--------------------:|------------:|-----------:|:---------------|-----------:|
|         0 |           758 |    5.56 |   100.00 |                 7.83 |           47.75 |           96.57 |        64.64 |               50.53 |     70.45 |             32.59 |              55.28 |              31.93 |               55.28 |         122 |      16.25 | [14.2, 18.6]   |       7.26 |
|         1 |          7213 |   52.92 |     0.00 |                 7.77 |            4.98 |          100.00 |        70.47 |               24.50 |     29.74 |             34.24 |              74.16 |               0.00 |               55.44 |         984 |      13.80 | [13.1, 14.5]   |       5.99 |
|         2 |          1917 |   14.06 |     0.00 |                 7.70 |            2.87 |            0.00 |         0.00 |               25.61 |     30.05 |             33.12 |              54.67 |              36.05 |                0.00 |         244 |      12.87 | [11.7, 14.2]   |       5.22 |
|         3 |          3743 |   27.46 |     0.00 |                 7.87 |            4.90 |          100.00 |        70.69 |               25.19 |     29.25 |             34.57 |              14.80 |             100.00 |               53.27 |         521 |      14.06 | [13.1, 15.0]   |       6.14 |

- Verificación: Σ share × tasa B = 13.8775% = tasa B de dev 13.8778% [DATA]. χ² cluster × y_B: p = 0.153 [DATA].
- UHNW con target B: 175 eventos en total y 122 en dev [DATA], por encima del mínimo de 100 del SPEC (pensado para A,
  con 79). Se aplica I-7 [DEF-default]: libro completo con `segment_uhnw` como variable; la pregunta de un scorecard UHNW
  propio con B se lleva a G2 (D7.2). `segment_uhnw` y `cluster` pasan como candidatas al paso 9.

## Tests
- `tests/test_step07.py` (ver pytest).

## Decisiones y preguntas abiertas
- D7.1–D7.2 en `reports/decision_log.md`.
