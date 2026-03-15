"""Orchestrator: download fresh CSVs from external services before graph build.

Usage:
    uv run warehouse/downloads/runner.py --output-dir /path/to/data [--year 2026]

Environment variables:
    STRIPE_API_KEY  — required to run the Stripe downloader
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_stripe(api_key: str, output_dir: Path, year: int) -> None:
    from stripe import StripeDownloader

    with StripeDownloader(api_key=api_key, output_dir=output_dir) as dl:
        path = dl.download(year=year)
    print(f"[stripe] wrote {path}")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Download transaction CSVs from external services."
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory to write CSV files (account data_base directory)",
    )
    parser.add_argument(
        "--year",
        type=int,
        default=datetime.now(tz=timezone.utc).year,
        help="Year to download (default: current year)",
    )
    args = parser.parse_args()

    stripe_key = os.environ.get("STRIPE_API_KEY")
    if stripe_key:
        run_stripe(api_key=stripe_key, output_dir=args.output_dir, year=args.year)
    else:
        print(
            "STRIPE_API_KEY not set — skipping Stripe download", file=sys.stderr
        )


if __name__ == "__main__":
    main()
