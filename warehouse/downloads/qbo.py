"""QuickBooks Online (QBO) OAuth2 downloader.

Downloads Sales Receipts from 2023-01-01 to the present and writes QBO_from_2023.csv matching
the format expected by load_qbo_transactions() in transaction_store.py.

Auth: OAuth2 authorization code flow with long-lived refresh tokens.
      Tokens are stored in qbo_tokens.json in the operator-specified tokens directory.
      Secrets (client_id, client_secret) are passed via env vars (QBO_CLIENT_ID,
      QBO_CLIENT_SECRET) and forwarded here by the caller.

API:  Entity query endpoint — SELECT * FROM SalesReceipt WHERE TxnDate >= ... AND TxnDate <= ...
      Paginated via STARTPOSITION / MAXRESULTS (max 1000 per page).

CSV:  One row per SalesItemLineDetail line. Transactions with N item lines produce N rows.
"""
from __future__ import annotations

import csv
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

CSV_COLUMNS = [
    "Donor",
    "Transaction date",
    "Num",
    "Product/Service full name",
    "Amount",
    "REF #",
    "Line created by",
    "Line created date",
    "Item class",
]


class QBODownloader:
    _TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
    _BASE_URL = "https://quickbooks.api.intuit.com"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        tokens_path: Path,
        output_dir: Path,
        _client: httpx.Client | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._tokens_path = tokens_path
        self.output_dir = output_dir
        self._client = _client or httpx.Client(timeout=30)

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _load_tokens(self) -> dict:  # type: ignore[type-arg]
        """Read qbo_tokens.json. Raises RuntimeError if the file does not exist."""
        if not self._tokens_path.exists():
            raise RuntimeError(
                f"QBO tokens file not found: {self._tokens_path}\n"
                "Use the Intuit OAuth2 Playground to obtain tokens and create this file."
            )
        return json.loads(self._tokens_path.read_text())  # type: ignore[no-any-return]

    def _save_tokens(self, tokens: dict) -> None:  # type: ignore[type-arg]
        """Atomically write updated tokens back to qbo_tokens.json."""
        tmp = self._tokens_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(tokens, indent=2))
        tmp.replace(self._tokens_path)

    def _ensure_valid_token(self, tokens: dict) -> str:  # type: ignore[type-arg]
        """Return a valid access token, refreshing if the current one is near expiry.

        If the access token expires within 5 minutes, a refresh is performed and the
        updated tokens are written back to disk. Raises RuntimeError on refresh failure.
        """
        expiry_str = tokens.get("token_expiry", "")
        if expiry_str:
            expiry = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
            needs_refresh = datetime.now(tz=UTC) >= expiry - timedelta(minutes=5)
        else:
            needs_refresh = True  # no expiry recorded — refresh to get a valid token
        if needs_refresh:
            new_tokens = self._refresh_token(tokens)
            self._save_tokens(new_tokens)
            return new_tokens["access_token"]  # type: ignore[no-any-return]
        return tokens["access_token"]  # type: ignore[no-any-return]

    def _refresh_token(self, tokens: dict) -> dict:  # type: ignore[type-arg]
        """Exchange a refresh token for new tokens via the Intuit token endpoint.

        Returns an updated tokens dict. Raises RuntimeError on HTTP failure.
        """
        r = self._client.post(
            self._TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": tokens["refresh_token"],
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            },
        )
        if not r.is_success:
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            raise RuntimeError(
                f"QBO token refresh failed (HTTP {r.status_code}): {detail}\n"
                "Use the Intuit OAuth2 Playground to obtain new tokens and update "
                f"{self._tokens_path}."
            )
        data = r.json()
        expiry = datetime.now(tz=UTC) + timedelta(seconds=int(data["expires_in"]))
        return {
            "realm_id": tokens["realm_id"],
            "access_token": data["access_token"],
            "refresh_token": data["refresh_token"],
            "token_expiry": expiry.isoformat(),
        }

    # ------------------------------------------------------------------
    # API fetch
    # ------------------------------------------------------------------

    def _fetch_receipts(self, realm_id: str, token: str, start: str, end: str) -> list[dict]:  # type: ignore[type-arg]
        """Paginate SalesReceipt query for the given date range. Returns all receipt dicts."""
        all_receipts: list[dict] = []  # type: ignore[type-arg]
        position = 1
        while True:
            query = (
                f"SELECT * FROM SalesReceipt "
                f"WHERE TxnDate >= '{start}' AND TxnDate <= '{end}' "
                f"STARTPOSITION {position} MAXRESULTS 1000"
            )
            r = self._client.get(
                f"{self._BASE_URL}/v3/company/{realm_id}/query",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json",
                },
                params={"query": query},
            )
            r.raise_for_status()
            receipts = r.json()["QueryResponse"].get("SalesReceipt", [])
            all_receipts.extend(receipts)
            if len(receipts) < 1000:
                break
            position += len(receipts)
        return all_receipts

    # ------------------------------------------------------------------
    # Row mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _map_row(txn: dict, line: dict) -> dict[str, str]:  # type: ignore[type-arg]
        """Map one SalesItemLineDetail line of a SalesReceipt to a CSV row dict."""
        detail = line["SalesItemLineDetail"]

        # Item class: use the leaf segment after the last colon, or empty if absent.
        class_name = detail.get("ClassRef", {}).get("name", "")
        item_class = class_name.rsplit(":", 1)[-1].strip() if class_name else ""

        # Line created date: reformat ISO 8601 to MM/DD/YYYY HH:MM:SS AM/PM.
        dt = datetime.fromisoformat(txn["MetaData"]["CreateTime"])
        line_created_date = dt.strftime("%m/%d/%Y %I:%M:%S %p")

        return {
            "Donor": txn["CustomerRef"]["name"],
            "Transaction date": datetime.strptime(txn["TxnDate"], "%Y-%m-%d").strftime(
                "%m/%d/%Y"
            ),
            "Num": txn.get("DocNumber", ""),
            "Product/Service full name": detail["ItemRef"]["name"],
            "Amount": f"{line['Amount']:.2f}",
            "REF #": txn.get("PaymentRefNum", ""),
            "Line created by": "",
            "Line created date": line_created_date,
            "Item class": item_class,
        }

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download(self) -> Path:
        """Download QBO Sales Receipts from 2023-01-01 to today and write QBO_from_2023.csv.

        Returns the path to the written file.
        """
        tokens = self._load_tokens()
        access_token = self._ensure_valid_token(tokens)
        realm_id = tokens["realm_id"]

        today = datetime.now(tz=UTC).date()
        start = "2023-01-01"
        end = today.strftime("%Y-%m-%d")
        receipts = self._fetch_receipts(realm_id, access_token, start, end)

        rows: list[dict[str, str]] = []
        skipped = 0
        for txn in receipts:
            for line in txn.get("Line", []):
                if line.get("DetailType") == "SalesItemLineDetail":
                    try:
                        rows.append(self._map_row(txn, line))
                    except KeyError as exc:
                        import json, sys
                        skipped += 1
                        print(
                            f"WARNING: skipping malformed SalesReceipt line "
                            f"(missing key {exc}). Transaction payload:",
                            file=sys.stderr,
                        )
                        print(json.dumps(txn, indent=2), file=sys.stderr)
        if skipped:
            print(f"WARNING: {skipped} line(s) skipped due to missing fields.", file=sys.stderr)

        rows.sort(key=lambda r: datetime.strptime(r["Transaction date"], "%m/%d/%Y"))

        output_path = self.output_dir / "QBO_from_2023.csv"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            raw_writer = csv.writer(f)
            raw_writer.writerow(["[CURRENT] Sales Transaction Export"] + [""] * 8)
            raw_writer.writerow([""] * 9)  # org name (not available via API)
            raw_writer.writerow([f"January, 2023-{today.strftime('%B, %Y')}"] + [""] * 8)
            raw_writer.writerow([""] * 9)  # blank row (row 4 of header block)
            dict_writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            dict_writer.writeheader()
            dict_writer.writerows(rows)
            raw_writer.writerow(["TOTAL"] + [""] * 8)

        return output_path

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> QBODownloader:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
