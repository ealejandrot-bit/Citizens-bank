# Gate 4 · Estabilidad, acción y gobernanza (pasos 15–17) · cierre

## Tests
- `python -m pytest -q` → **84 passed** (pasos 00–17).

## Resumen del bloque [DATA]
- Estabilidad: PSI dev→val del score 0.0034, de la probabilidad 0.0035, por tramo 0.0003; variables ≤ 0.0027;
  subgrupos (segmento, RV, antigüedad, historia, cluster) ≤ 0.035. Peso de cada variable estable entre folds.
- Arquetipos de quienes se van (3, descriptivos): relación desatendida 36.5%, salida activa a competidor 19.4%
  (69% de ellos en Crítico), desgaste silencioso 44.1% (21% en Estable: el modelo los ve poco).
- Playbook tramo × arquetipo con SLA (Crítico ≤ 5 días hábiles, Alto ≤ 15), control 12.5% en Alto; EWS con 5
  disparadores (2 requieren un segundo snapshot, L1).
- KPIs con línea base de validación y disparadores de recalibración / redesarrollo; gobernanza propuesta; limitaciones
  L1–L8.
- Entregable: `reports/model_document.md` (pasos 0–17 consolidados, ficha, parámetros, qué cambiaría con datos
  reales, preguntas al equipo de datos, registro de decisiones), `outputs/model/MANIFEST.json` (versión 1.0.0).

## Decisiones del bloque
- D15.1, D16.1–D16.2, D17.1 en `reports/decision_log.md`.

## Preguntas para el usuario (con default)

| # | Pregunta | Default |
|:--|:--|:--|
| G4-1 | Alerta de deterioro para el refresco mensual: caída ≥ 40 puntos (1 PDO = el riesgo se duplica) o bajar 2 tramos. | sí, 40 puntos |
| G4-2 | Roles de gobierno propuestos (dueño = negocio de banca privada; validación = MRM; monitoreo mensual). | aceptar como propuesta |
| G4-3 | ¿Cerramos la versión 1.0.0 del modelo con este documento? | sí; siguiente paso sugerido: Modelo 2 (ML) si lo quieres retomar |

Responde o escribe **"usa defaults"**.
