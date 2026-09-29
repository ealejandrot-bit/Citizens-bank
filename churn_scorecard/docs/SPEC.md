# SPEC — Churn Propensity Scorecard sobre `client_pulse_synthetic.xlsx`

Procedimiento completo, paso a paso. Se ejecuta con `/step NN` (ver CLAUDE.md). Este archivo es la fuente de verdad del
método; CLAUDE.md fija las convenciones de trabajo y `.claude/rules/` las reglas de reporte y de datos.

Pasos que terminan en gate: 0 → G0, 4 → G1, 11 → G2, 14 → G3, 17 → G4.

## C. FICHA DEL DATASET `[DATA]` — verifícala en `tests/test_step00.py` antes de cualquier otra cosa

Si algún hecho no coincide, detente: el archivo no es el esperado.

| Hecho | Valor |
|---|---|
| Hoja / filas / columnas | `client_pulse_synthetic` / 20,000 / 62 |
| Unidad | `household_id` (único, sin duplicados) |
| Snapshot | Un solo `snapshot_date` = 2025-12-31 (dataset transversal; **no hay panel ni cohortes**) |
| Segmento | HNW 18,897 · UHNW 1,103 |
| `churn_excluded` | 123 filas True (targets en NaN); `history_months` 13–24, `tenure_years` ≥ 1.14 |
| Elegibles | 19,877 |
| `hard_churn_6m` | 1,200 eventos = 6.04% de elegibles; para todos ellos `value_lost_6m / relationship_value` = 1.000 (pérdida total) |
| `soft_churn_3m` | 1,756 eventos = 8.83%; `value_lost_6m / relationship_value` entre 0.20 y 0.60 (mediana 0.40); disjunto de hard (0 solapes) |
| `value_lost_6m` | > 0 exactamente en hard ∪ soft (2,956 filas); es resultado post-T0 |
| Churn por valor | Σ RV de hard / Σ RV = 6.46%; Σ value_lost / Σ RV = 10.32% |
| Tamaño | Σ `relationship_value` = 206.27 BUSD; Σ `aum` = 135.09 BUSD (17,030 con inversiones); top 5% por RV = 37.4%, top 1% = 18.1%; mediana RV 4.84 MUSD, p5 1.27, p95 31.8 |
| `relationship_value` ≠ `aum` + `deposit_balance` | Verdadero: RV es una medida propia; documentar su definición como pregunta abierta |
| Missing = "no aplica" (estructural) | `aum`, `aum_outflow_*`, `investment_redemption_pct`, `positions_liquidated_pct`, `cash_pct_of_portfolio_chg`, `aum_vs_baseline_pct` faltan ⟺ `has_investments` = False (2,847); `pension_deposit_stopped_flag` ⟺ `has_pension_stream`; `business_payroll_stopped_flag` ⟺ `has_linked_business`; `salary_deposit_stopped_flag` ⟺ `has_payroll_stream`; `trustee_change_flag` ⟺ `has_trust`; `return_vs_benchmark` ⟺ `has_advisory` (con ~1–3% de excepciones a documentar) |
| Missing no estructural relevante | `client_reply_rate` 48.0%, `meetings_cancelled_by_client` 60.7%, `relationship_dissatisfaction_flag` 70.4%, `fixed_income_maturity_not_reinvested` 73.9% |
| Antigüedad / historia | `tenure_years` < 1: 404 filas; `history_months` < 24: 1,417 filas |
| Compuestos | `multi_signal_flag` ≡ (`multi_signal_count` ≥ 3) exacto; `multi_signal_count` (0–7) NO se reconstruye con los flags visibles (ρ = 0.59 con su suma); tasa hard por count: 2.8% (0) → 44.8% (7) |
| Señal univariada | Ninguna variable con AUC > 0.70 vs hard (máx: `multi_signal_count` 0.69, `banker_change_6m_flag` 0.64, `share_of_wallet` 0.64) ⟹ sin fuga evidente, señal moderada |
| Gradiente por tamaño | Tasa hard plana por decil de RV (5.2%–7.1%): churn por valor ≈ churn por relaciones |
| Pares redundantes (\|Spearman\| > 0.75) | `aum_outflow_pct_90d`~`aum_outflow_90d` 0.98; `relationship_value`~`aum` 0.97; `net_deposit_flow_pct_90d`~`deposit_balance_vs_6m_avg_pct` 0.91; `deposit_balance_change_pct_90d`~`deposit_balance_vs_6m_avg_pct` 0.88; `transfer_to_competitor_pct_90d`~`..._amount_90d` 0.82; `deposit_balance_change_pct_90d`~`net_deposit_flow_pct_90d` 0.80; `aum_outflow_pct_90d`~`aum_vs_baseline_pct` 0.77; `salary_deposit_stopped_flag`~`recurring_deposit_stopped_flag` 0.76; `multi_signal_flag`~`multi_signal_count` 0.76; `net_deposit_flow_pct_90d`~`net_external_flow_pct_90d` 0.76 |
| Valores imposibles | Ninguno detectado en saldos, porcentajes, antigüedad, `share_of_wallet` ∈ (0, 1] |

Consecuencias que gobiernan todo el diseño:
- **No hay dimensión temporal**: no existe OOT, no hay cohortes, no hay PSI temporal. Validación = holdout estratificado
  + K-fold repetido; la ausencia de OOT es una limitación obligatoria del documento, no se maquilla.
- **Las señales ya vienen ingenierizadas** (ventanas 60/90/180 días y 6M, baselines, flags). La ingeniería de señales se
  limita a derivadas transversales; no se reconstruyen series.
- **Columnas de resultado** (`hard_churn_6m`, `soft_churn_3m`, `value_lost_6m`, `churn_excluded`) están prohibidas como
  predictores. `value_lost_6m` sólo se usa para churn por valor y para calibración por AUM.
- **La cartera es mayoritariamente HNW**; UHNW = 1,095 elegibles con 80 eventos hard: por debajo del mínimo de 100
  eventos para scorecard separado. Se modela el libro completo con `segment` como variable y se reporta desempeño y
  calibración de UHNW por separado.

Parámetros `[DEF]` que se conservan del diseño original: escala S₀ = 600 @ O₀ = 20:1 (buenos:malos), PDO = 40 ⟹
Factor = 57.71, Offset = 427.12. Parámetros del escenario sintético anterior (2,000 relaciones, 40 banqueros, cohortes)
**quedan sustituidos por la ficha** y por las preguntas de la sección I.

## D. REGLAS NO NEGOCIABLES

1. Cero benchmarks de industria y cero cifras de bancos reales. Marco = MRM; no cites Basilea ni IFRS 9.
2. Ningún predictor usa columnas de resultado ni transformaciones de ellas. Todas las demás columnas se asumen as-of T0
   por construcción del proveedor: esa asunción se declara como limitación (no hay timestamps para auditarla).
3. Missing estructural ("no aplica") es una categoría con significado: bin propio en el scorecard, `NaN` nativo en GBM,
   indicador explícito cuando aporte. Nunca imputar por media/mediana.
4. Correlación no es causación. Ningún threshold sin evidencia. Ningún peso arbitrario.
5. PCA sólo como diagnóstico de redundancia (paso 8); prohibido en selección y en modelo.
6. Clustering permitido en pre-segmentación (7), arquetipos de churners (16) y clustering de variables (10); ajustado en
   desarrollo, asignado a validación sin reajuste; nunca causal.
7. Campeón 100% interpretable: cada variable con signo, lógica de negocio y monotonicidad. Challenger: EBM y GBM
   monotónico, poco profundo, explicado con TreeSHAP en log-odds. SHAP explica; no vuelve aditivo al modelo.
8. Score único = puntos escala PDO. La probabilidad calibrada se muestra como probabilidad; "0–100 = 100·p" no es un score.
9. Split 70/30 estratificado por target y segmento (una fila por household ⟹ no hay agrupación que hacer, pero se
   documenta). K-fold repetido sólo dentro de desarrollo. El holdout se toca una sola vez por modelo final.
10. Desbalance: pesos de clase, nunca SMOTE. Pesos guardados para corregir intercepto.
11. La selección campeón vs. challenger es multi-criterio (sección H). PR-AUC es la función objetivo del tuning, no el
    criterio de selección.
12. `multi_signal_count` y `multi_signal_flag` son compuestos del proveedor con regla no documentada: se permiten en el
    challenger y en el análisis; entran al campeón sólo si el proveedor entrega la regla (pregunta I-3). Si entran, se
    prueba su aporte incremental contra las señales subyacentes; si desplazan a todas, se documenta como riesgo de
    auditoría.
13. Colas pesadas: no eliminar outliers automáticamente; clasificar (error / real / extraordinario); capping sólo para
    errores documentados.

## G. PROCEDIMIENTO

### Paso 0 — Verificación y definición del problema (termina en G0)
- `src/step00_profile.py`: carga, `tests/test_step00.py` con los asserts de la ficha (filas, columnas, N elegibles, eventos
  hard/soft, unicidad de `household_id`, un solo snapshot, mapa de missing estructural).
- Tabla de alternativas de target **con los conteos del archivo**:

| Opción | Definición | Eventos `[DATA]` | Tasa | Indeterminados | Comentario |
|---|---|---|---|---|---|
| A | `hard_churn_6m` = pérdida total a 6M | 1,200 | 6.04% | 0 | Es cierre total, no fuga parcial; horizonte 6M |
| B | hard ∪ (soft con `value_lost_6m/RV` ≥ 0.25) = pérdida ≥ 25% dentro de 6M | 2,740 | 13.9% de 19,661 | 216 (soft con ratio 0.20–0.25, fuera de entrenamiento, dentro de scoring) | Es la definición económica del diseño original (θ = 25%); mezcla horizontes 3M/6M (3M ⊂ 6M) |
| C | hard ∪ soft | 2,956 | 14.9% | 0 | θ implícito = 20% |
| D | soft sólo | 1,756 | 8.83% | 0 | Sólo fuga parcial a 3M |

  Propuesta: **B como target principal** (coherente con churn económico y θ = 25%), **A como sensibilidad obligatoria** y
  como target del bloque de supervivencia si se pide. El usuario decide en G0.
- Horizonte: fijado por el dato (6M para A/B). Ventana de observación: la de las señales del proveedor (60/90/180 días,
  6M, baseline); `history_months` ≤ 24.
- Unidad: household (dada). T0 = 2025-12-31 (único). Sin cohortes.
- Anti-leakage: lista explícita de columnas prohibidas; placebo temporal imposible (declarar); cribado por AUC univariada
  > 0.85 e IV > 0.50.
- Churn rate vs. score vs. probabilidad: fórmulas y valores `[DATA]` del churn rate por households y por RV para A y B.

### Paso 1 — Target y churn rate
- Construir `y`, `y_indet`, `w` (pesos). Sensibilidad de eventos a θ = 25/35/50% sobre `value_lost_6m/RV` (tabla con
  conteos).
- Exclusiones con volumen: `churn_excluded` (123, motivo desconocido → pregunta I-4); `tenure_years` < 1 (404; regla
  original de antigüedad < 12M → pregunta I-8); `history_months` < 24 (1,417; se conservan con indicador salvo
  instrucción). Tabla de exclusiones acumuladas y N final.
- Censura: no aplica (no hay tiempo al evento); si se pide supervivencia, sólo es posible un modelo de tiempo discreto a
  dos periodos (3M/6M) usando soft/hard como etapas: documentar como opción limitada.
- Fórmulas y valores: churn por households, por RV, bruto (Σ RV de eventos / Σ RV) y económico (Σ value_lost / Σ RV).

### Paso 2 — Diccionario de datos
- `src/step02_dictionary.py` genera `outputs/tables/step02_dictionary.csv` con: nombre, tipo, unidad inferida, % missing,
  missing estructural (sí/no y columna gatillo), rango, significado de negocio, bloque (transaccional / patrimonial /
  relación / producto / servicio / digital / vida / economía / compuesto / estructural / resultado), dirección esperada
  vs. churn (signo a priori, a completar por el usuario si no es evidente), uso permitido (predictor / prohibido /
  auxiliar).
- Digital: no hay logins ni sesiones en el archivo; declarar dimensión ausente.

### Paso 3 — Calidad de datos
- Por variable: % missing, media, mediana, sd, p1/p5/p25/p50/p75/p95/p99, mín, máx; duplicados; negativos e imposibles;
  excepciones al missing estructural (los ~1–3% de casos con flag presente sin la condición); consistencia
  `has_investments` vs. `aum`; `relationship_value` vs. `aum` + `deposit_balance`.
- Outliers: clasificar colas de `relationship_value`, `value_lost_6m`, `aum_outflow_90d`,
  `transfer_to_competitor_bank_amount_90d` como real/extraordinario; sin capping salvo error probado.
- Asserts: N elegibles, sin duplicados, sin negativos en saldos, mapa estructural reproducido.

### Paso 4 — Muestra (termina en G1)
- Split 70/30 estratificado por (`y`, `segment`), `SEED = 42`; `data/processed/dev.parquet`, `val.parquet`. Tabla N y
  eventos por partición y por segmento. Repeated StratifiedKFold 5×5 dentro de dev para tuning y estabilidad.
- No hay OOT: declarar y registrar en `decision_log.md` como limitación L1.

### Paso 5 — Ingeniería de señales (transversal)
- Derivadas permitidas: `log_rv`, `aum_share = aum/RV`, `deposit_share`, `streams_stopped_count` (suma de flags de streams
  detenidos, con "no aplica" = 0 e indicador de elegibilidad), `n_products_held` (suma de `has_*`),
  `outflow_x_contact_gap`, `competitor_x_new_destinations`, indicadores de missing estructural, peer-relative por celda
  `segment` × banda de RV (cuantiles de dev) para `aum_outflow_pct_90d`, `net_deposit_flow_pct_90d`, `contact_gap_ratio`
  (celdas ≥ 100 households; medianas calculadas en dev).
- Tabla: variable, definición, dimensión (de las nueve del diseño; marcar las ausentes: digital), signo esperado, origen
  (proveedor / derivada).

### Paso 6 — Análisis univariado
- Para cada candidata vs. `y`: distribución por grupo, mediana, percentiles, effect size (Cliff's δ o diferencia
  estandarizada), tasa de churn por bin (deciles), missingness por grupo, AUC univariada e IV preliminar. Marcar
  candidatas y sospechosas de fuga.

### Paso 7 — Pre-segmentación
- K-means y GMM sobre estructurales (`segment`, `age_primary`, `tenure_years`, `log_rv`, `has_*`); K por silhouette, WCSS,
  estabilidad bootstrap, tamaño ≥ 5%, interpretabilidad. Tasa de churn por cluster sin causalidad. UHNW (80 eventos) ⟹
  sin scorecard separado; `segment` y cluster como candidatas; calibración por segmento en paso 14.

### Paso 8 — Correlación y diagnóstico de estructura
- Pearson, Spearman, VIF; pares > 0.6 listados con decisión (cuál aporta información incremental por IV y contribución en
  modelo). PCA sobre bloques (depósitos, salidas de AUM, externalización) sólo para varianza explicada y loadings; no
  entra al modelo.

### Paso 9 — Binning, WoE, IV (campeón)
- `optbinning` con `monotonic_trend="auto_asc_desc"`, `min_bin_size = 0.05`, mínimo 30 eventos por bin, missing como bin
  propio; comparar con cuantiles y business-defined. WoE = ln(%buenos/%malos), IV = Σ(%buenos − %malos)·WoE; umbrales
  0.02/0.10/0.30/0.50. Tabla WoE/IV completa para las 3 variables de mayor IV y resumen para todas.

### Paso 10 — Selección
- Campeón: relevancia de negocio, calidad, IV, clustering de variables (representante = menor (1−R²propio)/(1−R²vecino),
  desempate por IV), contribución incremental (ΔGini por adición), ElasticNet sobre WoE, VIF < 5. Cierre 6–10 variables
  con diversidad por dimensión (N permite hasta 10).
- Challenger (preselección): casi constantes; fuga (AUC > 0.85 o IV > 0.50); un representante por cluster |ρ| > 0.75;
  permutation importance OOF > 0 en ≥ 80% de folds; signo de negocio definido. Cierre 15–30.

### Paso 11 — Estimación (termina en G2)
- Régimen: eventos en dev ≈ 840 (A) o ≈ 1,918 (B) ⟹ **> 300: logística sobre WoE**.
- 11A Campeón: logística (statsmodels) sobre WoE con pesos; todos los β > 0 sobre WoE; intercepto corregido:
  β₀ = β₀* − ln(odds muestra) + ln(odds población). Tabla de coeficientes, p-valores, VIF.
- 11B Challenger: EBM (`interpret`) y XGBoost/LightGBM con `monotone_constraints` por variable (convención +1 ⟹ mayor
  variable, mayor churn); tabla de signos derivada del paso 6 y confirmada en G1. Espacio Optuna: `max_depth` {2,3},
  `min_child_weight` [5,50], `learning_rate` log-U[0.01,0.1], `n_estimators` por early stopping, `subsample` [0.6,0.9],
  `colsample_bytree` [0.5,0.9], `reg_lambda` [1,20], `reg_alpha` [0,5], `gamma` [0,5]; 150 trials, MedianPruner,
  objetivo = PR-AUC media en RepeatedStratifiedKFold 5×5 en dev; sensibilidad a 3 semillas. Variante con entradas WoE.
  RF sólo como referencia.
- Explicabilidad: `shap.TreeExplainer(model_output="raw")`; PDP/ICE con violaciones de monotonía = 0; SHAP interaction +
  ALE; interacciones > 20% de |φ| ⟹ documentar o restringir; estabilidad de reason codes en 200 réplicas bootstrap
  (≥ 70%).
- Tabla comparativa (sección H) y recomendación.

### Paso 12 — Escalamiento, tramos, salida por household
- Factor 57.71, Offset 427.12. Campeón: puntos por bin = (βⱼ·WoEⱼ + β₀/n)·Factor + Offset/n;
  `outputs/tables/step12_lookup.csv`. Challenger: Score = Offset − Factor·f_cal(x), f_cal = a + b·(φ₀ + Σφⱼ); puntos
  por variable = −Factor·b·φⱼ; residuo de redondeo al base; assert Σ = score por fila.
- Tramos sobre probabilidad calibrada: Crítico / Alto / Vigilancia / Estable con criterios en orden: capacidad (pregunta
  I-2; sin respuesta, reportar el caseload implícito por banquero para 40 / 100 / 200 banqueros), salto ≥ 2x contiguo
  (≥ 1.5x admisible en Vigilancia/Estable si la curva de gains no lo soporta), lift Crítico/Estable ≥ 5x, ≥ 30 eventos
  por tramo en validación. Bandas AAA…CCC/D con ≥ 30 eventos cada una, mapeadas a tramos.
- Escala maestra (dos tablas: households y RV): rango de score, probabilidad, % households, % RV, churn esperado,
  captura, lift, gobernanza. Prioridad intra-tramo = p × RV.
- Overrides disponibles en el archivo: `banker_change_6m_flag`, `complaint_escalated_flag`,
  `transfer_to_competitor_pct_90d` ≥ 10% (equivalente al "≥ 10% en un movimiento"), `trustee_change_flag`; no existen
  fallecimiento ni liquidity event (declarar). Precisión por regla en validación: ≥ 25% se queda, 12–25% baja a Alto,
  < 12% se elimina; ninguno > 30% del tramo.
- `outputs/scores/household_scores.csv`: `household_id`, segmento, cluster, score, probabilidad, tramo, banda, top 3
  drivers con puntos, overrides activos.

### Paso 13 — Validación
- AUC, PR-AUC, KS, Gini, lift y gains por decil, Precision@K y Lift@K para K = 1/5/10/20% con captura ponderada por RV;
  matriz de confusión al corte de Crítico con "falsos positivos por evento capturado".
- Aprobación: monotonicidad de tasa observada por tramo en dev y val; caída de Gini dev→val ≤ 15% relativo; PSI dev→val
  < 0.10 por tramo. Desempeño de UHNW reportado aparte (80 eventos totales: sólo métricas globales, sin tramos).

### Paso 14 — Calibración (termina en G3)
- Platt sobre validación (0.8 ≤ b ≤ 1.2); isotónica permitida sólo si validación tiene ≥ 300 eventos (A: 360 ✓,
  B: ≈ 820 ✓) y se compara con Platt por Brier y ECE con IC bootstrap. Alineación de la media de p con la tasa observada.
- Tramo: esperado vs. observado con Wilson 90%; shrinkage beta-binomial m = 30. Por segmento y por RV: Σ pᵢ·RVᵢ vs.
  Σ value_lost observado por tramo; si descalibra en la cola alta, interacción con `log_rv`.
- Intervención vs. predicción: sin cohortes pre/post, sólo diseño del control aleatorio 10–15% en Alto para el despliegue.
- Calibración parcial: proporción del churn a 3M vs. 6M derivable de soft (3M) y hard (6M) sólo como descriptivo.

### Paso 15 — Estabilidad
- PSI de score, de p_cal y de cada variable dev vs. val, por segmento, banda de RV, banda de antigüedad,
  `history_months`, cluster. Deriva de |φⱼ| entre folds. Sin PSI temporal (limitación L1).

### Paso 16 — Acción, arquetipos, EWS
- Clustering sólo de los eventos por sus señales pre-T0 (K-means/GMM; K por criterios); 3–4 arquetipos nombrados después
  de revisar centroides. Playbook tramo × arquetipo: responsable, SLA (Crítico ≤ 5 días hábiles, Alto ≤ 15), acción,
  cadencia. EWS: disparo por entrada a Crítico/Alto, override, y regla de migración diseñada para el refresco mensual
  futuro (no evaluable con un snapshot).

### Paso 17 — KPIs, monitoreo, gobernanza, limitaciones
- KPIs, disparadores (recalibración b fuera de 0.8–1.2 dos ciclos; redesarrollo PSI > 0.25 sostenido o Gini −15%),
  `reports/model_document.md` con índice completo.
- Limitaciones obligatorias: L1 sin OOT ni cohortes; L2 señales pre-ingenierizadas sin timestamps auditables; L3
  compuestos sin regla documentada; L4 dataset sintético (no representa cartera real; nada de lo aquí estimado se
  presenta como resultado de un banco); L5 UHNW sub-representado (80 eventos); L6 sin dimensión digital ni eventos de
  vida; L7 causalidad y efecto de la propia intervención no identificables.

## H. TABLAS DE DECISIÓN

Tabla 1 — Régimen por eventos de desarrollo: < 50 híbrido experto; 50–300 logística penalizada; > 300 logística sobre
WoE + challenger ML. **Aquí: > 300.**
Tabla 2 — Reemplazo del campeón por el challenger (todas obligatorias, medidas en validación): ΔGini ≥ +0.05 y
ΔPR-AUC ≥ +0.03; caída dev→val ≤ 15% y no peor que campeón; Brier ≤ campeón con b ∈ [0.8, 1.2]; violaciones de
monotonía = 0; reason codes estables (≥ 70%) y con signo coherente en 100% de variables; captura por RV en decil top
≥ campeón; PSI dev→val < 0.10 por tramo.
Tabla 3 — Cortes de tramos: capacidad → salto 2x (1.5x en Vigilancia/Estable si aplica) → lift ≥ 5x → ≥ 30 eventos.

## I. PREGUNTAS OBLIGATORIAS EN G0 (con default)

- **I-1** Target: A (hard, 6.04%) o B (hard ∪ soft ≥ 25%, 13.9%). Default: **B**, con A como sensibilidad.
- **I-2** Número de banqueros y capacidad (stock de casos críticos abiertos por banquero). Default: sin dato → Crítico
  dimensionado por lift/precisión/eventos y tabla de caseload implícito para 40 / 100 / 200 banqueros.
- **I-3** Regla de construcción de `multi_signal_count`. Default: desconocida → excluido del campeón, permitido en
  challenger.
- **I-4** Motivo de `churn_excluded` (123). Default: se excluyen y se documenta motivo desconocido.
- **I-5** Definición de `relationship_value` y de `share_of_wallet` (denominador). Default: se usan como vienen;
  limitación documentada.
- **I-6** Escala: S₀ = 600 @ 20:1, PDO = 40. Default: sí.
- **I-7** ¿Modelar el libro completo con `segment` como variable y reportar UHNW aparte? Default: sí (80 eventos UHNW
  impiden scorecard separado).
- **I-8** Exclusión de `tenure_years` < 1 (404). Default: excluir (regla de antigüedad < 12M del diseño original).
- **I-9** ¿Bloque de supervivencia a tiempo discreto (3M soft → 6M hard)? Default: no; sólo descriptivo en paso 14.
- **I-10** Uso de `value_lost_6m` para calibración por valor. Default: sí (es resultado, nunca predictor).

## J. ENTREGABLE Y CIERRE

`reports/model_document.md` consolidado en orden 0–17, precedido por modo, ficha del dataset, parámetros y supuestos.
Cierra con: (a) qué cambiaría con datos reales del banco y con panel temporal (cohortes, OOT, PSI temporal, placebo
temporal, series para velocidad/aceleración, dimensión digital, eventos de vida); (b) preguntas para el equipo de datos
(I-3, I-4, I-5 y las que surjan); (c) limitaciones L1–L7; (d) registro de decisiones final. Sin resumen ejecutivo.
Artefactos: `outputs/tables/step12_lookup.csv`, `outputs/tables/step12_master_scale_households.csv`,
`outputs/tables/step12_master_scale_rv.csv`, `outputs/scores/household_scores.csv`, `outputs/model/` (campeón y
challenger serializados con versión), `tests/` en verde.
