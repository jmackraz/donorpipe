#!/usr/bin/env python3
"""Fetch and display the transaction graph from the DonorPipe API."""

import argparse
import json
import sys

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch transaction graph from DonorPipe API")
    parser.add_argument("--account", required=True, help="Account ID")
    parser.add_argument(
        "--base-url", default="http://localhost:8000", help="API base URL (default: http://localhost:8000)"
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON instead of summary")
    args = parser.parse_args()

    url = f"{args.base_url}/accounts/{args.account}/graph"
    print(f"GET {url}", file=sys.stderr)

    response = httpx.get(url)
    response.raise_for_status()
    graph = response.json()

    if args.json:
        print(json.dumps(graph, indent=2))
    else:
        for key, entities in graph.items():
            print(f"  {key}: {len(entities)}")


if __name__ == "__main__":
    main()
