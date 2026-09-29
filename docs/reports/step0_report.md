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
| share deposit-only = E[p] | OK | 0.143 vs 0.144 |
| deposit-only UHNW < 8% | OK | 0.042 |
| valor ≤ tope Pareto | OK | máx 903,973,258 |
| bono: 0 o ≥ piso | OK | sin bono 0.249 |
| share UHNW en [2%, 10%] | OK | 5.515% |
| antigüedad < edad adulta | OK |  |
| history_months ≤ tope | OK |  |
| salary_base_annual NULL ⇔ sin flujo | OK |  |
| pension_monthly NULL ⇔ sin flujo | OK |  |
| dividend_annual NULL ⇔ sin flujo | OK |  |
| business_distribution_annual NULL ⇔ sin flujo | OK |  |
| sueldo ≥ piso PB | OK | min = 150,008 |
| mediana sueldo base en [$300k, $500k] | OK | 378,819 |
| corr(log sueldo, log patrimonio) en [0.30, 0.60] | OK | 0.384 |
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

|                    |       count |            mean |             std |            min |             5% |            25% |            50% |             75% |             95% |              max |
|:-------------------|------------:|----------------:|----------------:|---------------:|---------------:|---------------:|---------------:|----------------:|----------------:|-----------------:|
| relationship_value | 20,000.0000 | 10,381,939.7866 | 24,658,658.0905 | 1,000,062.5000 | 1,269,559.7925 | 2,475,457.0250 | 4,841,540.7500 | 10,194,870.2625 | 31,822,871.7955 | 903,973,258.1100 |
| deposit_balance    | 20,000.0000 |  3,581,436.9856 |  9,768,177.4292 |     1,358.2800 |   216,772.3120 |   692,859.3825 | 1,551,416.2050 |  3,434,962.4900 | 11,887,898.7730 | 419,923,774.5700 |
| aum                | 17,130.0000 |  7,939,874.8406 | 18,748,549.0536 |   113,383.2500 |   881,121.6620 | 1,834,332.0925 | 3,696,462.0850 |  7,756,118.5375 | 24,747,252.4800 | 773,011,257.6700 |
| age_primary        | 20,000.0000 |         60.4834 |         11.7048 |        28.0000 |        41.0000 |        52.0000 |        60.0000 |         68.0000 |         80.0000 |          94.0000 |
| tenure_years       | 20,000.0000 |          8.9860 |          6.1673 |         0.0100 |         1.6300 |         4.3700 |         7.6250 |         12.1325 |         20.9500 |          50.0000 |
| history_months     | 20,000.0000 |         23.3535 |          2.8047 |         0.0000 |        19.0000 |        24.0000 |        24.0000 |         24.0000 |         24.0000 |          24.0000 |

## Flags

|                          |   share |
|:-------------------------|--------:|
| has_investments          |  0.8565 |
| has_advisory             |  0.6026 |
| has_linked_business      |  0.2643 |
| has_trust                |  0.3187 |
| has_credit_anchor        |  0.3424 |
| has_payroll_stream       |  0.5386 |
| has_pension_stream       |  0.3401 |
| has_dividend_stream      |  0.4685 |
| has_any_recurring_stream |  0.9328 |

## Ingresos (USD)

|                              |       count |         mean |          std |          min |           5% |          25% |          50% |            75% |            95% |             max |
|:-----------------------------|------------:|-------------:|-------------:|-------------:|-------------:|-------------:|-------------:|---------------:|---------------:|----------------:|
| salary_base_annual           | 10,772.0000 | 441,213.1534 | 245,516.5759 | 150,008.4200 | 182,431.4945 | 270,144.9125 | 378,819.2100 |   541,454.7800 |   915,605.9440 |  2,645,329.4300 |
| bonus_annual                 | 10,772.0000 | 186,812.4493 | 202,332.7764 |       0.0000 |       0.0000 |  22,318.6300 | 139,987.2250 |   268,966.2125 |   573,189.8190 |  2,417,736.2000 |
| pension_monthly              |  6,801.0000 |  10,522.4372 |   5,450.6363 |   2,523.1500 |   4,234.8500 |   6,675.5600 |   9,280.5500 |    13,046.5500 |    20,805.2100 |     53,462.4600 |
| dividend_annual              |  9,370.0000 | 161,385.8936 | 441,890.8911 |     682.2400 |  11,887.9460 |  31,192.2775 |  66,637.7050 |   149,069.3625 |   546,162.1185 | 15,794,163.2900 |
| business_distribution_annual |  5,287.0000 | 859,594.6586 | 990,179.3193 |  27,106.3400 | 134,447.3260 | 315,231.1950 | 568,138.9600 | 1,024,427.7500 | 2,510,667.9620 | 16,691,166.7400 |
| recurring_income_monthly     | 20,000.0000 |  48,618.2001 |  68,525.8260 |       0.0000 |       0.0000 |  13,583.8400 |  30,842.8750 |    58,781.8675 |   152,483.2350 |  2,000,229.7700 |

## Mediana de ingresos por segmento (USD)

|                              |          HNW |           UHNW |
|:-----------------------------|-------------:|---------------:|
| salary_base_annual           | 368,546.1550 |   616,469.8650 |
| bonus_annual                 | 137,608.4150 |   208,386.4750 |
| pension_monthly              |   9,149.4200 |    12,254.5850 |
| dividend_annual              |  60,662.1750 |   673,425.5350 |
| business_distribution_annual | 520,075.7700 | 1,401,663.0600 |
| recurring_income_monthly     |  29,260.3800 |   119,212.1200 |

## Churn por segmento

| segment   |   households |   hard_churn |   soft_churn |
|:----------|-------------:|-------------:|-------------:|
| HNW       |  18,782.0000 |       0.0596 |       0.0879 |
| UHNW      |   1,095.0000 |       0.0731 |       0.0959 |

## Logo vs AUM churn

|    |   logo |   aum_value |   soft_contraction_value |
|:---|-------:|------------:|-------------------------:|
| 6m | 0.0604 |      0.0646 |                   0.0386 |

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
