# Decision log · Modelo 2 (ML)

Memoria del proyecto. Nada se decide fuera de este archivo. Etiquetas: `[DATA]` del archivo · `[DEF]` fijado por el
usuario · `[DEF-default]` default aplicado.

## Estado
- Último paso completado: **12** · proyecto cerrado (ML 1.0.0) · G0–G4 cerrados (2026-09-29).
- Tests: 38 / 38 PASS (pasos 00–12).

## Parámetros vigentes
| Parámetro | Valor | Etiqueta |
|:--|:--|:--|
| SPEC | `docs/SPEC.md` aprobado por el usuario | [DEF] |
| Modelos anteriores | no se borran ni se modifican; se usan para comparar (test de sha256 en cada corrida) | [DEF] |
| Target, split, holdout | los de M1: target B (θ = 0.25), dev / val y CV 5×5 heredados | [DEF-default] I-1 |
| Compuestos | permitidos, con variante sin ellos; si ΔPR-AUC < 1 sd se elige sin compuestos | [DEF-default] I-2 |
| Monotonía | obligatoria por signo de negocio (G1-1 de M1); "?" libres | [DEF-default] I-3 |
| Algoritmos | XGBoost y LightGBM; EBM y RF solo referencia | [DEF-default] I-4 |
| Calibración | OOF cruzado en dev (holdout sin tocar) | [DEF-default] I-5 |
| Tramos | cortes propios por reglas H-3 + vista a igual % de hogares que M1 | [DEF-default] I-6 |
| Si no cumple H-2 | se evalúa como complemento (paso 10) | [DEF-default] I-7 |
| Proxy de edad | prueba diagnóstica en el paso 8 | [DEF-default] I-8 |
| Escala | S₀ = 600 @ 20:1, PDO = 40 (Factor 57.71, Offset 427.12) | [DEF] heredado de M1 |
| SEED | 42 | [DEF] |
| Candidato principal | EBM monotónico sin interacciones (aditivo); XGBoost segundo candidato hasta el paso 9 | [DEF-default] G1-1 |
| Variables | 12 sin compuestos (D2.2) | [DEF-default] G1-2 |
| Umbral de reemplazo | se sigue hasta validar, con foco en uso conjunto (paso 10) | [DEF-default] G1-3 |
| Overrides ML | cambio de banquero y queja escalada → Alto; transferencia a competidor fuera (D6.2) | [DEF-default] G2-1 |
| Cola de RV y UHNW | sin ajuste; monitoreo (como G3-2/G3-3 de M1) | [DEF-default] G2-2 |
| XGBoost | segundo candidato solo como comparación hasta el paso 9 | [DEF-default] G2-3 |
| Tramos ML | cortes propios H-3 + vista a igual % que M1 | [DEF-default] G2-4 |
| Uso conjunto | se evalúa en el paso 10 (el ML no reemplaza al M1) | [DEF-default] G3-1 |
| XGBoost | retirado tras el paso 9 (documentado; cumple 4 de 8 criterios H-2) | [DEF-default] G3-2 |
| Crítico del EBM | sobrestima en val: documentar, re-calibrar con el próximo snapshot con resultados; publicar tasa observada | [DEF-default] G3-3 |
| A-lite | incluido en la comparativa (paso 9b) y en el uso conjunto (paso 10) | [DEF] G3 |
| Roles finales | M1 operativo; EBM challenger en monitoreo; A-lite ejecutivo; XGBoost retirado | [DEF-default] G4-1 |
| Regla de prioridad p×RV | propuesta al negocio como piloto con el control 12.5% del M1 | [DEF-default] G4-2 |
| Versión | ML 1.0.0 cerrada; siguiente: Modelo 3 (redes neuronales) | [DEF-default] G4-3 |

## Decisiones
- **D0.1 · Herencia por copia.** 16 archivos de `churn_scorecard/` copiados a `data/inherited/` con sha256 idéntico al
  origen [DATA]; el raw se lee desde `churn_scorecard/data/raw/` (solo lectura).
- **D0.2 · Protección de modelos anteriores.** 130 archivos de `churn_scorecard/outputs/model/` y `scorecard/outputs/`
  registrados con sha256 en `data/inherited/previous_models_sha256.json`; `tests/test_step00.py` falla si alguno cambia
  o desaparece [DATA].

- **D1.1 · Duplicados por grupo.** La regla por pares encadenaba eliminaciones (se perdía toda la familia de salidas de
  AUM). Se usan grupos con |ρ| > 0.95 en todos sus pares (enlace completo), uno por grupo con mayor IV: salen 8
  (p. ej. `relationship_value` y `log_rv` frente a `aum`; variables `_peer` frente a su base); pool = 62 [DATA].
- **D2.1 · Eliminación hacia atrás con regla 1-SE.** "No caer más de 1 sd" se aplica como 1 error estándar de la
  diferencia pareada por fold (1 sd de los folds, ~0.02, permitiría quitar casi todo) [DEF-default].
- **D2.2 · Sin compuestos.** Con compuestos: 12 variables, PR-AUC CV 0.3584; sin compuestos: 12 variables, 0.3584;
  diferencia < 1 sd ⟹ variante sin compuestos (I-2) [DATA]. Variables: `banker_change_6m_flag`, `client_reply_rate`,
  `share_of_wallet`, `transfer_to_competitor_pct_90d`, `repeat_complaint_flag`, `contact_gap_ratio`,
  `recurring_deposit_change_pct`, `return_vs_benchmark`, `cash_pct_of_portfolio_chg`, `complaint_age_days`,
  `meetings_cancelled_by_client`, `positions_liquidated_pct`.

- **D3.1 · Algoritmo.** XGBoost (prof. 2, 110 árboles) PR-AUC CV 0.3630 vs LightGBM (prof. 3, 115 árboles) 0.3645;
  diferencia ≤ 1 sd (0.019) ⟹ el más simple: XGBoost [DATA]. 3 semillas estables (0.3629–0.3637). En los mismos 5
  folds de r1: campeón M1 0.3424, EBM 0.3645, RF 0.3570, XGBoost 0.3617, LightGBM 0.3647 [DATA].
- **D3.2 · Early stopping de LightGBM.** La primera corrida detenía LightGBM en 5 árboles (el early stopping miraba el
  logloss por defecto, que empeora con los pesos de clase; b = 13.6) [DATA]. Corregido a PR-AUC y paso 3 re-ejecutado;
  XGBoost no cambia.

- **D4.1 · Explicabilidad.** EBM: aditividad exacta (error 1.8e-15), 0 interacciones, 0 violaciones de monotonía;
  reason codes top 1 estables 85.0% (top 3 89.5%), signo coherente 100%. XGBoost: aditividad 1.1e-6, interacción global
  17.9% (4 variables > 20%, documentadas, sin restricción: es segundo candidato), top 1 81.5%, signo 100% [DATA]. Las 2
  variables principales en ambos: `client_reply_rate` y `banker_change_6m_flag` (como en M1).
- **D5.1 · Calibración (OOF de dev).** EBM Platt a = 0.050, b = 1.030; XGBoost a = 0.308, b = 1.151; isotónica no mejora
  en ninguno ⟹ Platt [DATA]. Igual que M1, el quintil superior de RV queda subestimado (Σ p·RV / Σ RV eventos 0.85 EBM,
  0.82 XGBoost) y UHNW también (14.2% vs 16.3% EBM) [DATA]: se aplica la decisión G3-2/G3-3 de M1 (monitoreo).
- **D6.1 · Tramos EBM.** Cortes H-3 propios: Crítico 4% · Alto 16% · Vigilancia 56% · Estable 24% de dev (score ≤ 444 /
  519 / 578); Crítico con tasa 60.0% vs 56.6% del M1 a igual tamaño (4%) [DATA]. Vista a igual % que M1 guardada para
  el paso 10.
- **D6.2 · Overrides.** Cambio de banquero y queja escalada → Alto (precisión de movidos 13.9% / 14.1%); transferencia a
  competidor ≥ 10% eliminada: el EBM ya la incorpora y los hogares que movería tienen 2.8% de churn [DATA].
- **D6.3 · Lookup compacto y redondeo.** 6,730 bins del EBM → 323 filas uniendo bins con los mismos puntos; el
  redondeo a enteros mueve el score hasta 3.6 puntos y la probabilidad hasta 1.4 pp [DATA].

- **D7.1 · Robustez.** Orden de importancias estable en 25 folds (las 3 primeras siempre en el mismo puesto); quitar
  `client_reply_rate` baja la PR-AUC CV de 0.3644 a 0.3602 [DATA]. Por subgrupo el EBM rinde como el M1; clientes con
  1–3 años y con historia < 24 meses quedan subestimados (16.1% real vs 14.3% estimado; 16.4% vs 14.1%) [DATA].
- **D8.1 · Equidad (diagnóstico).** Las 12 variables predicen el tercil de edad con AUC 0.633 (proxy débil; lectura
  < 0.60 / 0.60–0.70 / > 0.70 [DEF-default]); marcado Crítico+Alto proporcional al churn por tercil (ratio 1.80–1.92;
  dispersión 1.07 vs 1.09 del M1) [DATA].
- **D9.1 · Validación y H-2.** En val: EBM Gini 0.406 / PR-AUC 0.343 vs M1 0.390 / 0.328; ΔGini +0.016 (IC95 −0.000 a
  +0.030) y ΔPR-AUC +0.015 (IC95 −0.001 a +0.030) [DATA]. EBM cumple 6 de 8 criterios H-2: falla ΔGini ≥ 0.05 y ΔPR-AUC
  ≥ 0.03 ⟹ no reemplaza al M1; paso 10 evalúa uso conjunto (I-7). XGBoost falla 4 (incluye caída dev→val 12.7% vs 12.1%
  y signo 99.96%). EBM en Crítico sobrestima en val (61.3% esperado vs 53.3% observado, fuera de Wilson 90%); resto de
  tramos dentro [DATA]. Top 1% de EBM: precisión 75.9% vs 63.8% del M1 [DATA].

- **D9b.1 · Comparativa con A-lite (pedido del usuario).** A-lite (5 variables, target A, `scorecard/`) no se re-ajusta:
  se usan sus scores copiados con sha256. 4,042 de los 5,779 hogares B de val estaban en su desarrollo ⟹ comparación
  justa en los 1,737 fuera del desarrollo de todos (238 eventos B, 106 A) [DATA]. Target B: PR-AUC A-lite 0.262 vs M1
  0.304 vs EBM 0.305; EBM − A-lite +0.042 (IC95 +0.013 a +0.069), M1 − A-lite +0.041; EBM − M1 +0.001 (IC95 −0.028 a
  +0.030) [DATA]. Target A: EBM 0.209, M1 0.191, A-lite 0.153 [DATA]. A-lite captura algo más de RV de eventos en el top
  10% (21.4% vs 20.3% M1 y 19.6% EBM con B) [DATA]. Subconjunto pequeño: IC amplios.

- **D10.1 · Uso conjunto.** Acuerdo de tramo M1–EBM 82.9%; hogares Crítico/Alto solo del M1: 277 (tasa 16.3%); solo
  del EBM: 139 (13.0%) [DATA]. Lente política (tramo primero, luego p×RV), captura de RV de eventos al 10% de hogares:
  M1 48.9%, M1 + orden EBM 49.4%, M1 + alerta EBM 48.9%, EBM 48.0% ⟹ empate (< 1 pp) ⟹ M1 solo (regla previa) [DATA].
  Hallazgo: ordenar por p×RV global (sin tramo primero) captura ~59–61% del RV que se va al 10% con cualquier modelo, a
  cambio de menos eventos (18–21% vs 28%) [DATA]: la regla de prioridad pesa más que el modelo; es decisión de negocio.
  En el subconjunto justo A-lite: su política captura 24.9% del RV al 10% (Crítico+Alto de A-lite = 13% de hogares).

- **D11.1 · Arquetipos.** Asignación sin reajuste de los arquetipos del M1 a los 803 eventos B de val: relación
  desatendida 33.1%, salida activa 19.3%, desgaste silencioso 47.6% [DATA]. El EBM no detecta mejor a ninguno: Crítico+Alto
  −4.9 / −2.6 / −2.6 pp vs M1 (el EBM marca 25.6% de hogares en Crítico+Alto vs 28.0% del M1); en desgaste silencioso
  deja menos en Estable (20.7% vs 24.9%) pero no sube más a Crítico+Alto [DATA]. A-lite (justo) marca 10.9% del desgaste
  silencioso en Crítico+Alto (marca solo 13% de hogares) [DATA]. El desgaste silencioso sigue siendo el punto ciego común.

- **D12.1 · Rol y cierre.** M1 1.0.0 sigue operativo; EBM (ML 1.0.0) como challenger en monitoreo con reapertura de
  la decisión de reemplazo si ΔPR-AUC ≥ +0.03 dos ciclos; A-lite para comunicación ejecutiva; XGBoost retirado.
  Manifiesto con sha256; modelos anteriores verificados intactos (130 archivos) [DATA]. Limitaciones propias L8–L11.

## Limitaciones registradas
- Heredadas de M1: L1 sin OOT; L2 señales sin timestamps; L3 compuestos sin regla; L4 dataset sintético; L5 UHNW
  sub-representado; L6 sin dimensión digital ni eventos de vida; L7 causalidad no identificable.

## G0 · respuesta del usuario (2026-09-29)
- "usa defaults, sólo no borres los modelos anteriores que los vamos a usar para comparar" → I-1 a I-8 [DEF-default];
  protección de modelos anteriores [DEF] (D0.2).

## G1 · respuesta del usuario (2026-09-29)
- "usa defaults" → G1-1 a G1-3 [DEF-default].

## G2 · respuesta del usuario (2026-09-29)
- "usa defaults" → G2-1 a G2-4 [DEF-default].

## G3 · respuesta del usuario (2026-09-29)
- "me encanta, pero incluye en la comparativa A-lite" → G3-1 a G3-3 [DEF-default]; A-lite agregado (paso 9b, D9b.1).
- "sí documenta, y vamos al que sigue" → se documenta y se sigue al paso 10.

## G4 · respuesta del usuario (2026-09-29)
- "yes default" → G4-1 a G4-3 [DEF-default]. Versión ML 1.0.0 cerrada.

## Preguntas abiertas
- Ninguna con el usuario; las del equipo de datos en `reports/model_document.md` §6.
