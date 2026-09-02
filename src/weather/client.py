"""Data acquisition: one city's current weather, over HTTP.

Fetching *many* cities is the pipeline's job, not this module's. The rest of the
program depends on the :class:`WeatherProvider` protocol rather than on this
concrete client, so everything above it can be tested with no network stack.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from weather.models import City, Observation

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

DEFAULT_TIMEOUT = 10.0

# The fields we ask Open-Meteo for, in its own naming.
_CURRENT_FIELDS = ("temperature_2m", "relative_humidity_2m", "wind_speed_10m")


class WeatherApiError(RuntimeError):
    """Raised when a reading cannot be retrieved or understood.

    Callers never have to know whether the underlying cause was a transport
    error or a malformed payload.
    """


class WeatherProvider(Protocol):
    """Anything that can supply a current reading for a city."""

    def fetch_current(self, city: City) -> Observation: ...


class OpenMeteoClient:
    """A :class:`WeatherProvider` backed by the public Open-Meteo API."""

    def __init__(
        self,
        *,
        base_url: str = OPEN_METEO_URL,
        timeout: float = DEFAULT_TIMEOUT,
        session: requests.Session | None = None,
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._session = session or self._build_session()

    @staticmethod
    def _build_session() -> requests.Session:
        """A session that retries the failures worth retrying."""
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
        )
        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=retry))
        return session

    def fetch_current(self, city: City) -> Observation:
        """Return the current reading for ``city``.

        Raises:
            WeatherApiError: on any transport failure or unexpected payload.
        """
        params: dict[str, str | float] = {
            "latitude": city.latitude,
            "longitude": city.longitude,
            "current": ",".join(_CURRENT_FIELDS),
            "wind_speed_unit": "ms",
            "timezone": "UTC",
        }

        try:
            response = self._session.get(self._base_url, params=params, timeout=self._timeout)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise WeatherApiError(f"request for {city.name} failed: {exc}") from exc

        return self._to_observation(city, payload)

    @staticmethod
    def _to_observation(city: City, payload: Any) -> Observation:
        """Translate an API payload into our own model."""
        try:
            current = payload["current"]
            return Observation(
                city=city.name,
                temperature_c=float(current["temperature_2m"]),
                humidity_pct=float(current["relative_humidity_2m"]),
                wind_speed_ms=float(current["wind_speed_10m"]),
                observed_at=str(current["time"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise WeatherApiError(f"unexpected payload for {city.name}: {exc}") from exc


__all__: Sequence[str] = (
    "OPEN_METEO_URL",
    "OpenMeteoClient",
    "WeatherApiError",
    "WeatherProvider",
)
