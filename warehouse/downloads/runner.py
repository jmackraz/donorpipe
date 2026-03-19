"""Orchestrator: download fresh CSVs from external services before graph build.

Usage:
    uv run warehouse/downloads/runner.py --output-dir /path/to/data [--year 2026] [--services donorbox stripe paypal qbo] [--tokens-dir /path/to/tokens]

Environment variables:
    STRIPE_API_KEY      — required to run the Stripe downloader
    DONORBOX_EMAIL      — org login email; required to run the DonorBox downloader
    DONORBOX_API_KEY    — DonorBox API key; required to run the DonorBox downloader
    PAYPAL_CLIENT_ID    — required to run the PayPal downloader
    PAYPAL_SECRET_KEY   — PayPal OAuth2 secret; required to run the PayPal downloader
    QBO_CLIENT_ID       — required to run the QBO downloader
    QBO_CLIENT_SECRET   — QBO OAuth2 client secret; required to run the QBO downloader
"""
from __future__ import annotations

import os
import sys
from datetime import UTC, datetime
from pathlib import Path


def find_service_dir(output_dir: Path, service_name: str) -> Path:
    """Return a pre-existing subdirectory whose name matches service_name (case-insensitive).

    Falls back to output_dir itself if no match is found.
    """
    needle = service_name.lower()
    for entry in output_dir.iterdir():
        if entry.is_dir() and entry.name.lower() == needle:
            return entry
    return output_dir


def run_donorbox(email: str, api_key: str, output_dir: Path, year: int) -> None:
    from donorbox import DonorBoxDownloader

    service_dir = find_service_dir(output_dir, "DonorBox")
    with DonorBoxDownloader(email=email, api_key=api_key, output_dir=service_dir) as dl:
        path = dl.download(year=year)
    print(f"[donorbox] wrote {path}")


def run_paypal(client_id: str, secret_key: str, output_dir: Path, year: int) -> None:
    from paypal import PayPalDownloader

    service_dir = find_service_dir(output_dir, "Paypal")
    with PayPalDownloader(client_id=client_id, secret_key=secret_key, output_dir=service_dir) as dl:
        path = dl.download(year=year)
    print(f"[paypal] wrote {path}")


def run_qbo(
    client_id: str, client_secret: str, tokens_dir: Path, output_dir: Path, year: int
) -> None:
    from qbo import QBODownloader

    tokens_path = tokens_dir / "qbo_tokens.json"
    service_dir = find_service_dir(output_dir, "QBO")
    with QBODownloader(
        client_id=client_id,
        client_secret=client_secret,
        tokens_path=tokens_path,
        output_dir=service_dir,
    ) as dl:
        path = dl.download(year=year)
    print(f"[qbo] wrote {path}")


def run_stripe(api_key: str, output_dir: Path, year: int) -> None:
    from stripe import StripeDownloader

    service_dir = find_service_dir(output_dir, "Stripe")
    with StripeDownloader(api_key=api_key, output_dir=service_dir) as dl:
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
    parser.add_argument(
        "--services",
        nargs="+",
        metavar="SERVICE",
        choices=["donorbox", "stripe", "paypal", "qbo"],
        default=None,
        help="Services to download (default: all with credentials set). "
             "Choices: donorbox stripe paypal qbo",
    )
    parser.add_argument(
        "--tokens-dir",
        type=Path,
        default=None,
        help="Directory containing OAuth2 token files (e.g. qbo_tokens.json). "
             "Required when QBO_CLIENT_ID/QBO_CLIENT_SECRET are set.",
    )
    args = parser.parse_args()

    requested = set(args.services) if args.services else {"donorbox", "stripe", "paypal", "qbo"}

    if "donorbox" in requested:
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

    if "stripe" in requested:
        stripe_key = os.environ.get("STRIPE_API_KEY")
        if stripe_key:
            run_stripe(api_key=stripe_key, output_dir=args.output_dir, year=args.year)
        else:
            print(
                "STRIPE_API_KEY not set — skipping Stripe download", file=sys.stderr
            )

    if "paypal" in requested:
        paypal_id = os.environ.get("PAYPAL_CLIENT_ID")
        paypal_secret = os.environ.get("PAYPAL_SECRET_KEY")
        if paypal_id and paypal_secret:
            run_paypal(
                client_id=paypal_id,
                secret_key=paypal_secret,
                output_dir=args.output_dir,
                year=args.year,
            )
        else:
            print(
                "PAYPAL_CLIENT_ID / PAYPAL_SECRET_KEY not set — skipping PayPal download",
                file=sys.stderr,
            )

    if "qbo" in requested:
        qbo_id = os.environ.get("QBO_CLIENT_ID")
        qbo_secret = os.environ.get("QBO_CLIENT_SECRET")
        if qbo_id and qbo_secret:
            if args.tokens_dir is None:
                print(
                    "Error: --tokens-dir is required when QBO_CLIENT_ID/QBO_CLIENT_SECRET are set",
                    file=sys.stderr,
                )
                sys.exit(1)
            run_qbo(
                client_id=qbo_id,
                client_secret=qbo_secret,
                tokens_dir=args.tokens_dir,
                output_dir=args.output_dir,
                year=args.year,
            )
        else:
            print(
                "QBO_CLIENT_ID / QBO_CLIENT_SECRET not set — skipping QBO download",
                file=sys.stderr,
            )


if __name__ == "__main__":
    main()
