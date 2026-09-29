# Paso 6 · Análisis univariado

## Objetivo
- Medir en dev cuánto separa cada candidata a eventos de no eventos (target B; A como sensibilidad), en qué dirección y
  si hay sospecha de fuga.

## Método
- 69 candidatas [DATA] = proveedor (sin `age_primary` ni buró, G1-3) + derivadas + compuestos (solo challenger).
- δ de Cliff (continuas); RR con IC 95% (binarias e infladas en su mínimo); AUC univariada (missing → mediana solo para
  la métrica); IV preliminar con 10 cuantiles y bins de missing por razón (no aplica / sin dato).
- Candidata: IV ≥ 0.02 o RR significativo. Sospecha de fuga: AUC > 0.85 o IV > 0.50.

## Código
- `src/step06_univariate.py` · `tests/test_step06.py` · tablas `step06_univariate_B.csv`, `step06_univariate_A.csv`,
  `step06_rate_by_bin_*.csv`.

## Resultados

### Top 20 por IV preliminar, target B [DATA]
| variable                               | compuesto   |   δ Cliff |      RR | IC95 RR      |   AUC univariada |   IV preliminar | signo esperado   | signo observado   | evaluación                    |
|:---------------------------------------|:------------|----------:|--------:|:-------------|-----------------:|----------------:|:-----------------|:------------------|:------------------------------|
| multi_signal_count                     | True        |     0.317 | nan     |              |            0.659 |           0.463 | +                | +                 | coincide                      |
| banker_change_6m_flag                  | False       |     0.217 |   2.912 | [2.68, 3.17] |            0.608 |           0.289 | +                | +                 | coincide                      |
| multi_signal_flag                      | True        |     0.230 |   2.482 | [2.29, 2.69] |            0.615 |           0.252 | +                | +                 | coincide                      |
| client_reply_rate                      | False       |    -0.178 | nan     |              |            0.529 |           0.218 | −                | −                 | coincide                      |
| products_closed_180d                   | False       |     0.122 |   2.304 | [2.09, 2.54] |            0.561 |           0.217 | +                | +                 | coincide                      |
| streams_stopped_count                  | False       |     0.112 |   3.165 | [2.86, 3.51] |            0.556 |           0.200 | +                | +                 | coincide                      |
| external_transfer_pct_of_balance_60d   | False       |     0.164 | nan     |              |            0.582 |           0.191 | +                | +                 | coincide                      |
| aum_vs_baseline_pct                    | False       |    -0.185 | nan     |              |            0.582 |           0.182 | −                | −                 | coincide                      |
| deposit_balance_vs_6m_avg_pct          | False       |    -0.170 | nan     |              |            0.585 |           0.178 | −                | −                 | coincide                      |
| share_of_wallet                        | False       |    -0.219 | nan     |              |            0.610 |           0.173 | −                | −                 | coincide                      |
| transfer_to_competitor_bank_amount_90d | False       |     0.142 | nan     |              |            0.571 |           0.173 | +                | +                 | sin evidencia / sin hipótesis |
| net_external_flow_pct_90d              | False       |    -0.156 | nan     |              |            0.578 |           0.166 | −                | −                 | coincide                      |
| transfer_to_competitor_pct_90d         | False       |     0.137 | nan     |              |            0.569 |           0.163 | +                | +                 | sin evidencia / sin hipótesis |
| outflow_x_contact_gap                  | False       |     0.161 | nan     |              |            0.580 |           0.161 | +                | +                 | coincide                      |
| ind_sin_dato_client_reply_rate         | False       |     0.198 |   2.015 | [1.84, 2.20] |            0.599 |           0.160 | +                | +                 | coincide                      |
| new_external_destinations_90d          | False       |     0.111 |   2.901 | [2.61, 3.22] |            0.555 |           0.160 | +                | +                 | coincide                      |
| net_deposit_flow_pct_90d               | False       |    -0.160 | nan     |              |            0.580 |           0.149 | −                | −                 | coincide                      |
| net_deposit_flow_pct_90d_peer          | False       |    -0.160 | nan     |              |            0.580 |           0.148 | −                | −                 | coincide                      |
| recurring_deposit_stopped_flag         | False       |     0.095 |   3.279 | [2.93, 3.67] |            0.545 |           0.144 | +                | +                 | coincide                      |
| deposit_balance_change_pct_90d         | False       |    -0.153 | nan     |              |            0.576 |           0.138 | −                | −                 | coincide                      |

- Candidatas: 47 de 69 [DATA]. Sospecha de fuga: 0 (ninguna) [DATA].
- Discrepancias de signo (efecto relevante y signo contrario al esperado): 0 (ninguna) [DATA].
- AUC univariada máxima B: 0.659 (`multi_signal_count`) [DATA].

### A vs B (IV y AUC; top 15 por IV B) [DATA]
| variable                               |   IV preliminar B |   AUC univariada B |   IV preliminar A |   AUC univariada A |
|:---------------------------------------|------------------:|-------------------:|------------------:|-------------------:|
| multi_signal_count                     |             0.463 |              0.659 |             0.665 |              0.694 |
| banker_change_6m_flag                  |             0.289 |              0.608 |             0.439 |              0.642 |
| multi_signal_flag                      |             0.252 |              0.615 |             0.399 |              0.649 |
| client_reply_rate                      |             0.218 |              0.529 |             0.266 |              0.530 |
| products_closed_180d                   |             0.217 |              0.561 |             0.335 |              0.588 |
| streams_stopped_count                  |             0.200 |              0.556 |             0.278 |              0.575 |
| external_transfer_pct_of_balance_60d   |             0.191 |              0.582 |             0.325 |              0.609 |
| aum_vs_baseline_pct                    |             0.182 |              0.582 |             0.302 |              0.598 |
| deposit_balance_vs_6m_avg_pct          |             0.178 |              0.585 |             0.281 |              0.617 |
| share_of_wallet                        |             0.173 |              0.610 |             0.283 |              0.643 |
| transfer_to_competitor_bank_amount_90d |             0.173 |              0.571 |             0.295 |              0.607 |
| net_external_flow_pct_90d              |             0.166 |              0.578 |             0.282 |              0.604 |
| transfer_to_competitor_pct_90d         |             0.163 |              0.569 |             0.286 |              0.601 |
| outflow_x_contact_gap                  |             0.161 |              0.580 |             0.240 |              0.594 |
| ind_sin_dato_client_reply_rate         |             0.160 |              0.599 |             0.196 |              0.608 |

- Correlación de rangos del IV entre targets: 0.982 [DATA]: las mismas señales
  ordenan ambos targets.

## Tests
- `tests/test_step06.py` (ver pytest).

## Decisiones y preguntas abiertas
- D6.1 en `reports/decision_log.md`.
