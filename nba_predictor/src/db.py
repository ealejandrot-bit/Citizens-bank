"""Esquema y escritura en SQLite."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.games import GAME_COLUMNS, LOG_COLUMNS

SCHEMA = """
CREATE TABLE IF NOT EXISTS team_game_logs (
    season            TEXT    NOT NULL,   -- '2016-17'
    season_type       TEXT    NOT NULL,   -- 'Regular Season' | 'PlayIn' | 'Playoffs'
    season_id         TEXT,
    team_id           INTEGER NOT NULL,
    team_abbreviation TEXT,
    team_name         TEXT,
    game_id           TEXT    NOT NULL,
    game_date         TEXT    NOT NULL,   -- YYYY-MM-DD
    matchup           TEXT,
    wl                TEXT,
    min INTEGER, fgm INTEGER, fga INTEGER, fg_pct REAL, fg3m INTEGER, fg3a INTEGER,
    fg3_pct REAL, ftm INTEGER, fta INTEGER, ft_pct REAL, oreb INTEGER, dreb INTEGER,
    reb INTEGER, ast INTEGER, stl INTEGER, blk INTEGER, tov INTEGER, pf INTEGER,
    pts INTEGER, plus_minus INTEGER,
    is_home           INTEGER,            -- 1 local, 0 visitante (de MATCHUP)
    PRIMARY KEY (game_id, team_id)
);

CREATE TABLE IF NOT EXISTS games (
    game_id         TEXT PRIMARY KEY,
    season          TEXT    NOT NULL,
    season_type     TEXT    NOT NULL,
    game_date       TEXT    NOT NULL,
    home_team_id    INTEGER NOT NULL,
    home_team_abbr  TEXT    NOT NULL,
    away_team_id    INTEGER NOT NULL,
    away_team_abbr  TEXT    NOT NULL,
    home_pts        INTEGER NOT NULL,
    away_pts        INTEGER NOT NULL,
    winner_team_id  INTEGER NOT NULL,
    winner_abbr     TEXT    NOT NULL,
    home_win        INTEGER NOT NULL CHECK (home_win IN (0, 1))
);
CREATE INDEX IF NOT EXISTS idx_games_date ON games (game_date);

-- Una fila por llamada exitosa; permite reanudar sin volver a descargar.
CREATE TABLE IF NOT EXISTS fetch_log (
    season      TEXT NOT NULL,
    season_type TEXT NOT NULL,
    n_rows      INTEGER NOT NULL,
    fetched_at  TEXT NOT NULL,
    PRIMARY KEY (season, season_type)
);
"""

LOG_TABLE_COLUMNS = ["season", "season_type", *LOG_COLUMNS, "is_home"]


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    return conn


def fetched(conn: sqlite3.Connection) -> set[tuple[str, str]]:
    return set(conn.execute("SELECT season, season_type FROM fetch_log").fetchall())


def _insert(conn: sqlite3.Connection, table: str, df: pd.DataFrame, columns: list[str]) -> None:
    placeholders = ", ".join("?" * len(columns))
    rows = df[columns].astype(object).where(df[columns].notna(), None).itertuples(index=False)
    conn.executemany(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})", rows)


def replace_season(conn: sqlite3.Connection, season: str, season_type: str,
                   logs: pd.DataFrame) -> None:
    """Reemplaza atómicamente los logs de (season, season_type) y lo marca como descargado."""
    with conn:
        conn.execute("DELETE FROM team_game_logs WHERE season = ? AND season_type = ?",
                     (season, season_type))
        _insert(conn, "team_game_logs", logs, LOG_TABLE_COLUMNS)
        conn.execute(
            "INSERT OR REPLACE INTO fetch_log VALUES (?, ?, ?, ?)",
            (season, season_type, len(logs), datetime.now(timezone.utc).isoformat(timespec="seconds")),
        )


def read_logs(conn: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM team_game_logs", conn)


def replace_games(conn: sqlite3.Connection, games: pd.DataFrame) -> None:
    """La tabla `games` es derivada: se reconstruye completa desde `team_game_logs`."""
    with conn:
        conn.execute("DELETE FROM games")
        _insert(conn, "games", games, GAME_COLUMNS)
