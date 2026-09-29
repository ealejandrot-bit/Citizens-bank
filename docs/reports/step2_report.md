# Paso 2 · Recurring deposits & flows

Semilla `20260928` · 20,000 hogares · 768,662 transacciones en 18 meses · montos en USD · **71 de 71 pruebas OK** (α = 0.01, Benjamini-Hochberg)

## Calibración

| variable                       | fuerza_excel   | motor      | alerta   |   tasa_alerta |    IV | base_IV    |   lift_alerta |   tendencia_z |   null_% |
|:-------------------------------|:---------------|:-----------|:---------|--------------:|------:|:-----------|--------------:|--------------:|---------:|
| salary_deposit_stopped_flag    | Very high      | propensity | = 1      |         0.036 | 0.323 | applicable |         5.712 |        16.018 |   47.286 |
| recurring_deposit_stopped_flag | High           | propensity | = 1      |         0.042 | 0.223 | applicable |         4.341 |        16.869 |    7.461 |
| recurring_deposit_change_pct   | High           | mixed      | <= -0.40 |         0.107 | 0.169 | all        |         2.664 |        10.393 |    7.390 |
| net_deposit_flow_pct_90d       | High           | mixed      | <= -0.15 |         0.277 | 0.238 | all        |         2.041 |        12.370 |    0.287 |
| pension_deposit_stopped_flag   | High           | propensity | = 1      |         0.020 | 0.220 | applicable |         5.810 |        10.675 |   65.729 |
| business_payroll_stopped_flag  | High           | factor     | = 1      |         0.056 | 0.159 | applicable |         3.330 |         8.762 |   73.889 |

AUC combinado de las variables de los Pasos 1 + 2 (logística): **0.649**; techo: 0.851.

## Robustez en 20 semillas de referencia

| variable                       |   ('tasa_alerta', 'min') |   ('tasa_alerta', 'median') |   ('tasa_alerta', 'max') |   ('IV', 'min') |   ('IV', 'median') |   ('IV', 'max') |   ('lift_alerta', 'min') |   ('lift_alerta', 'median') |   ('lift_alerta', 'max') |
|:-------------------------------|-------------------------:|----------------------------:|-------------------------:|----------------:|-------------------:|----------------:|-------------------------:|----------------------------:|-------------------------:|
| business_payroll_stopped_flag  |                    0.052 |                       0.055 |                    0.060 |           0.096 |              0.191 |           0.280 |                    2.674 |                       3.693 |                    4.400 |
| net_deposit_flow_pct_90d       |                    0.276 |                       0.280 |                    0.286 |           0.180 |              0.229 |           0.275 |                    1.769 |                       1.903 |                    2.103 |
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
| net_deposit_flow_pct finito | mín -6.94, p1 -1.55 |  |  | OK |
| USD± válido: net_deposit_flow_30d | rango $-159,741,054 a $116,460,945 |  |  | OK |
| USD± válido: net_deposit_flow_90d | rango $-672,085,203 a $121,046,487 |  |  | OK |
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
| tasa de alerta net_deposit_flow_pct_90d | 0.277 en [0.06, 0.32] |  |  | OK |
| IV net_deposit_flow_pct_90d (High, base all) | 0.238 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: net_deposit_flow_pct_90d | lift = 2.04 |  |  | OK |
| tendencia en la dirección esperada: net_deposit_flow_pct_90d | z = 12.4 |  |  | OK |
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
| IV mediano entre semillas en banda: net_deposit_flow_pct_90d | mediana 0.229 (p10–p90 0.191–0.270) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: net_deposit_flow_pct_90d | 0.276–0.286 |  |  | OK |
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
| ε por diseño (mixed): net_deposit_flow_pct_90d | ρ = -0.0431 (precursor directo de salida, D-14) |  |  | OK |
| ε por diseño (propensity): pension_deposit_stopped_flag | ρ = +0.1286 (precursor directo de salida, D-14) |  |  | OK |
| sin fuga del riesgo no observable: business_payroll_stopped_flag ⟂ ε | ρ = +0.0053 | 0.704 | 0.719 | OK |
| evento partial ⟂ ε dado z_outflow (Wald) | coef ε = +0.037 ± 0.057 | 0.519 | 0.719 | OK |
| evento business_move ⟂ ε dado z_outflow (Wald) | coef ε = -0.092 ± 0.114 | 0.417 | 0.719 | OK |
| ruido job_change ⟂ índice de riesgo | ρ = -0.0090 | 0.204 | 0.713 | OK |
| ruido retire ⟂ índice de riesgo | ρ = +0.0025 | 0.719 | 0.719 | OK |
| ruido leave ⟂ índice de riesgo | ρ = -0.0054 | 0.443 | 0.719 | OK |
| ruido business_sale ⟂ índice de riesgo | ρ = -0.0121 | 0.087 | 0.609 | OK |
| AUC combinado (Pasos 1 + 2) < AUC techo | 0.649 vs techo 0.851 |  |  | OK |

## Distribuciones

|                                |       count |          mean |            std |               min |               1% |              5% |           25% |          50% |          75% |            95% |            99% |              max |
|:-------------------------------|------------:|--------------:|---------------:|------------------:|-----------------:|----------------:|--------------:|-------------:|-------------:|---------------:|---------------:|-----------------:|
| salary_deposit_stopped_flag    | 10,540.0000 |        0.0368 |         0.1883 |            0.0000 |           0.0000 |          0.0000 |        0.0000 |       0.0000 |       0.0000 |         0.0000 |         1.0000 |           1.0000 |
| pension_deposit_stopped_flag   |  6,851.0000 |        0.0201 |         0.1405 |            0.0000 |           0.0000 |          0.0000 |        0.0000 |       0.0000 |       0.0000 |         0.0000 |         1.0000 |           1.0000 |
| recurring_deposit_stopped_flag | 18,507.0000 |        0.0425 |         0.2018 |            0.0000 |           0.0000 |          0.0000 |        0.0000 |       0.0000 |       0.0000 |         0.0000 |         1.0000 |           1.0000 |
| recurring_deposit_change_pct   | 18,521.0000 |       -0.0713 |         0.3120 |           -1.0000 |          -1.0000 |         -0.8376 |       -0.0836 |      -0.0080 |       0.0192 |         0.3206 |         0.6311 |           3.5607 |
| net_deposit_flow_30d           | 19,984.0000 | -140,821.9466 | 2,516,161.8226 | -159,741,054.0900 |  -4,483,446.9984 | -1,064,216.0075 | -131,900.3200 |  -4,410.6550 |  88,497.8525 |   618,013.1390 | 2,115,031.5470 | 116,460,945.1700 |
| net_deposit_flow_pct_30d       | 19,980.0000 |       -0.0447 |         0.3336 |          -12.6116 |          -0.9392 |         -0.3068 |       -0.0892 |      -0.0055 |       0.0653 |         0.1718 |         0.2639 |           0.7772 |
| net_deposit_flow_90d           | 19,947.0000 | -507,524.1751 | 7,201,367.6907 | -672,085,202.6700 | -11,530,665.3926 | -2,468,515.7550 | -279,603.6550 | -10,533.3100 | 153,448.9950 | 1,057,526.1840 | 3,320,296.3572 | 121,046,486.8300 |
| net_deposit_flow_pct_90d       | 19,943.0000 |       -0.0684 |         0.3606 |           -6.9422 |          -1.5469 |         -0.6018 |       -0.1712 |      -0.0137 |       0.1236 |         0.3156 |         0.4687 |           1.7101 |
| business_payroll_stopped_flag  |  5,223.0000 |        0.0565 |         0.2309 |            0.0000 |           0.0000 |          0.0000 |        0.0000 |       0.0000 |       0.0000 |         1.0000 |         1.0000 |           1.0000 |

## Correlación de Spearman (Pasos 1 + 2)

|                                |   aum_outflow_pct_90d |   deposit_balance_change_pct_90d |   aum_vs_baseline_pct |   deposit_balance_vs_6m_avg_pct |   salary_deposit_stopped_flag |   recurring_deposit_stopped_flag |   recurring_deposit_change_pct |   net_deposit_flow_pct_90d |   pension_deposit_stopped_flag |   business_payroll_stopped_flag |
|:-------------------------------|----------------------:|---------------------------------:|----------------------:|--------------------------------:|------------------------------:|---------------------------------:|-------------------------------:|---------------------------:|-------------------------------:|--------------------------------:|
| aum_outflow_pct_90d            |                  1.00 |                            -0.18 |                 -0.77 |                           -0.21 |                          0.21 |                             0.14 |                          -0.06 |                      -0.21 |                           0.14 |                            0.12 |
| deposit_balance_change_pct_90d |                 -0.18 |                             1.00 |                  0.19 |                            0.88 |                         -0.22 |                            -0.16 |                           0.06 |                       0.80 |                          -0.17 |                           -0.08 |
| aum_vs_baseline_pct            |                 -0.77 |                             0.19 |                  1.00 |                            0.21 |                         -0.23 |                            -0.16 |                           0.06 |                       0.19 |                          -0.17 |                           -0.11 |
| deposit_balance_vs_6m_avg_pct  |                 -0.21 |                             0.88 |                  0.21 |                            1.00 |                         -0.22 |                            -0.17 |                           0.06 |                       0.91 |                          -0.17 |                           -0.09 |
| salary_deposit_stopped_flag    |                  0.21 |                            -0.22 |                 -0.23 |                           -0.22 |                          1.00 |                             0.77 |                          -0.28 |                      -0.21 |                           0.57 |                            0.15 |
| recurring_deposit_stopped_flag |                  0.14 |                            -0.16 |                 -0.16 |                           -0.17 |                          0.77 |                             1.00 |                          -0.21 |                      -0.15 |                           0.73 |                            0.09 |
| recurring_deposit_change_pct   |                 -0.06 |                             0.06 |                  0.06 |                            0.06 |                         -0.28 |                            -0.21 |                           1.00 |                       0.06 |                          -0.18 |                           -0.07 |
| net_deposit_flow_pct_90d       |                 -0.21 |                             0.80 |                  0.19 |                            0.91 |                         -0.21 |                            -0.15 |                           0.06 |                       1.00 |                          -0.15 |                           -0.07 |
| pension_deposit_stopped_flag   |                  0.14 |                            -0.17 |                 -0.17 |                           -0.17 |                          0.57 |                             0.73 |                          -0.18 |                      -0.15 |                           1.00 |                            0.09 |
| business_payroll_stopped_flag  |                  0.12 |                            -0.08 |                 -0.11 |                           -0.09 |                          0.15 |                             0.09 |                          -0.07 |                      -0.07 |                           0.09 |                            1.00 |

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
| 00 [-6.942, -0.3786]    |  1,665.0000 | 317.0000 |        0.1599 |  1.0833 | 0.1887 |
| 01 [-0.3785, -0.2198]   |  1,855.0000 | 127.0000 |        0.0641 |  0.0629 | 0.0004 |
| 02 [-0.2198, -0.1339]   |  1,884.0000 |  98.0000 |        0.0494 | -0.2107 | 0.0040 |
| 03 [-0.1339, -0.0682]   |  1,881.0000 | 101.0000 |        0.0510 | -0.1791 | 0.0030 |
| 04 [-0.06819, -0.01369] |  1,887.0000 |  95.0000 |        0.0479 | -0.2432 | 0.0053 |
| 05 [-0.01368, 0.03865]  |  1,883.0000 |  99.0000 |        0.0499 | -0.2000 | 0.0037 |
| 06 [0.03871, 0.09295]   |  1,889.0000 |  93.0000 |        0.0469 | -0.2654 | 0.0063 |
| 07 [0.09295, 0.1567]    |  1,896.0000 |  86.0000 |        0.0434 | -0.3469 | 0.0103 |
| 08 [0.1567, 0.2427]     |  1,882.0000 | 100.0000 |        0.0505 | -0.1895 | 0.0033 |
| 09 [0.2427, 1.71]       |  1,900.0000 |  82.0000 |        0.0414 | -0.3964 | 0.0132 |
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
