# Paso 4 · Muestra

## Objetivo
- Separar desarrollo (70%) y validación (30%) y fijar las particiones de la CV repetida.

## Método
- Población: 19,473 hogares (A) = 19,261 (B) + 212 indeterminados [DATA]. Estratos: clase (hard / soft ≥ θ /
  indeterminado / no evento) × `segment`; `train_test_split` 70/30, SEED = 42 [DEF]. Una fila por household ⟹ no hay
  agrupación. Estratificar solo por B desbalanceaba A (6.22% vs 5.48%) y se corrigió (D4.1).
- CV: RepeatedStratifiedKFold 5 × 5 dentro de dev, mismos estratos (`cv_r1`–`cv_r5` en `dev.parquet`).
- Sin OOT ni cohortes: limitación **L1**.

## Código
- `src/step04_split.py` · `tests/test_step04.py` · `data/processed/dev.parquet`, `val.parquet`.

## Resultados

### Particiones [DATA]
| partición   | segmento   |   hogares (pobl. A) |   indeterminados B |   hogares B |   eventos B |   tasa B % |   eventos A |   tasa A % |   % UHNW |   % RV del total |
|:------------|:-----------|--------------------:|-------------------:|------------:|------------:|-----------:|------------:|-----------:|---------:|-----------------:|
| dev         | Total      |               13631 |                149 |       13482 |        1871 |      13.88 |         817 |       5.99 |     5.56 |            70.36 |
| dev         | HNW        |               12873 |                142 |       12731 |        1749 |      13.74 |         762 |       5.92 |     0.00 |            42.70 |
| dev         | UHNW       |                 758 |                  7 |         751 |         122 |      16.25 |          55 |       7.26 |   100.00 |            27.66 |
| val         | Total      |                5842 |                 63 |        5779 |         803 |      13.90 |         351 |       6.01 |     5.56 |            29.64 |
| val         | HNW        |                5517 |                 61 |        5456 |         750 |      13.75 |         327 |       5.93 |     0.00 |            18.09 |
| val         | UHNW       |                 325 |                  2 |         323 |          53 |      16.41 |          24 |       7.38 |   100.00 |            11.55 |

- Verificación: dev + val = 19,473 = 19,473 [DATA];
  eventos B 1871 + 803 = 2,674 = 2,674 [DATA];
  eventos A 817 + 351 = 1,168 [DATA].
- Tasa B dev vs val: 13.88% vs 13.90%; tasa A 5.99% vs
  6.01% [DATA]. La RV no se estratificó (colas reales, paso 3).
- Régimen (SPEC H, tabla 1): eventos B en dev = 1,871 > 300 ⟹ logística sobre WoE + challenger ML [DATA].
- UHNW en val: 53 eventos B y 24 eventos A [DATA] → métricas UHNW con IC anchos.

### Folds de la CV 5 × 5 en dev [DATA]
|   repetición | hogares por fold   | eventos B por fold   | eventos A por fold   | eventos B UHNW por fold   |
|-------------:|:-------------------|:---------------------|:---------------------|:--------------------------|
|            1 | 2726–2727          | 374–375              | 163–164              | 24–25                     |
|            2 | 2726–2727          | 374–375              | 163–164              | 24–25                     |
|            3 | 2726–2727          | 374–375              | 163–164              | 24–25                     |
|            4 | 2726–2727          | 374–375              | 163–164              | 24–25                     |
|            5 | 2726–2727          | 374–375              | 163–164              | 24–25                     |

## Tests
- `tests/test_step04.py` en verde; suite completa `python -m pytest -q`: 30 passed.

## Decisiones y preguntas abiertas
- D4.1 y limitación L1 en `reports/decision_log.md`; preguntas de G1 en `reports/gate_1.md`.
