# Decision log

Memoria del proyecto. Nada se decide fuera de este archivo. Etiquetas: `[DATA]` del archivo · `[DEF]` fijado por el
usuario · `[DEF-default]` default aplicado.

## Estado
- Último paso completado: **4** · G0 cerrado ("usa defaults") · **G1 abierto — esperando respuesta del usuario**.
- Tests: 30 / 30 PASS (pasos 00–04).

## Parámetros vigentes
| Parámetro | Valor | Etiqueta |
|:--|:--|:--|
| Escala | S₀ = 600 @ O₀ = 20:1 (buenos:malos), PDO = 40 ⟹ Factor 57.71, Offset 427.12 | [DEF-default] I-6 |
| SEED | 42 | [DEF] |
| Target principal | B = hard ∪ (soft con value_lost/RV ≥ θ), θ = 0.25; soft con pérdida < 0.25 = indeterminado | [DEF-default] I-1 |
| Target de sensibilidad | A = hard_churn_6m | [DEF-default] I-1 |
| Capacidad | sin dato → Crítico por lift / precisión / eventos; tabla de caseload 40 / 100 / 200 banqueros | [DEF-default] I-2 |
| `multi_signal_count` / `_flag` | fuera del campeón; permitidos en challenger | [DEF-default] I-3 |
| `churn_excluded` | se excluyen (123); motivo desconocido | [DEF-default] I-4 |
| `relationship_value`, `share_of_wallet` | se usan como vienen; RV = AUM + depósitos (G0-a) | [DEF-default] I-5, G0-a |
| Segmentación | libro completo con `segment` como variable; UHNW reportado aparte | [DEF-default] I-7 |
| Antigüedad | excluir `tenure_years` < 1 | [DEF-default] I-8 |
| Supervivencia | no; solo descriptivo en paso 14 | [DEF-default] I-9 |
| `value_lost_6m` | solo churn por valor y calibración por valor; nunca predictor | [DEF-default] I-10 |

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

- **D1.1 · Población y targets.** B: 19,261 hogares, 2,674 eventos (13.88%); A: 19,473 hogares, 1,168 eventos
  (6.00%) [DATA]. 212 indeterminados de B (soft con pérdida < 0.25) fuera de entrenamiento y dentro de scoring.
- **D1.2 · Exclusión tenure < 1 (I-8, default).** Los 404 excluidos tienen más churn que el resto (A 7.92% vs 6.00%;
  B 16.50% vs 13.88%) [DATA]. El modelo no se desarrolla sobre clientes nuevos; se pregunta en G1 cómo tratarlos.
- **D1.3 · Pesos de clase.** Balanceados, w = N / (2·n_clase); odds de población B 0.1612 (ln −1.825) y A 0.0638
  (ln −2.752) [DATA] para corregir el intercepto en el paso 11. Nunca SMOTE.
- **D2.1 · Diccionario.** 54 predictores, 5 prohibidas, 3 auxiliares (2 compuestos y `value_lost_6m`) [DATA].
  Dimensiones ausentes: digital y vida (L6). Signos a priori en `outputs/tables/step02_signs_a_priori.csv`; 7 sin
  hipótesis ("?").
- **D2.2 · Revisión regulatoria pendiente.** `age_primary` (fair lending) y `bureau_new_mortgage_elsewhere` (FCRA,
  propósito permisible): pregunta en G1.
- **D3.1 · Calidad.** 0 duplicados, 0 imposibles, RV = AUM + depósitos al centavo, excepciones estructurales ≤ 3%
  (134 valores de pensión sin `has_pension_stream`), 0 errores en colas; extraordinarios conservados sin capping
  (p. ej. 63 hogares = 52.3% del monto enviado a competidores) [DATA].
- **D4.1 · Split.** Estratificado por clase (hard / soft ≥ θ / indeterminado / no evento) × segmento. La versión
  inicial estratificada solo por B dejó A desbalanceada (6.22% vs 5.48%, test de ±0.5 pp fallido) y se corrigió sin
  relajar el umbral. Dev 13,631 (B 13,482 / 1,871 eventos; A 817) · val 5,842 (B 5,779 / 803; A 351) [DATA].

## Limitaciones registradas
- **L1** Sin OOT ni cohortes ni PSI temporal (un solo snapshot 2025-12-31) [DATA].
- **L2** Señales pre-ingenierizadas sin timestamps auditables; se asume as-of T0.
- **L4** Dataset sintético: nada se presenta como resultado de un banco real.

## G0 · respuesta del usuario (2026-09-29)
- "usa defaults" → I-1 a I-10 y G0-a con su default, marcados [DEF-default] en la tabla de parámetros.

## Preguntas abiertas
- G1-1 a G1-4 en `reports/gate_1.md`.
