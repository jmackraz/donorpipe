from __future__ import annotations

import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from qbo import QBODownloader
from donorpipe.models.transaction_store import TransactionStore
from donorpipe.models.util import csv_rows

FIXTURES = Path(__file__).parent.parent / "fixtures" / "api" / "qbo"


def _fixture(name: str) -> dict:  # type: ignore[type-arg]
    return json.loads((FIXTURES / name).read_text())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _future_expiry(hours: int = 1) -> str:
    return (datetime.now(tz=UTC) + timedelta(hours=hours)).isoformat()


def _past_expiry(minutes: int = 10) -> str:
    return (datetime.now(tz=UTC) - timedelta(minutes=minutes)).isoformat()


def _write_tokens(path: Path, **overrides: str) -> None:
    tokens = {
        "realm_id": "test_realm",
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "token_expiry": _future_expiry(),
        **overrides,
    }
    path.write_text(json.dumps(tokens))


def _make_downloader(
    tokens_path: Path,
    output_dir: Path,
    _client=None,
) -> QBODownloader:
    return QBODownloader(
        client_id="test_client_id",
        client_secret="test_client_secret",
        tokens_path=tokens_path,
        output_dir=output_dir,
        _client=_client,
    )


def _make_download_downloader(tmp_path: Path) -> QBODownloader:
    """Return a downloader with _fetch_receipts mocked against local fixtures."""
    tokens_path = tmp_path / "qbo_tokens.json"
    _write_tokens(tokens_path)
    receipts = _fixture("receipts_2025.json")["QueryResponse"]["SalesReceipt"]

    dl = _make_downloader(tokens_path, tmp_path)

    def mock_fetch(realm_id: str, token: str, year: int) -> list[dict]:  # type: ignore[type-arg]
        return receipts if year == 2025 else []

    dl._fetch_receipts = mock_fetch  # type: ignore[method-assign]
    return dl


# ---------------------------------------------------------------------------
# Mock HTTP client (for token tests)
# ---------------------------------------------------------------------------

class _MockResponse:
    def __init__(self, status_code: int, body: dict) -> None:  # type: ignore[type-arg]
        self.status_code = status_code
        self._body = body
        self.is_success = 200 <= status_code < 300

    def json(self) -> dict:  # type: ignore[type-arg]
        return self._body


class _MockClient:
    """Minimal httpx.Client stand-in for token refresh tests."""

    def __init__(self, response: _MockResponse) -> None:
        self._response = response
        self.last_post_kwargs: dict = {}  # type: ignore[type-arg]

    def post(self, url: str, **kwargs: object) -> _MockResponse:
        self.last_post_kwargs = {"url": url, **kwargs}
        return self._response

    def close(self) -> None:
        pass


# ---------------------------------------------------------------------------
# Token load tests
# ---------------------------------------------------------------------------

class TestTokenLoad:
    def test_missing_file_raises(self, tmp_path: Path) -> None:
        dl = _make_downloader(tmp_path / "qbo_tokens.json", tmp_path)
        with pytest.raises(RuntimeError, match="QBO tokens file not found"):
            dl._load_tokens()

    def test_valid_file_returns_dict(self, tmp_path: Path) -> None:
        tokens_path = tmp_path / "qbo_tokens.json"
        _write_tokens(tokens_path)
        dl = _make_downloader(tokens_path, tmp_path)
        tokens = dl._load_tokens()
        assert tokens["realm_id"] == "test_realm"
        assert tokens["access_token"] == "test_access_token"


# ---------------------------------------------------------------------------
# Token refresh / ensure_valid_token tests
# ---------------------------------------------------------------------------

class TestEnsureValidToken:
    def test_valid_token_returned_without_refresh(self, tmp_path: Path) -> None:
        tokens_path = tmp_path / "qbo_tokens.json"
        _write_tokens(tokens_path, token_expiry=_future_expiry(hours=2))
        dl = _make_downloader(tokens_path, tmp_path)
        tokens = dl._load_tokens()
        result = dl._ensure_valid_token(tokens)
        assert result == "test_access_token"
        on_disk = json.loads(tokens_path.read_text())
        assert on_disk["access_token"] == "test_access_token"

    def test_expired_token_triggers_refresh(self, tmp_path: Path) -> None:
        tokens_path = tmp_path / "qbo_tokens.json"
        _write_tokens(tokens_path, token_expiry=_past_expiry())

        refresh_response = _MockResponse(200, {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": "3600",
        })
        mock_client = _MockClient(refresh_response)
        dl = _make_downloader(tokens_path, tmp_path, _client=mock_client)

        tokens = dl._load_tokens()
        result = dl._ensure_valid_token(tokens)

        assert result == "new_access_token"
        on_disk = json.loads(tokens_path.read_text())
        assert on_disk["access_token"] == "new_access_token"
        assert on_disk["refresh_token"] == "new_refresh_token"
        assert on_disk["realm_id"] == "test_realm"

    def test_near_expiry_token_triggers_refresh(self, tmp_path: Path) -> None:
        tokens_path = tmp_path / "qbo_tokens.json"
        expiry = (datetime.now(tz=UTC) + timedelta(minutes=2)).isoformat()
        _write_tokens(tokens_path, token_expiry=expiry)

        refresh_response = _MockResponse(200, {
            "access_token": "refreshed_token",
            "refresh_token": "new_refresh_token",
            "expires_in": "3600",
        })
        dl = _make_downloader(tokens_path, tmp_path, _client=_MockClient(refresh_response))
        tokens = dl._load_tokens()
        result = dl._ensure_valid_token(tokens)
        assert result == "refreshed_token"

    def test_refresh_failure_raises_runtime_error(self, tmp_path: Path) -> None:
        tokens_path = tmp_path / "qbo_tokens.json"
        _write_tokens(tokens_path, token_expiry=_past_expiry())

        error_response = _MockResponse(401, {"error": "invalid_grant"})
        dl = _make_downloader(tokens_path, tmp_path, _client=_MockClient(error_response))

        tokens = dl._load_tokens()
        with pytest.raises(RuntimeError, match="QBO token refresh failed"):
            dl._ensure_valid_token(tokens)

    def test_refresh_failure_message_mentions_playground(self, tmp_path: Path) -> None:
        tokens_path = tmp_path / "qbo_tokens.json"
        _write_tokens(tokens_path, token_expiry=_past_expiry())

        error_response = _MockResponse(400, {"error": "invalid_grant"})
        dl = _make_downloader(tokens_path, tmp_path, _client=_MockClient(error_response))

        tokens = dl._load_tokens()
        with pytest.raises(RuntimeError, match="Playground"):
            dl._ensure_valid_token(tokens)

    def test_missing_expiry_triggers_refresh(self, tmp_path: Path) -> None:
        """qbo_tokens.json with no token_expiry field → refresh on first use."""
        tokens_path = tmp_path / "qbo_tokens.json"
        _write_tokens(tokens_path)
        # Remove token_expiry to simulate a freshly bootstrapped file
        tokens = json.loads(tokens_path.read_text())
        del tokens["token_expiry"]
        tokens_path.write_text(json.dumps(tokens))

        refresh_response = _MockResponse(200, {
            "access_token": "bootstrapped_token",
            "refresh_token": "new_refresh_token",
            "expires_in": "3600",
        })
        dl = _make_downloader(tokens_path, tmp_path, _client=_MockClient(refresh_response))
        tokens = dl._load_tokens()
        result = dl._ensure_valid_token(tokens)
        assert result == "bootstrapped_token"
        on_disk = json.loads(tokens_path.read_text())
        assert "token_expiry" in on_disk  # expiry written after first refresh

    def test_refresh_writes_atomic_tmp_then_replace(self, tmp_path: Path) -> None:
        tokens_path = tmp_path / "qbo_tokens.json"
        _write_tokens(tokens_path, token_expiry=_past_expiry())

        refresh_response = _MockResponse(200, {
            "access_token": "new_token",
            "refresh_token": "new_refresh",
            "expires_in": "3600",
        })
        dl = _make_downloader(tokens_path, tmp_path, _client=_MockClient(refresh_response))
        tokens = dl._load_tokens()
        dl._ensure_valid_token(tokens)

        assert not tokens_path.with_suffix(".tmp").exists()
        assert tokens_path.exists()


# ---------------------------------------------------------------------------
# Download / CSV output tests
# ---------------------------------------------------------------------------

class TestQBODownloaderUnit:
    def test_writes_csv(self, tmp_path: Path) -> None:
        path = _make_download_downloader(tmp_path).download(year=2025)
        assert path.exists()
        assert path.name == "QBO_from_2025.csv"

    def test_row_count(self, tmp_path: Path) -> None:
        path = _make_download_downloader(tmp_path).download(year=2025)
        # Receipt 1: 1 SalesItemLineDetail line. Receipt 2: 2. Total: 3 data rows.
        # (csv_rows does not stop at TOTAL — exclude it manually here)
        rows = [r for r in csv_rows(str(path), skip=4) if "TOTAL" not in ",".join(r.values())]
        assert len(rows) == 3

    def test_single_line_receipt_fields(self, tmp_path: Path) -> None:
        path = _make_download_downloader(tmp_path).download(year=2025)
        rows = {r["Num"]: r for r in csv_rows(str(path), skip=4)}

        r = rows["5001"]
        assert r["Donor"] == "Alice Donor"
        assert r["Transaction date"] == "06/01/2025"
        assert r["Product/Service full name"] == "Annual Fund"
        assert r["Amount"] == "250.00"
        assert r["REF #"] == "REF001"
        assert r["Line created date"] == "06/01/2025 10:00:00 AM"

    def test_item_class_leaf_extracted(self, tmp_path: Path) -> None:
        path = _make_download_downloader(tmp_path).download(year=2025)
        rows = {r["Num"]: r for r in csv_rows(str(path), skip=4)}
        # "30-Program:Kenya:Women's Work Center" → "Women's Work Center"
        assert rows["5001"]["Item class"] == "Women's Work Center"

    def test_multi_line_receipt_produces_two_rows(self, tmp_path: Path) -> None:
        path = _make_download_downloader(tmp_path).download(year=2025)
        all_rows = list(csv_rows(str(path), skip=4))
        rows_5002 = [r for r in all_rows if r["Num"] == "5002"]
        assert len(rows_5002) == 2

    def test_subtotal_lines_skipped(self, tmp_path: Path) -> None:
        """SubTotalLineDetail rows must not appear in output."""
        path = _make_download_downloader(tmp_path).download(year=2025)
        rows = list(csv_rows(str(path), skip=4))
        assert all(r["Donor"] != "" for r in rows)

    def test_missing_class_ref_defaults_to_empty(self, tmp_path: Path) -> None:
        """Line without ClassRef → empty Item class."""
        path = _make_download_downloader(tmp_path).download(year=2025)
        all_rows = list(csv_rows(str(path), skip=4))
        # Receipt 5002 line 2 ("General Operations") has no ClassRef
        ops_row = next(r for r in all_rows if r["Product/Service full name"] == "General Operations")
        assert ops_row["Item class"] == ""

    def test_rows_sorted_by_date(self, tmp_path: Path) -> None:
        path = _make_download_downloader(tmp_path).download(year=2025)
        rows = [r for r in csv_rows(str(path), skip=4) if r["Transaction date"]]
        dates = [datetime.strptime(r["Transaction date"], "%m/%d/%Y") for r in rows]
        assert dates == sorted(dates)

    def test_csv_four_line_header(self, tmp_path: Path) -> None:
        path = _make_download_downloader(tmp_path).download(year=2025)
        lines = path.read_text().splitlines()
        assert "[CURRENT] Sales Transaction Export" in lines[0]
        # Row 5 (index 4) should be the column header row
        assert lines[4].startswith("Donor,")

    def test_total_footer(self, tmp_path: Path) -> None:
        path = _make_download_downloader(tmp_path).download(year=2025)
        last_line = path.read_text().rstrip("\n").splitlines()[-1]
        assert last_line.startswith("TOTAL")


# ---------------------------------------------------------------------------
# Round-trip test
# ---------------------------------------------------------------------------

class TestQBOCSVRoundTrip:
    def test_receipts_created(self, tmp_path: Path) -> None:
        path = _make_download_downloader(tmp_path).download(year=2025)
        store = TransactionStore([str(path)])
        store.load()
        # 2 unique DocNumbers (5001, 5002); both lines of 5002 share the same Num so
        # the loader deduplicates them (same split-donation logic as manual exports).
        assert len(store.receipts) == 2

    def test_receipt_fields(self, tmp_path: Path) -> None:
        path = _make_download_downloader(tmp_path).download(year=2025)
        store = TransactionStore([str(path)])
        store.load()

        receipt = store.receipts.get("qbo:5001")
        assert receipt is not None
        assert receipt.name == "Alice Donor"  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Live test (skipped unless LIVE_DOWNLOADS=1)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.getenv("LIVE_DOWNLOADS"),
    reason="set LIVE_DOWNLOADS=1, QBO_CLIENT_ID, QBO_CLIENT_SECRET, QBO_TOKENS_PATH to run",
)
class TestQBODownloaderLive:
    def test_live_token_refresh(self, tmp_path: Path) -> None:
        import shutil
        tokens_src = Path(os.environ["QBO_TOKENS_PATH"])
        tokens_dst = tmp_path / "qbo_tokens.json"
        shutil.copy(tokens_src, tokens_dst)

        dl = QBODownloader(
            client_id=os.environ["QBO_CLIENT_ID"],
            client_secret=os.environ["QBO_CLIENT_SECRET"],
            tokens_path=tokens_dst,
            output_dir=tmp_path,
        )
        tokens = dl._load_tokens()
        tokens["token_expiry"] = _past_expiry()
        dl._save_tokens(tokens)
        tokens = dl._load_tokens()
        new_token = dl._ensure_valid_token(tokens)
        assert new_token
        on_disk = json.loads(tokens_dst.read_text())
        assert on_disk["access_token"] == new_token
