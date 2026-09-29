# Paso 8 · Equidad y uso responsable

## Objetivo
- Confirmar que el ML no reintroduce la edad por la puerta de atrás y que marca a los grupos de edad en proporción a
  su churn real. Solo diagnóstico: la edad nunca se usa para puntuar.

## Método
- Proxy: AUC de separar el tercil de mayor edad del de menor edad con las 12 variables (GBM, CV 5). Lectura [DEF-default
  D8.1]: < 0.60 sin proxy relevante; 0.60–0.70 débil; > 0.70 revisar.
- Marcado por tercil de edad (dev): % en Crítico y Crítico+Alto vs churn observado, EBM y M1.

## Código
- `src/step08_fairness.py` · `tests/test_step08.py` · `step08_*.csv`.

## Resultados

### Prueba de proxy [DATA]
| prueba                                                      |   hogares |   AUC (CV 5) | lectura     |
|:------------------------------------------------------------|----------:|-------------:|:------------|
| predecir tercil mayor vs menor de edad con las 12 variables |      8700 |        0.633 | proxy débil |

### Marcado por tercil de edad (dev) [DATA]
| tercil edad   | edad   |   hogares |   tasa churn B % |   % Crítico EBM |   % Crítico+Alto EBM |   ratio (Crítico+Alto / churn) EBM |   % Crítico M1 |   % Crítico+Alto M1 |   ratio (Crítico+Alto / churn) M1 |
|:--------------|:-------|----------:|-----------------:|----------------:|---------------------:|-----------------------------------:|---------------:|--------------------:|----------------------------------:|
| T1 (menor)    | 28–55  |      4602 |            13.62 |            4.22 |                26.10 |                               1.92 |           4.15 |               27.64 |                              2.03 |
| T2            | 56–66  |      4782 |            13.72 |            4.04 |                25.70 |                               1.87 |           3.89 |               28.19 |                              2.05 |
| T3 (mayor)    | 67–94  |      4098 |            14.35 |            3.90 |                25.77 |                               1.80 |           4.08 |               27.04 |                              1.88 |

- Dispersión del ratio marcado / churn entre terciles (máx / mín): EBM 1.07, M1 1.09 [DATA].

## Tests
- `tests/test_step08.py` (ver pytest).

## Decisiones y preguntas abiertas
- D8.1 en `reports/decision_log.md`.
