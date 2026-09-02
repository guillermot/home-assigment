"""Persistence: writing the report out."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_csv(frame: pd.DataFrame, path: str | Path) -> Path:
    """Write ``frame`` to ``path`` as CSV and return the resolved path.

    Parent directories are created so ``--output reports/today.csv`` works
    without extra setup.
    """
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination, index=False)
    return destination
