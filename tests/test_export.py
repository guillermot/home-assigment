"""Tests for CSV export."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from weather import processing
from weather.export import write_csv
from weather.models import Observation


def test_write_csv_round_trips(tmp_path: Path, observations: list[Observation]) -> None:
    frame = processing.to_dataframe(observations)

    destination = write_csv(frame, tmp_path / "weather_data.csv")
    reloaded = pd.read_csv(destination)

    assert list(reloaded.columns) == list(processing.COLUMNS)  # no stray index column
    pd.testing.assert_frame_equal(reloaded, frame)


def test_write_csv_creates_missing_directories(
    tmp_path: Path, observations: list[Observation]
) -> None:
    destination = write_csv(processing.to_dataframe(observations), tmp_path / "out" / "run.csv")

    assert destination.exists()
