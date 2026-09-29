# Paso 0 · Reporte de población, latentes y target

Semilla maestra `20260928` · 20,000 hogares · corte 2025-12-31 · montos en USD

## Chequeos

| Chequeo | Resultado | Detalle |
|---|---|---|
| filas | OK | 20,000 |
| moneda = USD | OK | USD |
| toda columna declarada en el diccionario | OK |  |
| montos USD numéricos y ≥ 0 | OK | 10 columnas en USD |
| household_id único | OK |  |
| piso de relación | OK | min = 1,000,062 |
| depósitos + AUM = relación | OK | máx desvío 0.0100 |
| AUM NULL ⇔ sin inversiones | OK |  |
| advisory ⊂ inversiones | OK |  |
| dividendos ⊂ inversiones | OK |  |
| share deposit-only | OK | 0.150 vs 0.15 |
| share UHNW en [2%, 10%] | OK | 5.515% |
| antigüedad < edad adulta | OK |  |
| history_months ≤ tope | OK |  |
| salary_base_annual NULL ⇔ sin flujo | OK |  |
| pension_monthly NULL ⇔ sin flujo | OK |  |
| dividend_annual NULL ⇔ sin flujo | OK |  |
| business_distribution_annual NULL ⇔ sin flujo | OK |  |
| sueldo ≥ piso PB | OK | min = 150,008 |
| mediana sueldo base en [$300k, $500k] | OK | 379,203 |
| corr(log sueldo, log patrimonio) en [0.30, 0.60] | OK | 0.372 |
| pensión ≥ piso | OK |  |
| ingreso recurrente > 0 ⇔ algún flujo | OK |  |
| frecuencias de pago ≈ config | OK | máx desvío 0.006 |
| target NULL ⇔ excluido | OK |  |
| hard y soft excluyentes | OK |  |
| tasa hard churn 6m | OK | 6.037% vs 6.0% (±0.51%) |
| tasa soft churn 3m | OK | 8.834% vs 9.0% (±0.61%) |
| antigüedad ≤ tope | OK |  |
| calibración E[p_hard] = tasa | OK | 6.0000% |
| AUC techo (oráculo) en [0.75, 0.90] | OK | 0.851 |
| correlación latentes ≈ config | OK | máx desvío 0.013 |

## Numéricas

|                    |       count |           mean |             std |            min |             5% |            25% |            50% |             75% |             95% |              max |
|:-------------------|------------:|---------------:|----------------:|---------------:|---------------:|---------------:|---------------:|----------------:|----------------:|-----------------:|
| relationship_value | 20,000.0000 | 9,436,103.6020 | 16,481,070.5633 | 1,000,062.5000 | 1,269,559.7925 | 2,475,457.0250 | 4,841,540.7500 | 10,194,870.2625 | 31,921,427.0215 | 782,205,499.5900 |
| deposit_balance    | 20,000.0000 | 3,793,483.8586 |  9,955,701.9391 |     1,358.2800 |   204,414.7800 |   645,822.2975 | 1,513,240.0650 |  3,642,004.3100 | 14,093,943.1785 | 782,205,499.5900 |
| aum                | 16,991.0000 | 6,641,892.4647 | 11,170,310.8242 |   113,383.2500 |   841,250.1850 | 1,691,045.3700 | 3,394,349.5300 |  7,179,175.0750 | 22,366,805.8550 | 418,825,870.1800 |
| age_primary        | 20,000.0000 |        60.4834 |         11.7048 |        28.0000 |        41.0000 |        52.0000 |        60.0000 |         68.0000 |         80.0000 |          94.0000 |
| tenure_years       | 20,000.0000 |         8.9860 |          6.1673 |         0.0100 |         1.6300 |         4.3700 |         7.6250 |         12.1325 |         20.9500 |          50.0000 |
| history_months     | 20,000.0000 |        23.3535 |          2.8047 |         0.0000 |        19.0000 |        24.0000 |        24.0000 |         24.0000 |         24.0000 |          24.0000 |

## Flags

|                          |   share |
|:-------------------------|--------:|
| has_investments          |  0.8496 |
| has_advisory             |  0.5978 |
| has_linked_business      |  0.2643 |
| has_trust                |  0.3187 |
| has_credit_anchor        |  0.3424 |
| has_payroll_stream       |  0.5386 |
| has_pension_stream       |  0.3401 |
| has_dividend_stream      |  0.4642 |
| has_any_recurring_stream |  0.9326 |

## Ingresos (USD)

|                              |       count |         mean |          std |          min |           5% |          25% |          50% |            75% |            95% |             max |
|:-----------------------------|------------:|-------------:|-------------:|-------------:|-------------:|-------------:|-------------:|---------------:|---------------:|----------------:|
| salary_base_annual           | 10,772.0000 | 440,425.3937 | 242,565.2422 | 150,008.4200 | 182,854.3425 | 271,005.3550 | 379,203.0200 |   541,003.2700 |   912,131.9375 |  2,645,329.4300 |
| bonus_annual                 | 10,772.0000 | 218,427.5747 | 192,529.8023 |     133.8900 |  26,671.5070 |  87,761.8575 | 166,704.7350 |   289,575.5300 |   590,795.2095 |  2,334,626.9300 |
| pension_monthly              |  6,801.0000 |  10,512.0412 |   5,440.8625 |   2,523.1500 |   4,226.1100 |   6,673.0300 |   9,275.7800 |    13,042.9700 |    20,807.2800 |     53,462.4600 |
| dividend_annual              |  9,284.0000 | 135,942.6418 | 306,319.4218 |     682.2400 |  11,082.3950 |  28,752.4750 |  60,951.7050 |   137,122.2750 |   478,712.8180 | 15,839,450.8700 |
| business_distribution_annual |  5,287.0000 | 852,224.2910 | 984,022.9558 |  27,106.3400 | 134,447.3260 | 315,166.4500 | 567,076.2400 | 1,015,861.6550 | 2,462,868.4400 | 21,847,768.2500 |
| recurring_income_monthly     | 20,000.0000 |  47,374.8848 |  63,409.4147 |       0.0000 |       0.0000 |  13,416.6550 |  30,628.6150 |    58,242.2925 |   149,424.4855 |  2,194,450.0500 |

## Mediana de ingresos por segmento (USD)

|                              |          HNW |           UHNW |
|:-----------------------------|-------------:|---------------:|
| salary_base_annual           | 369,461.7600 |   584,781.7650 |
| bonus_annual                 | 163,047.4900 |   256,894.0350 |
| pension_monthly              |   9,149.4200 |    12,154.1650 |
| dividend_annual              |  56,254.3750 |   597,196.2750 |
| business_distribution_annual | 520,075.7700 | 1,312,196.6600 |
| recurring_income_monthly     |  29,200.5100 |   108,164.8600 |

## Churn por segmento

| segment   |   households |   hard_churn |   soft_churn |
|:----------|-------------:|-------------:|-------------:|
| HNW       |  18,782.0000 |       0.0596 |       0.0879 |
| UHNW      |   1,095.0000 |       0.0731 |       0.0959 |

## Logo vs AUM churn

|    |   logo |   aum_value |   soft_contraction_value |
|:---|-------:|------------:|-------------------------:|
| 6m | 0.0604 |      0.0626 |                   0.0392 |

## Churn por decil de riesgo latente

|   decil_riesgo_latente |   hard_churn |   soft_churn |
|-----------------------:|-------------:|-------------:|
|                      1 |       0.0010 |       0.0111 |
|                      2 |       0.0040 |       0.0191 |
|                      3 |       0.0096 |       0.0297 |
|                      4 |       0.0136 |       0.0392 |
|                      5 |       0.0206 |       0.0478 |
|                      6 |       0.0287 |       0.0805 |
|                      7 |       0.0387 |       0.0981 |
|                      8 |       0.0609 |       0.1374 |
|                      9 |       0.1217 |       0.1791 |
|                     10 |       0.3048 |       0.2414 |

## Trayectoria principal

| primary_driver   |   households |   hard_churn |
|:-----------------|-------------:|-------------:|
| neglect          |   6,181.0000 |       0.0586 |
| outflow          |   7,494.0000 |       0.0807 |
| service          |   6,202.0000 |       0.0376 |

## Diccionario de columnas

| Columna | Unidad | Descripción |
|---|---|---|
| household_id | id | Identificador del hogar |
| snapshot_date | fecha | Fecha de corte t (ISO 8601) |
| segment | categoría | HNW / UHNW (UHNW si relationship_value ≥ USD 30M) |
| relationship_value | USD | AUM + depósitos en Citizens |
| deposit_balance | USD | Saldo en depósitos (checking, savings, MM, CD) |
| aum | USD | Valor de mercado de inversión, custodia y trust; NULL sin inversiones |
| has_investments | bool | Tiene cuentas de inversión |
| has_advisory | bool | Tiene cuentas advisory con benchmark |
| has_linked_business | bool | Tiene un negocio vinculado |
| has_trust | bool | Tiene trust |
| has_credit_anchor | bool | Tiene hipoteca o línea de crédito con Citizens |
| has_payroll_stream | bool | Recibe nómina en Citizens |
| has_pension_stream | bool | Recibe pensión / Social Security en Citizens |
| has_dividend_stream | bool | Recibe dividendos en Citizens |
| has_any_recurring_stream | bool | Tiene al menos un flujo recurrente (incl. negocio) |
| age_primary | años | Edad del titular principal |
| tenure_years | años | Antigüedad con el banco |
| history_months | meses | Historia disponible, tope 24 |
| salary_base_annual | USD | Sueldo base anual; NULL sin nómina |
| bonus_annual | USD | Bono anual (un pago); NULL sin nómina |
| pay_frequency | categoría | biweekly / semimonthly / monthly |
| pension_monthly | USD | Pensión mensual; NULL sin pensión |
| dividend_annual | USD | Dividendos anuales; NULL sin flujo de dividendos |
| business_distribution_annual | USD | Distribuciones anuales del negocio; NULL sin negocio |
| recurring_income_monthly | USD | Ingreso recurrente mensual sin bono |
| churn_excluded | bool | Excluido del target (muerte / reubicación) |
| hard_churn_6m | 0/1 | Salida total en (t, t+6m]; NULL si excluido |
| soft_churn_3m | 0/1 | Contracción > 20% sin salida en (t, t+3m]; NULL si excluido |
| value_lost_6m | USD | Valor perdido por churn; NULL si excluido |
