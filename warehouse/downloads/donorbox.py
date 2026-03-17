from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

import httpx
from dateutil import parser as dateutil_parser

# Column order must match the DonorBox manual export format expected by
# load_donorbox_transactions() in transaction_store.py.
CSV_COLUMNS = [
    "Name",
    "Donating Company",
    "Donor's First Name",
    "Donor's Last Name",
    "Donor Email",
    "Make Donation Anonymous",
    "Campaign",
    "Amount",
    "Fair Market Value",
    "Fair Market Value Description",
    "Tax Deductible Amount",
    "Currency",
    "Amount in USD",
    "Processing Fee",
    "Platform Fee",
    "Tax Fee",
    "Total Fee",
    "Net Amount",
    "Converted Net Amount",
    "Net amount in USD",
    "Fee Covered",
    "Donor Comment",
    "Internal Notes",
    "Donated At",
    "Phone",
    "Address",
    "Address 2",
    "City",
    "State / Province",
    "Postal Code",
    "Country",
    "Employer",
    "Occupation",
    "Designation",
    "Receipt Id",
    "Donation Type",
    "Card Type",
    "Last 4 Digits",
    "Stripe Charge Id",
    "Pay Pal Transaction Id",
    "Pay Pal Capture Id",
    "Recurring Donation",
    "Recurring Plan Id",
    "Recurring Start Date",
    "Join Mailing List",
    "Dedication Type",
    "Honoree Name",
    "Recipient Name",
    "Recipient Email",
    "Recipient Address",
    "Recipient Message",
    "First Donation",
    "Fundraiser",
    "Donor Id",
    "Status",
    "Would you like to receive occasional updates from us?",
]


class DonorBoxDownloader:
    """Download DonorBox donations for a given year and write a CSV in the
    format expected by load_donorbox_transactions() in transaction_store.py.

    Fields not available through the DonorBox API (e.g. Fair Market Value,
    Platform Fee, Card Type) are written as empty strings.

    Net Amount is computed as Amount − Processing Fee, which is the best
    approximation available from the API.
    """

    _BASE_URL = "https://donorbox.org"

    def __init__(
        self,
        email: str,
        api_key: str,
        output_dir: Path,
        _client: httpx.Client | None = None,
    ) -> None:
        self._client = _client or httpx.Client(
            auth=(email, api_key),
            base_url=self._BASE_URL,
            timeout=30,
        )
        self.output_dir = output_dir

    def _paginate(self, path: str, params: dict) -> list[dict]:
        """Return all items from a page-based DonorBox list endpoint."""
        items: list[dict] = []
        p = dict(params)
        p["per_page"] = 100
        page = 1
        while True:
            p["page"] = page
            r = self._client.get(path, params=p)
            r.raise_for_status()
            data: list[dict] = r.json()
            items.extend(data)
            if len(data) < 100:
                break
            page += 1
        return items

    @staticmethod
    def _fmt(value: object) -> str:
        """Convert a value to a CSV-safe string."""
        if value is None:
            return ""
        return str(value)

    @staticmethod
    def _fmt_bool(value: object) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        return ""

    @staticmethod
    def _fmt_amount(value: object) -> str:
        if value is None:
            return ""
        try:
            return f"{float(value):.2f}"  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return str(value)

    def download(self, year: int) -> Path:
        """Download all DonorBox donations for *year* and write donorbox_{year}.csv.

        Returns the path to the written file.
        """
        output_path = self.output_dir / f"donorbox_{year}.csv"

        donations = self._paginate(
            "/api/v1/donations",
            {
                "date_from": f"{year}-01-01",
                "date_to": f"{year}-12-31",
                "order": "asc",
            },
        )

        rows: list[dict[str, str]] = []
        for d in donations:
            donor = d.get("donor") or {}
            campaign = d.get("campaign") or {}

            amount = d.get("amount") or 0.0
            processing_fee = d.get("processing_fee") or 0.0

            # Platform fee rate changed 4/1/2025: 1.75% before, 2.0% from then on.
            try:
                donation_date = dateutil_parser.parse(
                    str(d.get("donation_date") or "")
                ).date()
            except (ValueError, OverflowError):
                donation_date = date.min
            platform_rate = 0.02 if donation_date >= date(2025, 4, 1) else 0.0175
            try:
                platform_fee = float(amount) * platform_rate
            except (TypeError, ValueError):
                platform_fee = 0.0
            try:
                net = float(amount) - float(processing_fee) - float(platform_fee)
            except (TypeError, ValueError):
                net = 0.0

            rows.append(
                {
                    "Name": self._fmt(donor.get("name")),
                    "Donating Company": self._fmt(d.get("donating_company")),
                    "Donor's First Name": self._fmt(donor.get("first_name")),
                    "Donor's Last Name": self._fmt(donor.get("last_name")),
                    "Donor Email": self._fmt(donor.get("email")),
                    "Make Donation Anonymous": self._fmt_bool(
                        d.get("anonymous_donation")
                    ),
                    "Campaign": self._fmt(campaign.get("name")),
                    "Amount": self._fmt_amount(amount),
                    "Fair Market Value": "",
                    "Fair Market Value Description": "",
                    "Tax Deductible Amount": "",
                    "Currency": self._fmt(d.get("currency")),
                    "Amount in USD": self._fmt_amount(d.get("converted_amount")),
                    "Processing Fee": self._fmt_amount(processing_fee),
                    "Platform Fee": self._fmt_amount(platform_fee),
                    "Tax Fee": "",
                    "Total Fee": "",
                    "Net Amount": self._fmt_amount(net),
                    "Converted Net Amount": "",
                    "Net amount in USD": "",
                    "Fee Covered": "",
                    "Donor Comment": self._fmt(d.get("comment")),
                    "Internal Notes": "",
                    "Donated At": self._fmt(d.get("donation_date")),
                    "Phone": self._fmt(donor.get("phone")),
                    "Address": self._fmt(donor.get("address")),
                    "Address 2": "",
                    "City": self._fmt(donor.get("city")),
                    "State / Province": self._fmt(donor.get("state")),
                    "Postal Code": self._fmt(donor.get("zip_code")),
                    "Country": self._fmt(donor.get("country")),
                    "Employer": self._fmt(donor.get("employer")),
                    "Occupation": self._fmt(donor.get("occupation")),
                    "Designation": self._fmt(d.get("designation")),
                    "Receipt Id": self._fmt(d.get("id")),
                    "Donation Type": self._fmt(d.get("donation_type")),
                    "Card Type": "",
                    "Last 4 Digits": "",
                    "Stripe Charge Id": self._fmt(d.get("stripe_charge_id")),
                    "Pay Pal Transaction Id": self._fmt(d.get("paypal_transaction_id")),
                    "Pay Pal Capture Id": "",
                    "Recurring Donation": self._fmt_bool(d.get("recurring")),
                    "Recurring Plan Id": "",
                    "Recurring Start Date": "",
                    "Join Mailing List": self._fmt_bool(d.get("join_mailing_list")),
                    "Dedication Type": "",
                    "Honoree Name": "",
                    "Recipient Name": "",
                    "Recipient Email": "",
                    "Recipient Address": "",
                    "Recipient Message": "",
                    "First Donation": self._fmt_bool(d.get("first_recurring_donation")),
                    "Fundraiser": "",
                    "Donor Id": self._fmt(donor.get("id")),
                    "Status": self._fmt(d.get("status")),
                    "Would you like to receive occasional updates from us?": "",
                }
            )

        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

        return output_path

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> DonorBoxDownloader:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
