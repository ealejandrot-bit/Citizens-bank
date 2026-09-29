# Paso 12 · Monitoreo, gobierno, documento

## Objetivo
- Cerrar el Modelo 2 con su rol definido, KPIs, limitaciones, manifiesto y documento consolidado.

## Método
- Comparativa final desde las tablas de los pasos 9, 9b, 10 y 11; KPIs del EBM como challenger; manifiesto con sha256.

## Código
- `src/step12_governance.py` · `tests/test_step12.py` · `step12_*.csv`, `outputs/model/MANIFEST.json`, `reports/model_document.md`.

## Resultados

### Comparativa final [DATA]
|                                      | M1 · scorecard       | EBM (ML)                     | A-lite                    | XGBoost        |
|:-------------------------------------|:---------------------|:-----------------------------|:--------------------------|:---------------|
| Variables                            | 8                    | 12                           | 5                         | 12             |
| Forma                                | puntos por bin (WoE) | puntos por bin (EBM aditivo) | puntos por bin (WoE)      | árboles + SHAP |
| Gini · val completo (5,779)          | 0.390                | 0.406                        | — (70% en su desarrollo)  | 0.403          |
| PR-AUC · val completo                | 0.328                | 0.343                        | —                         | 0.344          |
| PR-AUC · subconjunto justo (1,737)   | 0.304                | 0.305                        | 0.262                     | 0.297          |
| Precisión top 5% · justo             | 49.4%                | 49.4%                        | 40.2%                     | 46.0%          |
| Criterios H-2 de reemplazo cumplidos | — (referencia)       | 6 de 8                       | no evaluado (otro target) | 4 de 8         |
| Razones por cliente estables (top 1) | 91.7% (M1 paso 11)   | 85.0%                        | —                         | 81.5%          |
| Rol recomendado                      | modelo operativo     | challenger en monitoreo      | comunicación ejecutiva    | retirado       |

### KPIs [DATA / DEF]
| dimensión                  | KPI                                                           | línea base [DATA]                   | umbral / acción [DEF]                                                        | frecuencia   |
|:---------------------------|:--------------------------------------------------------------|:------------------------------------|:-----------------------------------------------------------------------------|:-------------|
| Challenger vs operativo    | ΔPR-AUC EBM − M1 en cada snapshot con resultados              | +0.015 (val)                        | ≥ +0.03 sostenido en 2 ciclos ⟹ reabrir la decisión de reemplazo (tabla H-2) | semestral    |
| Discriminación EBM         | Gini                                                          | 0.406                               | caída > 15% relativo ⟹ redesarrollo                                          | mensual      |
| Calibración EBM            | pendiente Platt b en el último snapshot con resultados        | 0.878 (val)                         | fuera de 0.8–1.2 dos ciclos ⟹ recalibración                                  | mensual      |
| Crítico EBM (G3-3)         | esperada vs observada en Crítico                              | 61.3% vs 53.3%                      | re-calibrar con el próximo snapshot; publicar la tasa observada              | mensual      |
| Estabilidad                | PSI dev→val por tramo                                         | 0.0008                              | > 0.25 sostenido ⟹ redesarrollo                                              | mensual      |
| Deriva de explicación      | participación de |f_j| por variable                           | ver step07_importance_stability.csv | cambio de puesto de las 3 primeras ⟹ revisión                                | trimestral   |
| Prioridad (hallazgo D10.1) | captura de RV de eventos al 10%: tramo primero vs p×RV global | 48.9% vs 58.8% (M1)                 | decisión de negocio; medir con el control 12.5% del M1                       | trimestral   |

### Limitaciones
| id    | limitación                                                                                                                                                             |
|:------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| L1–L7 | Heredadas del M1: sin OOT; señales sin timestamps; compuestos sin regla; dataset sintético; UHNW pequeño; sin digital ni eventos de vida; causalidad no identificable. |
| L8    | El EBM sobrestima Crítico en val (61% esperado vs 53% observado); se corrige con el próximo snapshot (no se reusa val).                                                |
| L9    | A-lite se desarrolló con otro split y otro target: comparación justa solo en 1,737 hogares (IC amplios).                                                               |
| L10   | El paso 10 usa val después de validar: la elección entre reglas de uso conjunto tiene un leve optimismo (regla fijada antes, D10.1).                                   |
| L11   | La probabilidad del M1 fue calibrada sobre val (paso 14 del M1): su Brier y b en val le favorecen en la comparación.                                                   |

- Modelos anteriores intactos: sí (130 archivos verificados por sha256) [DATA].

## Tests
- `tests/test_step12.py` (ver pytest).

## Decisiones y preguntas abiertas
- D12.1 en `reports/decision_log.md`; preguntas G4 en `reports/gate_4.md`.
