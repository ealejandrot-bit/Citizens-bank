# Paso 1 · Balances & AUM

Semilla `20260928` · 20,000 hogares × 24 meses · montos en USD · **50 de 50 pruebas OK** (α = 0.01, Benjamini-Hochberg)

## Calibración

| variable                       | alerta   |   tasa_alerta | rango_tasa   |   IV_hard |   IV_soft | banda_IV   |   tendencia_z |   tendencia_p |   lift_alerta |   spearman_tramos |   null_% |
|:-------------------------------|:---------|--------------:|:-------------|----------:|----------:|:-----------|--------------:|--------------:|--------------:|------------------:|---------:|
| aum_outflow_pct_90d            | > 0.10   |         0.135 | [0.06, 0.16] |     0.165 |     0.076 | [0.1, 0.3] |        12.663 |         0.000 |         2.530 |             0.782 |   14.459 |
| deposit_balance_change_pct_90d | <= -0.25 |         0.097 | [0.06, 0.14] |     0.149 |     0.066 | [0.1, 0.3] |        10.733 |         0.000 |         2.451 |             0.842 |    0.553 |
| aum_vs_baseline_pct            | <= -0.20 |         0.084 | [0.05, 0.12] |     0.146 |     0.065 | [0.1, 0.3] |         9.377 |         0.000 |         2.492 |             0.479 |   14.982 |
| deposit_balance_vs_6m_avg_pct  | <= -0.30 |         0.107 | [0.05, 0.14] |     0.168 |     0.080 | [0.1, 0.3] |        11.399 |         0.000 |         2.453 |             0.794 |    0.790 |

AUC combinado de las 4 variables (logística): **0.602**; techo con la probabilidad verdadera: 0.851.

## Robustez en 20 semillas de referencia

| variable                       |   ('tasa_alerta', 'min') |   ('tasa_alerta', 'median') |   ('tasa_alerta', 'max') |   ('IV_hard', 'min') |   ('IV_hard', 'median') |   ('IV_hard', 'max') |   ('lift_alerta', 'min') |   ('lift_alerta', 'median') |   ('lift_alerta', 'max') |
|:-------------------------------|-------------------------:|----------------------------:|-------------------------:|---------------------:|------------------------:|---------------------:|-------------------------:|----------------------------:|-------------------------:|
| aum_outflow_pct_90d            |                    0.129 |                       0.133 |                    0.138 |                0.148 |                   0.198 |                0.239 |                    2.530 |                       2.779 |                    2.996 |
| aum_vs_baseline_pct            |                    0.078 |                       0.082 |                    0.086 |                0.136 |                   0.180 |                0.232 |                    2.186 |                       2.546 |                    2.830 |
| deposit_balance_change_pct_90d |                    0.093 |                       0.097 |                    0.100 |                0.133 |                   0.176 |                0.199 |                    2.237 |                       2.676 |                    2.861 |
| deposit_balance_vs_6m_avg_pct  |                    0.104 |                       0.107 |                    0.112 |                0.163 |                   0.200 |                0.236 |                    2.350 |                       2.710 |                    2.927 |

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
| aum_outflow_pct ≥ 0 | máx 2.085 |  |  | OK |
| USD válido: aum_outflow_30d | máx $91,788,313 |  |  | OK |
| USD válido: aum_outflow_90d | máx $399,421,814 |  |  | OK |

## 3 · Calibración (tasa de alerta, IV, monotonía)

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| tasa de alerta aum_outflow_pct_90d | 0.135 en [0.06, 0.16] |  |  | OK |
| IV aum_outflow_pct_90d | 0.165 en [0.1, 0.3] |  |  | OK |
| tendencia creciente del riesgo (Cochran-Armitage) aum_outflow_pct_90d | z = 12.7 (ρ tramos 0.78) |  |  | OK |
| lift del grupo en alerta ≥ 1.5: aum_outflow_pct_90d | lift = 2.53 |  |  | OK |
| tasa de alerta deposit_balance_change_pct_90d | 0.097 en [0.06, 0.14] |  |  | OK |
| IV deposit_balance_change_pct_90d | 0.149 en [0.1, 0.3] |  |  | OK |
| tendencia creciente del riesgo (Cochran-Armitage) deposit_balance_change_pct_90d | z = 10.7 (ρ tramos 0.84) |  |  | OK |
| lift del grupo en alerta ≥ 1.5: deposit_balance_change_pct_90d | lift = 2.45 |  |  | OK |
| tasa de alerta aum_vs_baseline_pct | 0.084 en [0.05, 0.12] |  |  | OK |
| IV aum_vs_baseline_pct | 0.146 en [0.1, 0.3] |  |  | OK |
| tendencia creciente del riesgo (Cochran-Armitage) aum_vs_baseline_pct | z = 9.4 (ρ tramos 0.48) |  |  | OK |
| lift del grupo en alerta ≥ 1.5: aum_vs_baseline_pct | lift = 2.49 |  |  | OK |
| tasa de alerta deposit_balance_vs_6m_avg_pct | 0.107 en [0.05, 0.14] |  |  | OK |
| IV deposit_balance_vs_6m_avg_pct | 0.168 en [0.1, 0.3] |  |  | OK |
| tendencia creciente del riesgo (Cochran-Armitage) deposit_balance_vs_6m_avg_pct | z = 11.4 (ρ tramos 0.79) |  |  | OK |
| lift del grupo en alerta ≥ 1.5: deposit_balance_vs_6m_avg_pct | lift = 2.45 |  |  | OK |
| IV en banda en todas las semillas: aum_outflow_pct_90d | IV 0.148–0.239 en 20 semillas |  |  | OK |
| alerta en rango en todas las semillas: aum_outflow_pct_90d | 0.129–0.138 |  |  | OK |
| IV en banda en todas las semillas: deposit_balance_change_pct_90d | IV 0.133–0.199 en 20 semillas |  |  | OK |
| alerta en rango en todas las semillas: deposit_balance_change_pct_90d | 0.093–0.100 |  |  | OK |
| IV en banda en todas las semillas: aum_vs_baseline_pct | IV 0.136–0.232 en 20 semillas |  |  | OK |
| alerta en rango en todas las semillas: aum_vs_baseline_pct | 0.078–0.086 |  |  | OK |
| IV en banda en todas las semillas: deposit_balance_vs_6m_avg_pct | IV 0.163–0.236 en 20 semillas |  |  | OK |
| alerta en rango en todas las semillas: deposit_balance_vs_6m_avg_pct | 0.104–0.112 |  |  | OK |

## 4 · Pruebas estadísticas

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| KS ruido de depósitos ~ t(6) estandarizada | D = 0.0011; n = 328,601 | 0.805 | 0.805 | OK |
| ν recuperado por MLE ≈ 6 | ν̂ = 5.96; escala 0.8154 |  |  | OK |
| curtosis del ruido ≈ 6/(ν−4) | 3.10 vs 3.00 |  |  | OK |
| sin fuga del riesgo no observable: aum_outflow_pct_30d ⟂ ε | ρ = -0.0076 | 0.322 | 0.516 | OK |
| sin fuga del riesgo no observable: aum_outflow_pct_90d ⟂ ε | ρ = -0.0020 | 0.794 | 0.805 | OK |
| sin fuga del riesgo no observable: deposit_balance_change_pct_30d ⟂ ε | ρ = +0.0094 | 0.184 | 0.368 | OK |
| sin fuga del riesgo no observable: deposit_balance_change_pct_90d ⟂ ε | ρ = +0.0117 | 0.1 | 0.267 | OK |
| sin fuga del riesgo no observable: deposit_balance_change_pct_180d ⟂ ε | ρ = +0.0132 | 0.0639 | 0.256 | OK |
| sin fuga del riesgo no observable: aum_vs_baseline_pct ⟂ ε | ρ = +0.0039 | 0.614 | 0.805 | OK |
| sin fuga del riesgo no observable: deposit_balance_vs_6m_avg_pct ⟂ ε | ρ = +0.0136 | 0.0549 | 0.256 | OK |
| AUC combinado < AUC techo | 0.602 vs techo 0.851 |  |  | OK |

## Distribuciones

|                                 |       count |         mean |            std |     min |      1% |      5% |     25% |     50% |         75% |            95% |            99% |              max |
|:--------------------------------|------------:|-------------:|---------------:|--------:|--------:|--------:|--------:|--------:|------------:|---------------:|---------------:|-----------------:|
| aum_outflow_30d                 | 17,130.0000 | 177,332.3421 | 1,288,850.8718 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 | 22,425.3600 |   730,783.0985 | 3,118,570.1586 |  91,788,313.2400 |
| aum_outflow_pct_30d             | 17,130.0000 |       0.0223 |         0.0805 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |      0.0070 |         0.1382 |         0.2862 |           5.6781 |
| aum_outflow_90d                 | 17,103.0000 | 504,274.9351 | 4,108,175.3085 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 | 91,224.9350 | 1,999,780.6240 | 8,820,670.9776 | 399,421,814.3300 |
| aum_outflow_pct_90d             | 17,103.0000 |       0.0534 |         0.1484 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |      0.0196 |         0.3399 |         0.7310 |           2.0853 |
| deposit_balance_change_pct_30d  | 19,980.0000 |      -0.0283 |         0.0994 | -0.9043 | -0.3905 | -0.2399 | -0.0486 | -0.0069 |      0.0266 |         0.0801 |         0.1353 |           0.8717 |
| deposit_balance_change_pct_90d  | 19,890.0000 |      -0.0452 |         0.1632 | -0.9837 | -0.6746 | -0.4211 | -0.0731 | -0.0094 |      0.0434 |         0.1257 |         0.1939 |           0.5502 |
| deposit_balance_change_pct_180d | 19,587.0000 |      -0.0319 |         0.1598 | -0.9377 | -0.5911 | -0.3407 | -0.0957 | -0.0124 |      0.0646 |         0.1782 |         0.2841 |           0.6453 |
| aum_vs_baseline_pct             | 16,999.0000 |      -0.0368 |         0.1089 | -0.9177 | -0.5044 | -0.2822 | -0.0196 | -0.0031 |      0.0054 |         0.0379 |         0.0819 |           0.3508 |
| deposit_balance_vs_6m_avg_pct   | 19,843.0000 |      -0.0597 |         0.1915 | -0.9987 | -0.7731 | -0.5052 | -0.0883 | -0.0128 |      0.0481 |         0.1354 |         0.2106 |           1.0525 |

## Correlación de Spearman entre variables

|                                |   aum_outflow_pct_90d |   deposit_balance_change_pct_90d |   aum_vs_baseline_pct |   deposit_balance_vs_6m_avg_pct |
|:-------------------------------|----------------------:|---------------------------------:|----------------------:|--------------------------------:|
| aum_outflow_pct_90d            |                 1.000 |                           -0.377 |                -0.827 |                          -0.413 |
| deposit_balance_change_pct_90d |                -0.377 |                            1.000 |                 0.363 |                           0.904 |
| aum_vs_baseline_pct            |                -0.827 |                            0.363 |                 1.000 |                           0.398 |
| deposit_balance_vs_6m_avg_pct  |                -0.413 |                            0.904 |                 0.398 |                           1.000 |

## WoE · aum_outflow_pct_90d

| row_0                    |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:-------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0                   |  8,416.0000 | 441.0000 |        0.0498 | -0.2071 | 0.0174 |
| 01 [5.709e-05, 0.004975] |    867.0000 |  39.0000 |        0.0430 | -0.3486 | 0.0048 |
| 02 [0.004977, 0.00815]   |    868.0000 |  37.0000 |        0.0409 | -0.4017 | 0.0062 |
| 03 [0.008152, 0.01201]   |    862.0000 |  43.0000 |        0.0475 | -0.2464 | 0.0025 |
| 04 [0.01201, 0.01738]    |    863.0000 |  42.0000 |        0.0464 | -0.2708 | 0.0030 |
| 05 [0.01738, 0.02673]    |    860.0000 |  45.0000 |        0.0497 | -0.1991 | 0.0017 |
| 06 [0.02674, 0.0546]     |    846.0000 |  59.0000 |        0.0652 |  0.0856 | 0.0003 |
| 07 [0.05468, 0.1652]     |    808.0000 |  97.0000 |        0.1072 |  0.6254 | 0.0235 |
| 08 [0.1653, 0.3268]      |    780.0000 | 125.0000 |        0.1381 |  0.9131 | 0.0569 |
| 09 [0.3269, 2.085]       |    788.0000 | 117.0000 |        0.1293 |  0.8370 | 0.0463 |
| NULL                     |  2,719.0000 | 155.0000 |        0.0539 | -0.1209 | 0.0020 |

## WoE · deposit_balance_change_pct_90d

| row_0                    |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:-------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-0.9837, -0.2413]    |  1,720.0000 | 257.0000 |        0.1300 |  0.8413 | 0.1022 |
| 01 [-0.2408, -0.09469]   |  1,830.0000 | 147.0000 |        0.0744 |  0.2222 | 0.0054 |
| 02 [-0.09467, -0.05663]  |  1,856.0000 | 120.0000 |        0.0607 |  0.0059 | 0.0000 |
| 03 [-0.05663, -0.03125]  |  1,871.0000 | 106.0000 |        0.0536 | -0.1257 | 0.0015 |
| 04 [-0.03123, -0.009374] |  1,888.0000 |  89.0000 |        0.0450 | -0.3086 | 0.0083 |
| 05 [-0.009354, 0.01106]  |  1,879.0000 |  97.0000 |        0.0491 | -0.2182 | 0.0043 |
| 06 [0.01107, 0.03194]    |  1,872.0000 | 105.0000 |        0.0531 | -0.1356 | 0.0017 |
| 07 [0.03195, 0.05694]    |  1,882.0000 |  94.0000 |        0.0476 | -0.2511 | 0.0056 |
| 08 [0.05696, 0.09439]    |  1,892.0000 |  85.0000 |        0.0430 | -0.3564 | 0.0108 |
| 09 [0.0944, 0.5502]      |  1,887.0000 |  90.0000 |        0.0455 | -0.2970 | 0.0077 |
| NULL                     |    100.0000 |  10.0000 |        0.0909 |  0.4819 | 0.0016 |

## WoE · aum_vs_baseline_pct

| row_0                     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:--------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-0.9177, -0.1655]     |  1,463.0000 | 227.0000 |        0.1343 |  0.8793 | 0.0971 |
| 01 [-0.1655, -0.02965]    |  1,548.0000 | 142.0000 |        0.0840 |  0.3550 | 0.0125 |
| 02 [-0.02965, -0.01406]   |  1,602.0000 |  88.0000 |        0.0521 | -0.1556 | 0.0019 |
| 03 [-0.01405, -0.007432]  |  1,605.0000 |  85.0000 |        0.0503 | -0.1920 | 0.0029 |
| 04 [-0.007412, -0.003159] |  1,610.0000 |  80.0000 |        0.0473 | -0.2553 | 0.0050 |
| 05 [-0.003158, -1.11e-16] |  1,611.0000 |  78.0000 |        0.0462 | -0.2811 | 0.0059 |
| 06 [-1.11e-16, 0.001968]  |  1,618.0000 |  72.0000 |        0.0426 | -0.3650 | 0.0097 |
| 07 [0.001969, 0.009688]   |  1,592.0000 |  98.0000 |        0.0580 | -0.0423 | 0.0001 |
| 08 [0.009689, 0.0229]     |  1,617.0000 |  73.0000 |        0.0432 | -0.3507 | 0.0090 |
| 09 [0.0229, 0.3508]       |  1,597.0000 |  93.0000 |        0.0550 | -0.0975 | 0.0008 |
| NULL                      |  2,814.0000 | 164.0000 |        0.0551 | -0.0989 | 0.0014 |

## WoE · deposit_balance_vs_6m_avg_pct

| row_0                   |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-0.9987, -0.3214]   |  1,719.0000 | 253.0000 |        0.1283 |  0.8263 | 0.0977 |
| 01 [-0.3213, -0.1172]   |  1,795.0000 | 177.0000 |        0.0898 |  0.4266 | 0.0218 |
| 02 [-0.1171, -0.06758]  |  1,873.0000 |  99.0000 |        0.0502 | -0.1947 | 0.0035 |
| 03 [-0.06758, -0.03702] |  1,876.0000 |  96.0000 |        0.0487 | -0.2269 | 0.0046 |
| 04 [-0.0369, -0.01282]  |  1,874.0000 |  98.0000 |        0.0497 | -0.2053 | 0.0038 |
| 05 [-0.01281, 0.01064]  |  1,867.0000 | 105.0000 |        0.0532 | -0.1330 | 0.0017 |
| 06 [0.01065, 0.03463]   |  1,870.0000 | 102.0000 |        0.0517 | -0.1634 | 0.0025 |
| 07 [0.03463, 0.06234]   |  1,888.0000 |  84.0000 |        0.0426 | -0.3661 | 0.0113 |
| 08 [0.06235, 0.1025]    |  1,878.0000 |  94.0000 |        0.0477 | -0.2489 | 0.0055 |
| 09 [0.1025, 1.053]      |  1,892.0000 |  80.0000 |        0.0406 | -0.4167 | 0.0144 |
| NULL                    |    145.0000 |  12.0000 |        0.0764 |  0.2862 | 0.0007 |

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
