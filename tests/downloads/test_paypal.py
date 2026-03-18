from __future__ import annotations

import json
import os
from pathlib import Path
import pytest

from paypal import PayPalDownloader
from donorpipe.models.transaction_store import TransactionStore
from donorpipe.models.util import csv_rows

FIXTURES = Path(__file__).parent.parent / "fixtures" / "api" / "paypal"


def _fixture(name: str) -> dict:  # type: ignore[type-arg]
    return json.loads((FIXTURES / name).read_text())


def _make_downloader(output_dir: Path) -> PayPalDownloader:
    """Return a PayPalDownloader with _paginate mocked against local fixtures."""
    transactions = _fixture("transactions_month1.json")["transaction_details"]

    dl = PayPalDownloader(
        client_id="test_client_id",
        secret_key="test_secret_key",
        output_dir=output_dir,
    )
    # Pre-set token so download() skips the real _get_token() call.
    dl._token = "test_token"  # type: ignore[assignment]

    def mock_paginate(start_date: str, end_date: str) -> list[dict]:  # type: ignore[type-arg]
        # Return fixture data only for March 2025; empty for all other months.
        if "2025-03" in start_date:
            return transactions
        return []

    dl._paginate = mock_paginate  # type: ignore[method-assign]
    return dl


class TestPayPalDownloaderUnit:
    def test_writes_csv(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2025)
        assert path.exists()
        assert path.name == "paypal_2025.csv"

    def test_row_count(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2025)
        rows = list(csv_rows(str(path)))
        assert len(rows) == 3  # donation, partner fee, withdrawal

    def test_donation_fields(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2025)
        rows = {r["Transaction ID"]: r for r in csv_rows(str(path))}

        d = rows["25B16188FF732802U"]
        assert d["Type"] == "Donation Payment"
        assert d["Name"] == "Test Donor"
        assert d["From Email Address"] == "donor@example.com"
        assert float(d["Net"]) == pytest.approx(48.51)
        assert d["Gross"] == "50.00"
        assert d["Fee"] == "-1.49"
        assert d["Balance Impact"] == "Credit"
        # 2025-03-01T15:40:49Z → 07:40:49 PST (UTC-8, no DST in March)
        assert d["Date"] == "03/01/2025"
        assert d["Time"] == "07:40:49"
        assert d["TimeZone"] == "PST"
        assert d["Status"] == "Completed"

    def test_partner_fee_fields(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2025)
        rows = {r["Transaction ID"]: r for r in csv_rows(str(path))}

        f = rows["5PU95094C5021335H"]
        assert f["Type"] == "Partner Fee"
        assert f["Reference Txn ID"] == "25B16188FF732802U"
        assert f["Balance Impact"] == "Debit"
        assert float(f["Net"]) == pytest.approx(-0.88)

    def test_withdrawal_fields(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2025)
        rows = {r["Transaction ID"]: r for r in csv_rows(str(path))}

        w = rows["45X02981NP708135E"]
        assert w["Type"] == "User Initiated Withdrawal"
        assert float(w["Net"]) == pytest.approx(-47.63)
        assert w["Balance Impact"] == "Debit"
        assert w["Balance"] == "0.00"

    def test_rows_sorted_by_datetime(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2025)
        rows = list(csv_rows(str(path)))
        # donation and partner fee are at 15:40:49; withdrawal at 17:14:58
        assert rows[-1]["Transaction ID"] == "45X02981NP708135E"


class TestPayPalCSVRoundTrip:
    """Round-trip: CSV written by downloader → parsed by load_paypal_transactions()."""

    def test_entities_created(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2025)
        store = TransactionStore([str(path)])
        store.load()

        assert len(store.charges) == 1
        assert len(store.payouts) == 1

    def test_charge_payout_link(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2025)
        store = TransactionStore([str(path)])
        store.load()

        charge = store.charges.get("paypal:25B16188FF732802U")
        assert charge is not None
        assert charge.payout_tx_id == "45X02981NP708135E"

    def test_partner_fee_applied_to_charge(self, tmp_path: Path) -> None:
        path = _make_downloader(tmp_path).download(year=2025)
        store = TransactionStore([str(path)])
        store.load()

        charge = store.charges["paypal:25B16188FF732802U"]
        # Net starts at 48.51 (gross 50.00 - fee 1.49), partner fee -0.88 applied → 47.63
        assert float(charge.net) == pytest.approx(47.63)  # type: ignore[arg-type]


@pytest.mark.skipif(
    not os.getenv("LIVE_DOWNLOADS"),
    reason="set LIVE_DOWNLOADS=1 and PAYPAL_CLIENT_ID/PAYPAL_SECRET_KEY to run against real PayPal API",
)
class TestPayPalDownloaderLive:
    def test_live_download(self, tmp_path: Path) -> None:
        client_id = os.environ["PAYPAL_CLIENT_ID"]
        secret_key = os.environ["PAYPAL_SECRET_KEY"]
        with PayPalDownloader(
            client_id=client_id, secret_key=secret_key, output_dir=tmp_path
        ) as dl:
            path = dl.download(year=2025)
        assert path.exists()
        rows = list(csv_rows(str(path)))
        assert len(rows) > 0
