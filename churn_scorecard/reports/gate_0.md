# Gate 0 · Verificación y definición del problema

## Tests
- `python -m pytest -q` → **16 passed** (`tests/test_step00.py`).

## Resumen del bloque
- Ficha verificada: 19 de 20 hechos coinciden tal cual; el 20º (RV vs AUM + depósitos) coincide literalmente pero no
  en interpretación (D0.2). Las cifras de la ficha usan los 19,877 elegibles (D0.4).
- Targets [DATA]: A 1,200 eventos (6.04% de 19,877); B 2,740
  (13.94% de 19,661; 216 indeterminados); C 2,956
  (14.87%); D 1,756 (8.83%).
- Churn rate [DATA]: A hogares 6.04% / RV bruto 6.46% / económico 6.46%; B hogares 13.94% / RV bruto 15.20% /
  económico 10.19%. UHNW: A 7.31% con 80 eventos; B 16.21% con 176 eventos.
- Anti-fuga: ninguna señal con AUC > 0.70; `multi_signal_count` IV 0.547 > 0.50 (compuesto, fuera del campeón; D0.5).
- Detalle: `reports/step00.md`.

## Preguntas para el usuario (con default)

| # | Pregunta | Default |
|:--|:--|:--|
| I-1 | Target: A (hard, 6.04% [DATA]) o B (hard ∪ soft con pérdida ≥ 25%, 13.94% [DATA]) | **B** principal, A sensibilidad |
| I-2 | Número de banqueros y capacidad (casos críticos abiertos por banquero) | sin dato → Crítico por lift / precisión / eventos + tabla de caseload para 40 / 100 / 200 banqueros |
| I-3 | Regla de construcción de `multi_signal_count` | desconocida → fuera del campeón, permitido en challenger |
| I-4 | Motivo de `churn_excluded` (123 [DATA]) | se excluyen; motivo desconocido documentado |
| I-5 | Definición de `relationship_value` y de `share_of_wallet` (denominador) | se usan como vienen; limitación documentada |
| I-6 | Escala S₀ = 600 @ 20:1, PDO = 40 | sí |
| I-7 | Libro completo con `segment` como variable, UHNW reportado aparte | sí (80 eventos UHNW [DATA] < 100) |
| I-8 | Excluir `tenure_years` < 1 (404 [DATA]) | excluir |
| I-9 | Bloque de supervivencia a tiempo discreto (3M soft → 6M hard) | no; solo descriptivo en paso 14 |
| I-10 | Usar `value_lost_6m` para calibración por valor | sí (resultado, nunca predictor) |
| G0-a | D0.2: en el archivo RV = AUM + depósitos al centavo. ¿Se trata RV como esa suma (y se documenta que la ficha estaba equivocada) o hay otra definición del proveedor? | tratar RV = AUM + depósitos; `relationship_value` y `aum` como par redundante en el paso 8; la definición queda en I-5 |

Responde cada pregunta o escribe **"usa defaults"**. No avanzo al paso 1 hasta tu respuesta.
