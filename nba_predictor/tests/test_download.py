import sqlite3

import pytest
import requests

from src.download_gamelogs import parse_args, run
from src.nba_client import fetch_team_game_logs


def test_retry_then_success(raw_response):
    calls, waits = [], []

    def flaky(season, season_type, timeout):
        calls.append(season)
        if len(calls) < 3:
            raise requests.exceptions.ReadTimeout("timeout")
        return raw_response

    df = fetch_team_game_logs("2023-24", "Regular Season", max_retries=5,
                              endpoint=flaky, sleep=waits.append)
    assert len(df) == len(raw_response)
    assert len(calls) == 3
    assert len(waits) == 2 and waits[1] > waits[0]  # backoff creciente


def test_retry_exhausted_raises():
    def down(*_):
        raise requests.exceptions.ConnectionError("down")

    with pytest.raises(requests.exceptions.ConnectionError):
        fetch_team_game_logs("2023-24", "Playoffs", max_retries=2, endpoint=down,
                             sleep=lambda s: None)


def test_non_retryable_error_is_not_retried():
    calls = []

    def bug(*_):
        calls.append(1)
        raise TypeError("bug")

    with pytest.raises(TypeError):
        fetch_team_game_logs("2023-24", "Playoffs", max_retries=3, endpoint=bug, sleep=lambda s: None)
    assert len(calls) == 1


def _args(tmp_path, *extra):
    return parse_args(["--db", str(tmp_path / "nba.sqlite"), "--raw-dir", str(tmp_path / "raw"),
                       "--seasons", "2023-24", "--season-types", "Regular Season", "Playoffs",
                       *extra])


def test_run_end_to_end_and_resume(tmp_path, raw_response):
    fetched, pauses = [], []

    def fake_fetch(season, season_type, **_):
        fetched.append((season, season_type))
        return raw_response if season_type == "Regular Season" else raw_response.iloc[:0]

    assert run(_args(tmp_path), fetch=fake_fetch, sleep=pauses.append) == 0
    assert len(fetched) == 2 and len(pauses) == 1  # pausa entre llamadas, no antes de la primera

    conn = sqlite3.connect(tmp_path / "nba.sqlite")
    assert conn.execute("SELECT COUNT(*) FROM team_game_logs").fetchone()[0] == 6
    assert conn.execute("SELECT COUNT(*) FROM games").fetchone()[0] == 3
    assert conn.execute("SELECT COUNT(*) FROM fetch_log").fetchone()[0] == 2
    row = conn.execute("SELECT home_team_abbr, away_team_abbr, winner_abbr, game_date FROM games "
                       "WHERE game_id = '0022300003'").fetchone()
    assert row == ("LAL", "BOS", "BOS", "2023-10-26")
    conn.close()
    assert (tmp_path / "raw" / "leaguegamelog_2023-24_RegularSeason.csv").exists()

    fetched.clear()
    assert run(_args(tmp_path), fetch=fake_fetch, sleep=pauses.append) == 0
    assert fetched == []  # reanudable: no vuelve a pedir lo ya guardado

    assert run(_args(tmp_path, "--force"), fetch=fake_fetch, sleep=pauses.append) == 0
    assert len(fetched) == 2
    conn = sqlite3.connect(tmp_path / "nba.sqlite")
    assert conn.execute("SELECT COUNT(*) FROM team_game_logs").fetchone()[0] == 6  # sin duplicar


def test_run_continues_after_failure(tmp_path, raw_response):
    def fake_fetch(season, season_type, **_):
        if season_type == "Playoffs":
            raise requests.exceptions.ConnectionError("down")
        return raw_response

    assert run(_args(tmp_path), fetch=fake_fetch, sleep=lambda s: None) == 1
    conn = sqlite3.connect(tmp_path / "nba.sqlite")
    assert conn.execute("SELECT season_type FROM fetch_log").fetchall() == [("Regular Season",)]
    assert conn.execute("SELECT COUNT(*) FROM games").fetchone()[0] == 3
