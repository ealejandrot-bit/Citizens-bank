# Registro de decisiones

Formato: fecha · paso · decisión · alternativas descartadas · motivo.

## 2026-09-29 · Paso 0

**D0.1 · Fuente de datos en CSV, no XLSX.** El brief indica `./data/client_pulse_synthetic.xlsx`; ese archivo no
existe. La base está en `data/synthetic/client_pulse_synthetic.csv` (salida del generador del repo) y cumple los
35 hechos de la sección DATOS. Se lee en solo lectura; la ruta es configurable con `DATA_PATH`.
- Descartado: convertir a XLSX (duplica la fuente y abre la puerta a divergencias).

**D0.2 · Proyecto en `scorecard/`.** El repo ya contiene el generador sintético (`synthetic/`, `scripts/`, `docs/`,
`requirements.txt`). El scorecard vive en su propia carpeta con su `requirements.txt` congelado para no mezclar
dependencias; los modelos 2 (ML) y 3 (redes) seguirán el mismo patrón.
- Descartado: estructura en la raíz (colisiona con `README.md`, `requirements.txt` y `data/` existentes).

**D0.3 · Condición de missing del bloque 40–74%.** Verificada por crosstab contra los `has_*`:
- `salary_deposit_stopped_flag` ⇐ `has_payroll_stream` = False (0 violaciones; 232 NaN extra con nómina = patrón no detectado).
- `return_vs_benchmark` ⇐ `has_advisory` = False (0 violaciones; 251 NaN extra con advisory).
- `client_reply_rate`, `meetings_cancelled_by_client`, `relationship_dissatisfaction_flag`,
  `fixed_income_maturity_not_reinvested`: ningún `has_*` explica el missing (concordancia máx. 52–61%). La condición
  es operativa y **no observable en la base** (< 3 contactos, campo no registrado por el banker, fuera del piloto
  del Assistant, sin vencimientos), según el diccionario del generador (`synthetic/schema.py`). Se tratarán como
  bin "sin dato" propio, no como "no aplica".

**D0.4 · WARN `pension_deposit_stopped_flag`.** 134 hogares con `has_pension_stream` = False tienen valor (siempre 0)
en vez de NaN; 124 de ellos tienen `history_months` = 24. Interpretación: el detector de patrones marcó una
pensión que el flag de estructura no reconoce. Impacto nulo en señal (todos 0 = "no se detuvo"). Propuesta: en el
paso 3 recodificar a "no aplica" cuando `has_pension_stream` = False, documentado. No se detiene el pipeline:
el hecho del brief se cumple en 99.3% de los casos y la dirección de la excepción es benigna.

**D0.5 · Parámetros confirmados por el usuario (2026-09-29).** Target primario `hard_churn_6m`; capacidad Crítico =
top 3% (default, sin dato de banqueros). Instrucción: base sintética → documentar inconsistencias y seguir con los
datos tal cual; **no mover la concentración de valor** (hay hogares que concentran mucho más capital).

## 2026-09-29 · Paso 1

**D1.1 · Dos medidas de churn por valor.** (i) Σ RV de hogares con evento ÷ Σ RV (valor en riesgo) y (ii) Σ
`value_lost_6m` ÷ Σ RV (valor efectivamente perdido). En hard churn coinciden (pérdida total: `value_lost_6m` =
RV en el 100% de los eventos); en soft churn (ii) ≈ 40% de (i) (pérdida mediana 39.8% del RV).
- Descartado: `aum` como base de valor (missing estructural en 14.4%, sesga contra hogares solo depósitos).

**D1.2 · Intervalos bootstrap sin tocar el estimador.** 500 réplicas de hogares estratificadas por segmento; IC 95%
percentil. El estimador puntual usa RV crudo; el IC solo muestra la dependencia de pocos hogares grandes (un solo
hogar hard = 4.96% del valor perdido).
- Descartado: winsorizar o recortar RV para estabilizar la tasa (cambia la concentración; instrucción D0.5).

**D1.3 · Excluidos.** Los 123 `churn_excluded` (muerte / reubicación; 0.66% del RV) salen de entrenamiento y
métricas y se conservan en el archivo de scoring con bandera. Sin censura ni tiempo al evento: corte único, cada
hogar tiene ventana completa de 6m (hard) y 3m (soft) desde T0.

## 2026-09-29 · Paso 2

**D2.1 · Dirección esperada "?" en nivel patrimonial, `segment`, `age_primary` e `history_months`.** No hay
hipótesis de negocio defendible del signo; se deja a los datos (el binning monótono `auto_asc_desc` elige).
**D2.2 · Elegibles con revisión regulatoria:** `age_primary` (fair lending / UDAAP) y `bureau_new_mortgage_elsewhere`
(FCRA, propósito permisible). Se decide en el paso 10.

## 2026-09-29 · Paso 3

**D3.1 · Sin capping en ninguna variable.** El brief permitía capping p1/p99 para estabilidad de bins; no se usa:
(a) instrucción D0.5 para `relationship_value`; (b) `optbinning` pre-bina por cuantiles, invariante a transformaciones
monótonas de las colas, así que el capping no cambia los bins. Los 2 hogares "extraordinarios" (RV > $712M, 0.8% del
RV) son consistentes (identidad y segmento cuadran) y se conservan.
- Descartado: winsorizar p1/p99; eliminar outliers; log-transformar para el modelo (irrelevante con WoE).

**D3.2 · Taxonomía de missing para el binning.** "No aplica" (estructural, ligado a `has_*`) ≠ "sin dato" (historia
corta, condición operativa, patrón no detectado, saldo base < $10k). Cada uno tendrá bin propio cuando haya volumen.

**D3.3 · Inconsistencias documentadas, sin corregir la fuente** (tratamiento en la construcción de features, paso 5):
- `pension_deposit_stopped_flag` con valor 0 en 134 hogares sin `has_pension_stream` → se recodifica a "no aplica".
- `salary_deposit_stopped_flag` NaN en 232 hogares con nómina (patrón no detectado) → "sin dato", no "no aplica".
  Análogo en `business_payroll_stopped_flag` (64) y `recurring_deposit_*` (~150).
- `history_months` ≠ min(24, ⌊tenure·12⌋) en 61 hogares, todos por ±1 mes (redondeo) → se ignora.
- `history_months` = 0 en 5 hogares (recién abiertos) → se conservan; sus señales de ventana son "sin dato".
- `salary_deposit_stopped_flag` = 1 con `recurring_deposit_stopped_flag` = 0 en 11 hogares → coherente con el umbral
  de #4 (flujo ≥ 10% del ingreso); se conserva.
- `contact_gap_ratio` = −0.0 en 561 hogares → cosmético, equivale a 0.
- Ratios > 100% del saldo (p. ej. 628 hogares con transferencias 60d > 100% del saldo promedio) → plausibles
  (el denominador es un promedio y puede haber entradas); se conservan, el binning los absorbe en el bin extremo.
