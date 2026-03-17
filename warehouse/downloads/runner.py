"""Orchestrator: download fresh CSVs from external services before graph build.

Usage:
    uv run warehouse/downloads/runner.py --output-dir /path/to/data [--year 2026]

Environment variables:
    STRIPE_API_KEY      — required to run the Stripe downloader
    DONORBOX_EMAIL      — org login email; required to run the DonorBox downloader
    DONORBOX_API_KEY    — DonorBox API key; required to run the DonorBox downloader
"""
from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path


def run_donorbox(email: str, api_key: str, output_dir: Path, year: int) -> None:
    from donorbox import DonorBoxDownloader

    with DonorBoxDownloader(email=email, api_key=api_key, output_dir=output_dir) as dl:
        path = dl.download(year=year)
    print(f"[donorbox] wrote {path}")


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
        default=datetime.now(tz=UTC).year,
        help="Year to download (default: current year)",
    )
    args = parser.parse_args()

    donorbox_email = os.environ.get("DONORBOX_EMAIL")
    donorbox_key = os.environ.get("DONORBOX_API_KEY")
    if donorbox_email and donorbox_key:
        run_donorbox(
            email=donorbox_email,
            api_key=donorbox_key,
            output_dir=args.output_dir,
            year=args.year,
        )
    else:
        print(
            "DONORBOX_EMAIL / DONORBOX_API_KEY not set — skipping DonorBox download",
            file=sys.stderr,
        )

    stripe_key = os.environ.get("STRIPE_API_KEY")
    if stripe_key:
        run_stripe(api_key=stripe_key, output_dir=args.output_dir, year=args.year)
    else:
        print(
            "STRIPE_API_KEY not set — skipping Stripe download", file=sys.stderr
        )


if __name__ == "__main__":
    main()
