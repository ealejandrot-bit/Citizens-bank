# Churn Propensity Scorecard · Documento de modelo

Modelo 1 de 3 (scoring estadístico) · Client Pulse · Citizens Private Bank · base **sintética**.
Toda cifra es [DATA-SINT]: sale de los datos, pero la base es sintética; no es resultado de un banco real.

## Índice

0. [Setup e inventario](#0-setup-e-inventario)

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

**Parámetros por confirmar con el usuario** (defaults activos hasta respuesta)
- (a) Target primario: `hard_churn_6m`.
- (b) Capacidad operativa: Crítico = top 3% por probabilidad (~600 hogares; ~180 en holdout).
