# Gate 2 · Explicabilidad, calibración y escalamiento (pasos 4–6)

## Tests
- `python -m pytest -q` → **21 passed** (pasos 00–06).

## Resumen del bloque [DATA]
- EBM (principal): explicación exacta por cliente, sin interacciones, 0 violaciones de signo; razones por cliente
  estables 85% (XGBoost 81.5%); signo coherente 100% en ambos.
- Calibración sin tocar validación: EBM casi calibrado de origen (b = 1.03); XGBoost b = 1.15; Platt en ambos.
- Score PDO del EBM: base + puntos por variable (lookup de 323 filas); Σ puntos + base = score en los 20,000 hogares.

| tramo (dev) | EBM: % hogares | EBM: tasa | M1: % hogares | M1: tasa |
|:--|--:|--:|--:|--:|
| Crítico | 4.1% | 60.0% | 4.0% | 56.6% |
| Alto | 21.8% | 22.5% | 23.6% | 22.9% |
| Vigilancia | 51.0% | 10.8% | 44.3% | 11.0% |
| Estable | 23.2% | 4.6% | 28.0% | 4.7% |

  Verificación: Σ share × tasa = 13.88% = tasa dev en ambos [DATA].

## Decisiones del bloque
- D4.1, D5.1, D6.1–D6.3 en `reports/decision_log.md`.

## Preguntas para el usuario (con default)

| # | Pregunta | Default |
|:--|:--|:--|
| G2-1 | Alertas que suben a Alto en el ML: se quedan cambio de banquero y queja escalada; la de transferencia a competidor sale porque el EBM ya la usa (los que movería se van solo 2.8%). ¿De acuerdo? | sí |
| G2-2 | Igual que el M1, el ML se queda corto en el 20% más rico y en UHNW. ¿Mismo tratamiento que en el M1 (sin ajuste, vigilar)? | sí |
| G2-3 | ¿Se mantiene XGBoost como segundo candidato hasta la validación (paso 9), aunque tiene interacciones y razones menos estables? | sí, solo como comparación |
| G2-4 | Tramos del ML: cortes propios (Estable 23%) y además la vista con los mismos % del M1 para comparar a igual capacidad. ¿De acuerdo? | sí |

Responde o escribe **"usa defaults"**. No avanzo al paso 7 hasta tu respuesta.
