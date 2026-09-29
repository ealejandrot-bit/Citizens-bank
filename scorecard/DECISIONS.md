# Registro de decisiones

Formato: fecha · paso · decisión · alternativas descartadas · motivo.

## 2026-09-29 · Paso 0

**D0.1 · Fuente de datos en CSV, no XLSX.** El brief indica `./data/client_pulse_synthetic.xlsx`; ese archivo no
existe. La base está en `data/synthetic/client_pulse_synthetic.csv` (salida del generador del repo) y cumple los
35 hechos de la sección DATOS. Se lee en solo lectura; la ruta es configurable con `DATA_PATH`.
- Descartado: convertir a XLSX (duplica la fuente y abre la puerta a divergencias).

**D0.2 · Proyecto en `scorecard/`.** El repo ya contiene el generador sintético (`synthetic/`, `scripts/`, `docs/`,
`requirements.txt`). El scorecard vive en su propia carpeta con su `requirements.txt` congelado para no mezclar
dependencias; los modelos 2 (ML) y 3 (redes) seguirán el mismo patrón.
- Descartado: estructura en la raíz (colisiona con `README.md`, `requirements.txt` y `data/` existentes).

**D0.3 · Condición de missing del bloque 40–74%.** Verificada por crosstab contra los `has_*`:
- `salary_deposit_stopped_flag` ⇐ `has_payroll_stream` = False (0 violaciones; 232 NaN extra con nómina = patrón no detectado).
- `return_vs_benchmark` ⇐ `has_advisory` = False (0 violaciones; 251 NaN extra con advisory).
- `client_reply_rate`, `meetings_cancelled_by_client`, `relationship_dissatisfaction_flag`,
  `fixed_income_maturity_not_reinvested`: ningún `has_*` explica el missing (concordancia máx. 52–61%). La condición
  es operativa y **no observable en la base** (< 3 contactos, campo no registrado por el banker, fuera del piloto
  del Assistant, sin vencimientos), según el diccionario del generador (`synthetic/schema.py`). Se tratarán como
  bin "sin dato" propio, no como "no aplica".

**D0.4 · WARN `pension_deposit_stopped_flag`.** 134 hogares con `has_pension_stream` = False tienen valor (siempre 0)
en vez de NaN; 124 de ellos tienen `history_months` = 24. Interpretación: el detector de patrones marcó una
pensión que el flag de estructura no reconoce. Impacto nulo en señal (todos 0 = "no se detuvo"). Propuesta: en el
paso 3 recodificar a "no aplica" cuando `has_pension_stream` = False, documentado. No se detiene el pipeline:
el hecho del brief se cumple en 99.3% de los casos y la dirección de la excepción es benigna.

**D0.5 · Parámetros confirmados por el usuario (2026-09-29).** Target primario `hard_churn_6m`; capacidad Crítico =
top 3% (default, sin dato de banqueros). Instrucción: base sintética → documentar inconsistencias y seguir con los
datos tal cual; **no mover la concentración de valor** (hay hogares que concentran mucho más capital).

## 2026-09-29 · Paso 1

**D1.1 · Dos medidas de churn por valor.** (i) Σ RV de hogares con evento ÷ Σ RV (valor en riesgo) y (ii) Σ
`value_lost_6m` ÷ Σ RV (valor efectivamente perdido). En hard churn coinciden (pérdida total: `value_lost_6m` =
RV en el 100% de los eventos); en soft churn (ii) ≈ 40% de (i) (pérdida mediana 39.8% del RV).
- Descartado: `aum` como base de valor (missing estructural en 14.4%, sesga contra hogares solo depósitos).

**D1.2 · Intervalos bootstrap sin tocar el estimador.** 500 réplicas de hogares estratificadas por segmento; IC 95%
percentil. El estimador puntual usa RV crudo; el IC solo muestra la dependencia de pocos hogares grandes (un solo
hogar hard = 4.96% del valor perdido).
- Descartado: winsorizar o recortar RV para estabilizar la tasa (cambia la concentración; instrucción D0.5).

**D1.3 · Excluidos.** Los 123 `churn_excluded` (muerte / reubicación; 0.66% del RV) salen de entrenamiento y
métricas y se conservan en el archivo de scoring con bandera. Sin censura ni tiempo al evento: corte único, cada
hogar tiene ventana completa de 6m (hard) y 3m (soft) desde T0.

## 2026-09-29 · Paso 2

**D2.1 · Dirección esperada "?" en nivel patrimonial, `segment`, `age_primary` e `history_months`.** No hay
hipótesis de negocio defendible del signo; se deja a los datos (el binning monótono `auto_asc_desc` elige).
**D2.2 · Elegibles con revisión regulatoria:** `age_primary` (fair lending / UDAAP) y `bureau_new_mortgage_elsewhere`
(FCRA, propósito permisible). Se decide en el paso 10.

## 2026-09-29 · Paso 3

**D3.1 · Sin capping en ninguna variable.** El brief permitía capping p1/p99 para estabilidad de bins; no se usa:
(a) instrucción D0.5 para `relationship_value`; (b) `optbinning` pre-bina por cuantiles, invariante a transformaciones
monótonas de las colas, así que el capping no cambia los bins. Los 2 hogares "extraordinarios" (RV > $712M, 0.8% del
RV) son consistentes (identidad y segmento cuadran) y se conservan.
- Descartado: winsorizar p1/p99; eliminar outliers; log-transformar para el modelo (irrelevante con WoE).

**D3.2 · Taxonomía de missing para el binning.** "No aplica" (estructural, ligado a `has_*`) ≠ "sin dato" (historia
corta, condición operativa, patrón no detectado, saldo base < $10k). Cada uno tendrá bin propio cuando haya volumen.

**D3.3 · Inconsistencias documentadas, sin corregir la fuente** (tratamiento en la construcción de features, paso 5):
- `pension_deposit_stopped_flag` con valor 0 en 134 hogares sin `has_pension_stream` → se recodifica a "no aplica".
- `salary_deposit_stopped_flag` NaN en 232 hogares con nómina (patrón no detectado) → "sin dato", no "no aplica".
  Análogo en `business_payroll_stopped_flag` (64) y `recurring_deposit_*` (~150).
- `history_months` ≠ min(24, ⌊tenure·12⌋) en 61 hogares, todos por ±1 mes (redondeo) → se ignora.
- `history_months` = 0 en 5 hogares (recién abiertos) → se conservan; sus señales de ventana son "sin dato".
- `salary_deposit_stopped_flag` = 1 con `recurring_deposit_stopped_flag` = 0 en 11 hogares → coherente con el umbral
  de #4 (flujo ≥ 10% del ingreso); se conserva.
- `contact_gap_ratio` = −0.0 en 561 hogares → cosmético, equivale a 0.
- Ratios > 100% del saldo (p. ej. 628 hogares con transferencias 60d > 100% del saldo promedio) → plausibles
  (el denominador es un promedio y puede haber entradas); se conservan, el binning los absorbe en el bin extremo.

## 2026-09-29 · Mejoras al plan aprobadas por el usuario

**DM.1 · El holdout solo evalúa; nada se ajusta en él.** El brief ajustaba Platt en el holdout (con CV interna) y
validaba en el mismo holdout, lo que sesga la validación hacia el optimismo. Cambio:
- Paso 14: Platt (a, b), shift de intercepto y shrinkage por tramo se ajustan sobre **predicciones out-of-fold (OOF)
  de la CV 5×5 en desarrollo** (promedio de las 5 repeticiones por hogar). El holdout solo mide b, Brier y
  esperado vs observado.
- Mismo principio para lo que depende de la etiqueta: cortes de tramo (paso 12) y precisión/asignación de overrides
  (paso 12) se deciden con OOF de desarrollo y se **reportan** en holdout. Si un criterio (p. ej. ≥ 30 eventos por
  tramo) no se cumple en holdout, se reporta como hallazgo; no se recorta en holdout.
- Descartado: ajustar en holdout con CV interna (el brief). Descartado también partir el holdout en calibración y
  prueba (reduce el holdout a ~180 eventos hard y deja UHNW con ~12).

**DM.2 · Revisión FCRA de `bureau_new_mortgage_elsewhere` (paso 10).** Además del criterio de fair lending, se
evalúa: (a) propósito permisible (FCRA §604) para usar datos de buró en un modelo de retención/marketing; (b) que el
missing (5.04%, hogares sin propósito permisible o sin aprobación legal) no se convierta en un proxy; (c) el aporte
incremental del modelo con y sin la variable. Si no hay base legal documentada, sale del campeón y queda como
sensibilidad.

## 2026-09-29 · Paso 4

**D4.1 · Split 70/30 estratificado por `hard_churn_6m` × `segment`, semilla 42; CV 5×5 (RepeatedStratifiedKFold)
en desarrollo con la misma estratificación.** Folds guardados en `04_split.csv` (`cv_r1`–`cv_r5`) para que todos
los pasos usen exactamente las mismas particiones y las predicciones OOF (DM.1) sean trazables.
- Descartado: estratificar también por quintil de RV (reduce la varianza del churn por valor entre muestras, pero
  la instrucción D0.5 pide no intervenir la concentración; se reporta la diferencia: 6.62% dev vs 6.07% holdout).
- Descartado: OOT (corte único). La CV repetida sustituye solo parcialmente la estabilidad temporal (limitación).
- Hallazgo: holdout con 24 eventos hard UHNW y ~11–12 por fold de CV → métricas UHNW con intervalos anchos.

## 2026-09-29 · Paso 5

**D5.1 · Razón de missing como variable auxiliar** (`<var>__miss` ∈ ok / no_aplica / sin_dato) para 35 predictores.
El paso 9 la usa como bin propio. El missing es informativo: `client_reply_rate` sin dato (< 3 contactos) tiene tasa
hard 8.55% vs 3.72% con dato.
- Descartado: imputar (mediana, 0 o modelo); destruye la señal del missing y mezcla "no aplica" con "sin dato".

**D5.2 · `aum_outflow_to_rv_90d` = `aum_outflow_90d` ÷ RV; 0 sin inversiones.** Permite comparar la salida de AUM
entre hogares con y sin inversiones. El QC original exigía ∈ [0, 1]; falló (máx. 10.3) porque el denominador es RV en
T0, ya neto de la salida: 258 hogares sacaron en 90d más de lo que les queda (tasa hard 33.3%, 5.5× la base). Es
señal legítima (información ≤ T0), no error: el control se corrigió a ≥ 0 y el caso queda como WARN informativo.
- Descartado: usar RV previo como denominador (no está en la base); recortar la razón a 1 (pierde la señal).

**D5.3 · `log_relationship_value`** solo para legibilidad de gráficas y clustering (paso 7); en el WoE es
equivalente a RV. **Conteo propio de señales** (33 umbrales del Excel, 7 grupos): ρ = 0.978 con `multi_signal_count`
y 93.8% de coincidencia exacta; las diferencias vienen de columnas que no están en la base (destinos nuevos 30d,
umbrales de aceleración / HHI, monto no reinvertido, % de reuniones canceladas, fuera de SLA). Solo diagnóstico.

**D5.4 · Huecos de tipo de feature** (para el equipo de datos; no se crean features nuevas porque la base no trae las
series): sin tendencia en externalización; sin aceleración fuera de transferencias; sin persistencia en salida de
activos, ingresos y banquero; rendimiento con una sola variable; relación con banquero sin cambio vs baseline.

## 2026-09-29 · Paso 6

**D6.1 · Univariado solo en desarrollo.** El holdout no se mira hasta el paso 13 (DM.1).
**D6.2 · Dos medidas de efecto.** δ de Cliff (no paramétrica, robusta a colas) para continuas; **risk ratio con IC 95%
y Fisher** para binarias y variables infladas en su mínimo (≥ 70% en el mínimo). Motivo: con prevalencia p, |δ| ≤ p,
así que δ califica como "despreciable" un flag con lift 4.9× (`salary_deposit_stopped_flag`: δ = 0.145, RR = 5.6).
Umbrales RR: fuerte ≥ 2, moderado ≥ 1.5, con IC inferior > 1.
- Descartado: solo δ (brief); solo d de Cohen (asume normalidad, inválido con colas pesadas y ceros).
**D6.3 · Lift máximo por grupo con ≥ 30 eventos** (mismo mínimo que un bin) para no leer lifts de celdas chicas.

## 2026-09-29 · Paso 7

**D7.1 · Regla de K fijada antes de ver resultados:** entre K con cluster mínimo ≥ 5% y ARI bootstrap medio ≥ 0.80,
mayor silhouette. Resultado K = 3 (silhouette 0.191, ARI 0.992, mínimo 14.4%). K = 4–8 fallan estabilidad (ARI ≤ 0.85,
p5 ≤ 0.58).
- Descartado: GMM como método principal. Con 8 binarias la verosimilitud diagonal no está acotada y el BIC decrece
  sin fin (de 187,300 en K = 2 a −275,088 en K = 8); solo coincide con K-means en K = 3 (ARI 0.83).
- Descartado: k-prototypes / Gower (más adecuado para datos mixtos, pero K-means sobre binarias estandarizadas da
  clusters estables e interpretables y es reproducible con sklearn). Queda como alternativa.
**D7.2 · Sin modelos separados.** UHNW 80 eventos < 100; `segment` entra forzado; cluster = candidata del paso 9.
**D7.3 · Hallazgo: la estructura no separa riesgo.** Tasa hard 6.04% / 6.08% / 5.95% por cluster (χ² p = 0.98), en
línea con el paso 6 (has_*, edad, antigüedad, RV: todos despreciables). En esta base el churn lo explican las señales
de comportamiento, no el perfil. Se espera que cluster no pase IV ≥ 0.02; si no pasa, sale por evidencia.

## 2026-09-29 · Paso 8

**D8.1 · Correlación y VIF sobre rangos.** Spearman por pares con dato en ambas (mín. 200). VIF diagnóstico sobre
rangos normalizados (missing → mediana); el VIF que decide es el de WoE (paso 10).
- Descartado: Pearson / VIF sobre valores crudos (colas de hasta 6,390× dominan la covarianza).
**D8.2 · Información incremental por par** = ΔAUC (CV, 5 folds de `cv_r1`) de una logística con las dos variables vs
la mejor sola. Δ < 0.005 → redundantes. Ninguna se elimina aquí: la elección de representante es del paso 10.
**D8.3 · PCA solo diagnóstico.** No entra en selección ni en modelo (pierde interpretabilidad y monotonicidad).

## 2026-09-29 · Paso 9

**D9.1 · Tamaño mínimo de bin diferenciado (desvío del brief).** El brief fija ≥ 5% de población por bin. Con esa regla,
8 flags con RR ≥ 3 en el paso 6 quedarían fusionados en un solo bin (IV ≈ 0): `salary_deposit_stopped_flag` (1.9% de
hogares, 77 eventos, RR 5.6), `repeat_complaint_flag` (3.7%), `bureau_new_mortgage_elsewhere` (3.7%),
`recurring_deposit_stopped_flag` (3.8%), `trustee_change_flag` (1.4%), `business_payroll_stopped_flag` (1.4%),
`pension_deposit_stopped_flag` (0.7%), `relationship_dissatisfaction_flag` (1.2%). Regla adoptada: 5% en continuas;
1% en binarias, conteos y variables infladas en su mínimo; **≥ 30 eventos por bin en todas** (el mínimo que da un
WoE estimable). Pensión (27 eventos) e insatisfacción (26) no alcanzan ni así → IV 0 en el scorecard; pasan a
candidatas de override (paso 12), donde se evalúa su precisión.
- Descartado: 5% para todo (pierde las señales más fuertes); sin mínimo de población (bins de 30 eventos y < 1%
  inestables).
**D9.2 · Estabilidad de WoE.** Bins fijos de desarrollo, WoE recalculado en los 25 conjuntos de entrenamiento de la CV
5×5. Inestable = sd > 0.25 y signo distinto al de la mediana en > 20% de los folds → se elimina el corte con el
vecino de WoE más cercano. Resultado: 0 bins inestables; sd máx. 0.098 (`complaint_age_days`).
**D9.3 · Bins especiales pequeños.** "sin dato" con < 30 eventos se fusiona con "no aplica" si existe; si el grupo
sigue con < 30 eventos → WoE = 0 (neutral): no hay datos para asignar riesgo y un WoE de 5–10 eventos es ruido.
Costo: se pierde la señal de missing en variables con poco "sin dato" (p. ej. `banker_change_6m_flag` sin dato:
75 hogares, 9 eventos, 12%).
**D9.4 · `log_relationship_value` no se bina** (mismo WoE que `relationship_value`).
**D9.5 · Búsqueda de pre-binning.** `optbinning` con `min_prebin_size` = 1% no encontró cortes en
`positions_liquidated_pct` (87% en cero, empates). Se prueban 1%, 2% y 5% y se queda el de mayor IV; todos cumplen las
mismas restricciones (monotonía, 30 eventos, tamaño). `positions_liquidated_pct` pasa de IV 0 a 0.146.
- Riesgo: leve optimismo del IV por elegir el máximo de 3; se controla con la estabilidad entre folds y con la
  validación en holdout (paso 13).

## 2026-09-29 · Paso 10

**D10.1 · Embudo:** IV ≥ 0.02 (38) → exclusión regulatoria (37) → clustering jerárquico promedio sobre 1 − |Spearman|
de los WoE, corte |ρ| > 0.6, representante = mayor IV (30) → VIF < 5 sobre WoE (30; ninguna > 5 tras el clustering)
→ LASSO L1 en la CV 5×5, C por regla 1-SE (C = 0.1) → regla de cierre (12 señales + `segment`).
**D10.2 · Revisión regulatoria (DM.2).**
- `bureau_new_mortgage_elsewhere` (IV 0.125): sin base legal documentada de propósito permisible (FCRA §604); su bin
  "sin dato" (712 hogares sin propósito permisible / sin aprobación, tasa 7.3%) tendría WoE −0.204, es decir, la falta
  de permiso daría puntos de riesgo (proxy indebido); ΔAUC CV por incluirla −0.0005. **Fuera del campeón**, se
  reporta como modelo de sensibilidad (paso 11).
- `age_primary` (IV 0.003): fuera por evidencia y por criterio de fair lending. Proxy de edad: |ρ| máx entre los WoE
  finales y la edad = 0.043 (sin proxy).
**D10.3 · Regla de cierre revisada (transparencia).** La regla inicial (orden por frecuencia L1 y luego IV) se fijó
antes de ver resultados, pero en C_1SE 13 variables empataron en 100% de frecuencia y el tope de 12 dejó fuera toda la
dimensión "deterioro de saldos" (incl. `deposit_balance_vs_6m_avg_pct`, IV 0.349), contra el requisito de diversidad
del brief. Se revisó a "diversidad primero": la de mayor IV de cada dimensión de señal / nivel, luego relleno por IV,
≤ 3 por dimensión. AUC CV: v1 0.7717 vs v2 0.7710 (dentro de 1 sd = 0.016). Ambas se reportan.
- Nota: las AUC de este paso usan WoE de todo desarrollo (optimistas ~0.008; ver D11.1).

## 2026-09-29 · Paso 11

**D11.1 · CV anidada.** Con WoE ajustado en todo desarrollo, la CV ve las etiquetas del fold de prueba: AUC 0.772
(optimista) vs **0.764 con bins re-ajustados dentro de cada fold**. Las OOF para calibrar (DM.1) salen de la versión
anidada. Descartado: usar las OOF optimistas (sesgarían Platt hacia probabilidades más extremas).
**D11.2 · Interacción UHNW × top-3** (cambio de banquero, transferencias externas, productos cerrados): ΔAUC −0.0007,
mejora en 12% de los folds, β de interacción no significativos (p ≥ 0.60) → no se incluye.
**D11.3 · Eliminación hacia atrás p > 0.05** (sin tocar forzadas): salen `deposit_balance_vs_6m_avg_pct` (p = 0.56, su
información ya la cubren SOW y transferencias externas) y `transfer_to_competitor_bank_amount_90d` (p = 0.09). AUC
anidado 0.7629 → 0.7637: no se pierde nada. Consecuencia: "deterioro de saldos" queda sin variable propia; se acepta
porque la evidencia condicional dice que no aporta, y la diversidad del brief sigue en 8 dimensiones de señal.
**D11.4 · Dos versiones del scorecard (pedido del usuario: explicable a la alta dirección).**
- Regla A-lite fijada antes de ver resultados: forward selection con CV anidada sobre las variables de A (`segment`
  forzada); el modelo más chico con AUC anidado ≥ AUC(A) − 0.01. Resultado: 4 señales (cambio de banquero, tasa de
  respuesta al banquero, transferencias externas, share of wallet) + `segment`.
- Regla de campeón: A-lite solo si además en holdout el IC pareado de Δ incluye 0 o la brecha ≤ 0.01. Resultado:
  brecha holdout 0.012, IC [−0.024, −0.001] → **A campeón operativo; A-lite versión ejecutiva**. Por pedido del
  usuario, ambas se escalan, validan y calibran en los pasos 12–15.
**D11.5 · Campeón vs challenger.** LightGBM monótono (53 variables crudas, 107 árboles) no supera a A: ΔAUC holdout
−0.002 [−0.012, +0.008], ΔPR-AUC +0.006 [−0.009, +0.019]; la regla exige +0.03 / +0.05 sin traslape. A campeón; costo
de explicabilidad de B: sin tabla de puntos, drivers solo vía SHAP.
**D11.6 · `segment` forzada con β inestable.** β = 2.06 (MLE) vs 1.33 (L2): su WoE es ≈ ±0.02 (IV 0.003), así que la
contribución al logit es chica (0.10) aunque β sea grande. Se mantiene por diseño (calibración por segmento).
**D11.7 · Hallazgo: holdout más difícil que la CV.** AUC holdout 0.725 vs 0.764 anidado; B muestra la misma brecha
(0.722 vs 0.758), así que no es sobreajuste específico de A sino variación de muestra (360 eventos; IC ±0.03). Se
revisa con PSI desarrollo vs holdout en el paso 15. Pendiente de calibración en holdout 0.84 → se corrige en el paso 14.

## 2026-09-29 · Paso 12

**D12.1 · Escala y puntos enteros.** Factor = 40/ln 2 = 57.71; Offset = 600 − 57.71·ln 15 = 443.72. Puntos por bin
redondeados a entero (tabla legible para dirección); score oficial = Σ puntos enteros; error de redondeo ≤ n/2 puntos
(5.5 en A, 2.5 en A-lite). La probabilidad sale de la calibración, no del score.
**D12.2 · Tramos decididos con OOF de desarrollo (DM.1).** Platt (capa modelo) ajustado sobre OOF anidadas:
A a = −0.089, b = 0.962; A-lite a = −0.054, b = 0.977 (el paso 14 lo valida). Crítico = top 3%. Búsqueda en rejilla
de los otros dos cortes con restricciones del brief (salto ≥ 2×, lift C/E ≥ 5×, ≥ 70 eventos por tramo en desarrollo).
- Regla inicial de elección (más hogares en Estable) **revisada**: elegía cortes al borde de la factibilidad
  (Vigilancia de 4.3% y 15 eventos en holdout; saltos 1.89× y 1.49× en holdout). Regla adoptada: máximo margen de
  separación (ratio contiguo mínimo), desempate por Estable más grande. Cortes A: p_cal ≥ 26.2% / 7.2% / 3.0%
  (3% / 19% / 66% acumulado). A-lite: 23.0% / 5.9% / 3.0%.
- Hallazgo: en holdout A cumple lift (13.8×) pero el salto Vigilancia/Estable es 1.82× y Alto/Vigilancia 1.99×;
  no se reajusta sobre el holdout (DM.1). Consistente con D11.7.
**D12.3 · Overrides decididos en desarrollo.** Precisión ≥ 25% → Crítico; 12–25% → Alto; < 12% → fuera; una regla que
aportaría > 30% del tramo baja un nivel o sale. Resultado A: pensión detenida → Crítico (29.0% dev / 37.5% holdout);
transferencias a competidores ≥ 10% (30.3%, bajó de Crítico a Alto por aportar > 30% del Crítico), cambio de banquero,
queja escalada, queja repetida, insatisfacción, cambio de trustee y ≥ 2 destinos nuevos → Alto (15.9–21.8%). Ninguna
eliminada. En conjunto los overrides aportan 34% del Alto en holdout (457 de 1,361): la regla del brief es por regla, no
agregada; se reporta para decisión de capacidad.
**D12.4 · `segment` fuera de reason codes.** Es estructural y no accionable; con β inestable (D11.6) su bin UHNW resta
26 puntos y aparecía como driver ("riesgo por ser UHNW"). Sigue dentro del score por diseño.
**D12.5 · Etiquetas legibles** en lookup y reason codes (sí/no, rangos con %, "sin dato", "no aplica").
**D12.6 · Capacidad fija en Alto (decisión del usuario, 2026-09-29: opción b).** Sin capacidad, Alto quedaba en 22.8%
de la cartera (~4,600 hogares con SLA de 15 días; un tercio por override). Ahora Alto = **10% de la cartera**
(parámetro `alto_capacity_pct`; supuesto: SLA 3× el de Crítico → ~3× su volumen; el usuario no tiene el dato y puede
cambiarlo). El cupo se ocupa por prioridad = max(p_cal, precisión en desarrollo del override activo), acotada bajo el
corte de Crítico; lo que no cabe baja a Vigilancia. Regla ≤ 30% del tramo por override, aplicada sobre el cupo:
salen `banker_change_6m_flag` y `complaint_escalated_flag` (cada una ocuparía > 30% del Alto; su señal sigue en el
score, cambio de banquero es la variable de más peso). Reemplaza el resultado de overrides de D12.3.
Resultado A (holdout): Alto 10.2% de hogares, churn 11.4% (antes 9.0%); saltos 2.99× / 2.18× / 1.89× (en desarrollo
2.57× / 2.60× / 2.82×); lift Crítico/Estable 12.3×. En conjunto los overrides son 47% del Alto en holdout (282 de 606).
- Descartado: Alto sin capacidad (opción a); cupo ocupado solo por p_cal (dejaría fuera overrides con precisión
  20–33%, mayor que la del margen del modelo, ~12%).

## 2026-09-29 · Paso 13

**D13.1 · Criterios de aprobación** (fijados antes de calcularlos; umbrales estándar de la práctica, no ajustados a
los resultados): C1 supera a `multi_signal_count` y `multi_signal_flag` en AUC y captura del decil top con IC sin
traslape [GATE, del brief]; C2 AUC holdout IC inferior > 0.65; C3 KS ≥ 0.25; C4 captura decil top ≥ 30%; C5 captura de
valor decil top ≥ 25%; C6 tasa por decil monótona (Spearman ≤ −0.90); C7 AUC UHNW ≥ 0.60 (informativo).
**D13.2 · KS con empates.** El KS por orden de filas es ambiguo con puntajes empatados (benchmarks discretos); se
calcula como máx(TPR − FPR) sobre umbrales únicos.
**D13.3 · QC GATE FALLIDO (C1) — pendiente de decisión del usuario.** En holdout (360 eventos) A supera a
`multi_signal_flag` sin traslape, pero frente a `multi_signal_count` los IC marginales se traslapan: AUC 0.725
[0.696, 0.757] vs 0.683 [0.653, 0.715]; captura decil top 37.7% [33.0, 42.2] vs 32.6% [28.7, 36.7]. La prueba pareada
(mismos hogares, mismas réplicas) sí es significativa: ΔAUC +0.041 [+0.015, +0.064]; Δcaptura +5.1 pp [+2.1, +8.7];
Δcaptura de valor +4.4 pp [−0.3, +9.8] (no significativa). Evidencia adicional en desarrollo (OOF anidadas, 840
eventos): AUC 0.764 [0.747, 0.779] vs 0.698 [0.678, 0.716], sin traslape. A-lite vs count en holdout: ΔAUC +0.029
[0.000, +0.053] (en el límite), Δcaptura +4.7 pp [+1.4, +7.8]. C2–C7 se cumplen en ambos modelos.
Por la regla del brief el pipeline se detiene hasta que el usuario decida el criterio.
**D13.4 · Criterio C1 cambiado por decisión del usuario (2026-09-29, opción 1).** C1 (gate) = el IC95 de la
**diferencia pareada** (mismas réplicas bootstrap sobre los mismos hogares) excluye 0 en AUC y en captura del decil top,
frente a `multi_signal_count` y `multi_signal_flag`. Motivo: el traslape de IC marginales no implica ausencia de
diferencia; con dos modelos evaluados sobre los mismos hogares la prueba correcta es pareada. El criterio original
(C1b) se sigue reportando como informativo y no se cumple frente a `multi_signal_count`.
Resultado: **A aprobado** (ΔAUC vs count [+0.015, +0.064]; Δcaptura [+2.1, +8.7] pp). **A-lite aprobado con reserva**:
ΔAUC vs count [+0.0005, +0.053] (en el 2.2% de las réplicas no supera al conteo); se mantiene como versión ejecutiva,
no como la que ordena la operación. Mensaje para dirección: la mejora sobre `multi_signal_count` es real pero moderada.

## 2026-09-29 · Paso 14

**D14.1 · Calibración ajustada solo en desarrollo (DM.1).** Platt sobre OOF anidadas (A: a = −0.089, b = 0.962;
A-lite: −0.054, 0.977). Shift de intercepto: no se aplica (en desarrollo la media calibrada = tasa; en holdout el
intercepto de ajuste −0.042 tiene IC [−0.155, +0.071] que incluye 0).
**D14.2 · Hallazgo: probabilidades algo extremas en holdout.** b de recalibración en holdout 0.876 [0.779, 0.973]
(A) y 0.856 (A-lite): dentro de 0.8–1.2 pero con IC que excluye 1. Se nota en Crítico (esperado 39.6% vs observado
34.0%; valor observado/esperado 0.64 [0.43, 0.95]) y en Estable (2.2% vs 2.8%). En desarrollo el Crítico está
calibrado (39.4% vs 38.4%). Lectura: el holdout es más difícil que desarrollo (D11.7); no se re-calibra con holdout.
Disparador: si en el primer ciclo con datos reales b < 0.9 o el Crítico observado queda bajo su Wilson 90%, se
recalibra con la cohorte nueva.
**D14.3 · Tasa oficial por tramo** = shrinkage beta-binomial (m = 30) sobre desarrollo; con N de cientos a miles el
shrinkage apenas mueve la tasa (Alto 14.28% → 14.24%). En holdout la tasa oficial de Alto (14.2%) y Estable (1.8%)
quedan fuera del Wilson 90% (11.4% [9.4, 13.7] y 2.8% [2.3, 3.4]): los cortes se eligieron maximizando la separación
en desarrollo (optimismo de selección) y el holdout separa menos. Alternativa para comunicar: usar la media de p_cal
del tramo (Alto 12.2%, dentro del Wilson) y reportar la tasa observada de holdout como rango.
**D14.4 · Valor.** Sin descalibración por tamaño: interacción con log RV en desarrollo β = −0.014 (p = 0.87) → no se
agrega. Por quintil de RV y en el top 5% la tasa esperada cae dentro del Wilson 90%; la brecha de valor se concentra en
Crítico (pocos hogares grandes: el mayor churner es 14% del valor observado del tramo).
**D14.5 · Overrides.** Todas las reglas de Alto tienen precisión en holdout (19–33%) mayor que la tasa oficial del
tramo (14.2%). Pensión detenida (Crítico): 37.5% en holdout vs tasa del tramo 38.5% (29.0% en desarrollo), por
debajo del tramo en ambas muestras → candidata a bajar a Alto en la primera revisión con datos reales.

## 2026-09-29 · Paso 15

**D15.1 · Estabilidad sin eje temporal.** PSI desarrollo vs holdout (score y variables), métricas por sub-población,
bootstrap de coeficientes y sensibilidad al re-binning. Descartado: simular un OOT partiendo por antigüedad o historia
(no es tiempo calendario; mezclaría estabilidad con segmentación).
**D15.2 · Hallazgo: la brecha CV–holdout no es de población.** PSI del score 0.003 (A) y 0.001 (A-lite); todas las
variables < 0.004. Con la misma distribución de entrada, la caída de AUC (0.764 → 0.725, D11.7) es variación de la
relación señal–churn en una muestra de 360 eventos, no cambio de población.
**D15.3 · Sub-población más débil: cluster 2 (solo depósitos).** AUC holdout 0.660 [0.562, 0.762] con 35 eventos, y
churn observado 4.1% vs esperado 6.4%; en desarrollo su AUC es 0.751. Se monitorea; no justifica un modelo aparte
(D7.2). El resto de las bandas con ≥ 20 eventos tiene AUC ≥ 0.69.
**D15.4 · `segment`:** β bootstrap [0.04, 3.39], positivo en 99.4% de réplicas pero con CV 0.39: confirma D11.6
(forzada, efecto real pequeño e impreciso).

## 2026-09-29 · Paso 16

**D16.1 · Arquetipos.** K-means sobre −WoE de 14 señales en los 840 churners de desarrollo; K = 3 (silhouette 0.274,
ARI bootstrap 0.925, mínimo 23%); K = 4 más estable (0.987) pero con menor silhouette y un cluster de 12.5%. Nombres
fijados después de ver los centroides, con reglas reproducibles (mayor riesgo en envíos a competidores → Externalización
activa; mayor riesgo en cambio de banquero → Salida con el banquero; el resto → Desenganche silencioso). El nombrado
automático inicial por "dimensión con mayor lift" se descartó: para el cluster más grande todos los lifts eran
negativos y el nombre resultante ("insatisfacción con el rendimiento") no correspondía a su perfil.
**D16.2 · Hallazgo: punto ciego del score.** El Desenganche silencioso es 49% de los churners (44% de su valor) y solo
7–10% cae en Crítico/Alto; 60–66% queda en Vigilancia. Su señal dominante es la falta de contacto (65% con < 3 contactos
del banquero en 90 días, bin "sin dato" de `client_reply_rate`; 48% en toda la cartera). Externalización activa se
detecta al 99% y Salida con el banquero al 53%. Se agrega al playbook una campaña de cobertura en Vigilancia.
**D16.3 · Etiqueta corregida.** El peor bin de `client_reply_rate` es "sin dato" (< 3 contactos en 90d), no "tasa de
respuesta baja": se etiqueta como falta de contacto del banquero, lo que convierte la acción en un tema de cobertura.
**D16.4 · Asignación de no churners.** Los hogares alertados se asignan al centroide más cercano solo para elegir la
acción; el arquetipo de un hogar sin eventos es aproximado (el centroide del Desenganche silencioso está cerca del
perfil sin señales).

## 2026-09-29 · Paso 17

**D17.1 · Gobierno.** KPIs con línea base del holdout [DATA-SINT]; disparadores: recalibración (b ∉ [0.8, 1.2] dos
trimestres o Crítico fuera de su Wilson dos ciclos), redesarrollo (PSI > 0.25 sostenido o Gini < 0.85 × 0.450 = 0.382),
revisión de variable (PSI > 0.25), revisión de overrides (precisión < tasa del tramo dos trimestres), capacidad (> 20%
de casos fuera de SLA). Roles: dueño Head of PB, desarrollo Analytics, validación independiente Model Risk, comité
mensual de retención.
