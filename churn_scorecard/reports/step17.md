# Paso 17 · KPIs, monitoreo, gobernanza, limitaciones

## Objetivo
- Dejar el modelo operable y auditable: qué se mide, cuándo se actúa, quién decide y qué no puede afirmar.

## Método
- Línea base de KPIs = resultados de validación (pasos 13–15); umbrales del SPEC y de las decisiones G3 [DEF].
- `reports/model_document.md` armado desde las tablas generadas, con índice de todos los pasos.

## Código
- `src/step17_governance.py` · `tests/test_step17.py` · `step17_*.csv`, `reports/model_document.md`.

## Resultados

### KPIs
| dimensión                  | KPI                                              | línea base [DATA]            | umbral / acción [DEF]                                                          | frecuencia   |
|:---------------------------|:-------------------------------------------------|:-----------------------------|:-------------------------------------------------------------------------------|:-------------|
| Discriminación             | Gini (val)                                       | 0.390                        | caída > 15% relativo vs línea base ⟹ redesarrollo                              | mensual      |
| Discriminación             | PR-AUC (val)                                     | 0.328                        | seguimiento                                                                    | mensual      |
| Calibración                | pendiente Platt b                                | 0.854                        | fuera de 0.8–1.2 dos ciclos ⟹ recalibración                                    | mensual      |
| Calibración                | media p calibrada vs tasa observada              | 13.90% vs 13.90%             | brecha > 1 pp dos ciclos ⟹ recalibración                                       | mensual      |
| Estabilidad                | PSI del score                                    | 0.0034                       | 0.10–0.25 vigilar; > 0.25 sostenido ⟹ redesarrollo                             | mensual      |
| Estabilidad                | PSI de variables (máx.)                          | 0.0027                       | > 0.25 en una variable ⟹ revisar su fuente                                     | mensual      |
| Tramos                     | tasa Crítico / Alto / Vigilancia / Estable (val) | 55.6% / 21.1% / 11.1% / 5.8% | pérdida de monotonía o lift Crítico/Estable < 5x ⟹ revisar cortes              | trimestral   |
| Operación                  | precisión en Crítico (val)                       | 55.6%                        | seguimiento; FP por evento capturado 0.80                                      | mensual      |
| Operación                  | captura top 10% (val)                            | 27.9% eventos · 25.8% RV     | seguimiento                                                                    | mensual      |
| Valor (G3-2)               | Σ p·RV / Σ RV de eventos, quintil superior de RV | 0.85                         | < 0.85 dos ciclos ⟹ probar ajuste por log_rv                                   | trimestral   |
| Segmento (G3-3)            | UHNW en Alto: observada vs esperada              | 31.6% vs 19.4% (24 eventos)  | revisión prioritaria del banquero; recalibrar UHNW si ≥ 100 eventos acumulados | trimestral   |
| Efecto de la acción (G3-4) | churn tratados vs control en Alto                | control 12.5% = 595 hogares  | efecto mínimo detectable 4.9 pp                                                | a 6 meses    |

### Disparadores
| disparador            | condición [DEF SPEC / G3]                                                | acción                                                                          |
|:----------------------|:-------------------------------------------------------------------------|:--------------------------------------------------------------------------------|
| Recalibración         | b fuera de 0.8–1.2 en dos ciclos, o media p vs tasa > 1 pp en dos ciclos | re-estimar Platt con el último snapshot con outcome; cortes de score sin cambio |
| Redesarrollo          | PSI del score > 0.25 sostenido, o Gini −15% relativo vs línea base       | repetir pasos 5–14 con nuevos datos (y OOT si ya hay 2+ snapshots)              |
| Revisión de variable  | PSI > 0.25 en una variable o cambio de definición del proveedor          | revisar la fuente; bin neutral temporal si la variable se cae                   |
| Revisión de overrides | precisión de una regla < 12% en dos ciclos                               | eliminar la regla                                                               |
| Cola de valor         | quintil superior de RV con Σ p·RV / Σ RV de eventos < 0.85 dos ciclos    | probar interacción con log_rv (paso 14)                                         |

### Gobernanza
| rol                      | responsable (propuesto)          | responsabilidad                                                                                       |
|:-------------------------|:---------------------------------|:------------------------------------------------------------------------------------------------------|
| Dueño del modelo         | Wealth / banca privada (negocio) | aprueba cortes, overrides y playbook                                                                  |
| Desarrollo               | equipo de modelos                | código, tablas, reportes, recalibración                                                               |
| Validación independiente | MRM (SR 11-7 o equivalente)      | revisa este documento antes del uso; revalidación anual                                               |
| Monitoreo                | equipo de modelos + MRM          | tablero mensual de KPIs y disparadores                                                                |
| Cumplimiento             | legal / fair lending             | confirma exclusión de edad y buró (G1-3) y uso de datos                                               |
| Cambios                  | comité de modelos                | cambios de variables o cortes = cambio material; recalibración Platt = cambio no material documentado |

### Limitaciones
| id   | limitación                                                                                                                              |
|:-----|:----------------------------------------------------------------------------------------------------------------------------------------|
| L1   | Sin OOT ni cohortes ni PSI temporal: un solo snapshot 2025-12-31. La validación es una partición aleatoria del mismo periodo.           |
| L2   | Señales pre-ingenierizadas por el proveedor sin timestamps auditables; se asume que todas son as-of T0.                                 |
| L3   | `multi_signal_count` / `_flag` sin regla documentada: fuera del campeón; solo en el challenger de referencia.                           |
| L4   | Dataset sintético: no representa una cartera real; nada de lo estimado se presenta como resultado de un banco.                          |
| L5   | UHNW sub-representado: 53 eventos B en val; solo métricas globales y lectura descriptiva por tramo.                                     |
| L6   | Sin dimensión digital ni eventos de vida (fallecimiento, liquidity event): no hay overrides por esas causas.                            |
| L7   | Causalidad y efecto de la propia intervención no identificables: arquetipos descriptivos; efecto solo medible con el control aleatorio. |
| L8   | Pesos de clase balanceados con intercepto corregido; la probabilidad publicada depende de la calibración Platt sobre val.               |

## Tests
- `tests/test_step17.py` (ver pytest).

## Decisiones y preguntas abiertas
- D17.1 en `reports/decision_log.md`; preguntas G4 en `reports/gate_4.md`.
