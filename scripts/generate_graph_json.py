#! /usr/bin/env python3
"""Generate tests/data/graph.json from real CSV exports.

Usage:
    env OSF_EXPORTS=testdata uv run scripts/generate_graph_json.py -d Stripe DonorBox QBO
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# ensure src is importable when run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from donorpipe.models.transaction_loader import TransactionLoader

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "tests", "data", "graph.json")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate graph.json from CSV exports")
    parser.add_argument("--file", "-f", dest="files", nargs="+", action="extend", required=False)
    parser.add_argument("--dir", "-d", dest="dirs", nargs="+", action="extend", required=False)
    args = parser.parse_args()

    if args.files is None and args.dirs is None:
        parser.error("At least one of --file/-f or --dir/-d is required")

    loader = TransactionLoader(args.files or [], args.dirs or [])
    tx_store = loader.load()

    graph = tx_store.to_graph()

    output_path = os.path.abspath(OUTPUT_PATH)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    print(f"Wrote {output_path}")
    print(f"  donations: {len(graph['donations'])}, charges: {len(graph['charges'])}, "
          f"payouts: {len(graph['payouts'])}, receipts: {len(graph['receipts'])}")


if __name__ == "__main__":
    main()
