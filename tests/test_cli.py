"""End-to-end tests for the CLI, driven by a fake provider instead of the API."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from tests.conftest import StubProvider as FakeProvider
from weather import processing
from weather.cities import DEFAULT_CITIES
from weather.cli import main


def test_main_writes_csv_and_reports_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "weather_data.csv"

    exit_code = main(["--output", str(output)], provider=FakeProvider())

    assert exit_code == 0
    frame = pd.read_csv(output)
    assert list(frame.columns) == list(processing.COLUMNS)
    assert len(frame) == len(DEFAULT_CITIES)
    # Default ranking is hottest first.
    assert frame[processing.TEMP_C].is_monotonic_decreasing
    assert "New York" in capsys.readouterr().out


def test_main_keeps_going_when_some_cities_fail(tmp_path: Path) -> None:
    output = tmp_path / "weather_data.csv"

    exit_code = main(["--output", str(output)], provider=FakeProvider(broken={"Tokyo", "Paris"}))

    assert exit_code == 0
    frame = pd.read_csv(output)
    assert len(frame) == len(DEFAULT_CITIES) - 2
    assert "Tokyo" not in set(frame[processing.CITY])


def test_main_fails_when_no_city_can_be_fetched(tmp_path: Path) -> None:
    everything = {city.name for city in DEFAULT_CITIES}
    output = tmp_path / "weather_data.csv"

    exit_code = main(["--output", str(output)], provider=FakeProvider(broken=everything))

    assert exit_code == 1
    assert not output.exists()  # nothing useful to write


def test_main_honours_sort_order(tmp_path: Path) -> None:
    output = tmp_path / "weather_data.csv"

    exit_code = main(
        ["--output", str(output), "--sort-by", "temp", "--ascending"],
        provider=FakeProvider(),
    )

    assert exit_code == 0
    frame = pd.read_csv(output)
    assert frame[processing.TEMP_C].is_monotonic_increasing
    coldest = min(DEFAULT_CITIES, key=lambda city: city.latitude)
    assert frame.loc[0, processing.CITY] == coldest.name


def test_short_sort_keys_map_to_columns(tmp_path: Path) -> None:
    """`--sort-by city` must rank by the City column, not by temperature."""
    output = tmp_path / "weather_data.csv"

    exit_code = main(["--output", str(output), "--sort-by", "city"], provider=FakeProvider())

    assert exit_code == 0
    frame = pd.read_csv(output)
    assert list(frame[processing.CITY]) == sorted(
        (city.name for city in DEFAULT_CITIES), reverse=True
    )


def test_unknown_sort_column_is_rejected_by_the_parser(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        main(["--sort-by", "Pressure"], provider=FakeProvider())
