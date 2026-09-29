# Paso 5 · Ingeniería de señales (transversal)

## Objetivo
- Agregar solo derivadas transversales permitidas y dejar explícito el tratamiento del missing.

## Método
- Derivadas del SPEC; peer-relative con celdas `segment` × quintil de RV (cortes y medianas de dev).
- Razón de missing `<var>__miss` (ok / no_aplica / sin_dato); 134 valores de pensión sin gatillo recodificados a
  "no aplica" [DATA]. Sin imputación por media o mediana (el peer-relative resta la mediana de la celda; no imputa).
- Excluidas de los modelos por G1-3 [DEF-default]: `age_primary`, `bureau_new_mortgage_elsewhere`. Compuestos: solo
  challenger [DEF-default I-3].

## Código
- `src/step05_features.py` · `tests/test_step05.py` · `data/processed/features.parquet`.

## Resultados

### Variables [DATA]
| variable                                          | definición                                                                                          | dimensión     | signo esperado   | origen                      |
|:--------------------------------------------------|:----------------------------------------------------------------------------------------------------|:--------------|:-----------------|:----------------------------|
| segment_uhnw                                      | HNW / UHNW (UHNW si RV ≥ $30M)                                                                      | estructural   | ?                | proveedor                   |
| relationship_value                                | valor de la relación con el banco (= AUM + depósitos, G0-a)                                         | patrimonial   | ?                | proveedor                   |
| deposit_balance                                   | saldo en depósitos                                                                                  | patrimonial   | ?                | proveedor                   |
| aum                                               | activos bajo gestión (inversión, custodia, trust)                                                   | patrimonial   | ?                | proveedor                   |
| has_investments                                   | tiene cuentas de inversión                                                                          | producto      | −                | proveedor                   |
| has_advisory                                      | tiene advisory con benchmark                                                                        | producto      | −                | proveedor                   |
| has_linked_business                               | tiene negocio vinculado                                                                             | producto      | −                | proveedor                   |
| has_trust                                         | tiene trust                                                                                         | producto      | −                | proveedor                   |
| has_credit_anchor                                 | tiene hipoteca / línea con el banco                                                                 | producto      | −                | proveedor                   |
| has_payroll_stream                                | recibe nómina en el banco                                                                           | producto      | −                | proveedor                   |
| has_pension_stream                                | recibe pensión en el banco                                                                          | producto      | −                | proveedor                   |
| has_dividend_stream                               | recibe dividendos en el banco                                                                       | producto      | −                | proveedor                   |
| tenure_years                                      | antigüedad con el banco                                                                             | relación      | −                | proveedor                   |
| history_months                                    | historia transaccional disponible (tope 24)                                                         | estructural   | ?                | proveedor                   |
| recurring_income_monthly                          | ingreso recurrente mensual                                                                          | patrimonial   | ?                | proveedor                   |
| aum_outflow_pct_90d                               | salida neta de AUM 90d ÷ AUM promedio                                                               | transaccional | +                | proveedor                   |
| deposit_balance_change_pct_90d                    | cambio de depósitos 3m vs 3m previos                                                                | transaccional | −                | proveedor                   |
| salary_deposit_stopped_flag                       | la nómina dejó de llegar                                                                            | transaccional | +                | proveedor                   |
| recurring_deposit_stopped_flag                    | algún flujo recurrente relevante dejó de llegar                                                     | transaccional | +                | proveedor                   |
| recurring_deposit_change_pct                      | cambio del ingreso recurrente vs su promedio                                                        | transaccional | −                | proveedor                   |
| net_deposit_flow_pct_90d                          | flujo neto de depósitos 90d ÷ saldo promedio                                                        | transaccional | −                | proveedor                   |
| external_transfer_pct_of_balance_60d              | transferencias externas 60d ÷ saldo promedio                                                        | transaccional | +                | proveedor                   |
| new_external_destinations_90d                     | destinos externos nuevos 90d                                                                        | transaccional | +                | proveedor                   |
| investment_redemption_pct                         | redenciones netas 90d ÷ AUM promedio                                                                | transaccional | +                | proveedor                   |
| products_closed_180d                              | productos cerrados 180d                                                                             | producto      | +                | proveedor                   |
| banker_change_6m_flag                             | cambió el banquero principal 6m                                                                     | relación      | +                | proveedor                   |
| contact_gap_ratio                                 | días sin contacto ÷ cadencia acordada                                                               | relación      | +                | proveedor                   |
| client_reply_rate                                 | contactos respondidos ≤ 7d ÷ contactos 90d (NaN si < 3 contactos)                                   | relación      | −                | proveedor                   |
| complaint_escalated_flag                          | queja escalada 12m                                                                                  | servicio      | +                | proveedor                   |
| complaint_age_days                                | antigüedad de la queja abierta más vieja                                                            | servicio      | +                | proveedor                   |
| aum_vs_baseline_pct                               | AUM ex-mercado vs media 6m                                                                          | patrimonial   | −                | proveedor                   |
| deposit_balance_vs_6m_avg_pct                     | depósitos del último mes vs media 6m                                                                | transaccional | −                | proveedor                   |
| pension_deposit_stopped_flag                      | la pensión dejó de llegar                                                                           | transaccional | +                | proveedor                   |
| business_payroll_stopped_flag                     | la nómina del negocio no corrió                                                                     | transaccional | +                | proveedor                   |
| transfer_to_competitor_pct_90d                    | enviado a bancos competidores 90d ÷ saldo promedio                                                  | transaccional | +                | proveedor                   |
| external_transfer_acceleration                    | aceleración de transferencias externas (3 × 30d)                                                    | transaccional | +                | proveedor                   |
| net_external_flow_pct_90d                         | flujo externo neto 90d ÷ saldo promedio                                                             | transaccional | −                | proveedor                   |
| external_destination_concentration                | concentración de destinos externos                                                                  | transaccional | +                | proveedor                   |
| outflow_vs_baseline_pct                           | salidas del último mes vs promedio 6m                                                               | transaccional | +                | proveedor                   |
| fixed_income_maturity_not_reinvested              | principal vencido no reinvertido ÷ vencido                                                          | transaccional | +                | proveedor                   |
| cash_pct_of_portfolio_chg                         | cambio del % en cash del portafolio vs 6m                                                           | transaccional | +                | proveedor                   |
| return_vs_benchmark                               | rendimiento 12m − benchmark                                                                         | economía      | −                | proveedor                   |
| accounts_closed_90d                               | cuentas cerradas 90d                                                                                | producto      | +                | proveedor                   |
| share_of_wallet                                   | RV ÷ patrimonio total estimado (denominador sin definir, I-5)                                       | patrimonial   | −                | proveedor                   |
| share_of_wallet_change                            | cambio de SOW 6m                                                                                    | patrimonial   | −                | proveedor                   |
| trustee_change_flag                               | cambio de trustee 12m                                                                               | producto      | +                | proveedor                   |
| repeat_complaint_flag                             | queja repetida o reabierta 12m                                                                      | servicio      | +                | proveedor                   |
| positions_liquidated_pct                          | posiciones vendidas sin reemplazo 90d                                                               | transaccional | +                | proveedor                   |
| meetings_cancelled_by_client                      | reuniones canceladas por el cliente 6m                                                              | relación      | +                | proveedor                   |
| relationship_dissatisfaction_flag                 | insatisfacción detectada y confirmada (piloto)                                                      | servicio      | +                | proveedor                   |
| aum_outflow_90d                                   | salida neta de AUM 90d                                                                              | transaccional | +                | proveedor                   |
| transfer_to_competitor_bank_amount_90d            | monto enviado a competidores 90d                                                                    | transaccional | +                | proveedor                   |
| log_rv                                            | log10(relationship_value)                                                                           | patrimonial   | ?                | derivada                    |
| aum_share                                         | aum / RV (0 sin inversiones)                                                                        | patrimonial   | ?                | derivada                    |
| deposit_share                                     | deposit_balance / RV                                                                                | patrimonial   | ?                | derivada                    |
| streams_stopped_count                             | suma de flags de streams detenidos (salario, pensión, nómina de negocio, recurrente); no aplica = 0 | transaccional | +                | derivada                    |
| n_streams_eligible                                | streams con gatillo (nómina, pensión, negocio): elegibilidad del conteo                             | producto      | −                | derivada                    |
| n_products_held                                   | suma de has_* (8)                                                                                   | producto      | −                | derivada                    |
| outflow_x_contact_gap                             | aum_outflow_pct_90d (0 sin inversiones) × contact_gap_ratio                                         | transaccional | +                | derivada                    |
| competitor_x_new_destinations                     | transfer_to_competitor_pct_90d × new_external_destinations_90d                                      | transaccional | +                | derivada                    |
| ind_sin_dato_client_reply_rate                    | 1 si < 3 contactos del banquero en 90d (client_reply_rate sin dato)                                 | relación      | +                | derivada                    |
| ind_sin_dato_meetings_cancelled_by_client         | 1 si el banquero no registra reuniones                                                              | relación      | ?                | derivada                    |
| ind_sin_dato_relationship_dissatisfaction_flag    | 1 si fuera del piloto del Assistant                                                                 | servicio      | ?                | derivada                    |
| ind_sin_dato_fixed_income_maturity_not_reinvested | 1 si sin vencimientos de renta fija                                                                 | transaccional | ?                | derivada                    |
| aum_outflow_pct_90d_peer                          | aum_outflow_pct_90d − mediana de su celda segment × quintil de RV (dev)                             | transaccional | +                | derivada                    |
| net_deposit_flow_pct_90d_peer                     | net_deposit_flow_pct_90d − mediana de su celda (dev)                                                | transaccional | −                | derivada                    |
| contact_gap_ratio_peer                            | contact_gap_ratio − mediana de su celda (dev)                                                       | relación      | +                | derivada                    |
| <var>__miss                                       | razón de missing: ok / no_aplica / sin_dato                                                         | —             | —                | auxiliar (bins del campeón) |

### Dimensiones [DATA]
| dimensión     |   variables de proveedor | estado       |
|:--------------|-------------------------:|:-------------|
| transaccional |                       22 | presente     |
| patrimonial   |                        7 | presente     |
| relación      |                        5 | presente     |
| producto      |                       11 | presente     |
| servicio      |                        4 | presente     |
| economía      |                        1 | presente     |
| digital       |                        0 | AUSENTE (L6) |
| vida          |                        0 | AUSENTE (L6) |

### Celdas peer-relative [DATA]
| celda   |   hogares dev |
|:--------|--------------:|
| HNW_Q1  |          2575 |
| HNW_Q2  |          2574 |
| HNW_Q3  |          2575 |
| HNW_Q4  |          2574 |
| HNW_Q5  |          2575 |
| UHNW_Q1 |           152 |
| UHNW_Q2 |           151 |
| UHNW_Q3 |           152 |
| UHNW_Q4 |           151 |
| UHNW_Q5 |           152 |

- Todas las celdas con ≥ 100 hogares de dev: mínimo 151 [DATA].

## Tests
- `tests/test_step05.py` (ver pytest).

## Decisiones y preguntas abiertas
- D5.1 en `reports/decision_log.md`.
