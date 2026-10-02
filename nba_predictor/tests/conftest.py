import pandas as pd
import pytest

TEAMS = {1610612747: ("LAL", "Los Angeles Lakers"), 1610612738: ("BOS", "Boston Celtics"),
         1610612744: ("GSW", "Golden State Warriors"), 1610612752: ("NYK", "New York Knicks")}


def _row(game_id, date, team_id, opp_id, home, pts, opp_pts, season_id="22023"):
    abbr, name = TEAMS[team_id]
    opp = TEAMS[opp_id][0]
    return {
        "SEASON_ID": season_id, "TEAM_ID": team_id, "TEAM_ABBREVIATION": abbr, "TEAM_NAME": name,
        "GAME_ID": game_id, "GAME_DATE": date,
        "MATCHUP": f"{abbr} vs. {opp}" if home else f"{abbr} @ {opp}",
        "WL": "W" if pts > opp_pts else "L", "MIN": 240, "FGM": 40, "FGA": 85, "FG_PCT": 0.47,
        "FG3M": 12, "FG3A": 35, "FG3_PCT": 0.343, "FTM": 15, "FTA": 20, "FT_PCT": 0.75,
        "OREB": 10, "DREB": 33, "REB": 43, "AST": 25, "STL": 7, "BLK": 5, "TOV": 13, "PF": 19,
        "PTS": pts, "PLUS_MINUS": pts - opp_pts, "VIDEO_AVAILABLE": 1,
    }


def make_game(game_id, date, home_id, away_id, home_pts, away_pts):
    """Las dos filas que devuelve LeagueGameLog para un partido (orden visitante, local)."""
    return [_row(game_id, date, away_id, home_id, False, away_pts, home_pts),
            _row(game_id, date, home_id, away_id, True, home_pts, away_pts)]


@pytest.fixture
def raw_response():
    rows = (make_game("0022300001", "2023-10-24", 1610612744, 1610612747, 104, 108)
            + make_game("0022300002", "2023-10-24", 1610612738, 1610612752, 115, 101)
            + make_game("0022300003", "2023-10-26", 1610612747, 1610612738, 99, 99 + 7))
    return pd.DataFrame(rows)
