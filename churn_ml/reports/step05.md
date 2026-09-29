# Paso 5 · Calibración

## Objetivo
- Que la probabilidad publicada del ML coincida con la tasa observada, sin usar el holdout.

## Método
- OOF por hogar = promedio de 5 predicciones fuera de fold (CV 5×5). Platt vs isotónica en un 2º nivel de 5 folds,
  IC bootstrap 95%; isotónica solo si ΔBrier < 0 con IC (D5.1). Aceptación 0.8 ≤ b ≤ 1.2.

## Código
- `src/step05_calibration.py` · `tests/test_step05.py` · `step05_*.csv`, `outputs/model/step05_calibrators.pkl`.

## Resultados

### Métodos [DATA]
| modelo   | método                   |   Brier |   ECE (pp) |   media p % |   tasa % |
|:---------|:-------------------------|--------:|-----------:|------------:|---------:|
| EBM      | sin calibrar (OOF)       |  0.1058 |     0.7012 |     13.8798 |  13.8778 |
| EBM      | Platt (2º nivel OOF)     |  0.1058 |     0.6166 |     13.8760 |  13.8778 |
| EBM      | isotónica (2º nivel OOF) |  0.1059 |     0.6607 |     13.8727 |  13.8778 |
| XGBoost  | sin calibrar (OOF)       |  0.1062 |     1.2978 |     13.3642 |  13.8778 |
| XGBoost  | Platt (2º nivel OOF)     |  0.1059 |     0.6638 |     13.8767 |  13.8778 |
| XGBoost  | isotónica (2º nivel OOF) |  0.1060 |     0.8590 |     13.8757 |  13.8778 |

### Platt e isotónica vs Platt [DATA]
| modelo   |   ΔBrier (iso − Platt) |   IC95 inf |   IC95 sup |    ΔECE |      a |      b |   b IC95 inf |   b IC95 sup | 0.8 ≤ b ≤ 1.2   | método elegido   |
|:---------|-----------------------:|-----------:|-----------:|--------:|-------:|-------:|-------------:|-------------:|:----------------|:-----------------|
| EBM      |                 0.0001 |    -0.0001 |     0.0003 | -0.0005 | 0.0503 | 1.0301 |       0.9687 |       1.0916 | True            | Platt            |
| XGBoost  |                 0.0002 |    -0.0001 |     0.0004 |  0.0003 | 0.3081 | 1.1508 |       1.0818 |       1.2197 | True            | Platt            |

![Calibración](../outputs/figs/step05_calibration.png)

### Por segmento (OOF calibrado) [DATA]
| modelo   | segmento   |   hogares |   eventos |   p media % |   tasa % |
|:---------|:-----------|----------:|----------:|------------:|---------:|
| EBM      | HNW        |     12731 |      1749 |       13.86 |    13.74 |
| EBM      | UHNW       |       751 |       122 |       14.15 |    16.25 |
| XGBoost  | HNW        |     12731 |      1749 |       13.91 |    13.74 |
| XGBoost  | UHNW       |       751 |       122 |       13.42 |    16.25 |

### Por quintil de RV (OOF calibrado) [DATA]
| modelo   | quintil RV   |   hogares |   p media % |   tasa % |   Σ p·RV / Σ RV eventos |
|:---------|:-------------|----------:|------------:|---------:|------------------------:|
| EBM      | Q1 (menor)   |      2697 |      13.935 |   14.164 |                   0.985 |
| EBM      | Q2           |      2696 |      13.489 |   13.501 |                   0.995 |
| EBM      | Q3           |      2696 |      14.216 |   13.613 |                   1.045 |
| EBM      | Q4           |      2696 |      13.747 |   13.316 |                   1.040 |
| EBM      | Q5 (mayor)   |      2697 |      14.001 |   14.794 |                   0.851 |
| XGBoost  | Q1 (menor)   |      2697 |      13.999 |   14.164 |                   0.989 |
| XGBoost  | Q2           |      2696 |      13.582 |   13.501 |                   1.001 |
| XGBoost  | Q3           |      2696 |      14.202 |   13.613 |                   1.044 |
| XGBoost  | Q4           |      2696 |      13.832 |   13.316 |                   1.046 |
| XGBoost  | Q5 (mayor)   |      2697 |      13.774 |   14.794 |                   0.823 |

- Referencia M1 (G3-2): en validación el M1 subestimaba el quintil superior (Σ p·RV / Σ RV eventos = 0.85) [DATA].

## Tests
- `tests/test_step05.py` (ver pytest).

## Decisiones y preguntas abiertas
- D5.1 en `reports/decision_log.md`.
