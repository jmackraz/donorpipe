"""PayPal Transaction API downloader.

Downloads transactions for a given year and writes a CSV matching the format
expected by load_paypal_transactions() in transaction_store.py.

Auth: OAuth2 client credentials (PAYPAL_CLIENT_ID, PAYPAL_SECRET_KEY).
API:  GET /v1/reporting/transactions — max 31-day range; requests are chunked by month.
"""
from __future__ import annotations

import calendar
import csv
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

PACIFIC = ZoneInfo("America/Los_Angeles")

# Full 40-column header matching the manually-downloaded PayPal Activity report.
CSV_COLUMNS = [
    "Date",
    "Time",
    "TimeZone",
    "Name",
    "Type",
    "Status",
    "Currency",
    "Gross",
    "Fee",
    "Net",
    "From Email Address",
    "To Email Address",
    "Transaction ID",
    "Shipping Address",
    "Address Status",
    "Item Title",
    "Item ID",
    "Shipping and Handling Amount",
    "Insurance Amount",
    "Sales Tax",
    "Option 1 Name",
    "Option 1 Value",
    "Option 2 Name",
    "Option 2 Value",
    "Reference Txn ID",
    "Invoice Number",
    "Custom Number",
    "Quantity",
    "Receipt ID",
    "Balance",
    "Address Line 1",
    "Address Line 2/District/Neighborhood",
    "Town/City",
    "State/Province/Region/County/Territory/Prefecture/Republic",
    "Zip/Postal Code",
    "Country",
    "Contact Phone Number",
    "Subject",
    "Note",
    "Country Code",
    "Balance Impact",
]

# Maps PayPal transaction event codes to the Type strings used by the loader.
# Add new codes here as they are encountered in live runs.
EVENT_CODE_TYPES: dict[str, str] = {
    "T0013": "Donation Payment",            # Website Payments Standard - payment received
    "T0002": "Subscription Payment",        # Recurring payment
    "T0006": "Express Checkout Payment",    # PayPal Checkout APIs (ignored by loader)
    "T0113": "Partner Fee",                 # Partner/referral fee
    "T0300": "Bank Deposit to PP Account",  # Bank → PayPal deposit (ignored by loader)
    "T0401": "User Initiated Withdrawal",   # PayPal-to-bank withdrawal
    "T0400": "General Withdrawal",          # General withdrawal from PayPal account
    "T0403": "User Initiated Withdrawal",   # Funds transfer to bank
    "T0001": "Mass Pay Payment",            # MassPay payment
    "T1201": "Mass Pay Payment",            # Mass Pay (alternate code)
}

TRANSACTION_STATUSES: dict[str, str] = {
    "S": "Completed",
    "P": "Pending",
    "V": "Reversed",
    "F": "Denied",
}


class PayPalDownloader:
    """Download PayPal transactions for a given year and write paypal_{year}.csv.

    The CSV format matches the manually-downloaded PayPal Activity report and is
    compatible with load_paypal_transactions() in transaction_store.py.
    """

    _BASE_URL = "https://api.paypal.com"

    def __init__(
        self,
        client_id: str,
        secret_key: str,
        output_dir: Path,
        _client: httpx.Client | None = None,
    ) -> None:
        self._client_id = client_id
        self._secret_key = secret_key
        self._token: str | None = None
        self._client = _client or httpx.Client(base_url=self._BASE_URL, timeout=30)
        self.output_dir = output_dir

    def _get_token(self) -> str:
        """Fetch an OAuth2 access token using client credentials."""
        r = self._client.post(
            "/v1/oauth2/token",
            auth=(self._client_id, self._secret_key),
            data={"grant_type": "client_credentials"},
        )
        r.raise_for_status()
        return r.json()["access_token"]  # type: ignore[no-any-return]

    def _paginate(self, start_date: str, end_date: str) -> list[dict]:  # type: ignore[type-arg]
        """Return all transaction_details for the given ISO 8601 date range.

        Fetches token lazily on first call so that mocking _paginate in tests
        does not trigger a real token request.
        """
        if self._token is None:
            self._token = self._get_token()

        items: list[dict] = []  # type: ignore[type-arg]
        page = 1
        while True:
            r = self._client.get(
                "/v1/reporting/transactions",
                headers={"Authorization": f"Bearer {self._token}"},
                params={
                    "start_date": start_date,
                    "end_date": end_date,
                    "fields": "transaction_info,payer_info,shipping_info",
                    "page_size": 100,
                    "page": page,
                },
            )
            r.raise_for_status()
            data = r.json()
            items.extend(data.get("transaction_details", []))
            if page >= data.get("total_pages", 1):
                break
            page += 1
        return items

    @staticmethod
    def _month_bounds(year: int, month: int) -> tuple[str, str]:
        last_day = calendar.monthrange(year, month)[1]
        start = f"{year:04d}-{month:02d}-01T00:00:00Z"
        end = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59Z"
        return start, end

    @staticmethod
    def _map_row(tx: dict) -> dict[str, str] | None:  # type: ignore[type-arg]
        """Map a single transaction_details entry to a CSV row dict.

        Returns None for unknown event codes (logged to stdout).
        """
        info = tx.get("transaction_info", {})
        payer = tx.get("payer_info", {})
        shipping = tx.get("shipping_info", {})

        event_code = info.get("transaction_event_code", "")
        tx_type = EVENT_CODE_TYPES.get(event_code)
        if tx_type is None:
            print(f"[paypal] skipping unknown event code: {event_code}")
            return None

        dt_str = info.get("transaction_initiation_date", "")
        try:
            dt_utc = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            dt_local = dt_utc.astimezone(PACIFIC)
            date = dt_local.strftime("%m/%d/%Y")
            time = dt_local.strftime("%H:%M:%S")
            tz_name = dt_local.strftime("%Z")  # "PDT" or "PST"
        except ValueError:
            date = ""
            time = ""
            tz_name = ""

        gross_str = info.get("transaction_amount", {}).get("value", "0.00")
        fee_info = info.get("fee_amount", {})
        fee_str = fee_info.get("value", "") if fee_info else ""

        gross = float(gross_str)
        fee = float(fee_str) if fee_str else 0.0
        net = gross + fee  # fee_amount is negative

        payer_name = payer.get("payer_name", {})
        name = payer_name.get("alternate_full_name", "")
        balance_impact = "Credit" if gross > 0 else "Debit"
        subject = info.get("transaction_subject", "")

        # Shipping address fields
        ship_addr = shipping.get("address", {})
        addr_line1 = ship_addr.get("line1", "")
        addr_line2 = ship_addr.get("line2", "")
        addr_city = ship_addr.get("city", "")
        addr_state = ship_addr.get("state", "")
        addr_zip = ship_addr.get("postal_code", "")
        addr_country = ship_addr.get("country_code", "")
        # Combined shipping address string (matches manual download format)
        ship_parts = [p for p in [addr_line1, addr_city, addr_state, addr_zip, addr_country] if p]
        shipping_address = ", ".join(ship_parts)

        row: dict[str, str] = {col: "" for col in CSV_COLUMNS}
        row.update(
            {
                "Date": date,
                "Time": time,
                "TimeZone": tz_name,
                "Name": name,
                "Type": tx_type,
                "Status": TRANSACTION_STATUSES.get(info.get("transaction_status", ""), ""),
                "Currency": info.get("transaction_amount", {}).get("currency_code", ""),
                "Gross": gross_str,
                "Fee": fee_str,
                "Net": f"{net:.2f}",
                "From Email Address": payer.get("email_address", ""),
                "To Email Address": "",
                "Transaction ID": info.get("transaction_id", ""),
                "Shipping Address": shipping_address,
                "Address Status": payer.get("address_status", ""),
                "Item Title": subject,
                "Reference Txn ID": info.get("paypal_reference_id", ""),
                "Balance": info.get("ending_balance", {}).get("value", ""),
                "Address Line 1": addr_line1,
                "Address Line 2/District/Neighborhood": addr_line2,
                "Town/City": addr_city,
                "State/Province/Region/County/Territory/Prefecture/Republic": addr_state,
                "Zip/Postal Code": addr_zip,
                "Country": addr_country,
                "Country Code": payer.get("country_code", ""),
                "Subject": subject,
                "Note": info.get("transaction_note", ""),
                "Balance Impact": balance_impact,
            }
        )
        return row

    def download(self, year: int) -> Path:
        """Download all PayPal transactions for *year* and write paypal_{year}.csv.

        Returns the path to the written file.
        """
        now = datetime.now(tz=UTC)
        last_month = now.month if now.year == year else 12

        all_rows: list[dict[str, str]] = []
        for month in range(1, last_month + 1):
            start, end = self._month_bounds(year, month)
            for tx in self._paginate(start, end):
                row = self._map_row(tx)
                if row is not None:
                    all_rows.append(row)

        # Sort by datetime, matching the loader's sorted() call.
        all_rows.sort(
            key=lambda r: datetime.strptime(
                f"{r['Date']} {r['Time']}", "%m/%d/%Y %H:%M:%S"
            )
            if r["Date"]
            else datetime.min
        )

        output_path = self.output_dir / f"paypal_{year}.csv"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(all_rows)

        return output_path

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> PayPalDownloader:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
