from __future__ import annotations

import json
import os
from pathlib import Path
import pytest

from stripe import StripeDownloader
from donorpipe.models.transaction_store import TransactionStore
from donorpipe.models.util import csv_rows

FIXTURES = Path(__file__).parent.parent / "fixtures" / "api" / "stripe"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def _make_downloader(output_dir: Path) -> StripeDownloader:
    """Return a StripeDownloader with _paginate mocked against local fixtures."""
    payouts = _fixture("payouts_page1.json")["data"]
    bt_for_payout = _fixture("balance_transactions_payout.json")["data"]
    bt_all = _fixture("balance_transactions_all.json")["data"]

    dl = StripeDownloader(api_key="sk_test_fake", output_dir=output_dir)

    def mock_paginate(path: str, params: dict) -> list[dict]:
        if path == "payouts":
            return payouts
        elif "payout" in params:
            return bt_for_payout
        else:
            return bt_all

    dl._paginate = mock_paginate  # type: ignore[method-assign]
    return dl


class TestStripeDownloaderUnit:
    def test_writes_csv(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2026)
        assert path.exists()
        assert path.name == "stripe_2026.csv"

    def test_row_count(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2026)
        rows = list(csv_rows(str(path)))
        assert len(rows) == 3  # 2 charges + 1 payout

    def test_charge_fields(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2026)
        rows = {r["Source"]: r for r in csv_rows(str(path))}

        ch = rows["ch_1aaa"]
        assert ch["Type"] == "charge"
        assert ch["Transfer"] == "po_1test"
        assert ch["donorbox_name (metadata)"] == "Jane Sample"
        assert float(ch["Net"]) == pytest.approx(97.11)

    def test_payment_fields(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2026)
        rows = {r["Source"]: r for r in csv_rows(str(path))}

        p = rows["ch_1bbb"]
        assert p["Type"] == "payment"
        assert p["Transfer"] == "po_1test"
        assert p["donorbox_name (metadata)"] == "John Doe"

    def test_payout_fields(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2026)
        rows = {r["Source"]: r for r in csv_rows(str(path))}

        po = rows["po_1test"]
        assert po["Type"] == "payout"
        assert po["Transfer"] == ""


class TestStripeCSVRoundTrip:
    """Round-trip: CSV written by downloader → parsed by load_stripe_transactions()."""

    def test_entities_created(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2026)
        store = TransactionStore([str(path)])
        store.load()

        assert len(store.charges) == 2
        assert len(store.payouts) == 1

    def test_charge_payout_link(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2026)
        store = TransactionStore([str(path)])
        store.load()

        charge = store.charges["stripe:ch_1aaa"]
        assert charge.payout_tx_id == "po_1test"
        assert charge.name == "Jane Sample"

    def test_payout_tx_id(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2026)
        store = TransactionStore([str(path)])
        store.load()

        assert "stripe:po_1test" in store.payouts


@pytest.mark.skipif(
    not os.getenv("LIVE_DOWNLOADS"),
    reason="set LIVE_DOWNLOADS=1 and STRIPE_API_KEY to run against real Stripe API",
)
class TestStripeDownloaderLive:
    def test_live_download(self, tmp_path: Path) -> None:
        api_key = os.environ["STRIPE_API_KEY"]
        with StripeDownloader(api_key=api_key, output_dir=tmp_path) as dl:
            path = dl.download(year=2025)
        assert path.exists()
        rows = list(csv_rows(str(path)))
        assert len(rows) > 0
