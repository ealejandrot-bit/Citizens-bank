# Paso 2 · Diccionario de datos

## Objetivo
- Clasificar las 62 columnas (tipo, unidad, missing, bloque, dirección esperada, uso) antes de mirar su relación con el target.

## Método
- Metadatos de negocio fijados a priori en `src/step02_dictionary.py`; % missing, rango y gatillo estructural calculados del archivo.
- Uso: predictor · prohibido (resultados, id, fecha) · auxiliar (compuestos [DEF-default I-3]; `value_lost_6m` [DEF-default I-10]).

## Código
- `src/step02_dictionary.py` · `tests/test_step02.py` · `outputs/tables/step02_dictionary.csv` (tabla completa).

## Resultados

### Columnas por bloque [DATA]
| bloque        |   columnas |   predictores |
|:--------------|-----------:|--------------:|
| compuesto     |          2 |             0 |
| economía      |          1 |             1 |
| estructural   |          5 |             3 |
| patrimonial   |          7 |             7 |
| producto      |         12 |            12 |
| relación      |          5 |             5 |
| resultado     |          4 |             0 |
| servicio      |          4 |             4 |
| transaccional |         22 |            22 |
| digital       |          0 |             0 |
| vida          |          0 |             0 |

- Verificación: 62 columnas = 62 [DATA].
- Dimensiones ausentes: **digital** (sin logins ni sesiones) y **vida** (sin eventos de vida; `salary_…` /
  `pension_deposit_stopped_flag` son proxies transaccionales, no eventos) → limitación L6.

### Uso [DATA]
| uso                                                            |   columnas |
|:---------------------------------------------------------------|-----------:|
| predictor                                                      |         54 |
| prohibido                                                      |          5 |
| auxiliar                                                       |          2 |
| auxiliar (solo churn por valor y calibración; nunca predictor) |          1 |

### Dirección esperada de los predictores (a confirmar en G1)
| bloque        | dirección esperada   |   predictores |
|:--------------|:---------------------|--------------:|
| economía      | −                    |             1 |
| estructural   | ?                    |             3 |
| patrimonial   | ?                    |             4 |
| patrimonial   | −                    |             3 |
| producto      | +                    |             4 |
| producto      | −                    |             8 |
| relación      | +                    |             3 |
| relación      | −                    |             2 |
| servicio      | +                    |             4 |
| transaccional | +                    |            17 |
| transaccional | −                    |             5 |

- Sin hipótesis ("?"): `segment`, `relationship_value`, `deposit_balance`, `aum`, `age_primary`, `history_months`,
  `recurring_income_monthly`. En GBM quedan sin restricción monótona salvo que el usuario fije el signo en G1.
- `age_primary` es predictor candidato con revisión de fair lending; `bureau_new_mortgage_elsewhere` con revisión FCRA
  (propósito permisible): se decide en el paso 10.

## Tests
- `tests/test_step02.py` en verde; suite completa `python -m pytest -q`: 30 passed.

## Decisiones y preguntas abiertas
- D2.1–D2.2 en `reports/decision_log.md`; confirmación de signos en G1.
