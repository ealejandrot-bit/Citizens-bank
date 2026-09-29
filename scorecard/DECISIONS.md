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
