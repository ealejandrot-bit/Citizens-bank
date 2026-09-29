# Client Pulse · Base sintética

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
python scripts/stats_step0.py       # 200 pruebas estadísticas + 200 semillas de referencia (~1 min)
python -m pytest                    # tests de semillas, reproducibilidad y suite estadística rápida
```

Los CSV no se versionan: se regeneran de forma idéntica desde la semilla. El
manifiesto (`data/synthetic/step0_manifest.json`) guarda el SHA-256 esperado de cada
salida, así que si un rebuild da otro hash, algo cambió.

## Estado

| Paso | Contenido | Estado |
|---|---|---|
| 0 | Población, latentes, target, ingresos | Construido y validado (200 pruebas) |
| 1 | Balances & AUM: variables 1, 2, 17, 18 | Construido y validado (50 pruebas, 20 semillas) |
| 2 | Recurring deposits & flows: variables 3, 4, 5, 6, 19, 20 | Construido y validado (65 pruebas, 20 semillas) |
| 3–8 | Resto de variables por grupo (ver `docs/decisiones.md`) | Pendiente |
