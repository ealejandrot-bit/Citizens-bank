# Gate 3 · Robustez, equidad y validación (pasos 7–9)

## Tests
- `python -m pytest -q` → **29 passed** (pasos 00–09).

## Resumen del bloque [DATA]
- Robustez: importancias estables; sin dependencia de una sola variable; por subgrupo rinde como el M1.
- Equidad: la edad no entra; las variables la adivinan débilmente (AUC 0.63); marcado proporcional al churn por edad.
- Validación (holdout, una vez, mismos 5,779 hogares):

| | M1 (scorecard) | EBM | XGBoost |
|:--|--:|--:|--:|
| Gini | 0.390 | 0.406 | 0.403 |
| PR-AUC | 0.328 | 0.343 | 0.344 |
| Precisión en el top 1% | 63.8% | 75.9% | 77.6% |
| Precisión en Crítico | 55.6% | 53.3% | 51.9% |
| Captura del RV que se va, top 10% | 25.8% | 26.7% | 26.6% |
| Caída de Gini dev→val | 12.1% | 8.6% | 12.7% |
| Criterios H-2 cumplidos | — | 6 de 8 | 4 de 8 |

- El EBM mejora al M1 (+0.015 de PR-AUC, 97% de las réplicas bootstrap a favor) pero no alcanza los umbrales de
  reemplazo (+0.05 Gini, +0.03 PR-AUC) ⟹ **no reemplaza** al M1.
- El EBM sobrestima Crítico en val (61% esperado vs 53% observado); los otros 3 tramos quedan bien calibrados.

## Decisiones del bloque
- D7.1, D8.1, D9.1 en `reports/decision_log.md`.

## Preguntas para el usuario (con default)

| # | Pregunta | Default |
|:--|:--|:--|
| G3-1 | Según la tabla H-2 el ML no reemplaza al scorecard. ¿Seguimos con el paso 10 para ver si conviene usarlos juntos (p. ej. el ML ordena dentro de cada tramo del M1)? | sí |
| G3-2 | XGBoost cumple menos criterios que el EBM. ¿Lo retiramos y seguimos solo con el EBM? | sí, se retira (queda documentado) |
| G3-3 | El EBM sobrestima el tramo Crítico en validación. No se puede re-ajustar con estos datos sin tocar otra vez la validación. | documentar y re-calibrar con el próximo snapshot con resultados; mientras tanto, publicar la tasa observada de Crítico |

Responde o escribe **"usa defaults"**. No avanzo al paso 10 hasta tu respuesta.

## Adenda · comparativa con A-lite (pedido del usuario, paso 9b) [DATA]
- A-lite (5 variables, `scorecard/`) medido sin re-ajustar en los 1,737 hogares de val fuera del desarrollo de todos los
  modelos (238 eventos B):

| | A-lite (5 var.) | M1 (8 var.) | EBM (12 var.) |
|:--|--:|--:|--:|
| PR-AUC target B | 0.262 | 0.304 | 0.305 |
| Gini target B | 0.312 | 0.321 | 0.327 |
| Precisión top 5% (B) | 40.2% | 49.4% | 49.4% |
| Captura RV de eventos top 10% (B) | 21.4% | 20.3% | 19.6% |
| PR-AUC target A (hard) | 0.153 | 0.191 | 0.209 |

- A-lite encuentra menos churners (−0.04 de PR-AUC vs M1 y EBM, IC que excluye 0) a cambio de ser el más simple; en
  este subconjunto el EBM y el M1 quedan empatados (+0.001).
- Respuesta del usuario: defaults G3 aprobados; se sigue al paso 10.
