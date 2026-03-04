#! /usr/bin/env python3
# main
import argparse

from donorpipe.cli.cmd_loop import ExpenseReportingCmd
from donorpipe.models.transaction_loader import TransactionLoader


#old_dirs_filepat =  re.compile(r'[^a-zA-Z]*old[^a-zA-Z]*', re.IGNORECASE)
#readline.parse_and_bind("bind ^I rl_complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", "-f", dest='files', nargs='+', action='extend', required=False)
    parser.add_argument("--dir", "-d", dest='dirs', nargs='+', action='extend', required=False)
    args = parser.parse_args()
    if args.files is None and args.dirs is None:
        parser.error("At least one of --file/-f or --dir/-d is required")

    loader = TransactionLoader(args.files or [], args.dirs or [])
    ExpenseReportingCmd(loader).cmdloop()