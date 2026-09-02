"""The use case: many cities in, one ranked report out.

The module name is literal. ``build_report`` runs three stages in order, each
one handing its output to the next::

    fetch_all              ->  to_dataframe           ->  rank_by
    provider + cities          Observations               DataFrame
    Observations               DataFrame with the         ordered by the
    + FetchFailures            full report schema         chosen column

Stage 1 lives here because tolerating per-city failure is part of the use case;
stages 2 and 3 are delegated to `processing`, which owns the schema and the
unit conversions.

This layer knows the *order* of those stages and nothing else — no argparse, no
HTTP, no filesystem — so the whole use case can be exercised in tests with a
stub provider and no network.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence

import pandas as pd

from weather import processing
from weather.client import WeatherApiError, WeatherProvider
from weather.models import City, FetchFailure, Observation

logger = logging.getLogger(__name__)


def fetch_all(
    provider: WeatherProvider, cities: Iterable[City]
) -> tuple[list[Observation], list[FetchFailure]]:
    """Fetch every city, tolerating individual failures.

    One unreachable city should not cost us the other nine, so failures are
    returned alongside the successful readings rather than raised. Reporting
    them is the caller's decision, not ours.
    """
    observations: list[Observation] = []
    failures: list[FetchFailure] = []

    for city in cities:
        try:
            observations.append(provider.fetch_current(city))
        except WeatherApiError as exc:
            failures.append(FetchFailure(city=city.name, reason=str(exc)))

    return observations, failures


def build_report(
    provider: WeatherProvider,
    cities: Sequence[City],
    *,
    sort_by: str,
    ascending: bool = False,
) -> tuple[pd.DataFrame, int]:
    """Fetch, process and rank the cities; return the report and failure count."""
    observations, failures = fetch_all(provider, cities)

    for failure in failures:
        logger.error("Could not fetch %s: %s", failure.city, failure.reason)

    frame = processing.to_dataframe(observations)
    frame = processing.rank_by(frame, sort_by, ascending=ascending)
    return frame, len(failures)
