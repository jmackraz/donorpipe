from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
import httpx

# Column order must match what load_stripe_transactions() expects.
CSV_COLUMNS = [
    "Type",
    "Net",
    "Created (UTC)",
    "Description",
    "donorbox_name (metadata)",
    "Source",
    "Transfer",
]


class StripeDownloader:
    """Download Stripe balance transactions for a given year and write a CSV
    in the format expected by load_stripe_transactions() in transaction_store.py.

    The downloader makes two passes:
      1. Fetch all payouts + their constituent balance transactions to build
         a charge_id → payout_id mapping (used to populate the Transfer column).
      2. Fetch all balance transactions for the year (with expanded sources)
         to get donor metadata and write the final CSV rows.

    NOTE: Stripe returns payout `net` as a negative value (debit from Stripe
    balance). The value is written as-is; the operator should verify this
    matches expectations in the domain model.
    """

    _BASE_URL = "https://api.stripe.com/v1/"

    def __init__(
        self,
        api_key: str,
        output_dir: Path,
        _client: httpx.Client | None = None,
    ) -> None:
        self._client = _client or httpx.Client(
            auth=(api_key, ""),
            base_url=self._BASE_URL,
            timeout=30,
        )
        self.output_dir = output_dir

    def _paginate(self, path: str, params: dict) -> list[dict]:
        """Return all items from a paginated Stripe list endpoint."""
        items: list[dict] = []
        p = dict(params)
        while True:
            r = self._client.get(path, params=p)
            r.raise_for_status()
            data = r.json()
            items.extend(data["data"])
            if not data["has_more"]:
                break
            p["starting_after"] = data["data"][-1]["id"]
        return items

    @staticmethod
    def _year_bounds(year: int) -> tuple[int, int]:
        start = int(datetime(year, 1, 1, tzinfo=timezone.utc).timestamp())
        end = int(datetime(year + 1, 1, 1, tzinfo=timezone.utc).timestamp()) - 1
        return start, end

    def download(self, year: int) -> Path:
        """Download all Stripe transactions for *year* and write stripe_{year}.csv.

        Returns the path to the written file.
        """
        start, end = self._year_bounds(year)
        output_path = self.output_dir / f"stripe_{year}.csv"

        # Pass 1: fetch payouts + build charge_id → payout_id mapping.
        # Extend the payout window 30 days past year-end so that charges made
        # in late December (which settle in early January) still get mapped.
        charge_to_payout: dict[str, str] = {}
        payout_items: list[dict] = self._paginate(
            "payouts",
            {"created[gte]": start, "created[lte]": end + 30 * 86400, "limit": 100},
        )
        for payout in payout_items:
            payout_id = payout["id"]
            for bt in self._paginate(
                "balance_transactions",
                {"payout": payout_id, "limit": 100},
            ):
                if bt["type"] in ("charge", "payment"):
                    src = bt["source"]
                    src_id = src["id"] if isinstance(src, dict) else src
                    charge_to_payout[src_id] = payout_id

        # Pass 2: fetch all balance transactions for the year with expanded sources.
        all_bt: list[dict] = self._paginate(
            "balance_transactions",
            {
                "created[gte]": start,
                "created[lte]": end,
                "limit": 100,
                "expand[]": "data.source",
            },
        )

        rows: list[dict[str, str]] = []
        for bt in all_bt:
            tx_type = bt["type"]
            src = bt["source"]
            src_id = src["id"] if isinstance(src, dict) else src
            net_dollars = bt["net"] / 100.0
            created_str = datetime.fromtimestamp(
                bt["created"], tz=timezone.utc
            ).strftime("%Y-%m-%d %H:%M:%S")

            if tx_type in ("charge", "payment"):
                metadata = src.get("metadata", {}) if isinstance(src, dict) else {}
                rows.append(
                    {
                        "Type": tx_type,
                        "Net": f"{net_dollars:.2f}",
                        "Created (UTC)": created_str,
                        "Description": bt.get("description") or "",
                        "donorbox_name (metadata)": metadata.get("donorbox_name", ""),
                        "Source": src_id,
                        "Transfer": charge_to_payout.get(src_id, ""),
                    }
                )
            elif tx_type == "payout":
                rows.append(
                    {
                        "Type": "payout",
                        "Net": f"{net_dollars:.2f}",
                        "Created (UTC)": created_str,
                        "Description": bt.get("description") or "",
                        "donorbox_name (metadata)": "",
                        "Source": src_id,
                        "Transfer": "",
                    }
                )
            # Other types (refund, fee, adjustment, etc.) are skipped.

        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

        return output_path

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> StripeDownloader:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
