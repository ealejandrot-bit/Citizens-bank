# Paso 1 · Balances & AUM

Semilla `20260928` · 20,000 hogares × 24 meses · montos en USD · **54 de 54 pruebas OK** (α = 0.01, Benjamini-Hochberg)

## Calibración

| variable                       | alerta   |   tasa_alerta | rango_tasa   |   IV_hard |   IV_soft | banda_IV   |   tendencia_z |   tendencia_p |   lift_alerta |   spearman_tramos |   null_% |
|:-------------------------------|:---------|--------------:|:-------------|----------:|----------:|:-----------|--------------:|--------------:|--------------:|------------------:|---------:|
| aum_outflow_pct_90d            | > 0.10   |         0.060 | [0.04, 0.16] |     0.134 |     0.031 | [0.1, 0.3] |         8.632 |         0.000 |         3.014 |             0.564 |   14.459 |
| deposit_balance_change_pct_90d | <= -0.25 |         0.058 | [0.04, 0.16] |     0.248 |     0.054 | [0.1, 0.3] |        11.222 |         0.000 |         4.096 |             0.503 |    0.553 |
| aum_vs_baseline_pct            | <= -0.20 |         0.048 | [0.04, 0.16] |     0.175 |     0.046 | [0.1, 0.3] |         8.741 |         0.000 |         4.125 |             0.365 |   14.982 |
| deposit_balance_vs_6m_avg_pct  | <= -0.30 |         0.059 | [0.04, 0.16] |     0.267 |     0.069 | [0.1, 0.3] |        12.723 |         0.000 |         4.104 |             0.648 |    0.790 |

AUC combinado de las 4 variables (logística): **0.621**; techo con la probabilidad verdadera: 0.851.

## Robustez en 20 semillas de referencia

| variable                       |   ('tasa_alerta', 'min') |   ('tasa_alerta', 'median') |   ('tasa_alerta', 'max') |   ('IV_hard', 'min') |   ('IV_hard', 'median') |   ('IV_hard', 'max') |   ('lift_alerta', 'min') |   ('lift_alerta', 'median') |   ('lift_alerta', 'max') |
|:-------------------------------|-------------------------:|----------------------------:|-------------------------:|---------------------:|------------------------:|---------------------:|-------------------------:|----------------------------:|-------------------------:|
| aum_outflow_pct_90d            |                    0.053 |                       0.056 |                    0.058 |                0.093 |                   0.114 |                0.150 |                    2.699 |                       2.932 |                    3.394 |
| aum_vs_baseline_pct            |                    0.043 |                       0.045 |                    0.048 |                0.153 |                   0.177 |                0.220 |                    3.495 |                       4.011 |                    4.740 |
| deposit_balance_change_pct_90d |                    0.053 |                       0.055 |                    0.059 |                0.159 |                   0.206 |                0.255 |                    3.674 |                       4.134 |                    4.695 |
| deposit_balance_vs_6m_avg_pct  |                    0.054 |                       0.056 |                    0.059 |                0.214 |                   0.257 |                0.304 |                    3.597 |                       4.109 |                    4.454 |

## 1 · Estructura de las series

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| depósitos mes 0 = Paso 0 |  |  |  | OK |
| AUM mes 0 = Paso 0 |  |  |  | OK |
| depósitos > 0 en toda la serie | mín $1,010.82 |  |  | OK |
| AUM > 0 con inversiones | mín $79,228.66 |  |  | OK |
| flujos de AUM ≥ 0 |  |  |  | OK |
| índice TWR > 0 |  |  |  | OK |
| columnas declaradas con unidad |  |  |  | OK |

## 2 · NULL, rangos y dinero

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| aum_outflow_90d NULL ⇔ sin inversiones o < 3 meses |  |  |  | OK |
| aum_vs_baseline NULL ⇔ sin inversiones o < 7 meses |  |  |  | OK |
| deposit_change_90d NULL ⇔ < 6 meses o base < $10k | NULL por base baja: 4 |  |  | OK |
| deposit_vs_6m NULL ⇔ < 7 meses o base < $10k |  |  |  | OK |
| cambios % > −100% |  |  |  | OK |
| aum_outflow_pct ≥ 0 | máx 11.229 |  |  | OK |
| USD válido: aum_outflow_30d | máx $97,512,617 |  |  | OK |
| USD válido: aum_outflow_90d | máx $423,166,431 |  |  | OK |

## 3 · Calibración (tasa de alerta, IV, monotonía)

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| tasa de alerta aum_outflow_pct_90d | 0.060 en [0.04, 0.16] |  |  | OK |
| IV aum_outflow_pct_90d | 0.134 en [0.1, 0.3] |  |  | OK |
| tendencia creciente del riesgo (Cochran-Armitage) aum_outflow_pct_90d | z = 8.6 (ρ tramos 0.56) |  |  | OK |
| lift del grupo en alerta ≥ 1.5: aum_outflow_pct_90d | lift = 3.01 |  |  | OK |
| tasa de alerta deposit_balance_change_pct_90d | 0.058 en [0.04, 0.16] |  |  | OK |
| IV deposit_balance_change_pct_90d | 0.248 en [0.1, 0.3] |  |  | OK |
| tendencia creciente del riesgo (Cochran-Armitage) deposit_balance_change_pct_90d | z = 11.2 (ρ tramos 0.50) |  |  | OK |
| lift del grupo en alerta ≥ 1.5: deposit_balance_change_pct_90d | lift = 4.10 |  |  | OK |
| tasa de alerta aum_vs_baseline_pct | 0.048 en [0.04, 0.16] |  |  | OK |
| IV aum_vs_baseline_pct | 0.175 en [0.1, 0.3] |  |  | OK |
| tendencia creciente del riesgo (Cochran-Armitage) aum_vs_baseline_pct | z = 8.7 (ρ tramos 0.36) |  |  | OK |
| lift del grupo en alerta ≥ 1.5: aum_vs_baseline_pct | lift = 4.12 |  |  | OK |
| tasa de alerta deposit_balance_vs_6m_avg_pct | 0.059 en [0.04, 0.16] |  |  | OK |
| IV deposit_balance_vs_6m_avg_pct | 0.267 en [0.1, 0.3] |  |  | OK |
| tendencia creciente del riesgo (Cochran-Armitage) deposit_balance_vs_6m_avg_pct | z = 12.7 (ρ tramos 0.65) |  |  | OK |
| lift del grupo en alerta ≥ 1.5: deposit_balance_vs_6m_avg_pct | lift = 4.10 |  |  | OK |
| IV mediano entre semillas en banda: aum_outflow_pct_90d | mediana 0.114 (p10–p90 0.095–0.131) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: aum_outflow_pct_90d | 0.053–0.058 |  |  | OK |
| IV mediano entre semillas en banda: deposit_balance_change_pct_90d | mediana 0.206 (p10–p90 0.172–0.230) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: deposit_balance_change_pct_90d | 0.053–0.059 |  |  | OK |
| IV mediano entre semillas en banda: aum_vs_baseline_pct | mediana 0.177 (p10–p90 0.158–0.215) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: aum_vs_baseline_pct | 0.043–0.048 |  |  | OK |
| IV mediano entre semillas en banda: deposit_balance_vs_6m_avg_pct | mediana 0.257 (p10–p90 0.229–0.290) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: deposit_balance_vs_6m_avg_pct | 0.054–0.059 |  |  | OK |

## 4 · Pruebas estadísticas

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| KS ruido de depósitos ~ t(6) estandarizada | D = 0.0011; n = 352,751 | 0.798 | 0.865 | OK |
| ν recuperado por MLE ≈ 6 | ν̂ = 6.00; escala 0.8160 |  |  | OK |
| curtosis del ruido ≈ 6/(ν−4) | 2.98 vs 3.00 |  |  | OK |
| episodio ⟂ ε dado z_outflow (Wald) | coef ε = -0.024 ± 0.062; coef z = +1.42 | 0.701 | 0.865 | OK |
| pendiente del episodio recuperada | 1.423 vs 1.4 |  |  | OK |
| choque de liquidez ⟂ ε | ρ = -0.0019 | 0.787 | 0.865 | OK |
| choque de liquidez ⟂ índice de riesgo | ρ = +0.0012 | 0.865 | 0.865 | OK |
| ε por diseño vía mudanza: aum_outflow_pct_30d | ρ = -0.0037 |  |  | OK |
| ε por diseño vía mudanza: aum_outflow_pct_90d | ρ = +0.0194 |  |  | OK |
| ε por diseño vía mudanza: deposit_balance_change_pct_30d | ρ = +0.0099 |  |  | OK |
| ε por diseño vía mudanza: deposit_balance_change_pct_90d | ρ = -0.0291 |  |  | OK |
| ε por diseño vía mudanza: deposit_balance_change_pct_180d | ρ = -0.0429 |  |  | OK |
| ε por diseño vía mudanza: aum_vs_baseline_pct | ρ = -0.0381 |  |  | OK |
| ε por diseño vía mudanza: deposit_balance_vs_6m_avg_pct | ρ = -0.0335 |  |  | OK |
| AUC combinado < AUC techo | 0.621 vs techo 0.851 |  |  | OK |

## Distribuciones

|                                 |       count |         mean |            std |     min |      1% |      5% |     25% |     50% |         75% |          95% |            99% |              max |
|:--------------------------------|------------:|-------------:|---------------:|--------:|--------:|--------:|--------:|--------:|------------:|-------------:|---------------:|-----------------:|
| aum_outflow_30d                 | 17,130.0000 |  92,592.7812 | 1,212,824.2079 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |      0.0000 | 226,832.7180 | 1,636,390.8464 |  97,512,616.9300 |
| aum_outflow_pct_30d             | 17,130.0000 |       0.0119 |         0.0968 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |      0.0000 |       0.0428 |         0.1991 |           6.3490 |
| aum_outflow_90d                 | 17,103.0000 | 361,221.6516 | 4,428,119.4210 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 | 42,822.4650 | 763,962.8270 | 6,053,369.1822 | 423,166,431.0100 |
| aum_outflow_pct_90d             | 17,103.0000 |       0.0357 |         0.1928 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |      0.0118 |       0.1545 |         0.7222 |          11.2286 |
| deposit_balance_change_pct_30d  | 19,980.0000 |      -0.0062 |         0.0706 | -0.9043 | -0.2756 | -0.1108 | -0.0320 | -0.0003 |      0.0306 |       0.0834 |         0.1381 |           0.8717 |
| deposit_balance_change_pct_90d  | 19,890.0000 |      -0.0240 |         0.1413 | -0.9710 | -0.6486 | -0.2914 | -0.0564 | -0.0014 |      0.0480 |       0.1289 |         0.1968 |           0.5502 |
| deposit_balance_change_pct_180d | 19,587.0000 |      -0.0244 |         0.1617 | -0.9710 | -0.6453 | -0.3279 | -0.0844 | -0.0055 |      0.0700 |       0.1827 |         0.2877 |           0.6893 |
| aum_vs_baseline_pct             | 16,999.0000 |      -0.0215 |         0.0947 | -0.9200 | -0.5195 | -0.1910 | -0.0131 | -0.0016 |      0.0071 |       0.0404 |         0.0841 |           0.3508 |
| deposit_balance_vs_6m_avg_pct   | 19,843.0000 |      -0.0299 |         0.1557 | -0.9961 | -0.6979 | -0.3450 | -0.0657 | -0.0041 |      0.0528 |       0.1388 |         0.2120 |           1.0525 |

## Correlación de Spearman entre variables

|                                |   aum_outflow_pct_90d |   deposit_balance_change_pct_90d |   aum_vs_baseline_pct |   deposit_balance_vs_6m_avg_pct |
|:-------------------------------|----------------------:|---------------------------------:|----------------------:|--------------------------------:|
| aum_outflow_pct_90d            |                 1.000 |                           -0.175 |                -0.743 |                          -0.192 |
| deposit_balance_change_pct_90d |                -0.175 |                            1.000 |                 0.191 |                           0.883 |
| aum_vs_baseline_pct            |                -0.743 |                            0.191 |                 1.000 |                           0.218 |
| deposit_balance_vs_6m_avg_pct  |                -0.192 |                            0.883 |                 0.218 |                           1.000 |

## WoE · aum_outflow_pct_90d

| row_0                    |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:-------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0                   |  9,214.0000 | 533.0000 |        0.0547 | -0.1084 | 0.0055 |
| 01 [5.709e-05, 0.004311] |    763.0000 |  44.0000 |        0.0545 | -0.1017 | 0.0004 |
| 02 [0.004323, 0.006827]  |    769.0000 |  37.0000 |        0.0459 | -0.2807 | 0.0028 |
| 03 [0.006829, 0.009559]  |    754.0000 |  52.0000 |        0.0645 |  0.0755 | 0.0002 |
| 04 [0.009561, 0.01283]   |    768.0000 |  38.0000 |        0.0471 | -0.2531 | 0.0023 |
| 05 [0.01283, 0.01738]    |    765.0000 |  41.0000 |        0.0509 | -0.1741 | 0.0011 |
| 06 [0.01738, 0.0245]     |    759.0000 |  47.0000 |        0.0583 | -0.0312 | 0.0000 |
| 07 [0.0245, 0.03879]     |    755.0000 |  51.0000 |        0.0633 |  0.0549 | 0.0001 |
| 08 [0.03883, 0.1699]     |    757.0000 |  49.0000 |        0.0608 |  0.0126 | 0.0000 |
| 09 [0.1701, 11.23]       |    654.0000 | 153.0000 |        0.1896 |  1.2905 | 0.1191 |
| NULL                     |  2,719.0000 | 155.0000 |        0.0539 | -0.1209 | 0.0020 |

## WoE · deposit_balance_change_pct_90d

| row_0                    |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:-------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-0.971, -0.1314]     |  1,655.0000 | 322.0000 |        0.1629 |  1.1049 | 0.1977 |
| 01 [-0.1313, -0.07232]   |  1,869.0000 | 108.0000 |        0.0546 | -0.1060 | 0.0011 |
| 02 [-0.07228, -0.04359]  |  1,877.0000 |  99.0000 |        0.0501 | -0.1968 | 0.0035 |
| 03 [-0.04356, -0.02125]  |  1,892.0000 |  85.0000 |        0.0430 | -0.3564 | 0.0108 |
| 04 [-0.02124, -0.001393] |  1,882.0000 |  95.0000 |        0.0481 | -0.2405 | 0.0052 |
| 05 [-0.001372, 0.01708]  |  1,869.0000 | 107.0000 |        0.0541 | -0.1152 | 0.0013 |
| 06 [0.01709, 0.03685]    |  1,875.0000 | 102.0000 |        0.0516 | -0.1661 | 0.0026 |
| 07 [0.03687, 0.06085]    |  1,888.0000 |  88.0000 |        0.0445 | -0.3198 | 0.0089 |
| 08 [0.06086, 0.09777]    |  1,894.0000 |  83.0000 |        0.0420 | -0.3812 | 0.0123 |
| 09 [0.09779, 0.5502]     |  1,876.0000 | 101.0000 |        0.0511 | -0.1764 | 0.0029 |
| NULL                     |    100.0000 |  10.0000 |        0.0909 |  0.4819 | 0.0016 |

## WoE · aum_vs_baseline_pct

| row_0                     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:--------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-0.92, -0.04434]      |  1,429.0000 | 261.0000 |        0.1544 |  1.0420 | 0.1463 |
| 01 [-0.04433, -0.01753]   |  1,599.0000 |  91.0000 |        0.0538 | -0.1204 | 0.0012 |
| 02 [-0.01749, -0.00967]   |  1,600.0000 |  90.0000 |        0.0533 | -0.1320 | 0.0014 |
| 03 [-0.009668, -0.005249] |  1,601.0000 |  89.0000 |        0.0527 | -0.1438 | 0.0017 |
| 04 [-0.005249, -0.001649] |  1,613.0000 |  77.0000 |        0.0456 | -0.2952 | 0.0065 |
| 05 [-0.001649, 0]         |  1,615.0000 |  74.0000 |        0.0438 | -0.3359 | 0.0083 |
| 06 [0, 0.003631]          |  1,601.0000 |  89.0000 |        0.0527 | -0.1438 | 0.0017 |
| 07 [0.003632, 0.01142]    |  1,604.0000 |  86.0000 |        0.0509 | -0.1797 | 0.0025 |
| 08 [0.01143, 0.02481]     |  1,606.0000 |  84.0000 |        0.0497 | -0.2044 | 0.0032 |
| 09 [0.02483, 0.3508]      |  1,595.0000 |  95.0000 |        0.0562 | -0.0751 | 0.0005 |
| NULL                      |  2,814.0000 | 164.0000 |        0.0551 | -0.0989 | 0.0014 |

## WoE · deposit_balance_vs_6m_avg_pct

| row_0                    |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:-------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-0.9961, -0.1604]    |  1,643.0000 | 329.0000 |        0.1668 |  1.1337 | 0.2101 |
| 01 [-0.1604, -0.08456]   |  1,856.0000 | 116.0000 |        0.0588 | -0.0279 | 0.0001 |
| 02 [-0.08456, -0.05055]  |  1,882.0000 |  90.0000 |        0.0456 | -0.2943 | 0.0076 |
| 03 [-0.05054, -0.0256]   |  1,864.0000 | 108.0000 |        0.0548 | -0.1033 | 0.0010 |
| 04 [-0.02558, -0.004068] |  1,876.0000 |  96.0000 |        0.0487 | -0.2269 | 0.0046 |
| 05 [-0.004057, 0.01763]  |  1,881.0000 |  91.0000 |        0.0461 | -0.2828 | 0.0070 |
| 06 [0.01763, 0.04036]    |  1,871.0000 | 101.0000 |        0.0512 | -0.1737 | 0.0028 |
| 07 [0.04037, 0.06761]    |  1,894.0000 |  78.0000 |        0.0396 | -0.4429 | 0.0161 |
| 08 [0.06762, 0.1067]     |  1,875.0000 |  97.0000 |        0.0492 | -0.2161 | 0.0042 |
| 09 [0.1067, 1.053]       |  1,890.0000 |  82.0000 |        0.0416 | -0.3911 | 0.0128 |
| NULL                     |    145.0000 |  12.0000 |        0.0764 |  0.2862 | 0.0007 |

## Diccionario

| Columna | Unidad | Descripción |
|---|---|---|
| household_id | id | Identificador del hogar |
| aum_outflow_30d | USD | #1 · max(0, retiros − aportes) de inversión, último mes; NULL sin inversiones |
| aum_outflow_pct_30d | fracción | #1 · aum_outflow_30d ÷ AUM promedio de la ventana |
| aum_outflow_90d | USD | #1 · max(0, retiros − aportes) de inversión, últimos 3 meses |
| aum_outflow_pct_90d | fracción | #1 · aum_outflow_90d ÷ AUM promedio (alerta > 10%) |
| deposit_balance_change_pct_30d | fracción | #2 · media último mes ÷ mes previo − 1 |
| deposit_balance_change_pct_90d | fracción | #2 · media 3m ÷ 3m previos − 1 (alerta ≤ −25%); NULL si base < $10k |
| deposit_balance_change_pct_180d | fracción | #2 · media 6m ÷ 6m previos − 1 |
| aum_vs_baseline_pct | fracción | #17 · AUM ex-mercado t ÷ media meses −6..−1 − 1 (alerta ≤ −20%) |
| deposit_balance_vs_6m_avg_pct | fracción | #18 · depósitos último mes ÷ media meses −6..−1 − 1 (alerta ≤ −30%) |
