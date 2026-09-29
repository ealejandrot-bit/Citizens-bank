# Client Pulse · Base sintética

**Base final:** `data/synthetic/client_pulse_synthetic.csv` (20,000 hogares × 62 columnas, las 37
variables del Excel + target). Resumen de cada variable en `docs/reports/final_report.md`.

**Scores:** `python scripts/score_models.py` construye la variable de churn sobre la ventana de
resultado y compara reglas, scorecard experto, scorecard WoE, Gradient Boosting, logística y red
neuronal. Resultados en `docs/reports/model_comparison.md`.

Base sintética a nivel hogar con las 37 variables de `docs/Client_Pulse_37_Variables.xlsx`,
para prototipar el score de attrition de Citizens Private Bank (scorecard → ML → neural).
Se construye por pasos, validando la distribución y las semillas de cada uno.
Todos los montos están en **USD** (Citizens es un banco de EE. UU.); el diccionario de
columnas con unidades está en `synthetic/schema.py` y al final de cada reporte.

## Estructura

```
config/params.yaml          Todos los parámetros y la semilla maestra (con su origen)
synthetic/seeds.py          SeedManager: un flujo aleatorio independiente por nombre
synthetic/population.py     Paso 0: hogares, factores latentes, target
synthetic/exit_events.py    Evento común: mudanza del banco principal (Pasos 1+)
synthetic/pipeline.py       Orden de construcción (un solo lugar para scripts y tests)
synthetic/schema.py         Diccionario de columnas con unidad (montos en USD)
synthetic/stats_tests.py    Pruebas estadísticas (ajuste, colas, curtosis, sesgo, duplicados, semilla)
config/validation.yaml      Criterios: α, semillas de referencia, máximos y bandas de negocio (USD)
synthetic/validate.py       Chequeos por paso (el build falla si alguno no pasa)
scripts/extract_catalog.py  Excel → data/catalog/variables_catalog.csv
scripts/build_step0.py      Construye, valida y escribe el Paso 0
synthetic/balances.py       Paso 1: series mensuales de depósitos y AUM → variables 1, 2, 17, 18
synthetic/validate_step1.py Validación del Paso 1 (estructura, NULL, calibración, t(6), fuga)
synthetic/metrics.py        WoE / IV y tendencia de Cochran-Armitage
scripts/build_step1.py      Construye, valida y escribe el Paso 1 (+ 20 semillas de referencia)
synthetic/recurring.py      Paso 2: transacciones recurrentes + algoritmo de detección → variables 3, 4, 5, 6, 19, 20
synthetic/validate_step2.py Validación del Paso 2 (detector, exclusiones, bono, calibración, fuga)
scripts/build_step2.py      Construye, valida y escribe el Paso 2 (+ 20 semillas de referencia)
synthetic/transfers.py      Paso 3: transferencias externas, catálogo sintético, identidad contable → 7, 8, 21–25
synthetic/validate_step3.py Validación del Paso 3 (identidad, exclusiones, ABA/HHI, pisos PB, calibración, fuga)
scripts/build_step3.py      Construye, valida y escribe el Paso 3 (+ 20 semillas de referencia)
synthetic/investments.py    Paso 4: composición del portafolio, vencimientos, benchmark → 9, 26, 27, 28, 34
synthetic/validate_common.py Piezas de validación compartidas (calibración, semillas, AUC combinado)
synthetic/validate_step4.py Validación del Paso 4
scripts/build_step4.py      Construye, valida y escribe el Paso 4 (+ 20 semillas de referencia)
synthetic/relationship.py   Paso 5: cuentas y cierres, share of wallet, trustee → 10, 29, 30, 31, 32
synthetic/validate_step5.py Validación del Paso 5
scripts/build_step5.py      Construye, valida y escribe el Paso 5 (+ 20 semillas de referencia)
synthetic/banker.py         Paso 6: carteras, cambios de banker, bitácora de interacción → 11, 12, 13, 35
synthetic/validate_step6.py Validación del Paso 6
scripts/build_step6.py      Construye, valida y escribe el Paso 6 (+ 20 semillas de referencia)
synthetic/complaints.py     Paso 7: quejas (categoría, SLA, escalamiento, reapertura) y Assistant → 14, 15, 33, 36
synthetic/validate_step7.py Validación del Paso 7
scripts/build_step7.py      Construye, valida y escribe el Paso 7 (+ 20 semillas de referencia)
synthetic/composite.py      Paso 8: multi-señal (umbrales del Excel) y buró → 16, 37
synthetic/validate_step8.py Validación del Paso 8 y de la base final
scripts/build_step8.py      Paso 8 + base final consolidada + reporte final de las 37 variables
synthetic/outcome.py        Ventana de resultado (t, t+6m] y construcción de la variable de churn
synthetic/scoring.py        Metodologías de score, métricas, bootstrap e importancia de drivers
scripts/score_models.py     Construye el churn, entrena y compara las metodologías
docs/decisiones.md          Log de decisiones y supuestos a validar
docs/distribuciones.md      Distribución por variable (Paso 0 construido, 1–37 propuesta)
docs/reports/               Reporte de cada paso
```

## Uso

```bash
pip install -r requirements.txt
python scripts/extract_catalog.py   # catálogo de variables
python scripts/build_step0.py       # genera data/synthetic/step0_*.csv + manifiesto
python scripts/build_step1.py       # genera data/synthetic/step1_*.csv + manifiesto
python scripts/build_step2.py       # genera data/synthetic/step2_*.csv + manifiesto
python scripts/build_step3.py       # genera data/synthetic/step3_*.csv + catálogo + manifiesto (~2.5 min)
python scripts/build_step4.py       # genera data/synthetic/step4_*.csv + manifiesto
python scripts/build_step5.py       # genera data/synthetic/step5_*.csv + manifiesto
python scripts/build_step6.py       # genera data/synthetic/step6_*.csv + manifiesto
python scripts/build_step7.py       # genera data/synthetic/step7_*.csv + manifiesto
python scripts/build_step8.py       # base final (client_pulse_synthetic*.csv) + docs/reports/final_report.md
python scripts/stats_step0.py       # 200 pruebas estadísticas + 200 semillas de referencia (~1 min)
python -m pytest                    # tests de semillas, reproducibilidad y suite estadística rápida
```

Los CSV intermedios no se versionan: se regeneran de forma idéntica desde la semilla. La base final
principal sí está en el repositorio. El
manifiesto (`data/synthetic/step0_manifest.json`) guarda el SHA-256 esperado de cada
salida, así que si un rebuild da otro hash, algo cambió.

## Estado

| Paso | Contenido | Estado |
|---|---|---|
| 0 | Población, latentes, target, ingresos | Construido y validado (200 pruebas) |
| 1 | Balances & AUM: variables 1, 2, 17, 18 | Construido y validado (54 pruebas, 20 semillas) |
| 2 | Recurring deposits & flows: variables 3, 4, 5, 6, 19, 20 | Construido y validado (71 pruebas, 20 semillas) |
| 3 | Transfers: variables 7, 8, 21, 22, 23, 24, 25 | Construido y validado (71 pruebas, 20 semillas) |
| 4 | Investments: variables 9, 26, 27, 28, 34 | Construido y validado (53 pruebas, 20 semillas) |
| 5 | Relationship & closures: variables 10, 29, 30, 31, 32 | Construido y validado (56 pruebas, 20 semillas) |
| 6 | Banker: variables 11, 12, 13, 35 | Construido y validado (40 pruebas, 20 semillas) |
| 7 | Complaints & voice of client: variables 14, 15, 33, 36 | Construido y validado (38 pruebas, 20 semillas) |
| 8 | External & composite: variables 16, 37 + base final | Construido y validado (24 pruebas, 10 semillas) |

**Las 37 variables están construidas y validadas.**
