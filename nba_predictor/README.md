# NBA · Predicción de ganadores

**Fase 1 (actual): datos.** Descarga los game logs de equipos de 2016-17 a 2025-26 desde
stats.nba.com (`nba_api`) y los guarda en SQLite. Features y modelo vienen después de
validar los datos.

## Estructura

```
data/                 nba.sqlite (no versionado) y data/raw/ con el CSV de cada respuesta
notebooks/            Exploración (vacío por ahora)
src/config.py         Temporadas, tipos de temporada, pausas, reintentos, rutas
src/nba_client.py     Llamada a LeagueGameLog con reintentos y backoff exponencial
src/games.py          Normalización y emparejado local/visitante → una fila por partido
src/db.py             Esquema SQLite y escrituras atómicas por temporada
src/download_gamelogs.py  Script de descarga (reanudable)
src/validate_data.py  Chequeos de calidad sobre la base
tests/                Pruebas con respuestas simuladas de la API (sin red)
```

## Uso

Desde `nba_predictor/`:

```bash
pip install -r requirements.txt
python -m src.download_gamelogs      # ~30 llamadas (10 temporadas × 3 tipos), unos minutos
python -m src.validate_data          # resumen por temporada + chequeos OK/FALLA
python -m pytest
```

- Una llamada a `LeagueGameLog` por (temporada, tipo) trae todos los equipos; tipos:
  `Regular Season`, `PlayIn` (desde 2020-21) y `Playoffs`.
- Pausa de 2–3 s entre llamadas; hasta 5 reintentos con backoff de 5, 10, 20, 40, 80 s
  (tope 120 s) ante timeouts, errores HTTP o respuestas incompletas.
- Reanudable: lo descargado queda en `fetch_log` y se salta; `--force` vuelve a bajarlo.
  Si una temporada falla, el resto sigue y el script sale con código 1.

## Tablas

| Tabla | Grano | Contenido |
|---|---|---|
| `team_game_logs` | equipo × partido (PK `game_id, team_id`) | Box score de equipo tal como lo da la API, más `season`, `season_type`, `is_home` |
| `games` | partido (PK `game_id`) | `season`, `season_type`, `game_date`, local y visitante (id y abreviatura), `home_pts`, `away_pts`, `winner_team_id`, `winner_abbr`, `home_win` |
| `fetch_log` | temporada × tipo | Filas recibidas y fecha de descarga |

`games` se reconstruye completa desde `team_game_logs` en cada corrida. Local/visitante sale de
`MATCHUP` (`LAL vs. BOS` = LAL local; `LAL @ BOS` = LAL visitante). Un partido sólo entra si
tiene exactamente una fila local y una visitante, misma fecha, sin empate y con `WL`
coherente con el marcador; los descartados aparecen en `validate_data`.

## Qué revisa `validate_data`

Cobertura de todas las temporadas/tipos, emparejado de cada `game_id`, nulos, puntos en
[50, 200], ningún equipo dos veces el mismo día, fechas dentro de la temporada, 30 equipos por
temporada regular, 82 partidos por equipo (72 en 2020-21; 63–75 en 2019-20), 60–105 partidos
de playoffs y 6 de play-in desde 2020-21. Imprime además la tasa de victorias locales por
temporada.

## Limitaciones conocidas

- La final de la NBA Cup (desde 2023-24) no cuenta como temporada regular y no está en estos
  tres tipos; los partidos de grupo y cuartos/semis sí están en `Regular Season`.
- Partidos en sede neutral (burbuja 2020, juegos internacionales, final de la Cup) conservan
  el local designado por la NBA: `home_win` no siempre implica ventaja de cancha real.
