"""Parámetros de la Fase 1 (descarga de datos). Un solo lugar para rutas y temporadas."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "nba.sqlite"

FIRST_SEASON_START = 2016  # 2016-17
LAST_SEASON_START = 2025  # 2025-26

# Valores que acepta `season_type_all_star` en LeagueGameLog.
# PlayIn sólo existe desde 2020-21; en temporadas anteriores la API devuelve 0 filas.
SEASON_TYPES = ("Regular Season", "PlayIn", "Playoffs")

# stats.nba.com limita y a veces cuelga conexiones: pausa entre llamadas y backoff exponencial.
PAUSE_SECONDS = 2.0
PAUSE_JITTER = 1.0
REQUEST_TIMEOUT = 60
MAX_RETRIES = 5
BACKOFF_BASE = 5.0
BACKOFF_MAX = 120.0


def season_label(start_year: int) -> str:
    """2016 -> '2016-17'."""
    return f"{start_year}-{str(start_year + 1)[-2:]}"


def all_seasons() -> list[str]:
    return [season_label(y) for y in range(FIRST_SEASON_START, LAST_SEASON_START + 1)]
