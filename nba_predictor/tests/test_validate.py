from src import db
from src.games import build_games, normalize_logs
from src.validate_data import run_checks


def _results(tmp_path, raw):
    conn = db.connect(tmp_path / "nba.sqlite")
    db.replace_season(conn, "2023-24", "Regular Season", normalize_logs(raw, "2023-24", "Regular Season"))
    games, _ = build_games(db.read_logs(conn))
    db.replace_games(conn, games)
    return {name: ok for name, ok, _ in run_checks(conn, ["2023-24"])}


def test_consistent_games_pass_row_level_checks(tmp_path, raw_response):
    res = _results(tmp_path, raw_response)
    assert res["Cada game_id tiene un local y un visitante consistentes"]
    assert res["Sin nulos en fecha, marcador y ganador"]
    assert res["winner_team_id coherente con home_win"]
    assert res["Fechas dentro del año de la temporada"]
    # Muestra de 3 partidos: los chequeos de volumen deben fallar.
    assert not res["30 equipos por temporada regular"]
    assert not res["Todas las temporadas/tipos descargados"]


def test_detects_bad_rows(tmp_path, raw_response):
    raw = raw_response.copy()
    raw.loc[0, "MATCHUP"] = "LAL vs. GSW"  # dos locales en el mismo partido
    raw.loc[2, "PTS"] = 30
    res = _results(tmp_path, raw)
    assert not res["Cada game_id tiene un local y un visitante consistentes"]
    assert not res["games = game_id únicos en team_game_logs"]
    assert not res["Puntos en rango [50, 200]"]
