# Gate 2 · Señales, selección y estimación (pasos 5–11)

## Tests
- `python -m pytest -q` → **60 passed** (pasos 00–11).

## Resumen del bloque [DATA]
- Paso 5: 15 derivadas; razón de missing (ok / no aplica / sin dato) en 34 variables; peer-relative por segmento × quintil de RV.
- Paso 6: 47 de 69 candidatas con señal; 0 sospechas de fuga con B; 0 signos contrarios a lo esperado.
- Paso 7: K = 4 clusters estructurales (ARI 0.869); sin diferencia de riesgo significativa (χ² p = 0.153).
- Paso 8: 58 pares con |ρ| > 0.6 (42 redundantes); PCA solo diagnóstico.
- Paso 9: 44 de 68 variables con IV ≥ 0.02; 0 no monótonas; máx. IV 0.305 (`transfer_to_competitor_pct_90d`).
- Paso 10: campeón de 8 variables en 5 dimensiones (Gini CV 0.441 con bins fijos); challenger de 16 variables.
- Paso 11: campeón Gini 0.429 / PR-AUC 0.344 (CV anidada) vs challenger XGBoost Gini 0.431 / PR-AUC 0.363; el
  challenger no cumple 4 criterios H-2 evaluables en dev → se recomienda el campeón.

### Variables del campeón [DATA]
| variable | IV | dimensión | signo | β |
|:--|--:|:--|:-:|--:|
| `client_reply_rate` | 0.216 | relación | − | 0.645 |
| `banker_change_6m_flag` | 0.289 | relación | + | 0.737 |
| `share_of_wallet` | 0.196 | patrimonial | − | 0.486 |
| `outflow_x_contact_gap` | 0.205 | transaccional | + | 0.325 |
| `return_vs_benchmark` | 0.061 | economía | − | 0.725 |
| `streams_stopped_count` | 0.199 | transaccional | + | 0.487 |
| `cash_pct_of_portfolio_chg` | 0.107 | transaccional | + | 0.507 |
| `contact_gap_ratio_peer` | 0.139 | relación | + | 0.339 |

## Decisiones del bloque
- D5.1, D6.1, D7.1–D7.2, D8.1, D9.1–D9.5, D10.1–D10.4, D11.1–D11.4 en `reports/decision_log.md`.

## Preguntas para el usuario (con default)

| # | Pregunta | Default |
|:--|:--|:--|
| G2-1 | Flags raros y variables casi siempre en cero: ¿se usan bins de negocio ({0,1}; "= mínimo / > mínimo") con ≥ 30 eventos por bin en vez del mínimo de 5% de hogares del SPEC? (D9.1, D9.1b) | sí, bins de negocio |
| G2-2 | UHNW tiene 175 eventos con target B (> 100). ¿Scorecard UHNW propio? | no: libro único con `segment_uhnw` (IV 0.002, sin riesgo distinto); UHNW reportado aparte en validación |
| G2-3 | ¿Se acepta que la adición elija cualquier miembro de cada cluster de variables (uno por cluster) en vez del representante 1−R² literal? (D10.2: Gini 0.441 vs 0.386, mejor en 25/25 folds) | sí, D10.2 |
| G2-4 | ¿Campeón (WoE + logística) sigue a escalamiento, tramos, validación y calibración? | sí; challenger como referencia, medido una vez en validación en el paso 13 |

Responde o escribe **"usa defaults"**. No avanzo al paso 12 hasta tu respuesta.
