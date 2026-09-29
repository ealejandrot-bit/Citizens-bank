# Paso 7 · Robustez en dev

## Objetivo
- Verificar que el EBM no depende de una sola variable ni de un subgrupo, y que su peso por variable es estable.

## Método
- EBM re-ajustado en los 25 entrenamientos de la CV 5×5: participación de |f_j|; sensibilidad a quitar la variable
  principal (PR-AUC pareado); desempeño OOF por subgrupo (≥ 30 eventos) frente a XGBoost y M1.

## Código
- `src/step07_robustness.py` · `tests/test_step07.py` · `step07_*.csv`.

## Resultados

### Estabilidad de importancias (25 folds) [DATA]
| variable                       |   participación media % |   sd (pp) |   CV % | puesto mín–máx   |
|:-------------------------------|------------------------:|----------:|-------:|:-----------------|
| client_reply_rate              |                   21.10 |      1.35 |   6.41 | 1–1              |
| banker_change_6m_flag          |                   17.94 |      0.71 |   3.97 | 2–2              |
| share_of_wallet                |                   10.98 |      0.64 |   5.82 | 3–3              |
| contact_gap_ratio              |                    8.48 |      0.66 |   7.79 | 4–6              |
| transfer_to_competitor_pct_90d |                    8.04 |      0.48 |   5.97 | 4–7              |
| return_vs_benchmark            |                    7.95 |      0.59 |   7.38 | 4–6              |
| recurring_deposit_change_pct   |                    6.03 |      0.75 |  12.36 | 5–10             |
| positions_liquidated_pct       |                    5.12 |      0.30 |   5.94 | 7–10             |
| cash_pct_of_portfolio_chg      |                    4.61 |      0.59 |  12.70 | 7–11             |
| repeat_complaint_flag          |                    4.35 |      0.27 |   6.29 | 8–11             |
| meetings_cancelled_by_client   |                    3.56 |      0.63 |  17.80 | 9–12             |
| complaint_age_days             |                    1.84 |      0.17 |   9.29 | 11–12            |

- Verificación: participación media suma 100.0% [DATA].

### Sensibilidad a quitar la variable principal [DATA]
| variante                  |   PR-AUC CV |     sd |   Δ pareado |   % folds peor |
|:--------------------------|------------:|-------:|------------:|---------------:|
| EBM completo              |      0.3644 | 0.0207 |    nan      |       nan      |
| EBM sin client_reply_rate |      0.3602 | 0.0199 |     -0.0042 |        84.0000 |

### Desempeño por subgrupo (OOF) [DATA]
| subgrupo       | nivel   |   hogares |   eventos |   tasa % |   AUC EBM |   PR-AUC EBM |   p media % EBM |   AUC XGBoost |   PR-AUC XGBoost |   p media % XGBoost |   AUC M1 (OOF r1) |   PR-AUC M1 (OOF r1) |   p media % M1 (OOF r1) |   ΔAUC EBM − M1 |
|:---------------|:--------|----------:|----------:|---------:|----------:|-------------:|----------------:|--------------:|-----------------:|--------------------:|------------------:|---------------------:|------------------------:|----------------:|
| segment        | HNW     |     12731 |      1749 |   13.738 |     0.714 |        0.362 |          13.865 |         0.715 |            0.361 |              13.390 |             0.712 |                0.340 |                  13.973 |           0.001 |
| segment        | UHNW    |       751 |       122 |   16.245 |     0.737 |        0.393 |          14.135 |         0.745 |            0.389 |              12.932 |             0.729 |                0.348 |                  13.037 |           0.008 |
| quintil RV     | Q1      |      2697 |       382 |   14.164 |     0.704 |        0.354 |          13.934 |         0.705 |            0.355 |              13.465 |             0.709 |                0.343 |                  13.867 |          -0.005 |
| quintil RV     | Q2      |      2696 |       364 |   13.501 |     0.696 |        0.332 |          13.505 |         0.702 |            0.337 |              13.120 |             0.703 |                0.323 |                  13.643 |          -0.007 |
| quintil RV     | Q3      |      2696 |       367 |   13.613 |     0.747 |        0.393 |          14.207 |         0.747 |            0.389 |              13.640 |             0.734 |                0.359 |                  14.180 |           0.012 |
| quintil RV     | Q4      |      2696 |       359 |   13.316 |     0.719 |        0.369 |          13.754 |         0.720 |            0.370 |              13.332 |             0.717 |                0.356 |                  14.042 |           0.002 |
| quintil RV     | Q5      |      2697 |       399 |   14.794 |     0.709 |        0.367 |          13.999 |         0.710 |            0.366 |              13.264 |             0.703 |                0.329 |                  13.873 |           0.007 |
| antigüedad     | 15+     |      2123 |       259 |   12.200 |     0.718 |        0.366 |          13.503 |         0.724 |            0.368 |              12.993 |             0.726 |                0.348 |                  13.444 |          -0.008 |
| antigüedad     | 1–3     |      1600 |       257 |   16.062 |     0.692 |        0.394 |          14.285 |         0.698 |            0.392 |              13.761 |             0.701 |                0.354 |                  14.259 |          -0.009 |
| antigüedad     | 3–7     |      4431 |       630 |   14.218 |     0.716 |        0.358 |          13.859 |         0.716 |            0.359 |              13.369 |             0.714 |                0.338 |                  13.985 |           0.002 |
| antigüedad     | 7–15    |      5328 |       725 |   13.607 |     0.720 |        0.357 |          13.925 |         0.719 |            0.356 |              13.389 |             0.710 |                0.340 |                  13.957 |           0.010 |
| historia < 24m | no      |     12788 |      1757 |   13.739 |     0.717 |        0.361 |          13.869 |         0.718 |            0.361 |              13.358 |             0.714 |                0.340 |                  13.912 |           0.003 |
| historia < 24m | sí      |       694 |       114 |   16.427 |     0.683 |        0.384 |          14.076 |         0.689 |            0.381 |              13.484 |             0.696 |                0.341 |                  14.081 |          -0.013 |
| cluster        | 0       |       751 |       122 |   16.245 |     0.737 |        0.393 |          14.135 |         0.745 |            0.389 |              12.932 |             0.729 |                0.348 |                  13.037 |           0.008 |
| cluster        | 1       |      7130 |       984 |   13.801 |     0.722 |        0.370 |          13.968 |         0.722 |            0.368 |              13.434 |             0.720 |                0.346 |                  14.176 |           0.002 |
| cluster        | 2       |      1896 |       244 |   12.869 |     0.699 |        0.307 |          13.253 |         0.701 |            0.301 |              13.138 |             0.695 |                0.291 |                  12.881 |           0.004 |
| cluster        | 3       |      3705 |       521 |   14.062 |     0.704 |        0.373 |          13.978 |         0.707 |            0.380 |              13.434 |             0.707 |                0.354 |                  14.142 |          -0.003 |

- EBM supera o iguala al M1 en AUC en 11 de 17 subgrupos [DATA]; el OOF de M1 es solo de r1 (menos estable).

## Tests
- `tests/test_step07.py` (ver pytest).

## Decisiones y preguntas abiertas
- D7.1 en `reports/decision_log.md`.
