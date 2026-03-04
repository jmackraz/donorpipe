#! /usr/bin/env python3
from __future__ import annotations

import argparse
import cmd
import datetime
import io
import itertools
from collections.abc import Iterable
from contextlib import redirect_stdout
from typing import Any

from consolemenu import SelectionMenu
from dateutil import parser as dateparser

from donorpipe.datewindow import VALID_INTERVALS
from donorpipe.models.transaction_filter import TransactionFilter
from donorpipe.models.transaction_loader import TransactionLoader
from donorpipe.models.transaction_store import TransactionStore
from donorpipe.models.transactions import Donation, Receipt, Transaction
from donorpipe.models.util import paged_print


def list_donations(tx_store: TransactionStore, donations: Iterable[Donation] | None = None,
                   show_chain: bool = True, long_form: bool = False, all_fields: bool = False) -> None:
    if donations is None:
        donations = tx_store.donations.values()
    for donation in donations:
        print(donation.descr() if long_form else donation)
        if all_fields:
            print(donation.record)
            print(donation.filename)
        if show_chain:
            charge = donation.charge
            if charge:
                print(charge)
                payout = charge.payout
                if payout:
                    print(payout)
                else:
                    print(f"payout {charge.payout_id} not found")
            else:
                print("{donation.charge_id} not found")
            if len(donation.receipts) == 1:
                rcpt = donation.receipts[0]
                print(rcpt.descr() if long_form else rcpt)
            elif len(donation.receipts) > 1:
                print("duplicate receipts:")
                for rcpt in donation.receipts:
                    print(rcpt.descr() if long_form else rcpt)
        print()

def list_payouts(tx_store: TransactionStore, payouts: Iterable[Any] | None = None) -> None:
    if not payouts:
        payouts = tx_store.payouts.values()
    for payout in payouts:
        print(payout)
        charges = payout.charges
        if charges:
            for charge in charges:
                print(charge)
        else:
            print(f"charges not found")
        print()

def list_receipts(tx_store: TransactionStore, receipts: Iterable[Receipt] | None = None,
                  show_chain: bool = True, long_form: bool = False, all_fields: bool = False) -> None:
    if not receipts:
        receipts = tx_store.receipts.values()
    for receipt in receipts:
        print(receipt.descr() if long_form else receipt)
        if all_fields:
            print(receipt.record)
            print(receipt.filename)
        if show_chain:
            if receipt.donation:
                print(receipt.donation)
            else:
                print("No donation found for this receipt.")
        print()


class ExpenseReportingCmd(cmd.Cmd):
    prompt = 'qvc>  '

    def __init__(self, tx_loader: Any) -> None:
        super().__init__()
        self.loader = tx_loader
        self.services: list[str] = []
        self.tx_store: TransactionStore | None = None
        self.prev_listing = ""  # last donations or payouts command, for repeating
        self.filter = TransactionFilter()

        self.update_tx_store()   # inits tx_store and services

    def update_tx_store(self) -> None:
        self.tx_store = self.loader.load()
        self.services = list({t.service for t in itertools.chain(self.tx_store.donations.values(),  # type: ignore[union-attr]
                                                                 self.tx_store.charges.values(),  # type: ignore[union-attr]
                                                                 self.tx_store.payouts.values(),  # type: ignore[union-attr]
                                                                 self.tx_store.receipts.values(),  # type: ignore[union-attr]
                                                                 self.tx_store.deposits.values())})  # type: ignore[union-attr]

    # multiple commands on one line
    def precmd(self, line: str) -> str:
        cmds = line.split(";")
        if len(cmds) > 1:
            self.cmdqueue.extend(cmds)
        else:
            return cmds[0]
        return ""

    def show_filters(self) -> None:
        """show current filter spec"""
        self.filter.show_filters()

    def do_reload(self, _: str) -> None:
        """Reload the transaction data from the CSV file"""
        self.update_tx_store()
        self.show_filters()

    def do_filter(self, arg: str) -> None:
        """Add or remove filter conditions (abbreviation: "f")
        Options "reset" to clear, service, name (pattern). Without an argument, show current filter.
        Date window filtering is controlled with 'start' and 'interval' commands.
        """
        method_args = arg.split()
        if not method_args:
            self.show_filters()
            return

        if method_args[0] == "reset":
            self.filter.reset()

        elif method_args[0] == "service":
            if len(method_args) < 2:
                svc = console_menu_select(self.services, "Select Account to include or exclude.")
            else:
                svc = method_args[1]

            if svc == "reset":
                self.filter.clear_services()
            elif svc == "all":
                for svc in self.services :
                    self.filter.add_service(svc)
            elif svc not in self.services:
                print("service must be one of:", self.services)
            else:
                self.filter.toggle_service(svc)  # type: ignore[arg-type]


        elif method_args[0] == "name":
            if len(method_args) < 2:
                print(f"current filter: {self.filter.filter_spec['name']}")
                return

            pat = method_args[1]
            if pat == "reset":
                self.filter.clear_name_pattern()
            else:
                self.filter.set_name_pattern(pat)
        else:
            print("options include reset, service, name")

        self.show_filters()

    def do_f(self, arg: str) -> None:
        """Shortcut for 'filter'"""
        self.do_filter(arg)



    def do_donations(self, arg: str) -> None:
        """Print the filtered list of donations in various ways. (abbreviation: "d")
        Options include 'short', 'associations', 'duplicates', 'missing', 'errors' (abbreviations work)
        Note that appending " /a" will print the full CSV-file record for each donation.
        """
        list_choices = ('short', 'associations', 'duplicates', 'missing', 'errors')
        list_choices_desc = ('short - summary listing',
                             'associations - charges, payouts, receipts linked to donation',
                             'duplicates - entered multiple times',
                             'missing - has no corresponding receipt (good for new data entry)',
                             'errors - discrepancies between donation and receipts'
                             )

        arg, long_form, show_all = complete_args(arg, list_choices, list_choices_desc)  # type: ignore[misc]

        the_list = self.tx_store.donations.values()  # type: ignore[union-attr]
        if not the_list:
            return
        the_list = sorted( self.filter.apply(the_list), key=lambda t: t.date)  # type: ignore[arg-type]

        # capture stdout to string, for paging
        str_io = io.StringIO()
        with redirect_stdout(str_io):
            if arg == "short":
                self.prev_listing = "donations short"
                for d in the_list:
                    print(d.descr() if long_form else d)  # type: ignore[attr-defined]

            elif arg == "associations":
                self.prev_listing = "donations associations"
                list_donations(self.tx_store, the_list, show_chain=True, long_form=long_form, all_fields=show_all)  # type: ignore[arg-type]

            elif arg == "missing":
                self.prev_listing = "donations missing"
                the_list = filter(lambda d: not d.receipts, the_list)  # type: ignore[attr-defined]
                list_donations(self.tx_store, the_list, show_chain=True, long_form=True, all_fields=show_all)  # type: ignore[arg-type]

            elif arg == "duplicates":
                self.prev_listing = "donations duplicates"
                the_list = filter(lambda d: len(d.receipts) > 1, the_list)  # type: ignore[attr-defined]
                list_donations(self.tx_store, the_list, show_chain=True, long_form=True, all_fields=show_all)  # type: ignore[arg-type]

            elif arg == "errors":
                self.prev_listing = "donations errors"
                def f(d: Donation) -> bool:
                    for rcpt in d.receipts:
                        if rcpt.discrepancies:
                            return True
                    return False
                the_list = filter(f, the_list)  # type: ignore[arg-type]
                list_donations(self.tx_store, the_list, show_chain=True, long_form=True, all_fields=show_all)  # type: ignore[arg-type]


            else:
                print(f"{arg} not implemented yet.")
        s = str_io.getvalue()
        paged_print(s)

    def do_d(self, arg: str) -> None:
        """Shortcut for 'donations', but defaults to 'short' listing"""
        self.do_donations(arg or "short")

    def do_list(self, _: str) -> None:
        """Repeat last donation or payout listing command (abbreviation: "l")"""
        if self.prev_listing:
            self.cmdqueue.append(self.prev_listing)
        else:
            print("no listing history yet.")

    def do_l(self, _: str) -> None:
        """Shortcut for 'list'"""
        self.do_list(_)

    def do_payouts(self, _: str) -> None:
        """list payouts and their associated charges (for reconciliation matching)"""

        self.prev_listing = "payouts"
        the_list = self.tx_store.payouts.values()  # type: ignore[union-attr]
        if not the_list:
            return
        the_list = sorted(self.filter.apply(the_list), key=lambda t: t.date)  # type: ignore[arg-type]

        str_io = io.StringIO()
        with redirect_stdout(str_io):
            list_payouts(self.tx_store, the_list)  # type: ignore[arg-type]
        s = str_io.getvalue()
        paged_print(s)

    def do_receipts(self, arg: str) -> None:
        """Print the filtered list of receipts in various ways. (abbreviation: "r")
        Options include 'short', 'missing'
        Note that appending " /a" will print the full CSV-file record for each receipt.
        """
        receipt_list_choices = ('short', 'long', 'associations', 'missing')
        receipt_list_choices_desc = ('short - summary event listing',
                                     'long - listing with more information',
                                     'associations - donation, ... linked to receipt',
                                     'missing - online receipts with no corresponding donation',
                                     )

        arg, long_form, show_all = complete_args(arg, receipt_list_choices, receipt_list_choices_desc)  # type: ignore[misc]

        the_list = self.tx_store.receipts.values()  # type: ignore[union-attr]
        if not the_list:
            return
        the_list = sorted( self.filter.apply(the_list), key=lambda t: t.date)  # type: ignore[arg-type]

        # capture stdout to string, for paging
        str_io = io.StringIO()
        with redirect_stdout(str_io):
            if arg == "short":
                self.prev_listing = "receipts short"
                for r in the_list:
                    print(r.descr() if long_form else r)  # type: ignore[attr-defined]

            elif arg == "long":
                self.prev_listing = "receipts short"
                for r in the_list:
                    print(r.descr())  # type: ignore[attr-defined]

            elif arg == "associations":
                self.prev_listing = "receipts associations"
                list_receipts(self.tx_store, the_list, show_chain=True, long_form=long_form, all_fields=show_all)  # type: ignore[arg-type]

            elif arg == "missing":
                self.prev_listing = "receipts missing"
                the_list = filter(lambda r: not r.donation and "Online" in r.product, the_list)  # type: ignore[attr-defined]
                list_receipts(self.tx_store, the_list, show_chain=True, long_form=True, all_fields=show_all)  # type: ignore[arg-type]

            else:
                print(f"{arg} not implemented yet.")
        s = str_io.getvalue()
        paged_print(s)

    def do_r(self, arg: str) -> None:
        """Shortcut for 'receipts', but defaults to 'short' listing"""
        self.do_receipts(arg or "short")

    # Sliding Date Window #

    def do_start(self, arg: str) -> None:
        """Set beginning of date range (will be 'rounded down' to the natural week/month/year interval start date)"""
        if arg == "reset":
            self.filter.clear_date_window()
        else:
            try:
                date_defaults = datetime.datetime( datetime.datetime.now().year, 1, 1)
                start_date = dateparser.parse(arg, default=date_defaults).date()
                print(start_date)
                self.filter.set_start_date(start_date)
            except ValueError as e:
                print(f"An unexpected error occurred: {e.__class__.__name__}: {e}")
                print(f"Not a valid date: {arg}")

        self.show_filters()

    def do_interval(self, arg: str) -> None:
        """Set the reporting interval."""
        if not arg:
            arg = console_menu_select(VALID_INTERVALS, "Choose an interval")  # type: ignore[assignment]
            if not arg:
                return
        try:
            self.filter.set_interval(arg)
        except ValueError:
            print(f"Invalid interval: {arg}")
        self.show_filters()

    def do_next(self, arg: str) -> None:
        """Move filter date window to the next interval"""
        self.filter.shift_date_window(1)
    def do_n(self, arg: str) -> None:
        """Shortcut for 'next' followed by 'list'"""
        self.do_next(arg)
        self.do_list(arg)
    def do_prev(self, arg: str) -> None:
        """Move filter date window to the previous interval"""
        self.filter.shift_date_window(-1)
    def do_p(self, arg: str) -> None:
        """Shortcut for 'prev' followed by 'list'"""
        self.do_prev(arg)
        self.do_list(arg)

    @staticmethod
    def do_q(_: str) -> bool:
        """quit"""
        return True
    @staticmethod
    def do_quit(_: str) -> bool:
        """quit"""
        return True
    @staticmethod
    def do_EOF(_: str) -> bool:
        """Exit on Ctrl-D"""
        print("EOF")
        return True

    def do_readcmds(self, arg: str) -> None:
        """ Read command strings from a specified file (or a default) and append them to the command queue
        Usage: readcmds <filename>
        """
        file_name = arg if arg else "default_commands.txt"
        try:
            with open(file_name, 'r') as file:
                commands = file.readlines()
                # Strip whitespace and filter out any empty lines
                commands = [command.strip() for command in commands if command.strip() and not command.strip().startswith('#')]
                self.cmdqueue.extend(commands)
                print(f"Commands from '{file_name}' have been added to the queue:\n\t{"\n\t".join(commands)}")
        except FileNotFoundError:
            print(f"File '{file_name}' not found.")
        except Exception as e:
            print(f"An error occurred while reading the file: {e.__class__.__name__}: {e}")

    def do_go(self, _: str) -> None:
        """Shortcut for 'readcmds'"""
        self.do_readcmds("")


def console_menu_select(choice_items: Iterable[Any], prompt: str,
                        desc_items: Iterable[Any] | None = None) -> Any | None:
    choices: list[Any] = list(choice_items)
    desc_list: list[Any] = list(desc_items) if desc_items else []
    item_list: list[Any] = desc_list or choices
    selection = SelectionMenu.get_selection(item_list, title=prompt )
    if 0 <= selection < len(item_list):
        return choices[selection]
    else:
        return None

def complete_args(arg: str, choices: tuple[str, ...] | None = None,
                  descriptions: tuple[str, ...] | None = None) -> tuple[str, bool, bool] | None:
    if "/l" in arg:
        long_form = True
        arg = arg.replace("/l", "").strip()
    else:
        long_form = False

    if "/a" in arg:
        show_all = True
        arg = arg.replace("/a", "").strip()
    else:
        show_all = False

    if choices and not arg:
        arg = console_menu_select(choices, "Choose donations to display", desc_items=descriptions)  # type: ignore[assignment]

    arg_matches = list(filter(lambda choice: choice.startswith(arg), choices))  # type: ignore[arg-type]
    match_count = len(arg_matches)
    if match_count == 0:
        print(f"{arg} not a valid choice.")
        return
    elif match_count > 1:
        print(f"{arg} is ambiguous.")
        return
    else:
        arg = arg_matches[0]

    return arg, long_form, show_all


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", dest='files', nargs='+', action='extend', required=False)
    parser.add_argument("--dir", "-d", dest='dirs', nargs='+', action='extend', required=False)
    args = parser.parse_args()
    if args.files is None and args.dirs is None:
        parser.error("At least one of --file/-f or --dir/-d is required")

    loader = TransactionLoader(args.files or [], args.dirs or [])
    ExpenseReportingCmd(loader).cmdloop()
