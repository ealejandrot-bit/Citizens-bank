# UHNWI Churn Propensity Scorecard · documento de modelo (pasos 0–17)

> **Toda cifra de este documento es [SINT-BASE]:** se calcula sobre `data/synthetic/client_pulse_synthetic.csv` (idéntica al Excel adjunto), una base **sintética** generada con parámetros explícitos (`config/params.yaml`). Ningún número es resultado de Citizens ni benchmark de industria. Reproducible: `python scripts/build_scorecard.py`.

## Modo, parámetros y supuestos

| Parámetro | Valor usado | Origen |
|---|---|---|
| Modo | **SINT-BASE**: pipeline de modo REAL ejecutado sobre la base sintética | Instrucción del usuario («usa la base sintética») |
| Universo | 20,000 hogares (1,103 UHNW ≥ $30M; resto HNW) | Base |
| Universo de modelado | 19,473 hogares (sin excluidos ni antigüedad < 12m) · UHNW 1,083 | Paso 1 |
| Unidad | Hogar / relación (`household_id`) | Paso 0 |
| T0 | 2025-12-31 (un solo corte) | Base |
| Observación / desempeño | 24 m / **6 m** (T0, T0+6m] | Base (no hay 12 m) |
| Target | hard ∪ económico: salida neta ex-mercado ≥ 25% al cierre de la ventana | Paso 1 |
| Indeterminados | salida neta ex-mercado entre 10% y 25%: fuera del entrenamiento, dentro del scoring | Prompt |
| Escala | S₀ = 600 a O₀ = 20:1 (buenos:malos), PDO = 40 → Factor = 57.7078, Offset = 427.1229 | Prompt |
| Banqueros | 360 (libros de 60 HNW / 25 UHNW de la base); capacidad 2 críticos nuevos/banquero/mes = **720 casos/mes** (3.7% de la cartera) | Prompt (2/mes) escalado a la base |
| Validación | 70/30 estratificado (segmento × target × indeterminado) + bootstrap. **Sin OOT** (un solo corte) | Paso 4 |

**Supuestos tomados por defecto (las preguntas del Paso 0 quedaron sin respuesta; cada uno se puede cambiar en `synthetic/scorecard.py`):**

- Universo completo con el segmento como variable de calibración, no solo UHNW: el UHNW aislado tiene 189 eventos (132 en desarrollo), por debajo de los 300 que exige WoE-logística. Toda métrica se reporta también para UHNW.
- Horizonte de 6 m en lugar de 12 m: la base no tiene ventana de 12 m.
- Umbral económico de 25% (el del prompt), no el 20% del deck; la sensibilidad está en el Paso 1.
- Capacidad: los 2 casos críticos por banquero al mes del prompt, aplicados a los banqueros implícitos de la base.
- Las horas de banquero por alerta no están dadas: los falsos positivos se reportan en alertas; la conversión a horas queda como parámetro H.

## 0. Definición del problema

**Objetivo.** Fijar qué es churn, con qué horizonte, en qué unidad y cuál es la regla anti-leakage.
**Por qué.** En UHNW la fuga es parcial: un target de cierre total llega tarde y modela cierres administrativos.
**Método.** Target jerárquico con severidad:
- Nivel 1: hard (valor ≤ 5% y sin recuperación).
- Nivel 2: económico (flujo neto ex-mercado ≥ u).
- La pérdida de banco principal (nómina, pensión, transferencias, share of wallet) entra como **features y overrides**, no como target, para no hacer circular el modelo.
- Unidad: hogar. La decisión de mover activos es familiar (trust, negocio vinculado), los traspasos entre cuentas del mismo hogar no son fuga y el banquero gestiona hogares.
**Anti-leakage.**
- Features con fecha ≤ T0 (ventanas de lookback 30/60/90/180d y 24m); target solo en (T0, T0+6m].
- `value_lost_6m`, `hard_churn_6m` y `soft_churn_3m` son resultados: prohibidos como predictores.
- `multi_signal_count` es una compuesta de las demás features: fuera del modelo.
**Datos.** Base + simulación de la ventana de resultado (`synthetic/outcome.py`, misma semilla maestra).
**Salida.** Ficha del target (tabla de parámetros arriba).
**Control de calidad.**
- Ninguna feature supera IV 0.50 (ver paso 9).
- La etiqueta hard reconstruida coincide 100% con el evento del generador (`docs/reports/model_comparison.md`).
**Decisiones.** Descartados: unidad cuenta (falsos positivos por traspasos internos); 12 m (no existe en la base); Cox (no hay tiempo al evento continuo, solo el mes).

## 1. Target y churn rate

**Objetivo.** Construir y medir el evento: cuántos hay, a qué umbral y qué pesan en AUM.
**Por qué.** El número de eventos decide el método (paso 11). En UHNW el rate por AUM manda: un hogar grande pesa más que veinte pequeños.
**Método y fórmulas.**
- Churn rate por relaciones = eventos ÷ relaciones activas en T0.
- Churn rate por AUM bruto = Σ (V₀ − V₆) de churners ÷ Σ V₀. Incluye mercado.
- Churn rate por AUM neto = Σ (Vx₀ − Vx₆) de churners ÷ Σ Vx₀, con Vx = depósitos + AUM ÷ índice de retorno del propio portafolio (flujo, no valuación).
**Datos.** Saldos mensuales simulados en (T0, T0+6m].

### 1.1 Exclusiones

| Exclusión | Volumen | Tratamiento |
|---|---|---|
| Excluidos del generador (fallecimiento / reubicación gestionada) | 123 | Fuera de desarrollo y de scoring |
| Antigüedad < 12 meses | 404 | Fuera de desarrollo; en producción se scorean con marca «fuera de política» |
| Vehículos de evento único (SPV), fraude, empleados, en proceso formal de salida | 0 (no identificables en la base) | Pedir marcas al banco (modo REAL) |
| **Universo de modelado** | **19,473** | = 20,000 − 123 − 404 |

### 1.2 Sensibilidad del número de eventos al umbral económico

| umbral u   |   hard |   económico |   eventos totales |   churn rate relaciones |   indeterminados (10%–u) |   eventos entrenables (dev 70%) |   eventos UHNW |
|:-----------|-------:|------------:|------------------:|------------------------:|-------------------------:|--------------------------------:|---------------:|
| 20%        |  1,168 |       2,439 |             3,607 |                  0.1852 |                    1,845 |                           2,525 |            199 |
| 25%        |  1,168 |       1,994 |             3,162 |                  0.1624 |                    2,290 |                           2,213 |            189 |
| 35%        |  1,168 |       1,293 |             2,461 |                  0.1264 |                    2,991 |                           1,723 |            146 |
| 50%        |  1,168 |         499 |             1,667 |                  0.0856 |                    3,785 |                           1,167 |            113 |

Cálculo con u = 25%: 1,168 hard + 1,994 económico = 3,162 eventos; 3,162 ÷ 19,473 = 16.24%.

### 1.3 Churn rate de cartera (6 m)

|                                         | numerador        | denominador   |   rate 6m |
|:----------------------------------------|:-----------------|:--------------|----------:|
| Churn por relaciones (hard ∪ económico) | 3,162 relaciones | 19,473        |    0.1624 |
| Churn por relaciones (solo hard)        | 1,168 relaciones | 19,473        |    0.0600 |
| Churn por AUM bruto (con mercado)       | $20.58 mil M     | $202.71 mil M |    0.1015 |
| Churn por AUM neto de mercado (flujo)   | $21.28 mil M     | $202.71 mil M |    0.1050 |
| Churn por AUM, solo hard (bruto)        | $12.78 mil M     | $202.71 mil M |    0.0630 |

### 1.4 Por segmento

| segment   |   relaciones |   eventos |   churn rate relaciones |   AUM inicial ($M) |   AUM perdido neto ($M) |   churn rate AUM neto |
|:----------|-------------:|----------:|------------------------:|-------------------:|------------------------:|----------------------:|
| HNW       |       18,390 |     2,973 |                  0.1617 |        123229.3625 |              12142.9297 |                0.0985 |
| UHNW      |        1,083 |       189 |                  0.1745 |         79478.4381 |               9140.2006 |                0.1150 |

Chequeo: churn de cartera = Σ share × tasa = 0.9444×0.1617 + 0.0556×0.1745 = 0.1624 ✓

**Censura.** Un solo corte y ventana simulada completa: no hay censura en la base. En modo REAL, las relaciones sin 6 m de desempeño no entran a la logística (quedan para la cohorte siguiente); en Cox serían censuradas.
**Control de calidad.** Los eventos de desarrollo (2,213) superan 300 → WoE-logística. Los indeterminados son 11.8% del universo, dentro del rango 10–25% del prompt.
**Decisiones.** u = 25% y rango indeterminado 10–25%. Descartado u = 50%: deja solo el 12% de los eventos como económicos y convierte el target en casi-hard.

## 2. Diccionario de datos y proceso generador

**Objetivo.** Inventariar variables con tipo, ventana, missing y dirección esperada. **Por qué.** El signo esperado se fija antes de ver datos: es la hipótesis que valida la monotonicidad del paso 9.
**Método.** 37 variables del Excel (seis bloques) + atributos estructurales. Bloque digital: **no existe en la base** (0 variables) → en modo REAL pedir logins, sesiones y transacciones digitales. Eventos de vida: solo `trustee_change_flag` (proxy de sucesión).

| variable                             | bloque                | tipo     | fuente                         | frecuencia         | ventana           | unidad   |   % missing | significado                                     | dirección esperada   |
|:-------------------------------------|:----------------------|:---------|:-------------------------------|:-------------------|:------------------|:---------|------------:|:------------------------------------------------|:---------------------|
| aum_outflow_pct_90d                  | Salida de activos     | continua | base sintética (37 vars Excel) | mensual (corte T0) | 90d               | fracción |        14.5 | Retiros netos de inversión ÷ AUM                | +                    |
| investment_redemption_pct            | Salida de activos     | continua | base sintética (37 vars Excel) | mensual (corte T0) | 90d               | fracción |        14.5 | Redenciones ÷ AUM                               | +                    |
| positions_liquidated_pct             | Salida de activos     | continua | base sintética (37 vars Excel) | mensual (corte T0) | 90d               | fracción |        14.6 | Posiciones liquidadas ÷ AUM                     | +                    |
| outflow_vs_baseline_pct              | Salida de activos     | continua | base sintética (37 vars Excel) | mensual (corte T0) | 90d vs 24m        | valor    |         0.8 | Salidas vs. baseline propio                     | +                    |
| fixed_income_maturity_not_reinvested | Salida de activos     | continua | base sintética (37 vars Excel) | mensual (corte T0) | 90d               | fracción |        73.9 | Vencimientos RF no reinvertidos                 | +                    |
| cash_pct_of_portfolio_chg            | Salida de activos     | continua | base sintética (37 vars Excel) | mensual (corte T0) | 90d               | fracción |        15.0 | Δ % cash del portafolio (pre-transferencia)     | +                    |
| aum_vs_baseline_pct                  | Deterioro de AUM      | continua | base sintética (37 vars Excel) | mensual (corte T0) | t vs meses −6..−1 | fracción |        15.0 | AUM ex-mercado vs. baseline                     | −                    |
| deposit_balance_change_pct_90d       | Deterioro de AUM      | continua | base sintética (37 vars Excel) | mensual (corte T0) | 3m vs 3m previos  | fracción |         0.5 | Δ saldo de depósitos                            | −                    |
| deposit_balance_vs_6m_avg_pct        | Deterioro de AUM      | continua | base sintética (37 vars Excel) | mensual (corte T0) | 1m vs 6m          | fracción |         0.8 | Depósitos vs. media 6m                          | −                    |
| net_deposit_flow_pct_90d             | Deterioro de AUM      | continua | base sintética (37 vars Excel) | mensual (corte T0) | 90d               | valor    |         0.3 | Flujo neto de depósitos ÷ saldo                 | −                    |
| external_transfer_pct_of_balance_60d | Externalización       | continua | base sintética (37 vars Excel) | mensual (corte T0) | 60d               | valor    |         0.1 | Transferencias externas ÷ saldo                 | +                    |
| new_external_destinations_90d        | Externalización       | continua | base sintética (37 vars Excel) | mensual (corte T0) | 90d               | fracción |         3.5 | Nuevos destinos externos                        | +                    |
| transfer_to_competitor_pct_90d       | Externalización       | continua | base sintética (37 vars Excel) | mensual (corte T0) | 90d               | valor    |         0.2 | Transferencias a bancos competidores ÷ saldo    | +                    |
| external_transfer_acceleration       | Externalización       | continua | base sintética (37 vars Excel) | mensual (corte T0) | 30d vs 90d        | valor    |         0.2 | Aceleración de transferencias externas          | +                    |
| net_external_flow_pct_90d            | Externalización       | continua | base sintética (37 vars Excel) | mensual (corte T0) | 90d               | valor    |         0.2 | Flujo externo neto (entradas − salidas) ÷ saldo | −                    |
| external_destination_concentration   | Externalización       | continua | base sintética (37 vars Excel) | mensual (corte T0) | 90d               | fracción |         0.2 | Concentración (HHI) de destinos externos        | +                    |
| salary_deposit_stopped_flag          | Banco principal       | binaria  | base sintética (37 vars Excel) | mensual (corte T0) | 45d               | 0/1      |        47.3 | Nómina detenida                                 | +                    |
| recurring_deposit_stopped_flag       | Banco principal       | binaria  | base sintética (37 vars Excel) | mensual (corte T0) | 45d               | 0/1      |         7.5 | Depósito recurrente detenido                    | +                    |
| recurring_deposit_change_pct         | Banco principal       | continua | base sintética (37 vars Excel) | mensual (corte T0) | 90d               | fracción |         7.4 | Δ monto de depósitos recurrentes                | −                    |
| pension_deposit_stopped_flag         | Banco principal       | binaria  | base sintética (37 vars Excel) | mensual (corte T0) | 45d               | 0/1      |        65.7 | Pensión detenida                                | +                    |
| business_payroll_stopped_flag        | Banco principal       | binaria  | base sintética (37 vars Excel) | mensual (corte T0) | 45d               | 0/1      |        73.9 | Nómina del negocio detenida                     | +                    |
| products_closed_180d                 | Pérdida de productos  | continua | base sintética (37 vars Excel) | mensual (corte T0) | 180d              | valor    |         0.5 | Productos cerrados                              | +                    |
| accounts_closed_90d                  | Pérdida de productos  | continua | base sintética (37 vars Excel) | mensual (corte T0) | 90d               | valor    |         0.2 | Cuentas cerradas                                | +                    |
| share_of_wallet                      | Pérdida de productos  | continua | base sintética (37 vars Excel) | mensual (corte T0) | t                 | fracción |         0.0 | Share of wallet estimado                        | −                    |
| share_of_wallet_change               | Pérdida de productos  | continua | base sintética (37 vars Excel) | mensual (corte T0) | 6m                | fracción |         0.8 | Δ share of wallet                               | −                    |
| complaint_escalated_flag             | Fricción de servicio  | binaria  | base sintética (37 vars Excel) | mensual (corte T0) | 180d              | 0/1      |         0.0 | Queja escalada                                  | +                    |
| complaint_age_days                   | Fricción de servicio  | continua | base sintética (37 vars Excel) | mensual (corte T0) | t                 | valor    |         0.0 | Antigüedad de la queja abierta                  | +                    |
| repeat_complaint_flag                | Fricción de servicio  | binaria  | base sintética (37 vars Excel) | mensual (corte T0) | 180d              | 0/1      |         0.0 | Queja repetida                                  | +                    |
| relationship_dissatisfaction_flag    | Fricción de servicio  | binaria  | base sintética (37 vars Excel) | mensual (corte T0) | 90d               | 0/1      |        70.4 | Insatisfacción / intención de salida            | +                    |
| return_vs_benchmark                  | Fricción de servicio  | continua | base sintética (37 vars Excel) | mensual (corte T0) | 12m               | fracción |        41.0 | Rendimiento vs. benchmark (valor percibido)     | −                    |
| banker_change_6m_flag                | Relación con banquero | binaria  | base sintética (37 vars Excel) | mensual (corte T0) | 6m                | 0/1      |         0.5 | Cambio de banquero                              | +                    |
| contact_gap_ratio                    | Relación con banquero | continua | base sintética (37 vars Excel) | mensual (corte T0) | t                 | valor    |         0.0 | Días sin contacto ÷ cadencia                    | +                    |
| client_reply_rate                    | Relación con banquero | continua | base sintética (37 vars Excel) | mensual (corte T0) | 180d              | fracción |        48.0 | Tasa de respuesta del cliente                   | −                    |
| meetings_cancelled_by_client         | Relación con banquero | continua | base sintética (37 vars Excel) | mensual (corte T0) | 180d              | valor    |        60.7 | Reuniones canceladas por el cliente             | +                    |
| trustee_change_flag                  | Evento de vida        | binaria  | base sintética (37 vars Excel) | mensual (corte T0) | 12m               | 0/1      |        68.1 | Cambio de trustee (sucesión)                    | +                    |
| bureau_new_mortgage_elsewhere        | Crédito / saldos      | binaria  | base sintética (37 vars Excel) | mensual (corte T0) | 6m                | 0/1      |         5.0 | Hipoteca nueva en otro acreedor (buró)          | +                    |
| multi_signal_count                   | Compuesta             | continua | base sintética (37 vars Excel) | mensual (corte T0) | t                 | valor    |         0.0 | Nº de grupos en alerta (umbrales Excel)         | +                    |
| log_relationship_value               | Estructural           | continua | atributo del hogar             | mensual (corte T0) | t                 | valor    |         0.0 | ln(relationship value)                          | ·                    |
| tenure_years                         | Estructural           | continua | atributo del hogar             | mensual (corte T0) | t                 | años     |         0.0 | Antigüedad                                      | −                    |
| has_credit_anchor                    | Crédito / saldos      | binaria  | base sintética (37 vars Excel) | mensual (corte T0) | t                 | bool     |         0.0 | Crédito ancla con el banco                      | −                    |
| has_trust                            | Estructural           | binaria  | atributo del hogar             | mensual (corte T0) | t                 | bool     |         0.0 | Tiene trust                                     | ·                    |
| has_linked_business                  | Estructural           | binaria  | atributo del hogar             | mensual (corte T0) | t                 | bool     |         0.0 | Negocio vinculado                               | ·                    |
| age_primary                          | Estructural           | continua | atributo del hogar             | mensual (corte T0) | t                 | años     |         0.0 | Edad del titular                                | ·                    |

**Proceso generador [SINT] (β verdaderos, `config/params.yaml`).**
- Latentes: tres factores N(0,1) correlacionados (outflow, neglect, service; ρ = 0.35 / 0.25 / 0.30).
- Índice de riesgo = 0.60·z_outflow + 0.45·z_neglect + 0.35·z_service − 0.15·ln(1 + antigüedad) − 0.20·crédito ancla + 0.10·UHNW + ε, con ε ~ N(0, 0.60²); luego se estandariza.
- Hard: logit p = a + 1.6·índice (tasa 6%). Soft: logit p = a + 1.2·índice (tasa 9%).
- Las features se generan desde los latentes con ruido propio, **nunca desde el target**.
- Techo teórico (AUC de la probabilidad verdadera) ≈ 0.86 para hard.

## 3. Calidad de datos

**Objetivo.** Detectar errores antes de modelar. **Por qué.** En UHNW las colas son reales (hogares de $900M); eliminarlas borra justo lo que importa.
**Método.** Perfil por variable, controles de dominio y clasificación de outliers (error / comportamiento real / operación extraordinaria). Capping solo para errores.

|                                      |   % missing |     media |    mediana |     d.e. |        p5 |       p25 |        p50 |       p75 |      p95 |      p99 |         mín |       máx |
|:-------------------------------------|------------:|----------:|-----------:|---------:|----------:|----------:|-----------:|----------:|---------:|---------:|------------:|----------:|
| aum_outflow_pct_90d                  |    14.32    |  0.04987  |  0         |  0.2168  |  0        |  0        |  0         |  0.01293  |  0.2759  |  1.004   |   0         |    7.684  |
| investment_redemption_pct            |    14.32    |  0.04228  |  0.003157  |  0.115   |  0        |  0        |  0.003157  |  0.0265   |  0.2634  |  0.5818  |   0         |    1.669  |
| positions_liquidated_pct             |    14.32    |  0.008596 |  0         |  0.03228 |  0        |  0        |  0         |  0        |  0.0525  |  0.187   |   0         |    0.4267 |
| outflow_vs_baseline_pct              |     0       |  4.519    | -0.4534    | 80.57    | -0.9729   | -0.7794   | -0.4534    |  0.05187  |  1.543   | 84.21    |  -1         | 6391      |
| fixed_income_maturity_not_reinvested |    73.9     |  0.3695   |  0.113     |  0.4209  |  0        |  0        |  0.113     |  0.833    |  1       |  1       |   0         |    1      |
| cash_pct_of_portfolio_chg            |    14.32    |  0.02892  |  0.004387  |  0.08794 | -0.01604  | -0.004513 |  0.004387  |  0.01821  |  0.1959  |  0.474   |  -0.05478   |    0.8129 |
| aum_vs_baseline_pct                  |    14.32    | -0.02938  | -0.001826  |  0.1177  | -0.2511   | -0.01367  | -0.001826  |  0.006973 |  0.04029 |  0.08376 |  -0.9449    |    0.3508 |
| deposit_balance_change_pct_90d       |     0.02054 | -0.01267  | -0.01035   |  0.2168  | -0.3658   | -0.1318   | -0.01035   |  0.1094   |  0.3278  |  0.5237  |  -0.9755    |    1.839  |
| deposit_balance_vs_6m_avg_pct        |     0.02568 | -0.02478  | -0.019     |  0.2457  | -0.444    | -0.1532   | -0.019     |  0.1185   |  0.3443  |  0.5541  |  -0.9967    |    4.532  |
| net_deposit_flow_pct_90d             |     0.02054 | -0.06815  | -0.01341   |  0.3614  | -0.6016   | -0.1705   | -0.01341   |  0.1241   |  0.3161  |  0.4705  |  -6.942     |    1.71   |
| external_transfer_pct_of_balance_60d |     0       |  0.1237   |  0.008626  |  0.727   |  0.002196 |  0.00512  |  0.008626  |  0.01466  |  0.4317  |  3.047   |   0         |   30.22   |
| new_external_destinations_90d        |     1.494   |  0.07752  |  0         |  0.3307  |  0        |  0        |  0         |  0        |  1       |  2       |   0         |    3      |
| transfer_to_competitor_pct_90d       |     0       |  0.06647  |  0.007163  |  0.4146  |  0        |  0.002724 |  0.007163  |  0.01393  |  0.1036  |  1.592   |   0         |   18.58   |
| external_transfer_acceleration       |     0       |  0.02065  |  0.0003829 |  0.8617  | -0.01839  | -0.003557 |  0.0003829 |  0.004615 |  0.0386  |  1.989   | -30.71      |   22.6    |
| net_external_flow_pct_90d            |     0       |  0.07689  |  0.08097   |  0.2478  | -0.1669   |  0.01153  |  0.08097   |  0.1709   |  0.3428  |  0.5323  |  -6.291     |    3.977  |
| external_destination_concentration   |     0       |  0.5979   |  0.5158    |  0.2576  |  0.2759   |  0.3812   |  0.5158    |  0.9082   |  1       |  1       |   0.171     |    1      |
| salary_deposit_stopped_flag          |    47.13    |  0.03662  |  0         |  0.1878  |  0        |  0        |  0         |  0        |  0       |  1       |   0         |    1      |
| recurring_deposit_stopped_flag       |     6.948   |  0.04227  |  0         |  0.2012  |  0        |  0        |  0         |  0        |  0       |  1       |   0         |    1      |
| recurring_deposit_change_pct         |     7.015   | -0.06877  | -0.0079    |  0.3008  | -0.7679   | -0.08271  | -0.0079    |  0.01874  |  0.3073  |  0.6106  |  -1         |    2.858  |
| pension_deposit_stopped_flag         |    65.58    |  0.0188   |  0         |  0.1358  |  0        |  0        |  0         |  0        |  0       |  1       |   0         |    1      |
| business_payroll_stopped_flag        |    73.84    |  0.05654  |  0         |  0.231   |  0        |  0        |  0         |  0        |  1       |  1       |   0         |    1      |
| products_closed_180d                 |     0       |  0.1601   |  0         |  0.5909  |  0        |  0        |  0         |  0        |  1       |  3       |   0         |    6      |
| accounts_closed_90d                  |     0       |  0.2221   |  0         |  0.7549  |  0        |  0        |  0         |  0        |  1       |  4       |   0         |   12      |
| share_of_wallet                      |     0       |  0.4889   |  0.4593    |  0.2542  |  0.1211   |  0.2896   |  0.4593    |  0.663    |  1       |  1       |   7.702e-05 |    1      |
| share_of_wallet_change               |     0       | -0.02069  | -0.004886  |  0.1189  | -0.225    | -0.04593  | -0.004886  |  0.02092  |  0.129   |  0.3083  |  -0.9726    |    0.8945 |
| complaint_escalated_flag             |     0       |  0.05361  |  0         |  0.2253  |  0        |  0        |  0         |  0        |  1       |  1       |   0         |    1      |
| complaint_age_days                   |     0       |  2.293    |  0         | 18.34    |  0        |  0        |  0         |  0        |  0       | 78.28    |   0         |  364      |
| repeat_complaint_flag                |     0       |  0.03687  |  0         |  0.1885  |  0        |  0        |  0         |  0        |  0       |  1       |   0         |    1      |
| relationship_dissatisfaction_flag    |    70.49    |  0.04107  |  0         |  0.1985  |  0        |  0        |  0         |  0        |  0       |  1       |   0         |    1      |
| return_vs_benchmark                  |    39.78    | -0.009776 | -0.01076   |  0.04157 | -0.07601  | -0.03808  | -0.01076   |  0.01742  |  0.06099 |  0.09075 |  -0.159     |    0.1557 |
| banker_change_6m_flag                |     0       |  0.1477   |  0         |  0.3549  |  0        |  0        |  0         |  0        |  1       |  1       |   0         |    1      |
| contact_gap_ratio                    |     0       |  0.498    |  0.2667    |  0.6464  |  0.01111  |  0.1      |  0.2667    |  0.6222   |  1.778   |  3.336   |  -0         |   12.17   |
| client_reply_rate                    |    47.97    |  0.6085   |  0.6667    |  0.2439  |  0.2      |  0.4486   |  0.6667    |  0.75     |  1       |  1       |   0         |    1      |
| meetings_cancelled_by_client         |    60.69    |  0.3193   |  0         |  0.6831  |  0        |  0        |  0         |  0        |  2       |  3       |   0         |    9      |
| trustee_change_flag                  |    68.14    |  0.04513  |  0         |  0.2076  |  0        |  0        |  0         |  0        |  0       |  1       |   0         |    1      |
| bureau_new_mortgage_elsewhere        |     5.053   |  0.03954  |  0         |  0.1949  |  0        |  0        |  0         |  0        |  0       |  1       |   0         |    1      |
| multi_signal_count                   |     0       |  1.74     |  1         |  1.527   |  0        |  1        |  1         |  2        |  5       |  6       |   0         |    7      |
| log_relationship_value               |     0       | 15.5      | 15.39      |  1.013   | 14.05     | 14.72     | 15.39      | 16.14     | 17.28    | 18.34    |  13.82      |   20.62   |
| tenure_years                         |     0       |  9.162    |  7.79      |  6.119   |  1.97     |  4.56     |  7.79      | 12.26     | 21.06    | 29.29    |   1         |   50      |
| has_credit_anchor                    |     0       |  0.3414   |  0         |  0.4742  |  0        |  0        |  0         |  1        |  1       |  1       |   0         |    1      |
| has_trust                            |     0       |  0.3186   |  0         |  0.4659  |  0        |  0        |  0         |  1        |  1       |  1       |   0         |    1      |
| has_linked_business                  |     0       |  0.2643   |  0         |  0.441   |  0        |  0        |  0         |  1        |  1       |  1       |   0         |    1      |
| age_primary                          |     0       | 60.5      | 60         | 11.7     | 41        | 52        | 60         | 69        | 80       | 87       |  28         |   94      |

### 3.1 Controles (umbral: 0 casos)

|                                          |   casos |
|:-----------------------------------------|--------:|
| share_of_wallet ∉ [0,1]                  |       0 |
| client_reply_rate ∉ [0,1]                |       0 |
| flags ∉ {0,1}                            |       0 |
| salidas/redenciones % < 0                |       0 |
| salidas/redenciones % > 100%             |     190 |
| caída de saldo < −100%                   |       0 |
| montos negativos (valor, depósitos, AUM) |       0 |
| tenure < 0 o > edad − 18                 |       0 |
| history_months > 24 o > tenure           |       0 |
| IDs duplicados                           |       0 |

Resultado: salidas/redenciones % > 100% = 190. **No es error de dominio**: el denominador es el AUM *promedio* de la ventana, que cae cuando el hogar se lleva el portafolio, así que una salida total puede superar 100%. Se conservan (son la señal) y el binning por cuantiles las absorbe en el bin extremo sin capping.
- Duplicados, fechas inconsistentes, cambios de definición y quiebres estructurales no aplican o no se detectan: hay un solo corte y no hay fechas por registro.
- Cuentas dormidas: `history_months` < 24 en 1425 hogares (historia incompleta, se conservan; las ventanas de 90d están completas).

### 3.2 Ilustración de outliers · `external_transfer_pct_of_balance_60d` (p99 = 3.047)

|                                                                                        |   hogares |
|:---------------------------------------------------------------------------------------|----------:|
| error (∉ dominio: < 0)                                                                 |         0 |
| comportamiento real (> p99 y el saldo cae ≥ 20%)                                       |       163 |
| operación extraordinaria (> p99, saldo estable: p. ej. compra de inmueble / impuestos) |        32 |

Ninguno es error: no se capa. Los casos «comportamiento real» son la señal que se quiere capturar.
**Control de calidad.** Si un control da > 0, se corrige en la fuente; el capping al p99.5 aplica solo a errores confirmados. Missing estructural (p. ej. flags de pensión sin flujo de pensión) = «no aplica», nunca 0.

## 4. Muestra

**Objetivo.** Separar desarrollo y validación sin fuga. **Método.** 70/30 estratificado por segmento × target × indeterminado. Sin sobremuestreo: la tasa de eventos es suficiente, así que no hay pesos que guardar. La única corrección de intercepto es por excluir indeterminados (paso 11).

|                                           |   relaciones |   eventos |   tasa |   UHNW |
|:------------------------------------------|-------------:|----------:|-------:|-------:|
| Desarrollo (entrena)                      |       12,028 |     2,213 | 0.1840 |    689 |
| Desarrollo · indeterminados (no entrenan) |        1,603 |         0 | 0.0000 |     69 |
| Validación (modelo)                       |        5,155 |       949 | 0.1841 |    295 |
| Validación · indeterminados (se scorean)  |          687 |         0 | 0.0000 |     30 |

**Control de calidad.** La tasa de desarrollo y la de validación difieren < 0.1 pp (por construcción).
- **OOT: no es posible.** La base tiene un solo corte.
- La aprobación del paso 13 queda **condicionada** a una validación OOT sobre la cohorte más reciente cuando exista el panel mensual (el código de modo REAL aplica el mismo pipeline por cohorte).
**Decisiones.** Descartado el random split como única validación → se complementa con bootstrap y con estabilidad por subpoblación (paso 15).

## 5. Ingeniería de señales

**Objetivo.** Traducir comportamientos en señales con nivel, recencia, magnitud relativa, tendencia y cambio vs. baseline propio. **Por qué.** En UHNW el nivel absoluto no discrimina; el cambio vs. el propio cliente sí.
**Método.** La base ya trae las señales construidas (ventanas en el diccionario del paso 2):

| Tipo de señal | Variables en la base |
|---|---|
| Magnitud relativa al AUM/saldo | aum_outflow_pct_90d, investment_redemption_pct, positions_liquidated_pct, external_transfer_pct_of_balance_60d, transfer_to_competitor_pct_90d |
| Tendencia (3M vs 3M previo) | deposit_balance_change_pct_90d, recurring_deposit_change_pct |
| Cambio vs baseline propio | aum_vs_baseline_pct, deposit_balance_vs_6m_avg_pct, outflow_vs_baseline_pct (24m) |
| Aceleración | external_transfer_acceleration |
| Recencia / frecuencia | complaint_age_days, contact_gap_ratio, new_external_destinations_90d, meetings_cancelled_by_client |
| Nivel / estado | share_of_wallet, client_reply_rate, flags de nómina / pensión / queja / banquero |
| **No disponibles** | persistencia (meses consecutivos de deterioro), volatilidad, engagement digital → pedir el panel mensual |

Las 9 dimensiones del prompt quedan cubiertas salvo **engagement digital** (0 variables); «crédito / saldos» solo con crédito ancla y buró (este último condicionado).

## 6. Análisis univariado (desarrollo)

**Objetivo.** Confirmar dirección y tamaño de efecto antes de modelar.
**Método.** Mediana y rango intercuartil por grupo; effect size = Cliff δ = 2·AUC − 1 sobre no-missing; missing por grupo.
**Criterio.** Candidata si |δ| ≥ 0.05 y la dirección es la esperada; «CONTRARIA» se investiga.

|                                      | dimensión             |   mediana churn |   mediana no-churn | p25–p75 churn     | p25–p75 no-churn   |   % missing churn |   % missing no-churn |   Cliff δ | esperado   | observado   | evidencia   |
|:-------------------------------------|:----------------------|----------------:|-------------------:|:------------------|:-------------------|------------------:|---------------------:|----------:|:-----------|:------------|:------------|
| multi_signal_count                   | Compuesta             |           2.000 |              1.000 | 1 – 4             | 1 – 2              |             0.000 |                0.000 |     0.253 | +          | +           | consistente |
| share_of_wallet                      | Pérdida de productos  |           0.386 |              0.470 | 0.21 – 0.586      | 0.299 – 0.676      |             0.000 |                0.000 |    -0.189 | −          | −           | consistente |
| fixed_income_maturity_not_reinvested | Salida de activos     |           0.498 |              0.000 | 0 – 1             | 0 – 0.751          |            77.858 |               72.878 |     0.188 | +          | +           | consistente |
| banker_change_6m_flag                | Relación con banquero |           0.000 |              0.000 | 0 – 1             | 0 – 0              |             0.000 |                0.000 |     0.185 | +          | +           | consistente |
| external_transfer_pct_of_balance_60d | Externalización       |           0.010 |              0.008 | 0.00586 – 0.021   | 0.00484 – 0.0137   |             0.000 |                0.000 |     0.181 | +          | +           | consistente |
| contact_gap_ratio                    | Relación con banquero |           0.389 |              0.256 | 0.144 – 0.878     | 0.1 – 0.578        |             0.000 |                0.000 |     0.178 | +          | +           | consistente |
| aum_vs_baseline_pct                  | Deterioro de AUM      |          -0.006 |             -0.001 | -0.0418 – 0.00322 | -0.0121 – 0.00737  |            23.000 |               10.688 |    -0.178 | −          | −           | consistente |
| transfer_to_competitor_pct_90d       | Externalización       |           0.009 |              0.007 | 0.00345 – 0.0213  | 0.00255 – 0.0129   |             0.000 |                0.000 |     0.167 | +          | +           | consistente |
| aum_outflow_pct_90d                  | Salida de activos     |           0.002 |              0.000 | 0 – 0.0293        | 0 – 0.0115         |            23.000 |               10.688 |     0.151 | +          | +           | consistente |
| deposit_balance_vs_6m_avg_pct        | Deterioro de AUM      |          -0.053 |             -0.011 | -0.243 – 0.09     | -0.14 – 0.125      |             0.000 |                0.031 |    -0.150 | −          | −           | consistente |
| share_of_wallet_change               | Pérdida de productos  |          -0.015 |             -0.003 | -0.0939 – 0.0146  | -0.0387 – 0.0203   |             0.000 |                0.000 |    -0.145 | −          | −           | consistente |
| net_deposit_flow_pct_90d             | Deterioro de AUM      |          -0.053 |             -0.007 | -0.279 – 0.0938   | -0.154 – 0.131     |             0.000 |                0.020 |    -0.142 | −          | −           | consistente |
| return_vs_benchmark                  | Fricción de servicio  |          -0.019 |             -0.009 | -0.046 – 0.00785  | -0.0363 – 0.0189   |            46.859 |               37.310 |    -0.138 | −          | −           | consistente |
| deposit_balance_change_pct_90d       | Deterioro de AUM      |          -0.039 |             -0.002 | -0.198 – 0.0908   | -0.12 – 0.117      |             0.000 |                0.020 |    -0.137 | −          | −           | consistente |
| investment_redemption_pct            | Salida de activos     |           0.009 |              0.002 | 0 – 0.0541        | 0 – 0.0245         |            23.000 |               10.688 |     0.136 | +          | +           | consistente |
| meetings_cancelled_by_client         | Relación con banquero |           0.000 |              0.000 | 0 – 1             | 0 – 0              |            56.801 |               61.477 |     0.134 | +          | +           | consistente |
| recurring_deposit_change_pct         | Banco principal       |          -0.022 |             -0.006 | -0.221 – 0.0127   | -0.078 – 0.0211    |             6.417 |                7.071 |    -0.127 | −          | −           | consistente |
| net_external_flow_pct_90d            | Externalización       |           0.066 |              0.085 | -0.00912 – 0.16   | 0.0167 – 0.175     |             0.000 |                0.000 |    -0.122 | −          | −           | consistente |
| client_reply_rate                    | Relación con banquero |           0.600 |              0.667 | 0.333 – 0.75      | 0.5 – 0.769        |            61.410 |               44.952 |    -0.106 | −          | −           | consistente |
| products_closed_180d                 | Pérdida de productos  |           0.000 |              0.000 | 0 – 0             | 0 – 0              |             0.000 |                0.000 |     0.105 | +          | +           | consistente |
| cash_pct_of_portfolio_chg            | Salida de activos     |           0.007 |              0.004 | -0.00385 – 0.0351 | -0.00439 – 0.0173  |            23.000 |               10.688 |     0.099 | +          | +           | consistente |
| positions_liquidated_pct             | Salida de activos     |           0.000 |              0.000 | 0 – 0             | 0 – 0              |            23.000 |               10.688 |     0.098 | +          | +           | consistente |
| new_external_destinations_90d        | Externalización       |           0.000 |              0.000 | 0 – 0             | 0 – 0              |             1.627 |                1.457 |     0.097 | +          | +           | consistente |
| outflow_vs_baseline_pct              | Salida de activos     |          -0.397 |             -0.495 | -0.752 – 0.206    | -0.797 – -0.00385  |             0.000 |                0.000 |     0.096 | +          | +           | consistente |
| salary_deposit_stopped_flag          | Banco principal       |           0.000 |              0.000 | 0 – 0             | 0 – 0              |            47.221 |               47.590 |     0.096 | +          | +           | consistente |
| recurring_deposit_stopped_flag       | Banco principal       |           0.000 |              0.000 | 0 – 0             | 0 – 0              |             6.281 |                6.979 |     0.084 | +          | +           | consistente |
| business_payroll_stopped_flag        | Banco principal       |           0.000 |              0.000 | 0 – 0             | 0 – 0              |            71.939 |               73.928 |     0.082 | +          | +           | consistente |
| trustee_change_flag                  | Evento de vida        |           0.000 |              0.000 | 0 – 0             | 0 – 0              |            68.821 |               67.652 |     0.067 | +          | +           | consistente |
| bureau_new_mortgage_elsewhere        | Crédito / saldos      |           0.000 |              0.000 | 0 – 0             | 0 – 0              |             5.016 |                5.023 |     0.066 | +          | +           | consistente |
| complaint_escalated_flag             | Fricción de servicio  |           0.000 |              0.000 | 0 – 0             | 0 – 0              |             0.000 |                0.000 |     0.066 | +          | +           | consistente |
| pension_deposit_stopped_flag         | Banco principal       |           0.000 |              0.000 | 0 – 0             | 0 – 0              |            65.025 |               65.828 |     0.065 | +          | +           | consistente |
| accounts_closed_90d                  | Pérdida de productos  |           0.000 |              0.000 | 0 – 0             | 0 – 0              |             0.000 |                0.000 |     0.064 | +          | +           | consistente |
| repeat_complaint_flag                | Fricción de servicio  |           0.000 |              0.000 | 0 – 0             | 0 – 0              |             0.000 |                0.000 |     0.063 | +          | +           | consistente |
| relationship_dissatisfaction_flag    | Fricción de servicio  |           0.000 |              0.000 | 0 – 0             | 0 – 0              |            69.679 |               71.034 |     0.060 | +          | +           | consistente |
| external_destination_concentration   | Externalización       |           0.530 |              0.513 | 0.394 – 0.966     | 0.378 – 0.845      |             0.000 |                0.000 |     0.055 | +          | +           | consistente |
| complaint_age_days                   | Fricción de servicio  |           0.000 |              0.000 | 0 – 0             | 0 – 0              |             0.000 |                0.000 |     0.052 | +          | +           | consistente |
| external_transfer_acceleration       | Externalización       |           0.001 |              0.000 | -0.004 – 0.00665  | -0.00341 – 0.0042  |             0.000 |                0.000 |     0.046 | +          | +           | débil       |
| tenure_years                         | Estructural           |           7.400 |              7.860 | 4.33 – 11.9       | 4.62 – 12.4        |             0.000 |                0.000 |    -0.040 | −          | −           | débil       |
| has_credit_anchor                    | Crédito / saldos      |           0.000 |              0.000 | 0 – 1             | 0 – 1              |             0.000 |                0.000 |    -0.024 | −          | −           | débil       |
| age_primary                          | Estructural           |          61.000 |             60.000 | 53 – 68           | 52 – 69            |             0.000 |                0.000 |     0.013 | ·          | +           | débil       |

Candidatas (evidencia consistente): 36 de 40; contrarias: ninguna.
El missing es informativo en varias variables (p. ej. `client_reply_rate`: missing = sin interacciones registradas), por eso va como bin propio.

## 7. Pre-segmentación

**Objetivo.** Ver si la cartera tiene poblaciones estructuralmente distintas que justifiquen scorecards separados.
**Método.** K-means sobre variables estructurales estandarizadas: ln(valor), antigüedad, % depósitos, tenencias, flujos recurrentes y crédito ancla. **Sin edad (ECOA).**
K se elige por silhouette entre las opciones con tamaño mínimo ≥ 5% y estabilidad (ARI medio en 5 submuestras del 80%) ≥ 0.80.

|   K |       WCSS |   silhouette |   estabilidad (ARI medio) |   tamaño mín % |
|----:|-----------:|-------------:|--------------------------:|---------------:|
|   2 | 157298.206 |        0.289 |                     1.000 |         14.317 |
|   3 | 135557.984 |        0.189 |                     0.649 |         14.317 |
|   4 | 124015.405 |        0.183 |                     0.650 |         14.317 |
|   5 | 115637.237 |        0.179 |                     0.734 |         14.158 |
|   6 | 111180.791 |        0.183 |                     0.544 |         13.095 |
|   7 | 106277.164 |        0.163 |                     0.630 |          5.074 |

**K elegido = 2.**

|   cluster |   relaciones |   valor mediano ($) |   tenure |   trust |   negocio |   nomina |   pension |   dividendos |   inversiones |   uhnw |   eventos |   churn | arquetipo estructural         |
|----------:|-------------:|--------------------:|---------:|--------:|----------:|---------:|----------:|-------------:|--------------:|-------:|----------:|--------:|:------------------------------|
|         0 |       16,685 |         5297079.170 |    7.790 |   0.321 |     0.265 |    0.538 |     0.338 |        0.547 |         1.000 |  0.062 |     2,421 |   0.145 | Inversionista patrimonial     |
|         1 |        2,788 |         2940066.075 |    7.800 |   0.302 |     0.261 |    0.542 |     0.354 |        0.000 |         0.000 |  0.016 |       741 |   0.266 | Depositante (sin inversiones) |

Solo K = 2 es estable (ARI ≥ 0.80): la estructura la domina la tenencia de inversiones. Los arquetipos del prompt (fundadores, next-gen, ejecutivos, family offices) **no emergen de forma estable** con las variables estructurales de la base (K ≥ 3 da ARI < 0.80); no se fuerzan.
Churn rate por segmento: descriptivo; **no implica causalidad** (el segmento correlaciona con antigüedad y crédito ancla, que están en el mecanismo).

**Regla de decisión.**
- Scorecard separado solo si cada segmento conserva ≥ 100 eventos **y** el modelo propio mejora en validación.
- Eventos de desarrollo por segmento: Depositante (sin inversiones): 509, Inversionista patrimonial: 1704.

| segmento                      |   eventos dev |   AUC único |   AUC propio |      Δ |
|:------------------------------|--------------:|------------:|-------------:|-------:|
| Depositante (sin inversiones) |           509 |       0.591 |        0.588 | -0.003 |
| Inversionista patrimonial     |         1,704 |       0.698 |        0.698 |  0.001 |

**Decisión: un solo scorecard.** La ganancia máxima de AUC de un modelo propio es +0.001, que no compensa multiplicar por 2 la validación y el monitoreo. El segmento se usa en la calibración (paso 14) y en el monitoreo (paso 15).

## 8. Correlación y diagnóstico de estructura

**Objetivo.** Identificar variables que miden el mismo fenómeno. **Método.** Pearson y Spearman (missing imputado a la mediana solo para este diagnóstico) y VIF sobre crudas.
PCA **solo diagnóstico**: no entra en la selección ni en el modelo.

### 8.1 Pares con |ρ| ≥ 0.6 (16)

| par                                                            |   Spearman |   Pearson | decisión                                                       |
|:---------------------------------------------------------------|-----------:|----------:|:---------------------------------------------------------------|
| aum_outflow_pct_90d ~ investment_redemption_pct                |      0.646 |     0.405 | se prefiere aum_outflow_pct_90d (IV 0.287 vs 0.218)            |
| aum_outflow_pct_90d ~ aum_vs_baseline_pct                      |     -0.737 |    -0.856 | se prefiere aum_vs_baseline_pct (IV 0.322 vs 0.287)            |
| investment_redemption_pct ~ positions_liquidated_pct           |      0.466 |     0.648 | se prefiere investment_redemption_pct (IV 0.218 vs 0.203)      |
| investment_redemption_pct ~ cash_pct_of_portfolio_chg          |      0.326 |     0.713 | se prefiere investment_redemption_pct (IV 0.218 vs 0.197)      |
| positions_liquidated_pct ~ cash_pct_of_portfolio_chg           |      0.412 |     0.616 | se prefiere positions_liquidated_pct (IV 0.203 vs 0.197)       |
| aum_vs_baseline_pct ~ external_transfer_pct_of_balance_60d     |     -0.146 |    -0.658 | se prefiere aum_vs_baseline_pct (IV 0.322 vs 0.210)            |
| deposit_balance_change_pct_90d ~ deposit_balance_vs_6m_avg_pct |      0.883 |     0.888 | se prefiere deposit_balance_vs_6m_avg_pct (IV 0.168 vs 0.130)  |
| deposit_balance_change_pct_90d ~ net_deposit_flow_pct_90d      |      0.804 |     0.767 | se prefiere net_deposit_flow_pct_90d (IV 0.150 vs 0.130)       |
| deposit_balance_change_pct_90d ~ net_external_flow_pct_90d     |      0.621 |     0.581 | se prefiere net_external_flow_pct_90d (IV 0.182 vs 0.130)      |
| deposit_balance_change_pct_90d ~ share_of_wallet_change        |      0.671 |     0.571 | se prefiere share_of_wallet_change (IV 0.145 vs 0.130)         |
| deposit_balance_vs_6m_avg_pct ~ net_deposit_flow_pct_90d       |      0.907 |     0.838 | se prefiere deposit_balance_vs_6m_avg_pct (IV 0.168 vs 0.150)  |
| deposit_balance_vs_6m_avg_pct ~ net_external_flow_pct_90d      |      0.686 |     0.642 | se prefiere net_external_flow_pct_90d (IV 0.182 vs 0.168)      |
| deposit_balance_vs_6m_avg_pct ~ share_of_wallet_change         |      0.714 |     0.602 | se prefiere deposit_balance_vs_6m_avg_pct (IV 0.168 vs 0.145)  |
| net_deposit_flow_pct_90d ~ net_external_flow_pct_90d           |      0.752 |     0.809 | se prefiere net_external_flow_pct_90d (IV 0.182 vs 0.150)      |
| salary_deposit_stopped_flag ~ recurring_deposit_stopped_flag   |      0.677 |     0.677 | se prefiere recurring_deposit_stopped_flag (IV 0.001 vs 0.000) |
| products_closed_180d ~ accounts_closed_90d                     |      0.478 |     0.719 | se prefiere products_closed_180d (IV 0.091 vs 0.000)           |

### 8.2 VIF sobre variables crudas (top 10)

|                                      |   VIF |
|:-------------------------------------|------:|
| deposit_balance_vs_6m_avg_pct        |  7.11 |
| net_deposit_flow_pct_90d             |  6.51 |
| aum_vs_baseline_pct                  |  6.09 |
| deposit_balance_change_pct_90d       |  5.02 |
| aum_outflow_pct_90d                  |  4.20 |
| multi_signal_count                   |  3.62 |
| net_external_flow_pct_90d            |  3.44 |
| investment_redemption_pct            |  3.34 |
| products_closed_180d                 |  2.67 |
| external_transfer_pct_of_balance_60d |  2.53 |

### 8.3 PCA diagnóstico (autovalores > 1: 10 de 39)

|     |   eigenvalue |   % varianza |   % acumulada | variables dominantes (loading)                                                                                                                          |
|:----|-------------:|-------------:|--------------:|:--------------------------------------------------------------------------------------------------------------------------------------------------------|
| PC1 |         8.27 |        21.21 |         21.21 | aum_vs_baseline_pct (-0.82); multi_signal_count (+0.79); net_deposit_flow_pct_90d (-0.75); aum_outflow_pct_90d (+0.74)                                  |
| PC2 |         2.27 |         5.83 |         27.03 | cash_pct_of_portfolio_chg (-0.54); deposit_balance_change_pct_90d (-0.54); deposit_balance_vs_6m_avg_pct (-0.53); positions_liquidated_pct (-0.53)      |
| PC3 |         2.02 |         5.17 |         32.20 | investment_redemption_pct (+0.56); cash_pct_of_portfolio_chg (+0.53); recurring_deposit_stopped_flag (-0.44); positions_liquidated_pct (+0.41)          |
| PC4 |         1.71 |         4.38 |         36.58 | complaint_escalated_flag (+0.65); repeat_complaint_flag (+0.63); complaint_age_days (+0.55); multi_signal_count (+0.26)                                 |
| PC5 |         1.53 |         3.94 |         40.52 | outflow_vs_baseline_pct (+0.61); external_transfer_acceleration (+0.44); transfer_to_competitor_pct_90d (+0.31); recurring_deposit_stopped_flag (-0.31) |
| PC6 |         1.17 |         3.00 |         43.52 | client_reply_rate (-0.40); meetings_cancelled_by_client (+0.36); external_transfer_acceleration (+0.34); complaint_age_days (-0.30)                     |

**Lectura (desde los loadings, no por nombre):**
- Los primeros componentes agrupan **salida de activos** (outflow / redención / liquidación / baseline) y **externalización** (transferencias externas, flujo neto): varias variables miden el mismo fenómeno.
- La varianza está repartida (sin componente dominante): hay información en varias dimensiones, lo que respalda un scorecard con diversidad de dimensiones.

## 9. Binning, WoE e IV

**Objetivo.** Discretizar cada variable en 4–8 bins monótonos con sentido de negocio.
**Método.** optbinning (programación con restricciones):
- Fine classing de 20 pre-bins → coarse de ≤ 8 bins.
- Cada bin con ≥ 5% de la población y ≥ 30 eventos.
- **Tendencia monótona forzada a la dirección esperada.**
- Missing como bin propio si cumple los mínimos; si no, se asigna al bin de tasa más cercana.
**Fórmulas.** WoE = ln(%buenos / %malos); IV = Σ (%buenos − %malos)·WoE.
**Criterio IV.** < 0.02 fuera · 0.02–0.10 débil · 0.10–0.30 medio · 0.30–0.50 fuerte · > 0.50 sospechoso de fuga.

| variable                             | dimensión             | tendencia forzada   |   bins |   IV (forzado) |   IV (auto) | missing                                                | monótono val   | clase IV       |   pérdida por monotonicidad |
|:-------------------------------------|:----------------------|:--------------------|-------:|---------------:|------------:|:-------------------------------------------------------|:---------------|:---------------|----------------------------:|
| aum_vs_baseline_pct                  | Deterioro de AUM      | descending          |      3 |          0.322 |       0.322 | bin propio                                             | sí             | fuerte         |                       0.000 |
| multi_signal_count                   | Compuesta             | ascending           |      4 |          0.294 |       0.294 | sin missing                                            | sí             | medio          |                       0.000 |
| aum_outflow_pct_90d                  | Salida de activos     | ascending           |      3 |          0.287 |       0.287 | bin propio                                             | sí             | medio          |                       0.000 |
| transfer_to_competitor_pct_90d       | Externalización       | ascending           |      4 |          0.260 |       0.260 | sin missing                                            | sí             | medio          |                       0.000 |
| banker_change_6m_flag                | Relación con banquero | ascending           |      2 |          0.223 |       0.223 | sin missing                                            | sí             | medio          |                       0.000 |
| investment_redemption_pct            | Salida de activos     | ascending           |      3 |          0.218 |       0.218 | bin propio                                             | sí             | medio          |                       0.000 |
| external_transfer_pct_of_balance_60d | Externalización       | ascending           |      4 |          0.210 |       0.210 | sin missing                                            | sí             | medio          |                       0.000 |
| positions_liquidated_pct             | Salida de activos     | ascending           |      2 |          0.203 |       0.203 | bin propio                                             | sí             | medio          |                       0.000 |
| cash_pct_of_portfolio_chg            | Salida de activos     | ascending           |      3 |          0.197 |       0.197 | bin propio                                             | sí             | medio          |                       0.000 |
| net_external_flow_pct_90d            | Externalización       | descending          |      3 |          0.182 |       0.182 | sin missing                                            | sí             | medio          |                       0.000 |
| deposit_balance_vs_6m_avg_pct        | Deterioro de AUM      | descending          |      4 |          0.168 |       0.168 | asignado a [0.2884, inf) (missing < 5% o < 30 eventos) | no             | medio          |                       0.000 |
| net_deposit_flow_pct_90d             | Deterioro de AUM      | descending          |      4 |          0.150 |       0.150 | asignado a [0.3121, inf) (missing < 5% o < 30 eventos) | no             | medio          |                       0.000 |
| share_of_wallet_change               | Pérdida de productos  | descending          |      4 |          0.145 |       0.145 | sin missing                                            | sí             | medio          |                       0.000 |
| share_of_wallet                      | Pérdida de productos  | descending          |      5 |          0.141 |       0.141 | sin missing                                            | sí             | medio          |                       0.000 |
| client_reply_rate                    | Relación con banquero | descending          |      2 |          0.135 |       0.135 | bin propio                                             | sí             | medio          |                       0.000 |
| deposit_balance_change_pct_90d       | Deterioro de AUM      | descending          |      4 |          0.130 |       0.130 | asignado a [0.2895, inf) (missing < 5% o < 30 eventos) | no             | medio          |                       0.000 |
| new_external_destinations_90d        | Externalización       | ascending           |      2 |          0.123 |       0.123 | asignado a [-inf, 0.5) (missing < 5% o < 30 eventos)   | sí             | medio          |                       0.000 |
| external_transfer_acceleration       | Externalización       | ascending           |      3 |          0.119 |       0.119 | sin missing                                            | sí             | medio          |                       0.000 |
| contact_gap_ratio                    | Relación con banquero | ascending           |      6 |          0.107 |       0.107 | sin missing                                            | sí             | medio          |                       0.000 |
| products_closed_180d                 | Pérdida de productos  | ascending           |      2 |          0.091 |       0.091 | sin missing                                            | sí             | débil          |                       0.000 |
| recurring_deposit_change_pct         | Banco principal       | descending          |      3 |          0.087 |       0.087 | bin propio                                             | sí             | débil          |                       0.000 |
| return_vs_benchmark                  | Fricción de servicio  | descending          |      4 |          0.080 |       0.080 | bin propio                                             | sí             | débil          |                       0.000 |
| complaint_escalated_flag             | Fricción de servicio  | ascending           |      2 |          0.068 |       0.068 | sin missing                                            | sí             | débil          |                       0.000 |
| outflow_vs_baseline_pct              | Salida de activos     | ascending           |      3 |          0.066 |       0.066 | sin missing                                            | sí             | débil          |                       0.000 |
| fixed_income_maturity_not_reinvested | Salida de activos     | ascending           |      3 |          0.048 |       0.048 | bin propio                                             | sí             | débil          |                       0.000 |
| meetings_cancelled_by_client         | Relación con banquero | ascending           |      2 |          0.044 |       0.044 | bin propio                                             | sí             | débil          |                       0.000 |
| external_destination_concentration   | Externalización       | ascending           |      2 |          0.022 |       0.022 | sin missing                                            | sí             | débil          |                       0.000 |
| tenure_years                         | Estructural           | descending          |      2 |          0.004 |       0.004 | sin missing                                            | sí             | fuera (< 0.02) |                       0.000 |
| has_credit_anchor                    | Crédito / saldos      | descending          |      2 |          0.003 |       0.003 | sin missing                                            | sí             | fuera (< 0.02) |                       0.000 |
| business_payroll_stopped_flag        | Banco principal       | ascending           |      1 |          0.002 |       0.002 | bin propio                                             | sí             | fuera (< 0.02) |                       0.000 |
| relationship_dissatisfaction_flag    | Fricción de servicio  | ascending           |      1 |          0.001 |       0.001 | bin propio                                             | sí             | fuera (< 0.02) |                       0.000 |
| recurring_deposit_stopped_flag       | Banco principal       | ascending           |      1 |          0.001 |       0.001 | bin propio                                             | sí             | fuera (< 0.02) |                       0.000 |
| trustee_change_flag                  | Evento de vida        | ascending           |      1 |          0.001 |       0.001 | bin propio                                             | sí             | fuera (< 0.02) |                       0.000 |
| pension_deposit_stopped_flag         | Banco principal       | ascending           |      1 |          0.000 |       0.000 | bin propio                                             | sí             | fuera (< 0.02) |                       0.000 |
| salary_deposit_stopped_flag          | Banco principal       | ascending           |      1 |          0.000 |       0.000 | bin propio                                             | sí             | fuera (< 0.02) |                       0.000 |
| bureau_new_mortgage_elsewhere        | Crédito / saldos      | ascending           |      1 |          0.000 |       0.000 | bin propio                                             | sí             | fuera (< 0.02) |                       0.000 |
| accounts_closed_90d                  | Pérdida de productos  | ascending           |      1 |          0.000 |       0.000 | sin missing                                            | sí             | fuera (< 0.02) |                     nan     |
| repeat_complaint_flag                | Fricción de servicio  | ascending           |      1 |          0.000 |       0.000 | sin missing                                            | sí             | fuera (< 0.02) |                     nan     |
| complaint_age_days                   | Fricción de servicio  | ascending           |      1 |          0.000 |       0.000 | sin missing                                            | sí             | fuera (< 0.02) |                     nan     |
| age_primary                          | Estructural           | auto_asc_desc       |      1 |          0.000 |       0.000 | sin missing                                            | sí             | fuera (< 0.02) |                     nan     |

*pérdida por monotonicidad* = 1 − IV forzado ÷ IV con tendencia libre. Si es > 50%, la relación no sigue la lógica de negocio y la variable no pasa.
Además, bins contiguos deben diferir en tasa con p < 0.05 (si no, se funden); por eso varias variables quedan con 2–4 bins en lugar de 4–8. Se prefiere menos bins estables a más bins con WoE de ruido.
**Flags raros (IV ≈ 0 con 1 bin):** quejas repetidas, insatisfacción expresada, cambio de trustee, nómina o pensión detenida y buró. Su categoría «1» tiene menos del 5% de la población, así que no puede ser un bin propio. No se pierden: pasan a **overrides y reglas de EWS** (pasos 12 y 16), donde se mide su precisión directamente.

### 9.1 Comparación de esquemas de binning (3 variables del modelo final)

**aum_vs_baseline_pct**

|                               |   bins (sin missing) |    IV | monótono   |   bin mín % pob |   bin mín eventos | cortes                                       |
|:------------------------------|---------------------:|------:|:-----------|----------------:|------------------:|:---------------------------------------------|
| Negocio (umbrales Excel/deck) |                    3 | 0.318 | sí         |           3.675 |                92 | -0.2, -0.05                                  |
| Cuantiles (quintiles)         |                    5 | 0.222 | no         |          12.912 |               216 | -0.0189, -0.00558, 0, 0.0112                 |
| Data-driven (árbol CART)      |                    6 | 0.326 | no         |           4.381 |                76 | -0.203, -0.0427, -0.0123, -0.00846, -0.00611 |
| Óptimo (optbinning, monótono) |                    3 | 0.322 | sí         |           5.653 |               216 | -0.203, -0.0216                              |

**transfer_to_competitor_pct_90d**

|                               |   bins (sin missing) |    IV | monótono   |   bin mín % pob |   bin mín eventos | cortes                                    |
|:------------------------------|---------------------:|------:|:-----------|----------------:|------------------:|:------------------------------------------|
| Negocio (umbrales Excel/deck) |                    4 | 0.249 | no         |           0.873 |                26 | 0.001, 0.05, 0.15                         |
| Cuantiles (quintiles)         |                    5 | 0.107 | no         |          19.995 |               347 | 0.0017, 0.00532, 0.00912, 0.0161          |
| Data-driven (árbol CART)      |                    6 | 0.267 | no         |           5.246 |               117 | 0.000841, 0.00264, 0.0068, 0.0199, 0.0847 |
| Óptimo (optbinning, monótono) |                    4 | 0.260 | sí         |           5.246 |               242 | 0.0068, 0.0199, 0.0847                    |

**client_reply_rate**

|                               |   bins (sin missing) |    IV | monótono   |   bin mín % pob |   bin mín eventos | cortes                            |
|:------------------------------|---------------------:|------:|:-----------|----------------:|------------------:|:----------------------------------|
| Negocio (umbrales Excel/deck) |                    3 | 0.129 | sí         |          13.302 |               248 | 0.5, 0.75                         |
| Cuantiles (quintiles)         |                    5 | 0.135 | no         |           4.490 |                62 | 0.375, 0.6, 0.667, 0.8            |
| Data-driven (árbol CART)      |                    6 | 0.155 | no         |           2.702 |                27 | 0.345, 0.678, 0.747, 0.754, 0.931 |
| Óptimo (optbinning, monótono) |                    2 | 0.135 | sí         |          10.226 |               240 | 0.345                             |

### 9.2 Tablas WoE/IV (desarrollo) y estabilidad del WoE dev → val

**aum_vs_baseline_pct** · IV = 0.322 · missing: bin propio

| bin                 |     N |   % pob |   malos |   tasa churn |     WoE |   IV bin |   tasa churn val |   WoE val |
|:--------------------|------:|--------:|--------:|-------------:|--------:|---------:|-----------------:|----------:|
| [-inf, -0.2031)     |   680 |  0.0565 |     319 |       0.4691 | -1.3659 |   0.1467 |           0.4776 |   -1.3990 |
| [-0.2031, -0.02156) | 1,219 |  0.1013 |     216 |       0.1772 |  0.0459 |   0.0002 |           0.1534 |    0.2192 |
| [-0.02156, inf)     | 8,571 |  0.7126 |   1,169 |       0.1364 |  0.3560 |   0.0804 |           0.1412 |    0.3167 |
| Missing             | 1,558 |  0.1295 |     509 |       0.3267 | -0.7664 |   0.0944 |           0.3281 |   -0.7723 |

**transfer_to_competitor_pct_90d** · IV = 0.260 · missing: sin missing

| bin                 |     N |   % pob |   malos |   tasa churn |     WoE |   IV bin |   tasa churn val |   WoE val |
|:--------------------|------:|--------:|--------:|-------------:|--------:|---------:|-----------------:|----------:|
| [-inf, 0.006803)    | 5,838 |  0.4854 |     886 |       0.1518 |  0.2313 |   0.0241 |           0.1616 |    0.1576 |
| [0.006803, 0.01991) | 4,395 |  0.3654 |     731 |       0.1663 |  0.1223 |   0.0053 |           0.1705 |    0.0933 |
| [0.01991, 0.08466)  | 1,164 |  0.0968 |     242 |       0.2079 | -0.1520 |   0.0023 |           0.1715 |    0.0863 |
| [0.08466, inf)      |   631 |  0.0525 |     354 |       0.5610 | -1.7348 |   0.2286 |           0.5251 |   -1.5893 |

**client_reply_rate** · IV = 0.135 · missing: bin propio

| bin            |     N |   % pob |   malos |   tasa churn |     WoE |   IV bin |   tasa churn val |   WoE val |
|:---------------|------:|--------:|--------:|-------------:|--------:|---------:|-----------------:|----------:|
| [-inf, 0.3452) | 1,230 |  0.1023 |     240 |       0.1951 | -0.0725 |   0.0005 |           0.2129 |   -0.1815 |
| [0.3452, inf)  | 5,027 |  0.4179 |     614 |       0.1221 |  0.4828 |   0.0831 |           0.1225 |    0.4804 |
| Missing        | 5,771 |  0.4798 |   1,359 |       0.2355 | -0.3120 |   0.0513 |           0.2324 |   -0.2940 |

**Problemas a vigilar.**
- Bins pequeños: el mínimo de 5% y 30 eventos evita WoE con ruido.
- WoE inestable entre cohortes: no medible con un solo corte; dev → val es el proxy.
- No monotonicidad: si aparece en validación, se funden bins contiguos (nunca se invierte el signo).
- Missing con WoE alto: se revisa si el missing es informativo (sin interacciones) o un defecto de captura.

## 10. Selección de variables

**Objetivo.** 5–8 variables no redundantes, con diversidad de dimensiones y signo correcto.
**Método (en orden).**
1. Filtro de negocio y regulación: variables prohibidas o condicionadas fuera.
2. IV entre 0.02 y 0.50, con monotonicidad que no destruye el IV.
3. Clustering de variables sobre WoE: jerárquico, distancia 1 − |ρ Spearman|, corte en |ρ| = 0.6. El centroide de cada cluster es la media del WoE estandarizado, sin PCA. Representante = menor (1 − R² propio)/(1 − R² vecino); si hay empate (± 0.05), gana el mayor IV.
4. Orden de entrada en el camino LASSO (logística L1) entre representantes.
5. Forward selection en ese orden. Entra una variable si cumple a la vez:
   - β > 0 sobre WoE;
   - VIF < 5;
   - p < 0.05;
   - ΔAUC (CV 5-fold) ≥ 0.002 una vez alcanzado el mínimo de 5;
   - máximo 2 variables por dimensión.

### 10.1 Variables excluidas por regulación o diseño

|                               | motivo                                                                                                 |
|:------------------------------|:-------------------------------------------------------------------------------------------------------|
| age_primary                   | Característica protegida (ECOA): no entra al modelo ni a la segmentación.                              |
| bureau_new_mortgage_elsewhere | Buró (FCRA): condicionada a propósito permisible; fuera del campeón hasta dictamen legal.              |
| multi_signal_count            | Compuesta de las demás con umbrales fijos: doble conteo; se usa como regla de EWS, no como predictor.  |
| log_relationship_value        | Tamaño no es comportamiento: se usa en priorización (p × AUM) y calibración por banda, no en el score. |
| has_trust                     | Estructural sin hipótesis de signo: va a pre-segmentación.                                             |
| has_linked_business           | Estructural sin hipótesis de signo: va a pre-segmentación.                                             |

### 10.2 Clustering de variables (21 clusters, 21 representantes)

| variable                             |   cluster |   R² propio |   R² vecino |   ratio (1−R²p)/(1−R²v) |    IV | representante   |
|:-------------------------------------|----------:|------------:|------------:|------------------------:|------:|:----------------|
| client_reply_rate                    |         1 |       1.000 |       0.226 |                   0.000 | 0.135 | True            |
| contact_gap_ratio                    |         2 |       1.000 |       0.226 |                   0.000 | 0.107 | True            |
| banker_change_6m_flag                |         3 |       1.000 |       0.073 |                   0.000 | 0.223 | True            |
| complaint_escalated_flag             |         4 |       1.000 |       0.031 |                   0.000 | 0.068 | True            |
| transfer_to_competitor_pct_90d       |         5 |       1.000 |       0.539 |                   0.000 | 0.260 | True            |
| external_transfer_pct_of_balance_60d |         6 |       1.000 |       0.577 |                   0.000 | 0.210 | True            |
| outflow_vs_baseline_pct              |         7 |       1.000 |       0.200 |                   0.000 | 0.066 | True            |
| deposit_balance_vs_6m_avg_pct        |         8 |       0.900 |       0.462 |                   0.186 | 0.168 | True            |
| deposit_balance_change_pct_90d       |         8 |       0.838 |       0.352 |                   0.250 | 0.130 | False           |
| net_deposit_flow_pct_90d             |         8 |       0.865 |       0.486 |                   0.264 | 0.150 | False           |
| net_external_flow_pct_90d            |         9 |       1.000 |       0.577 |                   0.000 | 0.182 | True            |
| share_of_wallet_change               |        10 |       1.000 |       0.394 |                   0.000 | 0.145 | True            |
| new_external_destinations_90d        |        11 |       1.000 |       0.488 |                   0.000 | 0.123 | True            |
| external_transfer_acceleration       |        12 |       1.000 |       0.405 |                   0.000 | 0.119 | True            |
| products_closed_180d                 |        13 |       1.000 |       0.186 |                   0.000 | 0.091 | True            |
| share_of_wallet                      |        14 |       1.000 |       0.132 |                   0.000 | 0.141 | True            |
| cash_pct_of_portfolio_chg            |        15 |       0.899 |       0.522 |                   0.211 | 0.197 | False           |
| positions_liquidated_pct             |        15 |       0.899 |       0.541 |                   0.219 | 0.203 | True            |
| aum_outflow_pct_90d                  |        16 |       0.925 |       0.428 |                   0.131 | 0.287 | False           |
| aum_vs_baseline_pct                  |        16 |       0.903 |       0.402 |                   0.162 | 0.322 | True            |
| investment_redemption_pct            |        16 |       0.768 |       0.732 |                   0.865 | 0.218 | False           |
| return_vs_benchmark                  |        17 |       1.000 |       0.082 |                   0.000 | 0.080 | True            |
| fixed_income_maturity_not_reinvested |        18 |       1.000 |       0.045 |                   0.000 | 0.048 | True            |
| external_destination_concentration   |        19 |       1.000 |       0.061 |                   0.000 | 0.022 | True            |
| recurring_deposit_change_pct         |        20 |       1.000 |       0.077 |                   0.000 | 0.087 | True            |
| meetings_cancelled_by_client         |        21 |       1.000 |       0.007 |                   0.000 | 0.044 | True            |

### 10.3 Forward selection (orden LASSO)

| variable                       |   AUC CV |    Δ AUC | decisión                                        |
|:-------------------------------|---------:|---------:|:------------------------------------------------|
| aum_vs_baseline_pct            |   0.6285 |   0.1285 | ENTRA                                           |
| transfer_to_competitor_pct_90d |   0.6447 |   0.0162 | ENTRA                                           |
| banker_change_6m_flag          |   0.6737 |   0.0290 | ENTRA                                           |
| client_reply_rate              |   0.7008 |   0.0271 | ENTRA                                           |
| positions_liquidated_pct       |   0.7041 |   0.0033 | ENTRA                                           |
| contact_gap_ratio              | nan      | nan      | descartada: ya hay 2 de «Relación con banquero» |
| share_of_wallet                |   0.7105 |   0.0064 | ENTRA                                           |
| complaint_escalated_flag       |   0.7127 |   0.0022 | ENTRA                                           |
| meetings_cancelled_by_client   | nan      | nan      | descartada: ya hay 2 de «Relación con banquero» |
| return_vs_benchmark            |   0.7150 |   0.0023 | ENTRA                                           |

**Variables finales (8):** `aum_vs_baseline_pct` (Deterioro de AUM), `transfer_to_competitor_pct_90d` (Externalización), `banker_change_6m_flag` (Relación con banquero), `client_reply_rate` (Relación con banquero), `positions_liquidated_pct` (Salida de activos), `share_of_wallet` (Pérdida de productos), `complaint_escalated_flag` (Fricción de servicio), `return_vs_benchmark` (Fricción de servicio).
Dimensiones cubiertas: 6 de las 9 del prompt.

## 11. Estimación

**Tabla de decisión por eventos.** < 50 → híbrido experto calibrado · 50–300 → logística penalizada o Cox · > 300 → logística sobre WoE.
Con 2,213 eventos de desarrollo corresponde **logística sobre WoE** (Modelo A).
No se usa Cox: la base no tiene tiempo al evento continuo, y la curva de hazard mensual del paso 14 cubre la necesidad del playbook.

**Modelo A (campeón).** ln(odds buenos) = β₀ + Σ βⱼ·WoEⱼ.

|                                | dimensión             |   β (WoE) |   e.e. |       z |   p-valor |     IV |    VIF |
|:-------------------------------|:----------------------|----------:|-------:|--------:|----------:|-------:|-------:|
| aum_vs_baseline_pct            | Deterioro de AUM      |    0.3241 | 0.0605 |  5.3562 |    0.0000 | 0.3217 | 2.1295 |
| transfer_to_competitor_pct_90d | Externalización       |    0.3677 | 0.0572 |  6.4289 |    0.0000 | 0.2602 | 1.4689 |
| banker_change_6m_flag          | Relación con banquero |    0.6916 | 0.0521 | 13.2798 |    0.0000 | 0.2226 | 1.0961 |
| client_reply_rate              | Relación con banquero |    0.7084 | 0.0705 | 10.0454 |    0.0000 | 0.1350 | 1.0334 |
| positions_liquidated_pct       | Salida de activos     |    0.5207 | 0.0671 |  7.7576 |    0.0000 | 0.2032 | 1.6790 |
| share_of_wallet                | Pérdida de productos  |    0.4043 | 0.0699 |  5.7827 |    0.0000 | 0.1411 | 1.1407 |
| complaint_escalated_flag       | Fricción de servicio  |    0.4783 | 0.0948 |  5.0467 |    0.0000 | 0.0675 | 1.0474 |
| return_vs_benchmark            | Fricción de servicio  |    0.4801 | 0.0965 |  4.9750 |    0.0000 | 0.0796 | 1.1027 |

- **Todos los β > 0:** sí ✓. **VIF máx:** 2.13 (< 5 ✓).
- Corrección de intercepto por indeterminados: el desarrollo excluye 1603 indeterminados, que en la población son «no churn».
  - β₀ = β₀* − ln(odds muestra) + ln(odds población) = 1.4736 − ln(4.4352) + ln(5.1595) = **1.6249**.

**Modelo B (challenger): gradient boosting** (HistGradientBoosting, todas las candidatas permitidas, crudas).

|                                    |      N |   eventos |    AUC |   Gini |   PR-AUC |   PR-AUC base (tasa) |      KS |   captura AUM top 10% |
|:-----------------------------------|-------:|----------:|-------:|-------:|---------:|---------------------:|--------:|----------------------:|
| Dev · Modelo A (scorecard WoE)     | 12,028 |     2,213 | 0.7168 | 0.4336 |   0.4109 |               0.1840 | 32.2511 |                0.2511 |
| Val · Modelo A (scorecard WoE)     |  5,155 |       949 | 0.7106 | 0.4213 |   0.3854 |               0.1841 | 30.3655 |                0.2180 |
| Dev · Modelo B (gradient boosting) | 12,028 |     2,213 | 0.8179 | 0.6358 |   0.5647 |               0.1840 | 48.4348 |                0.3555 |
| Val · Modelo B (gradient boosting) |  5,155 |       949 | 0.7113 | 0.4226 |   0.3881 |               0.1841 | 30.5462 |                0.2113 |

- Diferencia de AUC en validación (B − A), IC 95% bootstrap pareado: [-0.0080, +0.0088] → **no significativa**.
- Calibración en validación (sin indeterminados): p media A = 0.1647, Brier 0.1355 · B = 0.1813, Brier 0.1348 · observado 0.1841.

| Criterio | Modelo A · scorecard | Modelo B · GBM |
|---|---|---|
| AUC / PR-AUC / KS val | 0.711 / 0.385 / 30.4 | 0.711 / 0.388 / 30.5 |
| Caída de Gini dev → val | 2.8% | 33.5% |
| Variables | 8 | 37 |
| Explicabilidad | Puntos por bin; reason codes exactos | Requiere SHAP; no hay puntos auditables |
| Monotonicidad garantizada | Sí (binning forzado) | No (salvo restricciones explícitas) |
| Implementación | Lookup table (SQL/CRM) | Servicio de scoring + versión del modelo |

**Decisión: Modelo A campeón.**
- La ventaja de B no es significativa, o es menor que el costo de explicabilidad.
- B queda como challenger en el monitoreo: si supera a A en OOT de forma significativa en dos ciclos, se documenta el costo de explicabilidad y se reevalúa.

## 12. Escalamiento, tramos y salida por cliente

**Fórmulas.**
- Factor = PDO / ln 2 = 40 / 0.6931 = **57.7078**.
- Offset = S₀ − Factor·ln(O₀) = 600 − 57.7078·ln 20 = **427.1229**.
- Score = Offset + Factor·ln(odds buenos).
- Puntos por bin = (βⱼ·WoEⱼ + β₀/n)·Factor + Offset/n, con n = 8.
- Mayor score = menor churn. **El score son puntos, no una probabilidad**: 600 puntos equivale a odds 20:1, es decir p ≈ 4.8% *antes* de calibrar.

### 12.1 Lookup table completa

| variable                       | dimensión             | bin                  |   N dev |   % pob |   tasa churn dev |     WoE |      β |   puntos |   puntos vs neutral |
|:-------------------------------|:----------------------|:---------------------|--------:|--------:|-----------------:|--------:|-------:|---------:|--------------------:|
| aum_vs_baseline_pct            | Deterioro de AUM      | [-inf, -0.2031)      |     680 |  5.6535 |           0.4691 | -1.3659 | 0.3241 |  39.5628 |            -25.5489 |
| aum_vs_baseline_pct            | Deterioro de AUM      | [-0.2031, -0.02156)  |   1,219 | 10.1347 |           0.1772 |  0.0459 | 0.3241 |  65.9704 |              0.8587 |
| aum_vs_baseline_pct            | Deterioro de AUM      | [-0.02156, inf)      |   8,571 | 71.2587 |           0.1364 |  0.3560 | 0.3241 |  71.7715 |              6.6597 |
| aum_vs_baseline_pct            | Deterioro de AUM      | Missing              |   1,558 | 12.9531 |           0.3267 | -0.7664 | 0.3241 |  50.7758 |            -14.3359 |
| transfer_to_competitor_pct_90d | Externalización       | [-inf, 0.006803)     |   5,838 | 48.5367 |           0.1518 |  0.2313 | 0.3677 |  70.0189 |              4.9072 |
| transfer_to_competitor_pct_90d | Externalización       | [0.006803, 0.01991)  |   4,395 | 36.5397 |           0.1663 |  0.1223 | 0.3677 |  67.7075 |              2.5958 |
| transfer_to_competitor_pct_90d | Externalización       | [0.01991, 0.08466)   |   1,164 |  9.6774 |           0.2079 | -0.1520 | 0.3677 |  61.8874 |             -3.2243 |
| transfer_to_competitor_pct_90d | Externalización       | [0.08466, inf)       |     631 |  5.2461 |           0.5610 | -1.7348 | 0.3677 |  28.3007 |            -36.8110 |
| banker_change_6m_flag          | Relación con banquero | [-inf, 0.5)          |  10,257 | 85.2760 |           0.1514 |  0.2340 | 0.6916 |  74.4520 |              9.3403 |
| banker_change_6m_flag          | Relación con banquero | [0.5, inf)           |   1,771 | 14.7240 |           0.3727 | -0.9688 | 0.6916 |  26.4469 |            -38.6648 |
| client_reply_rate              | Relación con banquero | [-inf, 0.3452)       |   1,230 | 10.2261 |           0.1951 | -0.0725 | 0.7084 |  62.1481 |             -2.9637 |
| client_reply_rate              | Relación con banquero | [0.3452, inf)        |   5,027 | 41.7941 |           0.1221 |  0.4828 | 0.7084 |  84.8465 |             19.7348 |
| client_reply_rate              | Relación con banquero | Missing              |   5,771 | 47.9797 |           0.2355 | -0.3120 | 0.7084 |  52.3579 |            -12.7538 |
| positions_liquidated_pct       | Salida de activos     | [-inf, 0.04725)      |   9,803 | 81.5015 |           0.1491 |  0.2518 | 0.5207 |  72.6783 |              7.5666 |
| positions_liquidated_pct       | Salida de activos     | [0.04725, inf)       |     667 |  5.5454 |           0.3628 | -0.9264 | 0.5207 |  37.2748 |            -27.8369 |
| positions_liquidated_pct       | Salida de activos     | Missing              |   1,558 | 12.9531 |           0.3267 | -0.7664 | 0.5207 |  42.0823 |            -23.0295 |
| share_of_wallet                | Pérdida de productos  | [-inf, 0.1966)       |   1,551 | 12.8949 |           0.3301 | -0.7819 | 0.4043 |  46.8683 |            -18.2435 |
| share_of_wallet                | Pérdida de productos  | [0.1966, 0.3378)     |   2,392 | 19.8869 |           0.1923 | -0.0545 | 0.4043 |  63.8406 |             -1.2711 |
| share_of_wallet                | Pérdida de productos  | [0.3378, 0.5294)     |   3,312 | 27.5357 |           0.1715 |  0.0855 | 0.4043 |  67.1064 |              1.9947 |
| share_of_wallet                | Pérdida de productos  | [0.5294, 0.7829)     |   2,990 | 24.8587 |           0.1512 |  0.2359 | 0.4043 |  70.6156 |              5.5039 |
| share_of_wallet                | Pérdida de productos  | [0.7829, inf)        |   1,783 | 14.8237 |           0.1239 |  0.4660 | 0.4043 |  75.9848 |             10.8731 |
| complaint_escalated_flag       | Fricción de servicio  | [-inf, 0.5)          |  11,390 | 94.6957 |           0.1736 |  0.0709 | 0.4783 |  67.0700 |              1.9583 |
| complaint_escalated_flag       | Fricción de servicio  | [0.5, inf)           |     638 |  5.3043 |           0.3699 | -0.9569 | 0.4783 |  38.6980 |            -26.4137 |
| return_vs_benchmark            | Fricción de servicio  | [-inf, -0.04175)     |   1,595 | 13.2607 |           0.2163 | -0.2022 | 0.4801 |  59.5092 |             -5.6026 |
| return_vs_benchmark            | Fricción de servicio  | [-0.04175, 0.004157) |   3,077 | 25.5820 |           0.1641 |  0.1383 | 0.4801 |  68.9441 |              3.8323 |
| return_vs_benchmark            | Fricción de servicio  | [0.004157, 0.04165)  |   1,867 | 15.5221 |           0.1328 |  0.3866 | 0.4801 |  75.8224 |             10.7107 |
| return_vs_benchmark            | Fricción de servicio  | [0.04165, inf)       |     790 |  6.5680 |           0.0987 |  0.7218 | 0.4801 |  85.1107 |             19.9990 |
| return_vs_benchmark            | Fricción de servicio  | Missing              |   4,699 | 39.0672 |           0.2207 | -0.2279 | 0.4801 |  58.7977 |             -6.3140 |

Chequeo: score de un hogar con WoE = 0 en todo = Offset + β₀·Factor = 427.12 + 1.6249·57.7078 = 520.89. Rango observado del score: 328 – 602; mediana 540.

### 12.2 Tramos (sobre probabilidad calibrada; cortes fijados en validación)

**Criterios, en orden:**
1. **Capacidad.** Crítico = 720 casos = 3.70% de la cartera, trabajable en 30 días.
2. **Salto ≥ 2×** entre tramos contiguos y **lift ≥ 5×** de Crítico vs. Estable.
3. **≥ 30 eventos por tramo.**
- Entre las particiones que cumplen, se elige la de mayor IV del tramo.
- Todas las condiciones se cumplen.
- Umbrales de p calibrada: Crítico ≥ 44.30% · Alto ≥ 18.13% · Vigilancia ≥ 8.58% · Estable < 8.58%.
- Cortes equivalentes en puntos: difieren por segmento por el δ de calibración UHNW (paso 14). A igual score, un UHNW tiene más probabilidad.

|                       |   HNW |   UHNW |
|:----------------------|------:|-------:|
| Crítico si score ≤    | 428.6 |  449.5 |
| Alto si score ≤       | 512.4 |  533.3 |
| Vigilancia si score ≤ | 568.7 |  589.5 |

### 12.3 Escala maestra · relaciones (validación, con overrides)

| tramo      | score HNW     | score UHNW    | p calibrada (incl. overrides)   |   % relaciones |   churn esperado (p media) |   churn observado |   captura |   lift |   eventos |     N |
|:-----------|:--------------|:--------------|:--------------------------------|---------------:|---------------------------:|------------------:|----------:|-------:|----------:|------:|
| Crítico    | ≤ 429         | ≤ 450         | 5.3% – 78.6%                    |         0.0454 |                     0.5020 |            0.5019 |    0.1401 | 3.0896 |       133 |   265 |
| Alto       | > 429 y ≤ 512 | > 450 y ≤ 533 | 6.6% – 44.3%                    |         0.2871 |                     0.2384 |            0.2391 |    0.4226 | 1.4720 |       401 | 1,677 |
| Vigilancia | > 512 y ≤ 569 | > 533 y ≤ 590 | 8.6% – 18.1%                    |         0.4868 |                     0.1232 |            0.1280 |    0.3836 | 0.7879 |       364 | 2,844 |
| Estable    | > 569         | > 590         | 5.3% – 8.6%                     |         0.1808 |                     0.0739 |            0.0483 |    0.0537 | 0.2973 |        51 | 1,056 |

Chequeos:
- % relaciones suma 1.0000; captura suma 1.0000.
- Churn de cartera = Σ share × tasa = 0.0454×0.5019 + 0.2871×0.2391 + 0.4868×0.1280 + 0.1808×0.0483 = 0.1624 = tasa observada 0.1624 ✓.
- Lift Crítico/Estable = 10.4×.
- Saltos entre tramos contiguos:
  - sin overrides: Crítico/Alto 2.06×, Alto/Vigilancia 2.01×, Vigilancia/Estable 2.76×;
  - con overrides: Crítico/Alto 2.10×, Alto/Vigilancia 1.87×, Vigilancia/Estable 2.65×.
- Los overrides llevan a Alto casos de precisión 12–25%, por debajo de la tasa de Alto, así que diluyen el salto Alto/Vigilancia. Es el costo de la regla de negocio; se revisa trimestralmente (paso 14, capa 4).

### 12.4 Escala maestra · AUM (validación)

| tramo      | score HNW     | score UHNW    | p calibrada (incl. overrides)   |   % AUM |   churn esperado (Σp·AUM ÷ AUM) |   churn observado (AUM de churners ÷ AUM) |   captura de AUM de churners |   lift |   eventos |     N |
|:-----------|:--------------|:--------------|:--------------------------------|--------:|--------------------------------:|------------------------------------------:|-----------------------------:|-------:|----------:|------:|
| Crítico    | ≤ 429         | ≤ 450         | 5.3% – 78.6%                    |  0.0490 |                          0.5165 |                                    0.4957 |                       0.1396 | 2.8497 |       133 |   265 |
| Alto       | > 429 y ≤ 512 | > 450 y ≤ 533 | 6.6% – 44.3%                    |  0.2504 |                          0.2324 |                                    0.2468 |                       0.3553 | 1.4189 |       401 | 1,677 |
| Vigilancia | > 512 y ≤ 569 | > 533 y ≤ 590 | 8.6% – 18.1%                    |  0.5368 |                          0.1234 |                                    0.1504 |                       0.4642 | 0.8647 |       364 | 2,844 |
| Estable    | > 569         | > 590         | 5.3% – 8.6%                     |  0.1638 |                          0.0761 |                                    0.0434 |                       0.0409 | 0.2496 |        51 | 1,056 |

Chequeos:
- % AUM suma 1.0000; captura de AUM de churners suma 1.0000.
- Churn por AUM = 0.0490×0.4957 + 0.2504×0.2468 + 0.5368×0.1504 + 0.1638×0.0434 = 0.1740 = 0.1740 ✓.
- Aquí churn por AUM = valor de las relaciones que churnean ÷ valor del tramo. La salida neta efectiva (flujo) está en el paso 14 por banda de AUM.

### 12.5 Matriz de gobernanza

|            | quién actúa                                                              | SLA de contacto              | escalamiento                                 |
|:-----------|:-------------------------------------------------------------------------|:-----------------------------|:---------------------------------------------|
| Crítico    | Banquero + Head of PB (visto bueno); comité si valor ≥ p95 de la cartera | ≤ 5 días hábiles             | Head of PB revisa semanal; comité mensual    |
| Alto       | Banquero                                                                 | ≤ 15 días hábiles            | Head of PB si no hay contacto en SLA         |
| Vigilancia | Banquero (cadencia reforzada)                                            | próximo contacto de cadencia | sube a Alto si sube 2 tramos en un trimestre |
| Estable    | Banquero (cadencia normal)                                               | —                            | —                                            |

Prioridad intra-tramo = p calibrada × valor de la relación (columna `rank_intra_tramo` de la salida).

### 12.6 Overrides a Crítico (precisión en validación sobre casos que el modelo no puso en Crítico)

Regla de permanencia: precisión ≥ 25% se queda en Crítico; 12–25% baja a Alto; < 12% se elimina. Tope: ningún override puede ser > 30% del tramo.

| override                                                            |   casos (val, fuera de Crítico) |   precisión | decisión por precisión   | decisión final (con tope 30%)               |
|:--------------------------------------------------------------------|--------------------------------:|------------:|:-------------------------|:--------------------------------------------|
| Cambio de trustee (proxy sucesión / fallecimiento)                  |                              49 |      0.3061 | se queda en Crítico      | se queda en Crítico                         |
| Cambio de banquero (6m; proxy de salida ≤ 90 días)                  |                             704 |      0.2528 | se queda en Crítico      | baja a Alto (no cabe en el tope de Crítico) |
| Transferencia externa ≥ 10% del saldo (60d; proxy de un movimiento) |                             207 |      0.2464 | baja a Alto              | baja a Alto                                 |
| Queja formal escalada                                               |                             260 |      0.2462 | baja a Alto              | baja a Alto                                 |
| Intención de salida / insatisfacción expresada                      |                              51 |      0.2157 | baja a Alto              | baja a Alto                                 |

% de cada tramo que entra por override: Crítico 18.5%, Alto 20.5%, Vigilancia 0.0%, Estable 0.0%.
Tope 30%: cumple ✓.
Con overrides, Crítico tiene 895 hogares en la cartera, frente a una capacidad de 720/mes: el exceso se ordena por prioridad p × valor y lo que no entra en el mes pasa al SLA del mes siguiente.
Sin datos en la base (se piden en modo REAL): liquidity event, fallecimiento del principal, salida del banquero con fecha exacta (≤ 90 días).

### 12.7 Escala maestra sin overrides (efecto de los overrides)

| tramo      |   % relaciones |   churn observado |   captura |   lift |   eventos |     N |
|:-----------|---------------:|------------------:|----------:|-------:|----------:|------:|
| Crítico    |         0.0370 |            0.5463 |    0.1243 | 3.3630 |       118 |   216 |
| Alto       |         0.2314 |            0.2648 |    0.3772 | 1.6301 |       358 | 1,352 |
| Vigilancia |         0.5486 |            0.1317 |    0.4447 | 0.8105 |       422 | 3,205 |
| Estable    |         0.1830 |            0.0477 |    0.0537 | 0.2937 |        51 | 1,069 |

### 12.8 Salida por cliente (ejemplos: los 5 de mayor prioridad en Crítico)

| household_id   | segment   |   relationship_value_t0 |   score |   p_cal | tramo   | override   | arquetipo                                        | driver_1                                      |   driver_1_pts | driver_2                                      |   driver_2_pts | driver_3                                |   driver_3_pts |
|:---------------|:----------|------------------------:|--------:|--------:|:--------|:-----------|:-------------------------------------------------|:----------------------------------------------|---------------:|:----------------------------------------------|---------------:|:----------------------------------------|---------------:|
| HH004766       | UHNW      |           272199276.120 | 366.825 |   0.737 | Crítico |            | Externalización / mudanza del banco principal    | banker_change_6m_flag [0.5, inf)              |        -38.665 | transfer_to_competitor_pct_90d [0.08466, inf) |        -36.811 | positions_liquidated_pct [0.04725, inf) |        -27.837 |
| HH003568       | UHNW      |           301501529.120 | 428.688 |   0.522 | Crítico |            | Externalización / mudanza del banco principal    | transfer_to_competitor_pct_90d [0.08466, inf) |        -36.811 | complaint_escalated_flag [0.5, inf)           |        -26.414 | aum_vs_baseline_pct [-inf, -0.2031)     |        -25.549 |
| HH004323       | UHNW      |           199996293.400 | 412.321 |   0.584 | Crítico |            | Externalización / mudanza del banco principal    | banker_change_6m_flag [0.5, inf)              |        -38.665 | transfer_to_competitor_pct_90d [0.08466, inf) |        -36.811 | aum_vs_baseline_pct [-inf, -0.2031)     |        -25.549 |
| HH013250       | UHNW      |           202066361.310 | 445.644 |   0.458 | Crítico |            | Erosión silenciosa de wallet / salida de activos | banker_change_6m_flag [0.5, inf)              |        -38.665 | positions_liquidated_pct Missing              |        -23.029 | aum_vs_baseline_pct Missing             |        -14.336 |
| HH017101       | UHNW      |           164771165.030 | 428.740 |   0.522 | Crítico |            | Externalización / mudanza del banco principal    | transfer_to_competitor_pct_90d [0.08466, inf) |        -36.811 | complaint_escalated_flag [0.5, inf)           |        -26.414 | aum_vs_baseline_pct [-inf, -0.2031)     |        -25.549 |

Reason codes: bins con mayor pérdida de puntos vs. neutral (WoE = 0), pérdida = −βⱼ·WoEⱼ·Factor. Nunca se entrega un score sin sus tres drivers.
Lectura de «Missing» para el banquero:
- `aum_vs_baseline_pct` / `positions_liquidated_pct`: sin portafolio de inversión.
- `client_reply_rate`: sin interacciones registradas.
- `return_vs_benchmark`: sin cuenta advisory.
- Frecuencia del driver #1 en la cartera: client_reply_rate 5,643, banker_change_6m_flag 2,877, positions_liquidated_pct 2,807, return_vs_benchmark 2,730,  2,265, share_of_wallet 1,525, transfer_to_competitor_pct_90d 763, complaint_escalated_flag 598, aum_vs_baseline_pct 265.
Archivo completo: `data/synthetic/scorecard_clients.csv`.

## 13. Validación

**Métricas de referencia (validación de modelo, sin indeterminados).** Ver la tabla del paso 11.
**Validación operativa (población completa de validación, indeterminados = no churn):** AUC 0.702, PR-AUC 0.339 (base 0.162), KS 28.9, Gini 0.403.

### 13.1 Gains y lift por decil (validación operativa, p calibrada)

|   decil |   N |   eventos |   p_media |   tasa churn |   lift |   captura eventos acum. |   captura AUM acum. |
|--------:|----:|----------:|----------:|-------------:|-------:|------------------------:|--------------------:|
|       1 | 585 |       243 |    0.4321 |       0.4154 | 2.5571 |                  0.2561 |              0.2376 |
|       2 | 584 |       153 |    0.2508 |       0.2620 | 1.6128 |                  0.4173 |              0.3396 |
|       3 | 584 |       112 |    0.1926 |       0.1918 | 1.1806 |                  0.5353 |              0.5528 |
|       4 | 584 |        94 |    0.1570 |       0.1610 | 0.9909 |                  0.6344 |              0.6347 |
|       5 | 584 |        85 |    0.1361 |       0.1455 | 0.8960 |                  0.7239 |              0.7404 |
|       6 | 584 |        84 |    0.1229 |       0.1438 | 0.8854 |                  0.8124 |              0.8374 |
|       7 | 584 |        61 |    0.1099 |       0.1045 | 0.6430 |                  0.8767 |              0.9062 |
|       8 | 584 |        53 |    0.0939 |       0.0908 | 0.5587 |                  0.9326 |              0.9512 |
|       9 | 584 |        45 |    0.0819 |       0.0771 | 0.4743 |                  0.9800 |              0.9836 |
|      10 | 585 |        19 |    0.0681 |       0.0325 | 0.1999 |                  1.0000 |              1.0000 |

### 13.2 Métricas decisivas

- **Captura de AUM de churners en el decil top:** 23.7% ordenando por p; 58.3% ordenando por prioridad p × valor.
- **Falsos positivos en Crítico + Alto:** 1,408 alertas sin churn frente a 534 con churn: 2.64 alertas falsas por cada churner detectado.
  - Horas de banquero senior = FP × H, con H (horas por alerta) = **parámetro abierto**. Con la muestra de validación escalada a la cartera: ≈ 4,693 alertas falsas × H.

### 13.3 Criterios de aprobación

| Criterio | Umbral | Resultado | Estado |
|---|---|---|---|
| KS validación | ≥ 30 | 30.4 | PASA |
| PR-AUC > tasa base | > 0.184 | 0.385 | PASA |
| Caída de Gini dev → val | ≤ 15% relativo | 2.8% | PASA |
| Monotonicidad de tasa por tramo (dev y val) | estrictamente decreciente | sí | PASA |
| Monotonicidad por bin, variables finales (dev y val) | todas | 8/8 | PASA |
| PSI por tramo dev → val | < 0.10 | 0.0004 | PASA |
| OOT (cohorte más reciente) | caída de Gini ≤ 15% | no disponible (un corte) | **PENDIENTE** |

| tr         |   desarrollo |   validación |
|:-----------|-------------:|-------------:|
| Crítico    |       0.6461 |       0.6051 |
| Alto       |       0.3164 |       0.3110 |
| Vigilancia |       0.1356 |       0.1481 |
| Estable    |       0.0700 |       0.0531 |

**Dictamen:** aprobado para piloto en la base sintética; **la aprobación productiva queda condicionada al OOT** con datos del banco.

## 14. Calibración (cuatro capas)

**Capa 1 · Modelo.** Platt: logit(p_cal) = a + b·logit(p) sobre la validación operativa (incluye indeterminados).
- a = -0.2061, b = 0.8806 → b dentro de [0.8, 1.2].
- Cross-fit en mitades: (a, b) = (-0.125, 0.933) y (-0.286, 0.829).
- Brier: sin calibrar 0.1250, Platt (cross-fit) 0.1247, Isotónica (mitad → mitad) 0.1244.
- Isotónica: la validación tiene 949 eventos, suficiente, pero no mejora el Brier de forma material y rompe la suavidad → se queda Platt.
- **Tendencia central:** p calibrada media en la cartera = 0.1643 vs. churn observado de la cartera = 0.1624. Con un solo corte, la «tasa de largo plazo» es la del corte; en modo REAL es la media de las cohortes apiladas.

|   decil (1 = menor riesgo) |   p media sin calibrar |   p media calibrada |   churn observado |
|---------------------------:|-----------------------:|--------------------:|------------------:|
|                          1 |                 0.0599 |              0.0681 |            0.0359 |
|                          2 |                 0.0736 |              0.0819 |            0.0719 |
|                          3 |                 0.0855 |              0.0939 |            0.0925 |
|                          4 |                 0.1026 |              0.1099 |            0.1045 |
|                          5 |                 0.1181 |              0.1229 |            0.1455 |
|                          6 |                 0.1326 |              0.1361 |            0.1404 |
|                          7 |                 0.1544 |              0.1570 |            0.1627 |
|                          8 |                 0.1956 |              0.1926 |            0.1935 |
|                          9 |                 0.2655 |              0.2508 |            0.2620 |
|                         10 |                 0.4723 |              0.4321 |            0.4154 |

**Capa 1b · Segmento.** El tamaño no está en el score.
- Si la tasa observada de un segmento cae fuera del IC Wilson 90% de su esperado, se aplica un desplazamiento de intercepto δ propio del segmento: logit(p_cal) = a + b·logit(p) + δ_segmento.
- Se estima sobre toda la cartera, porque la validación sola tiene pocos eventos UHNW.

| segmento   |      N |   eventos |   esperado (Platt) |   observado |   Wilson 90% inf |   Wilson 90% sup | ¿dentro?   |   δ intercepto |   esperado tras δ |
|:-----------|-------:|----------:|-------------------:|------------:|-----------------:|-----------------:|:-----------|---------------:|------------------:|
| HNW        | 18,390 |     2,973 |             0.1637 |      0.1617 |           0.1572 |           0.1662 | sí         |         0.0000 |            0.1637 |
| UHNW       |  1,083 |       189 |             0.1368 |      0.1745 |           0.1564 |           0.1943 | NO         |         0.3186 |            0.1745 |

Lectura: el generador tiene un efecto UHNW de +0.10 en el índice de riesgo (paso 2). El score no lo captura porque el tamaño se excluyó a propósito, así que **la capa de calibración lo recupera** (δ UHNW = +0.319). Los tramos se cortan sobre esta p calibrada final.

**Capa 2 · Tramo.** Esperado vs. observado con IC de Wilson 90%; shrinkage beta-binomial p = (eventos + m·p_modelo)/(N + m), m = 30.

| tramo      |     N |   eventos |   esperado (p media) |   observado |   Wilson 90% inf |   Wilson 90% sup | ¿esperado dentro del IC?   |   p shrinkage (m = 30) |
|:-----------|------:|----------:|---------------------:|------------:|-----------------:|-----------------:|:---------------------------|-----------------------:|
| Crítico    |   265 |       133 |               0.5020 |      0.5019 |           0.4516 |           0.5521 | sí                         |                 0.5019 |
| Alto       | 1,677 |       401 |               0.2384 |      0.2391 |           0.2224 |           0.2567 | sí                         |                 0.2391 |
| Vigilancia | 2,844 |       364 |               0.1232 |      0.1280 |           0.1180 |           0.1386 | sí                         |                 0.1279 |
| Estable    | 1,056 |        51 |               0.0739 |      0.0483 |           0.0386 |           0.0603 | NO                         |                 0.0490 |

Tramos fuera del IC: Estable. En la cola baja, Platt con b < 1 sobreestima el riesgo del tramo Estable, un error conservador. Para reportar se usa la p con shrinkage; los cortes no se tocan en el año 1.

**Capa 3 · Cortes.**
- Fijos el año 1.
- Se recortan una vez al año si dos cohortes consecutivas caen fuera del IC.
- Nunca se recalibran modelo y cortes en el mismo ciclo.
**Capa 4 · Overrides.** Precisión por regla (paso 12.6), se re-mide cada trimestre.

**Intervención vs. predicción.**
- El playbook bajará el churn observado en Crítico; eso no es descalibración.
- La calibración se mide sobre cohortes previas al lanzamiento.
- La retención se mide por uplift, con un control aleatorio del 10–15% **solo en Alto**. En Crítico no hay control por razones éticas y comerciales.

**Calibración parcial (hazard mensual del evento).** p(≤ h meses) ≈ p₆·H(h).

|   mes |   eventos |   % acumulado del churn a 6m |
|------:|----------:|-----------------------------:|
|     1 |       693 |                       0.2192 |
|     2 |       721 |                       0.4472 |
|     3 |       763 |                       0.6885 |
|     4 |       322 |                       0.7903 |
|     5 |       313 |                       0.8893 |
|     6 |       350 |                       1.0000 |

**Por segmento y por AUM.** Σ pᵢ·AUMᵢ esperado vs. AUM de los churners observados.

| segment   |     N |   eventos |   p media |   churn obs. |   Σ p·AUM ($M) |   AUM de churners obs. ($M) |   ratio obs./esperado (AUM) |
|:----------|------:|----------:|----------:|-------------:|---------------:|----------------------------:|----------------------------:|
| HNW       | 5,517 |       892 |    0.1638 |       0.1617 |      5823.6860 |                   5769.3614 |                      0.9907 |
| UHNW      |   325 |        57 |    0.1771 |       0.1754 |      4385.1870 |                   5178.6040 |                      1.1809 |

| banda AUM   |     N |   eventos |   p media |   churn obs. |   Σ p·AUM ($M) |   AUM de churners obs. ($M) |   outflow neto obs. ($M) |   ratio obs./esperado (AUM) |
|:------------|------:|----------:|----------:|-------------:|---------------:|----------------------------:|-------------------------:|----------------------------:|
| $1–5M       | 2,993 |       504 |    0.1716 |       0.1684 |      1364.1243 |                   1337.8740 |                 840.5478 |                      0.9808 |
| $5–10M      | 1,310 |       203 |    0.1574 |       0.1550 |      1463.8212 |                   1440.3335 |                 903.7768 |                      0.9840 |
| $10–30M     | 1,214 |       185 |    0.1517 |       0.1524 |      2995.7404 |                   2991.1539 |                1888.3565 |                      0.9985 |
| $30–100M    |   273 |        45 |    0.1808 |       0.1648 |      2470.1232 |                   2247.5897 |                1618.5586 |                      0.9099 |
| > $100M     |    52 |        12 |    0.1580 |       0.2308 |      1915.0638 |                   2931.0143 |                1678.6187 |                      1.5305 |

Si la razón observado/esperado se aleja sistemáticamente de 1 en las bandas altas, se agrega la interacción tramo × banda de AUM en la calibración (no en el score).
En las bandas > $30M hay pocos eventos: la razón es volátil, e ± 1 hogar grande la mueve.

## 15. Estabilidad

**Criterio PSI.** < 0.10 estable · 0.10–0.25 vigilar · > 0.25 inestable.
- Por mes, trimestre y cohorte: **no medible** (un corte).
- Se mide dev → val (muestreo) y HNW → UHNW (poblaciones distintas).
- **PSI del score (deciles de dev) dev → val:** 0.0034.

|                                |   PSI dev→val |   PSI HNW→UHNW |
|:-------------------------------|--------------:|---------------:|
| aum_vs_baseline_pct            |        0.0042 |         0.1499 |
| transfer_to_competitor_pct_90d |        0.0003 |         0.0033 |
| banker_change_6m_flag          |        0.0002 |         0.0001 |
| client_reply_rate              |        0.0000 |         0.6377 |
| positions_liquidated_pct       |        0.0039 |         0.1468 |
| share_of_wallet                |        0.0014 |         0.0014 |
| complaint_escalated_flag       |        0.0001 |         0.0029 |
| return_vs_benchmark            |        0.0007 |         0.0176 |

El PSI HNW → UHNW **no es un fallo**: mide qué tan distinta es la población UHNW. Si es > 0.25, la calibración por segmento del paso 14 es obligatoria.

**Por segmento (validación operativa)**

| segment   |     N |   p media |   churn obs. |    AUC |   % en Crítico+Alto |
|:----------|------:|----------:|-------------:|-------:|--------------------:|
| HNW       | 5,517 |    0.1638 |       0.1617 | 0.7020 |              0.3317 |
| UHNW      |   325 |    0.1771 |       0.1754 | 0.6904 |              0.3446 |

**Por segmento estructural (validación operativa)**

| segmento_estructural          |     N |   p media |   churn obs. |    AUC |   % en Crítico+Alto |
|:------------------------------|------:|----------:|-------------:|-------:|--------------------:|
| Depositante (sin inversiones) |   862 |    0.2691 |       0.2691 | 0.5789 |              0.7854 |
| Inversionista patrimonial     | 4,980 |    0.1465 |       0.1440 | 0.6958 |              0.2540 |

**Por banda de AUM (validación operativa)**

| banda AUM   |     N |   p media |   churn obs. |    AUC |   % en Crítico+Alto |
|:------------|------:|----------:|-------------:|-------:|--------------------:|
| $1–5M       | 2,993 |    0.1716 |       0.1684 | 0.7041 |              0.3618 |
| $5–10M      | 1,310 |    0.1574 |       0.1550 | 0.7007 |              0.3115 |
| $10–30M     | 1,214 |    0.1517 |       0.1524 | 0.6942 |              0.2792 |
| $30–100M    |   273 |    0.1808 |       0.1648 | 0.6738 |              0.3626 |
| > $100M     |    52 |    0.1580 |       0.2308 | 0.8042 |              0.2500 |

**Por antigüedad (años) (validación operativa)**

| banda antigüedad   |     N |   p media |   churn obs. |    AUC |   % en Crítico+Alto |
|:-------------------|------:|----------:|-------------:|-------:|--------------------:|
| 1–3                |   711 |    0.1705 |       0.2039 | 0.6762 |              0.3418 |
| 3–7                | 1,897 |    0.1612 |       0.1508 | 0.6912 |              0.3210 |
| 7–15               | 2,371 |    0.1673 |       0.1653 | 0.7151 |              0.3429 |
| > 15               |   863 |    0.1595 |       0.1460 | 0.7097 |              0.3210 |

**Hallazgo · hogares sin inversiones.**
- Discriminación baja: AUC 0.58.
- Concentran alertas: 79% de ellos queda en Crítico+Alto.
- Por qué:
  - su churn observado es alto porque el target económico se dispara con la volatilidad del saldo de depósitos (compras, impuestos), no solo con fuga;
  - tres de las ocho variables quedan en «Missing» por no tener portafolio.
- **No es un defecto de estabilidad sino de definición del target para este segmento.**
- En modo REAL: medir la salida económica de depositantes con transferencias salientes netas (no con caída de saldo) y reevaluar un scorecard propio.

## 16. Acción, arquetipos y EWS

**Arquetipos.**
- K-means solo sobre churners de desarrollo, usando su perfil de riesgo previo a T0 (−WoE de 13 señales, estandarizado).
- K entre 3 y 5 por silhouette, con tamaño mínimo 10% y ARI ≥ 0.80.
- Describen *cómo se ven* los churners antes de irse; **no son causas**.

|   K |      WCSS |   silhouette |   estabilidad (ARI medio) |   tamaño mín % |
|----:|----------:|-------------:|--------------------------:|---------------:|
|   3 | 20161.900 |        0.169 |                     0.859 |         17.216 |
|   4 | 18631.794 |        0.154 |                     0.988 |         17.036 |
|   5 | 17791.031 |        0.150 |                     0.770 |         10.935 |

**K = 3.**

|                                                  |   churners dev |   % de churners |   valor mediano ($M) |   % económico (vs hard) | señales dominantes (centroide, d.e.)                                                                                             |
|:-------------------------------------------------|---------------:|----------------:|---------------------:|------------------------:|:---------------------------------------------------------------------------------------------------------------------------------|
| Erosión silenciosa de wallet / salida de activos |            574 |           0.259 |                3.315 |                   0.793 | positions_liquidated_pct (+1.2 d.e.), aum_vs_baseline_pct (+0.7 d.e.), return_vs_benchmark (+0.6 d.e.)                           |
| Externalización / mudanza del banco principal    |            381 |           0.172 |                4.956 |                   0.425 | transfer_to_competitor_pct_90d (+2.0 d.e.), external_transfer_pct_of_balance_60d (+1.9 d.e.), share_of_wallet_change (+1.4 d.e.) |
| Salida sin señal previa (no anticipable)         |          1,258 |           0.568 |                5.280 |                   0.620 | salary_deposit_stopped_flag (+0.0 d.e.), relationship_dissatisfaction_flag (-0.0 d.e.), trustee_change_flag (-0.1 d.e.)          |

- «Sin señal previa»: churners por debajo del churner promedio en todas las dimensiones. Es la parte del churn que ningún modelo con estas variables anticipa, y explica el techo de AUC.
- Las señales de servicio y banquero no forman un cluster propio: aparecen mezcladas con la externalización (centroide con banquero +0.8 d.e.).
- Los arquetipos se asignan a toda la cartera por centroide más cercano (columna `arquetipo`), para elegir la acción, no para puntuar.

### 16.1 Playbook = tramo × arquetipo (el score predice; no decide la acción)

| Arquetipo | Crítico (≤ 5 días hábiles) | Alto (≤ 15 días hábiles) | Vigilancia | Responsable |
|---|---|---|---|---|
| Erosión silenciosa de wallet / salida de activos | Reunión de revisión patrimonial: portafolio vs. objetivos, propuesta de consolidación | Llamada con revisión de desempeño y vencimientos | Alerta de vencimientos no reinvertidos | Banquero + especialista de inversiones |
| Externalización / mudanza del banco principal | Visita del banquero senior; mapear a dónde van los flujos y por qué | Contacto sobre nómina y flujos recurrentes | Monitoreo de transferencias | Banquero + Head of PB |
| Salida por servicio | Resolución de la queja con el Head of PB, compromiso de SLA | Seguimiento de caso y encuesta | Cierre de casos abiertos | Servicio + Head of PB |
| Salida con el banquero / desatención | Presentación del nuevo banquero con el Head of PB; plan de cadencia | Recuperar la cadencia; welcome call | Cadencia | Head of PB |
| Evento de vida / sucesión | Planeación sucesoria / Legacy con la next-gen | Contacto con trustee / familia | — | Banquero + Legacy |
| Salida sin señal previa | No debería llegar a Crítico por score; si llega por override, contacto de diagnóstico | Revisión de relación en la próxima cadencia | Cadencia | Banquero |

Filas sin arquetipo estadístico en esta base (servicio, banquero, evento de vida) se conservan en el playbook: las señales existen como drivers y overrides aunque no formen un cluster propio.

Cadencia: Crítico semanal hasta volver a Vigilancia; Alto quincenal; Vigilancia según la cadencia del segmento (UHNW 30 días, HNW 90).

### 16.2 EWS

- **Disparadores:** entrada a Crítico/Alto; override activado; subida de dos tramos en un trimestre; `multi_signal_count` ≥ 3 (regla de alerta, no predictor).
- **Integración CRM:** tarea con score, p calibrada, tramo, arquetipo, top 3 drivers y SLA; se cierra solo con el resultado del contacto registrado.
- **Matriz de migración mensual** (tramo t−1 × tramo t) y **KPI de regreso Crítico → Vigilancia** tras la intervención: requieren el panel mensual; en esta base (un corte) no son medibles.
- **Distribución actual de la cartera por tramo:** Crítico 4.6%, Alto 28.9%, Vigilancia 48.7%, Estable 17.8% (= 895, 5629, 9479, 3470 hogares).

## 17. KPIs, monitoreo, gobernanza y limitaciones

| KPI | Definición | Frecuencia | Umbral de acción |
|---|---|---|---|
| Churn rate por AUM (neto de mercado) | Σ flujo neto de salida de churners ÷ AUM inicial | Mensual (rolling 6m) | Tendencia al alza 2 trimestres |
| NNM retenido en alertados | NNM de Crítico+Alto tratados vs. control (solo Alto) | Trimestral | Uplift ≤ 0 dos trimestres |
| Precisión de alertas | churn observado en Crítico / Alto | Trimestral | Fuera del IC Wilson 90% |
| Tiempo alerta → contacto | días hábiles | Semanal | > SLA en > 10% de casos |
| PSI score y variables | vs. desarrollo | Mensual | > 0.10 vigilar; > 0.25 acción |
| Calibración por tramo | esperado vs. observado | Trimestral | 2 ciclos fuera de rango |

**Disparadores.**
- **Recalibración:** b de Platt fuera de [0.8, 1.2] durante dos ciclos.
- **Redesarrollo:** PSI > 0.25 sostenido o caída de Gini ≥ 15% relativo.
- **Challenger:** el GBM supera al scorecard de forma significativa en OOT en dos ciclos.
**Documento de modelo.** Este reporte cubre target, fuentes, ventanas, exclusiones, variables, transformaciones, binning, diagnóstico de estructura, segmentación, WoE/IV, campeón y challenger, escalamiento, calibración, validación, estabilidad y monitoreo. Código: `synthetic/scorecard.py`, `scripts/build_scorecard.py`.

### Limitaciones

- **Causalidad:** el modelo ordena por riesgo; no dice por qué se va nadie ni qué acción funciona (eso lo mide el uplift).
- **Datos sintéticos:** el mecanismo es mayormente aditivo y conocido; en datos reales habrá interacciones, errores de captura y cambios de definición que aquí no existen.
- **Un solo corte:** sin OOT, sin PSI temporal, sin matriz de migración, sin estacionalidad; cohortes apiladas no disponibles.
- **Horizonte de 6 m**, no 12 m; la curva de hazard solo cubre (0, 6].
- **Eventos no observados:** liquidity events, fallecimientos, divorcios, next-gen sin relación, digital: ausentes o con proxies.
- **Cambios de régimen:** mercado, tasas y competencia cambian la relación señal–churn; el umbral ex-mercado depende de un índice de retorno bien medido.
- **Efecto de la propia intervención:** una vez en producción, el churn observado en Crítico deja de medir la calidad predictiva.
- **Cola UHNW:** pocos eventos en > $30M; la captura de AUM depende de unos pocos hogares. El tamaño se corrige en calibración (δ UHNW), no en el score.
- **Depositantes sin inversiones:** baja discriminación y exceso de alertas (paso 15); el target económico es ruidoso para ellos.
- **Churn sin señal previa:** más de la mitad de los churners de desarrollo no muestra señal distintiva antes de T0 (paso 16).

## Cierre

### (a) Qué cambiaría en modo REAL

- Panel mensual con cohortes apiladas (≥ 3 años) → OOT real, PSI temporal, matriz de migración, cortes estables.
- Ventana de desempeño de 12 m y flujo neto medido con transacciones (no inferido del índice de retorno).
- Exclusiones con motivo (SPV, fraude, empleados, fallecidos, salida formal) y fecha del evento para Cox / curva de hazard real.
- Bloque digital y eventos de vida; `banker_id` para capacidad real por banquero.
- Validación independiente del binning y de los overrides sobre al menos dos cohortes.

### (b) Preguntas abiertas para el equipo de datos

1. ¿Existe un panel mensual de saldos y flujos por hogar, con al menos 36 meses?
2. ¿Cómo se consolida el hogar (trusts, LLC, negocio vinculado) y con qué frecuencia cambia?
3. ¿Hay flujo neto de inversión (aportes / retiros / ACATS) separado de la valuación?
4. ¿Qué marcas existen para fallecimiento, fraude, empleados, SPV y proceso formal de salida?
5. ¿Hay `banker_id` con historial de asignación y fecha de salida del banquero?
6. ¿Qué datos digitales hay (logins, sesiones, uso del Assistant) y desde cuándo?
7. ¿Hay dictamen legal para usar buró (FCRA) en revisión de cuenta?
8. ¿Cuántas horas de banquero senior cuesta una alerta (parámetro H)?

### (c) Limitaciones

Ver la sección «Limitaciones» del paso 17.

