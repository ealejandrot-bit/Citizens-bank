# Gate 1 · Datos, target y muestra (pasos 1–4)

## Tests
- `python -m pytest -q` → **30 passed** (pasos 00–04).

## Resumen del bloque [DATA]
- Target B: 19,261 hogares, 2,674 eventos (13.88%); A: 19,473 hogares, 1,168 eventos (6.00%). 212 indeterminados.
- Exclusiones: 123 `churn_excluded` y 404 con antigüedad < 1 año (más riesgosos: A 7.92% vs 6.00%).
- Churn B: hogares 13.88%, RV bruto 15.19%, económico 10.15%. UHNW B 16.29% (175 eventos).
- Diccionario: 54 predictores, 5 prohibidas, 3 auxiliares; sin dimensión digital ni de vida.
- Calidad: sin duplicados ni imposibles; colas reales conservadas; excepciones estructurales ≤ 3%.
- Split 70/30: dev 13,631 (B 1,871 eventos) / val 5,842 (B 803); tasas B 13.88% / 13.90%, A 5.99% / 6.01%.
  CV 5 × 5 en dev con 373–375 eventos B por fold. Sin OOT (L1).

## Preguntas para el usuario (con default)

| # | Pregunta | Default |
|:--|:--|:--|
| G1-1 | ¿Confirmas los signos esperados de los predictores (`step02_signs_a_priori.csv`; se usan como restricciones monótonas del challenger)? 7 sin hipótesis: `segment`, `relationship_value`, `deposit_balance`, `aum`, `age_primary`, `history_months`, `recurring_income_monthly` | aceptar los signos; las 7 sin signo quedan sin restricción monótona |
| G1-2 | Los 404 clientes con < 1 año quedan fuera del desarrollo y tienen más churn. ¿Cómo se tratan en operación? | se les calcula score con bandera "fuera de población de desarrollo" y el banquero los revisa en su onboarding; no se reportan métricas del modelo sobre ellos |
| G1-3 | `age_primary` (fair lending) y `bureau_new_mortgage_elsewhere` (FCRA, propósito permisible) | ambos fuera del campeón y del challenger salvo base legal documentada; se reportan solo como sensibilidad |
| G1-4 | Hogares con `history_months` < 24 (1,013 en A) | se conservan con indicador `hist_lt24` |

Signos a priori por bloque [DATA]:
| bloque        |   + |   ? |   − |
|:--------------|----:|----:|----:|
| economía      |   0 |   0 |   1 |
| estructural   |   0 |   3 |   0 |
| patrimonial   |   0 |   4 |   3 |
| producto      |   4 |   0 |   8 |
| relación      |   3 |   0 |   2 |
| servicio      |   4 |   0 |   0 |
| transaccional |  17 |   0 |   5 |

Responde o escribe **"usa defaults"**. No avanzo al paso 5 hasta tu respuesta.
