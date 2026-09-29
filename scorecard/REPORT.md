# Churn Propensity Scorecard · Documento de modelo

Modelo 1 de 3 (scoring estadístico) · Client Pulse · Citizens Private Bank · base **sintética**.
Toda cifra es [DATA-SINT]: sale de los datos, pero la base es sintética; no es resultado de un banco real.

## Índice

0. [Setup e inventario](#0-setup-e-inventario)
1. [Target y churn rate](#1-target-y-churn-rate)
2. [Diccionario de datos](#2-diccionario-de-datos)
3. [Calidad de datos](#3-calidad-de-datos)

---

## 0. Setup e inventario

**Objetivo**
- Dejar el entorno reproducible y confirmar por código que la base es la descrita antes de modelar.

**Por qué**
- Un scorecard auditable empieza por una fuente identificada (ruta, hash, forma) y hechos verificados; si un hecho
  no cuadra, todo lo posterior hereda el error.

**Método**
- Lectura en solo lectura, hash SHA-256 de la fuente, versiones de paquetes congeladas en `requirements.txt`.
- 36 controles contra la sección DATOS del brief: forma, unicidad, corte, segmentos, targets, exclusiones,
  colas de valor, missing estructural (regla: `has_*` = False ⇒ NaN), bloque 40–74%, historia corta.
- Missing estructural: crosstab de cada variable contra los 8 `has_*`; se reporta la violación (valor donde no
  aplica) y los NaN adicionales donde sí aplica.

**Código** · `src/00_setup.py` (utilidades en `src/common.py`)

**Salida** · `outputs/tables/00_inventory.md` (hechos, mapa de missing, columnas), `00_facts_qc.csv`,
`00_missing_map.csv`, `00_columns.csv`, `00_versions.csv`

| Hecho [DATA-SINT] | Esperado | Observado |
|:--|:--|:--|
| Filas / `household_id` únicos / columnas | 20,000 / 20,000 / 62 | 20,000 / 20,000 / 62 |
| `snapshot_date` | 2025-12-31 único | 2025-12-31 único |
| `segment` | HNW 18,897 / UHNW 1,103 | HNW 18,897 / UHNW 1,103 |
| `hard_churn_6m` | 1,200 / 19,877 (6.04%) | 1,200 / 19,877 (6.04%) |
| `soft_churn_3m` | 1,756 (8.83%) | 1,756 (8.83%) |
| hard ∩ soft | 0 | 0 |
| Unión hard ∪ soft | 2,956 (14.9%) | 2,956 (14.87%) |
| `churn_excluded` / targets NaN | 123 / todos NaN | 123 / todos NaN |
| `value_lost_6m` > 0 sin evento | 0 | 0 |
| Eventos duros HNW / UHNW | 1,120 / 80 | 1,120 / 80 |
| `relationship_value` mediana / p99 / máx | $4.8M / $92M / $904M | $4.84M / $92.5M / $904.0M |
| Top 5% hogares, % del valor | 37.5% | 37.48% |
| `history_months` < 24 | 1,425 | 1,425 |
| `aum_vs_baseline_pct` missing si historia < 24 | ~24% | 23.7% |

Mapa de missing [DATA-SINT]:

| Variable | Condición de missing | % missing | Valores donde no aplica | NaN extra donde aplica |
|:--|:--|--:|--:|--:|
| `aum` | `has_investments` = False | 14.35 | 0 | 0 |
| `aum_outflow_90d`, `aum_outflow_pct_90d`, `investment_redemption_pct` | `has_investments` = False | 14.49 | 0 | 27 (todos historia < 24) |
| `positions_liquidated_pct` | `has_investments` = False | 14.59 | 0 | 48 (historia < 24) |
| `aum_vs_baseline_pct`, `cash_pct_of_portfolio_chg` | `has_investments` = False | 15.00 | 0 | 131 (historia < 24) |
| `pension_deposit_stopped_flag` | `has_pension_stream` = False | 65.74 | **134** | 84 |
| `business_payroll_stopped_flag` | `has_linked_business` = False | 73.89 | 0 | 64 |
| `trustee_change_flag` | `has_trust` = False | 68.13 | 0 | 0 |
| `salary_deposit_stopped_flag` | `has_payroll_stream` = False | 47.30 | 0 | 232 |
| `return_vs_benchmark` | `has_advisory` = False | 41.00 | 0 | 251 (historia < 24) |
| `client_reply_rate` | operativa: < 3 contactos en 90d | 47.99 | n/a | n/a |
| `meetings_cancelled_by_client` | operativa: campo no registrado por el banker | 60.72 | n/a | n/a |
| `relationship_dissatisfaction_flag` | operativa: fuera del piloto del Assistant | 70.45 | n/a | n/a |
| `fixed_income_maturity_not_reinvested` | operativa: sin vencimientos | 73.91 | n/a | n/a |

**QC** · 35 PASS · 1 WARN · 0 FAIL
- WARN: `pension_deposit_stopped_flag` tiene valor (siempre 0) en 134 hogares sin `has_pension_stream`
  (124 con `history_months` = 24). Excepción benigna (0 = "no se detuvo"); se recodifica a "no aplica" en el paso 3.
- Las 4 variables con missing operativo no tienen condición observable en la base: se confirma solo con el
  diccionario del generador. Pregunta para el equipo de datos en un banco real.

**Decisiones y alternativas descartadas** · D0.1–D0.4 en `DECISIONS.md`
- Fuente CSV en vez del XLSX indicado (no existe; el CSV cumple todos los hechos). Descartado convertir a XLSX.
- Proyecto aislado en `scorecard/` para no colisionar con el generador del repo.
- Missing operativo tratado como bin "sin dato", distinto de "no aplica" estructural.

**Parámetros confirmados por el usuario** (D0.5)
- Target primario `hard_churn_6m`; secundario `soft_churn_3m`; sensibilidad unión.
- Capacidad operativa: Crítico = top 3% por probabilidad (~600 hogares; ~180 en holdout), sin dato de banqueros.
- Inconsistencias: se documentan y se trabaja con los datos tal cual. Concentración de valor intacta (sin capping).

---

## 1. Target y churn rate

**Objetivo**
- Fijar el evento, la población y la tasa de churn de cartera por hogares y por valor, antes de cualquier score.

**Por qué**
- En banca privada un hogar grande pesa más que veinte chicos: la tasa por hogares y la tasa por valor responden
  preguntas distintas y su brecha es información. El score se calibrará contra estas tasas.

**Método y fórmulas**
- Población: 19,877 hogares (`churn_excluded` = False). Los 123 excluidos (muerte / reubicación; 0.66% del RV) quedan
  fuera de entrenamiento y métricas y se conservan en el scoring con bandera.
- Ventanas desde T0 = 2025-12-31: hard = salida total en (T0, T0+6m]; soft = contracción > 20% sin salida en
  (T0, T0+3m]. Corte único: sin censura ni tiempo al evento; cada hogar tiene la ventana completa.
- Churn por hogares = eventos ÷ hogares.
- Churn por valor (i) = Σ RVᵢ·yᵢ ÷ Σ RVᵢ (valor en riesgo); (ii) = Σ `value_lost_6m`ᵢ·yᵢ ÷ Σ RVᵢ (valor perdido).
- IC 95%: bootstrap de hogares, 500 réplicas estratificadas por segmento. RV crudo, sin capping (D1.2).

**Código** · `src/01_target.py`

**Salida** · `outputs/tables/01_churn_rates.csv`, `01_value_concentration.csv`, `01_partial_loss.csv`, `01_excluded.csv`

| Target | Segmento | Hogares | Eventos | Churn hogares % [IC95] | Churn valor (i) % [IC95] | Churn valor (ii) % [IC95] |
|:--|:--|--:|--:|:--|:--|:--|
| hard 6m | Total | 19,877 | 1,200 | 6.04 [5.67, 6.38] | 6.46 [5.56, 7.38] | 6.46 [5.56, 7.38] |
| hard 6m | HNW | 18,782 | 1,120 | 5.96 [5.64, 6.30] | 6.00 [5.60, 6.46] | 6.00 [5.60, 6.46] |
| hard 6m | UHNW | 1,095 | 80 | 7.31 [5.84, 8.77] | 7.17 [5.07, 9.61] | 7.17 [5.07, 9.61] |
| soft 3m | Total | 19,877 | 1,756 | 8.83 [8.44, 9.23] | 9.64 [8.51, 10.91] | 3.86 [3.42, 4.38] |
| soft 3m | HNW | 18,782 | 1,651 | 8.79 [8.40, 9.19] | 8.95 [8.41, 9.53] | 3.53 [3.29, 3.76] |
| soft 3m | UHNW | 1,095 | 105 | 9.59 [7.85, 11.51] | 10.73 [7.90, 14.16] | 4.37 [3.16, 5.76] |
| unión | Total | 19,877 | 2,956 | 14.87 [14.37, 15.39] | 16.10 [14.58, 17.61] | 10.32 [9.33, 11.30] |
| unión | HNW | 18,782 | 2,771 | 14.75 [14.28, 15.26] | 14.96 [14.28, 15.63] | 9.54 [9.08, 10.01] |
| unión | UHNW | 1,095 | 185 | 16.90 [14.84, 19.13] | 17.90 [14.65, 21.80] | 11.55 [9.29, 14.30] |

![Churn por hogares vs por valor](outputs/figures/01_churn_rates.png)

Concentración del valor perdido [DATA-SINT] (se reporta, no se corrige):

| Target | Eventos | Valor perdido $M | Top 1 hogar % | Top 10 hogares % | Top 5% de eventos % | Mediana por evento $M |
|:--|--:|--:|--:|--:|--:|--:|
| hard 6m | 1,200 | 13,323 | 4.96 | 16.47 | 38.24 | 4.84 |
| soft 3m | 1,756 | 7,963 | 4.33 | 16.93 | 42.06 | 1.90 |
| unión | 2,956 | 21,286 | 3.10 | 12.02 | 42.23 | 2.88 |

- UHNW = 5.5% de los hogares y 39.0% del RV ($80.4B de $206.3B): pesa casi 7 veces más por valor que por hogares.
- Hard es pérdida total (`value_lost_6m` = RV en el 100% de los eventos) → (i) = (ii). Soft pierde en mediana 39.8%
  del RV (p10 23.9%, p90 56.3%).
- El IC del churn por valor hard (±0.9 pp) es 2.5 veces más ancho que el de hogares (±0.36 pp): un solo hogar UHNW de
  $661M explica 4.96% del valor perdido. Por eso la validación por valor (paso 13) llevará IC.

**QC** · 15 PASS · 0 WARN · 0 FAIL
- hard ∩ soft = 0; `value_lost_6m` = 0 en el 100% de los no-eventos; `value_lost_6m` ≤ RV en el 100%.
- Consistencia aritmética: tasa de cartera = Σ share × tasa por segmento (hogares y valor) para los 3 targets;
  eventos HNW + UHNW = total; unión = hard + soft en eventos y en valor perdido (diferencias < 1e-9).

**Decisiones y alternativas descartadas** · D1.1–D1.3
- Base de valor RV, no `aum` (missing estructural en 14.4%).
- IC por bootstrap sin winsorizar ni recortar RV (D0.5).

---

## 2. Diccionario de datos

**Objetivo**
- Clasificar las 62 columnas y decidir cuáles son predictores elegibles antes de ver su relación con el target.

**Por qué**
- Fijar dirección esperada y elegibilidad *a priori* permite detectar después señales con signo contrario al
  negocio y evita que outcomes o compuestos se cuelen como predictores.

**Método**
- Por columna: rol, dimensión, tipo, ventana, unidad, tipo de feature (nivel / frecuencia / recencia / magnitud /
  tendencia / aceleración / persistencia / cambio vs baseline), % missing, condición de missing estructural,
  dirección esperada (+ más churn, − menos churn, ? sin hipótesis) y elegibilidad.
- Descripciones y unidades del diccionario del generador; clasificación propia en `src/dictionary.py`.

**Código** · `src/02_dictionary.py`, `src/dictionary.py`

**Salida** · `outputs/tables/02_data_dictionary.csv` (tabla completa, 62 filas), `02_dictionary_summary.csv`

| Rol | Dimensión | Columnas | Elegibles |
|:--|:--|--:|--:|
| identificador | — | 2 | 0 |
| estructura | `segment`, `has_*` ×8, `age_primary`, `tenure_years`, `history_months` | 12 | 12 |
| nivel patrimonial | `relationship_value`, `deposit_balance`, `aum`, `recurring_income_monthly`, `share_of_wallet` | 5 | 5 |
| señal | salida de activos | 7 | 7 |
| señal | deterioro de saldos | 3 | 3 |
| señal | externalización / competencia | 9 | 9 |
| señal | ingresos recurrentes | 5 | 5 |
| señal | pérdida de productos | 4 | 4 |
| señal | fricción de servicio | 4 | 4 |
| señal | relación con banquero | 4 | 4 |
| señal | rendimiento | 1 | 1 |
| compuesto | `multi_signal_flag`, `multi_signal_count` | 2 | 0 |
| outcome | `hard_churn_6m`, `soft_churn_3m`, `value_lost_6m`, `churn_excluded` | 4 | 0 |

- 54 elegibles, 8 no elegibles. Las 37 señales tienen dirección esperada: 28 "+", 9 "−".
- Revisión regulatoria pendiente (paso 10): `age_primary` (fair lending / UDAAP) y `bureau_new_mortgage_elsewhere`
  (FCRA, propósito permisible).
- Ventanas presentes: 30d, 45d, 60d, 90d, 180d, 6m, 12m, baseline 6m y nivel en T0.

**QC** · 3 PASS · 0 WARN · 0 FAIL
- Las 62 columnas clasificadas, sin faltantes ni sobrantes; ninguna prohibida es elegible; toda señal tiene dirección.

**Decisiones y alternativas descartadas** · D2.1–D2.2
- Dirección "?" en nivel patrimonial, `segment`, edad e historia: sin hipótesis defendible, decide el binning.

---

## 3. Calidad de datos

**Objetivo**
- Perfilar cada variable, explicar todo el missing, detectar valores imposibles e inconsistencias lógicas y
  clasificar los outliers de valor, sin eliminar ni recortar nada.

**Por qué**
- El WoE hereda cualquier defecto de la variable. Un missing mal clasificado ("no aplica" vs "sin dato") mezcla
  poblaciones con riesgos distintos en un mismo bin.

**Método**
- Perfil: % missing, media, desviación, p1/p5/p25/p50/p75/p95/p99, mín, máx de las 50 numéricas.
- Missing: por variable, NaN estructural (`has_*` = False), valores donde no aplica, y NaN restante separado por
  `history_months` < 24 vs = 24. El NaN restante con historia completa se atribuye a la regla documentada del
  generador (patrón no detectado; saldo base < $10k; condición operativa).
- Rangos duros (imposibles): fracciones en [0, 1], cambios ≥ −100%, montos y conteos ≥ 0, flags ∈ {0, 1}, conteos
  enteros, edad 18–110, historia 0–24. Rangos blandos (plausibles a revisar): ratios > 100% del saldo, etc.
- Lógica: identidad RV = AUM + depósitos, regla de segmento, historia vs antigüedad, SOW previo ∈ [0, 1], coherencia
  monto ↔ porcentaje, flags de ingreso.
- Outliers de RV: error (rompe identidad o segmento) / extraordinario (log₁₀ RV > Q3 + 3·IQR) / real.

**Código** · `src/03_quality.py`

**Salida** · `outputs/tables/03_numeric_profile.csv`, `03_missing_explained.csv`, `03_range_checks.csv`,
`03_logic_checks.csv`, `03_history_tenure_diff.csv`, `03_value_outliers.csv`, `03_top15_households.csv`

Missing explicado [DATA-SINT] (resumen; tabla completa en `03_missing_explained.csv`):

| Causa | Variables | % missing |
|:--|:--|--:|
| Estructural puro | `aum`, `trustee_change_flag` | 14.4 / 68.1 |
| Estructural + historia corta | `aum_outflow_*`, `investment_redemption_pct`, `positions_liquidated_pct`, `aum_vs_baseline_pct`, `cash_pct_of_portfolio_chg`, `return_vs_benchmark` | 14.5–41.0 |
| Estructural + historia corta + patrón no detectado | `salary_*`, `pension_*`, `business_payroll_*`, `recurring_deposit_*` | 7.4–73.9 |
| Operativa (no observable en la base) | `fixed_income_maturity_not_reinvested`, `relationship_dissatisfaction_flag`, `meetings_cancelled_by_client`, `client_reply_rate`, `bureau_new_mortgage_elsewhere` | 5.0–73.9 |
| Solo historia corta (< 24 meses) | 12 señales de transferencias, cierres, banquero y SOW | 0.1–3.5 |
| Historia corta + saldo base < $10k | `deposit_balance_change_pct_90d`, `deposit_balance_vs_6m_avg_pct`, `net_deposit_flow_pct_90d` | 0.3–0.8 |

Inconsistencias [DATA-SINT] (documentadas; no se corrige la fuente, D3.3):

| Control | Hogares | Tratamiento |
|:--|--:|:--|
| `pension_deposit_stopped_flag` con valor sin `has_pension_stream` | 134 | recodificar a "no aplica" (paso 5) |
| `salary_deposit_stopped_flag` NaN con `has_payroll_stream` | 232 | "sin dato" (patrón no detectado) |
| `history_months` ≠ min(24, ⌊tenure·12⌋) | 61 | todos ±1 mes (52 −1, 9 +1): redondeo, se ignora |
| `history_months` = 0 | 5 | se conservan; señales de ventana = "sin dato" |
| `salary_…stopped` = 1 con `recurring_…stopped` = 0 | 11 | coherente con umbral ≥ 10% del ingreso de #4 |
| `contact_gap_ratio` = −0.0 | 561 | cosmético (= 0) |
| RV = AUM + depósitos · segmento vs $30M · SOW previo ∈ [0, 1] · monto ↔ % | 0 | — |
| Valores imposibles (rangos duros, flags, enteros) | 0 | — |

Extremos plausibles [DATA-SINT]: transferencias 60d > 100% del saldo promedio (628 hogares, 3.1%), salida neta de
depósitos > 100% (479), `outflow_vs_baseline_pct` > 11× la base (428; máx 6,390×, por el piso de $10k en la base),
a competidores > 100% (373), salida de AUM > 100% (168). Se conservan; el binning los agrupa en el bin extremo.

Outliers de `relationship_value` [DATA-SINT]:

| Clase | Hogares | RV total $M | Rango $M | Eventos hard | % del RV |
|:--|--:|--:|:--|--:|--:|
| error | 0 | 0 | — | 0 | 0.0 |
| extraordinario (RV > $712M) | 2 | 1,630.7 | 726.7–904.0 | 0 | 0.8 |
| real | 19,998 | 206,008.1 | 1.0–679.5 | 1,200 | 99.2 |

![Distribución de relationship_value](outputs/figures/03_relationship_value.png)

- Ningún outlier es error. El hogar de $904M tiene soft churn ($345M perdidos); el hard churner más grande
  ($661M) queda justo bajo la cerca. Todos se conservan sin capping (D3.1).

**QC** · 14 PASS · 6 WARN · 0 FAIL
- Gate > 90% missing no estructural: ninguna variable (máx. 73.9%, operativo). Gate de inconsistencia lógica:
  6 WARN documentados arriba; por instrucción del usuario (D0.5) se sigue con los datos tal cual.
- Todo el missing queda explicado por una causa: estructural, historia corta, operativa, patrón no detectado o saldo base.

**Decisiones y alternativas descartadas** · D3.1–D3.3
- Sin capping en ninguna variable (el pre-binning por cuantiles lo hace irrelevante; D0.5 para RV). Descartados
  winsorizar p1/p99 y eliminar outliers.
- "No aplica" y "sin dato" como categorías de missing distintas en el binning.
