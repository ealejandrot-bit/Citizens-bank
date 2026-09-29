# Modelo 1 · Churn Propensity Scorecard (Client Pulse)

Scorecard auditable e interpretable (WoE/IV + logística) para predecir `hard_churn_6m` en hogares
HNW/UHNW de banca privada, sobre la base **sintética** del repositorio. Gobernanza estilo SR 11-7.
Todas las cifras son [DATA-SINT]: salen de los datos, pero la base es sintética.

## Reproducir

```bash
pip install -r requirements.txt
./run_all.sh              # pasos 00–17 en orden (~15 min); se detiene en el primer QC gate fallido
```

- Fuente (solo lectura): `../data/synthetic/client_pulse_synthetic.csv`. Otra ruta: `DATA_PATH=/ruta/base.xlsx ./run_all.sh`.
- Semilla global 42 (numpy, sklearn, lightgbm).

## Resultado (Modelo 1)

- **A · campeón operativo**: logística sobre WoE con 10 señales + `segment`; tabla de puntos en
  `outputs/tables/12_scorecard_lookup.csv`. Holdout: AUC 0.725, decil top 38% de los eventos [DATA-SINT].
- **A-lite · versión ejecutiva**: 4 señales + `segment` (tarjeta de 5 renglones) en `12_scorecard_lookup_alite.csv`.
- Salida por hogar: `outputs/scored/scored_households.csv` (score, probabilidad calibrada, tramo, override, 3 razones,
  p × valor, prioridad; columnas `_lite` para A-lite).
- Documento de modelo: `REPORT.md` (pasos 0–17). Decisiones y desvíos del brief: `DECISIONS.md`.
- Supuestos a confirmar: capacidad Crítico 3% y Alto 10% (`src/common.py`).

## Estructura

```
src/common.py      rutas, semilla, parámetros, QC y utilidades
src/00_setup.py …  un script por paso (00–17)
src/woe.py         binning / WoE reutilizable
src/metrics.py     métricas, bootstrap, captura con empates
src/dictionary.py  diccionario de las 62 columnas
outputs/tables/    CSV + MD por paso
outputs/figures/   PNG
outputs/models/    modelos (pkl)
outputs/scored/    scored_households.csv
outputs/data/      matriz de features intermedia (regenerable, no versionada)
REPORT.md          documento de modelo, pasos 0–17
DECISIONS.md       decisiones metodológicas y alternativas descartadas
```
