import pandas as pd
import pytest

from src.games import build_games, normalize_logs, parse_is_home
from tests.conftest import make_game


def test_parse_is_home():
    assert parse_is_home("LAL vs. BOS") == 1
    assert parse_is_home("LAL @ BOS") == 0
    assert parse_is_home("LAL - BOS") is None


def test_normalize_logs(raw_response):
    logs = normalize_logs(raw_response, "2023-24", "Regular Season")
    assert (logs["season"] == "2023-24").all()
    assert logs["game_date"].iloc[0] == "2023-10-24"
    assert "video_available" not in logs.columns
    assert logs["is_home"].tolist() == [0, 1] * 3


def test_normalize_logs_missing_column_raises(raw_response):
    with pytest.raises(KeyError, match="pts"):
        normalize_logs(raw_response.drop(columns="PTS"), "2023-24", "Regular Season")


def test_build_games_one_row_per_game(raw_response):
    games, problems = build_games(normalize_logs(raw_response, "2023-24", "Regular Season"))
    assert problems.empty
    assert len(games) == 3
    g1 = games.set_index("game_id").loc["0022300001"]
    assert (g1.home_team_abbr, g1.away_team_abbr) == ("GSW", "LAL")
    assert (g1.home_pts, g1.away_pts) == (104, 108)
    assert g1.winner_abbr == "LAL" and g1.home_win == 0
    g2 = games.set_index("game_id").loc["0022300002"]
    assert g2.winner_abbr == "BOS" and g2.home_win == 1


def test_build_games_reports_inconsistencies(raw_response):
    extra = pd.DataFrame(
        make_game("0022300010", "2023-11-01", 1610612747, 1610612738, 100, 90)[:1]  # sólo una fila
        + make_game("0022300011", "2023-11-02", 1610612744, 1610612752, 110, 100))
    extra.loc[extra["GAME_ID"] == "0022300011", "WL"] = "W"  # ambos "ganan"
    raw = pd.concat([raw_response, extra], ignore_index=True)
    games, problems = build_games(normalize_logs(raw, "2023-24", "Regular Season"))
    assert len(games) == 3
    reasons = dict(zip(problems["game_id"], problems["reason"]))
    assert reasons["0022300010"].startswith("1 filas")
    assert reasons["0022300011"] == "WL no coincide con el marcador"
