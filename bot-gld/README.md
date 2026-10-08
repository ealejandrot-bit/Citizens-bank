# Bot GLD (fase 0–1: backtest, sin órdenes)

Especificación completa en [`SPEC.md`](SPEC.md). Resumen: solo GLD, long-only, **ningún código envía
órdenes** (las conexiones a IBKR son `readonly=True`), y no se corre backtest con datos reales hasta
que `check_connection.py` pase completo.

## Instalación

```bash
cd bot-gld
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # llenar IB_ACCOUNT; .env no se sube a git
```

## Flujo

1. **Pruebas (datos sintéticos):** `pytest`
2. **Conexión (solo lectura):** con IB Gateway abierto (cuenta real, *Read-Only API* activado, puerto 4001):
   `python check_connection.py` → imprime OK / FALLA en los 9 puntos. Si todos pasan escribe
   `logs/check_connection_ok.json`, que habilita los pasos siguientes.
3. **Descarga:** `python -m src.data.ibkr_source` → `data/GLD_1d.parquet` y `data/GLD_5m.parquet`.
4. **Reporte:** `python -m src.report trend_daily` y `python -m src.report vwap_intraday` →
   `reports/<fecha>_<estrategia>.md` + PNG.

Demo sin conexión: `python -m src.report trend_daily --sintetico` (datos sintéticos, marcado como tal).

## Notas

- Capital, costos, fechas de corte y parámetros viven en `config.yaml` (fijados antes de ver resultados).
- Con `capital_inicial: 27` y `fracciones: false`, GLD (> 27 USD/acción) es **no operable**: el reporte lo
  dice en lugar de simular. Con `fracciones: true` sí se simula, pero la comisión mínima/tope del 1% pesa mucho.
- Cada periodo (in-sample, out-of-sample, total) es un backtest independiente con el mismo capital, junto a
  comprar y mantener con sus costos.
- `tests/test_safety.py` falla si aparece cualquier función de órdenes en el código.
