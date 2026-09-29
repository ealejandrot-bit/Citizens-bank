# Client Pulse · Base sintética final

20,000 hogares · corte 2025-12-31 · montos en USD · semilla `20260928`

- **Base principal:** `data/synthetic/client_pulse_synthetic.csv` (62 columnas: atributos del hogar, las 37 variables del Excel en su columna principal y el target).
- **Base completa:** `data/synthetic/client_pulse_synthetic_full.csv` (101 columnas: todas las ventanas y montos).
- **Target:** hard churn 6m 6.0% · soft churn 3m 8.8% · excluidos 0.6%.
- **AUC combinado de las 37 variables** (logística simple): **0.762**; techo con la probabilidad verdadera: 0.851. La base es predictiva sin ser irreal.

## Las 37 variables

|   # | variable (Excel)                     | grupo                        | prioridad   | fuerza Excel   | factibilidad   | columna                              |   NULL % |   alerta % |   IV |   lift |
|----:|:-------------------------------------|:-----------------------------|:------------|:---------------|:---------------|:-------------------------------------|---------:|-----------:|-----:|-------:|
|   1 | aum_outflow                          | Balances & AUM               | P1          | High           | Medium         | aum_outflow_pct_90d                  |    14.49 |       7.66 | 0.27 |   3.95 |
|   2 | deposit_balance_change_pct           | Balances & AUM               | P1          | High           | High           | deposit_balance_change_pct_90d       |     0.55 |      10.49 | 0.25 |   3.17 |
|   3 | salary_deposit_stopped_flag          | Recurring deposits & flows   | P1          | Very high      | Medium         | salary_deposit_stopped_flag          |    47.30 |       3.64 | 0.32 |   5.71 |
|   4 | recurring_deposit_stopped_flag       | Recurring deposits & flows   | P1          | High           | Medium         | recurring_deposit_stopped_flag       |     7.46 |       4.22 | 0.22 |   4.34 |
|   5 | recurring_deposit_change_pct         | Recurring deposits & flows   | P1          | High           | Medium         | recurring_deposit_change_pct         |     7.40 |      10.70 | 0.17 |   2.66 |
|   6 | net_deposit_flow                     | Recurring deposits & flows   | P1          | High           | High           | net_deposit_flow_pct_90d             |     0.29 |      27.72 | 0.24 |   2.04 |
|   7 | external_transfer_pct_of_balance     | Transfers                    | P1          | Very high      | High           | external_transfer_pct_of_balance_60d |     0.08 |       6.49 | 0.32 |   4.93 |
|   8 | new_external_destinations            | Transfers                    | P1          | High           | High           | new_external_destinations_90d        |     3.48 |       5.95 | 0.29 |   4.36 |
|   9 | investment_redemption_pct            | Investments                  | P1          | High           | Medium         | investment_redemption_pct            |    14.49 |       6.19 | 0.17 |   2.88 |
|  10 | products_closed                      | Relationship & closures      | P1          | Very high      | High           | products_closed_180d                 |     0.53 |       9.74 | 0.36 |   3.36 |
|  11 | banker_change_6m_flag                | Banker                       | P1          | Very high      | High           | banker_change_6m_flag                |     0.53 |      14.85 | 0.44 |   4.10 |
|  12 | contact_gap_ratio                    | Banker                       | P1          | High           | Medium         | contact_gap_ratio                    |     0.00 |       3.67 | 0.17 |   2.00 |
|  13 | client_reply_rate                    | Banker                       | P1          | High           | Medium         | client_reply_rate                    |    47.99 |      25.50 | 0.24 |   1.95 |
|  14 | complaint_escalated_flag             | Complaints & voice of client | P1          | High           | High           | complaint_escalated_flag             |     0.00 |       5.34 | 0.13 |   3.11 |
|  15 | complaint_age_days                   | Complaints & voice of client | P1          | High           | High           | complaint_age_days                   |     0.00 |       1.99 | 0.12 |   3.75 |
|  16 | multi_signal_flag                    | External & composite         | P1          | High           | Medium         | multi_signal_flag                    |     0.00 |      23.96 | 0.64 |   3.41 |
|  17 | aum_vs_baseline_pct                  | Balances & AUM               | P2          | High           | Medium         | aum_vs_baseline_pct                  |    15.00 |       6.17 | 0.29 |   5.18 |
|  18 | deposit_balance_vs_6m_avg_pct        | Balances & AUM               | P2          | High           | High           | deposit_balance_vs_6m_avg_pct        |     0.79 |       9.94 | 0.29 |   3.62 |
|  19 | pension_deposit_stopped_flag         | Recurring deposits & flows   | P2          | High           | Medium         | pension_deposit_stopped_flag         |    65.75 |       1.95 | 0.22 |   5.81 |
|  20 | business_payroll_stopped_flag        | Recurring deposits & flows   | P2          | High           | Medium         | business_payroll_stopped_flag        |    73.89 |       5.65 | 0.16 |   3.33 |
|  21 | transfer_to_competitor_bank_amount   | Transfers                    | P2          | High           | Medium         | transfer_to_competitor_pct_90d       |     0.16 |       5.05 | 0.30 |   6.14 |
|  22 | external_transfer_acceleration       | Transfers                    | P2          | High           | High           | external_transfer_acceleration       |     0.16 |       4.27 | 0.22 |   4.84 |
|  23 | net_external_flow                    | Transfers                    | P2          | High           | High           | net_external_flow_pct_90d            |     0.16 |       5.13 | 0.26 |   5.05 |
|  24 | external_destination_concentration   | Transfers                    | P2          | High           | Medium         | external_destination_concentration   |     0.16 |       6.03 | 0.22 |   4.47 |
|  25 | outflow_vs_baseline_pct              | Transfers                    | P2          | High           | High           | outflow_vs_baseline_pct              |     0.77 |       7.60 | 0.11 |   2.37 |
|  26 | fixed_income_maturity_not_reinvested | Investments                  | P2          | High           | Medium         | fixed_income_maturity_not_reinvested |    73.91 |      36.84 | 0.21 |   2.05 |
|  27 | cash_pct_of_portfolio_chg            | Investments                  | P2          | High           | High           | cash_pct_of_portfolio_chg            |    15.00 |       7.89 | 0.14 |   2.74 |
|  28 | return_vs_benchmark                  | Investments                  | P2          | High           | Medium         | return_vs_benchmark                  |    40.99 |      31.60 | 0.12 |   1.64 |
|  29 | accounts_closed                      | Relationship & closures      | P2          | High           | High           | accounts_closed_90d                  |     0.16 |      14.34 | 0.23 |   1.89 |
|  30 | share_of_wallet                      | Relationship & closures      | P2          | High           | Medium         | share_of_wallet                      |     0.00 |      26.65 | 0.27 |   2.21 |
|  31 | share_of_wallet_change               | Relationship & closures      | P2          | High           | Medium         | share_of_wallet_change               |     0.77 |      13.69 | 0.22 |   2.65 |
|  32 | trustee_change_flag                  | Relationship & closures      | P2          | High           | Medium         | trustee_change_flag                  |    68.13 |       4.57 | 0.21 |   3.83 |
|  33 | repeat_complaint_flag                | Complaints & voice of client | P2          | High           | Medium         | repeat_complaint_flag                |     0.00 |       3.66 | 0.17 |   4.02 |
|  34 | positions_liquidated_pct             | Investments                  | P3          | High           | Medium         | positions_liquidated_pct             |    14.59 |       1.58 | 0.19 |   3.72 |
|  35 | meetings_cancelled_by_client         | Banker                       | P3          | High           | Low            | meetings_cancelled_by_client         |    60.72 |       5.28 | 0.16 |   2.08 |
|  36 | relationship_dissatisfaction_flag    | Complaints & voice of client | P3          | High           | Low            | relationship_dissatisfaction_flag    |    70.45 |       4.12 | 0.12 |   2.99 |
|  37 | bureau_new_mortgage_elsewhere        | External & composite         | P3          | High           | Low            | bureau_new_mortgage_elsewhere        |     5.04 |       3.97 | 0.16 |   3.71 |

## Pares más correlacionados (|ρ de Spearman| ≥ 0.6)

Son los pares redundantes que anticipa el Excel; el scorecard debe quedarse con uno de cada par (por IV).

|                                                                       |     ρ |
|:----------------------------------------------------------------------|------:|
| ('net_deposit_flow_pct_90d', 'deposit_balance_vs_6m_avg_pct')         |  0.91 |
| ('deposit_balance_change_pct_90d', 'deposit_balance_vs_6m_avg_pct')   |  0.88 |
| ('deposit_balance_change_pct_90d', 'net_deposit_flow_pct_90d')        |  0.8  |
| ('aum_outflow_pct_90d', 'aum_vs_baseline_pct')                        | -0.77 |
| ('salary_deposit_stopped_flag', 'recurring_deposit_stopped_flag')     |  0.77 |
| ('net_deposit_flow_pct_90d', 'net_external_flow_pct_90d')             |  0.76 |
| ('recurring_deposit_stopped_flag', 'pension_deposit_stopped_flag')    |  0.73 |
| ('deposit_balance_vs_6m_avg_pct', 'share_of_wallet_change')           |  0.71 |
| ('deposit_balance_vs_6m_avg_pct', 'net_external_flow_pct_90d')        |  0.69 |
| ('deposit_balance_change_pct_90d', 'share_of_wallet_change')          |  0.67 |
| ('aum_outflow_pct_90d', 'investment_redemption_pct')                  |  0.67 |
| ('investment_redemption_pct', 'fixed_income_maturity_not_reinvested') |  0.64 |
| ('deposit_balance_change_pct_90d', 'net_external_flow_pct_90d')       |  0.62 |

## Diccionario de la base principal

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
| age_primary | años | Edad del titular principal |
| tenure_years | años | Antigüedad con el banco |
| history_months | meses | Historia disponible, tope 24 |
| recurring_income_monthly | USD | Ingreso recurrente mensual sin bono |
| aum_outflow_pct_90d | fracción | #1 · aum_outflow_90d ÷ AUM promedio (alerta > 10%) |
| deposit_balance_change_pct_90d | fracción | #2 · media 3m ÷ 3m previos − 1 (alerta ≤ −25%); NULL si base < $10k |
| salary_deposit_stopped_flag | 0/1 | #3 · nómina detectada que dejó de llegar (45d); NULL sin patrón de nómina |
| recurring_deposit_stopped_flag | 0/1 | #4 · algún flujo recurrente ≥ 10% del ingreso dejó de llegar |
| recurring_deposit_change_pct | fracción | #5 · recurrente últimos 30d ÷ promedio mensual meses −7..−1 − 1 |
| net_deposit_flow_pct_90d | fracción | #6 · net_deposit_flow_90d ÷ saldo promedio (alerta ≤ −15%) |
| external_transfer_pct_of_balance_60d | fracción | #7 · ÷ saldo promedio (depósitos + cash en inversión) (alerta > 15%) |
| new_external_destinations_90d | entero | #8 · versión 90d (principal, D-18) |
| investment_redemption_pct | fracción | #9 · max(0, ventas y redenciones del cliente − compras) 90d ÷ AUM promedio (alerta > 20%) |
| products_closed_180d | entero | #10 · versión 180d (principal, D-20) |
| banker_change_6m_flag | 0/1 | #11 · cambió el banker principal en 6m (sin cobertura temporal < 30d) |
| contact_gap_ratio | ratio | #12 · días sin contacto significativo ÷ cadencia acordada (UHNW 30d, HNW 90d) (alerta > 2) |
| client_reply_rate | fracción | #13 · contactos del banker respondidos en ≤ 7d ÷ contactos, 90d; NULL si < 3 |
| complaint_escalated_flag | 0/1 | #14 · alguna queja escalada a gerencia / ombudsman / regulador / legal en 12m |
| complaint_age_days | días | #15 · días de la queja abierta más antigua; 0 si no hay (alerta > 30) |
| multi_signal_flag | 0/1 | #16 · ≥ 3 grupos en alerta |
| aum_vs_baseline_pct | fracción | #17 · AUM ex-mercado t ÷ media meses −6..−1 − 1 (alerta ≤ −20%) |
| deposit_balance_vs_6m_avg_pct | fracción | #18 · depósitos último mes ÷ media meses −6..−1 − 1 (alerta ≤ −30%) |
| pension_deposit_stopped_flag | 0/1 | #19 · pensión detectada que dejó de llegar; NULL sin patrón de pensión |
| business_payroll_stopped_flag | 0/1 | #20 · la nómina del negocio no corrió en 60d; NULL sin negocio / patrón |
| transfer_to_competitor_pct_90d | fracción | #21 · ÷ saldo promedio (alerta > 10%) |
| external_transfer_acceleration | fracción | #22 · [(A1 − A2) − (A2 − A3)] ÷ saldo promedio 90d |
| net_external_flow_pct_90d | fracción | #23 · ÷ saldo promedio (alerta ≤ −15%) |
| external_destination_concentration | fracción | #24 · HHI por institución (no por ABA), 90d |
| outflow_vs_baseline_pct | fracción | #25 · salidas último mes ÷ promedio mensual meses −7..−1 (piso $10k) − 1 |
| fixed_income_maturity_not_reinvested | fracción | #26 · principal vencido no reinvertido en 30d ÷ principal vencido; NULL sin vencimientos |
| cash_pct_of_portfolio_chg | fracción | #27 · cash % en t − promedio meses −6..−1 (0.10 = 10 pp) |
| return_vs_benchmark | fracción | #28 · TWR neto 12m − benchmark por perfil (−0.03 = −3 pp); NULL sin advisory |
| accounts_closed_90d | entero | #29 · cuentas cerradas en 90d (sin consolidación interna ni CD renovado) |
| share_of_wallet | fracción | #30 · (AUM + depósitos en Citizens) ÷ patrimonio total estimado, tope 1 (alerta < 30%) |
| share_of_wallet_change | fracción | #31 · SOW hoy − SOW hace 6 meses (−0.10 = −10 pp) |
| trustee_change_flag | 0/1 | #32 · Citizens deja de ser trustee o entra uno externo en 12m; NULL sin trust |
| repeat_complaint_flag | 0/1 | #33 · ≥ 2 quejas de la misma categoría (nivel 2) en 12m o alguna reabierta |
| positions_liquidated_pct | fracción | #34 · posiciones vendidas completas sin reemplazo 90d ÷ valor hace 90d (alerta > 15%) |
| meetings_cancelled_by_client | entero | #35 · reuniones canceladas por el cliente en 6m; NULL si el banker no registra el campo |
| relationship_dissatisfaction_flag | 0/1 | #36 · insatisfacción detectada por el Assistant y confirmada por una persona (30d); NULL fuera del piloto |
| bureau_new_mortgage_elsewhere | 0/1 | #37 · hipoteca / HELOC nueva con otro acreedor en 6m; NULL sin propósito permisible o sin aprobación legal |
| multi_signal_count | entero | #16 · nº de grupos del Excel (0–7) con alguna variable sobre su umbral de alerta |
| aum_outflow_90d | USD | #1 · max(0, retiros − aportes) de inversión, últimos 3 meses |
| transfer_to_competitor_bank_amount_90d | USD | #21 · enviado a bancos del catálogo de competidores, 90d |
| churn_excluded | bool | Excluido del target (muerte / reubicación) |
| hard_churn_6m | 0/1 | Salida total en (t, t+6m]; NULL si excluido |
| soft_churn_3m | 0/1 | Contracción > 20% sin salida en (t, t+3m]; NULL si excluido |
| value_lost_6m | USD | Valor perdido por churn; NULL si excluido |
