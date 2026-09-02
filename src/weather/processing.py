"""Data processing: observations in, report-shaped DataFrame out.

Every function here is pure — no network, no filesystem — which makes the
numeric behaviour cheap to test and safe to reuse.
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from weather.models import Observation

# Column names follow the exercise's example output. `Observed At (UTC)` is an
# addition: a scraped dataset is hard to interpret without knowing when it was
# taken.
CITY = "City"
TEMP_C = "Temperature (C)"
TEMP_F = "Temperature (F)"
HUMIDITY = "Humidity (%)"
WIND_MS = "Wind Speed (m/s)"
WIND_MPH = "Wind Speed (mph)"
OBSERVED_AT = "Observed At (UTC)"

COLUMNS: tuple[str, ...] = (
    CITY,
    TEMP_C,
    TEMP_F,
    HUMIDITY,
    WIND_MS,
    WIND_MPH,
    OBSERVED_AT,
)

# Short, shell-friendly names for the orderings worth offering. Only four of the
# seven columns rank differently: Fahrenheit sorts identically to Celsius and mph
# to m/s (both are linear transforms), and every row in a run shares one
# timestamp, so sorting by it does nothing.
SORT_KEYS: dict[str, str] = {
    "temp": TEMP_C,
    "humidity": HUMIDITY,
    "wind": WIND_MS,
    "city": CITY,
}

DEFAULT_SORT_KEY = "temp"

# The API reports metric only, so the imperial columns are derived here.
# Conversion factors are defined once, then reused by `_add_derived_columns`.
_MS_TO_MPH = 2.236936  # metres per second -> miles per hour
_C_TO_F_SCALE = 9 / 5  # Celsius -> Fahrenheit, step 1: scale the degree size
_C_TO_F_OFFSET = 32.0  # Celsius -> Fahrenheit, step 2: shift the freezing point

_DECIMALS = 1


def to_dataframe(observations: Iterable[Observation]) -> pd.DataFrame:
    """Build a DataFrame with the full report schema.

    An empty input still yields every column, so downstream sorting and export
    behave the same whether or not any city responded.
    """
    rows = []
    for obs in observations:
        rows.append(
            {
                CITY: obs.city,
                TEMP_C: obs.temperature_c,
                HUMIDITY: obs.humidity_pct,
                WIND_MS: obs.wind_speed_ms,
                OBSERVED_AT: obs.observed_at,
            }
        )
    frame = pd.DataFrame(rows, columns=[CITY, TEMP_C, HUMIDITY, WIND_MS, OBSERVED_AT])
    return _add_derived_columns(frame)


def _add_derived_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Add the imperial-unit columns, returning a new DataFrame."""
    result = frame.copy()  # assigning columns below would otherwise mutate the caller's frame
    result[TEMP_F] = (result[TEMP_C] * _C_TO_F_SCALE + _C_TO_F_OFFSET).round(_DECIMALS)
    result[WIND_MPH] = (result[WIND_MS] * _MS_TO_MPH).round(_DECIMALS)
    return result.reindex(columns=list(COLUMNS))


def rank_by(frame: pd.DataFrame, column: str, *, ascending: bool = False) -> pd.DataFrame:
    """Sort by ``column`` — hottest first by default — and renumber the rows.

    Raises:
        KeyError: if ``column`` is not part of the report.
    """
    if column not in frame.columns:
        raise KeyError(f"unknown column {column!r}; expected one of {list(frame.columns)}")
    return frame.sort_values(column, ascending=ascending).reset_index(drop=True)
