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

## Paso 2 · Recurring deposits & flows (variables 3, 4, 5, 6, 19, 20)

**D-14 · Dos motores de señal: propensión y factor.**
Con el factor de salida de dinero solo, ni el 3% más riesgoso pasa de 28% de churn, así que
ninguna variable generada desde él alcanza IV "Very high" (0.30–0.50). El Excel define "Very high"
como precursor directo de la salida ("the client is already moving money"). Por eso:
- **Motor "propensión":** el evento se genera desde el índice de riesgo total del Paso 0.
  Caso del Paso 2: la mudanza del banco principal, P = logit⁻¹(−7.6 + 4.2 · risk_index), ≈ 5% de
  hogares, que corta nómina (85%), pensión (45%), dividendos (30%) y distribuciones (40%).
  Estas variables se correlacionan con ε por diseño (ρ ≈ 0.13–0.15), no por fuga del target:
  dependen de la propensión, no del sorteo Bernoulli del churn.
- **Motor "factor":** redirección parcial del ingreso (z_outflow) y traslado de la nómina del
  negocio (z_outflow). Estas sí deben ser independientes de ε, y lo son (|ρ| < 0.01).
- El AUC combinado de los Pasos 1 y 2 es 0.65, todavía lejos del techo de 0.85.

**D-15 · Detección del Excel corrida sobre transacciones simuladas.**
Cada crédito recurrente se simula con su fecha durante 18 meses (≈ 520 mil transacciones), sobre un
calendario real de EE. UU.: días hábiles y feriados federales, nómina catorcenal en viernes,
quincenal el 15 y fin de mes, pensión en un día fijo por hogar, dividendos y distribuciones
trimestrales. Hay pagos corridos (3%) y omitidos (1% por año). Montos netos: nómina 62% del bruto,
pensión 85%. Encima se corre el algoritmo del Excel: ≥ 3 ocurrencias, CV de intervalos < 0.25,
max(45d, 1.5 × intervalo), reemplazo de nómina ≥ 50%, flujos ≥ 10% del ingreso, 60 días para la
nómina del negocio, y exclusiones de retiro, licencia, muerte y venta del negocio reportados.
Resultados del detector:
- 0% de falsos positivos en hogares sin eventos; 98% de recall en nóminas mudadas hace > 60 días.
- El 99% de los cambios de empleo con reemplazo ≥ 50% no se marca.
- Excluir el bono (> 2× la mediana del originador) importa: t = 31-dic, así que el bono de
  diciembre cae en la ventana de 30 días de #5. Sin la regla, el "aumento de ingreso recurrente"
  mediano de esos 2,411 hogares sería +396%; con la regla es −1%.
- Ruido que se marca igual que en la vida real: retiros no reportados, cambios de empleo con
  sueldo < 50% del anterior, licencias no reportadas, y mudanzas de menos de 45 días que todavía
  no se ven.

**D-16 · IV de flags de subpoblación: condicional y con varianza de muestreo.**
Los flags de nómina, pensión y negocio se calibran con IV entre los hogares donde aplican. Con
~100–300 eventos, el IV varía ±0.08 entre semillas. Por eso se exige que la semilla de producción y
la mediana entre 20 semillas caigan en la banda, y se reporta p10–p90. La semilla de producción
queda del lado bajo (nómina 0.32 vs mediana 0.39).

| Variable | Fuerza Excel | Motor | Alerta | IV (semilla / mediana 20 semillas) | Lift |
|---|---|---|---|---|---|
| salary_deposit_stopped_flag | Very high | propensión | 3.6% | 0.32 / 0.39 | 5.7× |
| recurring_deposit_stopped_flag | High | propensión | 4.2% | 0.22 / 0.25 | 4.3× |
| recurring_deposit_change_pct | High | mixto | 10.7% | 0.17 / 0.16 | 2.7× |
| net_deposit_flow_pct_90d | High | factor (serie Paso 1) | 18.1% | 0.16 / 0.20 | 2.4× |
| pension_deposit_stopped_flag | High | propensión | 2.0% | 0.22 / 0.27 | 5.8× |
| business_payroll_stopped_flag | High | factor | 5.6% | 0.16 / 0.19 | 3.3× |

- `net_deposit_flow` es por construcción el cambio de saldo de la serie del Paso 1 (créditos −
  débitos). Con el umbral del Excel (≤ −15%) alerta al 18%. Dividido por el saldo promedio puede
  ser < −100%.

**D-17 · La mudanza del banco principal es un evento común a todos los pasos.**
En el Paso 2 la mudanza cortaba la nómina, pero el saldo del Paso 1 no bajaba: los dólares no
cuadraban. Ahora el evento se sortea una vez (`synthetic/exit_events.py`, mismos flujos de semilla,
así que los eventos del Paso 2 quedan idénticos) y se ve en todos los pasos:
- **Paso 1:** traslado de 30–90% del saldo de depósitos en el mes del evento (90% de quienes se
  mudan) y ACATS de 20–80% del AUM 0–30 días después (60% de quienes tienen inversiones).
- **Paso 2:** corte de flujos (sin cambios).
- **Paso 3:** transferencias al banco o broker nuevo.

Efecto en el Paso 1: la señal de saldos es ahora en parte de propensión. Se recalibraron los
episodios (intercepto −4.0, pendiente 1.4, δ 12%) para volver a la banda "High".

| Variable | Alerta | IV | Lift |
|---|---|---|---|
| aum_outflow_pct_90d | 6.0% | 0.134 | 3.0× |
| deposit_balance_change_pct_90d | 5.8% | 0.248 | 4.1× |
| aum_vs_baseline_pct | 4.8% | 0.175 | 4.1× |
| deposit_balance_vs_6m_avg_pct | 5.9% | 0.267 | 4.1× |

- Los rangos de tasa de alerta del Paso 1 (supuestos míos; el Excel solo da el umbral) pasan a
  [4%, 16%]. `net_deposit_flow_pct_90d` (Paso 2) alerta ahora al 10%, con rango [6%, 22%].
- **La fuga se prueba en el generador, no en la variable.** Una logística episodio ~ z_outflow + ε
  debe dar coeficiente de ε ≈ 0 (Wald), y los eventos de ruido deben ser independientes del índice
  de riesgo. Probar "variable ⟂ ε entre hogares sin mudanza" daba ρ ≈ 0.02 por sesgo de selección:
  al filtrar por un evento que depende de ε, un ε alto queda asociado a un factor más bajo.
- Seguía abierto que el ruido del Paso 1 se estimaba incluyendo hogares con mudanza (curtosis 255);
  ahora se excluyen y ν̂ ≈ 6 otra vez.

## Paso 3 · Transfers (variables 7, 8, 21, 22, 23, 24, 25)

**D-18 · Transferencias simuladas una por una y cuadradas con el saldo.**
~3.2 millones de transacciones en 18 meses:
- **Salidas con origen en eventos ya simulados** y con el monto exacto que movió la serie del
  Paso 1: mudanza (depósitos al banco competidor en 2–6 tramos mensuales; ACATS del 80% de los
  hogares con inversión, 0–120 días después, a un broker en el 70% de los casos), episodios (45% es
  gasto y no genera transferencia; el resto va a banco competidor, broker o destino habitual) y
  choques (compra de casa a title/escrow, o IRS excluido).
- **Ruido:** envíos de fondo a 1–6 destinos habituales (0.5% del saldo al mes en ~4 envíos) y
  destinos nuevos esporádicos (2% por mes, mediana $15k).
- **Pagos excluidos por el Excel:** billers, IRS estimado trimestral (30% del ingreso), donaciones
  recurrentes y préstamos con Citizens. Sin la exclusión, la alerta de #7 pasaría de 6.5% a 8.8%.
- **Entradas externas:** cierran mes a mes la identidad
  ΔD = ingresos (Paso 2) + internos AUM→depósitos + entradas − salidas − tarjeta − otros débitos.
  Cuadra al centavo; 44% de los meses necesita débitos no explicados (tarjeta extra o cheques).
- **Catálogo sintético:** 111 instituciones con nombres genéricos y 1–3 ABA cada una, con dígito
  verificador válido. La ABA es fija por cuenta destino, y #24 agrupa por institución: 516 hogares
  cambian de HHI al agruparlos.
- **Pisos PB aplicados** ($50k por destino nuevo y $10k mensual de línea base) como parámetros.
  Los dos mejoran la precisión frente a los del Excel: lift 4.28 vs 3.20 en #8, y 2.36 vs 1.79 en #25.

Ajustes que este paso obligó a hacer en pasos previos (todos revalidados):
- **Mudanza por tramos** (2–6 meses): una relación PB no se muda en un día. Sin tramos, la ventana
  de 60 días de #7 veía solo un tercio de las mudanzas.
- **Volatilidad del saldo PB: 12% mensual** (antes 5%). Con 5%, el saldo era un espejo perfecto de
  las transferencias y las variables de saldo superaban "High". Con 12%, `net_deposit_flow_pct_90d`
  alerta al 28% con el umbral ilustrativo de −15%: **el umbral debería recalibrarse** (el 10% más
  bajo está en −38%).
- **Convención de meses única:** el mes 0 son los últimos 30 días (antes la mudanza usaba floor).
- **#23 solo wires/ACH:** los datos del Excel para #23 son "incoming and outgoing wires / ACH";
  el ACATS cuenta en #7 por la definición base de transferencia externa.
- **#8 en ventana de 90 días como principal:** a 30 días, con piso de $50k, es muy raro (2%) y su IV
  mediano es 0.08. El Excel lista ambas ventanas; la de 30 días se conserva.
- **#25 tiene forma de U:** riesgo alto al empezar la mudanza (> +100%) y al terminarla (≈ −100%
  frente a una línea base inflada por los tramos previos). Se valida con IV, lift y forma, no con
  tendencia lineal.
- **Tolerancia de ±0.03 a las bandas de IV en este grupo:** el Excel aclara que la fuerza es un
  "expert prior, to be validated with IV / SHAP", y aquí el mismo dinero se mide en bruto (#7) y
  en neto (#23). Medianas en 20 semillas:

| Variable | Excel | IV mediano (p10–p90) | Alerta | Lift |
|---|---|---|---|---|
| external_transfer_pct_of_balance_60d | Very high | 0.292 (0.26–0.33) | 6.5% | 4.9× |
| new_external_destinations_90d | High | 0.264 (0.23–0.32) | 5.9% | 4.4× |
| transfer_to_competitor_pct_90d | High | 0.295 (0.27–0.35) | 5.0% | 6.1× |
| external_transfer_acceleration | High | 0.202 (0.18–0.23) | 4.3% | 4.8× |
| net_external_flow_pct_90d | High | 0.254 (0.23–0.28) | 5.1% | 5.0× |
| external_destination_concentration | High | 0.225 (0.20–0.26) | 6.0% | 4.5× |
| outflow_vs_baseline_pct | High | 0.112 (0.08–0.13) | 7.6% | 2.4× |

El AUC combinado de las 17 variables de los Pasos 1–3 es 0.656; el techo sigue en 0.851.

## Paso 4 · Investments (variables 9, 26, 27, 28, 34)

**Criterio general desde aquí:** las variables deben *tener sentido* (dirección, magnitud,
plausibilidad y coherencia con los pasos previos), sin perseguir cada banda de IV al decimal.
Tolerancia de ±0.03 a las bandas expertas del Excel.

**D-19 · Rendimiento vs benchmark ligado al factor S sin tocar el target.**
El factor S del Paso 0 se interpreta como "servicio y valor percibido". El Paso 1 ahora agrega un
alpha anual al portafolio: −comisión (1% advisory, 0.2% resto) + habilidad N(0, 1.5%) − 2% · z_service.
El rendimiento de #28 es exactamente el índice TWR del Paso 1 (verificado), y el benchmark es el
del perfil (beta objetivo = beta real + desvío). El AUM ex-mercado (#17) no cambia, porque divide
por ese mismo índice. Pasos 1–3 reconstruidos y revalidados. La regresión de #28 sobre z_service
recupera −κ, y ε no entra.

**Composición del portafolio sin mover dólares del AUM:**
- **Señal factor:** venta a cash (z_outflow, 15–60% del AUM, últimos 150 días).
- **Señal propensión:** el 50% de quienes hacen ACATS liquida fondos propietarios (5–25% del AUM)
  0–30 días antes, porque el custodio nuevo no los acepta.
- **Ruido:** de-risking del asesor (5%), que sube el cash sin contar como venta del cliente;
  rebalanceos del asesor (excluidos); ventas completas ocasionales; RMD de diciembre para ≥ 73
  (excluida de #9); vencimientos de renta fija (30% en 90 días), con reinversión normal completa
  en el 65% de los casos. Quien se muda o liquida no reinvierte en el 85% (media no reinvertida
  0.95 vs 0.34).
- El cash % mensual parte del cash de inversión que usa el Paso 3 en el denominador de #7.

| Variable | Alerta | IV (semilla / mediana) | Lift |
|---|---|---|---|
| investment_redemption_pct | 6.2% | 0.18 | 2.9× |
| fixed_income_maturity_not_reinvested | 36.8% de quienes tuvieron vencimiento | 0.21 | 2.1× |
| cash_pct_of_portfolio_chg | 7.9% | 0.14 | 2.7× |
| return_vs_benchmark | 31.6% (≤ −3 pp) | 0.12 / 0.10 | 1.6× |
| positions_liquidated_pct | 1.6% | 0.19 | 3.7× |

- `return_vs_benchmark` es el driver más débil (mediana 0.096), como en la realidad: el mal
  rendimiento explica el "porqué", pero no anticipa la salida tanto como mover dinero.
- El AUC combinado de 22 variables es 0.683; el techo sigue en 0.851.

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
