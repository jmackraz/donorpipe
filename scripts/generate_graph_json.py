#! /usr/bin/env python3
"""Generate a graph.json from CSV exports.

The API serves graph.json from each account's data_base directory.
Run this script to build one before starting the dev server.

Usage:
    # Build graph.json into ./testdata (for dev with testdata):
    env OSF_EXPORTS=testdata uv run scripts/generate_graph_json.py -d Stripe DonorBox QBO --output testdata/graph.json

    # Build into tests/data/ (default, for test fixtures):
    env OSF_EXPORTS=testdata uv run scripts/generate_graph_json.py -d Stripe DonorBox QBO
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import sys

# ensure src is importable when run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from donorpipe.models.transaction_loader import TransactionLoader

DEFAULT_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "tests", "data", "graph.json")


def _file_entry(path: str) -> dict:
    st = os.stat(path)
    with open(path, "rb") as f:
        sha256 = hashlib.sha256(f.read()).hexdigest()
    return {
        "path": path,
        "size": st.st_size,
        "mtime": datetime.datetime.fromtimestamp(st.st_mtime, tz=datetime.timezone.utc).isoformat(),
        "sha256": sha256,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate graph.json from CSV exports")
    parser.add_argument("--file", "-f", dest="files", nargs="+", action="extend", required=False)
    parser.add_argument("--dir", "-d", dest="dirs", nargs="+", action="extend", required=False)
    parser.add_argument("--output", "-o", dest="output", default=None, help="Output path (default: tests/data/graph.json)")
    args = parser.parse_args()

    if args.files is None and args.dirs is None:
        parser.error("At least one of --file/-f or --dir/-d is required")

    loader = TransactionLoader(args.files or [], args.dirs or [])
    tx_store = loader.load()

    graph = tx_store.to_graph()
    meta = {
        "generated_at": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
        "files": [_file_entry(f) for f in loader.files],
    }
    graph = {"_meta": meta, **graph}

    output_path = os.path.abspath(args.output if args.output is not None else DEFAULT_OUTPUT_PATH)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    print(f"Wrote {output_path}")
    print(f"  donations: {len(graph['donations'])}, charges: {len(graph['charges'])}, "
          f"payouts: {len(graph['payouts'])}, receipts: {len(graph['receipts'])}")


if __name__ == "__main__":
    main()
