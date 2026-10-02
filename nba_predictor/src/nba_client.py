"""Descarga de game logs de equipos desde stats.nba.com vía nba_api, con reintentos."""
import json
import logging
import random
import time
from typing import Callable

import pandas as pd
import requests

from src import config

log = logging.getLogger(__name__)

# Errores que justifican reintentar: red/timeout/HTTP y respuestas truncadas o sin el dataset.
RETRYABLE = (requests.exceptions.RequestException, json.JSONDecodeError, KeyError, IndexError)


def _default_endpoint(season: str, season_type: str, timeout: int) -> pd.DataFrame:
    from nba_api.stats.endpoints import leaguegamelog

    endpoint = leaguegamelog.LeagueGameLog(
        season=season,
        season_type_all_star=season_type,
        player_or_team_abbreviation="T",  # T = game logs de equipos (una fila por equipo y partido)
        timeout=timeout,
    )
    return endpoint.get_data_frames()[0]


def backoff_delay(attempt: int, base: float = config.BACKOFF_BASE,
                  cap: float = config.BACKOFF_MAX) -> float:
    """Espera antes del reintento `attempt` (1, 2, ...): base * 2^(attempt-1) + jitter, con tope."""
    return min(cap, base * 2 ** (attempt - 1)) + random.uniform(0, 1)


def fetch_team_game_logs(
    season: str,
    season_type: str,
    *,
    max_retries: int = config.MAX_RETRIES,
    timeout: int = config.REQUEST_TIMEOUT,
    endpoint: Callable[[str, str, int], pd.DataFrame] = _default_endpoint,
    sleep: Callable[[float], None] = time.sleep,
) -> pd.DataFrame:
    """Todos los game logs de equipos de una temporada y tipo (una llamada a la API).

    Reintenta hasta `max_retries` veces con backoff exponencial; si se agotan, relanza el
    último error para que el llamador decida (el script sigue con la siguiente temporada).
    """
    for attempt in range(max_retries + 1):
        try:
            return endpoint(season, season_type, timeout)
        except RETRYABLE as exc:
            if attempt == max_retries:
                raise
            wait = backoff_delay(attempt + 1)
            log.warning("%s %s: intento %d/%d falló (%s: %s); reintento en %.1fs",
                        season, season_type, attempt + 1, max_retries + 1,
                        type(exc).__name__, exc, wait)
            sleep(wait)
    raise AssertionError("inalcanzable")
