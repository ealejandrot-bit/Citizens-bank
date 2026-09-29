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
