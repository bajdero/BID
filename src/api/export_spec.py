"""
src/api/export_spec.py
CLI helper — dump the current OpenAPI spec to docs/openapi.json.

Usage:
    python -m src.api.export_spec
    python -m src.api.export_spec --out path/to/spec.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export the BID FastAPI OpenAPI spec to a JSON file."
    )
    parser.add_argument(
        "--out",
        default="docs/openapi.json",
        help="Output path (default: docs/openapi.json)",
    )
    args = parser.parse_args()

    # Import here so the module can be imported without triggering app startup.
    from src.api.main import app  # noqa: PLC0415

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    spec = app.openapi()
    out.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    print(f"OpenAPI spec written to {out}  ({len(spec['paths'])} paths)")


if __name__ == "__main__":
    main()
