# Paso 0 · Reporte de población, latentes y target

Semilla maestra `20260928` · 20,000 hogares · corte 2025-12-31

## Chequeos

| Chequeo | Resultado | Detalle |
|---|---|---|
| filas | OK | 20,000 |
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
| has_any_recurring_stream |  0.9092 |

## Churn por segmento

| segment   |   households |   hard_churn |   soft_churn |
|:----------|-------------:|-------------:|-------------:|
| HNW       |  18,782.0000 |       0.0596 |       0.0879 |
| UHNW      |   1,095.0000 |       0.0731 |       0.0959 |

## Logo vs aum churn

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
