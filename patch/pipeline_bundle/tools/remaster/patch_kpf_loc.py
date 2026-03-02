#!/usr/bin/env python3
"""
Patch a KPF (zip-compatible) by replacing one loc_*.txt entry.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import zipfile


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Replace loc text inside a KPF archive")
    parser.add_argument(
        "--input-kpf",
        default=r".ref\BladeRunner_Enhanced\BladeRunnerEngine.kpf",
        help="Source KPF path",
    )
    parser.add_argument(
        "--output-kpf",
        default=r".tmp\remaster_patch\BladeRunnerEngine_poc_loc_it.kpf",
        help="Output patched KPF path",
    )
    parser.add_argument(
        "--loc-file",
        default=r".tmp\remaster_patch\loc_it.txt",
        help="Localization text file to inject",
    )
    parser.add_argument(
        "--entry-name",
        default="loc_it.txt",
        help="Entry name inside KPF to replace",
    )
    args = parser.parse_args()

    input_kpf = Path(args.input_kpf).resolve()
    output_kpf = Path(args.output_kpf).resolve()
    loc_file = Path(args.loc_file).resolve()
    entry_name = args.entry_name

    if not input_kpf.exists():
        raise FileNotFoundError(f"Input KPF not found: {input_kpf}")
    if not loc_file.exists():
        raise FileNotFoundError(f"LOC file not found: {loc_file}")

    output_kpf.parent.mkdir(parents=True, exist_ok=True)
    loc_bytes = loc_file.read_bytes()

    replaced = False
    with zipfile.ZipFile(input_kpf, "r") as zin, zipfile.ZipFile(output_kpf, "w") as zout:
        for info in zin.infolist():
            name = info.filename
            if name.lower() == entry_name.lower():
                new_info = zipfile.ZipInfo(filename=info.filename, date_time=info.date_time)
                new_info.compress_type = info.compress_type
                new_info.comment = info.comment
                new_info.extra = info.extra
                new_info.create_system = info.create_system
                new_info.external_attr = info.external_attr
                new_info.internal_attr = info.internal_attr
                new_info.flag_bits = info.flag_bits
                zout.writestr(new_info, loc_bytes)
                replaced = True
            else:
                zout.writestr(info, zin.read(name))

        if not replaced:
            # Add missing entry if it does not already exist.
            zout.writestr(entry_name, loc_bytes, compress_type=zipfile.ZIP_DEFLATED)

    print(f"[OK] input_kpf : {input_kpf}")
    print(f"[OK] output_kpf: {output_kpf}")
    print(f"[OK] loc_file  : {loc_file}")
    print(f"[OK] entry     : {entry_name}")
    print(f"[OK] replaced  : {replaced}")
    print(f"[SHA256] input : {sha256_file(input_kpf)}")
    print(f"[SHA256] output: {sha256_file(output_kpf)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
