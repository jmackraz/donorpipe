
import os
import glob
import re
from util import  shorten_gdrive_path
from transaction_store import TransactionStore
import getpass, pathlib, sys


old_dirs_filepat = re.compile(r'(?<![a-zA-Z])old(?![a-zA-Z])', re.IGNORECASE)

def associate_donation_receipts(tx_store):
    for d in tx_store.donations.values():
        if d.tx_id == "F8E63CT3XZ":
            print("ok, weird one")
        receipts = [rcpt for rcpt in tx_store.receipts.values() if rcpt.ref_id == d.tx_id]
        if len(receipts) == 1:
            rcpt = receipts[0]
            # cross-link
            d.receipt = rcpt
            rcpt.donation = d

        if len(receipts) > 1:
            d.duplicate_receipts = receipts
            for rcpt in receipts:
                rcpt.donation = d
        else:
            # no receipt found
            pass

def note_discrepancies(tx_store):
    """ annotate receipts with the fields not matching
    the corresponding donation. Must be called after associate_donation_receipts"""
    for d in tx_store.donations.values():
        for rcpt in d.receipts:
            # print(rcpt)
            discrepancies = []
            if d.name != rcpt.name:
                discrepancies.append('name')
            if d.net != rcpt.net:
                discrepancies.append('net')
            if d.date!= rcpt.date:
                discrepancies.append('date')
            if discrepancies:
                rcpt.discrepancies = " ".join(discrepancies)


class TransactionLoader:
    def __init__(self, filepaths, directories):
        self.filepaths = filepaths
        self.directories = directories
        self.files = []

    def _normalize_directories(self, directories):
        """If OSF_EXPORTS is set, prefix any *relative* directory with it."""
        base = os.environ.get("OSF_EXPORTS")
        if not base:
            return directories

        base = os.path.expanduser(base)
        normalized = []
        for d in directories:
            if not d:
                continue
            d = os.path.expanduser(d)
            if os.path.isabs(d):
                normalized.append(d)
            else:
                normalized.append(os.path.join(base, d))
        return normalized

    def _diagnose_directory(self, d: str, preview_limit: int = 20) -> bool:
        """
        Return True if directory looks accessible for traversal; otherwise print why and return False.
        Also prints a small preview of contents to confirm it's the directory you expect.
        """
        print(f"\n[dir-check] {shorten_gdrive_path(d)}")
        print(f"\n[dir-check] {d}")

        print("user:", getpass.getuser())
        print("uid :", os.getuid())
        print("euid:", os.geteuid())
        print("python:", sys.executable)
        print("cwd:", pathlib.Path().resolve())

        if not os.path.exists(d):
            print("  !! does not exist")
            return False
        if not os.path.isdir(d):
            print("  !! exists but is not a directory")
            return False

        # On macOS/Unix: need X to traverse, and R to list.
        can_read = os.access(d, os.R_OK)
        can_exec = os.access(d, os.X_OK)
        print(f"  access: readable={can_read}, traversable={can_exec}")
        if not (can_read and can_exec):
            print("  !! insufficient permissions to list/traverse")
            return False

        try:
            st = os.stat(d)
            print(f"  stat: size={st.st_size} bytes, mtime={st.st_mtime}")
        except OSError as e:
            print(f"  !! stat failed: {e}")
            return False

        # Quick preview of contents (non-recursive)
        try:
            entries = []
            with os.scandir(d) as it:
                for entry in it:
                    kind = "dir" if entry.is_dir(follow_symlinks=False) else "file"
                    entries.append((kind, entry.name))
                    if len(entries) >= preview_limit:
                        break

            if not entries:
                print("  contents: (empty)")
            else:
                print(f"  contents preview (first {len(entries)}):")
                for kind, name in entries:
                    print(f"    - [{kind}] {name}")
        except OSError as e:
            print(f"  !! listing failed: {e}")
            return False

        return True

    def load(self):
        """This method determines the list of files to load and creates a TransactionStore
        to load and store the transactions.  It then applies some analysis and rules to the loaded transactions."""
        self.files = []

        for g in self.filepaths:
            self.files.extend(glob.glob(g))

        # directory search
        norm_dirs = self._normalize_directories(self.directories)
        print("looking in directories:", norm_dirs)
        for d in norm_dirs:
            # if not self._diagnose_directory(d):
            #     continue

            for root, _, filenames in os.walk(d, followlinks=True):
                if old_dirs_filepat.search(root):
                    # print("skipping:", shorten_gdrive_path(root))
                    continue
                print("looking in:", shorten_gdrive_path(root))

                for filename in filenames:
                    if filename.lower().endswith('.csv'):
                        self.files.append(os.path.join(root, filename))

        tx_store = TransactionStore(self.files)
        tx_store.load()

        # "analytics"
        associate_donation_receipts(tx_store)
        note_discrepancies(tx_store)

        print(
            f"donations: {len(tx_store.donations)}, charges: {len(tx_store.charges)}, payouts: {len(tx_store.payouts)}, deposits: {len(tx_store.deposits)}, receipts: {len(tx_store.receipts)} ")

        return tx_store
