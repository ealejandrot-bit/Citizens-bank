# Decision log · Modelo 2 (ML)

Memoria del proyecto. Nada se decide fuera de este archivo. Etiquetas: `[DATA]` del archivo · `[DEF]` fijado por el
usuario · `[DEF-default]` default aplicado.

## Estado
- Último paso completado: **2** · G0 cerrado ("usa defaults", 2026-09-29) · bloque en curso: pasos 1–3 (G1).
- Tests: 9 / 9 PASS (pasos 00–02).

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

## Limitaciones registradas
- Heredadas de M1: L1 sin OOT; L2 señales sin timestamps; L3 compuestos sin regla; L4 dataset sintético; L5 UHNW
  sub-representado; L6 sin dimensión digital ni eventos de vida; L7 causalidad no identificable.

## G0 · respuesta del usuario (2026-09-29)
- "usa defaults, sólo no borres los modelos anteriores que los vamos a usar para comparar" → I-1 a I-8 [DEF-default];
  protección de modelos anteriores [DEF] (D0.2).

## Preguntas abiertas
- Ninguna. Las de G1 se abrirán al cerrar el paso 3.
