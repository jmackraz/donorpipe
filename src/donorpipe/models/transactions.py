from dateutil.parser import parse
from util import parse_float, currency_symbol


def payment_type(service):
    if service in ('stripe'):
        return "credit card"
    elif service in ('paypal'):
        return "paypal"
    else:
        return f"other: {service}"

class Transaction:
    def __init__(self, record, filename, service, tx_id, date, net, currency="USD"):
        self.record = record
        self.filename = filename
        self.service = service
        self.tx_id = tx_id
        self.date = parse(date).date()
        self.net = parse_float(net)
        self.currency = currency

    def __str__(self):
        date_str = self.date.strftime("%m-%d-%Y %H:%M")
        netstr = f"{currency_symbol(self.currency)}{self.net:.2f}"
        return f"{date_str:<15} {netstr:>10} {self.service:<20}"

    @property
    def id(self):
        return f"{self.service}:{self.tx_id}"


class Donation(Transaction):
    def __init__(self, record, filename, service, tx_id, date, net, name, payment_service, charge_tx_id,
                 designation, comment, email, currency="USD"):
        super().__init__(record, filename, service, tx_id, date, net, currency )
        self.name = name
        self.payment_service = payment_service
        self.charge_tx_id = charge_tx_id
        self.designation = designation
        self.comment = comment
        self.email = email

        # linkage to QBO sales
        self.receipt = None     # link to QBO sale. May be set later by associate_donation_receipts
        self.duplicate_receipts = []   # for illuminating dupe entry

    @property
    def charge_id(self):
        return f"{self.payment_service}:{self.charge_tx_id}"

    @property
    def receipts(self):
        receipts = self.duplicate_receipts or []
        if self.receipt:
            receipts.append(self.receipt)
        return receipts

    def __str__(self):
        return f"{'donation:':<10} {super().__str__()} {self.name}"

    def descr(self):
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


class Charge(Transaction):
    def __init__(self, record, filename, service, tx_id, date, net, name, description, payment_service, payout_tx_id, currency="USD" ):
        super().__init__(record, filename, service, tx_id, date, net, currency )
        self.name = name
        self.description = description
        self.payment_service = payment_service
        self.payout_tx_id = payout_tx_id

    def __str__(self):
        return f"{'charge:':<10} {super().__str__()} {self.name}"

    @property
    def payout_id(self):
        return f"{self.payment_service}:{self.payout_tx_id}"

class Payout(Transaction):
    def __init__(self, record, filename, service, tx_id, date, net, currency="USD"):
        super().__init__(record, filename, service, tx_id, date, net, currency)
    def __str__(self):
        return f"{'payout:':<10} {super().__str__()} {self.tx_id}"

class Receipt(Transaction):
    def __init__(self, record, filename, service, tx_id, date, net, name, ref_id, product, currency="USD"):
        super().__init__(record, filename, service, tx_id, date, net, currency)
        self.name = name
        self.ref_id = ref_id
        self.product = product
        self.donation = None    # link to Donation. May be set later by associate_donation_receipts
        self.discrepancies = None # holds annotations about diffs with donation

    def __str__(self):
        return f"{'receipt:':<10} {super().__str__()}"

    def descr(self):
        r = self.record
        descr = (f"{'receipt:':<10} {super().__str__()}\n"
                 f" name: {self.name}\n"
                 f" id: {self.tx_id} product/service: {r.get('Product/Service full name')}, class: {r.get('Item class')} ref #: {r.get('REF #')}, created by: {r.get('Line created by')} at: {r.get('Line created date')}"
                 )
        if self.discrepancies:
            descr += f"\n discrepancies: {self.discrepancies}"
        return descr
