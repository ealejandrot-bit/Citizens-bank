"""Chequeos de calidad sobre la base descargada (antes de construir features).

Uso (desde nba_predictor/):
    python -m src.validate_data [--db data/nba.sqlite]

Sale con código 1 si falla algún chequeo duro; los resúmenes son informativos.
"""
import argparse
import sqlite3
import sys
from pathlib import Path

import pandas as pd

from src import config
from src.games import build_games

# Partidos de temporada regular por equipo. 2019-20 se cortó por COVID (63-75 según equipo,
# incluidos los juegos de seeding en la burbuja); 2020-21 fue de 72.
EXPECTED_RS_GAMES = {"2019-20": (63, 75), "2020-21": (72, 72)}
DEFAULT_RS_GAMES = (82, 82)
PLAYOFF_GAMES_RANGE = (60, 105)  # 15 series de 4 a 7 partidos
PLAYIN_GAMES_FROM = "2020-21"    # 6 partidos por temporada desde entonces


def run_checks(conn: sqlite3.Connection, seasons: list[str]) -> list[tuple[str, bool, str]]:
    """Lista de (chequeo, pasó, detalle)."""
    results = []

    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    fetch_log = pd.read_sql_query("SELECT * FROM fetch_log", conn)
    logs = pd.read_sql_query("SELECT * FROM team_game_logs", conn)
    games = pd.read_sql_query("SELECT * FROM games", conn)

    expected = {(s, t) for s in seasons for t in config.SEASON_TYPES}
    missing = sorted(expected - set(zip(fetch_log["season"], fetch_log["season_type"])))
    check("Todas las temporadas/tipos descargados", not missing, f"faltan: {missing}" if missing else "")

    _, problems = build_games(logs)
    check("Cada game_id tiene un local y un visitante consistentes", problems.empty,
          problems.groupby("reason").size().to_string() if len(problems) else "")
    check("games = game_id únicos en team_game_logs", len(games) == logs["game_id"].nunique(),
          f"{len(games)} vs {logs['game_id'].nunique()}")
    check("Sin game_id duplicados en games", not games["game_id"].duplicated().any())

    null_cols = [c for c in ["game_date", "home_pts", "away_pts", "winner_team_id"]
                 if games[c].isna().any()]
    check("Sin nulos en fecha, marcador y ganador", not null_cols, str(null_cols) if null_cols else "")
    pts = pd.concat([games["home_pts"], games["away_pts"]])
    check("Puntos en rango [50, 200]", pts.between(50, 200).all(),
          f"min={pts.min()}, max={pts.max()}" if len(pts) else "")
    winner_ok = ((games["home_win"] == 1) == (games["winner_team_id"] == games["home_team_id"])).all()
    check("winner_team_id coherente con home_win", winner_ok)

    dup_day = logs.duplicated(["team_id", "game_date"]).sum()
    check("Ningún equipo juega dos veces el mismo día", dup_day == 0, f"{dup_day} casos")

    start_year = games["season"].str[:4].astype(int)
    game_year = games["game_date"].str[:4].astype(int)
    bad_dates = (~game_year.between(start_year, start_year + 1)).sum()
    check("Fechas dentro del año de la temporada", bad_dates == 0, f"{bad_dates} partidos")

    rs = logs[logs["season_type"] == "Regular Season"]
    teams = rs.groupby("season")["team_id"].nunique().reindex(seasons, fill_value=0)
    bad_teams = teams[teams != 30]
    check("30 equipos por temporada regular", bad_teams.empty, bad_teams.to_string() if len(bad_teams) else "")

    per_team = rs.groupby(["season", "team_abbreviation"]).size().rename("games").reset_index()
    bounds = per_team["season"].map(lambda s: EXPECTED_RS_GAMES.get(s, DEFAULT_RS_GAMES))
    off = per_team[[not (lo <= n <= hi) for n, (lo, hi) in zip(per_team["games"], bounds)]]
    check("Partidos de temporada regular por equipo (82; 72 en 2020-21)", off.empty,
          off.to_string(index=False) if len(off) else "")

    po = games[games["season_type"] == "Playoffs"].groupby("season").size().reindex(seasons, fill_value=0)
    bad_po = po[~po.between(*PLAYOFF_GAMES_RANGE)]
    check(f"Partidos de playoffs por temporada en {PLAYOFF_GAMES_RANGE}", bad_po.empty,
          bad_po.to_string() if len(bad_po) else "")

    pi = games[games["season_type"] == "PlayIn"].groupby("season").size()
    pi_expected = [s for s in seasons if s >= PLAYIN_GAMES_FROM]
    bad_pi = {s: int(pi.get(s, 0)) for s in pi_expected if pi.get(s, 0) != 6}
    check("6 partidos de play-in por temporada desde 2020-21", not bad_pi, str(bad_pi) if bad_pi else "")
    return results


def summary(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        """
        SELECT season, season_type, COUNT(*) AS games,
               ROUND(AVG(home_win), 3) AS home_win_rate,
               ROUND(AVG(home_pts), 1) AS avg_home_pts,
               ROUND(AVG(away_pts), 1) AS avg_away_pts,
               MIN(game_date) AS first_game, MAX(game_date) AS last_game
        FROM games GROUP BY season, season_type
        ORDER BY season, CASE season_type WHEN 'Regular Season' THEN 0
                                          WHEN 'PlayIn' THEN 1 ELSE 2 END
        """,
        conn,
    )


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--db", type=Path, default=config.DB_PATH)
    p.add_argument("--seasons", nargs="+", default=config.all_seasons())
    args = p.parse_args(argv)
    if not args.db.exists():
        print(f"No existe {args.db}; corre primero: python -m src.download_gamelogs")
        return 1

    conn = sqlite3.connect(args.db)
    pd.set_option("display.width", 140)
    print("Resumen por temporada\n" + summary(conn).to_string(index=False) + "\n")
    results = run_checks(conn, args.seasons)
    conn.close()

    for name, ok, detail in results:
        print(f"[{'OK ' if ok else 'FALLA'}] {name}")
        if not ok and detail:
            print("        " + detail.replace("\n", "\n        "))
    n_fail = sum(not ok for _, ok, _ in results)
    print(f"\n{len(results) - n_fail}/{len(results)} chequeos OK")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
