# Decision log

Memoria del proyecto. Nada se decide fuera de este archivo. Etiquetas: `[DATA]` del archivo · `[DEF]` fijado por el
usuario · `[DEF-default]` default aplicado.

## Estado
- Último paso completado: **0** · Gate vigente: **G0 abierto — esperando respuesta del usuario**.
- Tests: 16 / 16 PASS (`tests/test_step00.py`).

## Parámetros vigentes
| Parámetro | Valor | Etiqueta |
|:--|:--|:--|
| Escala | S₀ = 600 @ O₀ = 20:1 (buenos:malos), PDO = 40 ⟹ Factor 57.71, Offset 427.12 | [DEF] (confirmar I-6) |
| SEED | 42 | [DEF] |
| Target | pendiente (propuesta B, θ = 0.25; A sensibilidad) | pendiente I-1 |
| Capacidad | pendiente | pendiente I-2 |

## Decisiones
- **D0.0 · Ubicación.** El proyecto vive en `churn_scorecard/` dentro del repo Citizens-bank, separado del generador
  sintético (`synthetic/`, `scripts/`) y del Modelo 1 previo (`scorecard/`). Paso 0 del SPEC.
- **D0.1 · Bootstrap del archivo fuente.** `data/raw/client_pulse_synthetic.xlsx` no existía. Se creó una sola vez con
  `src/bootstrap_raw.py` a partir de `../data/synthetic/client_pulse_synthetic.csv` (sha256 `44a1d18b…`), hoja
  `client_pulse_synthetic`, con verificación de que la relectura es idéntica al CSV. Archivo en solo lectura desde ahí.
- **D0.2 · Discrepancia con la ficha: RV vs AUM + depósitos.** La ficha dice "RV ≠ AUM + depósitos: RV es una medida
  propia". En el archivo RV = AUM (0 si no hay inversiones) + depósitos con |dif| máx. $0.01 [DATA]; solo difiere por
  redondeo de flotantes. El test verifica ambas cosas (desigualdad literal y la identidad al centavo). Implicación:
  `relationship_value` y `aum` son casi colineales (Spearman 0.97 [DATA]); RV no aporta información distinta a la suma.
  Pregunta al usuario (G0-a).
- **D0.3 · ρ de compuestos.** El 0.59 de la ficha es Pearson entre `multi_signal_count` y la suma de las 10 señales
  binarias visibles (9 `*_flag` + `bureau_new_mortgage_elsewhere`) = 0.59 [DATA]; con Spearman o solo los 9 flags da
  0.46–0.56 [DATA]. Se documenta la definición.
- **D0.4 · Base de la ficha.** Las cifras de tamaño, missing estructural (2,847), historia (1,417) y top 5% / 1% de la
  ficha están calculadas sobre los 19,877 elegibles. Con esa base coinciden todas [DATA].
- **D0.5 · Cribado anti-fuga.** Ninguna señal individual supera AUC 0.70 [DATA]. `multi_signal_count` tiene IV A =
  0.547 > 0.50 [DATA] → marcado "sospechoso" por la regla del SPEC; es un compuesto de señales pre-T0 sin regla
  documentada (I-3), ya excluido del campeón por D.12. Control: `value_lost_6m` tendría AUC vs A = 1.000 [DATA].
- **D0.6 · Test RV.** La tolerancia "al centavo" se expresa como diferencia redondeada a 6 decimales ≤ $0.01 (la
  diferencia máxima es 0.0100001097 por ruido de flotante en magnitudes de 10⁸–10⁹); el umbral no se relajó.

## Limitaciones registradas
- **L1** Sin OOT ni cohortes ni PSI temporal (un solo snapshot 2025-12-31) [DATA].
- **L2** Señales pre-ingenierizadas sin timestamps auditables; se asume as-of T0.
- **L4** Dataset sintético: nada se presenta como resultado de un banco real.

## Preguntas abiertas (G0)
- I-1 a I-10 del SPEC §I y G0-a (D0.2). Ver `reports/gate_0.md`.
