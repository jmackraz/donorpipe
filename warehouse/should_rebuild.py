#!/usr/bin/env python3
"""Determine whether graph.json needs to be rebuilt.

Compares the file manifest embedded in an existing graph.json against the
current state of the filesystem.

Exit codes:
  0 — rebuild needed
  1 — graph is up to date (no changes detected)

Usage:
  uv run warehouse/should_rebuild.py --graph PATH/graph.json [--dir DIR ...]

--dir may be given multiple times. When supplied, the directories are scanned
for .csv files (skipping 'old/' subdirs); any CSV not listed in the manifest
is treated as a new file that requires a rebuild.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys


_OLD_DIR = re.compile(r"(?<![a-zA-Z])old(?![a-zA-Z])", re.IGNORECASE)

REBUILD_NEEDED = 0
UP_TO_DATE = 1


def find_csvs(directories: list[str]) -> set[str]:
    found: set[str] = set()
    for d in directories:
        d = os.path.expanduser(d)
        for root, _, filenames in os.walk(d, followlinks=True):
            if _OLD_DIR.search(root):
                continue
            for name in filenames:
                if name.lower().endswith(".csv"):
                    found.add(os.path.join(root, name))
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether graph.json needs rebuilding")
    parser.add_argument("--graph", required=True, help="Path to existing graph.json")
    parser.add_argument("--dir", dest="dirs", action="append", default=[], metavar="DIR",
                        help="Data directory to scan for new CSV files (may be repeated)")
    args = parser.parse_args()

    # ── Load graph.json ────────────────────────────────────────────────────────
    if not os.path.exists(args.graph):
        print(f"[should_rebuild] graph not found: {args.graph} → rebuild needed")
        sys.exit(REBUILD_NEEDED)

    with open(args.graph) as f:
        try:
            graph = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[should_rebuild] graph unreadable ({e}) → rebuild needed")
            sys.exit(REBUILD_NEEDED)

    meta = graph.get("_meta")
    if not meta or not meta.get("files"):
        print("[should_rebuild] graph has no manifest (_meta) → rebuild needed")
        sys.exit(REBUILD_NEEDED)

    # ── Check each file in the manifest ───────────────────────────────────────
    manifest_paths: set[str] = set()
    for entry in meta["files"]:
        path = entry["path"]
        manifest_paths.add(path)

        if not os.path.exists(path):
            print(f"[should_rebuild] REMOVED: {path} → rebuild needed")
            sys.exit(REBUILD_NEEDED)

        st = os.stat(path)

        if st.st_size != entry["size"]:
            print(f"[should_rebuild] SIZE CHANGED: {path} "
                  f"(was {entry['size']}, now {st.st_size}) → rebuild needed")
            sys.exit(REBUILD_NEEDED)

        current_mtime = st.st_mtime
        # mtime stored as ISO 8601; compare as float via round-trip
        import datetime
        stored_mtime_dt = datetime.datetime.fromisoformat(entry["mtime"])
        stored_mtime = stored_mtime_dt.timestamp()

        if abs(current_mtime - stored_mtime) > 1.0:  # 1-second tolerance
            print(f"[should_rebuild] MODIFIED: {path} "
                  f"(mtime changed) → rebuild needed")
            sys.exit(REBUILD_NEEDED)

    # ── Check for new CSV files not in the manifest ───────────────────────────
    if args.dirs:
        current_csvs = find_csvs(args.dirs)
        new_files = current_csvs - manifest_paths
        if new_files:
            for f in sorted(new_files):
                print(f"[should_rebuild] NEW FILE: {f} → rebuild needed")
            sys.exit(REBUILD_NEEDED)

    print(f"[should_rebuild] all {len(manifest_paths)} files unchanged → no rebuild needed")
    sys.exit(UP_TO_DATE)


if __name__ == "__main__":
    main()
