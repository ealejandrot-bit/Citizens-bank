# Paso 0 · Verificación y definición del problema

## Objetivo
- Verificar la ficha del dataset (SPEC §C) contra `data/raw/client_pulse_synthetic.xlsx` y dejar calculadas las
  opciones de target, el churn rate y el cribado anti-fuga para decidir en G0.

## Método
- Carga de la hoja `client_pulse_synthetic`; hechos de la ficha recalculados por código; elegibles = `churn_excluded` = False.
- Target B: hard ∪ (soft con `value_lost_6m / relationship_value` ≥ θ = 0.25 [DEF propuesta]); soft con pérdida
  < θ = indeterminado (fuera de entrenamiento, dentro de scoring).
- Churn por hogares = eventos / base; por RV bruto = Σ RV de eventos / Σ RV; económico = Σ value_lost de eventos / Σ RV.
- Cribado anti-fuga: AUC univariada (missing → mediana solo para el cribado) e IV preliminar (10 cuantiles + bin de
  missing) contra A y B; sospecha si AUC > 0.85 o IV > 0.50.

## Código
- `src/step00_profile.py` · `tests/test_step00.py` · bootstrap único del archivo: `src/bootstrap_raw.py` (D0.1).

## Resultados

### Ficha del dataset [DATA]
| hecho                                                              | esperado (ficha)                                                                                    | observado [DATA]                                                                                                         | coincide   | nota                                                                                     |
|:-------------------------------------------------------------------|:----------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------|:-----------|:-----------------------------------------------------------------------------------------|
| Hoja / filas / columnas                                            | client_pulse_synthetic / 20,000 / 62                                                                | client_pulse_synthetic / 20,000 / 62                                                                                     | sí         |                                                                                          |
| household_id único                                                 | sí                                                                                                  | 20,000 únicos                                                                                                            | sí         |                                                                                          |
| Un solo snapshot                                                   | 2025-12-31                                                                                          | 2025-12-31                                                                                                               | sí         |                                                                                          |
| Segmento                                                           | HNW 18,897 · UHNW 1,103                                                                             | HNW 18,897 · UHNW 1,103                                                                                                  | sí         |                                                                                          |
| churn_excluded                                                     | 123; targets NaN; history 13–24; tenure ≥ 1.14                                                      | 123; targets NaN = True; history 13–24; tenure ≥ 1.14                                                                    | sí         |                                                                                          |
| Elegibles                                                          | 19,877                                                                                              | 19,877                                                                                                                   | sí         |                                                                                          |
| hard_churn_6m                                                      | 1,200 = 6.04%; pérdida = 1.000                                                                      | 1,200 = 6.04%; pérdida 1.000–1.000                                                                                       | sí         |                                                                                          |
| soft_churn_3m                                                      | 1,756 = 8.83%; pérdida 0.20–0.60, mediana 0.40; disjunto                                            | 1,756 = 8.83%; pérdida 0.2003–0.5994, mediana 0.3978; solapes 0                                                          | sí         |                                                                                          |
| value_lost_6m > 0 ⟺ hard ∪ soft                                    | 2,956                                                                                               | 2,956; ⟺ True                                                                                                            | sí         |                                                                                          |
| Churn por valor (elegibles)                                        | 6.46% bruto; 10.32% económico                                                                       | 6.46%; 10.32%                                                                                                            | sí         |                                                                                          |
| Tamaño (elegibles)                                                 | ΣRV 206.27 B; ΣAUM 135.09 B (17,030); top 5% 37.4%; top 1% 18.1%; mediana 4.84 M; p5 1.27; p95 31.8 | ΣRV 206.27 B; ΣAUM 135.09 B (17,030); top 5% 37.4%; top 1% 18.1%; mediana 4.84 M; p5 1.27; p95 31.8                      | sí         | la ficha usa elegibles (19,877), no las 20,000 filas                                     |
| relationship_value ≠ aum + deposit_balance ('RV es medida propia') | Verdadero                                                                                           | RV = aum (0 si NaN) + deposit_balance con |dif| máx $0.01; igualdad exacta de flotantes en 33.2% por redondeo a centavos | **NO**     | DISCREPANCIA D0.2: RV sí es la suma (al centavo); solo difiere por redondeo de flotantes |
| Missing estructural has_investments                                | faltan ⟺ has_investments = False (2,847)                                                            | 2,847 elegibles sin inversiones                                                                                          | sí         |                                                                                          |
| Missing no estructural                                             | 48.0 / 60.7 / 70.4 / 73.9 %                                                                         | 48.0 / 60.7 / 70.4 / 73.9 %                                                                                              | sí         |                                                                                          |
| Antigüedad / historia (elegibles)                                  | tenure < 1: 404; history < 24: 1,417                                                                | 404; 1,417                                                                                                               | sí         |                                                                                          |
| Compuestos                                                         | flag ≡ count ≥ 3; ρ = 0.59 con suma de flags; tasa hard 2.8% (0) → 44.8% (7)                        | ≡ True; ρ Pearson = 0.59 (10 binarias visibles; Spearman 0.47); 2.8% → 44.8%                                             | sí         | ρ = Pearson con las 9 *_flag + bureau (D0.3)                                             |
| Señal univariada (AUC vs hard, missing → mediana)                  | máx ≤ 0.70: count 0.69, banker 0.64, SOW 0.64                                                       | multi_signal_count 0.693; multi_signal_flag 0.648; banker_change_6m_flag 0.641; share_of_wallet 0.636                    | sí         | la ficha no lista multi_signal_flag (0.648), segundo en el ranking                       |
| Gradiente por tamaño                                               | tasa hard por decil de RV 5.2%–7.1%                                                                 | 5.2%–7.1%                                                                                                                | sí         |                                                                                          |
| Pares redundantes |Spearman| > 0.75                                | 10 pares (ver step00_pairs.csv)                                                                     | 10 de 10 coinciden (±0.015)                                                                                              | sí         |                                                                                          |
| Valores imposibles                                                 | ninguno                                                                                             | saldos < 0: 0; share_of_wallet ∉ (0, 1]: 0; tenure < 0: 0                                                                | sí         |                                                                                          |

- 19 de 20 hechos coinciden. Las cifras de tamaño, historia y missing de la ficha
  están calculadas sobre los 19,877 elegibles, no sobre las 20,000 filas (D0.4).
- **Discrepancia D0.2**: la ficha afirma que RV ≠ AUM + depósitos ("medida propia"). En el archivo RV = AUM (0 si no
  hay inversiones) + depósitos con diferencia máxima de $0.01 [DATA]; la desigualdad solo aparece al comparar flotantes
  exactos (redondeo a centavos). Pregunta al usuario en G0.

### Pares redundantes [DATA]
| var A                          | var B                                  |   |ρ| ficha |   |ρ| observado [DATA] | coincide (±0.015)   |
|:-------------------------------|:---------------------------------------|------------:|-----------------------:|:--------------------|
| aum_outflow_pct_90d            | aum_outflow_90d                        |        0.98 |                  0.979 | True                |
| relationship_value             | aum                                    |        0.97 |                  0.966 | True                |
| net_deposit_flow_pct_90d       | deposit_balance_vs_6m_avg_pct          |        0.91 |                  0.906 | True                |
| deposit_balance_change_pct_90d | deposit_balance_vs_6m_avg_pct          |        0.88 |                  0.882 | True                |
| transfer_to_competitor_pct_90d | transfer_to_competitor_bank_amount_90d |        0.82 |                  0.815 | True                |
| deposit_balance_change_pct_90d | net_deposit_flow_pct_90d               |        0.8  |                  0.803 | True                |
| aum_outflow_pct_90d            | aum_vs_baseline_pct                    |        0.77 |                  0.769 | True                |
| salary_deposit_stopped_flag    | recurring_deposit_stopped_flag         |        0.76 |                  0.764 | True                |
| multi_signal_flag              | multi_signal_count                     |        0.76 |                  0.761 | True                |
| net_deposit_flow_pct_90d       | net_external_flow_pct_90d              |        0.76 |                  0.757 | True                |

### Mapa de missing estructural (elegibles) [DATA]
| variable                      | gatillo             |   elegibles sin gatillo |   NaN sin gatillo |   valor sin gatillo (excepción) |   NaN con gatillo (excepción) |   % excepciones |
|:------------------------------|:--------------------|------------------------:|------------------:|--------------------------------:|------------------------------:|----------------:|
| aum                           | has_investments     |                    2847 |              2847 |                               0 |                             0 |            0.00 |
| aum_outflow_90d               | has_investments     |                    2847 |              2847 |                               0 |                            27 |            0.14 |
| aum_outflow_pct_90d           | has_investments     |                    2847 |              2847 |                               0 |                            27 |            0.14 |
| investment_redemption_pct     | has_investments     |                    2847 |              2847 |                               0 |                            27 |            0.14 |
| positions_liquidated_pct      | has_investments     |                    2847 |              2847 |                               0 |                            48 |            0.24 |
| cash_pct_of_portfolio_chg     | has_investments     |                    2847 |              2847 |                               0 |                           131 |            0.66 |
| aum_vs_baseline_pct           | has_investments     |                    2847 |              2847 |                               0 |                           131 |            0.66 |
| pension_deposit_stopped_flag  | has_pension_stream  |                   13116 |             12982 |                             134 |                            83 |            1.09 |
| business_payroll_stopped_flag | has_linked_business |                   14623 |             14623 |                               0 |                            64 |            0.32 |
| salary_deposit_stopped_flag   | has_payroll_stream  |                    9169 |              9169 |                               0 |                           230 |            1.16 |
| trustee_change_flag           | has_trust           |                   13556 |             13556 |                               0 |                             0 |            0.00 |
| return_vs_benchmark           | has_advisory        |                    7900 |              7900 |                               0 |                           251 |            1.26 |

- Regla verificada: sin gatillo ⟹ NaN, con 0 violaciones salvo `pension_deposit_stopped_flag`
  (134 con valor sin
  `has_pension_stream`). Los NaN con gatillo presente son las excepciones de 1–3% (historia corta o patrón no detectado).

### Opciones de target [DATA]
| opción   | definición                                                   |   eventos |   base |   indeterminados | comentario                                                                                             |   tasa % |
|:---------|:-------------------------------------------------------------|----------:|-------:|-----------------:|:-------------------------------------------------------------------------------------------------------|---------:|
| A        | hard_churn_6m = pérdida total a 6M                           |      1200 |  19877 |                0 | cierre total, no fuga parcial; horizonte 6M                                                            |     6.04 |
| B        | hard ∪ (soft con value_lost/RV ≥ 0.25) = pérdida ≥ 25% en 6M |      2740 |  19661 |              216 | definición económica (θ = 25%); soft 0.20–0.25 fuera de entrenamiento, dentro de scoring; mezcla 3M/6M |    13.94 |
| C        | hard ∪ soft                                                  |      2956 |  19877 |                0 | θ implícito = 20%                                                                                      |    14.87 |
| D        | soft sólo                                                    |      1756 |  19877 |                0 | solo fuga parcial a 3M                                                                                 |     8.83 |

- Propuesta (SPEC): **B** principal, **A** sensibilidad obligatoria. Decide el usuario (I-1).
- Verificación: A = 1,200 y C = hard + soft = 1,200 + 1,756 = 2,956 [DATA];
  B = C − indeterminados = 2,956 − 216 = 2,740 [DATA]; base B = 19,877 − 216 = 19,661 [DATA].

### Churn rate: hogares, RV bruto y económico [DATA]
| target   | segmento   |   base |   eventos |   churn hogares % |   churn RV bruto % (Σ RV eventos / Σ RV) |   churn económico % (Σ value_lost eventos / Σ RV) |
|:---------|:-----------|-------:|----------:|------------------:|-----------------------------------------:|--------------------------------------------------:|
| A        | Total      |  19877 |      1200 |              6.04 |                                     6.46 |                                              6.46 |
| A        | HNW        |  18782 |      1120 |              5.96 |                                     6.00 |                                              6.00 |
| A        | UHNW       |   1095 |        80 |              7.31 |                                     7.17 |                                              7.17 |
| B        | Total      |  19661 |      2740 |             13.94 |                                    15.20 |                                             10.19 |
| B        | HNW        |  18575 |      2564 |             13.80 |                                    13.91 |                                              9.38 |
| B        | UHNW       |   1086 |       176 |             16.21 |                                    17.20 |                                             11.45 |

- Verificación: churn de cartera = Σ share × tasa por segmento (A hogares:
  603.7128%
  = 6.0371% [DATA]).
- Churn rate (tasa de la cartera), score (puntos de la escala PDO: S₀ = 600 @ 20:1, PDO = 40 ⟹ Factor
  57.71, Offset 427.12 [DEF]) y probabilidad calibrada (por hogar) son tres magnitudes distintas.

### Anti-fuga [DATA]
- Prohibidas como predictor: `hard_churn_6m`, `soft_churn_3m`, `value_lost_6m`, `churn_excluded`, `household_id`, `snapshot_date`. Compuestos (`multi_signal_count`,
  `multi_signal_flag`): solo challenger / análisis hasta I-3.
- Placebo temporal: imposible (un solo snapshot, sin timestamps) → limitación L1/L2.
- Cribado: 1 variables sospechosas. Máximos: AUC A
  0.693 (`multi_signal_count`), AUC B 0.655
  (`multi_signal_count`), IV A 0.547
  (`multi_signal_count`), IV B 0.364
  (`multi_signal_count`).
- Control del cribado: `value_lost_6m` tendría AUC vs A = 0.976 [DATA] (el cribado sí detecta una columna
  de resultado).

Top 10 por AUC vs A:
| variable                             | compuesto   |   % missing |   AUC A |   IV A |   AUC B |   IV B |
|:-------------------------------------|:------------|------------:|--------:|-------:|--------:|-------:|
| multi_signal_count                   | True        |       0.000 |   0.693 |  0.547 |   0.655 |  0.364 |
| multi_signal_flag                    | True        |       0.000 |   0.648 |  0.339 |   0.615 |  0.221 |
| banker_change_6m_flag                | False       |       0.533 |   0.641 |  0.369 |   0.607 |  0.243 |
| share_of_wallet                      | False       |       0.000 |   0.636 |  0.266 |   0.608 |  0.166 |
| deposit_balance_vs_6m_avg_pct        | False       |       0.795 |   0.618 |  0.289 |   0.585 |  0.178 |
| share_of_wallet_change               | False       |       0.770 |   0.617 |  0.225 |   0.583 |  0.125 |
| contact_gap_ratio                    | False       |       0.000 |   0.617 |  0.173 |   0.599 |  0.123 |
| deposit_balance_change_pct_90d       | False       |       0.553 |   0.612 |  0.251 |   0.579 |  0.150 |
| net_deposit_flow_pct_90d             | False       |       0.287 |   0.609 |  0.238 |   0.581 |  0.146 |
| external_transfer_pct_of_balance_60d | False       |       0.080 |   0.608 |  0.318 |   0.576 |  0.175 |

- Tabla completa: `outputs/tables/step00_leakage_screen.csv`.

### Horizonte, unidad y T0
- Horizonte 6M (A y B) fijado por el dato; ventana de observación = la de las señales del proveedor (60/90/180 días,
  6M, baseline); `history_months` ≤ 24 [DATA]. Unidad: household. T0 = 2025-12-31 (único). Sin cohortes ni OOT (L1).

## Tests
- `tests/test_step00.py`: 16 tests, 16 PASS (`python -m pytest -q`).

## Decisiones y preguntas abiertas
- D0.1 bootstrap del xlsx · D0.2 discrepancia RV · D0.3 definición de ρ en compuestos · D0.4 base de la ficha =
  elegibles. Preguntas I-1 a I-10 en `reports/gate_0.md`.
