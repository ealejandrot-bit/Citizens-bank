# Decision log · Modelo 2 (ML)

Memoria del proyecto. Nada se decide fuera de este archivo. Etiquetas: `[DATA]` del archivo · `[DEF]` fijado por el
usuario · `[DEF-default]` default aplicado.

## Estado
- Último paso completado: **6** · G0–G1 cerrados ("usa defaults", 2026-09-29) · G2 abierto, esperando respuesta.
- Tests: 21 / 21 PASS (pasos 00–06).

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

## Limitaciones registradas
- Heredadas de M1: L1 sin OOT; L2 señales sin timestamps; L3 compuestos sin regla; L4 dataset sintético; L5 UHNW
  sub-representado; L6 sin dimensión digital ni eventos de vida; L7 causalidad no identificable.

## G0 · respuesta del usuario (2026-09-29)
- "usa defaults, sólo no borres los modelos anteriores que los vamos a usar para comparar" → I-1 a I-8 [DEF-default];
  protección de modelos anteriores [DEF] (D0.2).

## G1 · respuesta del usuario (2026-09-29)
- "usa defaults" → G1-1 a G1-3 [DEF-default].

## Preguntas abiertas
- G2-1 a G2-4 en `reports/gate_2.md`.
