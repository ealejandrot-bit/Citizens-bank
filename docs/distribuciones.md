# Distribuciones por variable

Estado: **Paso 0 y Paso 1 construidos y validados** (variables 1, 2, 17, 18). El resto es una
**propuesta para revisión**, todavía no generada. Ajustes D-13 aplicados; ν = 6.

## Cómo se genera cada variable (patrón común)

Cada variable del Excel sale de uno o dos factores latentes del hogar
(`outflow`, `neglect`, `service`, ver `decisiones.md` D-02) más ruido propio.
Nunca sale del target. Se usan cinco familias:

| Familia | Para qué tipo de variable | Forma |
|---|---|---|
| **Bernoulli-logit** | Flags binarios | P(flag = 1) = logit⁻¹(a + b·z). `a` fija la tasa base, `b` la fuerza predictiva |
| **Hurdle** (valla) | Montos y % que muchas veces valen 0 | Parte 1: ¿ocurre? (Bernoulli-logit). Parte 2: ¿cuánto? (LogNormal o Beta, con mediana desplazada por z) |
| **Log-ratio t-Student** | Cambios % contra un periodo previo | ln(1 + x) ~ t(ν = 6)·σ + μ(z). Acota x > −100% y da colas pesadas con curtosis finita y estable (ver decisiones D-11: ν = 4 tiene curtosis infinita) |
| **Conteo** | Número de productos, destinos, reuniones | Binomial negativa con media exp(a + b·z) (sobredispersión) o Binomial(n, p(z)) |
| **Derivada** | Variables que el Excel define a partir de otras | Se calcula con la fórmula del Excel sobre series simuladas; no tiene distribución propia |

**Controles de calibración en cada paso:**
- **Tasa de alerta objetivo:** % de hogares que cruza el umbral ilustrativo del Excel.
- **IV objetivo según la fuerza predictiva del Excel:** Very high → IV 0.30–0.50; High → IV 0.10–0.30.
  La carga `b` sobre el latente se ajusta hasta caer en la banda, para que ninguna variable
  domine el score de forma irreal.

**Coherencia de los pares redundantes.** Los grupos Balances, Recurring y Transfers se
calculan desde **series mensuales simuladas** de saldo, depósitos recurrentes y
transferencias por hogar, no desde sorteos independientes. Así `deposit_balance_change_pct` y
`deposit_balance_vs_6m_avg_pct` quedan correlacionadas porque vienen del mismo saldo,
igual que en la realidad.

---

## Paso 0 · Atributos del hogar y target (construido)

| Columna | Distribución | Parámetros |
|---|---|---|
| relationship_value | LogNormal truncada (remuestreo bajo el piso) con cola Pareto truncada ≥ $30M | mediana $4M, σ = 1.2, piso $1M; cola α = 1.5, tope $1B |
| segment | Determinística | UHNW si valor ≥ $30M |
| has_investments | Bernoulli con p según patrimonio | P(solo depósitos) = logit⁻¹(logit 0.15 − 0.8·lv): 31% a $1M → 4% a $30M |
| deposit_balance | valor × Beta(2, 5) (100% si no hay inversiones) | media de la proporción ≈ 0.29 |
| aum | valor − depósitos (NULL sin inversiones) | — |
| age_primary | Normal truncada, redondeada hacia abajo | 61 ± 12, rango [28, 95] |
| tenure_years | Gamma, con tope | k = 2, θ = 4.5 (media 9); tope min(edad − 18, 50) |
| history_months | Determinística | min(12 × antigüedad, 24) |
| has_linked_business | Bernoulli por segmento | HNW 0.25 · UHNW 0.55 |
| has_trust | Bernoulli por segmento | HNW 0.30 · UHNW 0.70 |
| has_advisory | Bernoulli condicionada a tener inversiones | 0.70 |
| has_credit_anchor | Bernoulli | 0.35 |
| has_payroll_stream | Bernoulli según edad | activo (< 65) 0.80 · retirado 0.10 |
| has_pension_stream | Bernoulli según edad | retirado 0.85 · activo 0.05 |
| has_dividend_stream | Bernoulli condicionada a tener inversiones | 0.55 |
| salary_base_annual | LogNormal ligada al patrimonio (ρ = 0.45), piso $150k por remuestreo | mediana $350k, σ = 0.55 → resultado: mediana $379k, p95 $912k |
| bonus_annual | 25% sin bono (0); resto: sueldo × [0.10 + 1.40 · Beta(1.5, 3)] | media ≈ 57% entre quienes reciben; un pago al año |
| pay_frequency | Categórica | quincenal 45% · catorcenal 40% · mensual 15% |
| pension_monthly | LogNormal ligada al patrimonio (ρ = 0.30), piso $2.5k | mediana $9k (Social Security + pensión privada) |
| dividend_annual | AUM × rendimiento ~ Beta(4, 196) | rendimiento medio 2%, pagos trimestrales |
| business_distribution_annual | LogNormal ligada al patrimonio (ρ = 0.50) | mediana $500k |
| recurring_income_monthly | Suma: sueldo/12 + pensión + dividendos/12 + negocio/12 (sin bono) | resultado: mediana $31k (HNW $29k · UHNW $108k) |
| z_outflow, z_neglect, z_service | Normal multivariada | media 0, ρ = 0.35 / 0.25 / 0.30 |
| eps_idiosyncratic | Normal | σ = 0.6 (riesgo no observable) |
| churn_excluded | Bernoulli | 0.006 |
| hard_churn_6m | Bernoulli-logit sobre el índice de riesgo | pendiente 1.6, intercepto calibrado a 6% |
| soft_churn_3m | Bernoulli-logit, solo entre quienes no hacen hard churn | pendiente 1.2, calibrado a 9% |
| value_lost_6m | hard: 100% del valor · soft: valor × Uniforme(0.20, 0.60) | — |

---

## Variables 1–37 · Propuesta

Latente: **O** = outflow, **N** = neglect, **S** = service. "Alerta" es el % objetivo de
hogares elegibles que cruza el umbral del Excel.

### Paso 1 · Balances & AUM — CONSTRUIDO (ver decisiones D-12 y docs/reports/step1_report.md)

| # | Variable | Distribución | Latente | Alerta objetivo | NULL si |
|---|---|---|---|---|---|
| 1 | aum_outflow | Hurdle: P(>0) ≈ 35% · % de AUM ~ LogNormal (mediana 2%), tope 100% | O | > 10%: ≈ 8% | sin inversiones |
| 2 | deposit_balance_change_pct | Derivada de la serie de saldo; ln(1+x) ~ t(6), σ ≈ 0.15 | O | ≤ −25%: ≈ 10% | saldo previo < $10k |
| 17 | aum_vs_baseline_pct | Derivada de la serie de AUM ex-mercado; log-ratio t(6) | O | ≤ −20%: ≈ 8% | sin inversiones o < 6m de historia |
| 18 | deposit_balance_vs_6m_avg_pct | Derivada de la misma serie que #2 (ρ esperado ≈ 0.7 con #2) | O | ≤ −30%: ≈ 8% | saldo base < $10k |

### Paso 2 · Recurring deposits & flows

| # | Variable | Distribución | Latente | Alerta objetivo | NULL si |
|---|---|---|---|---|---|
| 3 | salary_deposit_stopped_flag | Bernoulli-logit, tasa base ≈ 4% | O (+N leve) | = 1: ≈ 4% | sin nómina |
| 4 | recurring_deposit_stopped_flag | Derivada: OR de los cortes por flujo (nómina, pensión, dividendos, otros ≥ 10% del ingreso) | O | = 1: ≈ 6% | sin flujos recurrentes |
| 5 | recurring_deposit_change_pct | Si algún flujo se cortó: −(peso del flujo) + ruido; si no: log-ratio t(6), σ ≈ 0.10 | O | ≤ −40%: ≈ 6% | sin flujos recurrentes |
| 6 | net_deposit_flow | Derivada de la serie (créditos − débitos); en % ~ t(6) con media −β·O | O | pct ≤ −15%: ≈ 10% | — |
| 19 | pension_deposit_stopped_flag | Bernoulli-logit, tasa base ≈ 2%; incluye muertes (excluidas del target) | O | = 1: ≈ 2% | sin pensión |
| 20 | business_payroll_stopped_flag | Bernoulli-logit, tasa base ≈ 4% | O | = 1: ≈ 4% | sin negocio vinculado |

### Paso 3 · Transfers (desde la serie de transferencias externas)

| # | Variable | Distribución | Latente | Alerta objetivo | NULL si |
|---|---|---|---|---|---|
| 7 | external_transfer_pct_of_balance | Hurdle: P(>0) ≈ 55% · LogNormal (mediana 3%), tope 150% | O (fuerte) | > 15%: ≈ 8% | — |
| 8 | new_external_destinations | Binomial negativa, media exp(a + b·O) | O | ≥ 1: ≈ 12% | — |
| 21 | transfer_to_competitor_bank_amount | Monto de #7 × proporción a competidores ~ Beta (sube con O) | O | > 10% del saldo: ≈ 5% | — |
| 22 | external_transfer_acceleration | Derivada de los bloques mensuales A1, A2, A3 | O | > 0 y A1 > 5%: ≈ 7% | sin salidas en los 3 bloques |
| 23 | net_external_flow | Entradas externas (Hurdle LogNormal) − salidas de #7 | O | pct ≤ −15%: ≈ 8% | — |
| 24 | external_destination_concentration | HHI de cuotas ~ Dirichlet(α); α baja (más concentrado) con O; nº de instituciones 1 + Poisson | O | > 0.7 con salidas > 10%: ≈ 5% | sin salidas |
| 25 | outflow_vs_baseline_pct | Derivada de la serie: último mes ÷ promedio de 6m − 1, con piso de $1k | O | > +100%: ≈ 8% | — |

### Paso 4 · Investments

| # | Variable | Distribución | Latente | Alerta objetivo | NULL si |
|---|---|---|---|---|---|
| 9 | investment_redemption_pct | Hurdle: P(>0) ≈ 40% · LogNormal (mediana 3%), tope 100% | O | > 20%: ≈ 6% | sin inversiones |
| 26 | fixed_income_maturity_not_reinvested | Mixtura: masa en 0 (reinvierte todo) + Beta(a, b); la masa en 0 baja con O | O | > 50%: ≈ 30% de los que tuvieron vencimientos | sin vencimientos en 90d (≈ 75%) |
| 27 | cash_pct_of_portfolio_chg | Cash base ~ Beta(2, 18) (≈ 10%); cambio ~ Normal(β·O, 3pp) dentro de [0, 1] | O | > +10pp: ≈ 5% | sin inversiones |
| 28 | return_vs_benchmark | Normal(−0.5pp, 3pp), en esencia exógena (ver pregunta 1) | exógena | ≤ −3pp: ≈ 20% | sin advisory |
| 34 | positions_liquidated_pct | #9 × proporción en liquidaciones totales ~ Beta(2, 3) | O | > 15%: ≈ 4% | sin inversiones |

### Paso 5 · Relationship & closures

| # | Variable | Distribución | Latente | Alerta objetivo | NULL si |
|---|---|---|---|---|---|
| 10 | products_closed | Binomial(nº de productos, p(O, S)); requiere agregar nº de productos | O + S | ≥ 1: ≈ 7% | — |
| 29 | accounts_closed | #10 + cuentas extra ~ Poisson, menos consolidaciones internas | O + S | ≥ 1: ≈ 9% | — |
| 30 | share_of_wallet | Beta (media ≈ 0.45), tope 1; fuente de estimación categórica (declarada / proveedor / modelo) con ruido distinto | O (inversa) | < 30%: ≈ 30% | — |
| 31 | share_of_wallet_change | Normal(−β·O, 4pp) con colas t(6) | O | ≤ −10pp: ≈ 6% | — |
| 32 | trustee_change_flag | Bernoulli-logit, tasa base ≈ 2%; incluye sucesiones por muerte | O + S | = 1: ≈ 2% | sin trust |

### Paso 6 · Banker

| # | Variable | Distribución | Latente | Alerta objetivo | NULL si |
|---|---|---|---|---|---|
| 11 | banker_change_6m_flag | Bernoulli **por banker** (salida del banker ≈ 10% cada 6m), heredada por todo su libro | exógena (ver pregunta 1) | = 1: ≈ 12% | — |
| 12 | contact_gap_ratio | LogNormal (mediana ≈ 0.8), sube con N; cadencia UHNW 30d · HNW 90d | N | > 2.0: ≈ 12% | — |
| 13 | client_reply_rate | Contactos ~ Poisson(λ por segmento); respuestas ~ Beta-Binomial(n, p(N)) | N | < 50%: ≈ 15% | < 3 contactos |
| 35 | meetings_cancelled_by_client | Reuniones ~ Poisson (UHNW 6, HNW 2 en 6m); canceladas ~ Binomial(n, p(N)) | N | ≥ 2 o ≥ 50%: ≈ 8% | sin reuniones |

### Paso 7 · Complaints & voice of client

| # | Variable | Distribución | Latente | Alerta objetivo | NULL si |
|---|---|---|---|---|---|
| 14 | complaint_escalated_flag | Quejas 12m ~ Poisson(exp(a + b·S)); escaladas ~ Binomial(quejas, p) | S | = 1: ≈ 2% | — |
| 15 | complaint_age_days | Masa en 0 (sin queja abierta, ≈ 95%) + Gamma (mediana 15d) que se alarga con S | S | > 30d: ≈ 2% | — |
| 33 | repeat_complaint_flag | Derivada: categorías de las quejas ~ Multinomial (8 categorías); flag si alguna se repite o se reabre | S | = 1: ≈ 2% | — |
| 36 | relationship_dissatisfaction_flag | Bernoulli-logit, tasa base ≈ 1.5% | S + N | = 1: ≈ 1.5% | antes del go-live del Assistant (ver pregunta 2) |

### Paso 8 · External & composite

| # | Variable | Distribución | Latente | Alerta objetivo | NULL si |
|---|---|---|---|---|---|
| 16 | multi_signal_flag | Derivada: nº de grupos (0–7) con alguna alerta; flag si ≥ 3 | — | ≥ 3 grupos: resultado, se revisa (≈ 5–8%) | — |
| 37 | bureau_new_mortgage_elsewhere | Bernoulli-logit, tasa base ≈ 3%; más probable sin crédito ancla | O | = 1: ≈ 3% | sin aprobación legal (ver pregunta 2) |

---

## Umbrales del Excel que parecen bajos para Private Banking

Con sueldos de ~$380k más bono e ingresos recurrentes de ~$31k al mes, algunos pisos
del Excel (hoja Parameters) dejarían pasar gasto normal como señal. Propuesta:

| Parámetro (Excel) | Valor Excel | Propuesta PB | Motivo |
|---|---|---|---|
| Outflow baseline floor | $1,000 / mes | $10,000 / mes | Colegiaturas, impuestos y pagos grandes son habituales |
| Monto mínimo por destino nuevo | $10,000 | $50,000 | Pagar a un contratista o una colegiatura no es "moverse" |
| Saldo mínimo para % | $10,000 | $10,000 (sin cambio) | Solo evita divisiones por casi cero |
| Detección de nómina (CV de intervalos < 0.25) | — | Excluir el bono anual antes de medir regularidad | Si no, el bono rompe el patrón y genera falsos "nómina detenida" |

## Decisiones abiertas

1. **Variables causales exógenas** (#11 cambio de banker, #28 rendimiento vs. benchmark).
   No son síntomas del cliente sino causas: el banker se va por razones propias del banker.
   Si se generan sin conexión al target, su IV sale ≈ 0 (el deck espera lo contrario: Cerulli,
   22% de los activos se mueve). Propuesta: generarlas en el Paso 0, antes del target, y
   sumarlas al índice de riesgo como efecto estructural (igual que el crédito ancla).
   Esto cambia el target del Paso 0, así que conviene decidirlo antes del Paso 1.
2. **Variables sin historia** (#35, #36, #37, factibilidad Low). Opciones: (a) generarlas
   completas, como si existieran; (b) NULL en la historia y con valor solo en los cortes
   recientes, que es lo realista para reentrenar. Propuesta: (b), con un parámetro para
   pasar a (a).
3. **Nº de productos y bankers.** #10 necesita el número de productos por hogar y #11 necesita
   el libro de cada banker. Se agregan al Paso 0: productos ~ 1 + Poisson (según segmento);
   bankers con libros de ≈ 60 hogares.
