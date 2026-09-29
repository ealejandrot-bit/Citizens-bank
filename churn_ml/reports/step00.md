# Paso 0 · Herencia y verificación

## Objetivo
- Partir exactamente de los mismos datos, target, split y holdout que el Modelo 1, sin modificar nada del Modelo 1.

## Método
- Copia con sha256 de 16 archivos de `churn_scorecard/` a `data/inherited/` (nunca se mueven ni se reescriben).
- Huella sha256 de 130 archivos de modelos anteriores (`churn_scorecard/outputs/model/` y `scorecard/outputs/`);
  un test verifica en cada corrida que no cambiaron (pedido del usuario: se usan para comparar).
- Verificación de los hechos de la sección B del SPEC en los datos heredados y en el raw.

## Código
- `src/step00_inherit.py` · `tests/test_step00.py` · `step00_inherited.csv`, `step00_previous_models.csv`, `step00_facts.csv`,
  `step00_candidates.csv`.

## Resultados

### Hechos verificados [DATA]
| hecho                                     | esperado (SPEC B)        | observado [DATA]            | coincide   |
|:------------------------------------------|:-------------------------|:----------------------------|:-----------|
| Filas / columnas raw                      | 20,000 / 62              | 20,000 / 62                 | True       |
| Target B: hogares / eventos / tasa        | 19,261 / 2,674 / 13.88%  | 19,261 / 2,674 / 13.88%     | True       |
| dev: hogares / B hogares / B eventos      | 13,631 / 13,482 / 1,871  | 13,631 / 13,482 / 1,871     | True       |
| val: hogares / B hogares / B eventos      | 5,842 / 5,779 / 803      | 5,842 / 5,779 / 803         | True       |
| dev ∩ val                                 | 0 hogares                | 0                           | True       |
| Folds CV 5×5 en dev                       | cv_r1..cv_r5 con 5 folds | 5, 5, 5, 5, 5               | True       |
| Campeón M1 · CV anidada Gini / PR-AUC     | 0.429 / 0.344            | 0.429 / 0.344               | True       |
| Campeón M1 · val Gini / PR-AUC            | 0.390 / 0.328            | 0.390 / 0.328               | True       |
| Missing estructural aum ⟺ sin inversiones | exacto                   | exacto                      | True       |
| Candidatas sin resultado / edad / buró    | 0 prohibidas             | 70 candidatas, 0 prohibidas | True       |
| Copias heredadas idénticas                | 16 de 16                 | 16 de 16                    | True       |

### Archivos heredados [DATA]
| origen (churn_scorecard/)                | destino (data/inherited/)   |   bytes | copia idéntica   |
|:-----------------------------------------|:----------------------------|--------:|:-----------------|
| data/processed/features.parquet          | features.parquet            | 5317389 | True             |
| data/processed/dev.parquet               | dev.parquet                 | 2903988 | True             |
| data/processed/val.parquet               | val.parquet                 | 1247082 | True             |
| data/processed/step01_population.parquet | step01_population.parquet   |  163033 | True             |
| data/processed/step07_clusters.parquet   | step07_clusters.parquet     |  139711 | True             |
| data/processed/step11A_oof.parquet       | m1_champion_oof_r1.parquet  |  188527 | True             |
| data/processed/step12_scores.parquet     | m1_step12_scores.parquet    |  210660 | True             |
| outputs/scores/household_scores.csv      | m1_household_scores.csv     | 3743238 | True             |
| outputs/tables/step05_features.csv       | step05_features.csv         |    5985 | True             |
| outputs/tables/step06_univariate_B.csv   | step06_univariate_B.csv     |   14142 | True             |
| outputs/tables/step08_spearman.csv       | step08_spearman.csv         |   37575 | True             |
| outputs/tables/step09_iv_summary.csv     | step09_iv_summary.csv       |   10377 | True             |
| outputs/tables/step11A_cv_folds.csv      | m1_step11A_cv_folds.csv     |    4215 | True             |
| outputs/tables/step13_global.csv         | m1_step13_global.csv        |     775 | True             |
| outputs/tables/step14_platt.csv          | m1_step14_platt.csv         |     148 | True             |
| outputs/model/MANIFEST.json              | m1_MANIFEST.json            |    1713 | True             |

### Modelos anteriores protegidos [DATA]
- 10 archivos de `churn_scorecard/outputs/model/` y 120 de `scorecard/outputs/`
  con su sha256 en `data/inherited/previous_models_sha256.json` (lista completa en `step00_previous_models.csv`).

### Candidatas [DATA]
- 70 variables: 67 de M1 + 2 compuestos (I-2) + `cluster`.

## Tests
- `tests/test_step00.py` (ver pytest).

## Decisiones y preguntas abiertas
- D0.1–D0.2 y respuestas G0 en `reports/decision_log.md`.
