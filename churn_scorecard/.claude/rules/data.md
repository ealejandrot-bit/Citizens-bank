# Reglas de datos

- `data/raw/` es de solo lectura. Ningún script escribe ahí (salvo el bootstrap único documentado en decision_log).
- Toda cifra reportada sale de una tabla generada por código y lleva etiqueta:
  `[DATA]` cifra del archivo · `[DEF]` parámetro fijado por el usuario · `[DEF-default]` default aplicado por falta de respuesta.
  Cifra sin etiqueta = error.
- Prohibidos como predictores: `hard_churn_6m`, `soft_churn_3m`, `value_lost_6m`, `churn_excluded` y cualquier
  transformación de ellos; `household_id`, `snapshot_date`. `multi_signal_count` / `multi_signal_flag`: solo challenger
  y análisis salvo que el proveedor entregue la regla (I-3).
- Missing estructural ("no aplica") = categoría propia: bin propio (campeón), NaN nativo (GBM), indicador si aporta.
  Prohibido imputar por media o mediana.
- Sin benchmarks de industria ni cifras de bancos reales. Sin Basilea ni IFRS 9.
- PCA solo diagnóstico (paso 8). Clustering nunca causal; se ajusta en dev y se asigna en val sin reajuste.
- Sin OOT ni PSI temporal (limitación L1). El holdout se toca una sola vez por modelo final.
- Desbalance: pesos de clase, nunca SMOTE.
- Outliers: clasificar (error / real / extraordinario); capping solo para errores documentados.
- Si falta un parámetro que cambia el resultado: detente y pregunta.
