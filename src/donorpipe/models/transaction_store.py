import csv
import os
import re

from transactions import Donation, Charge, Payout, Receipt
from util import csv_rows, parse_float, shorten_gdrive_path
from util import parse_datetime  # Import parse_datetime from util.py

benevity_filepat = re.compile(".*benevity.*", re.IGNORECASE)
paypal_filepat = re.compile(".*paypal.*", re.IGNORECASE)
stripe_filepat = re.compile(".*stripe.*", re.IGNORECASE)
donorbox_filepat = re.compile(".*DonorBox.*", re.IGNORECASE)
qbo_filepat = re.compile("(qbo|quickbooks)", re.IGNORECASE)


class TransactionStore:
    def __init__(self, files):
        self.files = files

        self.donations = {}
        self.charges = {}
        self.payouts = {}
        self.deposits = {}
        self.receipts = {}

    def add_donation(self, donation):
        if donation.id in self.donations:
            print("DUPLICATE:", donation)
        self.donations[donation.id] = donation

    def add_charge(self, charge):
        if charge.id in self.charges:
            print("DUPLICATE:", charge)
        self.charges[charge.id] = charge

    def add_payout(self, payout):
        if payout.id in self.payouts:
            print("DUPLICATE:", payout)
        self.payouts[payout.id] = payout

    def add_receipt(self, receipt):
        if receipt.id in self.receipts:
            print("DUPLICATE:", receipt)
        self.receipts[receipt.id] = receipt

    def add_deposit(self, deposit):
        if deposit.id in self.deposits:
            print("DUPLICATE:", deposit)
        self.deposits[deposit.id] = deposit

    # associations

    def donation_charge(self, donation):
        charge_id = donation.charge_id if donation else None
        return self.charges.get(charge_id)

    def charge_payout(self, charge):
        payout_id = charge.payout_id if charge else None
        return self.payouts.get(payout_id)

    def payout_charges(self, payout):
        return [ch  for ch in self.charges.values() if ch.payout_id == payout.id]
        return None

    @staticmethod
    def parse_filename(filename):
        match = donorbox_filepat.match(filename)
        if match:
            return dict(type="donorbox")

        match = stripe_filepat.match(filename)
        if match:
            return dict(type="stripe")

        match = paypal_filepat.match(filename)
        if match:
            return dict(type="paypal")

        match = qbo_filepat.match(filename)
        if match:
            return dict(type="qbo")

        match = benevity_filepat.match(filename)
        if match:
            return dict(type="benevity")

        # unknown file type
        return None


    def load(self):
        """ read in new transactions from downloaded csv files with account naming conventions
            pass through rules (lazy-loaded from YAML files) to assign categories and tags.
        """
        list_files = False
        #self.files.sort()
        for path in self.files:
            filename = os.path.basename(path)
            # print("file:", filename)
            info = self.parse_filename(filename)

            if not info:
                print("can't understand filename", filename)

            elif info['type'] == "donorbox":

                list_files and print("load donorbox transactions from:", shorten_gdrive_path(path))
                self.load_donorbox_transactions(path)
            elif info['type'] == "stripe":
                list_files and print("load stripe transactions from:", shorten_gdrive_path(path))
                self.load_stripe_transactions(path)
            elif info['type'] == "paypal":
                list_files and print("load paypal transactions from:", shorten_gdrive_path(path))
                self.load_paypal_transactions(path)
            elif info['type'] == "qbo":
                list_files and print("load qbo transactions from:", shorten_gdrive_path(path))
                self.load_qbo_transactions(path)
            elif info['type'] == "benevity":
                list_files and print("load benevity transactions from:", shorten_gdrive_path(path))
                self.load_benevity_transactions(path)
            else:
                print("can't handle type:", info['type'])

    def load_qbo_transactions(self, filename):

        # QBO doesn't export clean CSVs. They have junk at the beginning and the end.
        for r in csv_rows(filename, skip=4):
            fields_to_test =  ",".join(r.values())
            if "TOTAL" in fields_to_test:
                break

            net = r['Amount']
            date = r['Transaction date']
            receipt = Receipt(r, filename=filename, service="qbo", tx_id = r['Num'], date = date, net = net,
                              name = r['Donor'], ref_id = r['REF #'],
                              product=r['Product/Service full name'])

            if receipt.id in self.receipts:
                # so far, this is always a split.  Can turn this on or breakpoint on it for debugging.
                # print("Duplicate receipt ID (split donation):", receipt.id)
                pass
            self.receipts[receipt.id] = receipt

    def load_benevity_transactions(self, filename):
        """Load donations from benevity CSV file.
        We synthesize charges for each donation, and a payout for each file.
        We assume the "Check fee" will always be 0.00.  (always has been. payout won't match bank deposit.)
        """

        looking_for_header_block_end = False
        looking_for_column_headers = False
        with open(filename, encoding='utf-8-sig') as csvin:
            tuple_reader = csv.reader(csvin)
            for row in tuple_reader:
                #print("raw row:", row)
                if not row:
                    #print("skipping empty row")
                    continue
                if row[0] == "Disbursement ID":
                    payment_id = row[1]
                    looking_for_header_block_end = True
                elif row[0] == "Period Ending":
                    period_end = row[1]
                    looking_for_header_block_end = True
                    continue
                elif looking_for_header_block_end and row[0].startswith("#--"):
                    #print("header end found")
                    looking_for_column_headers = True
                    continue
                elif looking_for_column_headers and row[0] != "":
                    #print("column headers found")
                    field_names = row
                    break
                pass

            #print(f"ready to parse rows.  payment id: {payment_id} period end: {period_end}")

            payment_net = 0     # sum of donation charges

            # stream should be positioned on column-headers row
            if not field_names:
                print("ERROR: no field names found")
                return
            dict_reader = csv.DictReader(csvin, fieldnames=field_names)
            for r in dict_reader:
                if r['Company'] == 'Totals':
                    #print("end of donations rows")
                    break

                name = f"{r['Donor First Name']} {r['Donor Last Name']}"
                donation_id = r['Transaction ID']
                date = r['Donation Date']
                currency = r['Currency']
                net = parse_float(r['Total Donation to be Acknowledged']) + parse_float(r['Match Amount']) - parse_float(r['Cause Support Fee']) - parse_float(r['Merchant Fee'])
                payment_net += net

                #print(f"net: {net}, name: {name}, date: {date} transaction_id: {donation_id}")

                self.add_donation( Donation(r, filename, "benevity", tx_id=donation_id, date=date, net=net,
                                    name=name,
                                    payment_service="benevity",
                                    charge_tx_id=donation_id,
                                    designation=r['Project'],
                                    comment=r['Comment'],
                                    email=r['Email'],
                                    currency=currency))       # our choice, we synthesize the charge to suit

                # sythesized charge, ID is same as donation_id
                self.add_charge( Charge(r, filename=filename,service="benevity",
                                tx_id = donation_id, date = date, net = net,
                                name = name,
                                description = r['Project'],
                                payment_service = "benevity",
                                payout_tx_id = payment_id,
                                currency = currency,
                                ))

            # create a payout for all these donations/charges
            self.add_payout(Payout(r, filename=filename, service="benevity",
                            tx_id = payment_id, date = period_end,
                            net = payment_net, currency = currency ))


    def load_paypal_transactions(self, filename):
        charges_needing_payout = []
        partner_fees = []   # raw records of partner fees

        # Replace `csv_rows()` with the imported function as necessary
        for r in sorted(csv_rows(filename), key=lambda rec: parse_datetime(rec['Date'], rec['Time'])):
            # Process each row here
            tx_type = r['Type']
            net = r['Net']
            date = r['Date']
            name = r['Name']
            if r['Balance Impact'] not in ("Credit", "Debit"):
                if r['Balance Impact'] != "Memo":
                    print("unexpected paypal balance impact:", r['Balance Impact'])
                continue

            if tx_type in ("Donation Payment", "Subscription Payment"):
                # charge
                charge = Charge(r, filename=filename, service="paypal", tx_id = r['Transaction ID'], date = date, net = net,
                                name = name,
                                description = r['Subject'],
                                payment_service = "paypal",
                                payout_tx_id = None             # will patch up later when we see a withdrawal
                                )
                self.add_charge(charge)
                charges_needing_payout.append(charge)

            elif tx_type == "Partner Fee":
                partner_fees.append(r)

            elif tx_type in ("General Withdrawal", "User Initiated Withdrawal"):
                payout = Payout(r, filename=filename, service="paypal", tx_id = r['Transaction ID'], date = date, net = net )
                self.add_payout(payout)

                # patch up pending charges
                for ch in charges_needing_payout:
                    ch.payout_tx_id = payout.tx_id
                charges_needing_payout = []

            elif tx_type == "Mass Pay Payment":
                """donation from throw the paypal donor "hub" or by paypal itself.  We synthesize the charge."""
                charge = Charge(r, filename=filename, service="paypal", tx_id = r['Transaction ID'], date = date, net = net,
                                name = name,
                                description = r['Subject'],
                                payment_service = "paypal",
                                payout_tx_id = None  # will patch up later when we see a withdrawal
                                )
                self.add_charge(charge)
                charges_needing_payout.append(charge)

                self.add_donation( Donation(r, filename=filename, service="paypal",
                                    tx_id=r['Transaction ID'], date=date, net=net,
                                    name=name,
                                    payment_service="paypal",
                                    charge_tx_id=charge.tx_id,
                                    designation = r['Subject'],
                                    comment = r['Note'],
                                    email=r['From Email Address'])
                )

        for r in partner_fees:
            net = r['Net']
            charge_tx_id = r['Reference Txn ID']
            charge = self.charges.get(f"paypal:{charge_tx_id}")
            if charge:
                charge.net += parse_float(net)
            else:
                print("no charge found for paypal fee:", charge_tx_id)

        """
        Donation Payment
        General Withdrawal
        Subscription Payment
        User Initiated Withdrawal
        Partner Fee
        Mass Pay Payment
        """



    def load_stripe_transactions(self, filename):
        for r in csv_rows(filename):
            tx_type = r['Type']
            net = r['Net']
            date = r['Created (UTC)']
            description = r['Description']
            name = r['donorbox_name (metadata)']

            if tx_type == 'charge' or tx_type == 'payment':   # 'payment' == ACH
                self.add_charge(Charge(r, filename=filename, service="stripe",
                                tx_id = r['Source'], date = date, net = net,
                                name = name,
                                description = description,
                                payment_service = "stripe",
                                payout_tx_id = r['Transfer'],
                                ))

            elif tx_type == 'payout':
                self.add_payout(Payout(r, filename=filename, service="stripe", tx_id = r['Source'], date = date, net = net ))
            else:
                print("Unexpected Stripe transaction tx_type:", tx_type)
                continue

    def load_donorbox_transactions(self, filename):
        for r in csv_rows(filename):
            if r['Donation Type'] in ("stripe", "ach"):
                payment_service = "stripe"
                charge_id = r['Stripe Charge Id']
            elif r['Donation Type'] in ["paypal", "paypal_express"]:
                payment_service = "paypal"
                charge_id = r.get('Paypal Capture Id') or r.get('Pay Pal Capture Id')
            else:
                print("UNKNOWN DONATION TYPE:", r['Donation Type'])
                continue

            self.add_donation(Donation(r, filename=filename, service="donorbox",
                                tx_id=r['Receipt Id'], date=r['Donated At'], net=r['Net Amount'],
                                name=r['Name'],
                                payment_service=payment_service,
                                charge_tx_id=charge_id,
                                designation=f"{r['Campaign']}/{r['Designation']}",
                                comment=r['Donor Comment'],
                                email=r['Donor Email'],
                                       ))


"""
DonorBox
*Name
Donating Company
Donor's First Name
Donor's Last Name
*Donor Email
Make Donation Anonymous
Campaign
Amount Description
*Amount
Fair Market Value
Fair Market Value Description
Tax Deductible Amount
*Currency
Amount in USD
Processing Fee
Platform Fee
Total Fee
*Net Amount
Fee Covered
Donor Comment
Internal Notes
Donated At
Phone
Address
Address 2
City
State / Province
Postal Code
Country
Employer
Occupation
Designation
Receipt Id
*Donation Type
Card Type
Last 4 Digits
*Stripe Charge Id
*Pay Pal Transaction Id
Pay Pal Capture Id
Recurring Donation
Recurring Plan Id
Recurring Start Date
Join Mailing List
Dedication Type
Honoree Name
Recipient Name
Recipient Email
Recipient Address
Recipient Message
First Donation
Fundraiser
Donor Id
Would you like to receive occasional updates from us? You can unsubscribe at any time.

name=r['Name']
r['Donor Email']
r['Amount']
r['Receipt Id']
r['Currency']
r['Net Amount']
r['Donation Type']
r['Stripe Charge Id']
r['Pay Pal Transaction Id']

"""