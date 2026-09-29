# Paso 5 · Relationship & closures

Semilla `20260928` · 20,000 hogares · 153,621 cuentas · montos en USD · **56 de 56 pruebas OK** (α = 0.01, Benjamini-Hochberg)

## Calibración

| variable               | fuerza_excel   | motor   | alerta   |   tasa_alerta |    IV |   lift_alerta |   tendencia_z |   null_% |
|:-----------------------|:---------------|:--------|:---------|--------------:|------:|--------------:|--------------:|---------:|
| products_closed_180d   | Very high      | mixed   | >= 1     |         0.097 | 0.361 |         3.364 |        28.551 |    0.533 |
| accounts_closed_90d    | High           | mixed   | >= 1     |         0.143 | 0.234 |         1.890 |        22.621 |    0.161 |
| share_of_wallet        | High           | mixed   | <= 0.30  |         0.267 | 0.265 |         2.206 |        15.459 |    0.000 |
| share_of_wallet_change | High           | mixed   | <= -0.10 |         0.137 | 0.225 |         2.655 |        13.483 |    0.770 |
| trustee_change_flag    | High           | mixed   | = 1      |         0.046 | 0.206 |         3.835 |         8.674 |   68.199 |

AUC combinado de las variables de los Pasos 1–5 (logística): **0.696**; techo: 0.851.

## Robustez en 20 semillas de referencia

| variable               |   ('tasa_alerta', 'min') |   ('tasa_alerta', 'median') |   ('tasa_alerta', 'max') |   ('IV', 'min') |   ('IV', 'median') |   ('IV', 'max') |   ('lift_alerta', 'min') |   ('lift_alerta', 'median') |   ('lift_alerta', 'max') |
|:-----------------------|-------------------------:|----------------------------:|-------------------------:|----------------:|-------------------:|----------------:|-------------------------:|----------------------------:|-------------------------:|
| accounts_closed_90d    |                    0.136 |                       0.140 |                    0.144 |           0.179 |              0.229 |           0.275 |                    1.782 |                       1.977 |                    2.204 |
| products_closed_180d   |                    0.090 |                       0.094 |                    0.097 |           0.296 |              0.370 |           0.434 |                    3.135 |                       3.434 |                    3.795 |
| share_of_wallet        |                    0.229 |                       0.258 |                    0.278 |           0.195 |              0.235 |           0.305 |                    2.051 |                       2.225 |                    2.491 |
| share_of_wallet_change |                    0.114 |                       0.134 |                    0.153 |           0.165 |              0.222 |           0.272 |                    2.341 |                       2.716 |                    2.988 |
| trustee_change_flag    |                    0.037 |                       0.042 |                    0.047 |           0.106 |              0.185 |           0.277 |                    2.784 |                       3.660 |                    4.604 |

## Cierres por motivo

| close_reason           |   cuentas |
|:-----------------------|----------:|
| conversion             |      3377 |
| moved_relationship     |      2622 |
| consolidation          |      2539 |
| cd_renewed             |      1641 |
| cd_matured_not_renewed |       740 |
| client_request         |       660 |
| loan_paid_at_term      |       285 |

## 1 · Cuentas, cierres y reglas del Excel

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| columnas declaradas con unidad |  |  |  | OK |
| todo hogar tiene cuenta de cheques |  |  |  | OK |
| brokerage ⇔ has_investments |  |  |  | OK |
| advisory ⇔ has_advisory |  |  |  | OK |
| trust ⇔ has_trust |  |  |  | OK |
| business_account ⇔ has_linked_business |  |  |  | OK |
| cierres con fecha ≤ t | 11,864 cierres |  |  | OK |
| productos cerrados ≤ cuentas cerradas (90d) |  |  |  | OK |
| exclusiones del Excel reducen productos cerrados (180d) | 3,189 contados vs 10,559 sin excluir (cd_renewed, consolidation, conversion, loan_paid_at_term) |  |  | OK |
| consolidación interna excluida de cuentas cerradas | 2,526 consolidaciones |  |  | OK |
| coherencia: quien se muda cierra más productos (180d) | 1.94 vs 0.07 |  |  | OK |

## 2 · Share of wallet y trustee

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| SOW en (0, 1] | mediana 0.46; tope en 1: 5.9% |  |  | OK |
| fuente de la estimación registrada | {'vendor': 0.45, 'declared': 0.4, 'model': 0.15} |  |  | OK |
| cambio de SOW en [−1, 1] |  |  |  | OK |
| coherencia: quien se muda pierde share | mediana -0.196 vs -0.003 |  |  | OK |
| reestimar el patrimonio agrega ruido al cambio de SOW (advertencia del Excel) | d.e. 0.219 vs 0.102 |  |  | OK |
| error de estimación: declarado < proveedor < modelo | {'declared': 0.067, 'model': 0.332, 'vendor': 0.233} |  |  | OK |
| trustee NULL ⇔ sin trust |  |  |  | OK |
| sucesión por muerte = exclusión (flag 0) | n = 109 |  |  | OK |

## 3 · Calibración (tasa de alerta, IV, tendencia, lift)

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| tasa de alerta products_closed_180d | 0.097 en [0.03, 0.15] |  |  | OK |
| IV products_closed_180d (Very high) | 0.361 en [0.3, 0.5] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: products_closed_180d | lift = 3.36 |  |  | OK |
| tendencia en la dirección esperada: products_closed_180d | z = 28.6 |  |  | OK |
| tasa de alerta accounts_closed_90d | 0.143 en [0.04, 0.2] |  |  | OK |
| IV accounts_closed_90d (High) | 0.234 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: accounts_closed_90d | lift = 1.89 |  |  | OK |
| tendencia en la dirección esperada: accounts_closed_90d | z = 22.6 |  |  | OK |
| tasa de alerta share_of_wallet | 0.267 en [0.1, 0.4] |  |  | OK |
| IV share_of_wallet (High) | 0.265 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: share_of_wallet | lift = 2.21 |  |  | OK |
| tendencia en la dirección esperada: share_of_wallet | z = 15.5 |  |  | OK |
| tasa de alerta share_of_wallet_change | 0.137 en [0.03, 0.2] |  |  | OK |
| IV share_of_wallet_change (High) | 0.225 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: share_of_wallet_change | lift = 2.65 |  |  | OK |
| tendencia en la dirección esperada: share_of_wallet_change | z = 13.5 |  |  | OK |
| tasa de alerta trustee_change_flag | 0.046 en [0.01, 0.08] |  |  | OK |
| IV trustee_change_flag (High) | 0.206 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: trustee_change_flag | lift = 3.83 |  |  | OK |
| tendencia en la dirección esperada: trustee_change_flag | z = 8.7 |  |  | OK |
| IV mediano entre semillas en banda: products_closed_180d | mediana 0.370 (p10–p90 0.334–0.412) en [0.3, 0.5] |  |  | OK |
| alerta en rango en todas las semillas: products_closed_180d | 0.090–0.097 |  |  | OK |
| IV mediano entre semillas en banda: accounts_closed_90d | mediana 0.229 (p10–p90 0.201–0.258) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: accounts_closed_90d | 0.136–0.144 |  |  | OK |
| IV mediano entre semillas en banda: share_of_wallet | mediana 0.235 (p10–p90 0.198–0.276) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: share_of_wallet | 0.229–0.278 |  |  | OK |
| IV mediano entre semillas en banda: share_of_wallet_change | mediana 0.222 (p10–p90 0.178–0.244) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: share_of_wallet_change | 0.114–0.153 |  |  | OK |
| IV mediano entre semillas en banda: trustee_change_flag | mediana 0.185 (p10–p90 0.140–0.225) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: trustee_change_flag | 0.037–0.047 |  |  | OK |

## 4 · Fuga (generador) y AUC

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| SOW verdadero ⟂ ε dado z_outflow (MCO) | coef ε = +0.0053 ± 0.0106; coef z = -0.299 | 0.619 | 0.761 | OK |
| trustee por servicio ⟂ ε dado z_service (Wald) | coef ε = -0.052 | 0.769 | 0.769 | OK |
| ruido cd_matured_not_renewed ⟂ índice de riesgo | ρ = +0.0034 | 0.634 | 0.761 | OK |
| ruido conversion ⟂ índice de riesgo | ρ = -0.0169 | 0.0166 | 0.0994 | OK |
| ruido consolidation ⟂ índice de riesgo | ρ = -0.0035 | 0.618 | 0.761 | OK |
| ruido loan_paid_at_term ⟂ índice de riesgo | ρ = -0.0124 | 0.0793 | 0.238 | OK |
| AUC combinado (Pasos 1–5) < AUC techo | 0.696 vs techo 0.851 |  |  | OK |

## Distribuciones

|                        |       count |    mean |    std |     min |      1% |      5% |     25% |     50% |    75% |    95% |    99% |     max |
|:-----------------------|------------:|--------:|-------:|--------:|--------:|--------:|--------:|--------:|-------:|-------:|-------:|--------:|
| products_closed_90d    | 19,968.0000 |  0.1014 | 0.4907 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 | 0.0000 | 1.0000 | 3.0000 |  6.0000 |
| accounts_closed_90d    | 19,968.0000 |  0.2225 | 0.7537 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 | 0.0000 | 1.0000 | 4.0000 | 12.0000 |
| products_closed_180d   | 19,894.0000 |  0.1603 | 0.5898 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 | 0.0000 | 1.0000 | 3.0000 |  6.0000 |
| accounts_closed_180d   | 19,894.0000 |  0.3827 | 0.9183 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 | 1.0000 | 2.0000 | 5.0000 | 12.0000 |
| share_of_wallet        | 20,000.0000 |  0.4890 | 0.2539 |  0.0001 |  0.0535 |  0.1211 |  0.2904 |  0.4598 | 0.6632 | 1.0000 | 1.0000 |  1.0000 |
| share_of_wallet_change | 19,847.0000 | -0.0206 | 0.1186 | -0.9726 | -0.4525 | -0.2246 | -0.0459 | -0.0049 | 0.0209 | 0.1289 | 0.3084 |  0.8945 |
| trustee_change_flag    |  6,374.0000 |  0.0457 | 0.2088 |  0.0000 |  0.0000 |  0.0000 |  0.0000 |  0.0000 | 0.0000 | 0.0000 | 1.0000 |  1.0000 |

## WoE · products_closed_180d

| row_0     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:----------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0    | 16,972.0000 | 873.0000 |        0.0489 | -0.2226 | 0.0406 |
| 01 = 1    |  1,156.0000 | 109.0000 |        0.0862 |  0.3870 | 0.0114 |
| 02 [2, 2] |     66.0000 |  17.0000 |        0.2048 |  1.4093 | 0.0156 |
| 03 [2, 2] |     61.0000 |  22.0000 |        0.2651 |  1.7387 | 0.0270 |
| 04 [2, 2] |     61.0000 |  21.0000 |        0.2561 |  1.6933 | 0.0249 |
| 05 [2, 3] |     54.0000 |  29.0000 |        0.3494 |  2.1305 | 0.0463 |
| 06 [3, 3] |     55.0000 |  27.0000 |        0.3293 |  2.0421 | 0.0409 |
| 07 [3, 4] |     53.0000 |  30.0000 |        0.3614 |  2.1823 | 0.0494 |
| 08 [4, 4] |     50.0000 |  32.0000 |        0.3902 |  2.3035 | 0.0564 |
| 09 [4, 6] |     53.0000 |  30.0000 |        0.3614 |  2.1823 | 0.0494 |

## WoE · accounts_closed_90d

| row_0      |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:-----------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0     | 16,089.0000 | 910.0000 |        0.0535 | -0.1308 | 0.0138 |
| 01 = 1     |  2,104.0000 | 123.0000 |        0.0552 | -0.0945 | 0.0010 |
| 02 [2, 2]  |     66.0000 |  12.0000 |        0.1538 |  1.0697 | 0.0073 |
| 03 [2, 2]  |     62.0000 |  15.0000 |        0.1948 |  1.3468 | 0.0128 |
| 04 [2, 2]  |     63.0000 |  14.0000 |        0.1818 |  1.2642 | 0.0109 |
| 05 [2, 3]  |     63.0000 |  15.0000 |        0.1923 |  1.3309 | 0.0126 |
| 06 [3, 4]  |     54.0000 |  23.0000 |        0.2987 |  1.8999 | 0.0316 |
| 07 [4, 5]  |     50.0000 |  27.0000 |        0.3506 |  2.1333 | 0.0430 |
| 08 [5, 6]  |     46.0000 |  31.0000 |        0.4026 |  2.3517 | 0.0557 |
| 09 [6, 12] |     50.0000 |  28.0000 |        0.3590 |  2.1691 | 0.0455 |

## WoE · share_of_wallet

| row_0                  |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:-----------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [7.702e-05, 0.1765] |  1,760.0000 | 318.0000 |        0.1530 |  1.0314 | 0.1754 |
| 01 [0.1766, 0.2624]    |  1,933.0000 | 144.0000 |        0.0693 |  0.1473 | 0.0024 |
| 02 [0.2624, 0.3328]    |  1,933.0000 | 144.0000 |        0.0693 |  0.1473 | 0.0024 |
| 03 [0.3328, 0.4029]    |  1,969.0000 | 108.0000 |        0.0520 | -0.1577 | 0.0024 |
| 04 [0.4029, 0.474]     |  1,972.0000 | 106.0000 |        0.0510 | -0.1778 | 0.0031 |
| 05 [0.4742, 0.5524]    |  1,985.0000 |  92.0000 |        0.0443 | -0.3253 | 0.0096 |
| 06 [0.5524, 0.6462]    |  1,990.0000 |  87.0000 |        0.0419 | -0.3834 | 0.0130 |
| 07 [0.6462, 0.7636]    |  1,992.0000 |  85.0000 |        0.0409 | -0.4075 | 0.0145 |
| 08 [0.7636, 0.9999]    |  1,996.0000 |  82.0000 |        0.0395 | -0.4453 | 0.0171 |
| 09 = 1                 |  1,147.0000 |  34.0000 |        0.0288 | -0.7633 | 0.0250 |

## WoE · share_of_wallet_change

| row_0                     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:--------------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-0.9726, -0.1384]     |  1,679.0000 | 294.0000 |        0.1490 |  1.0025 | 0.1567 |
| 01 [-0.1384, -0.06393]    |  1,837.0000 | 135.0000 |        0.0685 |  0.1363 | 0.0020 |
| 02 [-0.06392, -0.03395]   |  1,857.0000 | 115.0000 |        0.0583 | -0.0342 | 0.0001 |
| 03 [-0.03395, -0.01667]   |  1,863.0000 | 110.0000 |        0.0558 | -0.0817 | 0.0006 |
| 04 [-0.01667, -0.004902]  |  1,857.0000 | 115.0000 |        0.0583 | -0.0342 | 0.0001 |
| 05 [-0.004891, 0.0009194] |  1,891.0000 |  81.0000 |        0.0411 | -0.4010 | 0.0135 |
| 06 [0.0009277, 0.01285]   |  1,878.0000 |  95.0000 |        0.0482 | -0.2356 | 0.0050 |
| 07 [0.01285, 0.03099]     |  1,873.0000 |  99.0000 |        0.0502 | -0.1919 | 0.0034 |
| 08 [0.031, 0.07159]       |  1,905.0000 |  67.0000 |        0.0340 | -0.5969 | 0.0276 |
| 09 [0.07162, 0.8945]      |  1,896.0000 |  77.0000 |        0.0390 | -0.4540 | 0.0169 |

## WoE · trustee_change_flag

| row_0     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:----------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0    |  5,700.0000 | 332.0000 |        0.0550 | -0.1398 | 0.0175 |
| 01 [1, 1] |     27.0000 |   6.0000 |        0.1818 |  1.2594 | 0.0147 |
| 02 [1, 1] |     23.0000 |   9.0000 |        0.2812 |  1.7961 | 0.0358 |
| 03 [1, 1] |     25.0000 |   7.0000 |        0.2188 |  1.4781 | 0.0215 |
| 04 [1, 1] |     22.0000 |  10.0000 |        0.3125 |  1.9397 | 0.0438 |
| 05 [1, 1] |     25.0000 |   7.0000 |        0.2188 |  1.4781 | 0.0215 |
| 06 [1, 1] |     27.0000 |   5.0000 |        0.1562 |  1.0924 | 0.0100 |
| 07 [1, 1] |     26.0000 |   6.0000 |        0.1875 |  1.2965 | 0.0154 |
| 08 [1, 1] |     27.0000 |   5.0000 |        0.1562 |  1.0924 | 0.0100 |
| 09 [1, 1] |     26.0000 |   6.0000 |        0.1875 |  1.2965 | 0.0154 |

## Diccionario

| Columna | Unidad | Descripción |
|---|---|---|
| household_id | id | Identificador del hogar |
| products_closed_90d | entero | #10 · productos distintos cerrados en 90d (sin CD renovado, préstamo a término, conversión, consolidación) |
| accounts_closed_90d | entero | #29 · cuentas cerradas en 90d (sin consolidación interna ni CD renovado) |
| products_closed_180d | entero | #10 · versión 180d (principal, D-20) |
| accounts_closed_180d | entero | #29 · versión 180d |
| share_of_wallet | fracción | #30 · (AUM + depósitos en Citizens) ÷ patrimonio total estimado, tope 1 (alerta < 30%) |
| wealth_estimate_source | categoría | #30 · fuente de la estimación: declared / vendor / model |
| share_of_wallet_change | fracción | #31 · SOW hoy − SOW hace 6 meses (−0.10 = −10 pp) |
| trustee_change_flag | 0/1 | #32 · Citizens deja de ser trustee o entra uno externo en 12m; NULL sin trust |
