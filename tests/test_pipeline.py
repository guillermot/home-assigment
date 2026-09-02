"""Tests for the orchestration layer: many cities in, one ranked report out."""

from __future__ import annotations

import logging

import pytest

from tests.conftest import NEW_YORK, TOKYO, StubProvider
from weather import processing
from weather.cities import DEFAULT_CITIES
from weather.client import WeatherProvider
from weather.pipeline import build_report, fetch_all


def test_fetch_all_returns_readings_and_failures() -> None:
    provider: WeatherProvider = StubProvider(broken={"Tokyo"})

    observations, failures = fetch_all(provider, [NEW_YORK, TOKYO])

    assert [obs.city for obs in observations] == ["New York"]
    assert [failure.city for failure in failures] == ["Tokyo"]
    assert "boom for Tokyo" in failures[0].reason


def test_fetch_all_with_no_cities_is_empty() -> None:
    assert fetch_all(StubProvider(), []) == ([], [])


def test_fetch_all_does_not_log(caplog: pytest.LogCaptureFixture) -> None:
    """Reporting is the caller's job; a failure must not be logged twice."""
    with caplog.at_level(logging.DEBUG):
        fetch_all(StubProvider(broken={"Tokyo"}), [NEW_YORK, TOKYO])

    assert caplog.records == []


def test_build_report_logs_each_failure_exactly_once(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.DEBUG):
        _, failed = build_report(
            StubProvider(broken={"Tokyo"}), [NEW_YORK, TOKYO], sort_by=processing.TEMP_C
        )

    assert failed == 1
    assert len(caplog.records) == 1
    assert "Tokyo" in caplog.records[0].message


def test_build_report_ranks_hottest_first() -> None:
    frame, failed = build_report(StubProvider(), DEFAULT_CITIES, sort_by=processing.TEMP_C)

    assert failed == 0
    assert len(frame) == len(DEFAULT_CITIES)
    assert frame[processing.TEMP_C].is_monotonic_decreasing


def test_build_report_ranks_ascending_when_asked() -> None:
    frame, _ = build_report(
        StubProvider(), DEFAULT_CITIES, sort_by=processing.TEMP_C, ascending=True
    )

    coldest = min(DEFAULT_CITIES, key=lambda city: city.latitude)
    assert frame[processing.TEMP_C].is_monotonic_increasing
    assert frame.loc[0, processing.CITY] == coldest.name


def test_build_report_of_total_failure_is_empty_but_well_formed() -> None:
    """The all-failures path must still produce a sortable, exportable frame."""
    everything = {city.name for city in DEFAULT_CITIES}

    frame, failed = build_report(
        StubProvider(broken=everything), DEFAULT_CITIES, sort_by=processing.TEMP_C
    )

    assert failed == len(DEFAULT_CITIES)
    assert frame.empty
    assert list(frame.columns) == list(processing.COLUMNS)
