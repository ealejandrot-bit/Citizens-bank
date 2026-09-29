# Paso 2 · Recurring deposits & flows

Semilla `20260928` · 20,000 hogares · 768,662 transacciones en 18 meses · montos en USD · **65 de 65 pruebas OK** (α = 0.01, Benjamini-Hochberg)

## Calibración

| variable                       | fuerza_excel   | motor      | alerta   |   tasa_alerta |    IV | base_IV    |   lift_alerta |   tendencia_z |   null_% |
|:-------------------------------|:---------------|:-----------|:---------|--------------:|------:|:-----------|--------------:|--------------:|---------:|
| salary_deposit_stopped_flag    | Very high      | propensity | = 1      |         0.036 | 0.323 | applicable |         5.712 |        16.018 |   47.286 |
| recurring_deposit_stopped_flag | High           | propensity | = 1      |         0.042 | 0.223 | applicable |         4.341 |        16.869 |    7.461 |
| recurring_deposit_change_pct   | High           | mixed      | <= -0.40 |         0.107 | 0.169 | all        |         2.664 |        10.393 |    7.390 |
| net_deposit_flow_pct_90d       | High           | factor     | <= -0.15 |         0.181 | 0.164 | all        |         2.359 |        11.145 |    0.287 |
| pension_deposit_stopped_flag   | High           | propensity | = 1      |         0.020 | 0.220 | applicable |         5.810 |        10.675 |   65.729 |
| business_payroll_stopped_flag  | High           | factor     | = 1      |         0.056 | 0.159 | applicable |         3.330 |         8.762 |   73.889 |

AUC combinado de las variables de los Pasos 1 + 2 (logística): **0.653**; techo: 0.851.

## Robustez en 20 semillas de referencia

| variable                       |   ('tasa_alerta', 'min') |   ('tasa_alerta', 'median') |   ('tasa_alerta', 'max') |   ('IV', 'min') |   ('IV', 'median') |   ('IV', 'max') |   ('lift_alerta', 'min') |   ('lift_alerta', 'median') |   ('lift_alerta', 'max') |
|:-------------------------------|-------------------------:|----------------------------:|-------------------------:|----------------:|-------------------:|----------------:|-------------------------:|----------------------------:|-------------------------:|
| business_payroll_stopped_flag  |                    0.052 |                       0.055 |                    0.060 |           0.096 |              0.191 |           0.280 |                    2.674 |                       3.693 |                    4.400 |
| net_deposit_flow_pct_90d       |                    0.179 |                       0.182 |                    0.188 |           0.154 |              0.196 |           0.224 |                    2.242 |                       2.449 |                    2.639 |
| pension_deposit_stopped_flag   |                    0.017 |                       0.019 |                    0.021 |           0.201 |              0.266 |           0.366 |                    5.422 |                       6.532 |                    7.970 |
| recurring_deposit_change_pct   |                    0.102 |                       0.107 |                    0.110 |           0.109 |              0.160 |           0.201 |                    2.295 |                       2.636 |                    2.875 |
| recurring_deposit_stopped_flag |                    0.039 |                       0.041 |                    0.043 |           0.223 |              0.251 |           0.308 |                    4.393 |                       4.677 |                    5.389 |
| salary_deposit_stopped_flag    |                    0.033 |                       0.035 |                    0.037 |           0.310 |              0.388 |           0.505 |                    5.728 |                       6.392 |                    7.398 |

## Eventos simulados

|                                          |   % hogares |
|:-----------------------------------------|------------:|
| mudanza del banco principal (propensión) |        4.93 |
| redirección parcial (z_outflow)          |        5.19 |
| negocio muda su operación                |        2.00 |
| cambio de empleo                         |        2.69 |
| retiro                                   |        1.33 |
| licencia                                 |        0.40 |
| muerte / excluidos                       |        0.61 |
| venta del negocio                        |        0.34 |

## 1 · Transacciones

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| fechas dentro de los 18 meses previos a t | 768,662 transacciones |  |  | OK |
| montos > 0 y solo donde hay pago |  |  |  | OK |
| sin pagos antes de la apertura de la relación |  |  |  | OK |
| columnas declaradas con unidad |  |  |  | OK |

## 2 · Algoritmo de detección

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| falsos positivos de nómina sin ningún evento < 0.5% | 0.00% |  |  | OK |
| recall: nómina mudada hace > 60 días detectada ≥ 95% | 98.2% de 282 |  |  | OK |
| cambio de empleo con reemplazo ≥ 50% no se marca (≥ 95%) | 99.3% de 422 |  |  | OK |
| exclusión: retiro reportado → flag 0 | n = 110 |  |  | OK |
| exclusión: licencia reportada → flag 0 | n = 35 |  |  | OK |
| exclusión: muerte reportada → flag 0 | n = 55 |  |  | OK |
| exclusión: venta del negocio → flag 0 | n = 42 |  |  | OK |
| excluir el bono evita inflar el ingreso recurrente (bono de diciembre) | mediana del cambio en 2411 hogares: -0.010 con la regla vs +3.956 sin ella |  |  | OK |

## 3 · NULL, rangos y dinero

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| sin nómina ⇒ salary_flag NULL |  |  |  | OK |
| sin pensión (ni retiro) ⇒ pension_flag NULL |  |  |  | OK |
| sin negocio ⇒ business_flag NULL |  |  |  | OK |
| nómina con ≥ 12m de historia: patrón detectado ≥ 95% | 98.1% |  |  | OK |
| tipo de flujo detenido ⇔ flag = 1 | {'payroll': 614, 'pension': 106, 'dividend': 46, 'business_distribution': 21} |  |  | OK |
| recurring_deposit_change_pct ≥ −100% | mín -1.000 (−100% = todos los flujos detenidos) |  |  | OK |
| net_deposit_flow_pct finito | mín -8.64, p1 -1.59 |  |  | OK |
| USD± válido: net_deposit_flow_30d | rango $-147,926,144 a $54,517,197 |  |  | OK |
| USD± válido: net_deposit_flow_90d | rango $-613,531,204 a $57,632,623 |  |  | OK |
| flujo neto 90d = cambio de saldo de la serie del Paso 1 |  |  |  | OK |

## 4 · Calibración (tasa de alerta, IV, tendencia, lift)

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| tasa de alerta salary_deposit_stopped_flag | 0.036 en [0.02, 0.08] |  |  | OK |
| IV salary_deposit_stopped_flag (Very high, base applicable) | 0.323 en [0.3, 0.5] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: salary_deposit_stopped_flag | lift = 5.71 |  |  | OK |
| tendencia en la dirección esperada: salary_deposit_stopped_flag | z = 16.0 |  |  | OK |
| tasa de alerta recurring_deposit_stopped_flag | 0.042 en [0.03, 0.1] |  |  | OK |
| IV recurring_deposit_stopped_flag (High, base applicable) | 0.223 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: recurring_deposit_stopped_flag | lift = 4.34 |  |  | OK |
| tendencia en la dirección esperada: recurring_deposit_stopped_flag | z = 16.9 |  |  | OK |
| tasa de alerta recurring_deposit_change_pct | 0.107 en [0.03, 0.12] |  |  | OK |
| IV recurring_deposit_change_pct (High, base all) | 0.169 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: recurring_deposit_change_pct | lift = 2.66 |  |  | OK |
| tendencia en la dirección esperada: recurring_deposit_change_pct | z = 10.4 |  |  | OK |
| tasa de alerta net_deposit_flow_pct_90d | 0.181 en [0.1, 0.22] |  |  | OK |
| IV net_deposit_flow_pct_90d (High, base all) | 0.164 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: net_deposit_flow_pct_90d | lift = 2.36 |  |  | OK |
| tendencia en la dirección esperada: net_deposit_flow_pct_90d | z = 11.1 |  |  | OK |
| tasa de alerta pension_deposit_stopped_flag | 0.020 en [0.01, 0.06] |  |  | OK |
| IV pension_deposit_stopped_flag (High, base applicable) | 0.220 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: pension_deposit_stopped_flag | lift = 5.81 |  |  | OK |
| tendencia en la dirección esperada: pension_deposit_stopped_flag | z = 10.7 |  |  | OK |
| tasa de alerta business_payroll_stopped_flag | 0.056 en [0.02, 0.08] |  |  | OK |
| IV business_payroll_stopped_flag (High, base applicable) | 0.159 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: business_payroll_stopped_flag | lift = 3.33 |  |  | OK |
| tendencia en la dirección esperada: business_payroll_stopped_flag | z = 8.8 |  |  | OK |
| IV mediano entre semillas en banda: salary_deposit_stopped_flag | mediana 0.388 (p10–p90 0.330–0.444) en [0.3, 0.5] |  |  | OK |
| alerta en rango en todas las semillas: salary_deposit_stopped_flag | 0.033–0.037 |  |  | OK |
| IV mediano entre semillas en banda: recurring_deposit_stopped_flag | mediana 0.251 (p10–p90 0.229–0.289) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: recurring_deposit_stopped_flag | 0.039–0.043 |  |  | OK |
| IV mediano entre semillas en banda: recurring_deposit_change_pct | mediana 0.160 (p10–p90 0.132–0.183) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: recurring_deposit_change_pct | 0.102–0.110 |  |  | OK |
| IV mediano entre semillas en banda: net_deposit_flow_pct_90d | mediana 0.196 (p10–p90 0.173–0.216) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: net_deposit_flow_pct_90d | 0.179–0.188 |  |  | OK |
| IV mediano entre semillas en banda: pension_deposit_stopped_flag | mediana 0.266 (p10–p90 0.220–0.317) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: pension_deposit_stopped_flag | 0.017–0.021 |  |  | OK |
| IV mediano entre semillas en banda: business_payroll_stopped_flag | mediana 0.191 (p10–p90 0.107–0.251) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: business_payroll_stopped_flag | 0.052–0.060 |  |  | OK |

## 5 · Pruebas estadísticas

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| ε por diseño (propensity): salary_deposit_stopped_flag | ρ = +0.1482 (precursor directo de salida, D-14) |  |  | OK |
| ε por diseño (propensity): recurring_deposit_stopped_flag | ρ = +0.1205 (precursor directo de salida, D-14) |  |  | OK |
| ε por diseño (mixed): recurring_deposit_change_pct | ρ = -0.0386 (precursor directo de salida, D-14) |  |  | OK |
| sin fuga del riesgo no observable: net_deposit_flow_pct_90d ⟂ ε | ρ = +0.0089 | 0.21 | 0.421 | OK |
| ε por diseño (propensity): pension_deposit_stopped_flag | ρ = +0.1286 (precursor directo de salida, D-14) |  |  | OK |
| sin fuga del riesgo no observable: business_payroll_stopped_flag ⟂ ε | ρ = +0.0053 | 0.704 | 0.704 | OK |
| AUC combinado (Pasos 1 + 2) < AUC techo | 0.653 vs techo 0.851 |  |  | OK |

## Distribuciones

|                                |       count |          mean |            std |               min |               1% |              5% |           25% |          50% |         75% |          95% |            99% |             max |
|:-------------------------------|------------:|--------------:|---------------:|------------------:|-----------------:|----------------:|--------------:|-------------:|------------:|-------------:|---------------:|----------------:|
| salary_deposit_stopped_flag    | 10,540.0000 |        0.0368 |         0.1883 |            0.0000 |           0.0000 |          0.0000 |        0.0000 |       0.0000 |      0.0000 |       0.0000 |         1.0000 |          1.0000 |
| pension_deposit_stopped_flag   |  6,851.0000 |        0.0201 |         0.1405 |            0.0000 |           0.0000 |          0.0000 |        0.0000 |       0.0000 |      0.0000 |       0.0000 |         1.0000 |          1.0000 |
| recurring_deposit_stopped_flag | 18,507.0000 |        0.0425 |         0.2018 |            0.0000 |           0.0000 |          0.0000 |        0.0000 |       0.0000 |      0.0000 |       0.0000 |         1.0000 |          1.0000 |
| recurring_deposit_change_pct   | 18,521.0000 |       -0.0713 |         0.3120 |           -1.0000 |          -1.0000 |         -0.8376 |       -0.0836 |      -0.0080 |      0.0192 |       0.3206 |         0.6311 |          3.5607 |
| net_deposit_flow_30d           | 19,984.0000 | -158,315.5297 | 1,714,974.5989 | -147,926,143.9600 |  -3,269,269.6201 |   -843,401.3850 |  -86,469.0700 |  -5,646.6200 | 32,516.6350 | 257,029.8090 |   902,139.8875 | 54,517,197.3300 |
| net_deposit_flow_pct_30d       | 19,980.0000 |       -0.0440 |         0.1628 |           -9.4472 |          -0.6406 |         -0.3156 |       -0.0511 |      -0.0069 |      0.0259 |       0.0741 |         0.1192 |          0.4657 |
| net_deposit_flow_90d           | 19,947.0000 | -642,448.7783 | 7,612,922.1590 | -613,531,204.0800 | -10,987,667.5312 | -2,316,052.2490 | -180,036.4900 | -10,302.8400 | 62,036.8350 | 467,213.3820 | 1,458,434.6238 | 57,632,622.7500 |
| net_deposit_flow_pct_90d       | 19,943.0000 |       -0.1026 |         0.3553 |           -8.6405 |          -1.5857 |         -0.7368 |       -0.0956 |      -0.0126 |      0.0502 |       0.1361 |         0.2040 |          0.7373 |
| business_payroll_stopped_flag  |  5,223.0000 |        0.0565 |         0.2309 |            0.0000 |           0.0000 |          0.0000 |        0.0000 |       0.0000 |      0.0000 |       1.0000 |         1.0000 |          1.0000 |

## Correlación de Spearman (Pasos 1 + 2)

|                                |   aum_outflow_pct_90d |   deposit_balance_change_pct_90d |   aum_vs_baseline_pct |   deposit_balance_vs_6m_avg_pct |   salary_deposit_stopped_flag |   recurring_deposit_stopped_flag |   recurring_deposit_change_pct |   net_deposit_flow_pct_90d |   pension_deposit_stopped_flag |   business_payroll_stopped_flag |
|:-------------------------------|----------------------:|---------------------------------:|----------------------:|--------------------------------:|------------------------------:|---------------------------------:|-------------------------------:|---------------------------:|-------------------------------:|--------------------------------:|
| aum_outflow_pct_90d            |                  1.00 |                            -0.38 |                 -0.83 |                           -0.41 |                          0.11 |                             0.07 |                          -0.04 |                      -0.41 |                           0.06 |                            0.21 |
| deposit_balance_change_pct_90d |                 -0.38 |                             1.00 |                  0.36 |                            0.90 |                         -0.09 |                            -0.07 |                           0.05 |                       0.84 |                          -0.07 |                           -0.17 |
| aum_vs_baseline_pct            |                 -0.83 |                             0.36 |                  1.00 |                            0.40 |                         -0.09 |                            -0.06 |                           0.04 |                       0.38 |                          -0.05 |                           -0.20 |
| deposit_balance_vs_6m_avg_pct  |                 -0.41 |                             0.90 |                  0.40 |                            1.00 |                         -0.10 |                            -0.07 |                           0.05 |                       0.93 |                          -0.07 |                           -0.19 |
| salary_deposit_stopped_flag    |                  0.11 |                            -0.09 |                 -0.09 |                           -0.10 |                          1.00 |                             0.77 |                          -0.28 |                      -0.10 |                           0.57 |                            0.15 |
| recurring_deposit_stopped_flag |                  0.07 |                            -0.07 |                 -0.06 |                           -0.07 |                          0.77 |                             1.00 |                          -0.21 |                      -0.07 |                           0.73 |                            0.09 |
| recurring_deposit_change_pct   |                 -0.04 |                             0.05 |                  0.04 |                            0.05 |                         -0.28 |                            -0.21 |                           1.00 |                       0.05 |                          -0.18 |                           -0.07 |
| net_deposit_flow_pct_90d       |                 -0.41 |                             0.84 |                  0.38 |                            0.93 |                         -0.10 |                            -0.07 |                           0.05 |                       1.00 |                          -0.07 |                           -0.18 |
| pension_deposit_stopped_flag   |                  0.06 |                            -0.07 |                 -0.05 |                           -0.07 |                          0.57 |                             0.73 |                          -0.18 |                      -0.07 |                           1.00 |                            0.09 |
| business_payroll_stopped_flag  |                  0.21 |                            -0.17 |                 -0.20 |                           -0.19 |                          0.15 |                             0.09 |                          -0.07 |                      -0.18 |                           0.09 |                            1.00 |

## WoE · salary_deposit_stopped_flag

| row_0     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:----------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0    |  9,582.0000 | 515.0000 |        0.0510 | -0.1739 | 0.0270 |
| 01 [1, 1] |     28.0000 |  15.0000 |        0.3488 |  2.1396 | 0.0464 |
| 02 [1, 1] |     29.0000 |  13.0000 |        0.3095 |  1.9669 | 0.0362 |
| 03 [1, 1] |     30.0000 |  12.0000 |        0.2857 |  1.8566 | 0.0310 |
| 04 [1, 1] |     29.0000 |  13.0000 |        0.3095 |  1.9669 | 0.0362 |
| 05 [1, 1] |     29.0000 |  14.0000 |        0.3256 |  2.0384 | 0.0407 |
| 06 [1, 1] |     29.0000 |  13.0000 |        0.3095 |  1.9669 | 0.0362 |
| 07 [1, 1] |     32.0000 |  10.0000 |        0.2381 |  1.6188 | 0.0216 |
| 08 [1, 1] |     31.0000 |  11.0000 |        0.2619 |  1.7410 | 0.0262 |
| 09 [1, 1] |     33.0000 |  10.0000 |        0.2326 |  1.5885 | 0.0210 |

## WoE · recurring_deposit_stopped_flag

| row_0     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:----------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0    | 16,682.0000 | 935.0000 |        0.0531 | -0.1436 | 0.0185 |
| 01 [1, 1] |     63.0000 |  24.0000 |        0.2759 |  1.7850 | 0.0325 |
| 02 [1, 1] |     66.0000 |  20.0000 |        0.2326 |  1.5606 | 0.0226 |
| 03 [1, 1] |     69.0000 |  17.0000 |        0.1977 |  1.3583 | 0.0158 |
| 04 [1, 1] |     60.0000 |  26.0000 |        0.3023 |  1.9119 | 0.0386 |
| 05 [1, 1] |     69.0000 |  18.0000 |        0.2069 |  1.4138 | 0.0177 |
| 06 [1, 1] |     64.0000 |  22.0000 |        0.2558 |  1.6843 | 0.0276 |
| 07 [1, 1] |     69.0000 |  17.0000 |        0.1977 |  1.3583 | 0.0158 |
| 08 [1, 1] |     67.0000 |  19.0000 |        0.2209 |  1.4957 | 0.0202 |
| 09 [1, 1] |     71.0000 |  16.0000 |        0.1839 |  1.2711 | 0.0135 |

## WoE · recurring_deposit_change_pct

| row_0                     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:--------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-1, -0.431]           |  1,585.0000 | 256.0000 |        0.1391 |  0.9192 | 0.1176 |
| 01 [-0.43, -0.1291]       |  1,693.0000 | 148.0000 |        0.0804 |  0.3067 | 0.0100 |
| 02 [-0.129, -0.07181]     |  1,758.0000 |  83.0000 |        0.0451 | -0.3067 | 0.0076 |
| 03 [-0.07181, -0.03159]   |  1,740.0000 | 100.0000 |        0.0543 | -0.1111 | 0.0011 |
| 04 [-0.03157, -0.007695]  |  1,749.0000 |  92.0000 |        0.0500 | -0.1992 | 0.0034 |
| 05 [-0.007685, 0.0007422] |  1,761.0000 |  80.0000 |        0.0435 | -0.3450 | 0.0095 |
| 06 [0.0007431, 0.01005]   |  1,752.0000 |  88.0000 |        0.0478 | -0.2451 | 0.0050 |
| 07 [0.01005, 0.04301]     |  1,759.0000 |  82.0000 |        0.0445 | -0.3193 | 0.0082 |
| 08 [0.04302, 0.1789]      |  1,749.0000 |  92.0000 |        0.0500 | -0.1992 | 0.0034 |
| 09 [0.179, 3.561]         |  1,750.0000 |  91.0000 |        0.0494 | -0.2106 | 0.0037 |
| NULL                      |  1,381.0000 |  88.0000 |        0.0599 | -0.0072 | 0.0000 |

## WoE · net_deposit_flow_pct_90d

| row_0                   |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-8.641, -0.405]     |  1,721.0000 | 261.0000 |        0.1317 |  0.8562 | 0.1068 |
| 01 [-0.4047, -0.1298]   |  1,816.0000 | 166.0000 |        0.0838 |  0.3510 | 0.0144 |
| 02 [-0.1298, -0.07231]  |  1,875.0000 | 107.0000 |        0.0540 | -0.1184 | 0.0013 |
| 03 [-0.07229, -0.03949] |  1,889.0000 |  93.0000 |        0.0469 | -0.2654 | 0.0063 |
| 04 [-0.03949, -0.01256] |  1,872.0000 | 110.0000 |        0.0555 | -0.0893 | 0.0008 |
| 05 [-0.01255, 0.01191]  |  1,888.0000 |  94.0000 |        0.0474 | -0.2542 | 0.0058 |
| 06 [0.01192, 0.0363]    |  1,892.0000 |  90.0000 |        0.0454 | -0.2996 | 0.0079 |
| 07 [0.03631, 0.06487]   |  1,887.0000 |  95.0000 |        0.0479 | -0.2432 | 0.0053 |
| 08 [0.06487, 0.1033]    |  1,887.0000 |  95.0000 |        0.0479 | -0.2432 | 0.0053 |
| 09 [0.1034, 0.7373]     |  1,895.0000 |  87.0000 |        0.0439 | -0.3349 | 0.0097 |
| NULL                    |     55.0000 |   2.0000 |        0.0351 | -0.3594 | 0.0003 |

## WoE · pension_deposit_stopped_flag

| row_0     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:----------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0    |  6,316.0000 | 363.0000 |        0.0543 | -0.1054 | 0.0104 |
| 01 [1, 1] |     11.0000 |   4.0000 |        0.2667 |  1.8115 | 0.0166 |
| 02 [1, 1] |      8.0000 |   7.0000 |        0.4667 |  2.6246 | 0.0445 |
| 03 [1, 1] |     12.0000 |   3.0000 |        0.2000 |  1.4768 | 0.0097 |
| 04 [1, 1] |      8.0000 |   6.0000 |        0.4286 |  2.4815 | 0.0361 |
| 05 [1, 1] |      9.0000 |   6.0000 |        0.4000 |  2.3703 | 0.0341 |
| 06 [1, 1] |     11.0000 |   4.0000 |        0.2667 |  1.8115 | 0.0166 |
| 07 [1, 1] |     11.0000 |   3.0000 |        0.2143 |  1.5602 | 0.0105 |
| 08 [1, 1] |     10.0000 |   5.0000 |        0.3333 |  2.1031 | 0.0248 |
| 09 [1, 1] |     11.0000 |   4.0000 |        0.2667 |  1.8115 | 0.0166 |

## WoE · business_payroll_stopped_flag

| row_0   |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:--------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0  |  4,631.0000 | 266.0000 |        0.0543 | -0.1323 | 0.0156 |
| 01 = 1  |    240.0000 |  53.0000 |        0.1809 |  1.2199 | 0.1437 |

## Diccionario

| Columna | Unidad | Descripción |
|---|---|---|
| household_id | id | Identificador del hogar |
| salary_deposit_stopped_flag | 0/1 | #3 · nómina detectada que dejó de llegar (45d); NULL sin patrón de nómina |
| pension_deposit_stopped_flag | 0/1 | #19 · pensión detectada que dejó de llegar; NULL sin patrón de pensión |
| recurring_deposit_stopped_flag | 0/1 | #4 · algún flujo recurrente ≥ 10% del ingreso dejó de llegar |
| recurring_deposit_stopped_type | categoría | #4 · tipo del flujo detenido (explica la alerta) |
| recurring_deposit_change_pct | fracción | #5 · recurrente últimos 30d ÷ promedio mensual meses −7..−1 − 1 |
| net_deposit_flow_30d | USD± | #6 · entradas − salidas de depósitos, último mes |
| net_deposit_flow_pct_30d | fracción | #6 · net_deposit_flow_30d ÷ saldo promedio |
| net_deposit_flow_90d | USD± | #6 · entradas − salidas de depósitos, últimos 3 meses |
| net_deposit_flow_pct_90d | fracción | #6 · net_deposit_flow_90d ÷ saldo promedio (alerta ≤ −15%) |
| business_payroll_stopped_flag | 0/1 | #20 · la nómina del negocio no corrió en 60d; NULL sin negocio / patrón |
