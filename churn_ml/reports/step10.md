# Paso 10 · Uso conjunto

## Objetivo
- Decidir cómo aprovechar el ML si no reemplaza al M1: ¿ordena mejor dentro de los tramos, alerta casos que el M1 no
  ve, o no agrega?

## Método
- Val (modelos congelados). Matriz de tramos M1 × EBM. Opciones a igual número de hogares contactados (K) en tres lentes
  consistentes. Regla previa (D10.1): dentro de la lente política, mayor captura de RV de eventos al 10%; empate < 1 pp
  ⟹ la más simple de operar.
- A-lite: mismas opciones en el subconjunto justo (1,737 hogares fuera del desarrollo de todos).

## Código
- `src/step10_joint.py` · `tests/test_step10.py` · `step10_*.csv`.

## Resultados

### Hogares por tramo M1 × EBM (val) [DATA]
| M1 \ EBM   |   Crítico |   Alto |   Vigilancia |   Estable |
|:-----------|----------:|-------:|-------------:|----------:|
| Crítico    |       183 |     67 |            0 |         0 |
| Alto       |        60 |   1031 |          277 |         0 |
| Vigilancia |         1 |    138 |         2285 |       112 |
| Estable    |         0 |      0 |          334 |      1291 |

- Acuerdo de tramo: 82.9% de los hogares [DATA]. Verificación: la matriz suma 5,779 = 5,779.

### Tasa B observada por celda (val) [DATA]
| M1 \ EBM (tasa B %)   |   Crítico |   Alto |   Vigilancia |   Estable |
|:----------------------|----------:|-------:|-------------:|----------:|
| Crítico               |      57.9 |   49.3 |        nan   |     nan   |
| Alto                  |      40   |   21.2 |         16.2 |     nan   |
| Vigilancia            |       0   |   13   |         11.2 |       7.1 |
| Estable               |     nan   |  nan   |          7.2 |       5.5 |

### Marcados Crítico/Alto por uno solo [DATA]
| grupo                 |   hogares |   eventos |   tasa B % |
|:----------------------|----------:|----------:|-----------:|
| Crítico/Alto en ambos |      1341 |       382 |      28.49 |
| solo M1               |       277 |        45 |      16.25 |
| solo EBM              |       139 |        18 |      12.95 |
| ninguno               |      4022 |       358 |       8.90 |

### Captura por opción a igual capacidad (val) [DATA]
| opción                              |   RV capturado @1% |   RV capturado @5% |   RV capturado @10% |   RV capturado @20% |   RV capturado @28% |   eventos @1% |   eventos @5% |   eventos @10% |   eventos @20% |   eventos @28% |
|:------------------------------------|-------------------:|-------------------:|--------------------:|--------------------:|--------------------:|--------------:|--------------:|---------------:|---------------:|---------------:|
| política · EBM (tramo, luego p×RV)  |               12.9 |               33.3 |                48.0 |                54.8 |                68.2 |           5.5 |          18.2 |           27.5 |           41.8 |           52.3 |
| política · M1 (tramo, luego p×RV)   |               12.0 |               33.5 |                48.9 |                57.3 |                59.4 |           4.9 |          19.3 |           27.8 |           43.0 |           53.2 |
| política · M1 + alerta EBM (c)      |               12.0 |               32.9 |                48.9 |                57.3 |                59.4 |           4.9 |          19.2 |           27.8 |           43.0 |           53.2 |
| política · M1 tramo + orden EBM (b) |               12.3 |               31.4 |                49.4 |                57.4 |                59.4 |           5.2 |          18.8 |           28.6 |           43.5 |           53.2 |
| probabilidad · EBM (p global)       |                5.5 |               17.6 |                26.7 |                45.5 |                53.2 |           5.5 |          18.2 |           28.8 |           43.7 |           52.4 |
| probabilidad · M1 (p global)        |                4.9 |               17.6 |                25.8 |                42.4 |                49.8 |           4.6 |          18.6 |           27.9 |           43.2 |           52.3 |
| valor · EBM (p×RV global)           |               22.4 |               45.3 |                60.9 |                72.7 |                79.7 |           3.5 |          11.6 |           21.0 |           33.4 |           42.1 |
| valor · M1 (p×RV global)            |               23.9 |               44.4 |                58.8 |                72.0 |                79.2 |           3.0 |          10.3 |           18.3 |           31.3 |           40.2 |
| valor · promedio M1/EBM             |               21.5 |               46.1 |                60.0 |                72.5 |                79.8 |           2.9 |          11.3 |           19.4 |           32.4 |           41.2 |

- Recomendación por la regla D10.1: **política · M1 (tramo, luego p×RV)** (captura de RV al 10%: 48.9% vs M1 48.9%) [DATA].
- Las lentes "valor" y "probabilidad" muestran el efecto de cambiar la prioridad (no solo el modelo): ordenar por p×RV
  global concentra más RV y menos eventos; es una decisión de negocio separada de la elección de modelo.

### A-lite en el subconjunto justo (captura de RV de eventos) [DATA]
| opción                                  |   RV capturado @1% |   RV capturado @5% |   RV capturado @10% |   RV capturado @20% |   RV capturado @28% |
|:----------------------------------------|-------------------:|-------------------:|--------------------:|--------------------:|--------------------:|
| política · A-lite (tramo, luego p×RV)   |                8.3 |               18.9 |                24.9 |                66.0 |                73.6 |
| política · A-lite + alerta EBM (c)      |                8.3 |               17.6 |                24.8 |                66.0 |                73.2 |
| política · A-lite tramo + orden EBM (b) |                8.1 |               19.6 |                25.3 |                66.9 |                73.4 |
| política · EBM (tramo, luego p×RV)      |                9.1 |               24.5 |                43.4 |                48.5 |                64.6 |
| política · M1 (tramo, luego p×RV)       |                7.6 |               29.5 |                46.8 |                53.2 |                55.2 |
| política · M1 + alerta EBM (c)          |                7.6 |               29.5 |                46.8 |                53.2 |                55.2 |
| política · M1 tramo + orden EBM (b)     |                7.6 |               27.1 |                47.4 |                53.1 |                55.2 |
| probabilidad · A-lite (p global)        |                2.5 |               12.1 |                21.4 |                36.2 |                50.6 |
| probabilidad · EBM (p global)           |                4.5 |               14.3 |                19.6 |                32.5 |                43.4 |
| probabilidad · M1 (p global)            |                3.3 |               12.5 |                20.3 |                36.0 |                43.5 |
| valor · A-lite (p×RV global)            |               17.5 |               45.4 |                63.8 |                74.6 |                81.2 |
| valor · EBM (p×RV global)               |               20.3 |               43.1 |                66.3 |                75.6 |                81.8 |
| valor · M1 (p×RV global)                |               20.4 |               50.2 |                65.2 |                76.1 |                80.7 |
| valor · promedio A-lite/EBM             |               21.2 |               46.7 |                65.9 |                75.4 |                81.5 |
| valor · promedio M1/EBM                 |               19.8 |               45.6 |                65.7 |                76.7 |                81.1 |

## Tests
- `tests/test_step10.py` (ver pytest).

## Decisiones y preguntas abiertas
- D10.1 en `reports/decision_log.md`.
