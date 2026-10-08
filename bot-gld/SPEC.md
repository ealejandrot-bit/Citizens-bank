# Bot GLD — Especificación del modelo (v0)

Instrucciones para Claude Code. Este archivo va en la raíz del repo como `SPEC.md`.

## Reglas no negociables
1. **Solo GLD.** Long-only (sin cortos, sin apalancamiento, sin opciones).
2. **Sin órdenes.** En esta fase el código no envía órdenes a IBKR. Nada de `placeOrder`. Fases 0–1 se conectan a la **cuenta real en modo Read-Only** (IB Gateway, puerto 4001) solo para leer datos; las órdenes de prueba (Fase 2) se harán únicamente en la cuenta paper.
3. **No se corre ningún backtest con datos reales** hasta que `check_connection.py` pase completo. Las pruebas del motor se hacen con datos sintéticos.
4. **Benchmark obligatorio:** toda estrategia se reporta junto a comprar y mantener GLD, mismo periodo, mismo capital y con sus costos.
5. **Parámetros fijados antes de ver resultados.** Nada de optimizar sobre el periodo out-of-sample.
6. Credenciales solo en `.env` (excluido de git). Nunca en código ni en logs.

## Estructura
```
bot-gld/
  SPEC.md
  README.md
  requirements.txt        # ib_async, pandas, numpy, pytest, python-dotenv
  .env.example            # IB_HOST=127.0.0.1, IB_PORT=4001, IB_CLIENT_ID=1, IB_ACCOUNT (cuenta real, solo lectura)
  .gitignore              # .env, data/, logs/, __pycache__/
  config.yaml             # capital, costos, parámetros de estrategias, fechas de corte
  check_connection.py     # ver checklist al final
  src/
    data/ibkr_source.py   # descarga históricos vía ib_async (diario y 5 min) → data/*.parquet
    data/loader.py        # lee parquet; interfaz única para el backtest
    strategies/trend_daily.py
    strategies/vwap_intraday.py
    backtest/engine.py
    backtest/costs.py
    backtest/metrics.py
    report.py             # genera reports/<fecha>_<estrategia>.md
  tests/                  # pytest con datos sintéticos
```

## Configuración (config.yaml)
- `capital_inicial`: parámetro (moneda USD). Valor inicial: 27 USD (tope actual 500 MXN; se actualizará al depositar más).
- `fracciones`: true/false. Si false, solo acciones enteras; si el capital no alcanza 1 acción, la estrategia reporta "no operable" en lugar de simular.
- Costos (todos editables; verificar contra la tabla vigente de IBKR antes de confiar en resultados):
  - Comisión IBKR Pro fija: 0.005 USD/acción, mínimo 1.00 USD, máximo 1% del valor de la operación.
  - Slippage: 0.01 USD por acción por lado (diario) y 0.02 (intradía).
  - Conversión MXN→USD: costo fijo único al inicio (parámetro).
  - Datos de mercado: costo mensual (parámetro, default 0) restado del capital cada mes.
- Fechas: `in_sample_end` y `out_sample_start` definidos en config, no en código.

## Estrategia 1 — Tendencia diaria (`trend_daily`)
- Señal al cierre del día t: largo si `close > SMA(200)`; si no, en efectivo.
- Ejecución: apertura del día t+1 (nunca al mismo cierre que generó la señal).
- Tamaño: 100% del capital disponible cuando está largo.
- Parámetro fijo: 200. Variante de control (no optimización): 50/200 cruce.

## Estrategia 2 — VWAP intradía (`vwap_intraday`)
- Barras de 5 min, solo horario regular (9:30–16:00 ET).
- Sin operaciones los primeros 30 min.
- Entrada: largo cuando una barra cierra arriba del VWAP del día habiendo cerrado la anterior abajo.
- Salida: barra cierra abajo del VWAP, o 15:55 ET. Nunca se queda posición de un día para otro.
- Máximo de operaciones por día: parámetro (default 2).
- Reportar además el número de day trades por ventana de 5 días hábiles (para la regla de pattern day trader).

## Motor de backtest
- Por eventos/barras, sin mirar el futuro: la señal usa datos hasta la barra t; la ejecución ocurre en t+1.
- Costos aplicados en cada lado de la operación.
- Equity diaria registrada para ambos: estrategia y comprar y mantener.
- Comprar y mantener: compra en la primera barra del periodo con todo el capital, vende en la última, con costos.

## Métricas (por periodo in-sample, out-of-sample y total)
CAGR, volatilidad anual, Sharpe (rf = 0, declarado), drawdown máximo y su duración, # operaciones, win rate, ganancia/pérdida promedio, exposición (% del tiempo invertido), costo total en USD y como % del capital inicial, y **diferencia vs. comprar y mantener** en CAGR, Sharpe y drawdown.

## Reporte
Markdown con: configuración usada (capital, costos, fechas, parámetros), tabla de métricas estrategia vs. comprar y mantener, curva de equity (PNG), lista de supuestos y advertencias (p. ej. datos con retraso, fracciones).

## Pruebas mínimas (pytest, datos sintéticos)
- Serie con tendencia constante: trend_daily queda largo y su resultado ≈ comprar y mantener menos costos.
- Serie plana con ruido: costos totales se reflejan exactamente en la equity.
- Sin look-ahead: alterar la barra t+1 no cambia la señal de t.
- Comisión: respeta mínimo y máximo.
- Intradía: nunca hay posición abierta al cierre.

## Orden de trabajo
1. Esqueleto + `check_connection.py`.
2. Costos, métricas y motor + pruebas con datos sintéticos.
3. Estrategias + pruebas.
4. Reporte.
5. **Esperar** a que pase `check_connection.py` → descargar datos de IBKR → correr backtest → entregar reporte.

## Checklist de `check_connection.py` (solo lectura)
Imprimir OK / FALLA por punto:
1. Conecta a IB_HOST:IB_PORT sin error.
2. Lista las cuentas del login y confirma que IB_ACCOUNT está entre ellas; imprime si es real o paper (paper empieza con "D"). Si es real, imprime: "MODO SOLO LECTURA – cuenta real".
3. Diferencia hora servidor vs. local < 2 s.
4. GLD resuelto (STK, SMART, USD, primaryExchange ARCA) y conId.
5. Snapshot de GLD: bid/ask/last y marketDataType (si no hay suscripción, pedir datos con retraso: reqMarketDataType(3)).
6. Account summary: NetLiquidation y moneda.
7. Posiciones y órdenes abiertas (deben estar vacías).
8. 5 barras diarias y 5 barras de 5 min de GLD.
9. Desconexión limpia.
El script no importa ni llama ninguna función de órdenes.
