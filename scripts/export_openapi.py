"""Export the FastAPI contract used to generate frontend API types."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.app.main import app


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("frontend/openapi.json"),
    )
    args = parser.parse_args()
    args.output.write_text(
        json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
