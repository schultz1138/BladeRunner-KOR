#!/usr/bin/env python3
"""
Validate in-game subtitle table integrity (CSV/TSV) for INGQUO-like files.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

AUD_RE = re.compile(r"^(\d{2})-(\d{4})\.AUD$", re.IGNORECASE)


def filename_to_id(filename: str) -> int:
    m = AUD_RE.match(filename.strip())
    if not m:
        raise ValueError(f"Invalid filename format: {filename}")
    return int(m.group(1)) * 10000 + int(m.group(2))


def detect_delimiter(path: Path) -> str:
    default = "\t" if path.suffix.lower() == ".tsv" else ","
    sample = path.read_text(encoding="utf-8-sig", errors="replace")[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
        return dialect.delimiter
    except csv.Error:
        return default


def read_id_set(table_path: Path) -> tuple[set[int], list[str]]:
    issues: list[str] = []
    ids: set[int] = set()

    delimiter = detect_delimiter(table_path)
    with table_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if not reader.fieldnames or "Filename" not in reader.fieldnames:
            issues.append(f"{table_path.name}: missing Filename header")
            return ids, issues

        for idx, row in enumerate(reader, start=2):
            filename = str(row.get("Filename") or "").strip()
            if not filename:
                issues.append(f"{table_path.name}:{idx}: empty Filename")
                continue
            try:
                id_val = filename_to_id(filename)
            except ValueError as e:
                issues.append(f"{table_path.name}:{idx}: {e}")
                continue
            if id_val in ids:
                issues.append(f"{table_path.name}:{idx}: duplicate id {id_val}")
            ids.add(id_val)

    return ids, issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate in-game subtitle table file (CSV/TSV)")
    parser.add_argument("table_path", help="Path to target table file")
    parser.add_argument("--baseline", help="Optional baseline table for ID set comparison")
    args = parser.parse_args()

    table_path = Path(args.table_path)
    ids, issues = read_id_set(table_path)

    if args.baseline:
        base_ids, base_issues = read_id_set(Path(args.baseline))
        issues.extend(base_issues)
        missing = sorted(base_ids - ids)
        extra = sorted(ids - base_ids)
        if missing:
            issues.append(f"Missing IDs vs baseline: {len(missing)} (first 10: {missing[:10]})")
        if extra:
            issues.append(f"Extra IDs vs baseline: {len(extra)} (first 10: {extra[:10]})")

    if issues:
        for line in issues:
            print(f"[FAIL] {line}")
        raise SystemExit(1)

    print(f"[OK] {table_path.name}: {len(ids)} IDs validated")


if __name__ == "__main__":
    main()
