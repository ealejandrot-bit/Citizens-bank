# Log de decisiones · Base sintética Client Pulse

Cada decisión que afecta distribuciones, semillas o el target queda registrada aquí
antes de construir. Las marcadas **[Validar]** son supuestos pendientes de confirmar.

## Paso 0 · Fundaciones

**D-01 · Semillas por nombre, no por orden.**
Hay una sola semilla maestra (`config/params.yaml → master_seed`). Cada componente
pide su generador con `SeedManager.rng("nombre")`, derivado de
`SeedSequence(master_seed, spawn_key=SHA-256(nombre))`. Consecuencias:
- Agregar, quitar o reordenar variables en pasos futuros no cambia lo ya generado.
- Cambiar la distribución de una columna no mueve otras (lo prueba un test).
- No se usa `np.random.seed`, `random.seed` ni `hash()` de Python.
- Pedir dos veces el mismo nombre da error (evita correlación accidental).
- El manifiesto de cada paso lista los flujos usados y el SHA-256 de las salidas.

**D-02 · Las variables se generan desde factores latentes, nunca desde el target.**
Cada hogar tiene tres factores latentes N(0,1) correlacionados (ρ 0.25–0.35), uno por
trayectoria de churn del deck (slide 24): `outflow` (salida de dinero), `neglect`
(deriva silenciosa / abandono del banker) y `service` (fricción de servicio).
El target sale de un índice de riesgo = combinación de los latentes + efectos
estructurales + un **componente idiosincrático no observable**. Las variables del
Excel saldrán de los latentes + ruido propio. Así:
- No hay fuga: ninguna variable "ve" el target.
- El AUC queda acotado. El techo (AUC con la probabilidad verdadera) es **0.851**;
  un modelo real sobre variables ruidosas debería quedar por debajo (≈0.72–0.80).
  Si en un paso futuro un modelo supera ese techo, algo está mal.
- Las variables de un mismo grupo quedan correlacionadas entre sí pero no son
  copias, así el scorecard no se queda con una sola variable que lo explica todo.

**D-03 · Tabla observable y tabla de verdad, separadas.**
`step0_households.csv` (observables + target) es lo que ve el modelo.
`step0_truth.csv` (latentes, índice, probabilidades) solo se usa para validar.

**D-04 · NULL ≠ cero.** [Excel · Base definitions]
Cada variable tiene `applies_to` en el catálogo. Fuera de esa subpoblación va NULL.
El Paso 0 crea las banderas que definen esas subpoblaciones (`has_investments`,
`has_payroll_stream`, `has_linked_business`, `has_trust`, `has_advisory`, …).

**D-05 · Target.**
- `hard_churn_6m`: salida total en (t, t+6m]. Tasa 6% **[Validar]**, anclada al
  deck (3% por trimestre, slide 17).
- `soft_churn_3m`: contracción > 20% sin salida total en (t, t+3m]. Tasa 9% sobre
  hogares elegibles **[Validar]**; el umbral de 20% está abierto en el deck (slide 69).
- Hard y soft son excluyentes.
- Exclusiones (muerte o reubicación, 0.6%) → target NULL, no churn (slide 59).
- El intercepto se calibra para que E[p] = tasa exacta (control de calibración, slide 17).

**D-06 · Población.** **[Validar]** todos los valores:
- Valor de la relación ~ LogNormal (mediana $4M, σ 1.2, piso $1M) → UHNW (≥ $30M) ≈ 5.5%.
- 15% de hogares solo con depósitos; en el resto, la proporción de depósitos ~ Beta(2,5).
- Edad ~ Normal truncada (61 ± 12); antigüedad ~ Gamma (media 9 años, tope 50).
- Historia disponible = min(antigüedad, 24 meses): los hogares nuevos tendrán NULL
  en variables que exigen línea base de 6 meses.
- Business vinculado 25% (55% en UHNW), trust 30% (70% en UHNW).

**D-07 · Un solo corte (snapshot) por ahora.**
El Paso 0 genera un corte t = 2025-12-31. El panel mensual (necesario para validar
out-of-time, slide 20) se agrega cuando existan las variables, reutilizando los
latentes con evolución temporal. **[Validar]** si lo quieres desde ya.

**D-08 · Ingresos de Private Banking.**
Los montos de ingreso (sueldo base, bono, pensión, dividendos, distribuciones del negocio)
son LogNormales ligadas al log-patrimonio, con pisos PB (sueldo ≥ $150k) aplicados por
remuestreo. Dependen del patrimonio pero no de los factores de riesgo: el nivel de ingreso es
estructura, no señal. Resultado: sueldo base mediano $379k (UHNW $585k), bono mediano $167k,
ingreso recurrente mensual mediano $31k (UHNW $108k). Todo esto está por validar.
Agregarlos no cambió ninguna columna previa (flujos de semilla nuevos, D-01). La excepción
es `has_any_recurring_stream`, que ahora incluye las distribuciones del negocio (+469 hogares).

**D-09 · Moneda: USD.**
Citizens es un banco de EE. UU.: todos los montos son dólares nominales, sin conversión.
`config/params.yaml → currency: USD`. Cada columna declara su unidad en
`synthetic/schema.py` y el build falla si aparece una columna sin declarar. Las
referencias también son de EE. UU.: ACH/SEC, ABA/SWIFT, Social Security, IRS, CFPB/OCC, FCRA.

## Plan de pasos (catálogo: `data/catalog/variables_catalog.csv`)

| Paso | Grupo | Variables |
|---|---|---|
| 1 | Balances & AUM | 1, 2, 17, 18 |
| 2 | Recurring deposits & flows | 3, 4, 5, 6, 19, 20 |
| 3 | Transfers | 7, 8, 21–25 |
| 4 | Investments | 9, 26, 27, 28, 34 |
| 5 | Relationship & closures | 10, 29–32 |
| 6 | Banker | 11, 12, 13, 35 |
| 7 | Complaints & voice of client | 14, 15, 33, 36 |
| 8 | External & composite | 16 (multi_signal, derivada de todas), 37 |

Se construye por grupo porque las variables de un grupo comparten mecánica y tienen
pares redundantes (p. ej. `deposit_balance_change_pct` vs `deposit_balance_vs_6m_avg_pct`)
que deben salir coherentes entre sí. Cada paso: especificación de distribución →
revisión contigo → construcción → chequeos (NULL, rangos, tasa de alerta, IV esperado).
