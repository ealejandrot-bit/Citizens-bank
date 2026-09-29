# Comparación de metodologías de score

19,877 hogares (sin excluidos) · partición estratificada 70/30 · semilla derivada de `20260928` · montos en USD.

## 1 · La variable de churn construida

Se simulan los 6 meses posteriores al corte y la etiqueta se construye sobre lo observado (definiciones del deck):

- **Hard churn 6m:** el valor de la relación cae a ≤ 5% del valor en t y no se recupera.
- **Soft churn 3m:** caída del valor ex-mercado > 20% en 3 meses, sin salida total.

|                         |   construida |   evento real (generador) |
|:------------------------|-------------:|--------------------------:|
| hard churn 6m (logo)    |         6.04 |                      6.04 |
| soft churn 3m           |        10.99 |                      8.83 |
| AUM churn (hard, valor) |         6.36 |                      6.46 |

Coincidencia etiqueta construida vs evento real:

|   soft real |     0 |    1 |
|------------:|------:|-----:|
|           0 | 17621 |  500 |
|           1 |    72 | 1684 |

El hard churn coincide al 100%. El soft churn construido tiene **falsos positivos**: hogares que no se estaban contrayendo, pero cruzaron el −20% por una compra de casa o por la volatilidad del saldo; y algunas contracciones reales no llegan al umbral. Es el ruido de etiqueta que tendría el banco, y la razón por la que el deck pide validar el umbral.

## 2 · IV de las 37 variables contra la etiqueta construida

|   # | variable                             |   IV hard (construida) |   IV soft (construida) |
|----:|:-------------------------------------|-----------------------:|-----------------------:|
|   1 | aum_outflow                          |                  0.265 |                  0.188 |
|   2 | deposit_balance_change_pct           |                  0.251 |                  0.027 |
|   3 | salary_deposit_stopped_flag          |                  0.169 |                  0.030 |
|   4 | recurring_deposit_stopped_flag       |                  0.207 |                  0.041 |
|   5 | recurring_deposit_change_pct         |                  0.169 |                  0.027 |
|   6 | net_deposit_flow                     |                  0.238 |                  0.037 |
|   7 | external_transfer_pct_of_balance     |                  0.318 |                  0.043 |
|   8 | new_external_destinations            |                  0.283 |                  0.035 |
|   9 | investment_redemption_pct            |                  0.153 |                  0.176 |
|  10 | products_closed                      |                  0.361 |                  0.047 |
|  11 | banker_change_6m_flag                |                  0.442 |                  0.065 |
|  12 | contact_gap_ratio                    |                  0.173 |                  0.036 |
|  13 | client_reply_rate                    |                  0.287 |                  0.084 |
|  14 | complaint_escalated_flag             |                  0.129 |                  0.023 |
|  15 | complaint_age_days                   |                  0.119 |                  0.021 |
|  16 | multi_signal_flag                    |                  0.636 |                  0.089 |
|  17 | aum_vs_baseline_pct                  |                  0.289 |                  0.189 |
|  18 | deposit_balance_vs_6m_avg_pct        |                  0.289 |                  0.044 |
|  19 | pension_deposit_stopped_flag         |                  0.075 |                  0.025 |
|  20 | business_payroll_stopped_flag        |                  0.042 |                  0.007 |
|  21 | transfer_to_competitor_bank_amount   |                  0.298 |                  0.051 |
|  22 | external_transfer_acceleration       |                  0.224 |                  0.035 |
|  23 | net_external_flow                    |                  0.261 |                  0.038 |
|  24 | external_destination_concentration   |                  0.221 |                  0.017 |
|  25 | outflow_vs_baseline_pct              |                  0.110 |                  0.036 |
|  26 | fixed_income_maturity_not_reinvested |                  0.055 |                  0.023 |
|  27 | cash_pct_of_portfolio_chg            |                  0.125 |                  0.164 |
|  28 | return_vs_benchmark                  |                  0.070 |                  0.073 |
|  29 | accounts_closed                      |                  0.234 |                  0.027 |
|  30 | share_of_wallet                      |                  0.265 |                  0.032 |
|  31 | share_of_wallet_change               |                  0.225 |                  0.066 |
|  32 | trustee_change_flag                  |                  0.068 |                  0.011 |
|  33 | repeat_complaint_flag                |                  0.170 |                  0.020 |
|  34 | positions_liquidated_pct             |                  0.164 |                  0.172 |
|  35 | meetings_cancelled_by_client         |                  0.076 |                  0.024 |
|  36 | relationship_dissatisfaction_flag    |                  0.037 |                  0.012 |
|  37 | bureau_new_mortgage_elsewhere        |                  0.149 |                  0.033 |

## 3 · Hard churn 6 meses (target principal)

Test: 5,963 hogares, churn 6.0%.

### Discriminación y uso operativo (test)

*precisión / recall / lift top 10%*: qué tan bien funciona la lista del 10% más riesgoso que recibe el banker. *captura AUM*: qué parte del valor de los que churnean queda en esa lista.

|                                         |   AUC |   Gini |    KS |   precisión top 10% |   recall top 10% |   lift top 10% |   captura AUM top 10% |   AUC HNW |   AUC UHNW |
|:----------------------------------------|------:|-------:|------:|--------------------:|-----------------:|---------------:|----------------------:|----------:|-----------:|
| M0a · Reglas de negocio                 | 0.545 |  0.091 | 0.111 |               0.112 |            0.186 |          1.862 |                 0.141 |     0.548 |      0.506 |
| M0b · Scorecard experto (deck)          | 0.696 |  0.393 | 0.333 |               0.225 |            0.372 |          3.724 |                 0.509 |     0.695 |      0.714 |
| M1 · Scorecard estadístico (WoE)        | 0.750 |  0.500 | 0.370 |               0.227 |            0.375 |          3.752 |                 0.341 |     0.749 |      0.779 |
| M2 · Gradient Boosting                  | 0.760 |  0.520 | 0.401 |               0.240 |            0.397 |          3.974 |                 0.520 |     0.758 |      0.782 |
| M2 · Logística (challenger)             | 0.766 |  0.533 | 0.406 |               0.240 |            0.397 |          3.974 |                 0.513 |     0.766 |      0.770 |
| M3 · Red neuronal (tabular + secuencia) | 0.753 |  0.506 | 0.386 |               0.233 |            0.386 |          3.863 |                 0.510 |     0.753 |      0.768 |
| Techo · probabilidad verdadera          | 0.859 |  0.719 | 0.561 |               0.326 |            0.539 |          5.392 |                 0.601 |     0.860 |      0.847 |

### Incertidumbre: IC 95% por bootstrap pareado (200 remuestras del test)

La captura de AUM depende de unos pocos hogares muy grandes (cola Pareto), por eso su intervalo es ancho. '¿diferencia real?' = el IC de la diferencia de AUC contra el Gradient Boosting no incluye 0.

|                                         |   AUC p2.5 |   AUC p97.5 |   captura AUM p2.5 |   captura AUM p97.5 |   Δ AUC vs M2 |   Δ p2.5 |   Δ p97.5 | ¿diferencia real?   |
|:----------------------------------------|-----------:|------------:|-------------------:|--------------------:|--------------:|---------:|----------:|:--------------------|
| M0a · Reglas de negocio                 |      0.525 |       0.562 |              0.089 |               0.245 |        -0.216 |   -0.245 |    -0.185 | sí                  |
| M0b · Scorecard experto (deck)          |      0.664 |       0.727 |              0.345 |               0.646 |        -0.065 |   -0.084 |    -0.045 | sí                  |
| M1 · Scorecard estadístico (WoE)        |      0.723 |       0.777 |              0.234 |               0.466 |        -0.011 |   -0.026 |     0.004 | no                  |
| M2 · Gradient Boosting                  |      0.732 |       0.789 |              0.368 |               0.658 |       nan     |  nan     |   nan     | nan                 |
| M2 · Logística (challenger)             |      0.737 |       0.795 |              0.360 |               0.660 |         0.006 |   -0.011 |     0.021 | no                  |
| M3 · Red neuronal (tabular + secuencia) |      0.724 |       0.782 |              0.311 |               0.656 |        -0.008 |   -0.026 |     0.008 | no                  |
| Techo · probabilidad verdadera          |      0.842 |       0.879 |              0.460 |               0.738 |         0.099 |    0.076 |     0.121 | sí                  |

### Calibración (test)

Control del deck (slide 17): el promedio del score debe igualar al churn observado.

|                                         |   prob. media |   churn observado |   Brier |
|:----------------------------------------|--------------:|------------------:|--------:|
| M1 · Scorecard estadístico (WoE)        |        0.0611 |            0.0604 |  0.0513 |
| M2 · Gradient Boosting                  |        0.0585 |            0.0604 |  0.0512 |
| M2 · Logística (challenger)             |        0.0620 |            0.0604 |  0.0512 |
| M3 · Red neuronal (tabular + secuencia) |        0.0620 |            0.0604 |  0.0513 |
| Techo · probabilidad verdadera          |        0.0604 |            0.0604 |  0.0458 |

Calibración por decil · M2 · Logística (challenger):

|    |   prob. media |   churn observado |        n |
|---:|--------------:|------------------:|---------:|
|  1 |        0.0133 |            0.0117 | 597.0000 |
|  2 |        0.0193 |            0.0168 | 596.0000 |
|  3 |        0.0239 |            0.0218 | 596.0000 |
|  4 |        0.0290 |            0.0268 | 596.0000 |
|  5 |        0.0346 |            0.0285 | 597.0000 |
|  6 |        0.0410 |            0.0302 | 596.0000 |
|  7 |        0.0494 |            0.0587 | 596.0000 |
|  8 |        0.0626 |            0.0721 | 596.0000 |
|  9 |        0.0920 |            0.0973 | 596.0000 |
| 10 |        0.2548 |            0.2395 | 597.0000 |

### Bandas de riesgo de los scorecards (test)

| Banda | Experto: % hogares | Experto: churn % | Estadístico: % hogares | Estadístico: churn % |
|---|---|---|---|---|
| Low 0–39 | 95.6 | 4.8 | 68.8 | 3.1 |
| Watch 40–69 | 3.8 | 30.2 | 31.0 | 12.2 |
| High 70–100 | 0.6 | 44.7 | 0.2 | 57.1 |

### Scorecard estadístico: 38 variables seleccionadas (IV ≥ 0.02, |ρ| entre WoE < 0.8)

Descartadas por redundancia: ninguna.

|                                      |    IV |   coef |   puntos máx |
|:-------------------------------------|------:|-------:|-------------:|
| client_reply_rate                    | 0.290 |  0.582 |       10.860 |
| banker_change_6m_flag                | 0.388 |  0.571 |        6.775 |
| share_of_wallet                      | 0.288 |  0.448 |        6.679 |
| return_vs_benchmark                  | 0.081 |  0.525 |        5.946 |
| aum_outflow_pct_90d                  | 0.233 | -0.317 |        5.329 |
| complaint_age_days                   | 0.136 |  0.269 |        4.425 |
| repeat_complaint_flag                | 0.156 |  0.340 |        4.277 |
| contact_gap_ratio                    | 0.187 |  0.368 |        4.150 |
| products_closed_180d                 | 0.374 |  0.185 |        3.626 |
| tenure_years                         | 0.026 |  0.786 |        3.482 |
| business_payroll_stopped_flag        | 0.031 |  0.347 |        3.285 |
| meetings_cancelled_by_client         | 0.056 |  0.328 |        3.208 |
| recurring_deposit_change_pct         | 0.181 |  0.279 |        3.146 |
| deposit_balance_vs_6m_avg_pct        | 0.263 |  0.238 |        2.912 |
| cash_pct_of_portfolio_chg            | 0.106 |  0.305 |        2.737 |
| net_deposit_flow_pct_90d             | 0.190 | -0.221 |        2.541 |
| share_of_wallet_change               | 0.222 |  0.179 |        2.400 |
| external_transfer_pct_of_balance_60d | 0.307 |  0.160 |        2.191 |
| external_transfer_acceleration       | 0.213 |  0.187 |        2.179 |
| trustee_change_flag                  | 0.055 |  0.172 |        2.030 |
| aum_vs_baseline_pct                  | 0.264 |  0.153 |        2.023 |
| complaint_escalated_flag             | 0.133 |  0.180 |        1.852 |
| investment_redemption_pct            | 0.131 |  0.140 |        1.709 |
| external_destination_concentration   | 0.239 |  0.122 |        1.522 |
| deposit_balance_change_pct_90d       | 0.212 | -0.132 |        1.484 |
| transfer_to_competitor_pct_90d       | 0.326 |  0.088 |        1.348 |
| net_external_flow_pct_90d            | 0.228 | -0.099 |        1.143 |
| relationship_dissatisfaction_flag    | 0.029 | -0.108 |        1.052 |
| outflow_vs_baseline_pct              | 0.113 |  0.116 |        1.019 |
| bureau_new_mortgage_elsewhere        | 0.134 |  0.074 |        0.866 |
| pension_deposit_stopped_flag         | 0.059 | -0.051 |        0.837 |
| new_external_destinations_90d        | 0.240 | -0.040 |        0.566 |
| salary_deposit_stopped_flag          | 0.175 | -0.032 |        0.525 |
| accounts_closed_90d                  | 0.241 |  0.024 |        0.475 |
| positions_liquidated_pct             | 0.125 |  0.036 |        0.472 |
| recurring_deposit_stopped_flag       | 0.194 | -0.031 |        0.411 |
| multi_signal_count                   | 0.597 | -0.014 |        0.319 |
| fixed_income_maturity_not_reinvested | 0.044 |  0.021 |        0.197 |

### Principales drivers del Gradient Boosting (importancia por permutación, test)

|                                      |   caída de AUC al permutar |   d.e. |
|:-------------------------------------|---------------------------:|-------:|
| banker_change_6m_flag                |                     0.0548 | 0.0069 |
| client_reply_rate                    |                     0.0299 | 0.0142 |
| multi_signal_count                   |                     0.0107 | 0.0018 |
| contact_gap_ratio                    |                     0.0068 | 0.0014 |
| share_of_wallet                      |                     0.0050 | 0.0028 |
| recurring_deposit_change_pct         |                     0.0047 | 0.0016 |
| repeat_complaint_flag                |                     0.0037 | 0.0007 |
| products_closed_180d                 |                     0.0032 | 0.0008 |
| external_destination_concentration   |                     0.0030 | 0.0011 |
| external_transfer_pct_of_balance_60d |                     0.0021 | 0.0008 |
| cash_pct_of_portfolio_chg            |                     0.0021 | 0.0022 |
| deposit_balance_vs_6m_avg_pct        |                     0.0014 | 0.0015 |
| has_credit_anchor                    |                     0.0011 | 0.0003 |
| bureau_new_mortgage_elsewhere        |                     0.0011 | 0.0004 |
| salary_deposit_stopped_flag          |                     0.0009 | 0.0003 |

## 3 · Soft churn 3 meses (alerta temprana)

Test: 5,963 hogares, churn 11.0%.

### Discriminación y uso operativo (test)

*precisión / recall / lift top 10%*: qué tan bien funciona la lista del 10% más riesgoso que recibe el banker. *captura AUM*: qué parte del valor de los que churnean queda en esa lista.

|                                         |   AUC |   Gini |    KS |   precisión top 10% |   recall top 10% |   lift top 10% |   captura AUM top 10% |   AUC HNW |   AUC UHNW |
|:----------------------------------------|------:|-------:|------:|--------------------:|-----------------:|---------------:|----------------------:|----------:|-----------:|
| M0a · Reglas de negocio                 | 0.522 |  0.045 | 0.071 |               0.154 |            0.140 |          1.405 |                 0.168 |     0.520 |      0.560 |
| M0b · Scorecard experto (deck)          | 0.563 |  0.126 | 0.120 |               0.183 |            0.166 |          1.665 |                 0.173 |     0.567 |      0.501 |
| M1 · Scorecard estadístico (WoE)        | 0.668 |  0.336 | 0.257 |               0.218 |            0.198 |          1.986 |                 0.147 |     0.670 |      0.619 |
| M2 · Gradient Boosting                  | 0.657 |  0.315 | 0.249 |               0.230 |            0.209 |          2.093 |                 0.162 |     0.661 |      0.583 |
| M2 · Logística (challenger)             | 0.664 |  0.327 | 0.257 |               0.228 |            0.208 |          2.077 |                 0.143 |     0.666 |      0.616 |
| M3 · Red neuronal (tabular + secuencia) | 0.642 |  0.284 | 0.225 |               0.201 |            0.183 |          1.833 |                 0.143 |     0.642 |      0.651 |

### Incertidumbre: IC 95% por bootstrap pareado (200 remuestras del test)

La captura de AUM depende de unos pocos hogares muy grandes (cola Pareto), por eso su intervalo es ancho. '¿diferencia real?' = el IC de la diferencia de AUC contra el Gradient Boosting no incluye 0.

|                                         |   AUC p2.5 |   AUC p97.5 |   captura AUM p2.5 |   captura AUM p97.5 |   Δ AUC vs M2 |   Δ p2.5 |   Δ p97.5 | ¿diferencia real?   |
|:----------------------------------------|-----------:|------------:|-------------------:|--------------------:|--------------:|---------:|----------:|:--------------------|
| M0a · Reglas de negocio                 |      0.510 |       0.533 |              0.104 |               0.277 |        -0.135 |   -0.159 |    -0.112 | sí                  |
| M0b · Scorecard experto (deck)          |      0.544 |       0.584 |              0.105 |               0.272 |        -0.094 |   -0.113 |    -0.071 | sí                  |
| M1 · Scorecard estadístico (WoE)        |      0.649 |       0.687 |              0.089 |               0.253 |         0.011 |   -0.002 |     0.025 | no                  |
| M2 · Gradient Boosting                  |      0.638 |       0.680 |              0.087 |               0.252 |       nan     |  nan     |   nan     | nan                 |
| M2 · Logística (challenger)             |      0.640 |       0.686 |              0.093 |               0.186 |         0.006 |   -0.005 |     0.018 | no                  |
| M3 · Red neuronal (tabular + secuencia) |      0.620 |       0.662 |              0.091 |               0.213 |        -0.016 |   -0.033 |     0.001 | no                  |

### Calibración (test)

Control del deck (slide 17): el promedio del score debe igualar al churn observado.

|                                         |   prob. media |   churn observado |   Brier |
|:----------------------------------------|--------------:|------------------:|--------:|
| M1 · Scorecard estadístico (WoE)        |        0.1095 |            0.1098 |  0.0946 |
| M2 · Gradient Boosting                  |        0.1098 |            0.1098 |  0.0948 |
| M2 · Logística (challenger)             |        0.1093 |            0.1098 |  0.0948 |
| M3 · Red neuronal (tabular + secuencia) |        0.1066 |            0.1098 |  0.0961 |

Calibración por decil · M1 · Scorecard estadístico (WoE):

|    |   prob. media |   churn observado |        n |
|---:|--------------:|------------------:|---------:|
|  1 |        0.0467 |            0.0335 | 597.0000 |
|  2 |        0.0583 |            0.0453 | 596.0000 |
|  3 |        0.0677 |            0.0772 | 596.0000 |
|  4 |        0.0767 |            0.0738 | 596.0000 |
|  5 |        0.0854 |            0.1005 | 597.0000 |
|  6 |        0.0950 |            0.0822 | 596.0000 |
|  7 |        0.1073 |            0.1124 | 596.0000 |
|  8 |        0.1293 |            0.1527 | 596.0000 |
|  9 |        0.1706 |            0.2030 | 596.0000 |
| 10 |        0.2576 |            0.2178 | 597.0000 |

### Bandas de riesgo de los scorecards (test)

| Banda | Experto: % hogares | Experto: churn % | Estadístico: % hogares | Estadístico: churn % |
|---|---|---|---|---|
| Low 0–39 | 95.8 | 10.4 | 48.1 | 6.6 |
| Watch 40–69 | 3.6 | 23.4 | 51.7 | 15.0 |
| High 70–100 | 0.6 | 36.1 | 0.2 | 23.1 |

### Scorecard estadístico: 28 variables seleccionadas (IV ≥ 0.02, |ρ| entre WoE < 0.8)

Descartadas por redundancia: aum_outflow_pct_90d, investment_redemption_pct, cash_pct_of_portfolio_chg, has_investments.

|                                      |    IV |   coef |   puntos máx |
|:-------------------------------------|------:|-------:|-------------:|
| client_reply_rate                    | 0.081 |  0.752 |       11.530 |
| positions_liquidated_pct             | 0.168 |  0.572 |        9.224 |
| banker_change_6m_flag                | 0.070 |  0.604 |        6.316 |
| outflow_vs_baseline_pct              | 0.036 |  0.527 |        5.791 |
| salary_deposit_stopped_flag          | 0.022 | -0.380 |        5.405 |
| recurring_deposit_stopped_flag       | 0.038 |  0.389 |        5.192 |
| new_external_destinations_90d        | 0.026 | -0.502 |        5.067 |
| share_of_wallet                      | 0.041 |  0.458 |        4.702 |
| transfer_to_competitor_pct_90d       | 0.037 | -0.393 |        4.507 |
| complaint_escalated_flag             | 0.026 |  0.419 |        4.113 |
| aum_vs_baseline_pct                  | 0.180 |  0.238 |        4.038 |
| fixed_income_maturity_not_reinvested | 0.021 |  0.274 |        3.737 |
| products_closed_180d                 | 0.055 |  0.201 |        3.469 |
| return_vs_benchmark                  | 0.060 |  0.306 |        3.345 |
| net_deposit_flow_pct_90d             | 0.039 |  0.304 |        3.199 |
| deposit_balance_change_pct_90d       | 0.024 | -0.362 |        3.074 |
| bureau_new_mortgage_elsewhere        | 0.027 |  0.257 |        2.894 |
| complaint_age_days                   | 0.021 |  0.181 |        2.748 |
| recurring_deposit_change_pct         | 0.028 |  0.269 |        2.572 |
| share_of_wallet_change               | 0.066 |  0.186 |        2.358 |
| net_external_flow_pct_90d            | 0.041 |  0.173 |        2.075 |
| contact_gap_ratio                    | 0.026 |  0.163 |        1.207 |
| accounts_closed_90d                  | 0.035 |  0.051 |        1.012 |
| external_transfer_acceleration       | 0.031 |  0.105 |        0.859 |
| multi_signal_count                   | 0.089 |  0.040 |        0.739 |
| deposit_balance_vs_6m_avg_pct        | 0.043 |  0.045 |        0.526 |
| external_destination_concentration   | 0.021 | -0.017 |        0.156 |
| external_transfer_pct_of_balance_60d | 0.043 | -0.008 |        0.147 |

### Principales drivers del Gradient Boosting (importancia por permutación, test)

|                                      |   caída de AUC al permutar |   d.e. |
|:-------------------------------------|---------------------------:|-------:|
| aum_vs_baseline_pct                  |                     0.0514 | 0.0013 |
| client_reply_rate                    |                     0.0216 | 0.0060 |
| banker_change_6m_flag                |                     0.0090 | 0.0013 |
| return_vs_benchmark                  |                     0.0047 | 0.0023 |
| cash_pct_of_portfolio_chg            |                     0.0045 | 0.0008 |
| outflow_vs_baseline_pct              |                     0.0038 | 0.0016 |
| multi_signal_count                   |                     0.0032 | 0.0015 |
| tenure_years                         |                     0.0024 | 0.0006 |
| complaint_age_days                   |                     0.0017 | 0.0003 |
| net_external_flow_pct_90d            |                     0.0017 | 0.0005 |
| meetings_cancelled_by_client         |                     0.0015 | 0.0001 |
| positions_liquidated_pct             |                     0.0012 | 0.0013 |
| fixed_income_maturity_not_reinvested |                     0.0010 | 0.0003 |
| age_primary                          |                     0.0008 | 0.0004 |
| external_destination_concentration   |                     0.0008 | 0.0010 |

## 4 · Cómo leer estos resultados

- El **techo** (AUC con la probabilidad verdadera) es el máximo alcanzable: parte del churn es azar puro, que ningún modelo puede anticipar.
- La base tiene un solo corte: la validación es una partición aleatoria, no out-of-time. Con el panel mensual se podría entrenar en meses viejos y probar en los últimos 6, como pide el deck (slide 20).
- La red neuronal es un MLP con la secuencia de 12 meses como entrada; una LSTM / Transformer (deck slide 24) requeriría PyTorch y más historia.

