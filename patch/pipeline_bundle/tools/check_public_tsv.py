#!/usr/bin/env python3
"""
Fail if a TSV contains non-empty values in the `en` column.

Intended for public-repo safety checks.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def normalize(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Check that TSV `en` column is empty")
    parser.add_argument("tsv_path", help="Target TSV path")
    parser.add_argument(
        "--max-print",
        type=int,
        default=20,
        help="Max offending rows to print (default: 20)",
    )
    args = parser.parse_args()

    tsv_path = Path(args.tsv_path).resolve()
    if not tsv_path.exists():
        raise FileNotFoundError(f"TSV not found: {tsv_path}")

    with tsv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        if not reader.fieldnames:
            raise ValueError("Empty TSV")
        if "en" not in reader.fieldnames:
            print(f"[OK] no `en` column: {tsv_path}")
            return 0

        offenders: list[tuple[int, str]] = []
        for line_no, row in enumerate(reader, start=2):
            value = normalize(row.get("en", "") or "")
            if value:
                uid = normalize(row.get("uid", "") or "")
                offenders.append((line_no, uid))

    if not offenders:
        print(f"[OK] `en` column is empty: {tsv_path}")
        return 0

    print(f"[FAIL] found {len(offenders)} row(s) with non-empty `en`: {tsv_path}")
    for line_no, uid in offenders[: max(0, args.max_print)]:
        if uid:
            print(f"  - line {line_no}, uid={uid}")
        else:
            print(f"  - line {line_no}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
