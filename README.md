# Weather Data Scraper

Fetches current weather for a list of cities from the [Open-Meteo API](https://open-meteo.com/),
processes it with `pandas`, prints a ranked table, and exports `weather_data.csv`.

```
Open-Meteo  ──▶  client.py  ──▶  processing.py  ──▶  export.py  ──▶  weather_data.csv
   (HTTP)        Observation      DataFrame +           CSV
                                  derived columns
                     └────────┬────────┘                 │
                         pipeline.py                     │
                    (failures tolerated)                 │
                              └────────────┬─────────────┘
                                        cli.py
                             (argparse + composition root)
```

## Quickstart

Requires [uv](https://docs.astral.sh/uv/) (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
It reads `.python-version` and provisions Python 3.12 itself — no manual venv needed.

```bash
uv sync          # create .venv and install dependencies
uv run weather   # fetch, display, and write weather_data.csv
```

Without uv:

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
weather
```

## Usage

```bash
uv run weather                                  # hottest city first
uv run weather --sort-by humidity --ascending   # driest city first
uv run weather --output reports/today.csv       # write elsewhere
```

| Option | Default | Purpose |
| --- | --- | --- |
| `--output PATH` | `weather_data.csv` | Where to write the CSV (directories are created) |
| `--sort-by KEY` | `temp` | Rank by `temp`, `humidity`, `wind` or `city` |
| `--ascending` | off | Rank low → high instead of high → low |
| `--timeout SECONDS` | `10` | Per-request timeout |
| `--log-level LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING` or `ERROR` |

`weather --help` lists the same options. The package also runs as `python -m weather`.

## Output

`weather_data.csv`, ranked by the chosen column:

| City | Temperature (C) | Temperature (F) | Humidity (%) | Wind Speed (m/s) | Wind Speed (mph) | Observed At (UTC) |
| --- | --- | --- | --- | --- | --- | --- |
| Tokyo | 25.9 | 78.6 | 76.0 | 0.89 | 2.0 | 2026-09-01T00:45 |
| Mumbai | 25.4 | 77.7 | 86.0 | 2.88 | 6.4 | 2026-09-01T00:45 |
| Rio de Janeiro | 24.1 | 75.4 | 89.0 | 2.63 | 5.9 | 2026-09-01T00:45 |
| … | | | | | | |
| Cape Town | 9.7 | 49.5 | 85.0 | 1.01 | 2.3 | 2026-09-01T00:45 |

The committed `weather_data.csv` is a real run of `uv run weather`.

Temperature and humidity come from the API; Fahrenheit and mph are derived
(`F = C × 9/5 + 32`, `mph = m/s × 2.236936`), rounded to one decimal place.

## Development

```bash
uv run pytest         # tests — no network access required
uv run ruff check .   # lint
uv run ruff format .  # format
uv run mypy           # strict type checking
```

## Layout

```
src/weather/
  models.py      # City / Observation / FetchFailure value objects
  cities.py      # the default 10-city list
  client.py      # WeatherProvider protocol, OpenMeteoClient — one city over HTTP
  pipeline.py    # the use case: many cities -> ranked report, failures tolerated
  processing.py  # DataFrame construction, unit conversion, ranking
  export.py      # CSV writing
  cli.py         # argparse + composition root
tests/           # pytest suite, HTTP mocked with `responses`
```

## Notes

**No `.env`.** Open-Meteo requires no API key, so there are no secrets to load
and no configuration layer to maintain.

**Retries for resiliency.** The HTTP session retries transient failures — 429 and
5xx, `GET` only — three times with exponential backoff (0s, 1s, 2s). This is
configured on the transport adapter, so no module above the client knows retries
exist. A city that still fails is recorded as a failure and the run continues
with the remaining nine; only a total failure exits non-zero.
