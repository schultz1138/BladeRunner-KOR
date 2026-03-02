#!/usr/bin/env python3
"""
Convert Blade Runner UI table files (ID,Text) into TRE files.
"""

from __future__ import annotations

import argparse
import csv
import struct
from pathlib import Path


def detect_delimiter(path: Path) -> str:
    default = "\t" if path.suffix.lower() == ".tsv" else ","
    sample = path.read_text(encoding="utf-8-sig", errors="replace")[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
        return dialect.delimiter
    except csv.Error:
        return default


def read_rows(table_path: Path) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    delimiter = detect_delimiter(table_path)
    with table_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if not reader.fieldnames:
            return rows

        id_key = None
        text_key = None
        for key in reader.fieldnames:
            if key is None:
                continue
            key_norm = key.strip().lower()
            if key_norm == "id":
                id_key = key
            elif key_norm == "text":
                text_key = key

        if id_key is None or text_key is None:
            raise ValueError(f"Missing ID/Text header in {table_path}")

        for row in reader:
            raw_id = (row.get(id_key) or "").strip()
            raw_text = str(row.get(text_key) or "").replace("\r\n", "\n").replace("\r", "\n").strip()
            if not raw_id:
                continue
            try:
                id_val = int(raw_id)
            except ValueError:
                continue
            if raw_text == "":
                continue
            rows.append((id_val, raw_text))

    rows.sort(key=lambda x: x[0])
    return rows


def write_tre(entries: list[tuple[int, str]], out_path: Path) -> tuple[int, int]:
    count = len(entries)
    ids: list[int] = []
    offsets: list[int] = []
    strings: list[bytes] = []

    current = 4 * (2 * count + 1)
    for id_val, text in entries:
        encoded = text.encode("utf-8") + b"\0"
        ids.append(id_val)
        offsets.append(current)
        strings.append(encoded)
        current += len(encoded)

    offsets.append(current)

    data = bytearray()
    data += struct.pack("<I", count)
    data += b"".join(struct.pack("<I", i) for i in ids)
    data += b"".join(struct.pack("<I", o) for o in offsets)
    data += b"".join(strings)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    return count, len(data)


def collect_table_files(input_dir: Path) -> list[Path]:
    picked: dict[str, Path] = {}
    candidates = sorted(
        list(input_dir.glob("*.tsv")) + list(input_dir.glob("*.csv")),
        key=lambda p: (p.stem.lower(), 0 if p.suffix.lower() == ".tsv" else 1, p.name.lower()),
    )
    for path in candidates:
        stem = path.stem.lower()
        if stem not in picked:
            picked[stem] = path
    return sorted(picked.values(), key=lambda p: p.name.lower())


def convert_dir(input_dir: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    table_files = collect_table_files(input_dir)
    if not table_files:
        print(f"[WARN] no UI table files (.csv/.tsv) in {input_dir}")
        return

    for table_file in table_files:
        entries = read_rows(table_file)
        out_file = output_dir / f"{table_file.stem.upper()}.TRE"
        count, size = write_tre(entries, out_file)
        print(f"[UI] {table_file.name} -> {out_file.name}: {count} entries, {size} bytes")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert UI table files (CSV/TSV) to TRE")
    parser.add_argument("input_dir", help="Input folder containing UI table files")
    parser.add_argument("output_dir", help="Output folder for TRE files")
    args = parser.parse_args()

    convert_dir(Path(args.input_dir), Path(args.output_dir))


if __name__ == "__main__":
    main()
