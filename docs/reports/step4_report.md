# Paso 4 · Investments

Semilla `20260928` · 20,000 hogares (17,130 con inversiones) · montos en USD · **53 de 53 pruebas OK** (α = 0.01, Benjamini-Hochberg)

## Calibración

| variable                             | fuerza_excel   | motor   | alerta   |   tasa_alerta |    IV |   lift_alerta |   tendencia_z |   null_% |
|:-------------------------------------|:---------------|:--------|:---------|--------------:|------:|--------------:|--------------:|---------:|
| investment_redemption_pct            | High           | mixed   | > 0.20   |         0.062 | 0.175 |         2.881 |        11.671 |   14.459 |
| fixed_income_maturity_not_reinvested | High           | mixed   | > 0.50   |         0.368 | 0.211 |         2.055 |         7.218 |   73.930 |
| cash_pct_of_portfolio_chg            | High           | mixed   | > 0.10   |         0.079 | 0.144 |         2.742 |         7.927 |   14.982 |
| return_vs_benchmark                  | High           | factor  | <= -0.03 |         0.316 | 0.119 |         1.638 |         8.196 |   41.007 |
| positions_liquidated_pct             | High           | mixed   | > 0.15   |         0.016 | 0.186 |         3.718 |        15.741 |   14.565 |

AUC combinado de las variables de los Pasos 1–4 (logística): **0.683**; techo: 0.851.

## Robustez en 20 semillas de referencia

| variable                             |   ('tasa_alerta', 'min') |   ('tasa_alerta', 'median') |   ('tasa_alerta', 'max') |   ('IV', 'min') |   ('IV', 'median') |   ('IV', 'max') |   ('lift_alerta', 'min') |   ('lift_alerta', 'median') |   ('lift_alerta', 'max') |
|:-------------------------------------|-------------------------:|----------------------------:|-------------------------:|----------------:|-------------------:|----------------:|-------------------------:|----------------------------:|-------------------------:|
| cash_pct_of_portfolio_chg            |                    0.077 |                       0.080 |                    0.083 |           0.098 |              0.132 |           0.176 |                    2.490 |                       2.750 |                    3.008 |
| fixed_income_maturity_not_reinvested |                    0.360 |                       0.368 |                    0.388 |           0.130 |              0.191 |           0.333 |                    1.686 |                       1.876 |                    2.477 |
| investment_redemption_pct            |                    0.058 |                       0.063 |                    0.065 |           0.123 |              0.162 |           0.202 |                    2.486 |                       2.872 |                    3.099 |
| positions_liquidated_pct             |                    0.015 |                       0.017 |                    0.019 |           0.109 |              0.169 |           0.221 |                    3.202 |                       4.027 |                    4.712 |
| return_vs_benchmark                  |                    0.317 |                       0.336 |                    0.379 |           0.046 |              0.096 |           0.175 |                    1.347 |                       1.589 |                    1.868 |

## Eventos simulados (% de hogares con inversiones)

|                  |     % |
|:-----------------|------:|
| liquidation      |  6.76 |
| proprietary_sale |  1.98 |
| advisor_derisk   |  5.31 |
| client_full_sale |  7.96 |
| maturity         | 30.46 |

## 1 · NULL, rangos y dinero

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| columnas declaradas con unidad |  |  |  | OK |
| investment_redemption_pct NULL sin inversiones |  |  |  | OK |
| cash_pct_of_portfolio_chg NULL sin inversiones |  |  |  | OK |
| positions_liquidated_pct NULL sin inversiones |  |  |  | OK |
| #26 NULL ⇔ sin vencimientos en 90d | con vencimiento: 5,218 |  |  | OK |
| #28 NULL ⇔ sin advisory o < 12 meses |  |  |  | OK |
| #26 en [0, 1] | masa en 0: 0.49 |  |  | OK |
| #9 y #34 ≥ 0 |  |  |  | OK |
| cash % del portafolio en [0, 95%] | mediana 0.105 |  |  | OK |
| USD válido: fixed_income_not_reinvested_amount | máx $78,535,369 |  |  | OK |

## 2 · Reglas del Excel y coherencia

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| rendimiento de #28 = índice TWR del Paso 1 (12 meses) |  |  |  | OK |
| RMD excluida de #9 | 689 hogares ≥ 73 con RMD: alerta 10.89% vs 12.05% si contara |  |  | OK |
| informativo: rebalanceos del asesor (no entran en #9, que mide venta neta del cliente) | 6,624 hogares rebalancearon en 90d ($3.8B vendidos y recomprados) |  |  | OK |
| de-risking del asesor sube el cash sin contar como venta del cliente | hogares con solo de-risking: cash +5pp 60.5% vs alerta #9 1.6% |  |  | OK |
| vencimientos de renta fija no cuentan en #34 | 4,405 hogares solo con vencimiento |  |  | OK |
| coherencia: quien se muda o liquida reinvierte menos (#26) | 0.95 vs 0.34 |  |  | OK |

## 3 · Calibración (tasa de alerta, IV, tendencia, lift)

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| tasa de alerta investment_redemption_pct | 0.062 en [0.02, 0.12] |  |  | OK |
| IV investment_redemption_pct (High) | 0.175 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: investment_redemption_pct | lift = 2.88 |  |  | OK |
| tendencia en la dirección esperada: investment_redemption_pct | z = 11.7 |  |  | OK |
| tasa de alerta fixed_income_maturity_not_reinvested | 0.368 en [0.1, 0.45] |  |  | OK |
| IV fixed_income_maturity_not_reinvested (High) | 0.211 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: fixed_income_maturity_not_reinvested | lift = 2.05 |  |  | OK |
| tendencia en la dirección esperada: fixed_income_maturity_not_reinvested | z = 7.2 |  |  | OK |
| tasa de alerta cash_pct_of_portfolio_chg | 0.079 en [0.03, 0.15] |  |  | OK |
| IV cash_pct_of_portfolio_chg (High) | 0.144 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: cash_pct_of_portfolio_chg | lift = 2.74 |  |  | OK |
| tendencia en la dirección esperada: cash_pct_of_portfolio_chg | z = 7.9 |  |  | OK |
| tasa de alerta return_vs_benchmark | 0.316 en [0.1, 0.4] |  |  | OK |
| IV return_vs_benchmark (High) | 0.119 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: return_vs_benchmark | lift = 1.64 |  |  | OK |
| tendencia en la dirección esperada: return_vs_benchmark | z = 8.2 |  |  | OK |
| tasa de alerta positions_liquidated_pct | 0.016 en [0.01, 0.1] |  |  | OK |
| IV positions_liquidated_pct (High) | 0.186 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: positions_liquidated_pct | lift = 3.72 |  |  | OK |
| tendencia en la dirección esperada: positions_liquidated_pct | z = 15.7 |  |  | OK |
| IV mediano entre semillas en banda: investment_redemption_pct | mediana 0.162 (p10–p90 0.134–0.180) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: investment_redemption_pct | 0.058–0.065 |  |  | OK |
| IV mediano entre semillas en banda: fixed_income_maturity_not_reinvested | mediana 0.191 (p10–p90 0.158–0.273) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: fixed_income_maturity_not_reinvested | 0.360–0.388 |  |  | OK |
| IV mediano entre semillas en banda: cash_pct_of_portfolio_chg | mediana 0.132 (p10–p90 0.120–0.157) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: cash_pct_of_portfolio_chg | 0.077–0.083 |  |  | OK |
| IV mediano entre semillas en banda: return_vs_benchmark | mediana 0.096 (p10–p90 0.069–0.131) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: return_vs_benchmark | 0.317–0.379 |  |  | OK |
| IV mediano entre semillas en banda: positions_liquidated_pct | mediana 0.169 (p10–p90 0.124–0.196) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: positions_liquidated_pct | 0.015–0.019 |  |  | OK |

## 4 · Fuga (generador) y AUC

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| venta a cash ⟂ ε dado z_outflow (Wald) | coef ε = -0.026 ± 0.056 | 0.639 | 0.819 | OK |
| #28 ⟂ ε dado z_service (MCO) | coef ε = -0.0000 ± 0.0006 | 0.952 | 0.952 | OK |
| #28: pendiente sobre z_service ≈ −κ (alpha del Paso 1) | -0.0183 vs −0.02 |  |  | OK |
| ruido advisor_derisk ⟂ índice de riesgo | ρ = -0.0080 | 0.297 | 0.819 | OK |
| ruido client_full_sale ⟂ índice de riesgo | ρ = -0.0049 | 0.525 | 0.819 | OK |
| ruido maturity ⟂ índice de riesgo | ρ = +0.0034 | 0.655 | 0.819 | OK |
| AUC combinado (Pasos 1–4) < AUC techo | 0.683 vs techo 0.851 |  |  | OK |

## Distribuciones

|                                      |       count |         mean |            std |     min |      1% |      5% |     25% |        50% |          75% |          95% |            99% |             max |
|:-------------------------------------|------------:|-------------:|---------------:|--------:|--------:|--------:|--------:|-----------:|-------------:|-------------:|---------------:|----------------:|
| investment_redemption_pct            | 17,103.0000 |       0.0422 |         0.1146 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |     0.0031 |       0.0265 |       0.2646 |         0.5801 |          1.6693 |
| fixed_income_maturity_not_reinvested |  5,218.0000 |       0.3714 |         0.4215 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |     0.1171 |       0.8458 |       1.0000 |         1.0000 |          1.0000 |
| fixed_income_not_reinvested_amount   |  5,218.0000 | 209,019.0148 | 1,602,838.0296 |  0.0000 |  0.0000 |  0.0000 |  0.0000 | 3,358.6350 | 122,992.4900 | 821,930.0195 | 2,419,899.4725 | 78,535,368.5300 |
| cash_pct_of_portfolio_chg            | 16,999.0000 |       0.0289 |         0.0878 | -0.0548 | -0.0245 | -0.0161 | -0.0045 |     0.0044 |       0.0182 |       0.1961 |         0.4727 |          0.8129 |
| return_vs_benchmark                  | 11,801.0000 |      -0.0098 |         0.0416 | -0.1590 | -0.1027 | -0.0760 | -0.0381 |    -0.0108 |       0.0174 |       0.0610 |         0.0909 |          0.1557 |
| positions_liquidated_pct             | 17,082.0000 |       0.0086 |         0.0321 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |     0.0000 |       0.0000 |       0.0525 |         0.1860 |          0.4267 |

## WoE · investment_redemption_pct

| row_0                    |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:-------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0                   |  7,611.0000 | 381.0000 |        0.0477 | -0.2718 | 0.0308 |
| 01 [2.682e-11, 0.005034] |    942.0000 |  60.0000 |        0.0599 | -0.0244 | 0.0000 |
| 02 [0.005035, 0.008934]  |    953.0000 |  48.0000 |        0.0480 | -0.2571 | 0.0035 |
| 03 [0.008941, 0.01362]   |    947.0000 |  54.0000 |        0.0539 | -0.1341 | 0.0010 |
| 04 [0.01362, 0.02003]    |    943.0000 |  58.0000 |        0.0579 | -0.0591 | 0.0002 |
| 05 [0.02003, 0.02932]    |    938.0000 |  63.0000 |        0.0629 |  0.0282 | 0.0000 |
| 06 [0.02934, 0.04436]    |    951.0000 |  50.0000 |        0.0500 | -0.2146 | 0.0025 |
| 07 [0.04439, 0.07235]    |    939.0000 |  62.0000 |        0.0619 |  0.0113 | 0.0000 |
| 08 [0.07243, 0.2169]     |    892.0000 | 109.0000 |        0.1089 |  0.6234 | 0.0302 |
| 09 [0.2171, 1.669]       |    842.0000 | 160.0000 |        0.1597 |  1.0634 | 0.1064 |

## WoE · fixed_income_maturity_not_reinvested

| row_0                |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:---------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0               |  2,436.0000 | 101.0000 |        0.0398 | -0.4007 | 0.0660 |
| 01 [0.00927, 0.2197] |    176.0000 |   4.0000 |        0.0222 | -0.8917 | 0.0190 |
| 02 [0.2203, 0.3279]  |    169.0000 |  10.0000 |        0.0559 | -0.0040 | 0.0000 |
| 03 [0.328, 0.4134]   |    171.0000 |   8.0000 |        0.0447 | -0.2270 | 0.0016 |
| 04 [0.4138, 0.4938]  |    167.0000 |  12.0000 |        0.0670 |  0.1823 | 0.0012 |
| 05 [0.4939, 0.5771]  |    166.0000 |  13.0000 |        0.0726 |  0.2652 | 0.0027 |
| 06 [0.5779, 0.6715]  |    172.0000 |   7.0000 |        0.0391 | -0.3580 | 0.0038 |
| 07 [0.6718, 0.7683]  |    167.0000 |  12.0000 |        0.0670 |  0.1823 | 0.0012 |
| 08 [0.7692, 0.9916]  |    171.0000 |   8.0000 |        0.0447 | -0.2270 | 0.0016 |
| 09 = 1               |  1,088.0000 | 124.0000 |        0.1023 |  0.6093 | 0.1138 |

## WoE · cash_pct_of_portfolio_chg

| row_0                     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:--------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-0.05478, -0.0119]    |  1,595.0000 |  95.0000 |        0.0562 | -0.0917 | 0.0008 |
| 01 [-0.0119, -0.006628]   |  1,608.0000 |  82.0000 |        0.0485 | -0.2461 | 0.0054 |
| 02 [-0.006621, -0.002638] |  1,604.0000 |  86.0000 |        0.0509 | -0.1963 | 0.0035 |
| 03 [-0.002637, 0.0008684] |  1,603.0000 |  87.0000 |        0.0515 | -0.1842 | 0.0031 |
| 04 [0.0008685, 0.004397]  |  1,595.0000 |  95.0000 |        0.0562 | -0.0917 | 0.0008 |
| 05 [0.004403, 0.008426]   |  1,616.0000 |  73.0000 |        0.0432 | -0.3666 | 0.0115 |
| 06 [0.008428, 0.014]      |  1,604.0000 |  86.0000 |        0.0509 | -0.1963 | 0.0035 |
| 07 [0.01401, 0.02504]     |  1,602.0000 |  88.0000 |        0.0521 | -0.1722 | 0.0028 |
| 08 [0.02507, 0.06885]     |  1,574.0000 | 116.0000 |        0.0686 |  0.1203 | 0.0015 |
| 09 [0.06893, 0.8129]      |  1,462.0000 | 228.0000 |        0.1349 |  0.8678 | 0.1105 |

## WoE · return_vs_benchmark

| row_0                     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:--------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-0.159, -0.06251]     |  1,056.0000 | 117.0000 |        0.0997 |  0.5525 | 0.0390 |
| 01 [-0.06248, -0.04463]   |  1,072.0000 | 101.0000 |        0.0861 |  0.3911 | 0.0182 |
| 02 [-0.04462, -0.03178]   |  1,105.0000 |  67.0000 |        0.0572 | -0.0472 | 0.0002 |
| 03 [-0.03178, -0.02124]   |  1,102.0000 |  71.0000 |        0.0605 |  0.0131 | 0.0000 |
| 04 [-0.02124, -0.01076]   |  1,094.0000 |  78.0000 |        0.0666 |  0.1138 | 0.0014 |
| 05 [-0.01076, -0.0001283] |  1,103.0000 |  70.0000 |        0.0597 | -0.0019 | 0.0000 |
| 06 [-0.0001269, 0.0113]   |  1,115.0000 |  57.0000 |        0.0486 | -0.2165 | 0.0043 |
| 07 [0.01131, 0.02433]     |  1,116.0000 |  57.0000 |        0.0486 | -0.2174 | 0.0043 |
| 08 [0.02434, 0.04334]     |  1,124.0000 |  48.0000 |        0.0410 | -0.3948 | 0.0131 |
| 09 [0.04336, 0.1557]      |  1,138.0000 |  35.0000 |        0.0298 | -0.7192 | 0.0381 |

## WoE · positions_liquidated_pct

| row_0                   |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0                  | 14,012.0000 | 786.0000 |        0.0531 | -0.1599 | 0.0208 |
| 01 [0.0003483, 0.01656] |    224.0000 |  19.0000 |        0.0782 |  0.2767 | 0.0012 |
| 02 [0.0166, 0.02418]    |    227.0000 |  16.0000 |        0.0658 |  0.0964 | 0.0001 |
| 03 [0.0242, 0.03294]    |    226.0000 |  16.0000 |        0.0661 |  0.1008 | 0.0002 |
| 04 [0.03295, 0.04124]   |    225.0000 |  18.0000 |        0.0741 |  0.2196 | 0.0008 |
| 05 [0.04127, 0.04889]   |    225.0000 |  17.0000 |        0.0702 |  0.1640 | 0.0004 |
| 06 [0.04899, 0.05583]   |    222.0000 |  21.0000 |        0.0864 |  0.3833 | 0.0025 |
| 07 [0.05587, 0.08657]   |    206.0000 |  36.0000 |        0.1488 |  0.9872 | 0.0215 |
| 08 [0.08667, 0.1584]    |    180.0000 |  63.0000 |        0.2593 |  1.6755 | 0.0824 |
| 09 [0.1585, 0.4267]     |    190.0000 |  53.0000 |        0.2181 |  1.4502 | 0.0566 |

## Diccionario

| Columna | Unidad | Descripción |
|---|---|---|
| household_id | id | Identificador del hogar |
| investment_redemption_pct | fracción | #9 · max(0, ventas y redenciones del cliente − compras) 90d ÷ AUM promedio (alerta > 20%) |
| fixed_income_maturity_not_reinvested | fracción | #26 · principal vencido no reinvertido en 30d ÷ principal vencido; NULL sin vencimientos |
| fixed_income_not_reinvested_amount | USD | #26 · monto no reinvertido |
| cash_pct_of_portfolio_chg | fracción | #27 · cash % en t − promedio meses −6..−1 (0.10 = 10 pp) |
| return_vs_benchmark | fracción | #28 · TWR neto 12m − benchmark por perfil (−0.03 = −3 pp); NULL sin advisory |
| positions_liquidated_pct | fracción | #34 · posiciones vendidas completas sin reemplazo 90d ÷ valor hace 90d (alerta > 15%) |
