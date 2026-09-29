# Decision log

Memoria del proyecto. Nada se decide fuera de este archivo. Etiquetas: `[DATA]` del archivo · `[DEF]` fijado por el
usuario · `[DEF-default]` default aplicado.

## Estado
- Último paso completado: **13** · G0, G1, G2 cerrados · bloque en curso: pasos 12–14 (G3) · G0 y G1 cerrados ("usa defaults", 2026-09-29) · bloque en curso: pasos 5–11 (G2).
- Tests: 71 / 71 PASS (pasos 00–13).

## Parámetros vigentes
| Parámetro | Valor | Etiqueta |
|:--|:--|:--|
| Escala | S₀ = 600 @ O₀ = 20:1 (buenos:malos), PDO = 40 ⟹ Factor 57.71, Offset 427.12 | [DEF-default] I-6 |
| SEED | 42 | [DEF] |
| Target principal | B = hard ∪ (soft con value_lost/RV ≥ θ), θ = 0.25; soft con pérdida < 0.25 = indeterminado | [DEF-default] I-1 |
| Target de sensibilidad | A = hard_churn_6m | [DEF-default] I-1 |
| Capacidad | sin dato → Crítico por lift / precisión / eventos; tabla de caseload 40 / 100 / 200 banqueros | [DEF-default] I-2 |
| `multi_signal_count` / `_flag` | fuera del campeón; permitidos en challenger | [DEF-default] I-3 |
| `churn_excluded` | se excluyen (123); motivo desconocido | [DEF-default] I-4 |
| `relationship_value`, `share_of_wallet` | se usan como vienen; RV = AUM + depósitos (G0-a) | [DEF-default] I-5, G0-a |
| Segmentación | libro completo con `segment` como variable; UHNW reportado aparte | [DEF-default] I-7 |
| Antigüedad | excluir `tenure_years` < 1 | [DEF-default] I-8 |
| Supervivencia | no; solo descriptivo en paso 14 | [DEF-default] I-9 |
| `value_lost_6m` | solo churn por valor y calibración por valor; nunca predictor | [DEF-default] I-10 |
| Signos esperados | los de `step02_signs_a_priori.csv`; las 7 "?" sin restricción monótona | [DEF-default] G1-1 |
| Clientes con tenure < 1 | score con bandera "fuera de población de desarrollo"; revisión del banquero en onboarding; sin métricas del modelo | [DEF-default] G1-2 |
| `age_primary`, `bureau_new_mortgage_elsewhere` | fuera del campeón y del challenger; solo sensibilidad | [DEF-default] G1-3 |
| `history_months` < 24 | se conservan con indicador `hist_lt24` | [DEF-default] G1-4 |
| Bins de flags raros / variables infladas en su mínimo | bins de negocio con ≥ 30 eventos por bin (D9.1, D9.1b) | [DEF] G2-1 |
| Modelo UHNW | un solo modelo con `segment_uhnw`; UHNW reportado aparte | [DEF] G2-2 |
| Selección por cluster | adición elige cualquier miembro, uno por cluster (D10.2) | [DEF] G2-3 |
| Modelo a escalar | campeón WoE + logística; challenger solo como referencia de ajuste de probabilidad (11C) | [DEF] G2-4 |

## Decisiones
- **D0.0 · Ubicación.** El proyecto vive en `churn_scorecard/` dentro del repo Citizens-bank, separado del generador
  sintético (`synthetic/`, `scripts/`) y del Modelo 1 previo (`scorecard/`). Paso 0 del SPEC.
- **D0.1 · Bootstrap del archivo fuente.** `data/raw/client_pulse_synthetic.xlsx` no existía. Se creó una sola vez con
  `src/bootstrap_raw.py` a partir de `../data/synthetic/client_pulse_synthetic.csv` (sha256 `44a1d18b…`), hoja
  `client_pulse_synthetic`, con verificación de que la relectura es idéntica al CSV. Archivo en solo lectura desde ahí.
- **D0.2 · Discrepancia con la ficha: RV vs AUM + depósitos.** La ficha dice "RV ≠ AUM + depósitos: RV es una medida
  propia". En el archivo RV = AUM (0 si no hay inversiones) + depósitos con |dif| máx. $0.01 [DATA]; solo difiere por
  redondeo de flotantes. El test verifica ambas cosas (desigualdad literal y la identidad al centavo). Implicación:
  `relationship_value` y `aum` son casi colineales (Spearman 0.97 [DATA]); RV no aporta información distinta a la suma.
  Pregunta al usuario (G0-a).
- **D0.3 · ρ de compuestos.** El 0.59 de la ficha es Pearson entre `multi_signal_count` y la suma de las 10 señales
  binarias visibles (9 `*_flag` + `bureau_new_mortgage_elsewhere`) = 0.59 [DATA]; con Spearman o solo los 9 flags da
  0.46–0.56 [DATA]. Se documenta la definición.
- **D0.4 · Base de la ficha.** Las cifras de tamaño, missing estructural (2,847), historia (1,417) y top 5% / 1% de la
  ficha están calculadas sobre los 19,877 elegibles. Con esa base coinciden todas [DATA].
- **D0.5 · Cribado anti-fuga.** Ninguna señal individual supera AUC 0.70 [DATA]. `multi_signal_count` tiene IV A =
  0.547 > 0.50 [DATA] → marcado "sospechoso" por la regla del SPEC; es un compuesto de señales pre-T0 sin regla
  documentada (I-3), ya excluido del campeón por D.12. Control: `value_lost_6m` tendría AUC vs A = 1.000 [DATA].
- **D0.6 · Test RV.** La tolerancia "al centavo" se expresa como diferencia redondeada a 6 decimales ≤ $0.01 (la
  diferencia máxima es 0.0100001097 por ruido de flotante en magnitudes de 10⁸–10⁹); el umbral no se relajó.

- **D1.1 · Población y targets.** B: 19,261 hogares, 2,674 eventos (13.88%); A: 19,473 hogares, 1,168 eventos
  (6.00%) [DATA]. 212 indeterminados de B (soft con pérdida < 0.25) fuera de entrenamiento y dentro de scoring.
- **D1.2 · Exclusión tenure < 1 (I-8, default).** Los 404 excluidos tienen más churn que el resto (A 7.92% vs 6.00%;
  B 16.50% vs 13.88%) [DATA]. El modelo no se desarrolla sobre clientes nuevos; se pregunta en G1 cómo tratarlos.
- **D1.3 · Pesos de clase.** Balanceados, w = N / (2·n_clase); odds de población B 0.1612 (ln −1.825) y A 0.0638
  (ln −2.752) [DATA] para corregir el intercepto en el paso 11. Nunca SMOTE.
- **D2.1 · Diccionario.** 54 predictores, 5 prohibidas, 3 auxiliares (2 compuestos y `value_lost_6m`) [DATA].
  Dimensiones ausentes: digital y vida (L6). Signos a priori en `outputs/tables/step02_signs_a_priori.csv`; 7 sin
  hipótesis ("?").
- **D2.2 · Revisión regulatoria pendiente.** `age_primary` (fair lending) y `bureau_new_mortgage_elsewhere` (FCRA,
  propósito permisible): pregunta en G1.
- **D3.1 · Calidad.** 0 duplicados, 0 imposibles, RV = AUM + depósitos al centavo, excepciones estructurales ≤ 3%
  (134 valores de pensión sin `has_pension_stream`), 0 errores en colas; extraordinarios conservados sin capping
  (p. ej. 63 hogares = 52.3% del monto enviado a competidores) [DATA].
- **D4.1 · Split.** Estratificado por clase (hard / soft ≥ θ / indeterminado / no evento) × segmento. La versión
  inicial estratificada solo por B dejó A desbalanceada (6.22% vs 5.48%, test de ±0.5 pp fallido) y se corrigió sin
  relajar el umbral. Dev 13,631 (B 13,482 / 1,871 eventos; A 817) · val 5,842 (B 5,779 / 803; A 351) [DATA].

- **D5.1 · Señales derivadas y missing.** 15 derivadas del SPEC (`common.DERIVED`) y razón de missing `<var>__miss`
  (ok / no_aplica / sin_dato) para 34 variables; 134 valores de pensión sin `has_pension_stream` → "no aplica" [DATA].
  Peer-relative = valor − mediana de dev de su celda segmento × quintil de RV (celdas de 151 a 2,575 hogares de dev)
  [DATA]; no es imputación. `competitor_x_new_destinations` hereda la razón de `new_external_destinations_90d` (D9.2).
- **D6.1 · Univariado.** 47 de 69 candidatas con IV ≥ 0.02 o RR significativo; 0 sospechas de fuga con B; 0
  discrepancias de signo [DATA]. Con A, `multi_signal_count` tiene IV 0.665 en dev (> 0.50) [DATA]: compuesto ya fuera
  del campeón (D0.5, D.12); en el challenger pasa por el filtro de fuga del paso 10 con target B.
- **D7.1 · Clustering sin edad.** El cluster es candidato a predictor; incluir `age_primary` reintroduciría la edad
  excluida por G1-3. Variables: `segment_uhnw`, `tenure_years`, `log_rv`, 8 `has_*`. K = 4 (regla fijada antes de ver
  resultados: tamaño ≥ 5%, ARI bootstrap ≥ 0.80, mayor silhouette); ARI 0.869; χ² cluster × y_B p = 0.153 [DATA].
- **D7.2 · UHNW con target B.** 175 eventos B en UHNW (122 en dev) [DATA] superan el mínimo de 100 del SPEC (pensado
  para A, 79). Se mantiene I-7 (libro único con `segment_uhnw`) [DEF-default]; pregunta G2-2.
- **D8.1 · Redundancia.** 58 pares con |ρ| > 0.6: 42 redundantes (ΔAUC < 0.005 al agregar la otra) y 16 con
  información incremental [DATA]. Nada se elimina en el paso 8; decide el paso 10. VIF sobre rangos infinito por
  identidades de construcción (RV = AUM + depósitos, `aum_share` + `deposit_share` = 1, base vs `_peer`).
- **D9.1 · Bins de negocio en binarias (desvío del SPEC).** Con `min_bin_size` = 5% los flags con < 5% de hogares en 1
  se fusionan y pierden la señal (p. ej. `complaint_age_days` quedaba con IV 0 [DATA]). Binarias → bins {0, 1} si ambos
  tienen ≥ 30 eventos (se mantiene el mínimo de eventos del SPEC). Pregunta G2-1.
- **D9.1b · Variables infladas en su mínimo.** Si ≥ 70% de los hogares con dato están en el mínimo: bins "= mínimo" /
  "> mínimo" (y "≥ 2" en conteos desde 0), siempre ≥ 30 eventos por bin. 8 variables; p. ej. `products_closed_180d`
  IV 0.208 vs 0.000 por cuantiles [DATA]. Pregunta G2-1.
- **D9.2 · Missing sin razón.** `competitor_x_new_destinations` tenía 204 NaN en dev sin razón de missing y el test de
  suma de bins lo detectó (quedaban fuera de la tabla). Corrección: razón heredada (paso 5) y, en `woe.py`, todo NaN sin
  razón va a "sin_dato". Pasos 5–9 re-ejecutados; tests en verde.
- **D9.3 · Especiales pequeños.** Un bin "sin dato" con < 30 eventos se une a "no aplica" si existe; si el grupo sigue
  con < 30 eventos, WoE = 0 (neutral).
- **D9.5 · Pre-binning.** Se prueban `min_prebin_size` 1% / 2% / 5% y se queda el de mayor IV (todas cumplen las
  restricciones); el pre-binning CART no encuentra cortes con muchos empates.

- **D10.1 · Criterio de adición.** Entra la variable de mayor ΔGini medio en los 25 folds (bins fijos del paso 9) si
  ΔGini > 0 en ≥ 80% de los folds (mismo umbral que la permutación del challenger), VIF(WoE) < 5 y todos los β con signo
  correcto; tope 10 [DEF-default]. Variables con signo "?" fuera del campeón (regla D.7: signo y lógica de negocio).
- **D10.2 · Representante de cluster (desvío del SPEC).** La regla literal (menor (1−R²propio)/(1−R²vecino)) deja
  fuera `banker_change_6m_flag` (IV 0.289) frente a `relationship_dissatisfaction_flag` (IV 0.027) en un cluster débil de
  2 flags: Gini CV 0.386 con 7 variables. Con "a lo sumo una por cluster, el aporte incremental elige el miembro":
  Gini CV 0.441 con 8 variables, mejor en 25 de 25 folds [DATA]. Campeón = D10.2; pregunta G2-3.
- **D10.3 · Transferencias externas fuera del campeón.** El cluster de transferencias externas (incluye
  `transfer_to_competitor_pct_90d`, IV 0.305) aporta ΔGini > 0 en solo 64–72% de los folds una vez que están
  `share_of_wallet` y `outflow_x_contact_gap` [DATA]: su información ya está en el modelo. Sigue disponible como
  override en el paso 12 (≥ 10%).
- **D10.4 · Challenger.** 70 candidatas → 14 redundantes (|ρ| > 0.75) → 40 sin permutation importance estable → 16
  variables [DATA], incluido `multi_signal_count` (compuesto, permitido en challenger por I-3).

- **D11.1 · Comparación en dev.** Campeón y challenger se comparan en la CV 5×5 de dev (mismos folds, pareado). Los
  criterios H-2 que exigen validación (caída dev→val, PSI por tramo, Brier tras Platt) se miden una sola vez en los
  pasos 13–14; el holdout no se usa para elegir aquí.
- **D11.2 · Campeón estimado.** 8 variables, todos los β > 0 (p < 0.001), VIF máx 1.38; intercepto corregido 1.807.
  CV anidada: Gini 0.429, PR-AUC 0.344, b = 0.94; media de p en dev 13.94% vs tasa B 13.88%; reason codes top 1
  estables en 91.7% [DATA]. Con target A: AUC 0.751 (mismas variables) [DATA].
- **D11.3 · Challenger.** XGBoost monotónico, 150 trials (0 podados), prof. 3, 69 árboles; Gini 0.431, PR-AUC 0.363,
  b = 0.98; 3 semillas con PR-AUC 0.3623–0.3630; EBM y variante WoE equivalentes; 0 violaciones de monotonía [DATA].
  `scale_pos_weight` con probabilidad corregida por prior (logit − ln spw).
- **D11.4 · Recomendación.** Challenger no cumple 4 criterios H-2 evaluables: ΔGini +0.002 (< 0.05), ΔPR-AUC +0.019
  (< 0.03), sobreajuste 0.047 vs 0.018, reason codes top 1 77.0% con signo 99.9% (< 100%) [DATA]. Sí mejora la captura
  de RV de eventos en el decil 1 (0.335 vs 0.284) [DATA]. Interacciones > 20% de |φ| en 10 de 16 variables (24.0%
  global) [DATA]: documentadas, sin restricción (el challenger no se promueve). Default: campeón a pasos 12–14;
  challenger como referencia, evaluado una vez en validación en el paso 13. Pregunta G2-4.

- **D12.1 · Probabilidad pre-calibración.** Los tramos se definen por score (orden) en dev; la probabilidad mostrada en
  el paso 12 es la del modelo con intercepto corregido. Platt sobre validación (paso 14) cambia la probabilidad, no el
  orden ni los cortes.
- **D12.2 · Eventos mínimos por tramo en dev.** "≥ 30 eventos por tramo en validación" se traduce a ≥ 70 en dev
  (30 × 1,871/803) para diseñar sin mirar validación; se verifica en validación en el paso 13. Tramos elegidos por
  mayor IV de tramo entre 3,085 configuraciones factibles: Crítico 4% · Alto 17% · Vigilancia 50% · Estable 29% de dev
  (score ≤ 445 / 517 / 573) [DATA].
- **D12.3 · Overrides.** Precisión medida en los hogares que el override mueve (no en todos los que tienen la señal).
  Ninguna regla llega a Crítico sin superar 30% del tramo; `banker_change_6m_flag`, `complaint_escalated_flag` y
  `transfer_to_competitor_pct_90d ≥ 10%` → Alto (precisión 13.5% / 17.3% / 14.9%); `trustee_change_flag` eliminada
  (11.7%) [DATA]. Cada regla ≤ 30% del tramo, pero la unión mueve 848 hogares = 36.3% del Alto del modelo [DATA]:
  pregunta G3.
- **D12.4 · Bandas.** Cortes por eventos acumulados dentro de cada tramo con ≥ 70 eventos por banda en dev; quedan 6
  bandas (CCC/D, B, BB, BBB, AA, AAA); Estable no alcanza para 3 bandas [DATA].
- **D12.5 · Bins no observados en dev.** Hogares con antigüedad < 1 (fuera de población) tienen "sin dato" en 4
  variables que en dev no lo tenían: 0 puntos (neutral), fila explícita en el lookup [DATA].

- **D13.1 · Validación aprobada.** Holdout usado una vez con el campeón final: Gini val 0.390 vs dev 0.444 (caída 12.1%
  ≤ 15%); PR-AUC 0.328; KS 0.282; tramos monótonos en val (55.6% / 21.1% / 11.1% / 5.8%), PSI por tramo 0.0003,
  lift Crítico/Estable 9.5x, ≥ 52 eventos por banda, overrides con precisión 14.4–24.4% en val; UHNW Gini 0.394 con
  53 eventos (solo global). Target A: AUC val 0.743 [DATA]. 9 de 9 criterios cumplidos. El Gini de val (0.390) queda
  también por debajo del de la CV anidada (0.429) [DATA]: se reporta, sin re-ajustar (holdout tocado una vez).

## Limitaciones registradas
- **L1** Sin OOT ni cohortes ni PSI temporal (un solo snapshot 2025-12-31) [DATA].
- **L2** Señales pre-ingenierizadas sin timestamps auditables; se asume as-of T0.
- **L4** Dataset sintético: nada se presenta como resultado de un banco real.

## G0 · respuesta del usuario (2026-09-29)
- "usa defaults" → I-1 a I-10 y G0-a con su default, marcados [DEF-default] en la tabla de parámetros.

## G1 · respuesta del usuario (2026-09-29)
- "usa defaults" → G1-1 a G1-4 con su default ([DEF-default] en la tabla de parámetros).

## G2 · respuesta del usuario (2026-09-29)
- "1. sí 2. sí un sólo modelo, 3. aceptar ajuste 4. sí, sólo quiero ver como se ve el ML con respecto a la probabilidad
  de ajuste y ya, después de los random trees y las pruebas" → G2-1 a G2-4 [DEF]. Se agrega la vista 11C (ajuste de
  probabilidad por decil de XGBoost, EBM y random forest vs campeón, OOF de dev); el ML no sigue a los pasos 12–17.
- **D11.5 · Vista 11C.** XGBoost y EBM se ajustan mejor que el campeón en dev (ECE 0.6 y 0.4 pp vs 1.1 pp; b 0.98 y
  0.99 vs 0.93); el random forest crudo sobrestima (media p 40.5% vs 13.9%, ECE 26.6 pp) por sus pesos balanceados y,
  corregido por prior, subestima el decil superior (34.8% vs 42.1%) [DATA]. El campeón se calibra en el paso 14.

## Preguntas abiertas
- Ninguna. Las de G3 se abrirán al cerrar el paso 14.
