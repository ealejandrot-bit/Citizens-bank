# Paso 1 · Balances & AUM

Semilla `20260928` · 20,000 hogares × 24 meses · montos en USD · **54 de 54 pruebas OK** (α = 0.01, Benjamini-Hochberg)

## Calibración

| variable                       | alerta   |   tasa_alerta | rango_tasa   |   IV_hard |   IV_soft | banda_IV   |   tendencia_z |   tendencia_p |   lift_alerta |   spearman_tramos |   null_% |
|:-------------------------------|:---------|--------------:|:-------------|----------:|----------:|:-----------|--------------:|--------------:|--------------:|------------------:|---------:|
| aum_outflow_pct_90d            | > 0.10   |         0.077 | [0.04, 0.16] |     0.266 |     0.067 | [0.1, 0.3] |        14.203 |         0.000 |         3.957 |             0.588 |   14.459 |
| deposit_balance_change_pct_90d | <= -0.25 |         0.105 | [0.04, 0.16] |     0.251 |     0.051 | [0.1, 0.3] |        12.825 |         0.000 |         3.166 |             0.661 |    0.553 |
| aum_vs_baseline_pct            | <= -0.20 |         0.062 | [0.04, 0.16] |     0.291 |     0.069 | [0.1, 0.3] |        11.900 |         0.000 |         5.178 |             0.384 |   14.982 |
| deposit_balance_vs_6m_avg_pct  | <= -0.30 |         0.099 | [0.04, 0.16] |     0.289 |     0.066 | [0.1, 0.3] |        13.524 |         0.000 |         3.618 |             0.830 |    0.795 |

AUC combinado de las 4 variables (logística): **0.631**; techo con la probabilidad verdadera: 0.851.

## Robustez en 20 semillas de referencia

| variable                       |   ('tasa_alerta', 'min') |   ('tasa_alerta', 'median') |   ('tasa_alerta', 'max') |   ('IV_hard', 'min') |   ('IV_hard', 'median') |   ('IV_hard', 'max') |   ('lift_alerta', 'min') |   ('lift_alerta', 'median') |   ('lift_alerta', 'max') |
|:-------------------------------|-------------------------:|----------------------------:|-------------------------:|---------------------:|------------------------:|---------------------:|-------------------------:|----------------------------:|-------------------------:|
| aum_outflow_pct_90d            |                    0.071 |                       0.072 |                    0.076 |                0.232 |                   0.272 |                0.342 |                    3.823 |                       4.118 |                    4.550 |
| aum_vs_baseline_pct            |                    0.057 |                       0.059 |                    0.062 |                0.227 |                   0.283 |                0.354 |                    4.387 |                       4.895 |                    5.828 |
| deposit_balance_change_pct_90d |                    0.099 |                       0.103 |                    0.107 |                0.192 |                   0.229 |                0.264 |                    2.747 |                       3.011 |                    3.347 |
| deposit_balance_vs_6m_avg_pct  |                    0.094 |                       0.099 |                    0.103 |                0.225 |                   0.277 |                0.340 |                    3.247 |                       3.508 |                    3.942 |

## 1 · Estructura de las series

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| depósitos mes 0 = Paso 0 |  |  |  | OK |
| AUM mes 0 = Paso 0 |  |  |  | OK |
| depósitos > 0 en toda la serie | mín $708.87 |  |  | OK |
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
| aum_outflow_pct ≥ 0 | máx 7.641 |  |  | OK |
| USD válido: aum_outflow_30d | máx $462,881,697 |  |  | OK |
| USD válido: aum_outflow_90d | máx $462,881,697 |  |  | OK |

## 3 · Calibración (tasa de alerta, IV, monotonía)

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| tasa de alerta aum_outflow_pct_90d | 0.077 en [0.04, 0.16] |  |  | OK |
| IV aum_outflow_pct_90d | 0.266 en [0.1, 0.3] |  |  | OK |
| tendencia creciente del riesgo (Cochran-Armitage) aum_outflow_pct_90d | z = 14.2 (ρ tramos 0.59) |  |  | OK |
| lift del grupo en alerta ≥ 1.5: aum_outflow_pct_90d | lift = 3.96 |  |  | OK |
| tasa de alerta deposit_balance_change_pct_90d | 0.105 en [0.04, 0.16] |  |  | OK |
| IV deposit_balance_change_pct_90d | 0.251 en [0.1, 0.3] |  |  | OK |
| tendencia creciente del riesgo (Cochran-Armitage) deposit_balance_change_pct_90d | z = 12.8 (ρ tramos 0.66) |  |  | OK |
| lift del grupo en alerta ≥ 1.5: deposit_balance_change_pct_90d | lift = 3.17 |  |  | OK |
| tasa de alerta aum_vs_baseline_pct | 0.062 en [0.04, 0.16] |  |  | OK |
| IV aum_vs_baseline_pct | 0.291 en [0.1, 0.3] |  |  | OK |
| tendencia creciente del riesgo (Cochran-Armitage) aum_vs_baseline_pct | z = 11.9 (ρ tramos 0.38) |  |  | OK |
| lift del grupo en alerta ≥ 1.5: aum_vs_baseline_pct | lift = 5.18 |  |  | OK |
| tasa de alerta deposit_balance_vs_6m_avg_pct | 0.099 en [0.04, 0.16] |  |  | OK |
| IV deposit_balance_vs_6m_avg_pct | 0.289 en [0.1, 0.3] |  |  | OK |
| tendencia creciente del riesgo (Cochran-Armitage) deposit_balance_vs_6m_avg_pct | z = 13.5 (ρ tramos 0.83) |  |  | OK |
| lift del grupo en alerta ≥ 1.5: deposit_balance_vs_6m_avg_pct | lift = 3.62 |  |  | OK |
| IV mediano entre semillas en banda: aum_outflow_pct_90d | mediana 0.272 (p10–p90 0.238–0.326) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: aum_outflow_pct_90d | 0.071–0.076 |  |  | OK |
| IV mediano entre semillas en banda: deposit_balance_change_pct_90d | mediana 0.229 (p10–p90 0.195–0.246) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: deposit_balance_change_pct_90d | 0.099–0.107 |  |  | OK |
| IV mediano entre semillas en banda: aum_vs_baseline_pct | mediana 0.283 (p10–p90 0.252–0.333) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: aum_vs_baseline_pct | 0.057–0.062 |  |  | OK |
| IV mediano entre semillas en banda: deposit_balance_vs_6m_avg_pct | mediana 0.277 (p10–p90 0.248–0.308) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: deposit_balance_vs_6m_avg_pct | 0.094–0.103 |  |  | OK |

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
| ε por diseño vía mudanza: aum_outflow_pct_30d | ρ = +0.0317 |  |  | OK |
| ε por diseño vía mudanza: aum_outflow_pct_90d | ρ = +0.0502 |  |  | OK |
| ε por diseño vía mudanza: deposit_balance_change_pct_30d | ρ = -0.0247 |  |  | OK |
| ε por diseño vía mudanza: deposit_balance_change_pct_90d | ρ = -0.0406 |  |  | OK |
| ε por diseño vía mudanza: deposit_balance_change_pct_180d | ρ = -0.0209 |  |  | OK |
| ε por diseño vía mudanza: aum_vs_baseline_pct | ρ = -0.0550 |  |  | OK |
| ε por diseño vía mudanza: deposit_balance_vs_6m_avg_pct | ρ = -0.0413 |  |  | OK |
| AUC combinado < AUC techo | 0.631 vs techo 0.851 |  |  | OK |

## Distribuciones

|                                 |       count |         mean |            std |     min |      1% |      5% |     25% |     50% |         75% |            95% |             99% |              max |
|:--------------------------------|------------:|-------------:|---------------:|--------:|--------:|--------:|--------:|--------:|------------:|---------------:|----------------:|-----------------:|
| aum_outflow_30d                 | 17,130.0000 | 365,745.9744 | 6,588,537.7959 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |      0.0000 |   409,985.6110 |  5,064,140.5729 | 462,881,697.4200 |
| aum_outflow_pct_30d             | 17,130.0000 |       0.0386 |         0.2844 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |      0.0000 |         0.0742 |          1.1151 |           9.0071 |
| aum_outflow_90d                 | 17,103.0000 | 640,720.7646 | 7,361,740.2878 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 | 48,786.6750 | 1,321,523.5920 | 11,978,046.7712 | 462,881,697.4200 |
| aum_outflow_pct_90d             | 17,103.0000 |       0.0493 |         0.2142 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |      0.0129 |         0.2729 |          0.9955 |           7.6408 |
| deposit_balance_change_pct_30d  | 19,979.0000 |      -0.0094 |         0.1494 | -0.9265 | -0.4843 | -0.2348 | -0.0819 | -0.0055 |      0.0699 |         0.2074 |          0.3585 |           3.4891 |
| deposit_balance_change_pct_90d  | 19,890.0000 |      -0.0127 |         0.2168 | -0.9755 | -0.6354 | -0.3659 | -0.1320 | -0.0105 |      0.1094 |         0.3282 |          0.5243 |           1.8394 |
| deposit_balance_change_pct_180d | 19,587.0000 |       0.0066 |         0.2756 | -0.9440 | -0.5785 | -0.3970 | -0.1753 | -0.0154 |      0.1640 |         0.4742 |          0.8026 |           2.6592 |
| aum_vs_baseline_pct             | 16,999.0000 |      -0.0292 |         0.1172 | -0.9449 | -0.6364 | -0.2497 | -0.0137 | -0.0018 |      0.0069 |         0.0402 |          0.0839 |           0.3508 |
| deposit_balance_vs_6m_avg_pct   | 19,842.0000 |      -0.0249 |         0.2455 | -0.9967 | -0.7648 | -0.4439 | -0.1535 | -0.0191 |      0.1182 |         0.3443 |          0.5516 |           4.5317 |

## Correlación de Spearman entre variables

|                                |   aum_outflow_pct_90d |   deposit_balance_change_pct_90d |   aum_vs_baseline_pct |   deposit_balance_vs_6m_avg_pct |
|:-------------------------------|----------------------:|---------------------------------:|----------------------:|--------------------------------:|
| aum_outflow_pct_90d            |                 1.000 |                           -0.185 |                -0.768 |                          -0.210 |
| deposit_balance_change_pct_90d |                -0.185 |                            1.000 |                 0.190 |                           0.883 |
| aum_vs_baseline_pct            |                -0.768 |                            0.190 |                 1.000 |                           0.214 |
| deposit_balance_vs_6m_avg_pct  |                -0.210 |                            0.883 |                 0.214 |                           1.000 |

## WoE · aum_outflow_pct_90d

| row_0                    |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:-------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0                   |  9,088.0000 | 471.0000 |        0.0493 | -0.2182 | 0.0208 |
| 01 [5.709e-05, 0.004419] |    786.0000 |  42.0000 |        0.0507 | -0.1774 | 0.0012 |
| 02 [0.004419, 0.00703]   |    789.0000 |  38.0000 |        0.0459 | -0.2800 | 0.0029 |
| 03 [0.007037, 0.009897]  |    777.0000 |  50.0000 |        0.0605 |  0.0066 | 0.0000 |
| 04 [0.009898, 0.01354]   |    795.0000 |  32.0000 |        0.0387 | -0.4570 | 0.0071 |
| 05 [0.01354, 0.01863]    |    778.0000 |  49.0000 |        0.0593 | -0.0147 | 0.0000 |
| 06 [0.01864, 0.02676]    |    793.0000 |  34.0000 |        0.0411 | -0.3948 | 0.0055 |
| 07 [0.02677, 0.04824]    |    775.0000 |  52.0000 |        0.0629 |  0.0480 | 0.0001 |
| 08 [0.04829, 0.2814]     |    752.0000 |  75.0000 |        0.0907 |  0.4414 | 0.0099 |
| 09 [0.2824, 7.641]       |    625.0000 | 202.0000 |        0.2443 |  1.6129 | 0.2169 |
| NULL                     |  2,719.0000 | 155.0000 |        0.0539 | -0.1209 | 0.0020 |

## WoE · deposit_balance_change_pct_90d

| row_0                   |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-0.9755, -0.2569]   |  1,662.0000 | 315.0000 |        0.1593 |  1.0788 | 0.1863 |
| 01 [-0.2566, -0.1635]   |  1,841.0000 | 136.0000 |        0.0688 |  0.1387 | 0.0020 |
| 02 [-0.1635, -0.1051]   |  1,866.0000 | 110.0000 |        0.0557 | -0.0861 | 0.0007 |
| 03 [-0.1051, -0.05615]  |  1,898.0000 |  79.0000 |        0.0400 | -0.4324 | 0.0154 |
| 04 [-0.05615, -0.01041] |  1,876.0000 | 101.0000 |        0.0511 | -0.1764 | 0.0029 |
| 05 [-0.0104, 0.03327]   |  1,877.0000 |  99.0000 |        0.0501 | -0.1968 | 0.0035 |
| 06 [0.03331, 0.08214]   |  1,886.0000 |  91.0000 |        0.0460 | -0.2854 | 0.0072 |
| 07 [0.0822, 0.1428]     |  1,895.0000 |  81.0000 |        0.0410 | -0.4059 | 0.0137 |
| 08 [0.1428, 0.2415]     |  1,893.0000 |  84.0000 |        0.0425 | -0.3687 | 0.0115 |
| 09 [0.2415, 1.839]      |  1,883.0000 |  94.0000 |        0.0475 | -0.2516 | 0.0056 |
| NULL                    |    100.0000 |  10.0000 |        0.0909 |  0.4819 | 0.0016 |

## WoE · aum_vs_baseline_pct

| row_0                     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:--------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-0.9449, -0.05761]    |  1,375.0000 | 315.0000 |        0.1864 |  1.2683 | 0.2386 |
| 01 [-0.0575, -0.01846]    |  1,599.0000 |  91.0000 |        0.0538 | -0.1204 | 0.0012 |
| 02 [-0.01846, -0.01015]   |  1,608.0000 |  82.0000 |        0.0485 | -0.2296 | 0.0041 |
| 03 [-0.01014, -0.005442]  |  1,608.0000 |  82.0000 |        0.0485 | -0.2296 | 0.0041 |
| 04 [-0.005442, -0.001826] |  1,620.0000 |  70.0000 |        0.0414 | -0.3942 | 0.0111 |
| 05 [-0.001826, 0]         |  1,624.0000 |  65.0000 |        0.0385 | -0.4702 | 0.0153 |
| 06 [0, 0.00343]           |  1,607.0000 |  83.0000 |        0.0491 | -0.2169 | 0.0036 |
| 07 [0.003437, 0.01124]    |  1,610.0000 |  80.0000 |        0.0473 | -0.2553 | 0.0050 |
| 08 [0.01126, 0.02464]     |  1,610.0000 |  80.0000 |        0.0473 | -0.2553 | 0.0050 |
| 09 [0.02464, 0.3508]      |  1,602.0000 |  88.0000 |        0.0521 | -0.1556 | 0.0019 |
| NULL                      |  2,814.0000 | 164.0000 |        0.0551 | -0.0989 | 0.0014 |

## WoE · deposit_balance_vs_6m_avg_pct

| row_0                   |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-0.9967, -0.2985]   |  1,633.0000 | 339.0000 |        0.1719 |  1.1697 | 0.2271 |
| 01 [-0.2984, -0.1894]   |  1,859.0000 | 113.0000 |        0.0573 | -0.0556 | 0.0003 |
| 02 [-0.1894, -0.1225]   |  1,876.0000 |  96.0000 |        0.0487 | -0.2269 | 0.0046 |
| 03 [-0.1224, -0.06815]  |  1,861.0000 | 111.0000 |        0.0563 | -0.0744 | 0.0005 |
| 04 [-0.06811, -0.01904] |  1,878.0000 |  94.0000 |        0.0477 | -0.2489 | 0.0055 |
| 05 [-0.01903, 0.03199]  |  1,885.0000 |  86.0000 |        0.0436 | -0.3411 | 0.0099 |
| 06 [0.03201, 0.08688]   |  1,874.0000 |  98.0000 |        0.0497 | -0.2053 | 0.0038 |
| 07 [0.08691, 0.1551]    |  1,896.0000 |  76.0000 |        0.0385 | -0.4698 | 0.0179 |
| 08 [0.1551, 0.2571]     |  1,881.0000 |  91.0000 |        0.0461 | -0.2828 | 0.0070 |
| 09 [0.2571, 4.532]      |  1,888.0000 |  84.0000 |        0.0426 | -0.3661 | 0.0113 |
| NULL                    |    146.0000 |  12.0000 |        0.0759 |  0.2794 | 0.0007 |

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
