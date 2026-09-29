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

**D-10 · Validación estadística** (`scripts/stats_step0.py`, reporte en
`docs/reports/step0_stats_report.md`). 200 pruebas, todas OK con α = 0.01 y corrección
Benjamini-Hochberg:
- **Bondad de ajuste:** cada columna contra la distribución y los parámetros con que se generó.
  Se usa KS y Cramér-von Mises sobre la PIT, χ² para edad y frecuencia de pago, y binomial
  exacta para las banderas. Como no se estima ningún parámetro, los gl son los nominales:
  χ² gl = celdas − 1; Hosmer-Lemeshow gl = grupos − 2; Mardia asimetría gl = p(p+1)(p+2)/6 = 10;
  independencia gl = (r−1)(c−1); Jarque-Bera gl = 2.
- **Colas y curtosis:** se exige cola pesada en escala USD (curtosis de exceso > 0 significativa;
  patrimonio ≈ 376). Tras normalizar por PIT, la curtosis debe ser 0 (Anscombe-Glynn, Jarque-Bera).
  La curtosis de log(patrimonio) coincide con la teórica de la Normal truncada. Se agregan
  L-momentos e índice de Hill, más robustos que la curtosis clásica.
- **Dinero:** sin negativos, sin infinitos, al centavo, bajo máximos plausibles; medias iguales a las
  teóricas (prueba t) y dentro de bandas de negocio PB (`config/validation.yaml`).
- **Sesgo:** 30 independencias por diseño (Spearman), target independiente de atributos sin efecto
  diseñado (χ²), y efectos diseñados con el signo correcto.
- **Duplicados y variedad:** 0 filas duplicadas, 0 pares casi idénticos (distancia mínima entre
  vecinos 0.035 d.e.; p1 = 0.17), 303 combinaciones de banderas. Las repeticiones de montos
  coinciden con lo esperado por redondear al centavo (pensión: 15 observadas vs 15.2 esperadas).
- **Semilla:** la semilla de producción no es atípica frente a 200 semillas de referencia
  (percentiles 15–92 en las 10 métricas clave). Los p-valores KS entre semillas son uniformes,
  así que el generador no tiene sesgo sistemático.

**D-11 · Grados de libertad de la t-Student: ν = 6 en lugar de 4.**
El estudio de 60 réplicas × 20,000 muestra que con ν = 4 la curtosis teórica es infinita: la
muestral va de 6 a 43 entre réplicas (CV 2.0). Así la curtosis no se puede validar y dos semillas
darían colas muy distintas. Con ν = 5 sigue siendo inestable (CV 0.45). Con ν = 6 queda estable
(teórica 3, CV 0.20) y conserva colas pesadas. La máxima verosimilitud recupera ν sin sesgo (< 1%)
en todos los casos, así que si Citizens entrega datos reales, ν se estima de ellos.

**D-13 · Ajustes de plausibilidad aplicados** (antes eran hallazgos pendientes):
- **Solo depósitos según patrimonio:** logit p = logit(0.15) − 0.8·lv → ≈ 31% a $1M, 15% a $4M, 4% a $30M.
  Resultado: 14.3% en total y 4.2% en UHNW (antes 16.6%).
- **Bono:** 25% sin bono (bono = 0, no NULL); el resto recibe 10% + 140% × Beta(1.5, 3) del sueldo.
- **Cola Pareto:** por encima de $30M, Pareto truncada con α = 1.5 y tope de $1B. Se conserva
  P(≥ $30M), así que el segmento y el target no cambian. La MLE truncada recupera α.
- **Grados de libertad de Hosmer-Lemeshow corregidos:** el target solo calibra el intercepto en la
  muestra → gl = g − 1 (antes g − 2). Para solo depósitos, p_i es conocida → gl = g.

Contexto histórico de los hallazgos:
1. **Hogares grandes solo con depósitos.** La probabilidad de no tener inversiones no depende del
   patrimonio (15% en HNW y UHNW). Hay 183 hogares de más de $30M solo en depósitos, y uno de
   $782M que concentra el 0.4% del libro. Por eso la media de depósitos de esta semilla queda en el
   percentil 99.8 (no se rechaza tras BH). Propuesta: que la probabilidad caiga con el patrimonio.
2. **Bonos muy chicos.** 1.5 × Beta(1.5, 3) produce bonos casi nulos: 123 menores a $10k y 265 menores
   al 5% del sueldo. Propuesta: una masa de "sin bono" (≈ 25%, p. ej. médicos o abogados socios)
   y, para el resto, un bono con piso de 10% del sueldo.
3. **Cola del patrimonio.** La LogNormal da un índice de Hill de 2.4 en el top 1%. La riqueza real
   suele tener una cola Pareto más pesada (α ≈ 1.5). Si importa el peso de los UHNW en el AUM
   churn, se puede usar una cola Pareto por encima de $30M.

## Paso 1 · Balances & AUM (variables 1, 2, 17, 18)

**D-12 · Variables calculadas desde series mensuales, no sorteadas.**
Cada hogar tiene 24 meses de depósitos (promedio mensual) y AUM (cierre de mes), anclados al
Paso 0 en t y simulados hacia atrás, así ningún valor del Paso 0 cambia. Componentes:
- **Ruido de fondo:** incrementos log de depósitos = 0.2% + 5% · t(6) estandarizada. La prueba KS
  y la MLE (ν̂ ≈ 6) confirman que el ruido de la serie es t(6).
- **Mercado:** un rendimiento común por mes (0.6% + 4% · t(6)), una beta de renta variable por hogar
  en [0.3, 1.0] y un índice TWR. Así el AUM ex-mercado (#17) solo se mueve con los flujos del cliente.
- **Flujos de fondo del AUM** (hurdle): aportes P = 12% (mediana 2%) y retiros P = 20% (mediana 1%).
- **Señal:** episodio de salida con P = logit⁻¹(−3.0 + 2.2 · z_outflow) (≈ 14% de hogares), duración
  de 1 a 6 meses hasta t, intensidad mensual ~ LogNormal (mediana 14%) con multiplicador por canal
  (depósitos [1.0, 2.0], AUM [0.3, 1.1]).
- **Ruido que imita señal:** choque de liquidez independiente del riesgo (10% de hogares en 12
  meses; impuestos o compra de casa; mediana 25% del saldo). Genera falsos positivos realistas: el
  12% de los hogares con choque y sin episodio dispara la alerta de AUM.
- **Ventanas en meses** (aproximación a los días del Excel): 30d = 1, 90d = 3, 180d = 6, línea base
  (t−210d, t−30d] = meses −6..−1. Los meses anteriores a la apertura no existen → NULL.

**Resultado** (semilla de producción; 20 semillas de referencia en el reporte):

| Variable | Alerta | Tasa | IV hard | Lift de la alerta |
|---|---|---|---|---|
| aum_outflow_pct_90d | > 10% | 13.5% | 0.165 | 2.5× |
| deposit_balance_change_pct_90d | ≤ −25% | 9.7% | 0.149 | 2.5× |
| aum_vs_baseline_pct | ≤ −20% | 8.4% | 0.146 | 2.5× |
| deposit_balance_vs_6m_avg_pct | ≤ −30% | 10.7% | 0.168 | 2.5× |

- Las cuatro quedan en la banda "High" (IV 0.10–0.30) en las 20 semillas de referencia.
- El AUC combinado de las cuatro es 0.60, lejos del techo de 0.85: ninguna variable explica todo.
- Correlación de Spearman entre #2 y #18 ≈ 0.90: el par redundante del Excel sale redundante,
  como se esperaba; se decide por IV.
- La forma es de palo de hockey (plana en el medio, fuerte en la cola), por eso la monotonía se
  valida con Cochran-Armitage y lift, no con ρ ≈ 1.
- **Las dos medidas de AUM no pueden alertar igual:** retiros brutos ÷ AUM promedio (#1) siempre
  alerta más que la caída neta ex-mercado (#17) ante el mismo episodio. Por eso las tasas objetivo
  son rangos.

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
