# Paso 7 · Complaints & voice of client

Semilla `20260928` · 20,000 hogares · 5,458 quejas · **38 de 38 pruebas OK** (α = 0.01, Benjamini-Hochberg)

## Calibración

| variable                          | fuerza_excel   | motor   | alerta   |   tasa_alerta |    IV |   lift_alerta |   tendencia_z |   null_% |
|:----------------------------------|:---------------|:--------|:---------|--------------:|------:|--------------:|--------------:|---------:|
| complaint_escalated_flag          | High           | mixed   | = 1      |         0.053 | 0.129 |         3.106 |        15.214 |    0.000 |
| complaint_age_days                | High           | mixed   | > 30     |         0.020 | 0.119 |         3.750 |        14.271 |    0.000 |
| repeat_complaint_flag             | High           | mixed   | = 1      |         0.037 | 0.170 |         4.018 |        16.701 |    0.000 |
| relationship_dissatisfaction_flag | High           | mixed   | = 1      |         0.041 | 0.121 |         2.994 |         6.533 |   70.418 |

AUC combinado de las variables de los Pasos 1–5 (logística): **0.761**; techo: 0.851.

## Robustez en 20 semillas de referencia

| variable                          |   ('tasa_alerta', 'min') |   ('tasa_alerta', 'median') |   ('tasa_alerta', 'max') |   ('IV', 'min') |   ('IV', 'median') |   ('IV', 'max') |   ('lift_alerta', 'min') |   ('lift_alerta', 'median') |   ('lift_alerta', 'max') |
|:----------------------------------|-------------------------:|----------------------------:|-------------------------:|----------------:|-------------------:|----------------:|-------------------------:|----------------------------:|-------------------------:|
| complaint_age_days                |                    0.018 |                       0.019 |                    0.021 |           0.077 |              0.099 |           0.163 |                    2.815 |                       3.504 |                    4.555 |
| complaint_escalated_flag          |                    0.052 |                       0.054 |                    0.056 |           0.088 |              0.114 |           0.149 |                    2.620 |                       2.931 |                    3.352 |
| relationship_dissatisfaction_flag |                    0.037 |                       0.040 |                    0.044 |           0.129 |              0.204 |           0.306 |                    2.949 |                       3.782 |                    5.093 |
| repeat_complaint_flag             |                    0.035 |                       0.037 |                    0.039 |           0.083 |              0.121 |           0.161 |                    2.699 |                       3.314 |                    3.758 |

## Quejas por categoría y origen

| category               |   acats_delay |   noise |   service |
|:-----------------------|--------------:|--------:|----------:|
| banker_attention       |             0 |       0 |       857 |
| digital                |             0 |       0 |       523 |
| fees_pricing           |             0 |       0 |       638 |
| fraud_dispute          |             0 |     430 |       220 |
| investment_performance |             0 |       0 |       555 |
| process_delay          |             0 |       0 |      1061 |
| statement_error        |             0 |     411 |       280 |
| transfers_wires        |           150 |       0 |       333 |

## Escalamiento

| escalation_level   |   quejas |
|:-------------------|---------:|
| none               |     3882 |
| management         |      890 |
| regulator          |      317 |
| ombudsman          |      223 |
| legal              |      146 |

## 1 · Quejas, Assistant y reglas del Excel

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| columnas declaradas con unidad |  |  |  | OK |
| volumen plausible para PB (10–25% de hogares con queja al año) | 18.2% de hogares; 5,458 quejas |  |  | OK |
| fechas coherentes (apertura ≤ cierre ≤ t) |  |  |  | OK |
| #15: 0 días ⇔ sin queja abierta |  |  |  | OK |
| queja fuera de SLA ⇒ antigüedad > SLA mínimo |  |  |  | OK |
| escalamiento más frecuente fuera de SLA (regla del generador) | 0.40 vs 0.11 |  |  | OK |
| niveles de escalamiento del Excel (gerencia, ombudsman, regulador, legal) | {'management': 890, 'regulator': 317, 'ombudsman': 223, 'legal': 146} |  |  | OK |
| #36 NULL ⇔ fuera del piloto del Assistant | piloto 30% |  |  | OK |
| revisión humana: precisión de la señal confirmada ≥ 85% | 97.5% |  |  | OK |
| coherencia: quien se muda expresa más insatisfacción |  |  |  | OK |

## 2 · Calibración (tasa de alerta, IV, tendencia, lift)

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| tasa de alerta complaint_escalated_flag | 0.053 en [0.01, 0.08] |  |  | OK |
| IV complaint_escalated_flag (High) | 0.129 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: complaint_escalated_flag | lift = 3.11 |  |  | OK |
| tendencia en la dirección esperada: complaint_escalated_flag | z = 15.2 |  |  | OK |
| tasa de alerta complaint_age_days | 0.020 en [0.005, 0.06] |  |  | OK |
| IV complaint_age_days (High) | 0.119 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: complaint_age_days | lift = 3.75 |  |  | OK |
| tendencia en la dirección esperada: complaint_age_days | z = 14.3 |  |  | OK |
| tasa de alerta repeat_complaint_flag | 0.037 en [0.01, 0.08] |  |  | OK |
| IV repeat_complaint_flag (High) | 0.170 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: repeat_complaint_flag | lift = 4.02 |  |  | OK |
| tendencia en la dirección esperada: repeat_complaint_flag | z = 16.7 |  |  | OK |
| tasa de alerta relationship_dissatisfaction_flag | 0.041 en [0.005, 0.06] |  |  | OK |
| IV relationship_dissatisfaction_flag (High) | 0.121 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: relationship_dissatisfaction_flag | lift = 2.99 |  |  | OK |
| tendencia en la dirección esperada: relationship_dissatisfaction_flag | z = 6.5 |  |  | OK |
| IV mediano entre semillas en banda: complaint_escalated_flag | mediana 0.114 (p10–p90 0.102–0.143) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: complaint_escalated_flag | 0.052–0.056 |  |  | OK |
| IV mediano entre semillas en banda: complaint_age_days | mediana 0.099 (p10–p90 0.082–0.118) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: complaint_age_days | 0.018–0.021 |  |  | OK |
| IV mediano entre semillas en banda: repeat_complaint_flag | mediana 0.121 (p10–p90 0.089–0.131) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: repeat_complaint_flag | 0.035–0.039 |  |  | OK |
| IV mediano entre semillas en banda: relationship_dissatisfaction_flag | mediana 0.204 (p10–p90 0.135–0.248) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: relationship_dissatisfaction_flag | 0.037–0.044 |  |  | OK |

## 3 · Fuga (generador) y AUC

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| nº de quejas ⟂ ε dado z_service y z_neglect | coef ε = +0.0001 ± 0.0034 | 0.988 | 0.988 | OK |
| ruido (fraude, estado de cuenta) ⟂ índice de riesgo | ρ = -0.0006 | 0.928 | 0.988 | OK |
| piloto del Assistant ⟂ índice de riesgo (sin sesgo de selección) | ρ = -0.0057 | 0.423 | 0.988 | OK |
| AUC combinado (Pasos 1–7) < AUC techo | 0.761 vs techo 0.851 |  |  | OK |

## Distribuciones

|                                   |       count |   mean |     std |    min |     1% |     5% |    25% |    50% |    75% |    95% |     99% |      max |
|:----------------------------------|------------:|-------:|--------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|--------:|---------:|
| complaint_escalated_flag          | 20,000.0000 | 0.0535 |  0.2250 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |  1.0000 |   1.0000 |
| open_complaint_flag               | 20,000.0000 | 0.0374 |  0.1899 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  1.0000 |   1.0000 |
| complaint_age_days                | 20,000.0000 | 2.3189 | 18.4668 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 80.0000 | 364.0000 |
| complaint_out_of_sla_flag         | 20,000.0000 | 0.0237 |  0.1520 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  1.0000 |   1.0000 |
| repeat_complaint_flag             | 20,000.0000 | 0.0366 |  0.1878 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  1.0000 |   1.0000 |
| complaints_12m                    | 20,000.0000 | 0.2729 |  0.8809 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |  3.0000 |  50.0000 |
| relationship_dissatisfaction_flag |  5,911.0000 | 0.0409 |  0.1982 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |  1.0000 |   1.0000 |

## WoE · complaint_escalated_flag

| row_0   |   no_evento |     evento |   tasa_evento |     woe |     iv |
|:--------|------------:|-----------:|--------------:|--------:|-------:|
| 00 = 0  | 17,794.0000 | 1,021.0000 |        0.0543 | -0.1134 | 0.0116 |
| 01 = 1  |    883.0000 |   179.0000 |        0.1685 |  1.1505 | 0.1175 |

## WoE · complaint_age_days

| row_0         |   no_evento |     evento |   tasa_evento |     woe |     iv |
|:--------------|------------:|-----------:|--------------:|--------:|-------:|
| 00 = 0        | 18,131.0000 | 1,071.0000 |        0.0558 | -0.0875 | 0.0071 |
| 01 [1, 7]     |     61.0000 |    14.0000 |        0.1867 |  1.2962 | 0.0113 |
| 02 [7, 14]    |     62.0000 |    13.0000 |        0.1733 |  1.2086 | 0.0095 |
| 03 [14, 22]   |     66.0000 |     9.0000 |        0.1200 |  0.7952 | 0.0034 |
| 04 [22, 33]   |     62.0000 |    13.0000 |        0.1733 |  1.2086 | 0.0095 |
| 05 [33, 47]   |     60.0000 |    15.0000 |        0.2000 |  1.3793 | 0.0133 |
| 06 [47, 69]   |     62.0000 |    13.0000 |        0.1733 |  1.2086 | 0.0095 |
| 07 [69, 105]  |     60.0000 |    15.0000 |        0.2000 |  1.3793 | 0.0133 |
| 08 [107, 171] |     59.0000 |    16.0000 |        0.2133 |  1.4585 | 0.0153 |
| 09 [171, 364] |     54.0000 |    21.0000 |        0.2800 |  1.8109 | 0.0270 |

## WoE · repeat_complaint_flag

| row_0     |   no_evento |     evento |   tasa_evento |     woe |     iv |
|:----------|------------:|-----------:|--------------:|--------:|-------:|
| 00 = 0    | 18,108.0000 | 1,041.0000 |        0.0544 | -0.1146 | 0.0120 |
| 01 [1, 1] |     64.0000 |    17.0000 |        0.2099 |  1.4366 | 0.0159 |
| 02 [1, 1] |     66.0000 |    15.0000 |        0.1852 |  1.2847 | 0.0120 |
| 03 [1, 1] |     65.0000 |    16.0000 |        0.1975 |  1.3624 | 0.0139 |
| 04 [1, 1] |     61.0000 |    20.0000 |        0.2469 |  1.6425 | 0.0225 |
| 05 [1, 1] |     60.0000 |    20.0000 |        0.2500 |  1.6589 | 0.0228 |
| 06 [1, 1] |     64.0000 |    17.0000 |        0.2099 |  1.4366 | 0.0159 |
| 07 [1, 1] |     66.0000 |    15.0000 |        0.1852 |  1.2847 | 0.0120 |
| 08 [1, 1] |     63.0000 |    18.0000 |        0.2222 |  1.5078 | 0.0180 |
| 09 [1, 1] |     60.0000 |    21.0000 |        0.2593 |  1.7065 | 0.0249 |

## WoE · relationship_dissatisfaction_flag

| row_0     |   no_evento |   evento |   tasa_evento |     woe |     iv |
|:----------|------------:|---------:|--------------:|--------:|-------:|
| 00 = 0    |  5,319.0000 | 319.0000 |        0.0566 | -0.0952 | 0.0083 |
| 01 [1, 1] |     23.0000 |   4.0000 |        0.1481 |  1.0642 | 0.0086 |
| 02 [1, 1] |     21.0000 |   6.0000 |        0.2222 |  1.5209 | 0.0212 |
| 03 [1, 1] |     24.0000 |   3.0000 |        0.1111 |  0.7712 | 0.0040 |
| 04 [1, 1] |     24.0000 |   3.0000 |        0.1111 |  0.7712 | 0.0040 |
| 05 [1, 1] |     20.0000 |   6.0000 |        0.2308 |  1.5685 | 0.0221 |
| 06 [1, 1] |     22.0000 |   5.0000 |        0.1852 |  1.3084 | 0.0144 |
| 07 [1, 1] |     23.0000 |   4.0000 |        0.1481 |  1.0642 | 0.0086 |
| 08 [1, 1] |     21.0000 |   6.0000 |        0.2222 |  1.5209 | 0.0212 |
| 09 [1, 1] |     23.0000 |   4.0000 |        0.1481 |  1.0642 | 0.0086 |

## Diccionario

| Columna | Unidad | Descripción |
|---|---|---|
| household_id | id | Identificador del hogar |
| complaint_escalated_flag | 0/1 | #14 · alguna queja escalada a gerencia / ombudsman / regulador / legal en 12m |
| open_complaint_flag | 0/1 | #15 · tiene queja abierta (distingue 0 días de sin queja) |
| complaint_age_days | días | #15 · días de la queja abierta más antigua; 0 si no hay (alerta > 30) |
| complaint_out_of_sla_flag | 0/1 | #15 · alguna queja abierta fuera de SLA (override del deck) |
| repeat_complaint_flag | 0/1 | #33 · ≥ 2 quejas de la misma categoría (nivel 2) en 12m o alguna reabierta |
| complaints_12m | entero | nº de quejas en 12m (contexto) |
| relationship_dissatisfaction_flag | 0/1 | #36 · insatisfacción detectada por el Assistant y confirmada por una persona (30d); NULL fuera del piloto |
