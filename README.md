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
docs/decisiones.md          Log de decisiones y supuestos a validar
docs/distribuciones.md      Distribución por variable (Paso 0 construido, 1–37 propuesta)
docs/reports/               Reporte de cada paso
```

## Uso

```bash
pip install -r requirements.txt
python scripts/extract_catalog.py   # catálogo de variables
python scripts/build_step0.py       # genera data/synthetic/step0_*.csv + manifiesto
python scripts/stats_step0.py       # 200 pruebas estadísticas + 200 semillas de referencia (~1 min)
python -m pytest                    # tests de semillas, reproducibilidad y suite estadística rápida
```

Los CSV no se versionan: se regeneran de forma idéntica desde la semilla. El
manifiesto (`data/synthetic/step0_manifest.json`) guarda el SHA-256 esperado de cada
salida, así que si un rebuild da otro hash, algo cambió.

## Estado

| Paso | Contenido | Estado |
|---|---|---|
| 0 | Población, latentes, target | Construido y validado |
| 1–8 | Variables por grupo (ver `docs/decisiones.md`) | Pendiente |
