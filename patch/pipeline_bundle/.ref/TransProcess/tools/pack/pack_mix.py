#!/usr/bin/env python3
"""
Pack files into a Westwood MIX archive.
"""

from __future__ import annotations

import argparse
from pathlib import Path


def calculate_fold_hash(filename: str) -> int:
    name = filename.upper()
    i = 0
    h = 0
    while i < len(name) and i < 12:
        group_sum = 0
        for _ in range(4):
            group_sum >>= 8
            if i < len(name):
                group_sum |= ord(name[i]) << 24
                i += 1
            else:
                group_sum |= 0
        h = ((h << 1) | ((h >> 31) & 1)) + group_sum
    return h & 0xFFFFFFFF


def load_manifest(manifest: Path) -> list[str]:
    names: list[str] = []
    for line in manifest.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        names.append(stripped)
    return names


def pack_mix(input_dir: Path, output_mix: Path, names: list[str]) -> None:
    entries: list[tuple[int, int, int, bytes, str]] = []
    offset = 0
    seen_hashes: dict[int, str] = {}

    for name in names:
        path = input_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"Missing input file: {path}")

        data = path.read_bytes()
        h = calculate_fold_hash(name)
        if h in seen_hashes:
            raise RuntimeError(f"Hash collision: {name} vs {seen_hashes[h]} (0x{h:08X})")
        seen_hashes[h] = name

        entries.append((h, offset, len(data), data, name))
        offset += len(data)

    output_mix.parent.mkdir(parents=True, exist_ok=True)
    with output_mix.open("wb") as f:
        f.write(len(entries).to_bytes(2, "little"))
        f.write(offset.to_bytes(4, "little"))

        for h, off, size, _data, _name in entries:
            f.write(h.to_bytes(4, "little"))
            f.write(off.to_bytes(4, "little"))
            f.write(size.to_bytes(4, "little"))

        for _h, _off, _size, data, _name in entries:
            f.write(data)

    print(f"[MIX] wrote {output_mix} ({len(entries)} files, {offset} data bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pack a Westwood MIX archive")
    parser.add_argument("input_dir", help="Input folder containing files to pack")
    parser.add_argument("output_mix", help="Output MIX path")
    parser.add_argument("--manifest", help="Optional manifest file with explicit filenames and order")
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_mix = Path(args.output_mix)

    if args.manifest:
        names = load_manifest(Path(args.manifest))
    else:
        names = sorted(p.name for p in input_dir.iterdir() if p.is_file())

    if not names:
        raise SystemExit("No files to pack")

    pack_mix(input_dir, output_mix, names)


if __name__ == "__main__":
    main()
