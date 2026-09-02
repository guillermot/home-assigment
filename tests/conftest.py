"""Shared fixtures.

``NEW_YORK_PAYLOAD`` is a real response captured from Open-Meteo, so the
parsing tests are pinned to the shape the API actually returns.
"""

from __future__ import annotations

from typing import Any

import pytest

from weather.client import WeatherApiError
from weather.models import City, Observation

NEW_YORK = City("New York", 40.7128, -74.0060)
TOKYO = City("Tokyo", 35.6895, 139.6917)


class StubProvider:
    """A ``WeatherProvider`` that never touches the network.

    Returns a deterministic reading per city and raises for the cities named in
    ``broken``, which is what lets the pipeline and CLI tests drive every path.
    """

    def __init__(self, broken: set[str] | None = None) -> None:
        self.broken = broken or set()

    def fetch_current(self, city: City) -> Observation:
        if city.name in self.broken:
            raise WeatherApiError(f"boom for {city.name}")
        # Latitude gives each city a distinct, predictable temperature.
        return Observation(city.name, city.latitude, 50.0, 3.0, "2026-09-01T00:00")


NEW_YORK_PAYLOAD: dict[str, Any] = {
    "latitude": 40.710335,
    "longitude": -73.99308,
    "timezone": "GMT",
    "current_units": {
        "time": "iso8601",
        "temperature_2m": "°C",
        "relative_humidity_2m": "%",
        "wind_speed_10m": "m/s",
    },
    "current": {
        "time": "2026-09-01T00:00",
        "interval": 900,
        "temperature_2m": 21.4,
        "relative_humidity_2m": 88,
        "wind_speed_10m": 1.86,
    },
}


@pytest.fixture
def new_york_payload() -> dict[str, Any]:
    return NEW_YORK_PAYLOAD


@pytest.fixture
def observations() -> list[Observation]:
    """Three readings with deliberately distinct temperatures and humidity."""
    return [
        Observation("London", 12.0, 70.0, 4.0, "2026-09-01T00:00"),
        Observation("Cairo", 35.0, 20.0, 2.0, "2026-09-01T00:00"),
        Observation("Oslo", 3.0, 90.0, 6.0, "2026-09-01T00:00"),
    ]
