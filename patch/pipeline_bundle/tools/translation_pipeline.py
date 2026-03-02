#!/usr/bin/env python3
"""
Unified translation pipeline utilities.

Step 1:
- Build a single master TSV from local classic translation tables.

Step 2:
- Split master TSV back into ui/cutscene/ingame build input tables.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import struct
import zipfile
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional


TOKEN_RE = re.compile(r"(<[^>]+>|\$[^$]+\$|%[^%]+%)")

CLASSIC_UI_TABLES = [
    "ACTORS",
    "AUTOSAVE",
    "CLUES",
    "CLUETYPE",
    "CRIMES",
    "DLGMENU",
    "ENDCRED",
    "ERRORMSG",
    "HELP",
    "KIA",
    "KIACRED",
    "OPTIONS",
    "SCORERS",
    "SPINDEST",
    "VK",
]

CLASSIC_CUTSCENE_TABLES = [
    "BRLOGO",
    "END01A",
    "END01B",
    "END01C",
    "END01D",
    "END01E",
    "END01F",
    "END03",
    "END04A",
    "END04B",
    "END04C",
    "END06",
    "INTRGT",
    "INTRO",
    "MW_A",
    "MW_B01",
    "MW_B02",
    "MW_B03",
    "MW_B04",
    "MW_B05",
    "MW_C01",
    "MW_C02",
    "MW_C03",
    "MW_D",
    "TB_FLY",
    "WSTLGO",
]


MASTER_COLUMNS = [
    "uid",
    "domain",
    "table",
    "key",
    "filename",
    "frame_start",
    "frame_end",
    "actor",
    "token_sig",
    "en",
    "ko",
    "status",
    "note",
]


def detect_delimiter(path: Path) -> str:
    default = "\t" if path.suffix.lower() == ".tsv" else ","
    sample = path.read_text(encoding="utf-8-sig", errors="replace")[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
        return dialect.delimiter
    except csv.Error:
        return default


def read_dict_rows(path: Path) -> List[dict[str, str]]:
    delimiter = detect_delimiter(path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if not reader.fieldnames:
            return []
        out: List[dict[str, str]] = []
        for row in reader:
            out.append({(k or ""): (v or "") for k, v in row.items()})
        return out


def collect_table_files(input_dir: Path) -> List[Path]:
    picked: Dict[str, Path] = {}
    candidates = sorted(
        list(input_dir.glob("*.tsv")) + list(input_dir.glob("*.csv")),
        key=lambda p: (p.stem.lower(), 0 if p.suffix.lower() == ".tsv" else 1, p.name.lower()),
    )
    for path in candidates:
        stem = path.stem.lower()
        if stem not in picked:
            picked[stem] = path
    return sorted(picked.values(), key=lambda p: p.name.lower())


def find_table_by_stem(root: Path, stem: str) -> Optional[Path]:
    tsv = root / f"{stem}.tsv"
    csv_path = root / f"{stem}.csv"
    if tsv.is_file():
        return tsv
    if csv_path.is_file():
        return csv_path
    return None


def normalize_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n").strip()


def token_sig(value: str) -> str:
    if not value:
        return ""
    return "|".join(TOKEN_RE.findall(value))


def read_ui_id_text(path: Path) -> Dict[int, str]:
    rows = read_dict_rows(path)
    out: Dict[int, str] = {}
    for row in rows:
        id_raw = ""
        text_raw = ""
        for k, v in row.items():
            lk = k.strip().lower()
            if lk == "id":
                id_raw = v
            elif lk == "text":
                text_raw = v
        if id_raw == "":
            continue
        try:
            idx = int(id_raw.strip())
        except ValueError:
            continue
        out[idx] = normalize_text(text_raw)
    return out


def read_cutscene_rows(path: Path) -> List[dict[str, str]]:
    result: List[dict[str, str]] = []
    for row in read_dict_rows(path):
        start_raw = row.get("Frame Start") or row.get("frame_start") or row.get("start") or ""
        end_raw = row.get("Frame End") or row.get("frame_end") or row.get("end") or ""
        text = row.get("KO") or row.get("Text") or ""
        start = normalize_text(start_raw)
        end = normalize_text(end_raw)
        if start == "" or end == "":
            continue
        try:
            int(start)
            int(end)
        except ValueError:
            continue
        result.append(
            {
                "frame_start": start,
                "frame_end": end,
                "text": normalize_text(text),
            }
        )
    return result


def read_ingame_rows(path: Path) -> Dict[str, dict[str, str]]:
    out: Dict[str, dict[str, str]] = {}
    for row in read_dict_rows(path):
        filename = normalize_text(row.get("Filename", "")).upper()
        if filename == "":
            continue
        out[filename] = {
            "filename": filename,
            "actor": normalize_text(row.get("Actor", "")),
            "en": normalize_text(row.get("EN", "")),
            "ko": normalize_text(row.get("KO", "")),
        }
    return out


def make_status(ko: str) -> str:
    return "translated" if normalize_text(ko) else "todo"


def build_master_rows(source_root: Path, include_en: bool) -> List[dict[str, str]]:
    rows: List[dict[str, str]] = []

    ui_ko_root = source_root / "ui" / "ko_work"
    ui_en_root = source_root / "ui" / "en_original"
    cut_ko_root = source_root / "cutscene" / "ko_work"
    cut_en_root = source_root / "cutscene" / "en_reference"
    ing_ko_root = source_root / "ingame" / "ko_work"
    ing_en_root = source_root / "ingame" / "en_reference"

    # UI
    for ko_table in collect_table_files(ui_ko_root):
        table = ko_table.stem.upper()
        ko_map = read_ui_id_text(ko_table)
        en_map: Dict[int, str] = {}
        en_table = find_table_by_stem(ui_en_root, ko_table.stem)
        if en_table is not None:
            en_map = read_ui_id_text(en_table)

        all_ids = sorted(set(ko_map.keys()) | set(en_map.keys()))
        for idx in all_ids:
            en_text = en_map.get(idx, "")
            ko_text = ko_map.get(idx, "")
            rows.append(
                {
                    "uid": f"ui:{table}:{idx}",
                    "domain": "ui",
                    "table": table,
                    "key": str(idx),
                    "filename": "",
                    "frame_start": "",
                    "frame_end": "",
                    "actor": "",
                    "token_sig": token_sig(en_text),
                    "en": en_text if include_en else "",
                    "ko": ko_text,
                    "status": make_status(ko_text),
                    "note": "",
                }
            )

    # Cutscene
    for ko_table in collect_table_files(cut_ko_root):
        table = ko_table.stem.upper()
        ko_entries = read_cutscene_rows(ko_table)
        en_entries: List[dict[str, str]] = []
        en_table = find_table_by_stem(cut_en_root, ko_table.stem)
        if en_table is not None:
            en_entries = read_cutscene_rows(en_table)

        dup_counter: Counter[str] = Counter()
        for i, item in enumerate(ko_entries):
            base_key = f"{item['frame_start']}-{item['frame_end']}"
            dup_counter[base_key] += 1
            key = base_key if dup_counter[base_key] == 1 else f"{base_key}#{dup_counter[base_key]}"
            en_text = en_entries[i]["text"] if i < len(en_entries) else ""
            ko_text = item["text"]
            rows.append(
                {
                    "uid": f"cut:{table}:{key}",
                    "domain": "cutscene",
                    "table": table,
                    "key": key,
                    "filename": "",
                    "frame_start": item["frame_start"],
                    "frame_end": item["frame_end"],
                    "actor": "",
                    "token_sig": token_sig(en_text),
                    "en": en_text if include_en else "",
                    "ko": ko_text,
                    "status": make_status(ko_text),
                    "note": "",
                }
            )

    # In-game
    ing_ko_table = find_table_by_stem(ing_ko_root, "INGQUO")
    if ing_ko_table is None:
        raise FileNotFoundError(f"INGQUO table not found under {ing_ko_root}")
    ing_en_table = find_table_by_stem(ing_en_root, "INGQUO")

    ko_map = read_ingame_rows(ing_ko_table)
    en_map = read_ingame_rows(ing_en_table) if ing_en_table is not None else {}
    all_files = sorted(set(ko_map.keys()) | set(en_map.keys()))
    for filename in all_files:
        en_item = en_map.get(filename, {})
        ko_item = ko_map.get(filename, {})
        en_text = normalize_text(en_item.get("en", ""))
        ko_text = normalize_text(ko_item.get("ko", ""))
        actor = normalize_text(ko_item.get("actor", "") or en_item.get("actor", ""))
        rows.append(
            {
                "uid": f"ing:INGQUO:{filename}",
                "domain": "ingame",
                "table": "INGQUO",
                "key": filename,
                "filename": filename,
                "frame_start": "",
                "frame_end": "",
                "actor": actor,
                "token_sig": token_sig(en_text),
                "en": en_text if include_en else "",
                "ko": ko_text,
                "status": make_status(ko_text),
                "note": "",
            }
        )

    def safe_int(value: str, default: int) -> int:
        try:
            return int(value)
        except ValueError:
            return default

    def sort_key(row: dict[str, str]) -> tuple[int, str, int, int, str]:
        domain_rank = {"ui": 0, "cutscene": 1, "ingame": 2}
        if row["domain"] == "ui":
            return (domain_rank["ui"], row["table"], safe_int(row["key"], 10**9), 0, row["key"])
        if row["domain"] == "cutscene":
            return (
                domain_rank["cutscene"],
                row["table"],
                safe_int(row["frame_start"], 10**9),
                safe_int(row["frame_end"], 10**9),
                row["key"],
            )
        return (domain_rank.get(row["domain"], 99), row["table"], 10**9, 10**9, row["key"])

    rows.sort(key=sort_key)
    return rows


def write_tsv(path: Path, rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=MASTER_COLUMNS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in MASTER_COLUMNS})


def write_table_tsv(path: Path, fieldnames: List[str], rows: Iterable[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def read_master_rows(path: Path) -> List[dict[str, str]]:
    rows = read_dict_rows(path)
    if not rows:
        return rows

    required = {"uid", "domain", "table", "key", "ko"}
    missing = [k for k in sorted(required) if k not in rows[0]]
    if missing:
        raise ValueError(f"master TSV missing required columns: {missing}")
    return rows


def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def copy_reference_folders(base_source_root: Path, output_source_root: Path) -> List[str]:
    copied: List[str] = []
    for rel in ["ui/en_original", "cutscene/en_reference", "ingame/en_reference"]:
        src = base_source_root / rel
        if not src.exists():
            continue
        dst = output_source_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True)
        copied.append(rel)
    return copied


def parse_cut_key_suffix(key: str) -> int:
    if "#" not in key:
        return 1
    tail = key.split("#")[-1].strip()
    try:
        return int(tail)
    except ValueError:
        return 1


def cmd_split_master(args: argparse.Namespace) -> int:
    master_path = Path(args.master).resolve()
    output_source_root = Path(args.output_source_root).resolve()
    base_source_root = Path(args.base_source_root).resolve()
    report_path = Path(args.report_json).resolve() if args.report_json else None

    if not master_path.exists():
        raise FileNotFoundError(f"master TSV not found: {master_path}")

    rows = read_master_rows(master_path)
    clean_dir(output_source_root)

    copied_refs: List[str] = []
    if args.copy_reference:
        if not base_source_root.exists():
            raise FileNotFoundError(f"base source root not found: {base_source_root}")
        copied_refs = copy_reference_folders(base_source_root, output_source_root)

    ui_by_table: Dict[str, Dict[int, str]] = {}
    cut_by_table: Dict[str, List[dict[str, str]]] = {}
    ing_rows: Dict[str, dict[str, str]] = {}
    unknown_domains: Counter[str] = Counter()

    kept_rows = 0
    skipped_rows = 0
    for row in rows:
        domain = normalize_text(row.get("domain", "")).lower()
        table = normalize_text(row.get("table", "")).upper()
        key = normalize_text(row.get("key", ""))
        ko = row.get("ko", "")
        en = row.get("en", "")
        status = normalize_text(row.get("status", "")).lower()
        actor = row.get("actor", "")
        filename = normalize_text(row.get("filename", "")).upper()
        frame_start = normalize_text(row.get("frame_start", ""))
        frame_end = normalize_text(row.get("frame_end", ""))

        if args.translated_only and status != "translated":
            skipped_rows += 1
            continue
        if args.skip_empty_ko and normalize_text(ko) == "":
            skipped_rows += 1
            continue

        if domain == "ui":
            if key == "":
                skipped_rows += 1
                continue
            try:
                idx = int(key)
            except ValueError:
                skipped_rows += 1
                continue
            ui_by_table.setdefault(table, {})[idx] = normalize_text(ko)
            kept_rows += 1
            continue

        if domain == "cutscene":
            if frame_start == "" or frame_end == "":
                skipped_rows += 1
                continue
            try:
                int(frame_start)
                int(frame_end)
            except ValueError:
                skipped_rows += 1
                continue
            cut_by_table.setdefault(table, []).append(
                {
                    "key": key,
                    "Frame Start": frame_start,
                    "Frame End": frame_end,
                    "KO": normalize_text(ko),
                }
            )
            kept_rows += 1
            continue

        if domain == "ingame":
            fn = filename or key
            if fn == "":
                skipped_rows += 1
                continue
            ing_rows[fn] = {
                "Filename": fn,
                "Actor": normalize_text(actor),
                "EN": normalize_text(en),
                "KO": normalize_text(ko),
            }
            kept_rows += 1
            continue

        unknown_domains[domain] += 1
        skipped_rows += 1

    generated_files: List[str] = []
    generated_counts: Dict[str, int] = {
        "ui_tables": 0,
        "cutscene_tables": 0,
        "ingame_rows": 0,
    }

    # UI tables
    for table in sorted(ui_by_table.keys()):
        table_rows = [{"ID": str(i), "Text": text} for i, text in sorted(ui_by_table[table].items(), key=lambda x: x[0])]
        out_path = output_source_root / "ui" / "ko_work" / f"{table}.tsv"
        write_table_tsv(out_path, ["ID", "Text"], table_rows)
        generated_files.append(str(out_path))
        generated_counts["ui_tables"] += 1

    # Cutscene tables
    for table in sorted(cut_by_table.keys()):
        table_rows = cut_by_table[table]
        table_rows.sort(
            key=lambda r: (
                int(r["Frame Start"]),
                int(r["Frame End"]),
                parse_cut_key_suffix(r.get("key", "")),
            )
        )
        out_path = output_source_root / "cutscene" / "ko_work" / f"{table}.tsv"
        write_table_tsv(
            out_path,
            ["Frame Start", "Frame End", "KO"],
            [{k: v for k, v in row.items() if k in {"Frame Start", "Frame End", "KO"}} for row in table_rows],
        )
        generated_files.append(str(out_path))
        generated_counts["cutscene_tables"] += 1

    # In-game table
    ing_out_path = output_source_root / "ingame" / "ko_work" / "INGQUO.tsv"
    ing_table_rows = [ing_rows[name] for name in sorted(ing_rows.keys())]
    write_table_tsv(ing_out_path, ["Filename", "Actor", "EN", "KO"], ing_table_rows)
    generated_files.append(str(ing_out_path))
    generated_counts["ingame_rows"] = len(ing_table_rows)

    report = {
        "master": str(master_path),
        "output_source_root": str(output_source_root),
        "base_source_root": str(base_source_root) if args.copy_reference else None,
        "copy_reference": bool(args.copy_reference),
        "copied_reference_folders": copied_refs,
        "translated_only": bool(args.translated_only),
        "skip_empty_ko": bool(args.skip_empty_ko),
        "rows_input": len(rows),
        "rows_kept": kept_rows,
        "rows_skipped": skipped_rows,
        "unknown_domains": dict(unknown_domains),
        "generated_counts": generated_counts,
        "generated_files": generated_files,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="")

    print(f"[OK] split source root: {output_source_root}")
    print(
        "[INFO] "
        f"ui_tables={generated_counts['ui_tables']} "
        f"cutscene_tables={generated_counts['cutscene_tables']} "
        f"ingame_rows={generated_counts['ingame_rows']}"
    )
    print(f"[INFO] rows input={len(rows)} kept={kept_rows} skipped={skipped_rows}")
    if copied_refs:
        print(f"[INFO] copied refs: {', '.join(copied_refs)}")
    if report_path is not None:
        print(f"[OK] report: {report_path}")
    return 0


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


def parse_mix_entries(mix_bytes: bytes) -> Dict[int, list[tuple[int, int]]]:
    if len(mix_bytes) < 6:
        raise ValueError("Invalid MIX: too small")

    num_entries = int.from_bytes(mix_bytes[0:2], "little")
    table_size = num_entries * 12
    table_start = 6
    body_start = table_start + table_size
    if body_start > len(mix_bytes):
        raise ValueError("Invalid MIX: index table exceeds file size")

    index: Dict[int, list[tuple[int, int]]] = {}
    for i in range(num_entries):
        off = table_start + i * 12
        h = int.from_bytes(mix_bytes[off : off + 4], "little")
        rel = int.from_bytes(mix_bytes[off + 4 : off + 8], "little")
        size = int.from_bytes(mix_bytes[off + 8 : off + 12], "little")
        abs_start = body_start + rel
        abs_end = abs_start + size
        if abs_end > len(mix_bytes):
            continue
        index.setdefault(h, []).append((abs_start, size))
    return index


def get_mix_entry_data(mix_bytes: bytes, mix_index: Dict[int, list[tuple[int, int]]], filename: str) -> bytes:
    h = calculate_fold_hash(filename)
    candidates = mix_index.get(h, [])
    if not candidates:
        raise KeyError(filename)
    # If collisions exist, choose first candidate for deterministic behavior.
    start, size = candidates[0]
    return mix_bytes[start : start + size]


def parse_tre_entries(tre_bytes: bytes) -> list[tuple[int, str]]:
    if len(tre_bytes) < 4:
        raise ValueError("Invalid TRE: too small")

    count = int.from_bytes(tre_bytes[0:4], "little")
    ids_start = 4
    ids_end = ids_start + count * 4
    offs_start = ids_end
    offs_end = offs_start + (count + 1) * 4
    if offs_end > len(tre_bytes):
        raise ValueError("Invalid TRE: header too small for ids/offsets")

    ids = struct.unpack(f"<{count}I", tre_bytes[ids_start:ids_end]) if count else ()
    offs = struct.unpack(f"<{count + 1}I", tre_bytes[offs_start:offs_end]) if count else (offs_end,)

    # TRE offsets in Blade Runner resources are typically relative to byte 4
    # (immediately after the count field), not absolute file offsets.
    offset_base = 0
    if count and offs[0] + 4 == offs_end:
        offset_base = 4

    entries: list[tuple[int, str]] = []
    for i in range(count):
        start = offs[i] + offset_base
        end = offs[i + 1] + offset_base
        if start > end or end > len(tre_bytes):
            continue
        raw = tre_bytes[start:end]
        if raw.endswith(b"\x00"):
            raw = raw[:-1]
        text = raw.decode("utf-8", errors="replace")
        entries.append((ids[i], normalize_text(text)))
    return entries


def write_ui_tables_from_mix(
    mix_bytes: bytes,
    mix_index: Dict[int, list[tuple[int, int]]],
    out_source_root: Path,
    seed_ko_mode: str,
    missing_files: list[str],
) -> int:
    count_tables = 0
    for table in CLASSIC_UI_TABLES:
        name = f"{table}.TRE"
        try:
            tre_bytes = get_mix_entry_data(mix_bytes, mix_index, name)
        except KeyError:
            missing_files.append(name)
            continue

        entries = parse_tre_entries(tre_bytes)
        en_rows = [{"ID": str(idx), "Text": text} for idx, text in sorted(entries, key=lambda x: x[0])]
        if seed_ko_mode == "copy-en":
            ko_rows = [{"ID": row["ID"], "Text": row["Text"]} for row in en_rows]
        else:
            ko_rows = [{"ID": row["ID"], "Text": ""} for row in en_rows]

        write_table_tsv(out_source_root / "ui" / "en_original" / f"{table}.tsv", ["ID", "Text"], en_rows)
        write_table_tsv(out_source_root / "ui" / "ko_work" / f"{table}.tsv", ["ID", "Text"], ko_rows)
        count_tables += 1
    return count_tables


def write_cutscene_tables_from_mix(
    mix_bytes: bytes,
    mix_index: Dict[int, list[tuple[int, int]]],
    out_source_root: Path,
    seed_ko_mode: str,
    missing_files: list[str],
) -> int:
    count_tables = 0
    for table in CLASSIC_CUTSCENE_TABLES:
        name = f"{table}_E.TRE"
        try:
            tre_bytes = get_mix_entry_data(mix_bytes, mix_index, name)
        except KeyError:
            missing_files.append(name)
            continue

        entries = parse_tre_entries(tre_bytes)
        en_rows: List[dict[str, str]] = []
        ko_rows: List[dict[str, str]] = []
        for packed_id, text in entries:
            frame_start = str(packed_id & 0xFFFF)
            frame_end = str((packed_id >> 16) & 0xFFFF)
            en_rows.append({"Frame Start": frame_start, "Frame End": frame_end, "Text": text})
            ko_rows.append(
                {
                    "Frame Start": frame_start,
                    "Frame End": frame_end,
                    "KO": text if seed_ko_mode == "copy-en" else "",
                }
            )

        write_table_tsv(
            out_source_root / "cutscene" / "en_reference" / f"{table}.tsv",
            ["Frame Start", "Frame End", "Text"],
            en_rows,
        )
        write_table_tsv(
            out_source_root / "cutscene" / "ko_work" / f"{table}.tsv",
            ["Frame Start", "Frame End", "KO"],
            ko_rows,
        )
        count_tables += 1
    return count_tables


def write_ingame_tables_from_mix(
    mix_bytes: bytes,
    mix_index: Dict[int, list[tuple[int, int]]],
    out_source_root: Path,
    seed_ko_mode: str,
    missing_files: list[str],
) -> int:
    name = "INGQUO_E.TRE"
    try:
        tre_bytes = get_mix_entry_data(mix_bytes, mix_index, name)
    except KeyError:
        missing_files.append(name)
        return 0

    entries = parse_tre_entries(tre_bytes)
    en_rows: List[dict[str, str]] = []
    ko_rows: List[dict[str, str]] = []
    for quote_id, text in entries:
        bank = quote_id // 10000
        line_id = quote_id % 10000
        filename = f"{bank:02d}-{line_id:04d}.AUD"
        en_rows.append({"Filename": filename, "Actor": "", "EN": text, "KO": ""})
        ko_rows.append(
            {
                "Filename": filename,
                "Actor": "",
                "EN": text,
                "KO": text if seed_ko_mode == "copy-en" else "",
            }
        )

    write_table_tsv(out_source_root / "ingame" / "en_reference" / "INGQUO.tsv", ["Filename", "Actor", "EN", "KO"], en_rows)
    write_table_tsv(out_source_root / "ingame" / "ko_work" / "INGQUO.tsv", ["Filename", "Actor", "EN", "KO"], ko_rows)
    return len(en_rows)


def resolve_startup_mix_path(classic_startup_mix: str, classic_game_dir: str) -> Path:
    if classic_startup_mix:
        path = Path(classic_startup_mix).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Classic STARTUP.MIX not found: {path}")
        return path

    if not classic_game_dir:
        raise ValueError("Either --classic-startup-mix or --classic-game-dir is required for classic extraction")

    game_dir = Path(classic_game_dir).resolve()
    candidates = [
        game_dir / "STARTUP.MIX",
        game_dir / "startup.mix",
        game_dir / "Startup.mix",
    ]
    for c in candidates:
        if c.is_file():
            return c
    raise FileNotFoundError(f"STARTUP.MIX not found under game directory: {game_dir}")


def extract_classic_tables(startup_mix_path: Path, out_source_root: Path, seed_ko_mode: str) -> dict[str, object]:
    clean_dir(out_source_root)

    mix_bytes = startup_mix_path.read_bytes()
    mix_index = parse_mix_entries(mix_bytes)
    missing_files: List[str] = []

    ui_count = write_ui_tables_from_mix(mix_bytes, mix_index, out_source_root, seed_ko_mode, missing_files)
    cut_count = write_cutscene_tables_from_mix(mix_bytes, mix_index, out_source_root, seed_ko_mode, missing_files)
    ing_count = write_ingame_tables_from_mix(mix_bytes, mix_index, out_source_root, seed_ko_mode, missing_files)

    return {
        "startup_mix": str(startup_mix_path),
        "output_source_root": str(out_source_root),
        "seed_ko_mode": seed_ko_mode,
        "ui_tables": ui_count,
        "cutscene_tables": cut_count,
        "ingame_rows": ing_count,
        "missing_files": missing_files,
    }


def extract_enhanced_loc(engine_kpf_path: Path, out_loc_path: Path) -> dict[str, object]:
    if not engine_kpf_path.exists():
        raise FileNotFoundError(f"Enhanced engine KPF not found: {engine_kpf_path}")

    entry_names: List[str] = []
    loc_entry_name = ""
    loc_bytes = b""

    with zipfile.ZipFile(engine_kpf_path, "r") as zf:
        for info in zf.infolist():
            entry_names.append(info.filename)
        for name in entry_names:
            if name.lower() == "loc_en.txt":
                loc_entry_name = name
                break
        if loc_entry_name == "":
            raise FileNotFoundError("loc_en.txt entry not found in BladeRunnerEngine.kpf")
        loc_bytes = zf.read(loc_entry_name)

    text = loc_bytes.decode("utf-8-sig", errors="replace")
    out_loc_path.parent.mkdir(parents=True, exist_ok=True)
    out_loc_path.write_text(text, encoding="utf-8", newline="")

    return {
        "engine_kpf": str(engine_kpf_path),
        "entry_name": loc_entry_name,
        "output_loc_en": str(out_loc_path),
        "loc_size_bytes": len(loc_bytes),
    }


def cmd_extract_local(args: argparse.Namespace) -> int:
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    report_path = Path(args.report_json).resolve() if args.report_json else (output_root / "extract_report.json")

    if args.clean_output:
        for child in output_root.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

    did_work = False
    report: dict[str, object] = {
        "output_root": str(output_root),
        "classic": None,
        "enhanced": None,
    }

    if args.classic_startup_mix or args.classic_game_dir:
        startup_mix_path = resolve_startup_mix_path(args.classic_startup_mix, args.classic_game_dir)
        classic_report = extract_classic_tables(
            startup_mix_path=startup_mix_path,
            out_source_root=output_root / "source",
            seed_ko_mode=args.seed_ko_mode,
        )
        report["classic"] = classic_report
        did_work = True
        print(f"[OK] classic extracted: {classic_report['output_source_root']}")

    if args.enhanced_engine_kpf:
        enhanced_report = extract_enhanced_loc(
            engine_kpf_path=Path(args.enhanced_engine_kpf).resolve(),
            out_loc_path=output_root / "enhanced" / "loc_en.txt",
        )
        report["enhanced"] = enhanced_report
        did_work = True
        print(f"[OK] enhanced loc extracted: {enhanced_report['output_loc_en']}")

    if not did_work:
        raise ValueError("No extraction target specified. Use classic path options and/or --enhanced-engine-kpf")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="")
    print(f"[OK] extract report: {report_path}")
    return 0


def cmd_bootstrap_master(args: argparse.Namespace) -> int:
    source_root = Path(args.source_root).resolve()
    output_path = Path(args.output).resolve()
    report_path = Path(args.report_json).resolve() if args.report_json else None

    required = [
        source_root / "ui" / "ko_work",
        source_root / "ui" / "en_original",
        source_root / "cutscene" / "ko_work",
        source_root / "ingame" / "ko_work",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing required source paths: {missing}")

    rows = build_master_rows(source_root=source_root, include_en=not args.without_en)

    # UID uniqueness check.
    seen: set[str] = set()
    duplicates: List[str] = []
    for row in rows:
        uid = row["uid"]
        if uid in seen:
            duplicates.append(uid)
        seen.add(uid)
    if duplicates:
        raise RuntimeError(f"Duplicate UIDs detected (first 10): {duplicates[:10]}")

    write_tsv(output_path, rows)

    counts: Dict[str, int] = Counter(row["domain"] for row in rows)  # type: ignore[assignment]
    translated = sum(1 for row in rows if row["status"] == "translated")
    todo = sum(1 for row in rows if row["status"] == "todo")

    report = {
        "source_root": str(source_root),
        "output": str(output_path),
        "include_en": not args.without_en,
        "rows_total": len(rows),
        "rows_by_domain": dict(counts),
        "translated": translated,
        "todo": todo,
    }
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="")

    print(f"[OK] master TSV: {output_path}")
    print(
        f"[INFO] rows={len(rows)} ui={counts.get('ui', 0)} cutscene={counts.get('cutscene', 0)} ingame={counts.get('ingame', 0)}"
    )
    print(f"[INFO] translated={translated} todo={todo}")
    if report_path is not None:
        print(f"[OK] report: {report_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified translation pipeline utilities")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_extract = sub.add_parser("extract-local", help="Extract local original resources (classic/enhanced)")
    p_extract.add_argument(
        "--classic-startup-mix",
        default="",
        help="Path to classic STARTUP.MIX (optional)",
    )
    p_extract.add_argument(
        "--classic-game-dir",
        default="",
        help="Classic game directory containing STARTUP.MIX (optional)",
    )
    p_extract.add_argument(
        "--enhanced-engine-kpf",
        default="",
        help="Path to enhanced BladeRunnerEngine.kpf (optional)",
    )
    p_extract.add_argument(
        "--output-root",
        default=r".tmp\translation_pipeline\local_extract",
        help="Output root for extracted resources",
    )
    p_extract.add_argument(
        "--seed-ko-mode",
        choices=["empty", "copy-en"],
        default="empty",
        help="How to initialize ko_work text values for classic extraction",
    )
    p_extract.add_argument(
        "--clean-output",
        action="store_true",
        help="Clean output root before extraction",
    )
    p_extract.add_argument(
        "--report-json",
        default=r".tmp\translation_pipeline\extract_report.json",
        help="Extraction report JSON path (empty uses <output-root>\\extract_report.json)",
    )

    p_boot = sub.add_parser("bootstrap-master", help="Build master TSV from local classic tables")
    p_boot.add_argument(
        "--source-root",
        default=r".ref\TransProcess\source",
        help="Classic source root containing ui/cutscene/ingame folders",
    )
    p_boot.add_argument(
        "--output",
        default=r".tmp\translation_pipeline\master_translation.tsv",
        help="Output master TSV path",
    )
    p_boot.add_argument(
        "--without-en",
        action="store_true",
        help="Do not include EN column values in output TSV",
    )
    p_boot.add_argument(
        "--report-json",
        default=r".tmp\translation_pipeline\master_report.json",
        help="Optional report JSON path (empty to disable)",
    )

    p_split = sub.add_parser("split-master", help="Split master TSV into build input tables")
    p_split.add_argument(
        "--master",
        default=r".tmp\translation_pipeline\master_translation.tsv",
        help="Input master TSV path",
    )
    p_split.add_argument(
        "--output-source-root",
        default=r".tmp\translation_pipeline\source_split",
        help="Output source root (ui/cutscene/ingame)",
    )
    p_split.add_argument(
        "--base-source-root",
        default=r".ref\TransProcess\source",
        help="Base source root for optional reference folder copy",
    )
    p_split.add_argument(
        "--copy-reference",
        action="store_true",
        help="Copy ui/en_original, cutscene/en_reference, ingame/en_reference into output root",
    )
    p_split.add_argument(
        "--translated-only",
        action="store_true",
        help="Export only rows with status=translated",
    )
    p_split.add_argument(
        "--skip-empty-ko",
        action="store_true",
        help="Skip rows where KO is empty",
    )
    p_split.add_argument(
        "--report-json",
        default=r".tmp\translation_pipeline\split_report.json",
        help="Optional split report JSON path (empty to disable)",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.cmd == "extract-local":
        if args.report_json == "":
            args.report_json = None
        return cmd_extract_local(args)

    if args.cmd == "bootstrap-master":
        if args.report_json == "":
            args.report_json = None
        return cmd_bootstrap_master(args)
    if args.cmd == "split-master":
        if args.report_json == "":
            args.report_json = None
        return cmd_split_master(args)

    raise ValueError(f"Unsupported command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
