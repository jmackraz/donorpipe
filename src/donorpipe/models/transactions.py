from __future__ import annotations

from datetime import date
from typing import Any

from dateutil.parser import parse
from donorpipe.models.util import parse_float, currency_symbol


def payment_type(service: str) -> str:
    if service in ('stripe'):
        return "credit card"
    elif service in ('paypal'):
        return "paypal"
    else:
        return f"other: {service}"

class Transaction:
    def __init__(self, record: dict[str, Any], filename: str, service: str, tx_id: str,
                 date: str, net: str | float, currency: str = "USD") -> None:
        self.record = record
        self.filename = filename
        self.service = service
        self.tx_id = tx_id
        self.date = parse(date).date()
        self.net = parse_float(net)
        self.currency = currency

    def __str__(self) -> str:
        date_str = self.date.strftime("%m-%d-%Y %H:%M")
        netstr = f"{currency_symbol(self.currency)}{self.net:.2f}"
        return f"{date_str:<15} {netstr:>10} {self.service:<20}"

    @property
    def id(self) -> str:
        return f"{self.service}:{self.tx_id}"


class Donation(Transaction):
    def __init__(self, record: dict[str, Any], filename: str, service: str, tx_id: str,
                 date: str, net: str | float, name: str, payment_service: str,
                 charge_tx_id: str | None, designation: str, comment: str,
                 email: str, currency: str = "USD") -> None:
        super().__init__(record, filename, service, tx_id, date, net, currency )
        self.name = name
        self.payment_service = payment_service
        self.charge_tx_id = charge_tx_id
        self.designation = designation
        self.comment = comment
        self.email = email

        # linkage — populated by association passes in transaction_loader
        self.receipts: list[Receipt] = []
        self.charge: Charge | None = None

    @property
    def charge_id(self) -> str:
        return f"{self.payment_service}:{self.charge_tx_id}"

    def __str__(self) -> str:
        return f"{'donation:':<10} {super().__str__()} {self.name}"

    def descr(self) -> str:
        r = self.record
        descr = (f"{'donation:':<10} {super().__str__()}\n"
                f" name: {self.name}\n"
                f" pay by: {payment_type(self.payment_service)}, ref id: {self.tx_id}\n"
                f" designation: {self.designation}, comment: {self.comment}"
                )
        descr += f"\n Email: {self.email}"
        if r.get('Address'):
            descr += f" \n {r.get('Address')} {r.get('Address 2')}\n{r.get('City')}, {r.get('State / Province')}  {r.get('Postal Code')} {r.get('Country')}"
        return descr

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "service": self.service,
            "tx_id": self.tx_id,
            "date": self.date.isoformat(),
            "net": self.net,
            "currency": self.currency,
            "name": self.name,
            "payment_service": self.payment_service,
            "charge_tx_id": self.charge_tx_id,
            "designation": self.designation,
            "comment": self.comment,
            "email": self.email,
            "charge_id": self.charge.id if self.charge else None,
            "receipt_ids": [r.id for r in self.receipts],
        }

    @classmethod
    def from_dict(cls, data: dict) -> Donation:
        return cls(
            record={},
            filename="",
            service=data["service"],
            tx_id=data["tx_id"],
            date=data["date"],
            net=data["net"],
            name=data["name"],
            payment_service=data["payment_service"],
            charge_tx_id=data["charge_tx_id"],
            designation=data["designation"],
            comment=data["comment"],
            email=data["email"],
            currency=data.get("currency", "USD"),
        )


class Charge(Transaction):
    def __init__(self, record: dict[str, Any], filename: str, service: str, tx_id: str,
                 date: str, net: str | float, name: str, description: str,
                 payment_service: str, payout_tx_id: str | None, currency: str = "USD") -> None:
        super().__init__(record, filename, service, tx_id, date, net, currency )
        self.name = name
        self.description = description
        self.payment_service = payment_service
        self.payout_tx_id = payout_tx_id

        # linkage — populated by associate_charges_payouts
        self.payout: Payout | None = None

    def __str__(self) -> str:
        return f"{'charge:':<10} {super().__str__()} {self.name}"

    @property
    def payout_id(self) -> str:
        return f"{self.payment_service}:{self.payout_tx_id}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "service": self.service,
            "tx_id": self.tx_id,
            "date": self.date.isoformat(),
            "net": self.net,
            "currency": self.currency,
            "name": self.name,
            "description": self.description,
            "payment_service": self.payment_service,
            "payout_tx_id": self.payout_tx_id,
            "payout_id": self.payout.id if self.payout else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Charge:
        return cls(
            record={},
            filename="",
            service=data["service"],
            tx_id=data["tx_id"],
            date=data["date"],
            net=data["net"],
            name=data["name"],
            description=data["description"],
            payment_service=data["payment_service"],
            payout_tx_id=data["payout_tx_id"],
            currency=data.get("currency", "USD"),
        )


class Payout(Transaction):
    def __init__(self, record: dict[str, Any], filename: str, service: str, tx_id: str,
                 date: str, net: str | float, currency: str = "USD") -> None:
        super().__init__(record, filename, service, tx_id, date, net, currency)

        # linkage — populated as side-effect of associate_charges_payouts
        self.charges: list[Charge] = []

    def __str__(self) -> str:
        return f"{'payout:':<10} {super().__str__()} {self.tx_id}"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "service": self.service,
            "tx_id": self.tx_id,
            "date": self.date.isoformat(),
            "net": self.net,
            "currency": self.currency,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Payout:
        return cls(
            record={},
            filename="",
            service=data["service"],
            tx_id=data["tx_id"],
            date=data["date"],
            net=data["net"],
            currency=data.get("currency", "USD"),
        )


class Receipt(Transaction):
    def __init__(self, record: dict[str, Any], filename: str, service: str, tx_id: str,
                 date: str, net: str | float, name: str, ref_id: str,
                 product: str, currency: str = "USD") -> None:
        super().__init__(record, filename, service, tx_id, date, net, currency)
        self.name = name
        self.ref_id = ref_id
        self.product = product
        self.donation: Donation | None = None    # link to Donation. May be set later by associate_donation_receipts
        self.discrepancies: list[str] = []

    def __str__(self) -> str:
        return f"{'receipt:':<10} {super().__str__()}"

    def descr(self) -> str:
        r = self.record
        descr = (f"{'receipt:':<10} {super().__str__()}\n"
                 f" name: {self.name}\n"
                 f" id: {self.tx_id} product/service: {r.get('Product/Service full name')}, class: {r.get('Item class')} ref #: {r.get('REF #')}, created by: {r.get('Line created by')} at: {r.get('Line created date')}"
                 )
        if self.discrepancies:
            descr += f"\n discrepancies: {' '.join(self.discrepancies)}"
        return descr

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "service": self.service,
            "tx_id": self.tx_id,
            "date": self.date.isoformat(),
            "net": self.net,
            "currency": self.currency,
            "name": self.name,
            "ref_id": self.ref_id,
            "product": self.product,
            "donation_id": self.donation.id if self.donation else None,
            "discrepancies": self.discrepancies,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Receipt:
        obj = cls(
            record={},
            filename="",
            service=data["service"],
            tx_id=data["tx_id"],
            date=data["date"],
            net=data["net"],
            name=data["name"],
            ref_id=data["ref_id"],
            product=data["product"],
            currency=data.get("currency", "USD"),
        )
        obj.discrepancies = data.get("discrepancies", [])
        return obj
