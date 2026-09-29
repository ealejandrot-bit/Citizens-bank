# Gate 1 · Variables, selección y algoritmo (pasos 1–3)

## Tests
- `python -m pytest -q` → **11 passed** (pasos 00–03).

## Resumen del bloque [DATA]
- Paso 1: 70 candidatas → 62 (8 duplicados casi exactos; 0 constantes; 0 fuga).
- Paso 2: 12 variables sin compuestos (los compuestos no aportan: PR-AUC 0.3584 con y sin ellos).
- Paso 3 (CV 5×5): XGBoost 0.3630 y LightGBM 0.3645 empatados (≤ 1 sd) → XGBoost por ser más simple.

| modelo (mismos 5 folds r1) | PR-AUC | Gini | Brier | pendiente b | captura RV de eventos, decil 1 |
|:--|--:|--:|--:|--:|--:|
| campeón M1 (logística WoE) | 0.342 | 0.426 | 0.1074 | 0.93 | 0.269 |
| EBM monotónico | 0.365 | 0.429 | 0.1058 | 1.02 | 0.321 |
| XGBoost (elegido) | 0.362 | 0.429 | 0.1064 | 1.13 | 0.281 |
| LightGBM | 0.365 | 0.429 | 0.1060 | 1.04 | 0.312 |
| RF | 0.357 | 0.423 | 0.1075 | 1.10 | 0.309 |

- Los modelos ML separan igual que el M1 (Gini) pero encuentran más churners en la cima (PR-AUC +0.02).

## Decisiones del bloque
- D1.1, D2.1–D2.2, D3.1–D3.2 en `reports/decision_log.md`.

## Preguntas para el usuario (con default)

| # | Pregunta | Default |
|:--|:--|:--|
| G1-1 | EBM empata con los GBM en PR-AUC, calibra mejor y captura más valor en la cima, y es aditivo (cada variable suma puntos exactos, sin SHAP). ¿Pasa a ser el candidato principal en vez de XGBoost? | sí: EBM principal; XGBoost como segundo candidato hasta el paso 9 |
| G1-2 | ¿Se aceptan las 12 variables sin compuestos? | sí |
| G1-3 | La mejora esperada sobre el M1 (+0.02 de PR-AUC) está por debajo del umbral de reemplazo del SPEC (+0.03). ¿Se sigue igual hasta validar, con foco en uso conjunto (paso 10)? | sí |

Responde o escribe **"usa defaults"**. No avanzo al paso 4 hasta tu respuesta.
