# Paso 3 · Transfers

Semilla `20260928` · 20,000 hogares · 3,205,274 transacciones en 18 meses · montos en USD · **71 de 71 pruebas OK** (α = 0.01, Benjamini-Hochberg)

## Calibración

| variable                             | fuerza_excel   | alerta   |   tasa_alerta |    IV |   lift_alerta |   tendencia_z |   null_% |
|:-------------------------------------|:---------------|:---------|--------------:|------:|--------------:|--------------:|---------:|
| external_transfer_pct_of_balance_60d | Very high      | > 0.15   |         0.065 | 0.317 |         4.925 |        12.174 |    0.080 |
| new_external_destinations_90d        | High           | >= 1     |         0.059 | 0.292 |         4.362 |        21.544 |    3.497 |
| transfer_to_competitor_pct_90d       | High           | > 0.10   |         0.050 | 0.298 |         6.144 |        11.936 |    0.161 |
| external_transfer_acceleration       | High           | accel    |         0.043 | 0.223 |         4.844 |         4.950 |    0.161 |
| net_external_flow_pct_90d            | High           | <= -0.15 |         0.051 | 0.261 |         4.986 |        10.916 |    0.161 |
| external_destination_concentration   | High           | hhi      |         0.060 | 0.221 |         4.485 |         5.365 |    0.161 |
| outflow_vs_baseline_pct              | High           | > 1.0    |         0.076 | 0.110 |         2.373 |         2.282 |    0.770 |

AUC combinado de las variables de los Pasos 1–3 (logística): **0.656**; techo: 0.851.

## Robustez en 20 semillas de referencia

| variable                             |   ('tasa_alerta', 'min') |   ('tasa_alerta', 'median') |   ('tasa_alerta', 'max') |   ('IV', 'min') |   ('IV', 'median') |   ('IV', 'max') |   ('lift_alerta', 'min') |   ('lift_alerta', 'median') |   ('lift_alerta', 'max') |
|:-------------------------------------|-------------------------:|----------------------------:|-------------------------:|----------------:|-------------------:|----------------:|-------------------------:|----------------------------:|-------------------------:|
| external_destination_concentration   |                    0.057 |                       0.059 |                    0.061 |           0.172 |              0.225 |           0.268 |                    3.859 |                       4.244 |                    4.860 |
| external_transfer_acceleration       |                    0.039 |                       0.041 |                    0.045 |           0.151 |              0.202 |           0.249 |                    3.824 |                       4.529 |                    5.027 |
| external_transfer_pct_of_balance_60d |                    0.061 |                       0.064 |                    0.067 |           0.252 |              0.292 |           0.361 |                    4.532 |                       5.000 |                    5.626 |
| net_external_flow_pct_90d            |                    0.047 |                       0.050 |                    0.052 |           0.217 |              0.254 |           0.314 |                    4.526 |                       5.051 |                    5.455 |
| new_external_destinations_90d        |                    0.054 |                       0.058 |                    0.061 |           0.194 |              0.264 |           0.336 |                    3.574 |                       4.151 |                    4.837 |
| outflow_vs_baseline_pct              |                    0.071 |                       0.073 |                    0.078 |           0.068 |              0.112 |           0.143 |                    2.191 |                       2.422 |                    2.726 |
| transfer_to_competitor_pct_90d       |                    0.048 |                       0.050 |                    0.052 |           0.250 |              0.295 |           0.381 |                    5.729 |                       6.254 |                    6.988 |

## Transacciones por categoría

| category        |      size |            sum |    median |
|:----------------|----------:|---------------:|----------:|
| background      | 1,415,586 | 10,353,037,410 |     2,082 |
| biller          | 1,061,051 |  4,373,246,896 |     2,498 |
| donation        |   104,225 |    250,786,452 |     2,006 |
| episode_acats   |     1,360 |  2,085,667,002 |   436,898 |
| episode_deposit |     1,536 | 13,642,336,215 |   475,992 |
| incoming        |   395,699 | 85,941,885,408 |    44,196 |
| irs_shock       |       752 |  1,432,364,030 |   536,790 |
| irs_shock_aum   |       312 |  1,352,146,030 | 1,337,851 |
| irs_tax         |    91,844 |  5,057,891,512 |    37,960 |
| loan_citizens   |   120,834 |  1,159,759,936 |     7,958 |
| move_acats      |       689 |  8,924,251,718 | 4,149,397 |
| move_deposit    |     2,491 |  7,679,195,417 |   738,681 |
| one_off         |     7,155 |    178,964,268 |    15,398 |
| real_estate     |     1,222 |  3,128,951,985 |   580,001 |
| shock_aum       |       518 |  1,749,803,726 | 1,155,628 |

## 1 · Transacciones y catálogo

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| fechas en (t − 548d, t] y después de la apertura | 3,205,274 transacciones |  |  | OK |
| montos > 0 al centavo |  |  |  | OK |
| ABA con dígito verificador válido | 217 ABA |  |  | OK |
| cada ABA pertenece a una sola institución |  |  |  | OK |
| hay instituciones con varias ABA (prueba el agrupado de #24) | 74 de 111 |  |  | OK |
| toda transferencia externa tiene institución y ABA |  |  |  | OK |
| catálogo sin nombres reales (etiquetas sintéticas) |  |  |  | OK |
| columnas declaradas con unidad |  |  |  | OK |

## 2 · Identidad contable y coherencia

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| entradas externas de las transacciones = las que cierran la identidad | máx desvío $0.01 |  |  | OK |
| ΔD = ingresos + internos + entradas − salidas − tarjeta − otros (cada mes) |  |  |  | OK |
| meses con débitos no explicados (tarjeta extra, cheques) < 60% | 43.9% |  |  | OK |
| toda mudanza con traslado tiene envíos al banco nuevo | 882 hogares |  |  | OK |
| el traslado por mudanza va a un banco competidor |  |  |  | OK |
| coherencia: nómina detenida ↔ transferencias externas (ρ > 0) | ρ = 0.219 |  |  | OK |

## 3 · Reglas del Excel (exclusiones, destino nuevo, HHI, pisos)

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| las exclusiones evitan falsas alertas (IRS, billers, donaciones, préstamos) | alerta #7: 6.5% con exclusiones vs 8.8% sin ellas |  |  | OK |
| HHI por institución ≥ HHI por ABA | 516 hogares cambian al agrupar por institución |  |  | OK |
| piso PB mejora la precisión: destino nuevo ≥ $50k vs $10k | alerta 5.7% (lift 4.28) vs Excel 8.6% (lift 3.20) |  |  | OK |
| piso PB mejora la precisión: piso de línea base $10k vs $1k | alerta 7.5% (lift 2.36) vs Excel 11.8% (lift 1.79) |  |  | OK |

## 4 · NULL, rangos y dinero

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| USD válido: external_transfer_amount_60d | máx $486,622,004 |  |  | OK |
| USD válido: transfer_to_competitor_bank_amount_90d | máx $584,944,277 |  |  | OK |
| USD± válido: net_external_flow_30d | $-115,233,248 a $113,656,538 |  |  | OK |
| USD± válido: net_external_flow_90d | $-290,613,733 a $134,202,884 |  |  | OK |
| HHI en (0, 1] |  |  |  | OK |
| HHI NULL ⇔ sin salidas en 90d (o < 3 meses) |  |  |  | OK |
| destinos nuevos: enteros ≥ 0; NULL con < 16 meses de historia |  |  |  | OK |

## 5 · Calibración (tasa de alerta, IV con tolerancia ±0.03, tendencia, lift)

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| tasa de alerta external_transfer_pct_of_balance_60d | 0.065 en [0.04, 0.16] |  |  | OK |
| IV external_transfer_pct_of_balance_60d (Very high) | 0.317 en [0.3, 0.5] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: external_transfer_pct_of_balance_60d | lift = 4.93 |  |  | OK |
| tendencia en la dirección esperada: external_transfer_pct_of_balance_60d | z = 12.2 |  |  | OK |
| tasa de alerta new_external_destinations_90d | 0.059 en [0.02, 0.15] |  |  | OK |
| IV new_external_destinations_90d (High) | 0.292 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: new_external_destinations_90d | lift = 4.36 |  |  | OK |
| tendencia en la dirección esperada: new_external_destinations_90d | z = 21.5 |  |  | OK |
| tasa de alerta transfer_to_competitor_pct_90d | 0.050 en [0.03, 0.14] |  |  | OK |
| IV transfer_to_competitor_pct_90d (High) | 0.298 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: transfer_to_competitor_pct_90d | lift = 6.14 |  |  | OK |
| tendencia en la dirección esperada: transfer_to_competitor_pct_90d | z = 11.9 |  |  | OK |
| tasa de alerta external_transfer_acceleration | 0.043 en [0.02, 0.12] |  |  | OK |
| IV external_transfer_acceleration (High) | 0.223 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: external_transfer_acceleration | lift = 4.84 |  |  | OK |
| tendencia en la dirección esperada: external_transfer_acceleration | z = 4.9 |  |  | OK |
| tasa de alerta net_external_flow_pct_90d | 0.051 en [0.04, 0.2] |  |  | OK |
| IV net_external_flow_pct_90d (High) | 0.261 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: net_external_flow_pct_90d | lift = 4.99 |  |  | OK |
| tendencia en la dirección esperada: net_external_flow_pct_90d | z = 10.9 |  |  | OK |
| tasa de alerta external_destination_concentration | 0.060 en [0.02, 0.15] |  |  | OK |
| IV external_destination_concentration (High) | 0.221 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: external_destination_concentration | lift = 4.49 |  |  | OK |
| tendencia en la dirección esperada: external_destination_concentration | z = 5.4 |  |  | OK |
| tasa de alerta outflow_vs_baseline_pct | 0.076 en [0.03, 0.15] |  |  | OK |
| IV outflow_vs_baseline_pct (High) | 0.110 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: outflow_vs_baseline_pct | lift = 2.37 |  |  | OK |
| forma en U (ambas colas > centro): outflow_vs_baseline_pct | tasa extremos 0.087 / 0.110 vs centro 0.049 (tendencia lineal z = 2.3) |  |  | OK |
| IV mediano entre semillas en banda (±0.03): external_transfer_pct_of_balance_60d | mediana 0.292 (p10–p90 0.259–0.331) en [0.3, 0.5] |  |  | OK |
| alerta en rango en todas las semillas: external_transfer_pct_of_balance_60d | 0.061–0.067 |  |  | OK |
| IV mediano entre semillas en banda (±0.03): new_external_destinations_90d | mediana 0.264 (p10–p90 0.226–0.316) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: new_external_destinations_90d | 0.054–0.061 |  |  | OK |
| IV mediano entre semillas en banda (±0.03): transfer_to_competitor_pct_90d | mediana 0.295 (p10–p90 0.265–0.348) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: transfer_to_competitor_pct_90d | 0.048–0.052 |  |  | OK |
| IV mediano entre semillas en banda (±0.03): external_transfer_acceleration | mediana 0.202 (p10–p90 0.184–0.230) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: external_transfer_acceleration | 0.039–0.045 |  |  | OK |
| IV mediano entre semillas en banda (±0.03): net_external_flow_pct_90d | mediana 0.254 (p10–p90 0.230–0.282) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: net_external_flow_pct_90d | 0.047–0.052 |  |  | OK |
| IV mediano entre semillas en banda (±0.03): external_destination_concentration | mediana 0.225 (p10–p90 0.198–0.256) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: external_destination_concentration | 0.057–0.061 |  |  | OK |
| IV mediano entre semillas en banda (±0.03): outflow_vs_baseline_pct | mediana 0.112 (p10–p90 0.081–0.134) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: outflow_vs_baseline_pct | 0.071–0.078 |  |  | OK |

## 6 · Fuga (generador) y AUC

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| ruido ⟂ índice de riesgo: fracción de fondo sorteada | ρ = -0.0065 | 0.357 | 0.669 | OK |
| ruido ⟂ índice de riesgo: nº de destinos esporádicos | ρ = -0.0054 | 0.446 | 0.669 | OK |
| ruido ⟂ índice de riesgo: nº de destinos habituales | ρ = -0.0020 | 0.776 | 0.776 | OK |
| AUC combinado (Pasos 1–3) < AUC techo | 0.656 vs techo 0.851 |  |  | OK |

## Distribuciones

|                                        |       count |         mean |            std |               min |              1% |            5% |         25% |          50% |          75% |            95% |             99% |              max |
|:---------------------------------------|------------:|-------------:|---------------:|------------------:|----------------:|--------------:|------------:|-------------:|-------------:|---------------:|----------------:|-----------------:|
| external_transfer_amount_60d           | 19,984.0000 | 639,902.9906 | 7,965,861.7781 |            0.0000 |        579.7629 |    1,736.5190 |  6,896.5075 |  18,331.5050 |  51,815.2100 |   984,950.6310 | 12,124,978.1907 | 486,622,004.1700 |
| external_transfer_pct_of_balance_60d   | 19,984.0000 |       0.1227 |         0.7209 |            0.0000 |          0.0011 |        0.0022 |      0.0051 |       0.0086 |       0.0147 |         0.4265 |          3.0365 |          30.2129 |
| external_transfer_pct_of_balance_30d   | 20,000.0000 |       0.1038 |         0.8265 |            0.0000 |          0.0000 |        0.0007 |      0.0021 |       0.0040 |       0.0073 |         0.1660 |          2.8836 |          42.9828 |
| new_external_destinations_30d          | 19,459.0000 |       0.0310 |         0.2048 |            0.0000 |          0.0000 |        0.0000 |      0.0000 |       0.0000 |       0.0000 |         0.0000 |          1.0000 |           3.0000 |
| new_external_destinations_90d          | 19,304.0000 |       0.0774 |         0.3305 |            0.0000 |          0.0000 |        0.0000 |      0.0000 |       0.0000 |       0.0000 |         1.0000 |          2.0000 |           3.0000 |
| transfer_to_competitor_bank_amount_90d | 19,968.0000 | 460,226.3076 | 6,959,720.1638 |            0.0000 |          0.0000 |        0.0000 |  2,837.1850 |  12,837.2300 |  41,135.0350 |   480,584.5115 |  8,099,165.8307 | 584,944,277.1800 |
| transfer_to_competitor_pct_90d         | 19,968.0000 |       0.0664 |         0.4123 |            0.0000 |          0.0000 |        0.0000 |      0.0027 |       0.0072 |       0.0139 |         0.1091 |          1.5909 |          18.4920 |
| external_transfer_acceleration         | 19,968.0000 |       0.0206 |         0.8502 |          -30.7044 |         -0.8637 |       -0.0184 |     -0.0036 |       0.0004 |       0.0046 |         0.0391 |          1.9589 |          22.5993 |
| external_outflow_pct_30d               | 19,968.0000 |       0.0601 |         0.4228 |            0.0000 |          0.0000 |        0.0007 |      0.0021 |       0.0040 |       0.0073 |         0.1419 |          1.6375 |          22.6123 |
| net_external_flow_30d                  | 19,995.0000 |  45,605.2226 | 2,001,922.8934 | -115,233,248.3900 | -1,854,155.6810 | -123,430.9860 | -9,652.5600 |    -711.2100 |  92,141.8850 |   627,510.1780 |  2,162,369.4442 | 113,656,538.0600 |
| net_external_flow_90d                  | 19,968.0000 | 119,864.8769 | 4,799,361.5048 | -290,613,733.1100 | -5,999,078.9826 | -367,269.2760 | 15,599.7900 | 120,576.3250 | 366,662.1200 | 1,572,123.6025 |  4,753,989.3947 | 134,202,884.2700 |
| net_external_flow_pct_90d              | 19,968.0000 |       0.0774 |         0.2473 |           -6.2912 |         -0.9633 |       -0.1632 |      0.0112 |       0.0812 |       0.1709 |         0.3444 |          0.5339 |           3.9778 |
| external_destination_concentration     | 19,968.0000 |       0.5983 |         0.2577 |            0.1710 |          0.2292 |        0.2759 |      0.3814 |       0.5159 |       0.9121 |         1.0000 |          1.0000 |           1.0000 |
| external_outflow_pct_90d               | 19,968.0000 |       0.1472 |         0.7584 |            0.0001 |          0.0020 |        0.0038 |      0.0082 |       0.0134 |       0.0223 |         0.6738 |          3.2699 |          22.7572 |
| outflow_vs_baseline_pct                | 19,847.0000 |       4.4662 |        79.7091 |           -1.0000 |         -1.0000 |       -0.9729 |     -0.7795 |      -0.4553 |       0.0504 |         1.5482 |         83.6435 |       6,378.7637 |

## Correlación de Spearman (Pasos 1–3)

|                                      |   aum_outflow_pct_90d |   deposit_balance_change_pct_90d |   aum_vs_baseline_pct |   deposit_balance_vs_6m_avg_pct |   salary_deposit_stopped_flag |   recurring_deposit_stopped_flag |   recurring_deposit_change_pct |   net_deposit_flow_pct_90d |   pension_deposit_stopped_flag |   business_payroll_stopped_flag |   external_transfer_pct_of_balance_60d |   new_external_destinations_90d |   transfer_to_competitor_pct_90d |   external_transfer_acceleration |   net_external_flow_pct_90d |   external_destination_concentration |   outflow_vs_baseline_pct |
|:-------------------------------------|----------------------:|---------------------------------:|----------------------:|--------------------------------:|------------------------------:|---------------------------------:|-------------------------------:|---------------------------:|-------------------------------:|--------------------------------:|---------------------------------------:|--------------------------------:|---------------------------------:|---------------------------------:|----------------------------:|-------------------------------------:|--------------------------:|
| aum_outflow_pct_90d                  |                  1.00 |                            -0.18 |                 -0.77 |                           -0.21 |                          0.21 |                             0.14 |                          -0.06 |                      -0.21 |                           0.14 |                            0.12 |                                   0.16 |                            0.32 |                             0.12 |                             0.07 |                       -0.32 |                                 0.07 |                      0.06 |
| deposit_balance_change_pct_90d       |                 -0.18 |                             1.00 |                  0.19 |                            0.88 |                         -0.22 |                            -0.16 |                           0.06 |                       0.80 |                          -0.17 |                           -0.08 |                                  -0.14 |                           -0.25 |                            -0.12 |                            -0.05 |                        0.63 |                                -0.08 |                      0.06 |
| aum_vs_baseline_pct                  |                 -0.77 |                             0.19 |                  1.00 |                            0.21 |                         -0.23 |                            -0.16 |                           0.06 |                       0.19 |                          -0.17 |                           -0.11 |                                  -0.15 |                           -0.29 |                            -0.12 |                            -0.06 |                        0.34 |                                -0.07 |                     -0.02 |
| deposit_balance_vs_6m_avg_pct        |                 -0.21 |                             0.88 |                  0.21 |                            1.00 |                         -0.22 |                            -0.17 |                           0.06 |                       0.91 |                          -0.17 |                           -0.09 |                                  -0.16 |                           -0.29 |                            -0.13 |                            -0.05 |                        0.69 |                                -0.08 |                      0.05 |
| salary_deposit_stopped_flag          |                  0.21 |                            -0.22 |                 -0.23 |                           -0.22 |                          1.00 |                             0.77 |                          -0.28 |                      -0.21 |                           0.57 |                            0.15 |                                   0.22 |                            0.42 |                             0.23 |                             0.03 |                       -0.19 |                                 0.10 |                      0.02 |
| recurring_deposit_stopped_flag       |                  0.14 |                            -0.16 |                 -0.16 |                           -0.17 |                          0.77 |                             1.00 |                          -0.21 |                      -0.15 |                           0.73 |                            0.09 |                                   0.16 |                            0.29 |                             0.17 |                             0.03 |                       -0.14 |                                 0.09 |                      0.00 |
| recurring_deposit_change_pct         |                 -0.06 |                             0.06 |                  0.06 |                            0.06 |                         -0.28 |                            -0.21 |                           1.00 |                       0.06 |                          -0.18 |                           -0.07 |                                  -0.07 |                           -0.13 |                            -0.08 |                            -0.02 |                        0.05 |                                -0.03 |                     -0.01 |
| net_deposit_flow_pct_90d             |                 -0.21 |                             0.80 |                  0.19 |                            0.91 |                         -0.21 |                            -0.15 |                           0.06 |                       1.00 |                          -0.15 |                           -0.07 |                                  -0.15 |                           -0.29 |                            -0.13 |                            -0.05 |                        0.76 |                                -0.07 |                      0.03 |
| pension_deposit_stopped_flag         |                  0.14 |                            -0.17 |                 -0.17 |                           -0.17 |                          0.57 |                             0.73 |                          -0.18 |                      -0.15 |                           1.00 |                            0.09 |                                   0.16 |                            0.29 |                             0.18 |                             0.06 |                       -0.15 |                                 0.09 |                      0.02 |
| business_payroll_stopped_flag        |                  0.12 |                            -0.08 |                 -0.11 |                           -0.09 |                          0.15 |                             0.09 |                          -0.07 |                      -0.07 |                           0.09 |                            1.00 |                                   0.04 |                            0.13 |                             0.05 |                             0.03 |                       -0.06 |                                 0.03 |                     -0.00 |
| external_transfer_pct_of_balance_60d |                  0.16 |                            -0.14 |                 -0.15 |                           -0.16 |                          0.22 |                             0.16 |                          -0.07 |                      -0.15 |                           0.16 |                            0.04 |                                   1.00 |                            0.35 |                             0.55 |                            -0.06 |                       -0.17 |                                 0.04 |                      0.51 |
| new_external_destinations_90d        |                  0.32 |                            -0.25 |                 -0.29 |                           -0.29 |                          0.42 |                             0.29 |                          -0.13 |                      -0.29 |                           0.29 |                            0.13 |                                   0.35 |                            1.00 |                             0.24 |                             0.15 |                       -0.31 |                                 0.15 |                      0.16 |
| transfer_to_competitor_pct_90d       |                  0.12 |                            -0.12 |                 -0.12 |                           -0.13 |                          0.23 |                             0.17 |                          -0.08 |                      -0.13 |                           0.18 |                            0.05 |                                   0.55 |                            0.24 |                             1.00 |                             0.05 |                       -0.13 |                                -0.02 |                      0.25 |
| external_transfer_acceleration       |                  0.07 |                            -0.05 |                 -0.06 |                           -0.05 |                          0.03 |                             0.03 |                          -0.02 |                      -0.05 |                           0.06 |                            0.03 |                                  -0.06 |                            0.15 |                             0.05 |                             1.00 |                       -0.06 |                                 0.03 |                      0.28 |
| net_external_flow_pct_90d            |                 -0.32 |                             0.63 |                  0.34 |                            0.69 |                         -0.19 |                            -0.14 |                           0.05 |                       0.76 |                          -0.15 |                           -0.06 |                                  -0.17 |                           -0.31 |                            -0.13 |                            -0.06 |                        1.00 |                                -0.08 |                     -0.05 |
| external_destination_concentration   |                  0.07 |                            -0.08 |                 -0.07 |                           -0.08 |                          0.10 |                             0.09 |                          -0.03 |                      -0.07 |                           0.09 |                            0.03 |                                   0.04 |                            0.15 |                            -0.02 |                             0.03 |                       -0.08 |                                 1.00 |                     -0.01 |
| outflow_vs_baseline_pct              |                  0.06 |                             0.06 |                 -0.02 |                            0.05 |                          0.02 |                             0.00 |                          -0.01 |                       0.03 |                           0.02 |                           -0.00 |                                   0.51 |                            0.16 |                             0.25 |                             0.28 |                       -0.05 |                                -0.01 |                      1.00 |

## WoE · external_transfer_pct_of_balance_60d

| row_0                   |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [0, 0.003051]        |  1,884.0000 | 103.0000 |        0.0518 | -0.1599 | 0.0024 |
| 01 [0.003051, 0.004484] |  1,890.0000 |  96.0000 |        0.0483 | -0.2331 | 0.0049 |
| 02 [0.004485, 0.005771] |  1,903.0000 |  83.0000 |        0.0418 | -0.3846 | 0.0125 |
| 03 [0.005772, 0.007104] |  1,893.0000 |  93.0000 |        0.0468 | -0.2662 | 0.0063 |
| 04 [0.007106, 0.008632] |  1,892.0000 |  94.0000 |        0.0473 | -0.2551 | 0.0058 |
| 05 [0.008633, 0.01045]  |  1,891.0000 |  95.0000 |        0.0478 | -0.2440 | 0.0054 |
| 06 [0.01045, 0.01302]   |  1,905.0000 |  81.0000 |        0.0408 | -0.4099 | 0.0141 |
| 07 [0.01302, 0.01701]   |  1,891.0000 |  95.0000 |        0.0478 | -0.2440 | 0.0054 |
| 08 [0.01701, 0.02879]   |  1,885.0000 | 101.0000 |        0.0509 | -0.1799 | 0.0030 |
| 09 [0.02884, 30.21]     |  1,629.0000 | 357.0000 |        0.1798 |  1.2251 | 0.2571 |

## WoE · new_external_destinations_90d

| row_0     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:----------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0    | 17,142.0000 | 899.0000 |        0.0498 | -0.1964 | 0.0333 |
| 01 [1, 1] |    108.0000 |  19.0000 |        0.1496 |  1.0348 | 0.0113 |
| 02 [1, 1] |     98.0000 |  29.0000 |        0.2283 |  1.5454 | 0.0311 |
| 03 [1, 1] |     95.0000 |  32.0000 |        0.2520 |  1.6732 | 0.0383 |
| 04 [1, 1] |    101.0000 |  25.0000 |        0.1984 |  1.3697 | 0.0226 |
| 05 [1, 1] |     98.0000 |  29.0000 |        0.2283 |  1.5454 | 0.0311 |
| 06 [1, 1] |    107.0000 |  20.0000 |        0.1575 |  1.0940 | 0.0129 |
| 07 [1, 2] |     96.0000 |  30.0000 |        0.2381 |  1.5993 | 0.0338 |
| 08 [2, 2] |     92.0000 |  35.0000 |        0.2756 |  1.7934 | 0.0461 |
| 09 [2, 3] |     98.0000 |  29.0000 |        0.2283 |  1.5454 | 0.0311 |

## WoE · transfer_to_competitor_pct_90d

| row_0                    |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:-------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0                   |  2,968.0000 | 156.0000 |        0.0499 | -0.2016 | 0.0059 |
| 01 [1.453e-05, 0.002755] |  1,768.0000 |  90.0000 |        0.0484 | -0.2314 | 0.0045 |
| 02 [0.002757, 0.004398]  |  1,770.0000 |  88.0000 |        0.0474 | -0.2549 | 0.0054 |
| 03 [0.0044, 0.006009]    |  1,770.0000 |  88.0000 |        0.0474 | -0.2549 | 0.0054 |
| 04 [0.006011, 0.007801]  |  1,778.0000 |  80.0000 |        0.0431 | -0.3541 | 0.0101 |
| 05 [0.007803, 0.009908]  |  1,781.0000 |  76.0000 |        0.0409 | -0.4068 | 0.0130 |
| 06 [0.009909, 0.01268]   |  1,759.0000 |  99.0000 |        0.0533 | -0.1315 | 0.0015 |
| 07 [0.01268, 0.01704]    |  1,774.0000 |  84.0000 |        0.0452 | -0.3034 | 0.0076 |
| 08 [0.01704, 0.02762]    |  1,757.0000 | 101.0000 |        0.0544 | -0.1105 | 0.0011 |
| 09 [0.02762, 18.49]      |  1,522.0000 | 336.0000 |        0.1808 |  1.2316 | 0.2440 |

## WoE · external_transfer_acceleration

| row_0                      |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:---------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-30.7, -0.009846]      |  1,808.0000 | 177.0000 |        0.0892 |  0.4199 | 0.0212 |
| 01 [-0.009842, -0.004896]  |  1,900.0000 |  84.0000 |        0.0423 | -0.3720 | 0.0118 |
| 02 [-0.004896, -0.002524]  |  1,894.0000 |  91.0000 |        0.0458 | -0.2892 | 0.0074 |
| 03 [-0.002524, -0.0009018] |  1,884.0000 | 100.0000 |        0.0504 | -0.1901 | 0.0033 |
| 04 [-0.0009014, 0.00037]   |  1,880.0000 | 105.0000 |        0.0529 | -0.1394 | 0.0018 |
| 05 [0.0003707, 0.001727]   |  1,902.0000 |  82.0000 |        0.0413 | -0.3970 | 0.0133 |
| 06 [0.001727, 0.003504]    |  1,887.0000 |  97.0000 |        0.0489 | -0.2220 | 0.0045 |
| 07 [0.003506, 0.00602]     |  1,893.0000 |  92.0000 |        0.0463 | -0.2778 | 0.0068 |
| 08 [0.006021, 0.01198]     |  1,900.0000 |  84.0000 |        0.0423 | -0.3720 | 0.0118 |
| 09 [0.01199, 22.6]         |  1,699.0000 | 286.0000 |        0.1441 |  0.9608 | 0.1413 |

## WoE · net_external_flow_pct_90d

| row_0                    |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:-------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-6.291, -0.01792]    |  1,652.0000 | 333.0000 |        0.1678 |  1.1407 | 0.2152 |
| 01 [-0.01789, -0.003227] |  1,887.0000 |  97.0000 |        0.0489 | -0.2220 | 0.0045 |
| 02 [-0.003226, 0.02491]  |  1,890.0000 |  95.0000 |        0.0479 | -0.2443 | 0.0054 |
| 03 [0.02492, 0.05292]    |  1,897.0000 |  87.0000 |        0.0439 | -0.3355 | 0.0097 |
| 04 [0.05292, 0.08088]    |  1,881.0000 | 104.0000 |        0.0524 | -0.1495 | 0.0021 |
| 05 [0.0809, 0.111]       |  1,889.0000 |  95.0000 |        0.0479 | -0.2438 | 0.0053 |
| 06 [0.111, 0.148]        |  1,882.0000 | 102.0000 |        0.0514 | -0.1694 | 0.0027 |
| 07 [0.148, 0.1963]       |  1,894.0000 |  91.0000 |        0.0458 | -0.2892 | 0.0074 |
| 08 [0.1964, 0.2709]      |  1,889.0000 |  95.0000 |        0.0479 | -0.2438 | 0.0053 |
| 09 [0.271, 3.978]        |  1,886.0000 |  99.0000 |        0.0499 | -0.2012 | 0.0037 |

## WoE · external_destination_concentration

| row_0               |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:--------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [0.171, 0.3082]  |  1,669.0000 |  82.0000 |        0.0468 | -0.2663 | 0.0056 |
| 01 [0.3082, 0.3523] |  1,666.0000 |  85.0000 |        0.0485 | -0.2288 | 0.0042 |
| 02 [0.3523, 0.3883] |  1,658.0000 |  93.0000 |        0.0531 | -0.1346 | 0.0015 |
| 03 [0.3884, 0.4666] |  1,673.0000 |  78.0000 |        0.0445 | -0.3184 | 0.0078 |
| 04 [0.4667, 0.5045] |  1,651.0000 |  99.0000 |        0.0566 | -0.0681 | 0.0004 |
| 05 [0.5045, 0.5242] |  1,659.0000 |  92.0000 |        0.0525 | -0.1459 | 0.0018 |
| 06 [0.5242, 0.5669] |  1,651.0000 | 100.0000 |        0.0571 | -0.0581 | 0.0003 |
| 07 [0.5669, 0.6995] |  1,641.0000 | 110.0000 |        0.0628 |  0.0428 | 0.0002 |
| 08 [0.6995, 0.9999] |  1,466.0000 | 285.0000 |        0.1628 |  1.1047 | 0.1753 |
| 09 = 1              |  3,913.0000 | 174.0000 |        0.0426 | -0.3691 | 0.0239 |

## WoE · outflow_vs_baseline_pct

| row_0                  |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:-----------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-1, -0.9273]       |  1,801.0000 | 172.0000 |        0.0872 |  0.3975 | 0.0189 |
| 01 [-0.9272, -0.832]   |  1,864.0000 | 108.0000 |        0.0548 | -0.1005 | 0.0010 |
| 02 [-0.8319, -0.7256]  |  1,891.0000 |  81.0000 |        0.0411 | -0.4010 | 0.0135 |
| 03 [-0.7256, -0.6018]  |  1,861.0000 | 112.0000 |        0.0568 | -0.0627 | 0.0004 |
| 04 [-0.6017, -0.4551]  |  1,873.0000 |  99.0000 |        0.0502 | -0.1919 | 0.0034 |
| 05 [-0.4548, -0.2881]  |  1,874.0000 |  98.0000 |        0.0497 | -0.2025 | 0.0038 |
| 06 [-0.2881, -0.07869] |  1,874.0000 |  99.0000 |        0.0502 | -0.1924 | 0.0034 |
| 07 [-0.07825, 0.207]   |  1,881.0000 |  91.0000 |        0.0461 | -0.2800 | 0.0069 |
| 08 [0.207, 0.754]      |  1,862.0000 | 110.0000 |        0.0558 | -0.0811 | 0.0006 |
| 09 [0.7543, 6379]      |  1,755.0000 | 218.0000 |        0.1105 |  0.6598 | 0.0584 |

## Diccionario

| Columna | Unidad | Descripción |
|---|---|---|
| household_id | id | Identificador del hogar |
| external_transfer_amount_60d | USD | #7 · transferencias externas (wire, ACH, ACATS) 60d, sin excluidos |
| external_transfer_pct_of_balance_60d | fracción | #7 · ÷ saldo promedio (depósitos + cash en inversión) (alerta > 15%) |
| external_transfer_pct_of_balance_30d | fracción | #7 · versión 30d |
| new_external_destinations_30d | entero | #8 · destinos nuevos en 30d (acumulado ≥ $50k, ausentes 12m previos) |
| new_external_destinations_90d | entero | #8 · versión 90d (principal, D-18) |
| transfer_to_competitor_bank_amount_90d | USD | #21 · enviado a bancos del catálogo de competidores, 90d |
| transfer_to_competitor_pct_90d | fracción | #21 · ÷ saldo promedio (alerta > 10%) |
| external_transfer_acceleration | fracción | #22 · [(A1 − A2) − (A2 − A3)] ÷ saldo promedio 90d |
| external_outflow_pct_30d | fracción | #22 · A1 ÷ saldo (condición de alerta: > 5%) |
| net_external_flow_30d | USD± | #23 · entradas − salidas externas, 30d |
| net_external_flow_90d | USD± | #23 · entradas − salidas externas, 90d |
| net_external_flow_pct_90d | fracción | #23 · ÷ saldo promedio (alerta ≤ −15%) |
| external_destination_concentration | fracción | #24 · HHI por institución (no por ABA), 90d |
| external_outflow_pct_90d | fracción | #24 · salidas 90d ÷ saldo (condición de alerta: > 10%) |
| outflow_vs_baseline_pct | fracción | #25 · salidas último mes ÷ promedio mensual meses −7..−1 (piso $10k) − 1 |
