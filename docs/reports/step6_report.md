# Paso 6 · Banker

Semilla `20260928` · 20,000 hogares · 359 bankers · 581,419 interacciones · **40 de 40 pruebas OK** (α = 0.01, Benjamini-Hochberg)

## Calibración

| variable                     | fuerza_excel   | motor   | alerta   |   tasa_alerta |    IV |   lift_alerta |   tendencia_z |   null_% |
|:-----------------------------|:---------------|:--------|:---------|--------------:|------:|--------------:|--------------:|---------:|
| banker_change_6m_flag        | Very high      | mixed   | = 1      |         0.149 | 0.442 |         4.098 |        26.849 |    0.533 |
| contact_gap_ratio            | High           | factor  | > 2.0    |         0.037 | 0.173 |         2.002 |        13.489 |    0.000 |
| client_reply_rate            | High           | mixed   | < 0.5    |         0.255 | 0.242 |         1.947 |         6.023 |   47.980 |
| meetings_cancelled_by_client | High           | mixed   | >= 2     |         0.053 | 0.162 |         2.080 |         8.232 |   60.713 |

AUC combinado de las variables de los Pasos 1–5 (logística): **0.757**; techo: 0.851.

## Robustez en 20 semillas de referencia

| variable                     |   ('tasa_alerta', 'min') |   ('tasa_alerta', 'median') |   ('tasa_alerta', 'max') |   ('IV', 'min') |   ('IV', 'median') |   ('IV', 'max') |   ('lift_alerta', 'min') |   ('lift_alerta', 'median') |   ('lift_alerta', 'max') |
|:-----------------------------|-------------------------:|----------------------------:|-------------------------:|----------------:|-------------------:|----------------:|-------------------------:|----------------------------:|-------------------------:|
| banker_change_6m_flag        |                    0.137 |                       0.152 |                    0.179 |           0.208 |              0.321 |           0.415 |                    2.795 |                       3.337 |                    3.853 |
| client_reply_rate            |                    0.249 |                       0.252 |                    0.261 |           0.157 |              0.237 |           0.345 |                    1.783 |                       2.100 |                    2.775 |
| contact_gap_ratio            |                    0.036 |                       0.039 |                    0.042 |           0.104 |              0.164 |           0.214 |                    1.951 |                       2.168 |                    2.904 |
| meetings_cancelled_by_client |                    0.040 |                       0.049 |                    0.055 |           0.071 |              0.158 |           0.227 |                    1.750 |                       2.540 |                    3.219 |

## Interacciones por tipo

| kind                        |      n |
|:----------------------------|-------:|
| mass_mailing                | 162215 |
| call                        | 147851 |
| email                       |  97430 |
| meeting                     |  81170 |
| message                     |  80929 |
| meeting_cancelled_by_client |  11824 |

## Motivo del cambio de banker

| change_reason    |   hogares |
|:-----------------|----------:|
| banker_departure |      2102 |
| book_rebalancing |       516 |
| client_request   |       360 |

## 1 · Carteras, bitácora y reglas del Excel

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| columnas declaradas con unidad |  |  |  | OK |
| tamaño de cartera razonable | 359 bankers; 25–60 hogares |  |  | OK |
| cada cartera es de un solo segmento |  |  |  | OK |
| si el banker se va, cambia todo su libro | 38 bankers se fueron |  |  | OK |
| cobertura temporal (< 30d) no cuenta como cambio | n = 881 |  |  | OK |
| envíos masivos fuera de la tasa de respuesta y del contacto significativo | 162,215 envíos masivos |  |  | OK |
| llamadas < 5 min no son contacto significativo | 15,838 llamadas cortas |  |  | OK |
| #13 NULL ⇔ < 3 contactos en 90d | NULL 48.0% |  |  | OK |
| #35 NULL ⇔ el banker no registra 'cancelado por' | capturado en 39% de los hogares |  |  | OK |
| brecha de contacto ≥ 0 y cadencia UHNW 30d / HNW 90d |  |  |  | OK |
| coherencia: quien se muda contesta menos | 0.31 vs 0.61 |  |  | OK |
| coherencia: entre quienes cambiaron de banker, la bienvenida reduce la brecha | mediana 0.29 con bienvenida vs 0.44 sin ella |  |  | OK |

## 2 · Calibración (tasa de alerta, IV, tendencia, lift)

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| tasa de alerta banker_change_6m_flag | 0.149 en [0.05, 0.2] |  |  | OK |
| IV banker_change_6m_flag (Very high) | 0.442 en [0.3, 0.5] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: banker_change_6m_flag | lift = 4.10 |  |  | OK |
| tendencia en la dirección esperada: banker_change_6m_flag | z = 26.8 |  |  | OK |
| tasa de alerta contact_gap_ratio | 0.037 en [0.02, 0.25] |  |  | OK |
| IV contact_gap_ratio (High) | 0.173 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: contact_gap_ratio | lift = 2.00 |  |  | OK |
| tendencia en la dirección esperada: contact_gap_ratio | z = 13.5 |  |  | OK |
| tasa de alerta client_reply_rate | 0.255 en [0.05, 0.35] |  |  | OK |
| IV client_reply_rate (High) | 0.242 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: client_reply_rate | lift = 1.95 |  |  | OK |
| tendencia en la dirección esperada: client_reply_rate | z = 6.0 |  |  | OK |
| tasa de alerta meetings_cancelled_by_client | 0.053 en [0.03, 0.2] |  |  | OK |
| IV meetings_cancelled_by_client (High) | 0.162 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: meetings_cancelled_by_client | lift = 2.08 |  |  | OK |
| tendencia en la dirección esperada: meetings_cancelled_by_client | z = 8.2 |  |  | OK |
| IV mediano entre semillas en banda: banker_change_6m_flag | mediana 0.321 (p10–p90 0.250–0.404) en [0.3, 0.5] |  |  | OK |
| alerta en rango en todas las semillas: banker_change_6m_flag | 0.137–0.179 |  |  | OK |
| IV mediano entre semillas en banda: contact_gap_ratio | mediana 0.164 (p10–p90 0.126–0.201) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: contact_gap_ratio | 0.036–0.042 |  |  | OK |
| IV mediano entre semillas en banda: client_reply_rate | mediana 0.237 (p10–p90 0.171–0.299) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: client_reply_rate | 0.249–0.261 |  |  | OK |
| IV mediano entre semillas en banda: meetings_cancelled_by_client | mediana 0.158 (p10–p90 0.108–0.213) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: meetings_cancelled_by_client | 0.040–0.055 |  |  | OK |

## 3 · Fuga (generador) y AUC

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| cambio pedido por el cliente ⟂ ε dado z_service (Wald) | coef ε = +0.001 | 0.989 | 0.989 | OK |
| diligencia del banker ⟂ calidad del libro | ρ = +0.060 | 0.259 | 0.399 | OK |
| ruido: rebalanceo de carteras ⟂ índice de riesgo | ρ = -0.0079 | 0.266 | 0.399 | OK |
| AUC combinado (Pasos 1–6) < AUC techo | 0.757 vs techo 0.851 |  |  | OK |

## Distribuciones

|                               |       count |    mean |     std |     min |      1% |     5% |    25% |     50% |     75% |      95% |      99% |      max |
|:------------------------------|------------:|--------:|--------:|--------:|--------:|-------:|-------:|--------:|--------:|---------:|---------:|---------:|
| banker_change_6m_flag         | 19,894.0000 |  0.1488 |  0.3559 |  0.0000 |  0.0000 | 0.0000 | 0.0000 |  0.0000 |  0.0000 |   1.0000 |   1.0000 |   1.0000 |
| days_since_meaningful_contact | 20,000.0000 | 42.8903 | 56.2410 | -0.0000 | -0.0000 | 1.0000 | 9.0000 | 23.0000 | 53.0000 | 155.0000 | 292.0000 | 365.0000 |
| contact_gap_ratio             | 20,000.0000 |  0.4972 |  0.6448 | -0.0000 | -0.0000 | 0.0111 | 0.1000 |  0.2667 |  0.6222 |   1.7778 |   3.3333 |  12.1667 |
| client_reply_rate             | 10,402.0000 |  0.6087 |  0.2438 |  0.0000 |  0.0000 | 0.2000 | 0.4444 |  0.6667 |  0.7500 |   1.0000 |   1.0000 |   1.0000 |
| meetings_cancelled_by_client  |  7,855.0000 |  0.3192 |  0.6835 |  0.0000 |  0.0000 | 0.0000 | 0.0000 |  0.0000 |  0.0000 |   2.0000 |   3.0000 |   9.0000 |
| meetings_cancelled_pct        |  6,787.0000 |  0.1318 |  0.2559 |  0.0000 |  0.0000 | 0.0000 | 0.0000 |  0.0000 |  0.2000 |   0.6667 |   1.0000 |   1.0000 |

## WoE · banker_change_6m_flag

| row_0   |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:--------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0  | 16,141.0000 | 694.0000 |        0.0412 | -0.3986 | 0.1138 |
| 01 = 1  |  2,440.0000 | 496.0000 |        0.1689 |  1.1550 | 0.3298 |

## WoE · contact_gap_ratio

| row_0                 |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:----------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [-0, 0.03333]      |  1,921.0000 |  67.0000 |        0.0337 | -0.6077 | 0.0285 |
| 01 [0.03333, 0.07778] |  1,906.0000 |  82.0000 |        0.0412 | -0.3991 | 0.0134 |
| 02 [0.07778, 0.1333]  |  1,921.0000 |  66.0000 |        0.0332 | -0.6226 | 0.0297 |
| 03 [0.1333, 0.1889]   |  1,893.0000 |  95.0000 |        0.0478 | -0.2460 | 0.0054 |
| 04 [0.1889, 0.2667]   |  1,881.0000 | 107.0000 |        0.0538 | -0.1213 | 0.0014 |
| 05 [0.2667, 0.3778]   |  1,882.0000 | 105.0000 |        0.0528 | -0.1406 | 0.0019 |
| 06 [0.3778, 0.5222]   |  1,865.0000 | 123.0000 |        0.0619 |  0.0260 | 0.0001 |
| 07 [0.5222, 0.7667]   |  1,829.0000 | 158.0000 |        0.0795 |  0.2950 | 0.0099 |
| 08 [0.7667, 1.244]    |  1,820.0000 | 168.0000 |        0.0845 |  0.3612 | 0.0153 |
| 09 [1.244, 12.17]     |  1,759.0000 | 229.0000 |        0.1152 |  0.7042 | 0.0678 |

## WoE · client_reply_rate

| row_0               |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:--------------------|------------:|---------:|--------------:|--------:|-------:|
| 00 [0, 0.2857]      |    945.0000 |  60.0000 |        0.0597 |  0.4911 | 0.0296 |
| 01 [0.2857, 0.5833] |    972.0000 |  32.0000 |        0.0319 | -0.1584 | 0.0023 |
| 02 = 0.3333         |    936.0000 |  73.0000 |        0.0723 |  0.6953 | 0.0657 |
| 03 = 0.5            |    979.0000 |  49.0000 |        0.0477 |  0.2551 | 0.0073 |
| 04 [0.5833, 0.7]    |    981.0000 |  23.0000 |        0.0229 | -0.4919 | 0.0188 |
| 05 = 0.6667         |  1,348.0000 |  61.0000 |        0.0433 |  0.1525 | 0.0034 |
| 06 [0.7, 0.8]       |    991.0000 |  13.0000 |        0.0129 | -1.0563 | 0.0686 |
| 07 = 0.75           |    814.0000 |  24.0000 |        0.0286 | -0.2637 | 0.0050 |
| 08 [0.8, 0.9615]    |    986.0000 |  18.0000 |        0.0179 | -0.7362 | 0.0380 |
| 09 = 1              |  1,003.0000 |  32.0000 |        0.0309 | -0.1898 | 0.0033 |

## WoE · meetings_cancelled_by_client

| row_0     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:----------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0    |  5,618.0000 | 314.0000 |        0.0529 | -0.2514 | 0.0431 |
| 01 = 1    |  1,313.0000 | 152.0000 |        0.1038 |  0.4781 | 0.0528 |
| 02 [2, 2] |     47.0000 |   5.0000 |        0.0962 |  0.4754 | 0.0019 |
| 03 [2, 2] |     48.0000 |   3.0000 |        0.0588 |  0.0026 | 0.0000 |
| 04 [2, 2] |     47.0000 |   5.0000 |        0.0962 |  0.4754 | 0.0019 |
| 05 [2, 2] |     47.0000 |   4.0000 |        0.0784 |  0.2748 | 0.0006 |
| 06 [2, 2] |     43.0000 |   8.0000 |        0.1569 |  0.9987 | 0.0102 |
| 07 [2, 3] |     45.0000 |   7.0000 |        0.1346 |  0.8286 | 0.0067 |
| 08 [3, 3] |     39.0000 |  12.0000 |        0.2353 |  1.4808 | 0.0272 |
| 09 [3, 9] |     42.0000 |  10.0000 |        0.1923 |  1.2333 | 0.0175 |

## Diccionario

| Columna | Unidad | Descripción |
|---|---|---|
| household_id | id | Identificador del hogar |
| banker_change_6m_flag | 0/1 | #11 · cambió el banker principal en 6m (sin cobertura temporal < 30d) |
| banker_change_reason | categoría | #11 · banker_departure / client_request / book_rebalancing |
| days_since_meaningful_contact | días | #12 · días desde el último contacto significativo (365 = sin contacto en 12m) |
| contact_gap_ratio | ratio | #12 · días sin contacto significativo ÷ cadencia acordada (UHNW 30d, HNW 90d) (alerta > 2) |
| client_reply_rate | fracción | #13 · contactos del banker respondidos en ≤ 7d ÷ contactos, 90d; NULL si < 3 |
| meetings_cancelled_by_client | entero | #35 · reuniones canceladas por el cliente en 6m; NULL si el banker no registra el campo |
| meetings_cancelled_pct | fracción | #35 · ÷ reuniones agendadas |
