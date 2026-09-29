# SPEC — Client Pulse · Modelo 3 (NAM monótono)

Fuente de verdad del método. Las fases (§5) se ejecutan con `/fase N`; los parámetros viven en `config.yaml`.

## 1. Objetivo

Construir un Neural Additive Model monótono (una subred por variable, suma en log-odds, monotonía dura por signo de
negocio) y decidir, con un gate pre-registrado sobre el test, si supera al champion interpretable (LightGBM monótono o
EBM). Entregar calibración, scorecard PDO, EWS y un paquete MRM. Mismo split que M1 y M2 (comparación pareada).

## 2. Hechos del dataset a re-verificar en la fase 0 `[DATA]`

Heredados de la ficha verificada en M1 (paso 0) y M2 (paso 0). Base: 20,000 households salvo que se indique.

| # | Hecho | Valor esperado |
|---|---|---|
| 1 | Hoja / filas / columnas | `client_pulse_synthetic` / 20,000 / 62 |
| 2 | Unidad y snapshot | `household_id` único; un solo `snapshot_date` = 2025-12-31 |
| 3 | Segmento | HNW 18,897 · UHNW 1,103 |
| 4 | `churn_excluded` | 123 True; elegibles 19,877 |
| 5 | `hard_churn_6m` | 1,200 eventos = 6.04% de elegibles; pérdida = 100% del RV |
| 6 | `soft_churn_3m` | 1,756 = 8.83% de elegibles; disjunto de hard |
| 7 | `value_lost_6m` | > 0 exactamente en hard ∪ soft (2,956) |
| 8 | `relationship_value` | = AUM (0 sin inversiones) + depósitos, con diferencia máx. $0.01 (M1 D0.2) |
| 9 | Missing estructural | `aum` y derivados faltan ⟺ `has_investments` = False (2,847 elegibles) |
| 10 | Missing no estructural | `client_reply_rate` 48.0%, `meetings_cancelled_by_client` 60.7%, `relationship_dissatisfaction_flag` 70.4%, `fixed_income_maturity_not_reinvested` 73.9% (elegibles) |
| 11 | Antigüedad / historia | `tenure_years` < 1: 404; `history_months` < 24: 1,417 (elegibles) |
| 12 | Compuestos | `multi_signal_flag` ≡ (`multi_signal_count` ≥ 3); el count no se reconstruye con los flags visibles (ρ Pearson 0.59) |
| 13 | Señal univariada | ninguna variable con AUC > 0.70 vs hard |
| 14 | Split heredado (M1/M2) | dev 13,631 / val 5,842; target B: dev 1,871 eventos, val 803 |

## 3. Reglas absolutas

1. Dataset sintético y transversal: los reportes validan pipeline y metodología, no conclusiones sobre clientes.
2. Columnas de resultado (`value_lost_6m`, `hard_churn_6m`, `soft_churn_3m`, `churn_excluded`) nunca son features;
   tampoco `household_id` ni `snapshot_date`; edad y buró fuera (G1-3 de M1).
3. Missing estructural = categoría propia (indicador `app_<feature>` y valor neutro en el NAM); prohibido imputar por
   media/mediana sin indicador.
4. Monotonía dura por signo de negocio (§4) con violación = 0 verificada por test; nunca se relaja para converger.
5. Test abierto una sola vez (fase 10) con el gate de `config.yaml` fijado antes (fase 6). Nota: el mismo test ya fue
   mirado por M1 y M2; se declara como tercera mirada (L6).
6. Toda selección (features, hiperparámetros, champion, calibrador) se hace en train/validación.
7. Pesos de clase, nunca SMOTE; la probabilidad publicada es la calibrada.
8. Ningún número de un reporte a mano; todo sale de `outputs/pNN/`.
9. Parámetro en `null` ⟹ la fase que lo usa se detiene y pregunta.
10. Sin benchmarks de industria ni cifras de bancos reales; sin Basilea ni IFRS 9; PCA y clustering solo exploratorios.

## 4. Mapa de monotonía

Signos de negocio confirmados en M1 (G1-1) y usados en M2; `+` = mayor valor, más churn; `−` = mayor valor, menos
churn; `?` = libre. Dura = restricción con violación = 0 (test). Se re-confirman uno por uno en la fase 4.

| variable | signo | tipo |
|---|:-:|---|
| banker_change_6m_flag, transfer_to_competitor_pct_90d, transfer_to_competitor_bank_amount_90d, external_transfer_pct_of_balance_60d, new_external_destinations_90d, external_transfer_acceleration, external_destination_concentration, outflow_vs_baseline_pct, aum_outflow_pct_90d, aum_outflow_90d, investment_redemption_pct, positions_liquidated_pct, cash_pct_of_portfolio_chg, fixed_income_maturity_not_reinvested, salary_deposit_stopped_flag, recurring_deposit_stopped_flag, pension_deposit_stopped_flag, business_payroll_stopped_flag, products_closed_180d, accounts_closed_90d, trustee_change_flag, contact_gap_ratio, meetings_cancelled_by_client, complaint_escalated_flag, complaint_age_days, repeat_complaint_flag, relationship_dissatisfaction_flag | + | dura |
| client_reply_rate, share_of_wallet, share_of_wallet_change, deposit_balance_change_pct_90d, deposit_balance_vs_6m_avg_pct, net_deposit_flow_pct_90d, recurring_deposit_change_pct, net_external_flow_pct_90d, aum_vs_baseline_pct, return_vs_benchmark, tenure_years, has_* (8) | − | dura |
| segment, relationship_value, deposit_balance, aum, history_months, recurring_income_monthly | ? | libre |

## 5. Fases

| fase | nombre | entrega mínima | bloqueada por |
|---|---|---|---|
| 0 | Perfil | tabla esperado vs observado de §2 con discrepancias marcadas y explicadas | — |
| 1 | Target y población | tasas hard / soft / any_churn por segmento tras exclusiones; conteo por regla; preguntas al dueño del dato en STATUS | `target.*` |
| 2 | Data quality | missingness clasificada (estructural / ruido / sin regla); indicadores `app_<feature>`; decisión por variable para rangos extremos con filas afectadas (sin eliminar filas) | — |
| 3 | Leakage | `outputs/p03/leakage_table.csv`; `tests/test_leakage.py` la lee; decisión sobre `multi_signal_count` | `leakage.multi_signal_count` |
| 4 | Features y monotonía | feature dictionary con origen; mapa §4 cargado; confirmación del usuario signo por signo antes del commit | confirmación del usuario |
| 5 | EDA | churn rate por decil con IC; clusters de redundancia; PCA/clustering exploratorio (no entra al modelo sin evidencia) | — |
| 6 | Diseño de validación | train / validación / test guardados; EPV pooled y por segmento; `tests/test_splits.py`; gate impreso | `gate.delta_pr_auc`, `gate.delta_lift_at_5` |
| 7 | Benchmarks | logística, XGBoost, LightGBM en validación; pooled / HNW / UHNW; con y sin pesos de clase | — |
| 8 | Challenger interpretable | LightGBM monótono vs EBM en validación; champion provisional con evidencia | — |
| 9 | NAM monótono | `src/nam/`; `tests/test_monotone.py` (violación = 0 en duras); curva de entrenamiento; métricas en validación | PyTorch aprobado (§7) |
| 10 | Gate | única apertura del test: champion vs NAM con IC bootstrap, pooled y UHNW; `outputs/p10/decision.json` | gate lleno |
| 11 | Calibración | Platt vs isotónica en validación, elegida por ECE, evaluada en test; a y b guardados | — |
| 12 | Scorecard | lookup por bins; escala maestra por tasa observada en test; % de scores recortados; residual de completeness | `scorecard.*` |
| 13 | EWS y paquete MRM | curva alertas-por-mes vs churners capturados (pooled y UHNW); umbral solo si `ews.*`; modelo vs regla multi-señal reconstruida; `reports/MRM_package.md` | `ews.*` para el umbral |

## 6. Gate pre-registrado (fase 10)

El NAM reemplaza al champion solo si, en test y pooled: ΔPR-AUC (NAM − champion) ≥ `gate.delta_pr_auc` y
Δlift@5% ≥ `gate.delta_lift_at_5`, con el límite inferior del IC bootstrap pareado 95% (`gate.bootstrap_reps`) > 0 en
ambas; violación de monotonía = 0; y en UHNW sin deterioro (Δ con IC que incluye o supera 0). Si no, el NAM queda
documentado como challenger.

## 7. Dependencias

PyTorch (CPU) es necesario para el NAM y no está en los `requirements.txt` previos: se agrega aquí sujeto a aprobación
del usuario (regla de paquetes).

## 8. Limitaciones que abren el paquete MRM (fase 13)

L1 sin OOT ni cohortes (un snapshot); L2 señales pre-ingenierizadas sin timestamps; L3 compuestos sin regla documentada;
L4 dataset sintético; L5 UHNW pequeño (≈ 53 eventos B en test); L6 test ya mirado por M1 y M2 (tercera mirada).

## 9. Preguntas centrales que cierran el paquete MRM

1. ¿El NAM monótono supera al champion interpretable lo suficiente para justificar su complejidad?
2. ¿Cuántos churners (y cuánto RV) captura el EWS por cada 100 alertas?
3. ¿El modelo supera a la regla multi-señal reconstruida con los flags visibles?
