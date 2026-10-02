"""Normaliza los game logs crudos y los convierte en una fila por partido."""
import pandas as pd

# Columnas de LeagueGameLog (equipos) que guardamos, en minúsculas.
LOG_COLUMNS = [
    "season_id", "team_id", "team_abbreviation", "team_name", "game_id", "game_date",
    "matchup", "wl", "min", "fgm", "fga", "fg_pct", "fg3m", "fg3a", "fg3_pct", "ftm", "fta",
    "ft_pct", "oreb", "dreb", "reb", "ast", "stl", "blk", "tov", "pf", "pts", "plus_minus",
]

GAME_COLUMNS = [
    "game_id", "season", "season_type", "game_date",
    "home_team_id", "home_team_abbr", "away_team_id", "away_team_abbr",
    "home_pts", "away_pts", "winner_team_id", "winner_abbr", "home_win",
]


def normalize_logs(raw: pd.DataFrame, season: str, season_type: str) -> pd.DataFrame:
    """Respuesta de la API -> filas para `team_game_logs` (fecha ISO, columna is_home)."""
    df = raw.rename(columns=str.lower)
    missing = set(LOG_COLUMNS) - set(df.columns)
    if missing:
        raise KeyError(f"Faltan columnas en la respuesta de la API: {sorted(missing)}")
    df = df[LOG_COLUMNS].copy()
    df.insert(0, "season", season)
    df.insert(1, "season_type", season_type)
    df["game_date"] = pd.to_datetime(df["game_date"]).dt.strftime("%Y-%m-%d")
    df["is_home"] = df["matchup"].map(parse_is_home)
    return df


def parse_is_home(matchup: str) -> int | None:
    """'LAL vs. BOS' -> 1 (LAL local); 'LAL @ BOS' -> 0 (LAL visitante); otro -> None."""
    if " vs. " in matchup:
        return 1
    if " @ " in matchup:
        return 0
    return None


def build_games(logs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Empareja las dos filas (local y visitante) de cada game_id.

    Devuelve (games, problems): `games` sólo con partidos bien formados y `problems` con
    los game_id descartados y el motivo, para revisarlos en la validación.
    """
    problems = []
    g = logs.groupby("game_id")
    sizes = g.size()
    homes = g["is_home"].apply(lambda s: (s == 1).sum())
    aways = g["is_home"].apply(lambda s: (s == 0).sum())

    bad_size = sizes[sizes != 2].index
    problems += [(gid, f"{sizes[gid]} filas (se esperaban 2)") for gid in bad_size]
    bad_sides = sizes.index[(sizes == 2) & ((homes != 1) | (aways != 1))]
    problems += [(gid, "no hay exactamente un local y un visitante") for gid in bad_sides]

    ok = logs[~logs["game_id"].isin(set(bad_size) | set(bad_sides))]
    home = ok[ok["is_home"] == 1].set_index("game_id")
    away = ok[ok["is_home"] == 0].set_index("game_id")

    games = pd.DataFrame({
        "season": home["season"],
        "season_type": home["season_type"],
        "game_date": home["game_date"],
        "home_team_id": home["team_id"],
        "home_team_abbr": home["team_abbreviation"],
        "away_team_id": away["team_id"],
        "away_team_abbr": away["team_abbreviation"],
        "home_pts": home["pts"],
        "away_pts": away["pts"],
        "home_wl": home["wl"],
        "away_wl": away["wl"],
        "away_date": away["game_date"],
    }).reset_index()

    tie = games["home_pts"] == games["away_pts"]
    wl_mismatch = ~(
        ((games["home_pts"] > games["away_pts"]) & (games["home_wl"] == "W") & (games["away_wl"] == "L"))
        | ((games["home_pts"] < games["away_pts"]) & (games["home_wl"] == "L") & (games["away_wl"] == "W"))
    )
    date_mismatch = games["game_date"] != games["away_date"]
    same_team = games["home_team_id"] == games["away_team_id"]
    for mask, reason in [(tie, "empate en el marcador"),
                         (wl_mismatch & ~tie, "WL no coincide con el marcador"),
                         (date_mismatch, "fechas distintas entre local y visitante"),
                         (same_team, "local y visitante son el mismo equipo")]:
        problems += [(gid, reason) for gid in games.loc[mask, "game_id"]]
    games = games[~(tie | wl_mismatch | date_mismatch | same_team)].copy()

    home_won = games["home_pts"] > games["away_pts"]
    games["home_win"] = home_won.astype(int)
    games["winner_team_id"] = games["home_team_id"].where(home_won, games["away_team_id"])
    games["winner_abbr"] = games["home_team_abbr"].where(home_won, games["away_team_abbr"])

    games = games[GAME_COLUMNS].sort_values(["game_date", "game_id"]).reset_index(drop=True)
    problems_df = pd.DataFrame(problems, columns=["game_id", "reason"])
    return games, problems_df
