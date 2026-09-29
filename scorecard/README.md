# Modelo 1 · Churn Propensity Scorecard (Client Pulse)

Scorecard auditable e interpretable (WoE/IV + logística) para predecir `hard_churn_6m` en hogares
HNW/UHNW de banca privada, sobre la base **sintética** del repositorio. Gobernanza estilo SR 11-7.
Todas las cifras son [DATA-SINT]: salen de los datos, pero la base es sintética.

## Reproducir

```bash
pip install -r requirements.txt
./run_all.sh              # pasos 00–17 en orden; se detiene en el primer QC gate fallido
```

- Fuente (solo lectura): `../data/synthetic/client_pulse_synthetic.csv`. Otra ruta: `DATA_PATH=/ruta/base.xlsx ./run_all.sh`.
- Semilla global 42 (numpy, sklearn, lightgbm).

## Estructura

```
src/common.py      rutas, semilla, parámetros, QC y utilidades
src/00_setup.py …  un script por paso (00–17)
outputs/tables/    CSV + MD por paso
outputs/figures/   PNG
outputs/models/    modelos (pkl)
outputs/scored/    scored_households.csv
REPORT.md          documento de modelo, pasos 0–17
DECISIONS.md       decisiones metodológicas y alternativas descartadas
```
