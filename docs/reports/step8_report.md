# Paso 8 · External & composite

**24 de 24 pruebas OK** (α = 0.01, Benjamini-Hochberg)

## Calibración

| variable                      | fuerza_excel     | motor   | alerta   |   tasa_alerta |    IV |   lift_alerta |   tendencia_z |   null_% |
|:------------------------------|:-----------------|:--------|:---------|--------------:|------:|--------------:|--------------:|---------:|
| multi_signal_count            | High (compuesta) | mixed   | >= 3     |         0.240 | 0.636 |         3.415 |        32.940 |    0.000 |
| bureau_new_mortgage_elsewhere | High             | mixed   | = 1      |         0.040 | 0.156 |         3.710 |        15.106 |    5.051 |

## Robustez en 10 semillas de referencia

| variable                      |   ('tasa_alerta', 'min') |   ('tasa_alerta', 'median') |   ('tasa_alerta', 'max') |   ('IV', 'min') |   ('IV', 'median') |   ('IV', 'max') |   ('lift_alerta', 'min') |   ('lift_alerta', 'median') |   ('lift_alerta', 'max') |
|:------------------------------|-------------------------:|----------------------------:|-------------------------:|----------------:|-------------------:|----------------:|-------------------------:|----------------------------:|-------------------------:|
| bureau_new_mortgage_elsewhere |                    0.035 |                       0.038 |                    0.040 |           0.143 |              0.155 |           0.193 |                    3.611 |                       3.716 |                    4.215 |
| multi_signal_count            |                    0.230 |                       0.239 |                    0.248 |           0.541 |              0.600 |           0.705 |                    2.968 |                       3.241 |                    3.499 |

## Multi-señal: activación por grupo

|                              |   % hogares |
|:-----------------------------|------------:|
| Balances & AUM               |        14.5 |
| Recurring deposits & flows   |        35.6 |
| Transfers                    |        11.8 |
| Investments                  |        28.3 |
| Relationship & closures      |        42.8 |
| Banker                       |        32.0 |
| Complaints & voice of client |         8.8 |

## Multi-señal: churn por nº de grupos en alerta

|   multi_signal_count |   hogares_% |   churn_6m_% |
|---------------------:|------------:|-------------:|
|                    0 |        20.6 |          2.8 |
|                    1 |        32.2 |          3.6 |
|                    2 |        23.1 |          5.0 |
|                    3 |        11.7 |          6.8 |
|                    4 |         5.7 |         10.2 |
|                    5 |         3.4 |         19.9 |
|                    6 |         2.3 |         29.1 |
|                    7 |         0.9 |         44.8 |

## 1 · Multi-señal y buró

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| columnas declaradas con unidad |  |  |  | OK |
| conteo = suma de las 7 alertas de grupo |  |  |  | OK |
| churn crece con el nº de grupos en alerta | 0: 2.8% · 1: 3.6% · 2: 5.0% · 3: 6.8% · 4: 10.2% · 5: 19.9% · 6: 29.1% · 7: 44.8% |  |  | OK |
| #37 NULL ⇔ sin propósito permisible (o sin aprobación legal) | NULL 5.0% |  |  | OK |
| interruptor legal: sin aprobación, #37 queda NULL en todos |  |  |  | OK |
| compras financiadas con Citizens no cuentan como 'elsewhere' | 347 compras financiadas |  |  | OK |
| coherencia: quien se muda toma hipoteca en otro banco más seguido | 42.5% vs 1.9% |  |  | OK |

## 2 · Calibración (tasa de alerta, IV, tendencia, lift)

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| tasa de alerta multi_signal_count | 0.240 en [0.03, 0.3] |  |  | OK |
| IV multi_signal_count (High (compuesta)) | 0.636 en [0.3, 0.8] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: multi_signal_count | lift = 3.41 |  |  | OK |
| tendencia en la dirección esperada: multi_signal_count | z = 32.9 |  |  | OK |
| tasa de alerta bureau_new_mortgage_elsewhere | 0.040 en [0.005, 0.06] |  |  | OK |
| IV bureau_new_mortgage_elsewhere (High) | 0.156 en [0.1, 0.3] |  |  | OK |
| lift del grupo en alerta ≥ 1.5: bureau_new_mortgage_elsewhere | lift = 3.71 |  |  | OK |
| tendencia en la dirección esperada: bureau_new_mortgage_elsewhere | z = 15.1 |  |  | OK |
| IV mediano entre semillas en banda: multi_signal_count | mediana 0.600 (p10–p90 0.564–0.676) en [0.3, 0.8] |  |  | OK |
| alerta en rango en todas las semillas: multi_signal_count | 0.230–0.248 |  |  | OK |
| IV mediano entre semillas en banda: bureau_new_mortgage_elsewhere | mediana 0.155 (p10–p90 0.144–0.189) en [0.1, 0.3] |  |  | OK |
| alerta en rango en todas las semillas: bureau_new_mortgage_elsewhere | 0.035–0.040 |  |  | OK |

## 3 · Base final consolidada

| Prueba | Detalle | p | p BH | OK |
|---|---|---|---|---|
| 20,000 hogares únicos |  |  |  | OK |
| las 37 variables del Excel presentes (columna principal) |  |  |  | OK |
| sin columnas de verdad latente en la base (sin fuga) |  |  |  | OK |
| target presente y NULL solo en excluidos |  |  |  | OK |
| AUC combinado de las 37 variables < AUC techo | 0.762 vs techo 0.851 |  |  | OK |

## Diccionario

| Columna | Unidad | Descripción |
|---|---|---|
| household_id | id | Identificador del hogar |
| multi_signal_count | entero | #16 · nº de grupos del Excel (0–7) con alguna variable sobre su umbral de alerta |
| multi_signal_flag | 0/1 | #16 · ≥ 3 grupos en alerta |
| group_alert_balances | 0/1 | #16 · alerta en Balances & AUM |
| group_alert_recurring | 0/1 | #16 · alerta en Recurring deposits & flows |
| group_alert_transfers | 0/1 | #16 · alerta en Transfers |
| group_alert_investments | 0/1 | #16 · alerta en Investments |
| group_alert_relationship | 0/1 | #16 · alerta en Relationship & closures |
| group_alert_banker | 0/1 | #16 · alerta en Banker |
| group_alert_complaints | 0/1 | #16 · alerta en Complaints & voice of client |
| bureau_new_mortgage_elsewhere | 0/1 | #37 · hipoteca / HELOC nueva con otro acreedor en 6m; NULL sin propósito permisible o sin aprobación legal |
