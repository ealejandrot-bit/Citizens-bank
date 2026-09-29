# Paso 11 · Arquetipos y acción

## Objetivo
- Ver, por tipo de cliente que se va, si el ML detecta mejor que el M1 (en especial el "desgaste silencioso").

## Método
- Arquetipos del M1 (K = 3) asignados sin reajuste a los 803 eventos B de val; archivos del M1 leídos en solo
  lectura (sha256 verificado antes y después). A-lite en el subconjunto justo.

## Código
- `src/step11_archetypes.py` · `tests/test_step11.py` · `step11_*.csv`.

## Resultados

### Detección por arquetipo (eventos B de val) [DATA]
| arquetipo                  |   eventos val |   % eventos |   % en Crítico · M1 |   % en Crítico · EBM |   % en Crítico+Alto · M1 |   % en Crítico+Alto · EBM |   % en Estable · M1 |   % en Estable · EBM |   p media % · M1 |   p media % · EBM |   eventos justos (A-lite) |   % en Crítico+Alto · A-lite (justo) |   % en Crítico+Alto · M1 (justo) |   % en Crítico+Alto · EBM (justo) |   Δ Crítico+Alto EBM − M1 (pp) |
|:---------------------------|--------------:|------------:|--------------------:|---------------------:|-------------------------:|--------------------------:|--------------------:|---------------------:|-----------------:|------------------:|--------------------------:|-------------------------------------:|---------------------------------:|----------------------------------:|-------------------------------:|
| relación desatendida       |           266 |        33.1 |                 6.4 |                  4.5 |                     54.9 |                      50.0 |                 0.0 |                  0.0 |             19.5 |              19.8 |                        69 |                                 23.2 |                             63.8 |                              49.3 |                           -4.9 |
| salida activa a competidor |           155 |        19.3 |                72.3 |                 73.5 |                     99.4 |                      96.8 |                 0.0 |                  0.0 |             47.7 |              57.1 |                        41 |                                 95.1 |                            100.0 |                              95.1 |                           -2.6 |
| desgaste silencioso        |           382 |        47.6 |                 2.6 |                  1.0 |                     33.2 |                      30.6 |                24.9 |                 20.7 |             13.0 |              12.6 |                       128 |                                 10.9 |                             27.3 |                              24.2 |                           -2.6 |

- Verificación: % eventos suma 100.0% [DATA].
- Desgaste silencioso: Crítico+Alto M1 33.2% vs EBM 30.6%; en Estable M1 24.9% vs EBM 20.7% [DATA].

### Acción por arquetipo
| arquetipo                  | acción (playbook M1)                                                                            | qué cambia con el ML [DATA]                                                                                                                                                     |
|:---------------------------|:------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| relación desatendida       | reactivar la relación: reunión del banquero y plan de contacto                                  | el EBM marca 4.9 pp menos de estos eventos en Crítico+Alto que el M1 (el EBM marca 25.6% de hogares en Crítico+Alto vs 28.0% del M1): sin ventaja; se mantiene la acción del M1 |
| salida activa a competidor | retención inmediata con líder + banquero                                                        | el EBM marca 2.6 pp menos de estos eventos en Crítico+Alto que el M1 (el EBM marca 25.6% de hogares en Crítico+Alto vs 28.0% del M1): sin ventaja; se mantiene la acción del M1 |
| desgaste silencioso        | revisión proactiva ligera de portafolio y rendimiento; punto ciego común a los modelos (L6, L7) | el EBM marca 2.6 pp menos de estos eventos en Crítico+Alto que el M1 (el EBM marca 25.6% de hogares en Crítico+Alto vs 28.0% del M1): sin ventaja; se mantiene la acción del M1 |

## Tests
- `tests/test_step11.py` (ver pytest).

## Decisiones y preguntas abiertas
- D11.1 en `reports/decision_log.md`.
