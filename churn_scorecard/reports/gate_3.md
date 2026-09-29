# Gate 3 · Escalamiento, validación y calibración (pasos 12–14)

## Tests
- `python -m pytest -q` → **75 passed** (pasos 00–14).

## Resumen del bloque [DATA]
- Escala PDO: base 531 puntos; score de 296 a 640; score alto = menos churn. Σ puntos + base = score en los 20,000 hogares.
- Tramos (cortes en dev, score ≤ 445 / 517 / 573) y resultado en validación:

| tramo | % hogares val | tasa observada val | p calibrada | hogares (20,000) |
|:--|--:|--:|--:|--:|
| Crítico | 4.3% | 55.6% | 52.2% | 838 |
| Alto | 23.7% | 21.1% | 20.2% | 4,757 |
| Vigilancia | 43.9% | 11.1% | 11.6% | 8,854 |
| Estable | 28.1% | 5.8% | 6.3% | 5,551 |

  Verificación: Σ share × tasa = 13.90% = tasa val [DATA].
- Validación (holdout tocado una vez): Gini 0.390 (dev 0.444, caída 12.1% ≤ 15%); PSI por tramo 0.0003; lift
  Crítico/Estable 9.5x; 9/9 criterios de aprobación. Top 10% de hogares captura 27.9% de los eventos y 25.8% del RV
  que se va.
- Calibración: Platt (b = 0.854); isotónica no mejora; los 4 tramos dentro del IC de Wilson 90%.
- Overrides activos (→ Alto): cambio de banquero, queja escalada, transferencia a competidor ≥ 10%; cambio de
  fiduciario eliminado (precisión 11.7% < 12%). Caseload Crítico: 21 / 8.4 / 4.2 hogares por banquero con 40 / 100 / 200 banqueros.

## Decisiones del bloque
- D12.1–D12.5, D13.1, D14.1–D14.3 en `reports/decision_log.md`.

## Preguntas para el usuario (con default)

| # | Pregunta | Default |
|:--|:--|:--|
| G3-1 | Las 3 reglas de override juntas suben 848 hogares a Alto (36% del tramo; cada una por separado ≤ 30%). Su precisión en validación es 14–24% (≥ 12%). ¿Se mantienen las tres? | sí, las tres |
| G3-2 | En el 20% de hogares con más patrimonio el modelo se queda corto (tasa real 15.5% vs 13.7% estimada; dinero en riesgo subestimado ~15%). Ajustarlo por tamaño no es estadísticamente significativo (p = 0.097). | no ajustar; vigilar ese grupo en el monitoreo (paso 17) |
| G3-3 | UHNW en tramo Alto: se van 31.6% vs 19.4% estimado (solo 24 casos). | sin calibración propia; UHNW en Alto con revisión prioritaria del banquero |
| G3-4 | Grupo de control aleatorio en Alto para medir si las acciones funcionan: 10%, 12.5% o 15%. | 12.5% (595 hogares; detecta una reducción de churn de ~24% o más) |

Responde o escribe **"usa defaults"**. No avanzo al paso 15 hasta tu respuesta.
