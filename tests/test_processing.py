"""Tests for the pandas processing step."""

from __future__ import annotations

import pandas as pd
import pytest

from weather import processing
from weather.models import Observation


def test_to_dataframe_has_the_documented_schema(observations: list[Observation]) -> None:
    frame = processing.to_dataframe(observations)

    assert list(frame.columns) == list(processing.COLUMNS)
    assert len(frame) == len(observations)


def test_to_dataframe_of_nothing_keeps_the_schema() -> None:
    """An all-failures run must still produce a sortable, exportable frame."""
    frame = processing.to_dataframe([])

    assert frame.empty
    assert list(frame.columns) == list(processing.COLUMNS)


@pytest.mark.parametrize(
    ("celsius", "expected_fahrenheit"),
    [(0.0, 32.0), (100.0, 212.0), (-40.0, -40.0), (12.0, 53.6), (37.0, 98.6)],
)
def test_celsius_converts_to_fahrenheit(celsius: float, expected_fahrenheit: float) -> None:
    frame = processing.to_dataframe([Observation("X", celsius, 50.0, 1.0, "t")])

    assert frame.loc[0, processing.TEMP_F] == pytest.approx(expected_fahrenheit)


@pytest.mark.parametrize(
    ("ms", "expected_mph"),
    [(0.0, 0.0), (1.0, 2.2), (5.0, 11.2), (3.0, 6.7), (4.0, 8.9)],
)
def test_metres_per_second_convert_to_mph(ms: float, expected_mph: float) -> None:
    """The expectations are the exercise's own example figures."""
    frame = processing.to_dataframe([Observation("X", 10.0, 50.0, ms, "t")])

    assert frame.loc[0, processing.WIND_MPH] == pytest.approx(expected_mph)


def test_add_derived_columns_does_not_mutate_its_input() -> None:
    original = pd.DataFrame(
        {
            processing.CITY: ["X"],
            processing.TEMP_C: [10.0],
            processing.HUMIDITY: [50.0],
            processing.WIND_MS: [1.0],
            processing.OBSERVED_AT: ["t"],
        }
    )

    processing._add_derived_columns(original)

    assert processing.TEMP_F not in original.columns


def test_rank_by_orders_hottest_first(observations: list[Observation]) -> None:
    frame = processing.to_dataframe(observations)

    ranked = processing.rank_by(frame, processing.TEMP_C)

    assert list(ranked[processing.CITY]) == ["Cairo", "London", "Oslo"]
    assert list(ranked.index) == [0, 1, 2]  # index is renumbered after sorting


def test_rank_by_ascending_finds_the_driest(observations: list[Observation]) -> None:
    frame = processing.to_dataframe(observations)

    ranked = processing.rank_by(frame, processing.HUMIDITY, ascending=True)

    assert list(ranked[processing.CITY]) == ["Cairo", "London", "Oslo"]


def test_rank_by_unknown_column_is_rejected(observations: list[Observation]) -> None:
    frame = processing.to_dataframe(observations)

    with pytest.raises(KeyError, match="unknown column"):
        processing.rank_by(frame, "Pressure")
