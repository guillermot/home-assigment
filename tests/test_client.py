"""Tests for the Open-Meteo client. No test here touches the network."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
import responses

from tests.conftest import NEW_YORK
from weather.client import OPEN_METEO_URL, OpenMeteoClient, WeatherApiError
from weather.models import Observation


@responses.activate
def test_fetch_current_parses_payload(new_york_payload: dict[str, Any]) -> None:
    responses.add(responses.GET, OPEN_METEO_URL, json=new_york_payload, status=200)

    observation = OpenMeteoClient().fetch_current(NEW_YORK)

    assert observation == Observation(
        city="New York",
        temperature_c=21.4,
        humidity_pct=88.0,
        wind_speed_ms=1.86,
        observed_at="2026-09-01T00:00",
    )


@responses.activate
def test_fetch_current_requests_metres_per_second(new_york_payload: dict[str, Any]) -> None:
    """Open-Meteo defaults to km/h, so the unit override must be sent."""
    responses.add(responses.GET, OPEN_METEO_URL, json=new_york_payload, status=200)

    OpenMeteoClient().fetch_current(NEW_YORK)

    url = responses.calls[0].request.url
    assert url is not None
    query = parse_qs(urlparse(url).query)
    assert query["wind_speed_unit"] == ["ms"]
    assert query["current"] == ["temperature_2m,relative_humidity_2m,wind_speed_10m"]
    assert query["latitude"] == ["40.7128"]


@responses.activate
def test_http_error_raises_weather_api_error() -> None:
    responses.add(responses.GET, OPEN_METEO_URL, json={"error": True}, status=500)

    # Retries are configured, so a persistent 500 still ends as our own error.
    with pytest.raises(WeatherApiError, match="New York"):
        OpenMeteoClient().fetch_current(NEW_YORK)


@responses.activate
@pytest.mark.parametrize(
    "payload",
    [
        {},  # no "current" block at all
        {"current": {"time": "2026-09-01T00:00"}},  # measurements missing
        {"current": {"time": "x", "temperature_2m": "warm"}},  # unparseable value
    ],
    ids=["no-current", "missing-fields", "bad-value"],
)
def test_malformed_payload_raises_weather_api_error(payload: dict[str, Any]) -> None:
    responses.add(responses.GET, OPEN_METEO_URL, json=payload, status=200)

    with pytest.raises(WeatherApiError, match="unexpected payload"):
        OpenMeteoClient().fetch_current(NEW_YORK)
