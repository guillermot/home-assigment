"""Immutable value objects shared across the package.

These carry data only: no I/O, no pandas, no knowledge of where the numbers
came from. Keeping them dependency-free lets every other module depend on
them without creating cycles.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class City:
    """A location to request weather for."""

    name: str
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class Observation:
    """One current-weather reading, in the API's source units."""

    city: str
    temperature_c: float
    humidity_pct: float
    wind_speed_ms: float
    observed_at: str


@dataclass(frozen=True, slots=True)
class FetchFailure:
    """A city whose reading could not be retrieved, and why."""

    city: str
    reason: str
