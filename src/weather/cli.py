"""Command-line entry point.

This is the composition root: it parses arguments, builds the concrete provider,
hands both to the pipeline, and writes the result out. The wiring lives here so
that no other module has to know what the others are.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence

from weather import processing
from weather.cities import DEFAULT_CITIES
from weather.client import DEFAULT_TIMEOUT, OpenMeteoClient, WeatherProvider
from weather.export import write_csv
from weather.pipeline import build_report

logger = logging.getLogger("weather")

DEFAULT_OUTPUT = "weather_data.csv"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="weather",
        description="Fetch current weather for a list of cities and export it to CSV.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"CSV file to write (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--sort-by",
        default=processing.DEFAULT_SORT_KEY,
        choices=tuple(processing.SORT_KEYS),
        help="Rank cities by this measure (default: %(default)s)",
    )
    parser.add_argument(
        "--ascending",
        action="store_true",
        help="Rank low to high instead of high to low",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="Per-request timeout in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Logging verbosity (default: %(default)s)",
    )
    return parser


def main(argv: Sequence[str] | None = None, provider: WeatherProvider | None = None) -> int:
    """Run the CLI. ``provider`` is injectable so tests can skip the network."""
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=args.log_level, format="%(levelname)s %(message)s", stream=sys.stderr)

    client = provider or OpenMeteoClient(timeout=args.timeout)
    cities = DEFAULT_CITIES

    frame, failed = build_report(
        client,
        cities,
        sort_by=processing.SORT_KEYS[args.sort_by],
        ascending=args.ascending,
    )

    if frame.empty:
        logger.error("No weather data retrieved for any of the %d cities.", len(cities))
        return 1

    print(frame.to_string(index=False))
    destination = write_csv(frame, args.output)
    logger.info("Wrote %d rows to %s (%d failed).", len(frame), destination, failed)
    return 0
