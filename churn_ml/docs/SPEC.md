# SPEC — Churn Propensity · Modelo 2 (ML) sobre `client_pulse_synthetic.xlsx`

Procedimiento completo, paso a paso. Se ejecuta con `/step NN` (ver CLAUDE.md). Este archivo es la fuente de verdad del
método; CLAUDE.md fija las convenciones y `.claude/rules/` las reglas de reporte y de datos.

Pasos que terminan en gate: 0 → G0, 3 → G1, 6 → G2, 9 → G3, 12 → G4.

## A. OBJETIVO

Construir un modelo ML (gradient boosting monotónico) que prediga el target B con la mejor capacidad posible de
priorizar hogares y valor en riesgo, **explicable por hogar** y operable con los mismos tramos, SLA y monitoreo que el
Modelo 1, y decidir con la tabla H-2 si reemplaza, complementa o no al scorecard.

## B. PUNTO DE PARTIDA `[DATA]` (heredado de `../churn_scorecard/`, versión 1.0.0)

| Hecho heredado | Valor |
|---|---|
| Target B | hard 6M ∪ (soft con pérdida ≥ 25% del RV); 19,261 hogares, 2,674 eventos (13.88%); A como sensibilidad |
| Split | dev 13,631 (B 13,482 / 1,871 eventos) · val 5,842 (B 5,779 / 803); CV 5×5 en dev (`cv_r1..cv_r5`) |
| Features | `features.parquet` (20,000 filas): 54 del proveedor − edad − buró + 15 derivadas + razones de missing |
| Signos de negocio | `step05_features.csv` (G1-1): + / − = restricción monótona, "?" = libre |
| Campeón (M1) | 8 variables WoE; CV anidada Gini 0.429 / PR-AUC 0.344; val Gini 0.390 / PR-AUC 0.328; Platt b = 0.854 |
| Challenger previo (paso 11B de M1) | 16 variables, XGBoost prof. 3, 69 árboles: CV Gini 0.431 / PR-AUC 0.363; captura RV decil 1 0.335 vs 0.284; reason codes top 1 77.0%; interacciones 24% de Σ\|φ\| |
| Holdout | `val` usado una vez por el campeón M1; se usará una vez más, solo con el modelo ML final |

Consecuencias de diseño:
- Mismo target, split, folds y holdout ⟹ comparación pareada limpia contra M1.
- El valor esperado del ML está en **PR-AUC y captura de valor en la cola** (el Gini empató en M1); la selección se hace
  por la tabla H-2, no por una sola métrica.
- Sin dimensión temporal (L1): la validación es el holdout aleatorio del mismo snapshot.

## D. REGLAS NO NEGOCIABLES

1. Cero benchmarks de industria y cero cifras de bancos reales. Marco MRM; sin Basilea ni IFRS 9.
2. Ningún predictor usa columnas de resultado ni transformaciones de ellas. Edad y buró fuera (G1-3 de M1).
3. Missing estructural = NaN nativo del GBM; nunca imputar por media/mediana.
4. Monotonía obligatoria por signo de negocio; profundidad ≤ 3; `min_child_weight` ≥ 5.
5. Pesos de clase (nunca SMOTE); la probabilidad publicada es siempre la calibrada.
6. Calibración ajustada con predicciones OOF cruzadas de dev; el holdout no se usa para ajustar nada.
7. Toda selección (variables, hiperparámetros, algoritmo, cortes) se hace en dev con CV 5×5; el holdout se toca una
   vez, en el paso 9, con el modelo congelado.
8. Score único = escala PDO; puntos por variable desde SHAP (Σ puntos + base = score por fila).
9. Reason codes con estabilidad bootstrap reportada; si la estabilidad top 1 < 70%, se publican solo top 3 como
   conjunto y se documenta.
10. Clustering nunca causal. PCA prohibido en modelo.

## G. PROCEDIMIENTO

### Paso 0 — Herencia y verificación (termina en G0)
- Copiar a `data/inherited/` (con sha256): `features.parquet`, `dev.parquet`, `val.parquet`, `step01_population.parquet`,
  `step07_clusters.parquet`, `step05_features.csv`, OOF del campeón y su score por hogar. Test: hashes, tamaños y tasas
  de la sección B.
- Re-verificar en el archivo raw los hechos de la ficha que usa el ML (conteos, tasas, missing estructural).
- Preguntas de la sección I.

### Paso 1 — Conjunto de variables
- Candidatas: todas las del M1 (con compuestos si I-2 lo permite) + `cluster`; valores crudos, NaN nativo.
- Cribado: casi constantes (modal ≥ 99%); fuga (AUC univariada > 0.85 o IV > 0.50); pares |ρ| > 0.95 (duplicados
  casi exactos, p. ej. base vs `_peer` dentro de celda): uno por par.

### Paso 2 — Selección de variables
- Importancia por permutación OOF (ΔPR-AUC) en los 25 folds con un GBM base; se queda lo que aporta > 0 en ≥ 80% de los
  folds; eliminación hacia atrás mientras PR-AUC CV no caiga más de 1 sd. Cierre 12–30 variables.
- Variante con y sin compuestos (I-2) reportada lado a lado.

### Paso 3 — Algoritmo e hiperparámetros (termina en G1)
- XGBoost y LightGBM con `monotone_constraints`; Optuna (TPE, semilla 42) 150 trials cada uno, MedianPruner, objetivo
  PR-AUC media 5×5. Espacio: `max_depth` {2,3}, `min_child_weight` [5,50], `learning_rate` log-U[0.01,0.1],
  `n_estimators` por early stopping interno, `subsample` [0.6,0.9], `colsample_bytree` [0.5,0.9], `reg_lambda` [1,20],
  `reg_alpha` [0,5], `gamma` [0,5]. Referencias: EBM monotónico, RF, campeón M1 (OOF).
- Sensibilidad a 3 semillas. Elección del algoritmo por PR-AUC media, con empate (≤ 1 sd) a favor del más simple
  (menos árboles × profundidad).

### Paso 4 — Explicabilidad
- TreeSHAP `model_output="raw"` (log-odds); aditividad φ₀ + Σφ = margen (error < 1e-3).
- ICE/PDP: violaciones de monotonía = 0. Interacciones SHAP: variables con > 20% de su |φ| en interacción ⟹ documentar o
  restringir (`interaction_constraints`) si cambian el signo de negocio. ALE para las 5 de mayor |φ|.
- Reason codes: top 3 por φ positivo; estabilidad en 200 réplicas bootstrap (top 1 y top 3); signo coherente por variable.

### Paso 5 — Calibración
- Predicciones OOF cruzadas en dev (CV 5×5, promedio por hogar). Platt vs isotónica por Brier y ECE con IC bootstrap;
  isotónica solo si mejora Brier con IC < 0. Aceptación Platt 0.8 ≤ b ≤ 1.2. Alineación media p vs tasa.
- Calibración por segmento y por quintil de RV (Σ p·RV vs Σ RV de eventos), heredando las decisiones G3-2 / G3-3 de M1.

### Paso 6 — Escalamiento, tramos y salida (termina en G2)
- Score = Offset − Factor·logit(p_cal) redondeado; puntos por variable = −Factor·b·φⱼ (b de Platt), residuo de redondeo
  a la base; assert Σ = score por fila.
- Tramos con las reglas H-3 del M1 (salto ≥ 2x / 1.5x, lift Crítico/Estable ≥ 5x, ≥ 70 eventos por tramo en dev) y
  cortes propios; además, vista con el mismo % de hogares por tramo que M1 para comparar a igual capacidad.
- Overrides: mismas reglas activas de M1 re-evaluadas (≥ 25% Crítico, 12–25% Alto, ≤ 30% del tramo).
- `outputs/scores/household_scores_ml.csv`: score, probabilidad calibrada, tramo, banda, top 3 reason codes con puntos,
  overrides, y el tramo del M1 al lado.

### Paso 7 — Robustez en dev
- Estabilidad de |φⱼ| e importancias entre folds; sensibilidad a quitar la variable top; desempeño por segmento,
  quintil de RV, antigüedad, historia < 24 meses y cluster (OOF).

### Paso 8 — Equidad y uso responsable
- Sin edad ni buró como entrada; prueba de proxy: AUC de predecir `age_primary` (terciles) con las variables del modelo y
  diferencia de tasas de Crítico por tercil de edad (solo diagnóstico, no se usa para puntuar).

### Paso 9 — Validación en el holdout (termina en G3)
- Una sola vez, con el modelo congelado: AUC, Gini, PR-AUC, KS, gains/lift por decil, Precision@K / Lift@K con captura
  ponderada por RV, confusión al corte de Crítico, calibración por tramo (Wilson 90%), PSI dev→val por tramo.
- Tabla H-2 completa contra M1 (mismos hogares, pareado; IC bootstrap de ΔGini y ΔPR-AUC).

### Paso 10 — Uso conjunto
- Matriz tramo M1 × tramo ML en val: acuerdo, hogares que solo uno marca como Crítico/Alto y su tasa observada.
- Opciones: (a) ML reemplaza; (b) M1 prioriza y ML afina dentro de tramo; (c) ML solo como alerta adicional. Captura y
  caseload de cada opción a igual capacidad.

### Paso 11 — Arquetipos y acción
- Reutilizar los 3 arquetipos de M1 (asignación sin reajuste) y describir qué agrega el ML por arquetipo (en especial
  "desgaste silencioso", el punto débil de M1).

### Paso 12 — Monitoreo, gobernanza, documento (termina en G4)
- KPIs y disparadores (recalibración b fuera de 0.8–1.2 dos ciclos; redesarrollo PSI > 0.25 sostenido o Gini −15%;
  deriva de |φⱼ|); manifiesto de modelo con versión; `reports/model_document.md` (pasos 0–12, limitaciones L1–L8 de M1 +
  las propias del ML, registro de decisiones).

## H. TABLAS DE DECISIÓN

Tabla 2 — Reemplazo del M1 por el ML (heredada de M1; todas obligatorias, medidas en validación): ΔGini ≥ +0.05 y
ΔPR-AUC ≥ +0.03; caída dev→val ≤ 15% y no peor que M1; Brier ≤ M1 con b ∈ [0.8, 1.2]; violaciones de monotonía = 0;
reason codes estables (≥ 70%) y con signo coherente en 100% de variables; captura por RV en decil top ≥ M1; PSI dev→val
< 0.10 por tramo. Si no cumple todas: el ML no reemplaza; el paso 10 decide si complementa (opciones b / c).

Tabla 3 — Cortes de tramos: salto 2x (1.5x en Vigilancia/Estable) → lift ≥ 5x → ≥ 30 eventos por tramo en validación.

## I. PREGUNTAS EN G0 (con default)

- **I-1** ¿Mismo target (B), split y holdout que M1? Default: **sí** (comparación pareada).
- **I-2** ¿Se permiten los compuestos `multi_signal_count` / `_flag`? Default: **sí**, reportando la variante sin ellos;
  si la diferencia de PR-AUC es < 1 sd, se elige la variante sin compuestos (regla no documentada, L3).
- **I-3** ¿Monotonía obligatoria por signo de negocio? Default: **sí**; "?" libres.
- **I-4** Algoritmos: XGBoost y LightGBM (EBM y RF solo referencia). Default: **sí**.
- **I-5** ¿Calibración en OOF de dev (sin tocar el holdout)? Default: **sí**.
- **I-6** ¿Capacidad de Crítico igual a M1 (~4% de hogares) para comparar? Default: **cortes propios por reglas H-3, más
  vista a igual % que M1**.
- **I-7** Si el ML no cumple H-2: ¿se evalúa como complemento (paso 10)? Default: **sí**.
- **I-8** ¿Prueba de proxy de edad (paso 8)? Default: **sí, solo diagnóstico**.

## J. ENTREGABLE Y CIERRE

`reports/model_document.md` consolidado 0–12, precedido por modo, punto de partida heredado, parámetros y supuestos;
cierra con: comparación final M1 vs ML y recomendación de uso, qué cambiaría con datos reales y panel temporal,
preguntas para el equipo de datos, limitaciones, registro de decisiones. Artefactos: `outputs/model/` (modelo, calibrador,
manifiesto con versión), `outputs/scores/household_scores_ml.csv`, `outputs/tables/step06_master_scale*.csv`, `tests/` en verde.
