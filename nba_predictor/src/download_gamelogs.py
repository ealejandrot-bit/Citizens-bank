"""Fase 1: descarga los game logs de equipos 2016-17 a 2025-26 y los guarda en SQLite.

Uso (desde nba_predictor/):
    python -m src.download_gamelogs                      # todo lo que falte
    python -m src.download_gamelogs --seasons 2023-24 --force
    python -m src.download_gamelogs --season-types "Regular Season"

Es reanudable: cada (temporada, tipo) descargado queda en `fetch_log` y se salta en la
siguiente corrida salvo con --force. Al final reconstruye la tabla `games`.
"""
import argparse
import logging
import random
import sys
import time
from pathlib import Path

from src import config, db
from src.games import build_games, normalize_logs
from src.nba_client import fetch_team_game_logs

log = logging.getLogger("download")


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--seasons", nargs="+", default=config.all_seasons())
    p.add_argument("--season-types", nargs="+", default=list(config.SEASON_TYPES))
    p.add_argument("--db", type=Path, default=config.DB_PATH)
    p.add_argument("--raw-dir", type=Path, default=config.RAW_DIR,
                   help="Copia CSV de cada respuesta para auditoría")
    p.add_argument("--force", action="store_true", help="Volver a descargar lo ya guardado")
    p.add_argument("--pause", type=float, default=config.PAUSE_SECONDS)
    p.add_argument("--max-retries", type=int, default=config.MAX_RETRIES)
    p.add_argument("--timeout", type=int, default=config.REQUEST_TIMEOUT)
    return p.parse_args(argv)


def run(args: argparse.Namespace, fetch=fetch_team_game_logs, sleep=time.sleep) -> int:
    conn = db.connect(args.db)
    done = set() if args.force else db.fetched(conn)
    pending = [(s, t) for s in args.seasons for t in args.season_types if (s, t) not in done]
    log.info("%d combinaciones pendientes (%d ya descargadas)",
             len(pending), len(args.seasons) * len(args.season_types) - len(pending))

    failures = []
    for i, (season, season_type) in enumerate(pending):
        if i > 0:
            sleep(args.pause + random.uniform(0, config.PAUSE_JITTER))
        try:
            raw = fetch(season, season_type, max_retries=args.max_retries, timeout=args.timeout)
            logs = normalize_logs(raw, season, season_type)
        except Exception as exc:  # una temporada fallida no detiene las demás
            log.error("%s %s: FALLÓ tras reintentos (%s: %s)", season, season_type,
                      type(exc).__name__, exc)
            failures.append((season, season_type))
            continue
        if args.raw_dir:
            args.raw_dir.mkdir(parents=True, exist_ok=True)
            raw.to_csv(args.raw_dir / f"leaguegamelog_{season}_{season_type.replace(' ', '')}.csv",
                       index=False)
        db.replace_season(conn, season, season_type, logs)
        log.info("%s %-14s %5d filas (%d partidos)", season, season_type, len(logs),
                 logs["game_id"].nunique())

    games, problems = build_games(db.read_logs(conn))
    db.replace_games(conn, games)
    log.info("Tabla games: %d partidos; %d game_id descartados por inconsistencias",
             len(games), len(problems))
    if len(problems):
        log.warning("Revisa con: python -m src.validate_data")
    conn.close()

    if failures:
        log.error("Fallaron %d combinaciones: %s. Vuelve a correr el script para reintentarlas.",
                  len(failures), failures)
        return 1
    return 0


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return run(parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
