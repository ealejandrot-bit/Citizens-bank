# Paso 12 · Escalamiento, tramos, salida por household

## Objetivo
- Pasar el campeón a puntos (escala PDO), definir tramos y bandas con reglas previas a ver resultados, y entregar el score
  por household con drivers y overrides.

## Método
- Escala: S₀ = 600 @ 20:1, PDO = 40 ⟹ Factor 57.71, Offset 427.12 [DEF-default I-6]. Score = base + Σ puntos;
  base = Offset + Factor·β₀ = 531 [DATA]; puntos_j = Factor·β_j·WoE_j (enteros). Score alto = menos churn.
- Probabilidad = la del score (intercepto corregido, pre-Platt); se recalibra en el paso 14 (D12.1).
- Tramos (H-3) en dev: grilla de percentiles 1%; saltos ≥ 2x (Crítico/Alto, Alto/Vigilancia), ≥ 1.5x
  (Vigilancia/Estable), lift Crítico/Estable ≥ 5x, ≥ 70 eventos por tramo en dev (≈ 30 en validación; D12.2);
  entre factibles, mayor IV de tramo (3,085 configuraciones factibles [DATA]).
- Overrides: precisión de los hogares movidos en dev (≥ 25% Crítico, 12–25% Alto, < 12% fuera; ≤ 30% del tramo destino; D12.3).
- Drivers: variables con más puntos perdidos frente a su mejor bin.
- Bins no observados en dev ("sin dato" en hogares con antigüedad < 1): 0 puntos, neutral, marcados en el lookup (D12.5):
  `banker_change_6m_flag` 106, `outflow_x_contact_gap` 27, `return_vs_benchmark` 251, `cash_pct_of_portfolio_chg` 131 hogares [DATA].

## Código
- `src/step12_scaling.py` · `tests/test_step12.py` · `step12_*.csv`, `outputs/scores/household_scores.csv`.

## Resultados

### Cortes de tramo [DATA]
| corte                |   percentil dev (peor score) |   score ≤ |
|:---------------------|-----------------------------:|----------:|
| Crítico / Alto       |                          4.0 |     445.0 |
| Alto / Vigilancia    |                         21.0 |     517.0 |
| Vigilancia / Estable |                         71.0 |     573.0 |

### Escala maestra · households (dev, tramo final con overrides) [DATA]
| tramo      |   score mín |   score máx |   hogares |   % hogares |   p media % |   churn esperado (Σp) |   eventos observados |   tasa observada % |   captura eventos % |   lift | gobernanza [DEF-default paso 16]                      |
|:-----------|------------:|------------:|----------:|------------:|------------:|----------------------:|---------------------:|-------------------:|--------------------:|-------:|:------------------------------------------------------|
| Crítico    |         296 |         445 |       544 |        4.04 |       59.25 |                322.32 |                  308 |              56.62 |               16.46 |   4.08 | banquero + líder de equipo, contacto ≤ 5 días hábiles |
| Alto       |         446 |         624 |      3184 |       23.62 |       21.79 |                693.68 |                  728 |              22.86 |               38.91 |   1.65 | banquero, contacto ≤ 15 días hábiles                  |
| Vigilancia |         518 |         573 |      5977 |       44.33 |       11.40 |                681.28 |                  656 |              10.98 |               35.06 |   0.79 | seguimiento en revisión mensual                       |
| Estable    |         574 |         640 |      3777 |       28.02 |        5.52 |                208.30 |                  179 |               4.74 |                9.57 |   0.34 | gestión normal                                        |

- Verificación: % hogares suma 100.0%; captura suma 100.0%; churn de cartera
  Σ share × tasa = 13.88% = tasa dev 13.88% [DATA].
- Saltos de tasa [DATA]: Crítico/Alto 2.48x · Alto/Vigilancia 2.08x ·
  Vigilancia/Estable 2.32x · lift Crítico/Estable 11.95x.

### Escala maestra · RV (dev) [DATA]
| tramo      |   % RV |   captura RV de eventos % |   RV total $M |   RV de eventos $M |   RV esperado en riesgo $M (Σ p·RV) |
|:-----------|-------:|--------------------------:|--------------:|-------------------:|------------------------------------:|
| Crítico    |    4.7 |                      18.0 |       6,599.8 |            3,908.4 |                             3,816.2 |
| Alto       |   22.9 |                      40.6 |      32,293.1 |            8,812.7 |                             6,878.1 |
| Vigilancia |   41.7 |                      30.9 |      58,854.3 |            6,724.0 |                             6,552.0 |
| Estable    |   30.7 |                      10.5 |      43,318.2 |            2,285.9 |                             2,384.8 |

- Verificación: % RV suma 100.0%; captura RV de eventos suma 100.0% [DATA].

### Escala antes de overrides (dev) [DATA]
| tramo      |   hogares |   % hogares |   eventos observados |   tasa observada % |   lift |
|:-----------|----------:|------------:|---------------------:|-------------------:|-------:|
| Crítico    |       544 |        4.04 |                  308 |              56.62 |   4.08 |
| Alto       |      2336 |       17.33 |                  599 |              25.64 |   1.85 |
| Vigilancia |      6731 |       49.93 |                  774 |              11.50 |   0.83 |
| Estable    |      3871 |       28.71 |                  190 |               4.91 |   0.35 |

### Bandas (dev) [DATA]
| banda   |   hogares |   eventos |   tasa |   score_mín |   score_máx | tramo      |
|:--------|----------:|----------:|-------:|------------:|------------:|:-----------|
| CCC/D   |       544 |     308.0 |   56.6 |         296 |         445 | Crítico    |
| B       |      2336 |     599.0 |   25.6 |         446 |         517 | Alto       |
| BB      |      3024 |     392.0 |   13.0 |         518 |         543 | Vigilancia |
| BBB     |      3707 |     382.0 |   10.3 |         544 |         573 | Vigilancia |
| AA      |      1617 |     102.0 |    6.3 |         574 |         587 | Estable    |
| AAA     |      2254 |      88.0 |    3.9 |         588 |         640 | Estable    |

- Verificación: hogares suman 13,482 = 13,482; eventos 1,871 = 1,871 [DATA].

### Overrides (diseño en dev) [DATA]
| regla                                | destino probado   |   hogares activos dev |   movidos dev |   precisión movidos % |   movidos / tramo destino % |   umbral precisión % | cumple precisión   | cumple ≤ 30%   | decisión   |
|:-------------------------------------|:------------------|----------------------:|--------------:|----------------------:|----------------------------:|---------------------:|:-------------------|:---------------|:-----------|
| banker_change_6m_flag = 1            | Crítico           |                  1977 |          1522 |                  23.7 |                       279.8 |                 25.0 | False              | False          | Alto       |
| banker_change_6m_flag = 1            | Alto              |                  1977 |           415 |                  13.5 |                        17.8 |                 12.0 | True               | True           | Alto       |
| complaint_escalated_flag = 1         | Crítico           |                   714 |           594 |                  25.6 |                       109.2 |                 25.0 | True               | False          | Alto       |
| complaint_escalated_flag = 1         | Alto              |                   714 |           392 |                  17.3 |                        16.8 |                 12.0 | True               | True           | Alto       |
| transfer_to_competitor_pct_90d ≥ 10% | Crítico           |                   651 |           296 |                  37.2 |                        54.4 |                 25.0 | True               | False          | Alto       |
| transfer_to_competitor_pct_90d ≥ 10% | Alto              |                   651 |            74 |                  14.9 |                         3.2 |                 12.0 | True               | True           | Alto       |
| trustee_change_flag = 1              | Crítico           |                   186 |           127 |                  22.8 |                        23.3 |                 25.0 | False              | True           | eliminada  |
| trustee_change_flag = 1              | Alto              |                   186 |            77 |                  11.7 |                         3.3 |                 12.0 | False              | True           | eliminada  |

- Activos: banker_change_6m_flag = 1 → Alto, complaint_escalated_flag = 1 → Alto, transfer_to_competitor_pct_90d ≥ 10% → Alto [DATA].
- Unión de reglas activas: 848 hogares movidos = 36.3% del tramo Alto del modelo,
  precisión 15.2% [DATA]. Cada regla cumple ≤ 30%; la unión no (D12.3, pregunta G3). Sin datos de fallecimiento ni liquidity event en el archivo.

### Caseload (20,000 hogares puntuados) [DATA]
| tramo   |   hogares (20,000 puntuados) |   por banquero (40) |   por banquero (100) |   por banquero (200) |
|:--------|-----------------------------:|--------------------:|---------------------:|---------------------:|
| Crítico |                          838 |                20.9 |                  8.4 |                  4.2 |
| Alto    |                         4757 |               118.9 |                 47.6 |                 23.8 |

### Ejemplo: Σ puntos + base = score (hogar HH000001) [DATA]
| componente                |   puntos |
|:--------------------------|---------:|
| base                      |      531 |
| client_reply_rate         |       25 |
| banker_change_6m_flag     |       12 |
| share_of_wallet           |       10 |
| outflow_x_contact_gap     |        4 |
| return_vs_benchmark       |        0 |
| streams_stopped_count     |        3 |
| cash_pct_of_portfolio_chg |        2 |
| contact_gap_ratio_peer    |        9 |

- Verificación: 531 + 65 = 596 = score 596 [DATA]; el test lo verifica en los 20,000 hogares.

### Lookup (puntos por bin) [DATA]
| variable                  | bin                      |    WoE |   puntos |   puntos (SPEC, base repartida) |
|:--------------------------|:-------------------------|-------:|---------:|--------------------------------:|
| client_reply_rate         | [-inf, 0.422619)         | -0.069 |       -3 |                          63.851 |
| client_reply_rate         | [0.422619, 0.513158)     |  0.482 |       18 |                          84.365 |
| client_reply_rate         | [0.513158, 0.677995)     |  0.547 |       20 |                          86.755 |
| client_reply_rate         | [0.677995, 0.755)        |  0.682 |       25 |                          91.802 |
| client_reply_rate         | [0.755, inf)             |  0.881 |       33 |                          99.204 |
| client_reply_rate         | sin_dato                 | -0.362 |      -13 |                          52.962 |
| banker_change_6m_flag     | [-inf, 0.5)              |  0.282 |       12 |                          78.416 |
| banker_change_6m_flag     | [0.5, inf)               | -1.052 |      -45 |                          21.686 |
| share_of_wallet           | [-inf, 0.13389)          | -1.090 |      -31 |                          35.834 |
| share_of_wallet           | [0.13389, 0.197202)      | -0.578 |      -16 |                          50.192 |
| share_of_wallet           | [0.197202, 0.236721)     | -0.218 |       -6 |                          60.313 |
| share_of_wallet           | [0.236721, 0.340652)     | -0.056 |       -2 |                          64.860 |
| share_of_wallet           | [0.340652, 0.52935)      |  0.108 |        3 |                          69.469 |
| share_of_wallet           | [0.52935, 0.658137)      |  0.287 |        8 |                          74.473 |
| share_of_wallet           | [0.658137, 0.987773)     |  0.355 |       10 |                          76.381 |
| share_of_wallet           | [0.987773, inf)          |  0.759 |       21 |                          87.725 |
| outflow_x_contact_gap     | [-inf, 0.00163989)       |  0.228 |        4 |                          70.689 |
| outflow_x_contact_gap     | [0.00163989, 0.00524003) | -0.026 |        0 |                          65.945 |
| outflow_x_contact_gap     | [0.00524003, 0.0106561)  | -0.149 |       -3 |                          63.630 |
| outflow_x_contact_gap     | [0.0106561, 0.0625231)   | -0.431 |       -8 |                          58.354 |
| outflow_x_contact_gap     | [0.0625231, inf)         | -1.394 |      -26 |                          40.331 |
| return_vs_benchmark       | [-inf, -0.0417518)       | -0.428 |      -18 |                          48.495 |
| return_vs_benchmark       | [-0.0417518, -0.0133325) | -0.078 |       -3 |                          63.163 |
| return_vs_benchmark       | [-0.0133325, 0.00768266) |  0.055 |        2 |                          68.727 |
| return_vs_benchmark       | [0.00768266, 0.0344468)  |  0.334 |       14 |                          80.423 |
| return_vs_benchmark       | [0.0344468, inf)         |  0.543 |       23 |                          89.133 |
| return_vs_benchmark       | no_aplica                | -0.005 |        0 |                          66.221 |
| streams_stopped_count     | [-inf, 0.5)              |  0.122 |        3 |                          69.855 |
| streams_stopped_count     | [0.5, 1.5)               | -0.842 |      -24 |                          42.756 |
| streams_stopped_count     | [1.5, inf)               | -2.004 |      -56 |                          10.099 |
| cash_pct_of_portfolio_chg | [-inf, 0.0160397)        |  0.147 |        4 |                          70.709 |
| cash_pct_of_portfolio_chg | [0.0160397, 0.0235241)   |  0.079 |        2 |                          68.734 |
| cash_pct_of_portfolio_chg | [0.0235241, 0.0415827)   | -0.001 |        0 |                          66.398 |
| cash_pct_of_portfolio_chg | [0.0415827, 0.14944)     | -0.286 |       -8 |                          58.056 |
| cash_pct_of_portfolio_chg | [0.14944, inf)           | -1.093 |      -32 |                          34.479 |
| cash_pct_of_portfolio_chg | no_aplica                |  0.079 |        2 |                          68.748 |
| contact_gap_ratio_peer    | [-inf, -0.213889)        |  0.482 |        9 |                          75.840 |
| contact_gap_ratio_peer    | [-0.213889, -0.152778)   |  0.406 |        8 |                          74.355 |
| contact_gap_ratio_peer    | [-0.152778, -0.0972222)  |  0.270 |        5 |                          71.693 |
| contact_gap_ratio_peer    | [-0.0972222, 0.0972222)  |  0.156 |        3 |                          69.478 |
| contact_gap_ratio_peer    | [0.0972222, 0.180556)    | -0.042 |       -1 |                          65.609 |
| contact_gap_ratio_peer    | [0.180556, 0.291667)     | -0.085 |       -2 |                          64.772 |
| contact_gap_ratio_peer    | [0.291667, 0.719444)     | -0.331 |       -6 |                          59.956 |
| contact_gap_ratio_peer    | [0.719444, 1.16944)      | -0.451 |       -9 |                          57.621 |
| contact_gap_ratio_peer    | [1.16944, inf)           | -0.697 |      -14 |                          52.804 |
| banker_change_6m_flag     | sin_dato                 |  0.000 |        0 |                          66.425 |
| outflow_x_contact_gap     | sin_dato                 |  0.000 |        0 |                          66.425 |
| return_vs_benchmark       | sin_dato                 |  0.000 |        0 |                          66.425 |
| cash_pct_of_portfolio_chg | sin_dato                 |  0.000 |        0 |                          66.425 |

## Tests
- `tests/test_step12.py` (ver pytest).

## Decisiones y preguntas abiertas
- D12.1–D12.4 en `reports/decision_log.md`.
