# Gate 4 · Uso conjunto, arquetipos y cierre (pasos 10–12)

## Tests
- `python -m pytest -q` → **38 passed** (pasos 00–12).

## Resumen del bloque [DATA]
- Uso conjunto (val): M1 y EBM coinciden en el tramo del 82.9% de los hogares. A igual capacidad (10% de hogares, tramo
  primero), todas las combinaciones capturan 48–49% del RV que se va ⟹ el ML no agrega en operación.
- Hallazgo: priorizar por probabilidad × RV en toda la cartera (en vez de tramo primero) captura ~59–61% del RV que se
  va con cualquier modelo, a cambio de menos casos (18–21% de los eventos vs 28%).
- Arquetipos: el EBM no detecta mejor a ningún tipo; el "desgaste silencioso" (47.6% de los que se van) sigue siendo el
  punto ciego común.

| | M1 · scorecard | EBM (ML) | A-lite | XGBoost |
|:--|:--|:--|:--|:--|
| Variables | 8 | 12 | 5 | 12 |
| PR-AUC · 1,737 hogares que ningún modelo vio | 0.304 | 0.305 | 0.262 | 0.297 |
| Precisión top 5% · mismo subconjunto | 49.4% | 49.4% | 40.2% | 46.0% |
| Rol recomendado | operativo | challenger en monitoreo | comunicación ejecutiva | retirado |

## Decisiones del bloque
- D10.1, D11.1, D12.1 en `reports/decision_log.md`. Entregable: `reports/model_document.md`.

## Preguntas para el usuario (con default)

| # | Pregunta | Default |
|:--|:--|:--|
| G4-1 | Roles: M1 operativo, EBM challenger en monitoreo, A-lite para ejecutivos, XGBoost retirado. ¿De acuerdo? | sí |
| G4-2 | Regla de prioridad: el orden por probabilidad × RV en toda la cartera captura más valor que "tramo primero". ¿Se propone al negocio como piloto (usando el control 12.5% del M1)? | sí, como propuesta; la decisión es de negocio |
| G4-3 | ¿Cerramos la versión ML 1.0.0 y pasamos al Modelo 3 (redes neuronales)? | sí |

Responde o escribe **"usa defaults"**.
