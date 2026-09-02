"""Allow running the package with ``python -m weather``."""

from __future__ import annotations

from weather.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
