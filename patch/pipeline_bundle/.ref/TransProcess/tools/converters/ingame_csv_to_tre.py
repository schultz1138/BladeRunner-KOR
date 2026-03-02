#!/usr/bin/env python3
"""
Convert Blade Runner in-game subtitle table files (Filename,Actor,EN,KO) into *_E.TRE files.

ID mapping rule:
- Filename format must be NN-NNNN.AUD
- TRE id = int(NN) * 10000 + int(NNNN)

This mapping avoids index-shift bugs when rows are reordered or missing.
"""

from __future__ import annotations

import argparse
import csv
import re
import struct
from pathlib import Path

AUD_RE = re.compile(r"^(\d{2})-(\d{4})\.AUD$", re.IGNORECASE)


class IngameCsvError(RuntimeError):
    pass


def filename_to_id(filename: str) -> int:
    m = AUD_RE.match(filename.strip())
    if not m:
        raise IngameCsvError(f"Invalid filename format: {filename}")
    chapter = int(m.group(1))
    line_id = int(m.group(2))
    return chapter * 10000 + line_id


def detect_delimiter(path: Path) -> str:
    default = "\t" if path.suffix.lower() == ".tsv" else ","
    sample = path.read_text(encoding="utf-8-sig", errors="replace")[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
        return dialect.delimiter
    except csv.Error:
        return default


def read_rows(table_path: Path, fallback_en: bool, keep_empty: bool) -> list[tuple[int, str, str]]:
    rows: list[tuple[int, str, str]] = []
    seen_ids: set[int] = set()

    delimiter = detect_delimiter(table_path)
    with table_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        required = {"Filename", "KO"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise IngameCsvError(f"Missing required headers in {table_path}. Need at least: Filename,KO")

        for idx, row in enumerate(reader, start=2):
            filename = str(row.get("Filename") or "").strip()
            if filename == "":
                continue

            try:
                id_val = filename_to_id(filename)
            except IngameCsvError as e:
                raise IngameCsvError(f"{table_path.name}:{idx}: {e}") from e

            if id_val in seen_ids:
                raise IngameCsvError(f"{table_path.name}:{idx}: duplicate id {id_val} ({filename})")
            seen_ids.add(id_val)

            ko = str(row.get("KO") or "").replace("\r\n", "\n").replace("\r", "\n").strip()
            en = str(row.get("EN") or "").replace("\r\n", "\n").replace("\r", "\n").strip()

            text = ko if ko else (en if fallback_en else "")
            if text == "" and not keep_empty:
                continue

            rows.append((id_val, filename.upper(), text))

    rows.sort(key=lambda x: x[0])
    return rows


def write_tre(entries: list[tuple[int, str, str]], out_path: Path) -> tuple[int, int]:
    count = len(entries)
    ids: list[int] = []
    offsets: list[int] = []
    strings: list[bytes] = []

    current = 4 * (2 * count + 1)
    for id_val, _filename, text in entries:
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


def convert_dir(input_dir: Path, output_dir: Path, fallback_en: bool, keep_empty: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    table_files = collect_table_files(input_dir)
    if not table_files:
        print(f"[WARN] no ingame table files (.csv/.tsv) in {input_dir}")
        return

    for table_file in table_files:
        entries = read_rows(table_file, fallback_en=fallback_en, keep_empty=keep_empty)
        out_file = output_dir / f"{table_file.stem.upper()}_E.TRE"
        count, size = write_tre(entries, out_file)
        print(f"[ING] {table_file.name} -> {out_file.name}: {count} entries, {size} bytes")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert in-game subtitle table files (CSV/TSV) to TRE")
    parser.add_argument("input_dir", help="Input folder containing in-game table files")
    parser.add_argument("output_dir", help="Output folder for TRE files")
    parser.add_argument("--no-fallback-en", action="store_true", help="Do not fallback to EN when KO is empty")
    parser.add_argument("--drop-empty", action="store_true", help="Drop entries with both KO/EN empty")
    args = parser.parse_args()

    convert_dir(
        Path(args.input_dir),
        Path(args.output_dir),
        fallback_en=not args.no_fallback_en,
        keep_empty=not args.drop_empty,
    )


if __name__ == "__main__":
    main()
