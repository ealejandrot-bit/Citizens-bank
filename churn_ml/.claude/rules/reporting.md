# Reglas de reporte

Cada `reports/stepNN.md` tiene esta estructura fija, redactada a partir de las tablas de `outputs/tables/stepNN_*.csv`:

1. **Objetivo** (1–2 bullets).
2. **Método** (bullets; fórmulas cuando aplique).
3. **Código** · ruta del script y del test.
4. **Resultados** · tablas markdown generadas desde los CSV; cada cifra con `[DATA]`, `[DEF]` o `[DEF-default]`.
   Bajo cada tabla, la verificación aritmética cuando aplique: tramos suman 100%; churn de cartera = Σ share × tasa;
   captura suma 100%; Σ puntos + base = score.
5. **Tests** · resultado de `tests/test_stepNN.py` (n asserts, PASS/FAIL).
6. **Decisiones y preguntas abiertas** · con referencia a su entrada en `reports/decision_log.md`.

Formato: español, tablas markdown, bullets densos, sin introducción ni resumen ejecutivo. Figuras en `outputs/figs/`.
`reports/gate_N.md`: estado de tests, decisiones tomadas en el bloque, preguntas para el usuario con su default.
