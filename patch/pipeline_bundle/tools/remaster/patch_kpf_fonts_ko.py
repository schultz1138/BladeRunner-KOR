#!/usr/bin/env python3
"""
Patch fonts.kpf by replacing UI body fonts with a Korean-capable TTF.

Default behavior:
- Replace fonts/NotoSans-Regular.ttf
- Replace fonts/NotoSans-Bold.ttf
- Replace fonts/NotoSans-ExtraCondensedMedium.ttf
- Replace fonts/Montserrat-Regular.ttf
with the same source font file.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile


TARGET_ENTRIES = [
    "fonts/NotoSans-Regular.ttf",
    "fonts/NotoSans-Bold.ttf",
    "fonts/NotoSans-ExtraCondensedMedium.ttf",
    "fonts/Montserrat-Regular.ttf",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch fonts.kpf with Korean-capable font")
    parser.add_argument(
        "--input-kpf",
        default=r".ref\BladeRunner_Enhanced\fonts.kpf",
        help="Source fonts.kpf path",
    )
    parser.add_argument(
        "--output-kpf",
        default=r".tmp\remaster_patch\fonts_poc_ko.kpf",
        help="Output patched fonts.kpf path",
    )
    parser.add_argument(
        "--font-file",
        default=r".ref\TransProcess\assets\fonts\Kor_font.ttf",
        help="TTF file to inject for NotoSans regular/bold",
    )
    args = parser.parse_args()

    input_kpf = Path(args.input_kpf).resolve()
    output_kpf = Path(args.output_kpf).resolve()
    font_file = Path(args.font_file).resolve()

    if not input_kpf.exists():
        raise FileNotFoundError(f"Input KPF not found: {input_kpf}")
    if not font_file.exists():
        raise FileNotFoundError(f"Font file not found: {font_file}")

    output_kpf.parent.mkdir(parents=True, exist_ok=True)
    font_bytes = font_file.read_bytes()
    replaced_entries: list[str] = []

    with zipfile.ZipFile(input_kpf, "r") as zin, zipfile.ZipFile(output_kpf, "w") as zout:
        seen = set()
        for info in zin.infolist():
            name = info.filename
            lower_name = name.lower()
            matched = next((t for t in TARGET_ENTRIES if lower_name == t.lower()), None)
            if matched:
                new_info = zipfile.ZipInfo(filename=info.filename, date_time=info.date_time)
                new_info.compress_type = info.compress_type
                new_info.comment = info.comment
                new_info.extra = info.extra
                new_info.create_system = info.create_system
                new_info.external_attr = info.external_attr
                new_info.internal_attr = info.internal_attr
                new_info.flag_bits = info.flag_bits
                zout.writestr(new_info, font_bytes)
                replaced_entries.append(info.filename)
                seen.add(matched.lower())
            else:
                zout.writestr(info, zin.read(name))

        # If expected entries are missing, add them.
        for target in TARGET_ENTRIES:
            if target.lower() in seen:
                continue
            zout.writestr(target, font_bytes, compress_type=zipfile.ZIP_DEFLATED)
            replaced_entries.append(target)

    print(f"[OK] input_kpf : {input_kpf}")
    print(f"[OK] output_kpf: {output_kpf}")
    print(f"[OK] font_file : {font_file}")
    print(f"[OK] replaced_entries ({len(replaced_entries)}):")
    for name in replaced_entries:
        print(f"  - {name}")
    print(f"[SHA256] input : {sha256_file(input_kpf)}")
    print(f"[SHA256] output: {sha256_file(output_kpf)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
