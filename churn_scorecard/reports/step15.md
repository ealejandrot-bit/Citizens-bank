# Paso 15 · Estabilidad

## Objetivo
- Verificar que score, probabilidad, tramos y variables no cambian entre desarrollo y validación, ni dentro de los
  subgrupos, y que el peso de cada variable es estable entre folds.

## Método
- PSI = Σ (%val − %dev)·ln(%val/%dev) con bins de dev; lectura < 0.10 estable, 0.10–0.25 vigilar, > 0.25 cambio [DEF SPEC paso 17].
- Subgrupos: segmento, quintil de RV (cortes de dev), antigüedad, historia < 24 meses, cluster.
- Deriva de contribuciones: participación de |β_j·WoE_j| en los 25 entrenamientos de la CV 5×5.
- Sin PSI temporal: un solo snapshot (L1).

## Código
- `src/step15_stability.py` · `tests/test_step15.py` · `step15_*.csv`.

## Resultados

### PSI dev → val [DATA]
| objeto                                          |    PSI | lectura   |
|:------------------------------------------------|-------:|:----------|
| score (deciles de dev)                          | 0.0034 | estable   |
| p calibrada (deciles de dev)                    | 0.0035 | estable   |
| tramo                                           | 0.0003 | estable   |
| variable · client_reply_rate (bins WoE)         | 0.0008 | estable   |
| variable · banker_change_6m_flag (bins WoE)     | 0.0000 | estable   |
| variable · share_of_wallet (bins WoE)           | 0.0008 | estable   |
| variable · outflow_x_contact_gap (bins WoE)     | 0.0007 | estable   |
| variable · return_vs_benchmark (bins WoE)       | 0.0027 | estable   |
| variable · streams_stopped_count (bins WoE)     | 0.0003 | estable   |
| variable · cash_pct_of_portfolio_chg (bins WoE) | 0.0009 | estable   |
| variable · contact_gap_ratio_peer (bins WoE)    | 0.0015 | estable   |

### PSI por subgrupo [DATA]
| subgrupo         | nivel   |   hogares dev |   hogares val |   eventos val |   PSI score |   PSI tramo |   score medio dev |   score medio val | lectura   |
|:-----------------|:--------|--------------:|--------------:|--------------:|------------:|------------:|------------------:|------------------:|:----------|
| segmento         | HNW     |         12731 |          5456 |           750 |      0.0037 |      0.0005 |          543.5494 |          543.2227 | estable   |
| segmento         | UHNW    |           751 |           323 |            53 |      0.0347 |      0.0136 |          550.4141 |          552.9443 | estable   |
| quintil RV       | Q1      |          2697 |          1165 |           159 |      0.0031 |      0.0037 |          543.6533 |          543.1639 | estable   |
| quintil RV       | Q2      |          2696 |          1219 |           166 |      0.0197 |      0.0011 |          544.7596 |          544.2518 | estable   |
| quintil RV       | Q3      |          2696 |          1140 |           159 |      0.0143 |      0.0018 |          543.0816 |          542.0667 | estable   |
| quintil RV       | Q4      |          2696 |          1098 |           140 |      0.0129 |      0.0031 |          543.1654 |          544.2532 | estable   |
| quintil RV       | Q5      |          2697 |          1156 |           179 |      0.0103 |      0.0003 |          544.9989 |          545.1090 | estable   |
| banda antigüedad | 15+     |          2123 |           890 |           109 |      0.0153 |      0.0030 |          545.6665 |          544.2315 | estable   |
| banda antigüedad | 1–3     |          1600 |           723 |           125 |      0.0126 |      0.0044 |          542.9425 |          542.7303 | estable   |
| banda antigüedad | 3–7     |          4431 |          1826 |           246 |      0.0053 |      0.0016 |          543.7348 |          544.4754 | estable   |
| banda antigüedad | 7–15    |          5328 |          2340 |           323 |      0.0073 |      0.0008 |          543.7016 |          543.3556 | estable   |
| historia < 24m   | no      |         12788 |          5472 |           751 |      0.0036 |      0.0002 |          543.9379 |          543.8830 | estable   |
| historia < 24m   | sí      |           694 |           307 |            52 |      0.0143 |      0.0034 |          543.8199 |          541.6808 | estable   |
| cluster          | 0       |           751 |           323 |            53 |      0.0347 |      0.0136 |          550.4141 |          552.9443 | estable   |
| cluster          | 1       |          7130 |          3092 |           427 |      0.0079 |      0.0010 |          543.0473 |          543.0239 | estable   |
| cluster          | 2       |          1896 |           817 |           104 |      0.0301 |      0.0019 |          546.5069 |          547.1016 | estable   |
| cluster          | 3       |          3705 |          1547 |           219 |      0.0062 |      0.0013 |          543.0024 |          541.5714 | estable   |

### PSI de la mezcla de subgrupos [DATA]
| subgrupo         |   PSI de la mezcla dev→val |
|:-----------------|---------------------------:|
| segmento         |                     0.0000 |
| quintil RV       |                     0.0011 |
| banda antigüedad |                     0.0012 |
| historia < 24m   |                     0.0001 |
| cluster          |                     0.0003 |

### Deriva de contribuciones entre folds [DATA]
| variable                  |   participación media % |   sd entre folds (pp) |   CV % |   mín % |   máx % | orden estable (rango mín–máx del puesto)   |
|:--------------------------|------------------------:|----------------------:|-------:|--------:|--------:|:-------------------------------------------|
| banker_change_6m_flag     |                   23.61 |                  0.71 |   3.01 |   22.30 |   25.31 | 1–2                                        |
| client_reply_rate         |                   23.49 |                  1.17 |   4.99 |   20.63 |   25.55 | 1–2                                        |
| share_of_wallet           |                   12.32 |                  0.75 |   6.08 |   10.71 |   13.71 | 3–3                                        |
| return_vs_benchmark       |                    9.52 |                  0.64 |   6.76 |    8.70 |   11.59 | 4–5                                        |
| contact_gap_ratio_peer    |                    8.79 |                  0.84 |   9.53 |    6.86 |   10.23 | 4–8                                        |
| cash_pct_of_portfolio_chg |                    7.54 |                  0.55 |   7.24 |    6.18 |    8.44 | 5–8                                        |
| outflow_x_contact_gap     |                    7.37 |                  0.94 |  12.77 |    4.64 |    8.75 | 5–8                                        |
| streams_stopped_count     |                    7.36 |                  0.51 |   6.87 |    6.37 |    8.26 | 5–8                                        |

- Verificación: participación media suma 100.0% [DATA].
- Máx. PSI de subgrupo: 0.0347 (segmento ·
  UHNW) [DATA]; subgrupos pequeños tienen PSI más ruidoso.

## Tests
- `tests/test_step15.py` (ver pytest).

## Decisiones y preguntas abiertas
- D15.1 en `reports/decision_log.md`.
