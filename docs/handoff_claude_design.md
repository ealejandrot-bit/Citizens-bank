# HANDOFF IA → IA · Documentación de la base sintética Client Pulse

> **Para la persona:** pega este archivo completo en Claude Design. Todo lo que el documento necesita
> está aquí; Claude Design no necesita acceso al repositorio. Generado por `scripts/build_handoff.py`
> desde la configuración, los datos y los reportes del repositorio (ninguna cifra transcrita a mano).

---

## 1. INSTRUCCIONES PARA LA IA RECEPTORA

```yaml
tarea: diseñar un documento técnico de metodología de datos sintéticos, legible y visual
idioma: español
audiencia:
  primaria: validador independiente de riesgo de modelos (no participó en la construcción)
  secundaria: equipo de Citizens Private Bank (negocio y data science)
proposito: que el lector entienda, reproduzca y pueda cuestionar cómo se generó la base
fuente_unica_de_datos: bloque DATA (sección 3) de este archivo
reglas_duras:
  - usar SOLO cifras del bloque DATA; no inventar, redondear de más ni completar valores faltantes
  - si algo no está en DATA, escribir "no documentado" (no suponer)
  - toda cifra de resultados lleva la etiqueta [SINT]; nunca presentarla como dato del banco
  - conservar el origen de cada parámetro (Excel, Deck, Supuesto, Calibrado; 'Supuesto (simulación, sin etiqueta)' = parámetro técnico del simulador sin etiqueta en params.yaml, trátalo como supuesto no validado)
  - distinguir siempre parámetro de generación / resultado observado / criterio de aceptación
  - montos en USD; porcentajes con el mismo número de decimales que en DATA
  - no citar benchmarks ni cifras de bancos reales
estilo:
  tono: técnico, sobrio, sin adjetivos promocionales
  jerarquia: títulos numerados, tablas para datos, bullets densos, callouts para advertencias
  visuales_sugeridos:
    - diagrama de flujo del generador (arquitectura.flujo)
    - matriz de correlación de latentes (arquitectura.latentes.correlacion) como heatmap
    - tabla de parámetros agrupada por bloque con chip de color por origen
    - tabla de las 37 variables con barras de IV y marcas de banda (calibracion.bandas_iv)
    - gráfico de barras de pruebas OK por paso (pruebas.por_paso)
    - gráfico de AUC con intervalos de confianza por metodología (comparacion_modelos.resultados)
  graficos: solo con números de DATA; indicar la fuente (clave de DATA) al pie de cada gráfico
entregable: documento de varias páginas en el orden de la sección 2
```

## 2. ESTRUCTURA DEL DOCUMENTO (orden fijo → clave de DATA que alimenta cada sección)

| # | Sección | Contenido esperado | Clave(s) de DATA |
|---|---|---|---|
| 1 | Propósito y alcance | para qué sirve y para qué NO (tasas reales, causalidad) | meta, limitaciones |
| 2 | Arquitectura del generador | flujo, latentes, motores de señal, evento común, identidad contable, semillas | arquitectura |
| 3 | Parámetros | tablas por bloque (prefijo de `param`), origen y nota; resumen por origen | parametros |
| 4 | Supuestos | parámetros con origen Supuesto, agrupados por tema; riesgo si son falsos | parametros (origen = Supuesto), limitaciones |
| 5 | La base resultante | tamaño, concentración, target, exclusiones | base_observada |
| 6 | Las 37 variables | mecanismo, motor, NULL, alerta, IV, lift, fuerza y factibilidad del Excel | variables_37, calibracion |
| 7 | Calibración de la señal | bandas, tolerancia, criterio entre semillas, AUC combinado vs techo | calibracion |
| 8 | Pruebas estadísticas | familias, conteo por paso, corrección BH | pruebas |
| 9 | Correcciones y sesgos detectados | qué se corrigió y por qué no es sobreajuste | correcciones_y_sesgos_detectados |
| 10 | Variable de churn construida | definiciones, logo vs AUM churn, ruido de etiqueta | base_observada.churn_construido |
| 11 | Comparación de metodologías | tabla y gráfico de AUC con IC; lectura | comparacion_modelos |
| 12 | Hallazgos para Citizens | lista accionable | hallazgos_para_citizens |
| 13 | Decisiones (trazabilidad) | tabla D-01…D-25 | decisiones |
| 14 | Limitaciones | lista | limitaciones |
| 15 | Reproducibilidad | comandos, control por hashes, repositorio | reproducibilidad |

Resumen de parámetros por origen: Supuesto (simulación, sin etiqueta): 146, Supuesto: 97, Calibrado: 30, Excel: 13, Deck: 5 (total 291).

## 3. DATA

```yaml
meta:
  proyecto: Client Pulse · base sintética de attrition
  cliente: Citizens Private Bank (EE. UU.)
  etiqueta_obligatoria: '[SINT]'
  moneda: USD
  unidad: hogar (household/relationship)
  corte_T0: '2025-12-31'
  semilla_maestra: 20260928
  insumos:
  - Excel Client_Pulse_37_Variables.xlsx (37 variables, umbrales, fuerza, factibilidad)
  - Deck Client_Pulse_AI_Solution_Citizens.v3.pptx (framework, modelos, churn rate)
base_observada:
  hogares: 20000
  uhnw: 1103
  aum_total_usd_mm: 207638.8
  top5pct_share_valor: 0.375
  valor_mediano_usd: 4841541.0
  solo_depositos_pct: 0.143
  hard_churn_6m: 0.0604
  soft_churn_3m: 0.0883
  excluidos: 123
  churn_construido:
    hard_6m: 0.0604
    soft_3m: 0.1099
    aum_churn_hard: 0.0636
    coincidencia_hard: 100% (misma población de eventos)
    soft_falsos_positivos: 500
    soft_no_detectados: 72
arquitectura:
  flujo:
  - 'Paso 0: población, factores latentes, target, ingresos'
  - 'Evento común: mudanza del banco principal (propensión)'
  - 'Paso 1: series mensuales de depósitos y AUM (24 m)'
  - 'Paso 2: transacciones recurrentes + detección'
  - 'Paso 3: transferencias externas + identidad contable'
  - 'Paso 4: composición del portafolio'
  - 'Paso 5: cuentas, cierres, share of wallet, trustee'
  - 'Paso 6: carteras de banker + bitácora'
  - 'Paso 7: quejas + Assistant'
  - 'Paso 8: multi-señal + buró + base final'
  - 'Resultado: ventana (t, t+6m] y variable de churn construida'
  - 'Scoring: 6 metodologías comparadas'
  latentes:
    factores:
    - outflow
    - neglect
    - service
    correlacion:
    - - 1.0
      - 0.35
      - 0.25
    - - 0.35
      - 1.0
      - 0.3
    - - 0.25
      - 0.3
      - 1.0
    pesos_en_riesgo:
      outflow: 0.6
      neglect: 0.45
      service: 0.35
    sd_idiosincratico: 0.6
    rol_idiosincratico: 'riesgo no observable: acota el AUC alcanzable (techo 0.851)'
  motores_de_senal:
    propension: índice de riesgo total; para precursores directos de salida (Very high)
    factor: un solo latente (z_outflow, z_neglect o z_service)
    regla: ninguna variable se genera desde el target; la fuga se prueba en el generador (Wald)
  semillas: 'SeedManager: un flujo aleatorio por nombre (SHA-256 + numpy SeedSequence); agregar o reordenar variables no altera lo ya generado'
  coherencia:
  - la mudanza se ve a la vez en saldos, ingresos, transferencias, inversiones, cierres y buró
  - 'identidad contable mensual: ΔD = ingresos + internos + entradas − salidas − tarjeta − otros débitos (cuadra al centavo)'
parametros:
- param: master_seed
  valor: 20260928
  origen: Supuesto (simulación, sin etiqueta)
  nota: Única semilla del proyecto; todo deriva de aquí.
- param: n_households
  valor: 20000
  origen: Supuesto
  nota: Tamaño suficiente para IV/WoE y ML estable.
- param: snapshot_date
  valor: '2025-12-31'
  origen: Excel
  nota: t = corte mensual.
- param: currency
  valor: USD
  origen: Supuesto (simulación, sin etiqueta)
  nota: 'Banco de EE. UU.: todos los montos en dólares nominales, sin FX.'
- param: population.relationship_value_median
  valor: 4000000
  origen: Supuesto
  nota: null
- param: population.relationship_value_sigma
  valor: 1.2
  origen: Supuesto
  nota: null
- param: population.relationship_value_min
  valor: 1000000
  origen: Supuesto
  nota: piso de Private Bank.
- param: population.uhnw_threshold
  valor: 30000000
  origen: Deck
  nota: '"UHNW (above $30M)".'
- param: population.pareto_tail_alpha
  valor: 1.5
  origen: Supuesto
  nota: ajuste D-13.
- param: population.pareto_tail_max
  valor: 1000000000
  origen: Supuesto
  nota: 'tope: evita varianza infinita.'
- param: population.deposit_only_p_at_median
  valor: 0.15
  origen: Supuesto
  nota: null
- param: population.deposit_only_slope
  valor: -0.8
  origen: Supuesto
  nota: null
- param: population.deposit_share_beta
  valor:
  - 2.0
  - 5.0
  origen: Supuesto
  nota: null
- param: population.age_mean
  valor: 61
  origen: Supuesto
  nota: null
- param: population.age_sd
  valor: 12
  origen: Supuesto
  nota: null
- param: population.age_bounds
  valor:
  - 28
  - 95
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: population.tenure_gamma
  valor:
  - 2.0
  - 4.5
  origen: Supuesto
  nota: media 9 años.
- param: population.tenure_max_years
  valor: 50
  origen: Supuesto
  nota: tope de cola.
- param: population.history_months_cap
  valor: 24
  origen: Deck
  nota: null
- param: population.p_linked_business
  valor: 0.25
  origen: Supuesto
  nota: null
- param: population.p_linked_business_uhnw
  valor: 0.55
  origen: Supuesto
  nota: null
- param: population.p_trust
  valor: 0.3
  origen: Supuesto
  nota: null
- param: population.p_trust_uhnw
  valor: 0.7
  origen: Supuesto
  nota: null
- param: population.p_advisory_given_investments
  valor: 0.7
  origen: Supuesto
  nota: null
- param: population.p_credit_anchor
  valor: 0.35
  origen: Supuesto
  nota: null
- param: population.p_payroll_if_working
  valor: 0.8
  origen: Supuesto
  nota: 'trabajan: edad < retirement_age.'
- param: population.p_payroll_if_retired
  valor: 0.1
  origen: Supuesto
  nota: null
- param: population.p_pension_if_retired
  valor: 0.85
  origen: Supuesto
  nota: null
- param: population.p_pension_if_working
  valor: 0.05
  origen: Supuesto
  nota: null
- param: population.p_dividend_stream_given_investments
  valor: 0.55
  origen: Supuesto
  nota: null
- param: population.retirement_age
  valor: 65
  origen: Supuesto
  nota: null
- param: income.salary_base_median
  valor: 350000
  origen: Supuesto
  nota: profesionales / ejecutivos PB.
- param: income.salary_sigma
  valor: 0.55
  origen: Supuesto
  nota: p5 ≈ $150k, p95 ≈ $850k antes del ajuste por patrimonio.
- param: income.salary_wealth_corr
  valor: 0.45
  origen: Supuesto
  nota: null
- param: income.salary_min
  valor: 150000
  origen: Supuesto
  nota: piso de nómina PB.
- param: income.p_no_bonus
  valor: 0.25
  origen: Supuesto
  nota: médicos, abogados socios, etc.
- param: income.bonus_share_min
  valor: 0.1
  origen: Supuesto
  nota: null
- param: income.bonus_share_beta
  valor:
  - 1.5
  - 3.0
  origen: Supuesto
  nota: null
- param: income.bonus_share_max
  valor: 1.5
  origen: Supuesto
  nota: null
- param: income.pay_frequency
  valor:
    biweekly: 0.4
    semimonthly: 0.45
    monthly: 0.15
  origen: Supuesto
  nota: null
- param: income.pension_monthly_median
  valor: 9000
  origen: Supuesto
  nota: null
- param: income.pension_sigma
  valor: 0.5
  origen: Supuesto
  nota: null
- param: income.pension_wealth_corr
  valor: 0.3
  origen: Supuesto
  nota: null
- param: income.pension_monthly_min
  valor: 2500
  origen: Supuesto
  nota: null
- param: income.dividend_yield_beta
  valor:
  - 4.0
  - 196.0
  origen: Supuesto
  nota: null
- param: income.business_distribution_median
  valor: 500000
  origen: Supuesto
  nota: null
- param: income.business_distribution_sigma
  valor: 0.9
  origen: Supuesto
  nota: null
- param: income.business_distribution_wealth_corr
  valor: 0.5
  origen: Supuesto
  nota: null
- param: latent.factors
  valor:
  - outflow
  - neglect
  - service
  origen: Deck
  nota: null
- param: latent.risk_weights
  valor:
    outflow: 0.6
    neglect: 0.45
    service: 0.35
  origen: Supuesto
  nota: null
- param: latent.tenure_effect_per_log_year
  valor: -0.15
  origen: Supuesto
  nota: más antigüedad -> menos riesgo.
- param: latent.credit_anchor_effect
  valor: -0.2
  origen: Supuesto
  nota: null
- param: latent.uhnw_effect
  valor: 0.1
  origen: Supuesto
  nota: ligero, para que AUM churn ≠ logo churn.
- param: latent.idiosyncratic_sd
  valor: 0.6
  origen: Supuesto
  nota: null
- param: distributions.t_df
  valor: 6
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: target.hard_churn_6m_rate
  valor: 0.06
  origen: Deck
  nota: '[Supuesto anclado al deck]'
- param: target.hard_churn_slope
  valor: 1.6
  origen: Supuesto
  nota: pendiente logística sobre el índice.
- param: target.soft_churn_threshold
  valor: 0.2
  origen: Deck
  nota: '"AUM drop >20%" (a validar).'
- param: target.soft_churn_3m_rate
  valor: 0.09
  origen: Supuesto
  nota: sobre hogares elegibles; hard y soft son excluyentes.
- param: target.soft_churn_slope
  valor: 1.2
  origen: Supuesto
  nota: null
- param: target.soft_churn_loss_range
  valor:
  - 0.2
  - 0.6
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: target.exclusion_rate
  valor: 0.006
  origen: Supuesto
  nota: null
- param: exit_move.move_intercept
  valor: -7.6
  origen: Calibrado
  nota: ≈ 5% de hogares
- param: exit_move.move_slope
  valor: 4.2
  origen: Calibrado
  nota: null
- param: exit_move.move_window_days
  valor: 180
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: exit_move.p_stop_given_move
  valor:
    payroll: 0.85
    pension: 0.45
    dividend: 0.3
    business_distribution: 0.4
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: exit_move.deposit_transfer_p
  valor: 0.9
  origen: Supuesto
  nota: null
- param: exit_move.deposit_transfer_share
  valor:
  - 0.3
  - 0.9
  origen: Supuesto
  nota: fracción del saldo de depósitos
- param: exit_move.deposit_tranches
  valor:
  - 2
  - 6
  origen: Supuesto
  nota: tramos mensuales consecutivos desde el mes de la mudanza (D-18)
- param: exit_move.aum_transfer_p
  valor: 0.8
  origen: Calibrado
  nota: ACATS, entre hogares con inversiones (D-18)
- param: exit_move.aum_transfer_share
  valor:
  - 0.2
  - 0.8
  origen: Supuesto
  nota: fracción del AUM
- param: exit_move.acats_lag_days
  valor:
  - 0
  - 120
  origen: Calibrado
  nota: el ACATS llega semanas o meses después (D-18)
- param: step1.months
  valor: 24
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step1.min_balance_for_pct
  valor: 10000
  origen: Excel
  nota: saldo mínimo para %.
- param: step1.deposit_drift_monthly
  valor: 0.002
  origen: Supuesto
  nota: null
- param: step1.deposit_sigma_monthly
  valor: 0.12
  origen: Calibrado
  nota: volatilidad del saldo PB (D-18)
- param: step1.market_mu_monthly
  valor: 0.006
  origen: Supuesto
  nota: ≈ 7% anual.
- param: step1.market_sigma_monthly
  valor: 0.04
  origen: Supuesto
  nota: ≈ 14% anual.
- param: step1.equity_share_range
  valor:
  - 0.3
  - 1.0
  origen: Supuesto
  nota: beta del portafolio al mercado.
- param: step1.non_equity_return_monthly
  valor: 0.003
  origen: Supuesto
  nota: renta fija / cash.
- param: step1.idio_return_sigma
  valor: 0.01
  origen: Supuesto
  nota: null
- param: step1.advisory_fee_annual
  valor: 0.01
  origen: Supuesto
  nota: cuentas advisory
- param: step1.fund_expense_annual
  valor: 0.002
  origen: Supuesto
  nota: resto
- param: step1.manager_skill_sigma_annual
  valor: 0.015
  origen: Supuesto
  nota: null
- param: step1.alpha_service_loading_annual
  valor: 0.02
  origen: Calibrado
  nota: 'κ: por 1 d.e. de z_service'
- param: step1.contribution_p
  valor: 0.12
  origen: Supuesto
  nota: P(aporte en el mes)
- param: step1.contribution_median
  valor: 0.02
  origen: Supuesto
  nota: null
- param: step1.withdrawal_p
  valor: 0.2
  origen: Supuesto
  nota: retiros para gasto corriente
- param: step1.withdrawal_median
  valor: 0.01
  origen: Supuesto
  nota: null
- param: step1.flow_sigma
  valor: 0.8
  origen: Supuesto
  nota: σ log de los montos
- param: step1.episode_intercept
  valor: -4.0
  origen: Calibrado
  nota: tasa base de episodios (recalibrado con la mudanza, D-17)
- param: step1.episode_slope
  valor: 1.4
  origen: Calibrado
  nota: fuerza predictiva (IV)
- param: step1.episode_max_months
  valor: 6
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step1.episode_delta_median
  valor: 0.12
  origen: Calibrado
  nota: ≈ 12% mensual antes del multiplicador de canal
- param: step1.episode_delta_sigma
  valor: 0.5
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step1.episode_channel_range_deposit
  valor:
  - 1.0
  - 2.0
  origen: Calibrado
  nota: multiplicador de δ en depósitos
- param: step1.episode_channel_range_aum
  valor:
  - 0.3
  - 1.1
  origen: Calibrado
  nota: multiplicador de δ en AUM
- param: step1.shock_p_12m
  valor: 0.1
  origen: Supuesto
  nota: null
- param: step1.shock_size_median
  valor: 0.25
  origen: Supuesto
  nota: fracción que sale en el mes
- param: step1.shock_size_sigma
  valor: 0.5
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step1.shock_hits_aum_p
  valor: 0.5
  origen: Supuesto
  nota: null
- param: step2.history_days
  valor: 548
  origen: Supuesto (simulación, sin etiqueta)
  nota: 18 meses de transacciones.
- param: step2.net_pay_ratio_salary
  valor: 0.62
  origen: Supuesto
  nota: neto / bruto (impuestos PB + 401k).
- param: step2.net_pay_ratio_pension
  valor: 0.85
  origen: Supuesto
  nota: null
- param: step2.amount_noise_sd
  valor: 0.01
  origen: Supuesto
  nota: variación del monto por pago.
- param: step2.dividend_amount_noise_sd
  valor: 0.1
  origen: Supuesto
  nota: null
- param: step2.business_distribution_amount_noise_sd
  valor: 0.35
  origen: Supuesto
  nota: distribuciones irregulares.
- param: step2.late_payment_p
  valor: 0.03
  origen: Supuesto
  nota: pago corrido 1–3 días hábiles.
- param: step2.missed_payment_p_per_year
  valor: 0.01
  origen: Supuesto
  nota: un pago que no llega.
- param: step2.bonus_months
  valor:
  - 2
  - 3
  - 12
  origen: Supuesto
  nota: mes del bono (feb, mar, dic).
- param: step2.business_payroll_frequency
  valor:
    biweekly: 0.6
    semimonthly: 0.4
  origen: Supuesto
  nota: null
- param: step2.partial_intercept
  valor: -3.8
  origen: Calibrado
  nota: null
- param: step2.partial_slope
  valor: 1.5
  origen: Calibrado
  nota: null
- param: step2.partial_factor_range
  valor:
  - 0.2
  - 0.6
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step2.business_move_intercept
  valor: -5.0
  origen: Calibrado
  nota: null
- param: step2.business_move_slope
  valor: 3.0
  origen: Calibrado
  nota: null
- param: step2.job_change_p_12m
  valor: 0.05
  origen: Supuesto
  nota: null
- param: step2.job_change_ratio_sigma
  valor: 0.35
  origen: Supuesto
  nota: nuevo sueldo / anterior ~ LogNormal(0, σ)
- param: step2.job_change_gap_days
  valor:
  - 0
  - 45
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step2.retirement_p_12m
  valor: 0.1
  origen: Supuesto
  nota: titulares de 60 a 67 años con nómina
- param: step2.retirement_age_range
  valor:
  - 60
  - 67
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step2.retirement_reported_p
  valor: 0.8
  origen: Supuesto
  nota: si se reporta → exclusión
- param: step2.leave_p_12m
  valor: 0.01
  origen: Supuesto
  nota: licencia (60–120 días sin nómina)
- param: step2.leave_reported_p
  valor: 0.7
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step2.death_reported_p
  valor: 0.8
  origen: Supuesto (simulación, sin etiqueta)
  nota: hogares excluidos del target (Paso 0)
- param: step2.business_sale_p_12m
  valor: 0.015
  origen: Supuesto
  nota: venta del negocio → exclusión
- param: step2.detection.min_occurrences
  valor: 3
  origen: Excel
  nota: null
- param: step2.detection.cv_max
  valor: 0.25
  origen: Excel
  nota: null
- param: step2.detection.payroll_lookback_days
  valor: 180
  origen: Excel
  nota: ≥ 3 en 6 meses (nómina)
- param: step2.detection.recurring_lookback_days
  valor: 365
  origen: Excel
  nota: ≥ 3 en 12 meses (otros flujos)
- param: step2.detection.stop_days_min
  valor: 45
  origen: Excel
  nota: null
- param: step2.detection.stop_interval_multiple
  valor: 1.5
  origen: Excel
  nota: null
- param: step2.detection.min_stream_weight
  valor: 0.1
  origen: Excel
  nota: null
- param: step2.detection.replacement_min_ratio
  valor: 0.5
  origen: Excel
  nota: null
- param: step2.detection.bonus_multiple
  valor: 2.0
  origen: Excel
  nota: crédito > 2× la mediana del originador = bono (se excluye)
- param: step2.detection.business_stop_days
  valor: 60
  origen: Excel
  nota: null
- param: step3.history_days
  valor: 548
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.outflow_baseline_floor_monthly
  valor: 10000
  origen: Supuesto
  nota: piso PB; el Excel propone $1,000 (D-18)
- param: step3.new_destination_min_cumulative
  valor: 50000
  origen: Supuesto
  nota: piso PB; el Excel propone $10,000 (D-18)
- param: step3.lookback_new_destination_days
  valor: 365
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.institutions
  valor:
    private_bank: 15
    national_bank: 6
    regional_bank: 25
    digital_bank: 10
    broker_wealth: 20
    credit_union: 10
    title_escrow: 15
    other: 10
  origen: Supuesto
  nota: nº de instituciones por tipo del catálogo sintético
- param: step3.aba_per_institution
  valor:
  - 1
  - 3
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.competitor_types
  valor:
  - private_bank
  - national_bank
  - regional_bank
  - digital_bank
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.investment_cash_share_beta
  valor:
  - 2.0
  - 18.0
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.regular_payees_poisson
  valor: 1.5
  origen: Supuesto (simulación, sin etiqueta)
  nota: nº = 1 + Poisson
- param: step3.regular_payee_types
  valor:
    national_bank: 0.35
    regional_bank: 0.15
    broker_wealth: 0.25
    digital_bank: 0.1
    credit_union: 0.05
    other: 0.1
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.background_transfers_per_month
  valor: 4
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.background_monthly_share_median
  valor: 0.005
  origen: Calibrado
  nota: null
- param: step3.background_monthly_share_sigma
  valor: 0.5
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.background_amount_sigma
  valor: 0.4
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.one_off_p_month
  valor: 0.02
  origen: Calibrado
  nota: null
- param: step3.one_off_amount_median
  valor: 15000
  origen: Supuesto
  nota: null
- param: step3.one_off_amount_sigma
  valor: 1.0
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.one_off_types
  valor:
    title_escrow: 0.2
    other: 0.4
    regional_bank: 0.15
    national_bank: 0.15
    broker_wealth: 0.1
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.shock_real_estate_p
  valor: 0.6
  origen: Supuesto (simulación, sin etiqueta)
  nota: 'choque del Paso 1: compra de casa (title/escrow); si no, IRS (excluido)'
- param: step3.episode_destination
  valor:
    spending: 0.45
    competitor_bank: 0.22
    broker: 0.23
    existing_payee: 0.1
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.acats_to_broker_p
  valor: 0.7
  origen: Supuesto (simulación, sin etiqueta)
  nota: el resto va al brazo wealth del banco nuevo
- param: step3.billers_per_month
  valor: 3
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.biller_amount_median
  valor: 2500
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.biller_amount_sigma
  valor: 1.0
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.estimated_tax_rate
  valor: 0.3
  origen: Supuesto (simulación, sin etiqueta)
  nota: 'IRS: pagos estimados trimestrales ≈ 30% del ingreso / 4'
- param: step3.donation_p
  valor: 0.3
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.donation_monthly_median
  valor: 2000
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.loan_payment_median
  valor: 8000
  origen: Supuesto (simulación, sin etiqueta)
  nota: hogares con crédito ancla (pago a Citizens)
- param: step3.card_spending_share_of_income
  valor:
  - 0.2
  - 0.5
  origen: Supuesto (simulación, sin etiqueta)
  nota: débitos internos (tarjeta, cheques)
- param: step3.incoming_transfers_per_month
  valor:
  - 1
  - 3
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step3.iv_tolerance
  valor: 0.03
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step4.benchmark_tilt_sigma
  valor: 0.08
  origen: Supuesto
  nota: null
- param: step4.liquidation_intercept
  valor: -3.6
  origen: Calibrado
  nota: null
- param: step4.liquidation_slope
  valor: 1.7
  origen: Calibrado
  nota: sobre z_outflow
- param: step4.liquidation_share
  valor:
  - 0.15
  - 0.6
  origen: Supuesto (simulación, sin etiqueta)
  nota: fracción del AUM vendida a cash
- param: step4.liquidation_window_days
  valor: 150
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step4.liquidation_full_position_share_beta
  valor:
  - 1.5
  - 4.0
  origen: Supuesto (simulación, sin etiqueta)
  nota: parte vendida en posiciones completas (#34)
- param: step4.proprietary_p
  valor: 0.5
  origen: Supuesto
  nota: no todos tienen fondos propietarios
- param: step4.proprietary_share
  valor:
  - 0.05
  - 0.25
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step4.proprietary_sale_lead_days
  valor:
  - 0
  - 30
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step4.advisor_derisk_p
  valor: 0.05
  origen: Supuesto
  nota: null
- param: step4.advisor_derisk_pp
  valor:
  - 0.05
  - 0.15
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step4.rebalance_p_month
  valor: 0.15
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step4.rebalance_share
  valor:
  - 0.02
  - 0.1
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step4.client_full_sale_p_90d
  valor: 0.08
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step4.client_full_sale_share
  valor:
  - 0.01
  - 0.06
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step4.rmd_age
  valor: 73
  origen: Supuesto (simulación, sin etiqueta)
  nota: 'RMD de diciembre: excluida de #9'
- param: step4.rmd_rate
  valor: 0.04
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step4.cash_noise_pp_monthly
  valor: 0.01
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step4.maturity_p_90d_given_fi
  valor: 0.3
  origen: Supuesto
  nota: null
- param: step4.maturity_share_of_fi
  valor:
  - 0.05
  - 0.3
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step4.reinvest_full_p
  valor: 0.65
  origen: Supuesto
  nota: reinversión normal completa
- param: step4.reinvest_partial_beta
  valor:
  - 2.0
  - 2.0
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step4.nonreinvest_liquidation_p
  valor: 0.85
  origen: Supuesto (simulación, sin etiqueta)
  nota: si el hogar está liquidando / mudándose, no reinvierte
- param: step4.iv_tolerance
  valor: 0.03
  origen: Supuesto (simulación, sin etiqueta)
  nota: 'política general desde el Paso 3 (D-18): bandas = priors expertos'
- param: step5.p_savings
  valor: 0.7
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.p_money_market
  valor: 0.5
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.p_cd
  valor: 0.35
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.p_credit_card
  valor: 0.6
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.extra_accounts_poisson
  valor:
    HNW: 0.4
    UHNW: 1.2
  origen: Supuesto (simulación, sin etiqueta)
  nota: cuentas adicionales por producto
- param: step5.move_close_p
  valor:
    checking: 0.45
    savings: 0.55
    money_market: 0.55
    cd: 0.4
    brokerage: 0.6
    advisory: 0.6
    credit_card: 0.35
    credit_line: 0.2
    business_account: 0.3
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.move_close_lag_days
  valor:
  - 0
  - 90
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.episode_close_p
  valor: 0.3
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.cd_maturity_p_90d
  valor: 0.12
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.cd_renewed_p
  valor: 0.7
  origen: Supuesto (simulación, sin etiqueta)
  nota: renovado → excluido
- param: step5.random_close_p_90d
  valor: 0.01
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.loan_paid_at_term_p_90d
  valor: 0.02
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.conversion_p_90d
  valor: 0.02
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.consolidation_p_90d
  valor: 0.03
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.sow_logit_intercept
  valor: 0.0
  origen: Supuesto
  nota: SOW mediano ≈ 50%
- param: step5.sow_logit_zout
  valor: 0.3
  origen: Calibrado
  nota: null
- param: step5.sow_logit_noise
  valor: 0.9
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.wealth_sources
  valor:
    declared: 0.4
    vendor: 0.45
    model: 0.15
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.wealth_noise_sigma
  valor:
    declared: 0.1
    vendor: 0.35
    model: 0.5
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.estimate_updated_6m_p
  valor: 0.1
  origen: Supuesto (simulación, sin etiqueta)
  nota: si se reestimó, el cambio de SOW refleja la nueva estimación
- param: step5.trustee_move_p
  valor: 0.4
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.trustee_service_intercept
  valor: -4.5
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.trustee_service_slope
  valor: 0.8
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.trustee_noise_p_12m
  valor: 0.01
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.trustee_death_succession_p_12m
  valor: 0.01
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step5.iv_tolerance
  valor: 0.03
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step6.book_size
  valor:
    HNW: 60
    UHNW: 25
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step6.book_sort_noise
  valor: 0.5
  origen: Calibrado
  nota: null
- param: step6.departure_intercept
  valor: -3.2
  origen: Calibrado
  nota: ≈ 10% de bankers en 6 meses
- param: step6.departure_slope
  valor: 2.0
  origen: Calibrado
  nota: null
- param: step6.client_request_intercept
  valor: -4.2
  origen: Supuesto (simulación, sin etiqueta)
  nota: cambio pedido por el cliente (z_service)
- param: step6.client_request_slope
  valor: 0.9
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step6.rebalance_p_6m
  valor: 0.03
  origen: Supuesto (simulación, sin etiqueta)
  nota: 'ruido: rebalanceo de carteras'
- param: step6.temporary_coverage_p_6m
  valor: 0.05
  origen: Supuesto (simulación, sin etiqueta)
  nota: excluida (< 30 días)
- param: step6.cadence_days
  valor:
    HNW: 90
    UHNW: 30
  origen: Excel
  nota: null
- param: step6.banker_diligence_sigma
  valor: 0.3
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step6.contact_neglect_loading
  valor: 0.8
  origen: Calibrado
  nota: null
- param: step6.outreach_per_cadence
  valor: 2.5
  origen: Supuesto (simulación, sin etiqueta)
  nota: contactos del banker por período de cadencia
- param: step6.channel_mix
  valor:
    call: 0.45
    email: 0.3
    message: 0.25
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step6.call_minutes_median
  valor: 12
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step6.call_minutes_sigma
  valor: 0.8
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step6.mass_mailings_per_90d
  valor: 2
  origen: Supuesto (simulación, sin etiqueta)
  nota: excluidos
- param: step6.reply_intercept
  valor: 0.9
  origen: Supuesto (simulación, sin etiqueta)
  nota: P(respuesta ≤ 7 días) = logit⁻¹(a − b · z_neglect)
- param: step6.reply_neglect_slope
  valor: 1.1
  origen: Calibrado
  nota: null
- param: step6.reply_after_move_factor
  valor: 0.4
  origen: Supuesto (simulación, sin etiqueta)
  nota: quien se está mudando deja de contestar
- param: step6.welcome_call_p
  valor: 0.7
  origen: Supuesto (simulación, sin etiqueta)
  nota: tras un cambio de banker, dentro de 14 días
- param: step6.meetings_per_6m
  valor:
    HNW: 2
    UHNW: 6
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step6.cancel_intercept
  valor: -2.2
  origen: Supuesto (simulación, sin etiqueta)
  nota: P(cancelada por el cliente) = logit⁻¹(a + b · z_neglect)
- param: step6.cancel_neglect_slope
  valor: 0.8
  origen: Calibrado
  nota: null
- param: step6.cancel_after_move_add
  valor: 1.5
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step6.cancelled_by_captured_p
  valor: 0.4
  origen: Supuesto (simulación, sin etiqueta)
  nota: solo 40% de los bankers registra "cancelado por"
- param: step6.iv_tolerance
  valor: 0.03
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.complaint_base_rate_12m
  valor: 0.07
  origen: Calibrado
  nota: ≈ 16% de hogares con queja al año
- param: step7.complaint_service_loading
  valor: 1.4
  origen: Calibrado
  nota: pocos se quejan, y esos repiten
- param: step7.complaint_neglect_loading
  valor: 0.3
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.categories
  valor:
    fees_pricing: 0.18
    process_delay: 0.2
    banker_attention: 0.14
    digital: 0.14
    transfers_wires: 0.1
    statement_error: 0.08
    investment_performance: 0.1
    fraud_dispute: 0.06
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.sla_days
  valor:
    fees_pricing: 20
    process_delay: 30
    banker_attention: 15
    digital: 10
    transfers_wires: 10
    statement_error: 15
    investment_performance: 30
    fraud_dispute: 45
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.noise_complaints_12m
  valor: 0.04
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.noise_categories
  valor:
  - fraud_dispute
  - statement_error
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.acats_complaint_p
  valor: 0.2
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.resolution_median_days
  valor: 16
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.resolution_sigma
  valor: 0.9
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.resolution_service_loading
  valor: 0.6
  origen: Supuesto (simulación, sin etiqueta)
  nota: las quejas de clientes con S alto tardan más
- param: step7.escalation_intercept
  valor: -2.6
  origen: Supuesto (simulación, sin etiqueta)
  nota: P(escalada) = logit⁻¹(a + b · z_service + c · fuera de SLA)
- param: step7.escalation_service_slope
  valor: 0.6
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.escalation_out_of_sla_add
  valor: 1.2
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.escalation_levels
  valor:
    management: 0.55
    ombudsman: 0.15
    regulator: 0.2
    legal: 0.1
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.reopen_intercept
  valor: -2.8
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.reopen_service_slope
  valor: 0.9
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.assistant_pilot_p
  valor: 0.3
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.assistant_live_days
  valor: 60
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.dissatisfaction_intercept
  valor: -3.6
  origen: Supuesto (simulación, sin etiqueta)
  nota: estado real de insatisfacción (30 días)
- param: step7.dissatisfaction_service_slope
  valor: 1.3
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.dissatisfaction_neglect_slope
  valor: 0.5
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.dissatisfaction_move_add
  valor: 3.0
  origen: Supuesto (simulación, sin etiqueta)
  nota: quien se está mudando lo expresa ("moving my money")
- param: step7.assistant_usage_30d_p
  valor: 0.6
  origen: Supuesto (simulación, sin etiqueta)
  nota: conversó con el Assistant en los últimos 30 días
- param: step7.classifier_tpr
  valor: 0.8
  origen: Supuesto (simulación, sin etiqueta)
  nota: con confianza ≥ 0.75
- param: step7.classifier_fpr
  valor: 0.02
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.human_confirm_tp
  valor: 0.95
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.human_confirm_fp
  valor: 0.1
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step7.iv_tolerance
  valor: 0.03
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step8.multi_signal_min_groups
  valor: 3
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: step8.material_not_reinvested_usd
  valor: 100000
  origen: Supuesto (simulación, sin etiqueta)
  nota: '"> 50% and material amount" (#26)'
- param: step8.legal_cleared
  valor: true
  origen: Supuesto (simulación, sin etiqueta)
  nota: 'interruptor: false → la variable queda NULL (FCRA)'
- param: step8.permissible_purpose_p
  valor: 0.95
  origen: Supuesto (simulación, sin etiqueta)
  nota: revisión de cuenta existente con registro de propósito permisible
- param: step8.move_mortgage_elsewhere_p
  valor: 0.4
  origen: Calibrado
  nota: 'propensión: el banco nuevo ofrece hipoteca'
- param: step8.home_purchase_financed_p
  valor: 0.6
  origen: Supuesto (simulación, sin etiqueta)
  nota: compra de casa del Paso 3 financiada
- param: step8.citizens_lender_p
  valor:
    anchor: 0.6
    no_anchor: 0.25
  origen: Supuesto (simulación, sin etiqueta)
  nota: si financia, con Citizens (no cuenta) o con otro
- param: step8.refinance_elsewhere_p_6m
  valor: 0.008
  origen: Calibrado
  nota: ruido
- param: step8.iv_tolerance
  valor: 0.03
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: outcome.months
  valor: 6
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: outcome.hard_churn_residual_share
  valor:
  - 0.0
  - 0.03
  origen: Supuesto (simulación, sin etiqueta)
  nota: saldo que queda tras la salida total
- param: outcome.hard_churn_max_share
  valor: 0.05
  origen: Supuesto (simulación, sin etiqueta)
  nota: 'etiqueta: valor ≤ 5% del valor en t y se mantiene hasta t+6'
- param: outcome.soft_churn_threshold
  valor: 0.2
  origen: Supuesto (simulación, sin etiqueta)
  nota: 'etiqueta: caída ex-mercado > 20% en 3 meses sin salida total'
- param: outcome.soft_churn_window_months
  valor: 3
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: outcome.deposit_sigma_monthly
  valor: 0.12
  origen: Supuesto (simulación, sin etiqueta)
  nota: igual que el Paso 1
- param: outcome.aum_net_flow_sigma_monthly
  valor: 0.02
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: outcome.liquidity_shock_p_month
  valor: 0.01
  origen: Supuesto (simulación, sin etiqueta)
  nota: ruido que puede parecer contracción (compra de casa, impuestos)
- param: outcome.liquidity_shock_size_median
  valor: 0.3
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
- param: outcome.liquidity_shock_size_sigma
  valor: 0.5
  origen: Supuesto (simulación, sin etiqueta)
  nota: null
variables_37:
- id: 1
  variable_excel: aum_outflow
  columna: aum_outflow_pct_90d
  grupo: Balances & AUM
  prioridad: P1
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: derivada de series mensuales de AUM (retiros − aportes, sin ACATS internos)
  motor: mixto
  null_pct: 14.49
  alerta_pct: 7.66
  iv: 0.27
  lift: 3.95
- id: 2
  variable_excel: deposit_balance_change_pct
  columna: deposit_balance_change_pct_90d
  grupo: Balances & AUM
  prioridad: P1
  fuerza_excel: High
  factibilidad: High
  mecanismo: derivada de la serie mensual de depósitos (ruido t(6), episodios, choques, mudanza)
  motor: mixto
  null_pct: 0.55
  alerta_pct: 10.49
  iv: 0.25
  lift: 3.17
- id: 3
  variable_excel: salary_deposit_stopped_flag
  columna: salary_deposit_stopped_flag
  grupo: Recurring deposits & flows
  prioridad: P1
  fuerza_excel: Very high
  factibilidad: Medium
  mecanismo: algoritmo de detección del Excel sobre transacciones de nómina simuladas
  motor: propensión
  null_pct: 47.3
  alerta_pct: 3.64
  iv: 0.32
  lift: 5.71
- id: 4
  variable_excel: recurring_deposit_stopped_flag
  columna: recurring_deposit_stopped_flag
  grupo: Recurring deposits & flows
  prioridad: P1
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: detección sobre todos los flujos recurrentes (≥ 10% del ingreso)
  motor: propensión
  null_pct: 7.46
  alerta_pct: 4.22
  iv: 0.22
  lift: 4.34
- id: 5
  variable_excel: recurring_deposit_change_pct
  columna: recurring_deposit_change_pct
  grupo: Recurring deposits & flows
  prioridad: P1
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: recurrente 30d vs promedio 6m sobre transacciones (bono excluido)
  motor: mixto
  null_pct: 7.4
  alerta_pct: 10.7
  iv: 0.17
  lift: 2.66
- id: 6
  variable_excel: net_deposit_flow
  columna: net_deposit_flow_pct_90d
  grupo: Recurring deposits & flows
  prioridad: P1
  fuerza_excel: High
  factibilidad: High
  mecanismo: cambio de saldo de la serie de depósitos (identidad contable)
  motor: mixto
  null_pct: 0.29
  alerta_pct: 27.72
  iv: 0.24
  lift: 2.04
- id: 7
  variable_excel: external_transfer_pct_of_balance
  columna: external_transfer_pct_of_balance_60d
  grupo: Transfers
  prioridad: P1
  fuerza_excel: Very high
  factibilidad: High
  mecanismo: transferencias externas simuladas una por una (incluye ACATS)
  motor: mixto
  null_pct: 0.08
  alerta_pct: 6.49
  iv: 0.32
  lift: 4.93
- id: 8
  variable_excel: new_external_destinations
  columna: new_external_destinations_90d
  grupo: Transfers
  prioridad: P1
  fuerza_excel: High
  factibilidad: High
  mecanismo: destinos nuevos ≥ $50k sin envíos en 12m previos
  motor: mixto
  null_pct: 3.48
  alerta_pct: 5.95
  iv: 0.29
  lift: 4.36
- id: 9
  variable_excel: investment_redemption_pct
  columna: investment_redemption_pct
  grupo: Investments
  prioridad: P1
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: ventas y redenciones del cliente − compras (composición del portafolio)
  motor: mixto
  null_pct: 14.49
  alerta_pct: 6.19
  iv: 0.17
  lift: 2.88
- id: 10
  variable_excel: products_closed
  columna: products_closed_180d
  grupo: Relationship & closures
  prioridad: P1
  fuerza_excel: Very high
  factibilidad: High
  mecanismo: tabla de cuentas con fecha y motivo de cierre (exclusiones del Excel)
  motor: mixto
  null_pct: 0.53
  alerta_pct: 9.74
  iv: 0.36
  lift: 3.36
- id: 11
  variable_excel: banker_change_6m_flag
  columna: banker_change_6m_flag
  grupo: Banker
  prioridad: P1
  fuerza_excel: Very high
  factibilidad: High
  mecanismo: salida del banker decidida por banker según calidad del libro; todo el libro cambia
  motor: mixto
  null_pct: 0.53
  alerta_pct: 14.85
  iv: 0.44
  lift: 4.1
- id: 12
  variable_excel: contact_gap_ratio
  columna: contact_gap_ratio
  grupo: Banker
  prioridad: P1
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: 'bitácora de interacciones: días sin contacto significativo ÷ cadencia'
  motor: factor (z_neglect)
  null_pct: 0.0
  alerta_pct: 3.67
  iv: 0.17
  lift: 2.0
- id: 13
  variable_excel: client_reply_rate
  columna: client_reply_rate
  grupo: Banker
  prioridad: P1
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: respuestas del cliente ≤ 7d en la bitácora (quien se muda deja de contestar)
  motor: mixto
  null_pct: 47.99
  alerta_pct: 25.5
  iv: 0.24
  lift: 1.95
- id: 14
  variable_excel: complaint_escalated_flag
  columna: complaint_escalated_flag
  grupo: Complaints & voice of client
  prioridad: P1
  fuerza_excel: High
  factibilidad: High
  mecanismo: 'ciclo de vida de quejas: escalamiento según SLA y z_service'
  motor: mixto
  null_pct: 0.0
  alerta_pct: 5.34
  iv: 0.13
  lift: 3.11
- id: 15
  variable_excel: complaint_age_days
  columna: complaint_age_days
  grupo: Complaints & voice of client
  prioridad: P1
  fuerza_excel: High
  factibilidad: High
  mecanismo: antigüedad de la queja abierta más antigua
  motor: mixto
  null_pct: 0.0
  alerta_pct: 1.99
  iv: 0.12
  lift: 3.75
- id: 16
  variable_excel: multi_signal_flag
  columna: multi_signal_flag
  grupo: External & composite
  prioridad: P1
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: nº de grupos del Excel con alguna variable sobre su umbral; flag ≥ 3
  motor: compuesta
  null_pct: 0.0
  alerta_pct: 23.96
  iv: 0.64
  lift: 3.41
- id: 17
  variable_excel: aum_vs_baseline_pct
  columna: aum_vs_baseline_pct
  grupo: Balances & AUM
  prioridad: P2
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: AUM ex-mercado (÷ índice TWR) vs promedio de 6 meses
  motor: mixto
  null_pct: 15.0
  alerta_pct: 6.17
  iv: 0.29
  lift: 5.18
- id: 18
  variable_excel: deposit_balance_vs_6m_avg_pct
  columna: deposit_balance_vs_6m_avg_pct
  grupo: Balances & AUM
  prioridad: P2
  fuerza_excel: High
  factibilidad: High
  mecanismo: depósitos del último mes vs promedio de 6 meses
  motor: mixto
  null_pct: 0.79
  alerta_pct: 9.94
  iv: 0.29
  lift: 3.62
- id: 19
  variable_excel: pension_deposit_stopped_flag
  columna: pension_deposit_stopped_flag
  grupo: Recurring deposits & flows
  prioridad: P2
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: detección sobre transacciones de pensión
  motor: propensión
  null_pct: 65.75
  alerta_pct: 1.95
  iv: 0.22
  lift: 5.81
- id: 20
  variable_excel: business_payroll_stopped_flag
  columna: business_payroll_stopped_flag
  grupo: Recurring deposits & flows
  prioridad: P2
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: detección sobre débitos de la nómina del negocio (60 días)
  motor: factor (z_outflow)
  null_pct: 73.89
  alerta_pct: 5.65
  iv: 0.16
  lift: 3.33
- id: 21
  variable_excel: transfer_to_competitor_bank_amount
  columna: transfer_to_competitor_pct_90d
  grupo: Transfers
  prioridad: P2
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: transferencias a bancos del catálogo sintético de competidores
  motor: mixto
  null_pct: 0.16
  alerta_pct: 5.05
  iv: 0.3
  lift: 6.14
- id: 22
  variable_excel: external_transfer_acceleration
  columna: external_transfer_acceleration
  grupo: Transfers
  prioridad: P2
  fuerza_excel: High
  factibilidad: High
  mecanismo: 'bloques de 30d de salidas externas: [(A1−A2)−(A2−A3)] ÷ saldo'
  motor: mixto
  null_pct: 0.16
  alerta_pct: 4.27
  iv: 0.22
  lift: 4.84
- id: 23
  variable_excel: net_external_flow
  columna: net_external_flow_pct_90d
  grupo: Transfers
  prioridad: P2
  fuerza_excel: High
  factibilidad: High
  mecanismo: entradas − salidas externas (wires/ACH, sin ACATS)
  motor: mixto
  null_pct: 0.16
  alerta_pct: 5.13
  iv: 0.26
  lift: 5.05
- id: 24
  variable_excel: external_destination_concentration
  columna: external_destination_concentration
  grupo: Transfers
  prioridad: P2
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: HHI de salidas por institución (no por ABA)
  motor: mixto
  null_pct: 0.16
  alerta_pct: 6.03
  iv: 0.22
  lift: 4.47
- id: 25
  variable_excel: outflow_vs_baseline_pct
  columna: outflow_vs_baseline_pct
  grupo: Transfers
  prioridad: P2
  fuerza_excel: High
  factibilidad: High
  mecanismo: salidas del último mes vs promedio 6m con piso $10k (forma en U)
  motor: mixto
  null_pct: 0.77
  alerta_pct: 7.6
  iv: 0.11
  lift: 2.37
- id: 26
  variable_excel: fixed_income_maturity_not_reinvested
  columna: fixed_income_maturity_not_reinvested
  grupo: Investments
  prioridad: P2
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: vencimientos de renta fija y reinversión en 30 días
  motor: mixto
  null_pct: 73.91
  alerta_pct: 36.84
  iv: 0.21
  lift: 2.05
- id: 27
  variable_excel: cash_pct_of_portfolio_chg
  columna: cash_pct_of_portfolio_chg
  grupo: Investments
  prioridad: P2
  fuerza_excel: High
  factibilidad: High
  mecanismo: cash % mensual del portafolio (venta a cash, de-risking del asesor)
  motor: mixto
  null_pct: 15.0
  alerta_pct: 7.89
  iv: 0.14
  lift: 2.74
- id: 28
  variable_excel: return_vs_benchmark
  columna: return_vs_benchmark
  grupo: Investments
  prioridad: P2
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: TWR neto 12m (alpha ligado a z_service) − benchmark por perfil
  motor: factor (z_service)
  null_pct: 40.99
  alerta_pct: 31.6
  iv: 0.12
  lift: 1.64
- id: 29
  variable_excel: accounts_closed
  columna: accounts_closed_90d
  grupo: Relationship & closures
  prioridad: P2
  fuerza_excel: High
  factibilidad: High
  mecanismo: cuentas cerradas (solo se excluye consolidación interna)
  motor: mixto
  null_pct: 0.16
  alerta_pct: 14.34
  iv: 0.23
  lift: 1.89
- id: 30
  variable_excel: share_of_wallet
  columna: share_of_wallet
  grupo: Relationship & closures
  prioridad: P2
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: valor en Citizens ÷ patrimonio estimado (3 fuentes de calidad distinta)
  motor: mixto
  null_pct: 0.0
  alerta_pct: 26.65
  iv: 0.27
  lift: 2.21
- id: 31
  variable_excel: share_of_wallet_change
  columna: share_of_wallet_change
  grupo: Relationship & closures
  prioridad: P2
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: SOW hoy − SOW hace 6 meses (reestimación agrega ruido)
  motor: mixto
  null_pct: 0.77
  alerta_pct: 13.69
  iv: 0.22
  lift: 2.65
- id: 32
  variable_excel: trustee_change_flag
  columna: trustee_change_flag
  grupo: Relationship & closures
  prioridad: P2
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: cambio de trustee por mudanza, servicio y ruido; sucesión por muerte excluida
  motor: mixto
  null_pct: 68.13
  alerta_pct: 4.57
  iv: 0.21
  lift: 3.83
- id: 33
  variable_excel: repeat_complaint_flag
  columna: repeat_complaint_flag
  grupo: Complaints & voice of client
  prioridad: P2
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: ≥ 2 quejas de la misma categoría o reapertura
  motor: mixto
  null_pct: 0.0
  alerta_pct: 3.66
  iv: 0.17
  lift: 4.02
- id: 34
  variable_excel: positions_liquidated_pct
  columna: positions_liquidated_pct
  grupo: Investments
  prioridad: P3
  fuerza_excel: High
  factibilidad: Medium
  mecanismo: posiciones vendidas completas sin reemplazo
  motor: mixto
  null_pct: 14.59
  alerta_pct: 1.58
  iv: 0.19
  lift: 3.72
- id: 35
  variable_excel: meetings_cancelled_by_client
  columna: meetings_cancelled_by_client
  grupo: Banker
  prioridad: P3
  fuerza_excel: High
  factibilidad: Low
  mecanismo: reuniones canceladas por el cliente (campo capturado por 40% de bankers)
  motor: mixto
  null_pct: 60.72
  alerta_pct: 5.28
  iv: 0.16
  lift: 2.08
- id: 36
  variable_excel: relationship_dissatisfaction_flag
  columna: relationship_dissatisfaction_flag
  grupo: Complaints & voice of client
  prioridad: P3
  fuerza_excel: High
  factibilidad: Low
  mecanismo: 'Assistant: estado real → conversación → clasificador → revisión humana (solo piloto)'
  motor: mixto
  null_pct: 70.45
  alerta_pct: 4.12
  iv: 0.12
  lift: 2.99
- id: 37
  variable_excel: bureau_new_mortgage_elsewhere
  columna: bureau_new_mortgage_elsewhere
  grupo: External & composite
  prioridad: P3
  fuerza_excel: High
  factibilidad: Low
  mecanismo: 'buró: mudanza, compra de casa financiada fuera, refinanciamiento; interruptor legal'
  motor: mixto
  null_pct: 5.04
  alerta_pct: 3.97
  iv: 0.16
  lift: 3.71
calibracion:
  bandas_iv:
    Very high:
    - 0.3
    - 0.5
    High:
    - 0.1
    - 0.3
    compuesta_multisenal:
    - 0.3
    - 0.8
  tolerancia_iv: 0.03
  criterio_semillas: mediana entre semillas en banda; p10–p90 reportado
  iv_condicional: flags de subpoblación (nómina, pensión, negocio, trust) calibrados entre hogares donde aplican
  auc_combinado_37_variables: 0.762
  auc_techo: 0.851
pruebas:
  correccion_multiple: Benjamini-Hochberg (FDR), α = 0.01
  por_paso:
  - paso: 0
    ok: 202
    total: 202
    semillas_referencia: 200
  - paso: 1
    ok: 54
    total: 54
    semillas_referencia: 20
  - paso: 2
    ok: 71
    total: 71
    semillas_referencia: 20
  - paso: 3
    ok: 71
    total: 71
    semillas_referencia: 20
  - paso: 4
    ok: 53
    total: 53
    semillas_referencia: 20
  - paso: 5
    ok: 56
    total: 56
    semillas_referencia: 20
  - paso: 6
    ok: 40
    total: 40
    semillas_referencia: 20
  - paso: 7
    ok: 38
    total: 38
    semillas_referencia: 20
  - paso: 8
    ok: 24
    total: 24
    semillas_referencia: 10
  familias:
  - familia: bondad de ajuste
    pruebas: KS y Cramér-von Mises sobre PIT; χ² (gl = celdas − 1); binomial exacta; Hosmer-Lemeshow (gl = g − parámetros estimados)
  - familia: colas y curtosis
    pruebas: Anscombe-Glynn, Jarque-Bera (gl = 2), L-momentos, índice de Hill, MLE Pareto truncada, curtosis teórica Normal doblemente truncada
  - familia: multivariadas
    pruebas: Mardia asimetría (gl = 10) y curtosis; Fisher z de correlaciones
  - familia: grados de libertad t-Student
    pruebas: estudio ν = 4, 5, 6, 8 (60 réplicas × 20,000); ν = 6 elegido (curtosis 3 finita; ν = 4 infinita)
  - familia: sesgo y fuga
    pruebas: independencias por diseño (Spearman), χ² de independencia, Wald sobre el generador
  - familia: duplicados y variedad
    pruebas: filas exactas, casi-duplicados por vecino más cercano, repeticiones esperadas por redondeo (Poisson λ)
  - familia: calibración de variables
    pruebas: tasa de alerta, IV, Cochran-Armitage, lift, forma en U
  - familia: robustez de semilla
    pruebas: semillas de referencia, p-valores empíricos, uniformidad de p-valores entre semillas
decisiones:
- id: D-01
  seccion: Paso 0 · Fundaciones
  titulo: Semillas por nombre, no por orden
  detalle: 'Hay una sola semilla maestra (`config/params.yaml → master_seed`). Cada componente pide su generador con `SeedManager.rng("nombre")`,
    derivado de `SeedSequence(master_seed, spawn_key=SHA-256(nombre))`. Consecuencias: · Agregar, quitar o reordenar variables en pasos futuros
    no cambia lo ya generado. · Cambiar la distribución de una columna no mueve otras (lo prueba un test). · No se usa `np.random.seed`, `random.seed`
    ni `hash()` de Python. · Pedir dos veces el mismo nombre da error (evita correlación accidental). · El manifiesto de cada paso lista los flujos
    usados y el SHA-256 de las salidas.'
- id: D-02
  seccion: Paso 0 · Fundaciones
  titulo: Las variables se generan desde factores latentes, nunca desde el target
  detalle: 'Cada hogar tiene tres factores latentes N(0,1) correlacionados (ρ 0.25–0.35), uno por trayectoria de churn del deck (slide 24): `outflow`
    (salida de dinero), `neglect` (deriva silenciosa / abandono del banker) y `service` (fricción de servicio). El target sale de un índice de
    riesgo = combinación de los latentes + efectos estructurales + un **componente idiosincrático no observable**. Las variables del Excel saldrán
    de los latentes + ruido propio. Así: · No hay fuga: ninguna variable "ve" el target. · El AUC queda acotado. El techo (AUC con la probabilidad
    verdadera) es **0.851**; un modelo real sobre variables ruidosas debería quedar por debajo (≈0.72–0.80). Si en un paso futuro un modelo supera
    ese techo, algo está mal. · Las variables de un mismo grupo quedan correlacionadas entre sí pero no son copias, así el scorecard no se queda
    con una sola variable que lo explica todo.'
- id: D-03
  seccion: Paso 0 · Fundaciones
  titulo: Tabla observable y tabla de verdad, separadas
  detalle: '`step0_households.csv` (observables + target) es lo que ve el modelo. `step0_truth.csv` (latentes, índice, probabilidades) solo se
    usa para validar.'
- id: D-04
  seccion: Paso 0 · Fundaciones
  titulo: NULL ≠ cero
  detalle: '[Excel · Base definitions] Cada variable tiene `applies_to` en el catálogo. Fuera de esa subpoblación va NULL. El Paso 0 crea las
    banderas que definen esas subpoblaciones (`has_investments`, `has_payroll_stream`, `has_linked_business`, `has_trust`, `has_advisory`, …).'
- id: D-05
  seccion: Paso 0 · Fundaciones
  titulo: Target
  detalle: '- `hard_churn_6m`: salida total en (t, t+6m]. Tasa 6% **[Validar]**, anclada al deck (3% por trimestre, slide 17). · `soft_churn_3m`:
    contracción > 20% sin salida total en (t, t+3m]. Tasa 9% sobre hogares elegibles **[Validar]**; el umbral de 20% está abierto en el deck (slide
    69). · Hard y soft son excluyentes. · Exclusiones (muerte o reubicación, 0.6%) → target NULL, no churn (slide 59). · El intercepto se calibra
    para que E[p] = tasa exacta (control de calibración, slide 17).'
- id: D-06
  seccion: Paso 0 · Fundaciones
  titulo: Población
  detalle: '**[Validar]** todos los valores: · Valor de la relación ~ LogNormal (mediana $4M, σ 1.2, piso $1M) → UHNW (≥ $30M) ≈ 5.5%. · 15% de
    hogares solo con depósitos; en el resto, la proporción de depósitos ~ Beta(2,5). · Edad ~ Normal truncada (61 ± 12); antigüedad ~ Gamma (media
    9 años, tope 50). · Historia disponible = min(antigüedad, 24 meses): los hogares nuevos tendrán NULL en variables que exigen línea base de
    6 meses. · Business vinculado 25% (55% en UHNW), trust 30% (70% en UHNW).'
- id: D-07
  seccion: Paso 0 · Fundaciones
  titulo: Un solo corte (snapshot) por ahora
  detalle: El Paso 0 genera un corte t = 2025-12-31. El panel mensual (necesario para validar out-of-time, slide 20) se agrega cuando existan
    las variables, reutilizando los latentes con evolución temporal. **[Validar]** si lo quieres desde ya.
- id: D-08
  seccion: Paso 0 · Fundaciones
  titulo: Ingresos de Private Banking
  detalle: 'Los montos de ingreso (sueldo base, bono, pensión, dividendos, distribuciones del negocio) son LogNormales ligadas al log-patrimonio,
    con pisos PB (sueldo ≥ $150k) aplicados por remuestreo. Dependen del patrimonio pero no de los factores de riesgo: el nivel de ingreso es
    estructura, no señal. Resultado: sueldo base mediano $379k (UHNW $585k), bono mediano $167k, ingreso recurrente mensual mediano $31k (UHNW
    $108k). Todo esto está por validar. Agregarlos no cambió ninguna columna previa (flujos de semilla nuevos, D-01). La excepción es `has_any_recurring_stream`,
    que ahora incluye las distribuciones del negocio (+469 hogares).'
- id: D-09
  seccion: Paso 0 · Fundaciones
  titulo: 'Moneda: USD'
  detalle: 'Citizens es un banco de EE. UU.: todos los montos son dólares nominales, sin conversión. `config/params.yaml → currency: USD`. Cada
    columna declara su unidad en `synthetic/schema.py` y el build falla si aparece una columna sin declarar. Las referencias también son de EE.
    UU.: ACH/SEC, ABA/SWIFT, Social Security, IRS, CFPB/OCC, FCRA.'
- id: D-10
  seccion: Paso 0 · Fundaciones
  titulo: Validación estadística
  detalle: '(`scripts/stats_step0.py`, reporte en `docs/reports/step0_stats_report.md`). 200 pruebas, todas OK con α = 0.01 y corrección Benjamini-Hochberg:
    · **Bondad de ajuste:** cada columna contra la distribución y los parámetros con que se generó. Se usa KS y Cramér-von Mises sobre la PIT,
    χ² para edad y frecuencia de pago, y binomial exacta para las banderas. Como no se estima ningún parámetro, los gl son los nominales: χ² gl
    = celdas − 1; Hosmer-Lemeshow gl = grupos − 2; Mardia asimetría gl = p(p+1)(p+2)/6 = 10; independencia gl = (r−1)(c−1); Jarque-Bera gl = 2.
    · **Colas y curtosis:** se exige cola pesada en escala USD (curtosis de exceso > 0 significativa; patrimonio ≈ 376). Tras normalizar por PIT,
    la curtosis debe ser 0 (Anscombe-Glynn, Jarque-Bera). La curtosis de log(patrimonio) coincide con la teórica de la Normal truncada. Se agregan
    L-momentos e índice de Hill, más robustos que la curtosis clásica. · **Dinero:** sin negativos, sin infinitos, al centavo, bajo máximos plausibles;
    medias iguales a las teóricas (prueba t) y dentro de bandas de negocio PB (`config/validation.yaml`). · **Sesgo:** 30 independencias por diseño
    (Spearman), target independiente de atributos sin efecto diseñado (χ²), y efectos diseñados con el signo correcto. · **Duplicados y variedad:**
    0 filas duplicadas, 0 pares casi idénticos (distancia mínima entre vecinos 0.035 d.e.; p1 = 0.17), 303 combinaciones de banderas. Las repeticiones
    de montos coinciden con lo esperado por redondear al centavo (pensión: 15 observadas vs 15.2 esperadas). · **Semilla:** la semilla de producción
    no es atípica frente a 200 semillas de referencia (percentiles 15–92 en las 10 métricas clave). Los p-valores KS entre semillas son uniformes,
    así que el generador no tiene sesgo sistemático.'
- id: D-11
  seccion: Paso 0 · Fundaciones
  titulo: 'Grados de libertad de la t-Student: ν = 6 en lugar de 4'
  detalle: 'El estudio de 60 réplicas × 20,000 muestra que con ν = 4 la curtosis teórica es infinita: la muestral va de 6 a 43 entre réplicas
    (CV 2.0). Así la curtosis no se puede validar y dos semillas darían colas muy distintas. Con ν = 5 sigue siendo inestable (CV 0.45). Con ν
    = 6 queda estable (teórica 3, CV 0.20) y conserva colas pesadas. La máxima verosimilitud recupera ν sin sesgo (< 1%) en todos los casos, así
    que si Citizens entrega datos reales, ν se estima de ellos.'
- id: D-13
  seccion: Paso 0 · Fundaciones
  titulo: Ajustes de plausibilidad aplicados
  detalle: '(antes eran hallazgos pendientes): · **Solo depósitos según patrimonio:** logit p = logit(0.15) − 0.8·lv → ≈ 31% a $1M, 15% a $4M,
    4% a $30M. Resultado: 14.3% en total y 4.2% en UHNW (antes 16.6%). · **Bono:** 25% sin bono (bono = 0, no NULL); el resto recibe 10% + 140%
    × Beta(1.5, 3) del sueldo. · **Cola Pareto:** por encima de $30M, Pareto truncada con α = 1.5 y tope de $1B. Se conserva P(≥ $30M), así que
    el segmento y el target no cambian. La MLE truncada recupera α. · **Grados de libertad de Hosmer-Lemeshow corregidos:** el target solo calibra
    el intercepto en la muestra → gl = g − 1 (antes g − 2). Para solo depósitos, p_i es conocida → gl = g. Contexto histórico de los hallazgos:
    1. **Hogares grandes solo con depósitos.** La probabilidad de no tener inversiones no depende del patrimonio (15% en HNW y UHNW). Hay 183
    hogares de más de $30M solo en depósitos, y uno de $782M que concentra el 0.4% del libro. Por eso la media de depósitos de esta semilla queda
    en el percentil 99.8 (no se rechaza tras BH). Propuesta: que la probabilidad caiga con el patrimonio. 2. **Bonos muy chicos.** 1.5 × Beta(1.5,
    3) produce bonos casi nulos: 123 menores a $10k y 265 menores al 5% del sueldo. Propuesta: una masa de "sin bono" (≈ 25%, p. ej. médicos o
    abogados socios) y, para el resto, un bono con piso de 10% del sueldo. 3. **Cola del patrimonio.** La LogNormal da un índice de Hill de 2.4
    en el top 1%. La riqueza real suele tener una cola Pareto más pesada (α ≈ 1.5). Si importa el peso de los UHNW en el AUM churn, se puede usar
    una cola Pareto por encima de $30M.'
- id: D-12
  seccion: Paso 1 · Balances & AUM (variables 1, 2, 17, 18)
  titulo: Variables calculadas desde series mensuales, no sorteadas
  detalle: 'Cada hogar tiene 24 meses de depósitos (promedio mensual) y AUM (cierre de mes), anclados al Paso 0 en t y simulados hacia atrás,
    así ningún valor del Paso 0 cambia. Componentes: · **Ruido de fondo:** incrementos log de depósitos = 0.2% + 5% · t(6) estandarizada. La prueba
    KS y la MLE (ν̂ ≈ 6) confirman que el ruido de la serie es t(6). · **Mercado:** un rendimiento común por mes (0.6% + 4% · t(6)), una beta
    de renta variable por hogar en [0.3, 1.0] y un índice TWR. Así el AUM ex-mercado (#17) solo se mueve con los flujos del cliente. · **Flujos
    de fondo del AUM** (hurdle): aportes P = 12% (mediana 2%) y retiros P = 20% (mediana 1%). · **Señal:** episodio de salida con P = logit⁻¹(−3.0
    + 2.2 · z_outflow) (≈ 14% de hogares), duración de 1 a 6 meses hasta t, intensidad mensual ~ LogNormal (mediana 14%) con multiplicador por
    canal (depósitos [1.0, 2.0], AUM [0.3, 1.1]). · **Ruido que imita señal:** choque de liquidez independiente del riesgo (10% de hogares en
    12 meses; impuestos o compra de casa; mediana 25% del saldo). Genera falsos positivos realistas: el 12% de los hogares con choque y sin episodio
    dispara la alerta de AUM. · **Ventanas en meses** (aproximación a los días del Excel): 30d = 1, 90d = 3, 180d = 6, línea base (t−210d, t−30d]
    = meses −6..−1. Los meses anteriores a la apertura no existen → NULL. **Resultado** (semilla de producción; 20 semillas de referencia en el
    reporte): | Variable | Alerta | Tasa | IV hard | Lift de la alerta | |---|---|---|---|---| | aum_outflow_pct_90d | > 10% | 13.5% | 0.165 |
    2.5× | | deposit_balance_change_pct_90d | ≤ −25% | 9.7% | 0.149 | 2.5× | | aum_vs_baseline_pct | ≤ −20% | 8.4% | 0.146 | 2.5× | | deposit_balance_vs_6m_avg_pct
    | ≤ −30% | 10.7% | 0.168 | 2.5× | · Las cuatro quedan en la banda "High" (IV 0.10–0.30) en las 20 semillas de referencia. · El AUC combinado
    de las cuatro es 0.60, lejos del techo de 0.85: ninguna variable explica todo. · Correlación de Spearman entre #2 y #18 ≈ 0.90: el par redundante
    del Excel sale redundante, como se esperaba; se decide por IV. · La forma es de palo de hockey (plana en el medio, fuerte en la cola), por
    eso la monotonía se valida con Cochran-Armitage y lift, no con ρ ≈ 1. · **Las dos medidas de AUM no pueden alertar igual:** retiros brutos
    ÷ AUM promedio (#1) siempre alerta más que la caída neta ex-mercado (#17) ante el mismo episodio. Por eso las tasas objetivo son rangos.'
- id: D-14
  seccion: Paso 2 · Recurring deposits & flows (variables 3, 4, 5, 6, 19, 20)
  titulo: 'Dos motores de señal: propensión y factor'
  detalle: 'Con el factor de salida de dinero solo, ni el 3% más riesgoso pasa de 28% de churn, así que ninguna variable generada desde él alcanza
    IV "Very high" (0.30–0.50). El Excel define "Very high" como precursor directo de la salida ("the client is already moving money"). Por eso:
    · **Motor "propensión":** el evento se genera desde el índice de riesgo total del Paso 0. Caso del Paso 2: la mudanza del banco principal,
    P = logit⁻¹(−7.6 + 4.2 · risk_index), ≈ 5% de hogares, que corta nómina (85%), pensión (45%), dividendos (30%) y distribuciones (40%). Estas
    variables se correlacionan con ε por diseño (ρ ≈ 0.13–0.15), no por fuga del target: dependen de la propensión, no del sorteo Bernoulli del
    churn. · **Motor "factor":** redirección parcial del ingreso (z_outflow) y traslado de la nómina del negocio (z_outflow). Estas sí deben ser
    independientes de ε, y lo son (|ρ| < 0.01). · El AUC combinado de los Pasos 1 y 2 es 0.65, todavía lejos del techo de 0.85.'
- id: D-15
  seccion: Paso 2 · Recurring deposits & flows (variables 3, 4, 5, 6, 19, 20)
  titulo: Detección del Excel corrida sobre transacciones simuladas
  detalle: 'Cada crédito recurrente se simula con su fecha durante 18 meses (≈ 520 mil transacciones), sobre un calendario real de EE. UU.: días
    hábiles y feriados federales, nómina catorcenal en viernes, quincenal el 15 y fin de mes, pensión en un día fijo por hogar, dividendos y distribuciones
    trimestrales. Hay pagos corridos (3%) y omitidos (1% por año). Montos netos: nómina 62% del bruto, pensión 85%. Encima se corre el algoritmo
    del Excel: ≥ 3 ocurrencias, CV de intervalos < 0.25, max(45d, 1.5 × intervalo), reemplazo de nómina ≥ 50%, flujos ≥ 10% del ingreso, 60 días
    para la nómina del negocio, y exclusiones de retiro, licencia, muerte y venta del negocio reportados. Resultados del detector: · 0% de falsos
    positivos en hogares sin eventos; 98% de recall en nóminas mudadas hace > 60 días. · El 99% de los cambios de empleo con reemplazo ≥ 50% no
    se marca. · Excluir el bono (> 2× la mediana del originador) importa: t = 31-dic, así que el bono de diciembre cae en la ventana de 30 días
    de #5. Sin la regla, el "aumento de ingreso recurrente" mediano de esos 2,411 hogares sería +396%; con la regla es −1%. · Ruido que se marca
    igual que en la vida real: retiros no reportados, cambios de empleo con sueldo < 50% del anterior, licencias no reportadas, y mudanzas de
    menos de 45 días que todavía no se ven.'
- id: D-16
  seccion: Paso 2 · Recurring deposits & flows (variables 3, 4, 5, 6, 19, 20)
  titulo: 'IV de flags de subpoblación: condicional y con varianza de muestreo'
  detalle: Los flags de nómina, pensión y negocio se calibran con IV entre los hogares donde aplican. Con ~100–300 eventos, el IV varía ±0.08
    entre semillas. Por eso se exige que la semilla de producción y la mediana entre 20 semillas caigan en la banda, y se reporta p10–p90. La
    semilla de producción queda del lado bajo (nómina 0.32 vs mediana 0.39). | Variable | Fuerza Excel | Motor | Alerta | IV (semilla / mediana
    20 semillas) | Lift | |---|---|---|---|---|---| | salary_deposit_stopped_flag | Very high | propensión | 3.6% | 0.32 / 0.39 | 5.7× | | recurring_deposit_stopped_flag
    | High | propensión | 4.2% | 0.22 / 0.25 | 4.3× | | recurring_deposit_change_pct | High | mixto | 10.7% | 0.17 / 0.16 | 2.7× | | net_deposit_flow_pct_90d
    | High | factor (serie Paso 1) | 18.1% | 0.16 / 0.20 | 2.4× | | pension_deposit_stopped_flag | High | propensión | 2.0% | 0.22 / 0.27 | 5.8×
    | | business_payroll_stopped_flag | High | factor | 5.6% | 0.16 / 0.19 | 3.3× | · `net_deposit_flow` es por construcción el cambio de saldo
    de la serie del Paso 1 (créditos − débitos). Con el umbral del Excel (≤ −15%) alerta al 18%. Dividido por el saldo promedio puede ser < −100%.
- id: D-17
  seccion: Paso 2 · Recurring deposits & flows (variables 3, 4, 5, 6, 19, 20)
  titulo: La mudanza del banco principal es un evento común a todos los pasos
  detalle: 'En el Paso 2 la mudanza cortaba la nómina, pero el saldo del Paso 1 no bajaba: los dólares no cuadraban. Ahora el evento se sortea
    una vez (`synthetic/exit_events.py`, mismos flujos de semilla, así que los eventos del Paso 2 quedan idénticos) y se ve en todos los pasos:
    · **Paso 1:** traslado de 30–90% del saldo de depósitos en el mes del evento (90% de quienes se mudan) y ACATS de 20–80% del AUM 0–30 días
    después (60% de quienes tienen inversiones). · **Paso 2:** corte de flujos (sin cambios). · **Paso 3:** transferencias al banco o broker nuevo.
    Efecto en el Paso 1: la señal de saldos es ahora en parte de propensión. Se recalibraron los episodios (intercepto −4.0, pendiente 1.4, δ
    12%) para volver a la banda "High". | Variable | Alerta | IV | Lift | |---|---|---|---| | aum_outflow_pct_90d | 6.0% | 0.134 | 3.0× | | deposit_balance_change_pct_90d
    | 5.8% | 0.248 | 4.1× | | aum_vs_baseline_pct | 4.8% | 0.175 | 4.1× | | deposit_balance_vs_6m_avg_pct | 5.9% | 0.267 | 4.1× | · Los rangos
    de tasa de alerta del Paso 1 (supuestos míos; el Excel solo da el umbral) pasan a [4%, 16%]. `net_deposit_flow_pct_90d` (Paso 2) alerta ahora
    al 10%, con rango [6%, 22%]. · **La fuga se prueba en el generador, no en la variable.** Una logística episodio ~ z_outflow + ε debe dar coeficiente
    de ε ≈ 0 (Wald), y los eventos de ruido deben ser independientes del índice de riesgo. Probar "variable ⟂ ε entre hogares sin mudanza" daba
    ρ ≈ 0.02 por sesgo de selección: al filtrar por un evento que depende de ε, un ε alto queda asociado a un factor más bajo. · Seguía abierto
    que el ruido del Paso 1 se estimaba incluyendo hogares con mudanza (curtosis 255); ahora se excluyen y ν̂ ≈ 6 otra vez.'
- id: D-18
  seccion: Paso 3 · Transfers (variables 7, 8, 21, 22, 23, 24, 25)
  titulo: Transferencias simuladas una por una y cuadradas con el saldo
  detalle: '~3.2 millones de transacciones en 18 meses: · **Salidas con origen en eventos ya simulados** y con el monto exacto que movió la serie
    del Paso 1: mudanza (depósitos al banco competidor en 2–6 tramos mensuales; ACATS del 80% de los hogares con inversión, 0–120 días después,
    a un broker en el 70% de los casos), episodios (45% es gasto y no genera transferencia; el resto va a banco competidor, broker o destino habitual)
    y choques (compra de casa a title/escrow, o IRS excluido). · **Ruido:** envíos de fondo a 1–6 destinos habituales (0.5% del saldo al mes en
    ~4 envíos) y destinos nuevos esporádicos (2% por mes, mediana $15k). · **Pagos excluidos por el Excel:** billers, IRS estimado trimestral
    (30% del ingreso), donaciones recurrentes y préstamos con Citizens. Sin la exclusión, la alerta de #7 pasaría de 6.5% a 8.8%. · **Entradas
    externas:** cierran mes a mes la identidad ΔD = ingresos (Paso 2) + internos AUM→depósitos + entradas − salidas − tarjeta − otros débitos.
    Cuadra al centavo; 44% de los meses necesita débitos no explicados (tarjeta extra o cheques). · **Catálogo sintético:** 111 instituciones
    con nombres genéricos y 1–3 ABA cada una, con dígito verificador válido. La ABA es fija por cuenta destino, y #24 agrupa por institución:
    516 hogares cambian de HHI al agruparlos. · **Pisos PB aplicados** ($50k por destino nuevo y $10k mensual de línea base) como parámetros.
    Los dos mejoran la precisión frente a los del Excel: lift 4.28 vs 3.20 en #8, y 2.36 vs 1.79 en #25. Ajustes que este paso obligó a hacer
    en pasos previos (todos revalidados): · **Mudanza por tramos** (2–6 meses): una relación PB no se muda en un día. Sin tramos, la ventana de
    60 días de #7 veía solo un tercio de las mudanzas. · **Volatilidad del saldo PB: 12% mensual** (antes 5%). Con 5%, el saldo era un espejo
    perfecto de las transferencias y las variables de saldo superaban "High". Con 12%, `net_deposit_flow_pct_90d` alerta al 28% con el umbral
    ilustrativo de −15%: **el umbral debería recalibrarse** (el 10% más bajo está en −38%). · **Convención de meses única:** el mes 0 son los
    últimos 30 días (antes la mudanza usaba floor). · **#23 solo wires/ACH:** los datos del Excel para #23 son "incoming and outgoing wires /
    ACH"; el ACATS cuenta en #7 por la definición base de transferencia externa. · **#8 en ventana de 90 días como principal:** a 30 días, con
    piso de $50k, es muy raro (2%) y su IV mediano es 0.08. El Excel lista ambas ventanas; la de 30 días se conserva. · **#25 tiene forma de U:**
    riesgo alto al empezar la mudanza (> +100%) y al terminarla (≈ −100% frente a una línea base inflada por los tramos previos). Se valida con
    IV, lift y forma, no con tendencia lineal. · **Tolerancia de ±0.03 a las bandas de IV en este grupo:** el Excel aclara que la fuerza es un
    "expert prior, to be validated with IV / SHAP", y aquí el mismo dinero se mide en bruto (#7) y en neto (#23). Medianas en 20 semillas: | Variable
    | Excel | IV mediano (p10–p90) | Alerta | Lift | |---|---|---|---|---| | external_transfer_pct_of_balance_60d | Very high | 0.292 (0.26–0.33)
    | 6.5% | 4.9× | | new_external_destinations_90d | High | 0.264 (0.23–0.32) | 5.9% | 4.4× | | transfer_to_competitor_pct_90d | High | 0.295
    (0.27–0.35) | 5.0% | 6.1× | | external_transfer_acceleration | High | 0.202 (0.18–0.23) | 4.3% | 4.8× | | net_external_flow_pct_90d | High
    | 0.254 (0.23–0.28) | 5.1% | 5.0× | | external_destination_concentration | High | 0.225 (0.20–0.26) | 6.0% | 4.5× | | outflow_vs_baseline_pct
    | High | 0.112 (0.08–0.13) | 7.6% | 2.4× | El AUC combinado de las 17 variables de los Pasos 1–3 es 0.656; el techo sigue en 0.851.'
- id: D-19
  seccion: Paso 4 · Investments (variables 9, 26, 27, 28, 34)
  titulo: Rendimiento vs benchmark ligado al factor S sin tocar el target
  detalle: 'El factor S del Paso 0 se interpreta como "servicio y valor percibido". El Paso 1 ahora agrega un alpha anual al portafolio: −comisión
    (1% advisory, 0.2% resto) + habilidad N(0, 1.5%) − 2% · z_service. El rendimiento de #28 es exactamente el índice TWR del Paso 1 (verificado),
    y el benchmark es el del perfil (beta objetivo = beta real + desvío). El AUM ex-mercado (#17) no cambia, porque divide por ese mismo índice.
    Pasos 1–3 reconstruidos y revalidados. La regresión de #28 sobre z_service recupera −κ, y ε no entra. **Composición del portafolio sin mover
    dólares del AUM:** · **Señal factor:** venta a cash (z_outflow, 15–60% del AUM, últimos 150 días). · **Señal propensión:** el 50% de quienes
    hacen ACATS liquida fondos propietarios (5–25% del AUM) 0–30 días antes, porque el custodio nuevo no los acepta. · **Ruido:** de-risking del
    asesor (5%), que sube el cash sin contar como venta del cliente; rebalanceos del asesor (excluidos); ventas completas ocasionales; RMD de
    diciembre para ≥ 73 (excluida de #9); vencimientos de renta fija (30% en 90 días), con reinversión normal completa en el 65% de los casos.
    Quien se muda o liquida no reinvierte en el 85% (media no reinvertida 0.95 vs 0.34). · El cash % mensual parte del cash de inversión que usa
    el Paso 3 en el denominador de #7. | Variable | Alerta | IV (semilla / mediana) | Lift | |---|---|---|---| | investment_redemption_pct | 6.2%
    | 0.18 | 2.9× | | fixed_income_maturity_not_reinvested | 36.8% de quienes tuvieron vencimiento | 0.21 | 2.1× | | cash_pct_of_portfolio_chg
    | 7.9% | 0.14 | 2.7× | | return_vs_benchmark | 31.6% (≤ −3 pp) | 0.12 / 0.10 | 1.6× | | positions_liquidated_pct | 1.6% | 0.19 | 3.7× | ·
    `return_vs_benchmark` es el driver más débil (mediana 0.096), como en la realidad: el mal rendimiento explica el "porqué", pero no anticipa
    la salida tanto como mover dinero. · El AUC combinado de 22 variables es 0.683; el techo sigue en 0.851.'
- id: D-20
  seccion: Paso 5 · Relationship & closures (variables 10, 29, 30, 31, 32)
  titulo: Cuentas con fecha y motivo de cierre; SOW con patrimonio estimado
  detalle: '- **Tabla de cuentas** (≈ 90 mil): cheques para todos; ahorro, money market, CD y tarjeta según probabilidad; brokerage, advisory,
    trust, crédito y cuenta de negocio según las banderas del Paso 0; cuentas adicionales por producto (más en UHNW). · **Cierres:** - quien se
    muda cierra productos 0–90 días después del traslado (propensión); - un episodio de salida cierra ahorro o money market (factor); - ruido
    que cuenta: CD vencido no renovado, cierre ocasional; - ruido que el Excel excluye: CD renovado, préstamo pagado a término, conversión y consolidación
    interna. De 10,559 cierres en 180 días, se cuentan 3,189 productos. - El ruido se simula sobre 180 días. Primero lo hice solo sobre 90, y
    eso habría favorecido artificialmente a la ventana larga. · **#10 en ventana de 180 días como principal:** los cierres por mudanza llegan
    meses después del traslado; a 90 días el IV es ≈ 0.23. La de 90 días se conserva, igual que en #8. · **SOW:** patrimonio total verdadero estable,
    con SOW de hace 6 meses ligado a z_outflow (mediana 46%). Se estima con tres fuentes de distinta calidad: declarado 40% (error 7%), proveedor
    45% (23%) y modelo 15% (33%). La fuente se guarda como pide el Excel. El valor en Citizens sale de las series del Paso 1, así que quien se
    muda pierde ~20 pp de share. El 10% de hogares reestimados duplica la dispersión del cambio, que es justo la advertencia del Excel. · **Trustee:**
    mudanza (40% de los trusts de quienes se mudan), servicio (z_service) y ruido. La sucesión por muerte es exclusión. · Independencia del ruido
    probada sobre el **sorteo**, no sobre el cierre efectivo: una cuenta que ya se cerró por mudanza no puede convertirse después, y eso induce
    una correlación aparente. | Variable | Excel | Alerta | IV (semilla) | Lift | |---|---|---|---|---| | products_closed_180d | Very high | 9.7%
    | 0.36 | 3.4× | | accounts_closed_90d | High | 14.3% | 0.23 | 1.9× | | share_of_wallet | High | 26.7% (< 30%) | 0.27 | 2.2× | | share_of_wallet_change
    | High | 13.7% | 0.23 | 2.7× | | trustee_change_flag | High | 4.6% de los trusts | 0.21 | 3.8× | El AUC combinado de 27 variables es 0.696;
    el techo sigue en 0.851.'
- id: D-21
  seccion: Paso 6 · Banker (variables 11, 12, 13, 35)
  titulo: La salida del banker se decide por banker, según la calidad de su libro
  detalle: '- **Carteras:** libros de ~60 hogares HNW y ~25 UHNW, de un solo segmento, armados por calidad (índice de riesgo + ruido). En 6 meses
    sale ~10% de los bankers (38 en esta semilla), y con más probabilidad los de libros deteriorados. Cuando un banker sale, cambia todo su libro.
    La relación con el churn tiene sentido: los libros peores pierden banker, y es a esos clientes a los que un cambio más les pesa (Cerulli /
    55ip). · **Otros cambios:** pedido del cliente (z_service) y rebalanceo (ruido). La cobertura temporal (< 30 días) queda excluida, y el motivo
    se guarda. · **Variación entre semillas:** como deciden solo ~38 bankers, el IV de #11 varía bastante entre semillas (p10–p90 0.25–0.40, mediana
    0.32). Es el efecto real de que la decisión sea agrupada. · **Bitácora de 12 meses (~300 mil interacciones):** contactos del banker a una
    tasa que depende de la cadencia (UHNW 30d, HNW 90d), la diligencia del banker y z_neglect. El contacto significativo sigue la regla del Excel:
    reunión, llamada ≥ 5 min, o mensaje con respuesta del cliente en ≤ 7 días. Los envíos masivos quedan excluidos. Quien se está mudando contesta
    menos y cancela más. Tras un cambio de banker, el 70% recibe llamada de bienvenida; entre quienes cambiaron, la brecha mediana es 0.29 con
    bienvenida y 0.44 sin ella. · **"Cancelado por" (#35, factibilidad Low):** solo lo registra el 40% de los bankers; en el resto la variable
    es NULL, que es la situación real del Excel. | Variable | Excel | Alerta | IV mediano (p10–p90) | Lift | |---|---|---|---|---| | banker_change_6m_flag
    | Very high | 14.9% | 0.32 (0.25–0.40) | 4.1× | | contact_gap_ratio | High | 3.7% (> 2× cadencia) | 0.16 (0.13–0.20) | 2.0× | | client_reply_rate
    | High | 25.5% (< 50%) | 0.24 (0.17–0.30) | 1.9× | | meetings_cancelled_by_client | High | 5.3% (≥ 2) | 0.16 (0.11–0.21) | 2.1× | El AUC combinado
    de 31 variables es 0.757; el techo sigue en 0.851.'
- id: D-22
  seccion: Paso 7 · Complaints & voice of client (variables 14, 15, 33, 36)
  titulo: Quejas con ciclo de vida completo y Assistant solo en piloto
  detalle: '- **Volumen:** ~5,500 quejas en 12 meses; el 18% de los hogares se quejó, un volumen plausible para PB. La primera calibración daba
    27%, demasiado alto, y la corregí: pocos clientes se quejan y esos repiten. La frecuencia depende de z_service (carga 1.4) y z_neglect. ·
    **Categoría:** taxonomía de nivel 2 con 8 categorías. La categoría se inclina a "atención del banker" con N alto y a "proceso / rendimiento"
    con S alto. Fraude y errores de estado de cuenta son ruido independiente del riesgo. Quien hace ACATS puede quejarse de la demora de la transferencia.
    · **Ciclo de vida:** apertura, resolución (más lenta con S alto), SLA por categoría, escalamiento a gerencia / ombudsman / regulador / legal
    (más probable fuera de SLA) y reapertura. · **#15** incluye `open_complaint_flag`, para distinguir 0 días de "sin queja" como pide el Excel,
    y `complaint_out_of_sla_flag`, que es el override del deck. · **#36 (Assistant, factibilidad Low):** solo el piloto (30% de hogares, al azar
    y sin sesgo de selección) tiene valor; el resto es NULL. Cadena: estado real de insatisfacción (S, N, y +3 en logit si se está mudando: "I''m
    moving my money") → conversó en 30 días (60%) → clasificador (TPR 80%, FPR 2%) → revisión humana (confirma 95% de los verdaderos y 10% de
    los falsos). La precisión de la señal confirmada es 97.5%. | Variable | Alerta | IV mediano (p10–p90) | Lift | |---|---|---|---| | complaint_escalated_flag
    | 5.3% | 0.11 (0.10–0.14) | 3.1× | | complaint_age_days | 2.0% (> 30 días) | 0.10 (0.08–0.12) | 3.8× | | repeat_complaint_flag | 3.7% | 0.12
    (0.09–0.13) | 4.0× | | relationship_dissatisfaction_flag | 4.1% del piloto | 0.20 (0.14–0.25) | 3.0× | · Las quejas son señales raras: su
    IV queda en la parte baja de "High", pero el lift de la alerta es alto (3–4×). Tiene sentido: pocas quejas, muy informativas. El AUC combinado
    de 35 variables es 0.761; el techo sigue en 0.851.'
- id: D-23
  seccion: Paso 8 · External & composite (variables 16, 37) y base final
  titulo: Multi-señal desde los umbrales del Excel; buró con interruptor legal
  detalle: '- **#16:** por cada uno de los 7 grupos, ¿alguna variable supera su umbral ilustrativo del Excel? (#26 exige además un monto material
    ≥ $100k.) El conteo va de 0 a 7 y el flag es ≥ 3. El churn crece de forma monótona: 2.8% con 0 grupos, 6.8% con 3, 19.9% con 5 y 44.8% con
    7. Su IV (0.64) supera al de cualquier variable sola, como se espera de una compuesta, y tiene banda propia [0.30, 0.80]. · **#37:** hipoteca
    o HELOC nueva con otro acreedor en 6 meses. Fuentes: mudanza (40% de quienes se mudan), compra de casa del Paso 3 financiada fuera de Citizens
    (Citizens financia el 60% si hay crédito ancla y el 25% si no) y refinanciamiento (0.8%, ruido). Es NULL sin propósito permisible (5%). Con
    `step8.legal_cleared: false` queda NULL para todos (FCRA), y así está probado. **Hallazgo para Citizens: varios umbrales ilustrativos del
    Excel son laxos para PB.** Con ellos, el 24% de los hogares queda con ≥ 3 grupos en alerta. Los que más activan grupos: `net_deposit_flow_pct_90d
    ≤ −15%` (28%), `share_of_wallet < 30%` (27%), `client_reply_rate < 50%` (26%) y `return_vs_benchmark ≤ −3 pp` (32% de las cuentas advisory).
    El Excel ya prevé recalibrarlos con WoE/IV. Esta base permite hacerlo antes de tener los datos reales. **Base final:** `data/synthetic/client_pulse_synthetic.csv`
    (20,000 × 62: atributos del hogar, las 37 variables en su columna principal —mapa en `synthetic/schema.py → EXCEL_PRIMARY`— y el target).
    La versión completa (101 columnas, con todas las ventanas y montos) se regenera con `scripts/build_step8.py`. El AUC combinado de las 37 variables
    es 0.762, frente a un techo de 0.851. Resumen por variable en `docs/reports/final_report.md`.'
- id: D-24
  seccion: Variable de churn construida y comparación de metodologías
  titulo: La etiqueta se construye sobre la ventana de resultado, como lo haría el banco
  detalle: 'Se simulan los 6 meses posteriores al corte (mercado futuro, ruido del saldo, choques de liquidez) y sobre esos saldos se aplican
    las definiciones del deck: **hard churn** si el valor cae a ≤ 5% y no se recupera; **soft churn** si la caída ex-mercado supera el 20% en
    3 meses, sin salida total. · El hard churn coincide al 100% con el evento (6.04%); logo churn 6.0% vs AUM churn 6.4%. · El soft churn construido
    (11.0%) tiene ruido de etiqueta: 500 falsos positivos (compras de casa y volatilidad del saldo que cruzan el −20%) y 72 contracciones que
    no llegan al umbral. **El umbral de soft churn debe validarse** (deck slide 69).'
- id: D-25
  seccion: Variable de churn construida y comparación de metodologías
  titulo: Comparación de metodologías
  detalle: '(`scripts/score_models.py`, `docs/reports/model_comparison.md`). Partición estratificada 70/30, métricas en test, IC 95% por bootstrap
    pareado. | Hard churn 6m | AUC | KS | Precisión top 10% | Lift top 10% | |---|---|---|---|---| | M0a · Reglas de negocio (slide 20) | 0.55
    | 0.11 | 11% | 1.9× | | M0b · Scorecard experto (slide 22) | 0.70 | 0.33 | 23% | 3.7× | | M1 · Scorecard estadístico WoE | 0.75 | 0.37 | 23%
    | 3.8× | | M2 · Gradient Boosting | 0.76 | 0.40 | 24% | 4.0× | | M2 · Logística (challenger) | 0.77 | 0.41 | 24% | 4.0× | | M3 · Red neuronal
    (MLP + secuencia) | 0.75 | 0.39 | 23% | 3.9× | | Techo (probabilidad verdadera) | 0.86 | 0.56 | 33% | 5.4× | · Los estadísticos superan claramente
    al scorecard experto (+0.05–0.07 de AUC) y a las reglas. · **Gradient Boosting, logística, scorecard WoE y red neuronal no se distinguen**
    entre sí (IC de la diferencia incluye 0). Con el criterio de promoción del deck (slide 28), el más simple y explicable es suficiente. Esto
    también refleja que el generador es mayormente aditivo; en datos reales las interacciones podrían favorecer al Gradient Boosting. · Todos
    los probabilísticos quedan calibrados (media 5.9–6.2% vs 6.0% observado). · La captura de AUM varía mucho (IC ~0.35–0.65) porque depende de
    pocos hogares grandes (cola Pareto). · Soft churn (alerta temprana): AUC 0.64–0.67, por el ruido de etiqueta; el scorecard experto casi no
    lo anticipa (0.56). · Las bandas 70/40 del deck no calzan con la escala: el experto deja 96% en Low y el estadístico 0.2% en High. Las bandas
    deberían fijarse por capacidad del banker (p. ej. High = top 5%).'
correcciones_y_sesgos_detectados:
- 'repeticiones de montos: se comparan contra lo esperado por redondear al centavo (pensión 15 vs 15.2)'
- banda con 40 semillas sin corrección múltiple → p-valores empíricos con 200 semillas dentro de BH
- 'Hosmer-Lemeshow: gl = g − 1 (intercepto calibrado) y g (probabilidad conocida), no g − 2'
- monotonía con ρ de Spearman castigaba señales tipo palo de hockey → Cochran-Armitage + lift
- 'prueba del bono en una ventana sin bonos → se midió donde importa (bono de diciembre en #5)'
- IV exigido en todas las semillas → mediana en banda (varianza de muestreo de flags raros)
- ruido de cierres simulado solo en 90 días favorecía la ventana de 180 → extendido a 180 días
- ABA asignada por transacción → fija por cuenta destino
- mudanza que cortaba nómina sin bajar el saldo → evento común a todos los pasos
- convención de meses con floor → mes 0 = últimos 30 días
- fuga probada en hogares sin mudanza daba sesgo de selección → test de Wald sobre el generador
- independencia del ruido medida sobre el cierre efectivo (censurado) → sobre el sorteo
hallazgos_para_citizens:
- 'umbrales ilustrativos del Excel laxos para PB: 24% de hogares con ≥ 3 grupos en alerta'
- net_deposit_flow ≤ −15% alerta 28% con volatilidad PB de 12% mensual (10% más bajo en −38%)
- 'soft churn construido tiene ruido de etiqueta: el umbral de −20% debe validarse'
- la captura de AUM es volátil por la cola Pareto (pocos hogares grandes)
- 'bandas 70/40 del deck no calzan con la escala: fijarlas por capacidad del banker'
- 'variable 25 con forma en U: WoE la captura, una regla lineal no'
- pisos PB ($50k destino nuevo, $10k línea base) mejoran el lift frente a los del Excel
comparacion_modelos:
  target: hard churn 6m construido; partición estratificada 70/30; IC por bootstrap pareado (200)
  resultados:
  - metodologia: M0a · Reglas de negocio
    auc: 0.545
    ks: 0.111
    precision_top10: 0.112
    lift_top10: 1.862
    captura_aum_top10: 0.141
    auc_ic95:
    - 0.525
    - 0.562
    distinto_de_gbm: sí
  - metodologia: M0b · Scorecard experto (deck)
    auc: 0.696
    ks: 0.333
    precision_top10: 0.225
    lift_top10: 3.724
    captura_aum_top10: 0.509
    auc_ic95:
    - 0.664
    - 0.727
    distinto_de_gbm: sí
  - metodologia: M1 · Scorecard estadístico (WoE)
    auc: 0.75
    ks: 0.37
    precision_top10: 0.227
    lift_top10: 3.752
    captura_aum_top10: 0.341
    auc_ic95:
    - 0.723
    - 0.777
    distinto_de_gbm: 'no'
  - metodologia: M2 · Gradient Boosting
    auc: 0.76
    ks: 0.401
    precision_top10: 0.24
    lift_top10: 3.974
    captura_aum_top10: 0.52
    auc_ic95:
    - 0.732
    - 0.789
    distinto_de_gbm: referencia
  - metodologia: M2 · Logística (challenger)
    auc: 0.766
    ks: 0.406
    precision_top10: 0.24
    lift_top10: 3.974
    captura_aum_top10: 0.513
    auc_ic95:
    - 0.737
    - 0.795
    distinto_de_gbm: 'no'
  - metodologia: M3 · Red neuronal (tabular + secuencia)
    auc: 0.753
    ks: 0.386
    precision_top10: 0.233
    lift_top10: 3.863
    captura_aum_top10: 0.51
    auc_ic95:
    - 0.724
    - 0.782
    distinto_de_gbm: 'no'
  - metodologia: Techo · probabilidad verdadera
    auc: 0.859
    ks: 0.561
    precision_top10: 0.326
    lift_top10: 5.392
    captura_aum_top10: 0.601
    auc_ic95:
    - 0.842
    - 0.879
    distinto_de_gbm: sí
  lectura: estadísticos > experto > reglas; GBM, logística, WoE y red neuronal no se distinguen (generador mayormente aditivo)
limitaciones:
- un solo corte (sin out-of-time)
- latentes estáticos
- ventanas mensuales como aproximación a días
- relaciones impuestas por diseño, no aprendidas de datos
- 'variables sin historia real (#35, #36, #37)'
- parámetros 'Supuesto' pendientes de validar con Citizens
- red neuronal = MLP (no LSTM)
reproducibilidad:
  comandos:
  - pip install -r requirements.txt
  - python scripts/build_step0.py … build_step8.py
  - python scripts/stats_step0.py
  - python scripts/score_models.py
  - python -m pytest
  control: manifiestos data/synthetic/step*_manifest.json con SHA-256 de cada salida
  repositorio: ealejandrot-bit/Citizens-bank · rama claude/synthetic-excel-variables-v7orh6
```
