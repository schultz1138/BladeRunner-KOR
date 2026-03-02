#!/usr/bin/env python3
"""
Build a Korean localization candidate for Blade Runner Enhanced.

This script reuses existing classic translation table resources under .ref/TransProcess
and injects them into a loc template (typically loc_en.txt extracted from BladeRunnerEngine.kpf).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


SECTION_RE = re.compile(r"^\[(?P<section>[^\]]*)\]\s*$")
ENTRY_RE = re.compile(r'^(?P<key>[^=\r\n]+?)\s*=\s*"(?P<value>(?:\\.|[^"\\])*)"\s*$')
AUD_RE = re.compile(r"^(?P<bank>\d+)-(?P<id>\d+)\.AUD$", re.IGNORECASE)
TOKEN_RE = re.compile(r"(<[^>]+>|\$[^$]+\$|%[^%]+%)")


DIRECT_SECTION_CSV = OrderedDict(
    {
        "actors": "ACTORS",
        "clues": "CLUES",
        "cluetypes": "CLUETYPE",
        "crimes": "CRIMES",
        "dlgmenu": "DLGMENU",
        "scorers": "SCORERS",
        "spindest": "SPINDEST",
        "vk": "VK",
    }
)

# KIA.csv ID order (0..51) -> loc ui key mapping.
KIA_UI_KEYS = [
    "ui_clues_label",
    "ui_crime_label",
    "ui_source_label",
    "ui_unknown",
    "ui_type_label",
    "ui_none",
    "ui_filter_phototgraphs",
    "ui_filter_video_clips",
    "ui_filter_audio_recordings",
    "ui_filter_objects",
    "ui_intangible",
    "ui_clue_types_label",
    "ui_crime_scenes_label",
    "ui_info_sources_label",
    "ui_filter_whereabouts",
    "ui_filter_mo",
    "ui_filter_relicant",
    "ui_filter_non_replicant",
    "ui_male",
    "ui_female",
    "ui_suspect_male",
    "ui_suspect_female",
    "ui_no_suspects",
    "ui_game_options",
    "ui_crime_scene_database",
    "ui_suspect_database",
    "ui_clue_database",
    "ui_log_back",
    "ui_log_forward",
    "ui_resume_game",
    "ui_filters_all",
    "ui_filters_none",
    "ui_prev_suspect",
    "ui_next_suspect",
    "ui_prev_crime_scene",
    "ui_next_crime_scene",
    "ui_jump_to_suspect",
    "ui_kia",
    "ui_game_settings",
    "ui_save_game",
    "ui_load_game",
    "ui_help",
    "ui_quit_game",
    "ui_kia_diag_mode",
    "ui_chinyen",
    "ui_no_crimes",
    "ui_associated_crime_scenes",
    "ui_clue_filters",
    "ui_filter_other",
    "ui_no_photo",
    "ui_unlimited_supply",
    "ui_retired",
]

# Partial reuse from classic OPTIONS.csv
OPTIONS_UI_KEY_MAP = {
    1: "ui_difficulty",
    2: "ui_music_volume",
    3: "ui_sound_effects_volume",
    4: "ui_ambient_sound_volume",
    5: "ui_speech_volume",
    8: "ui_easy",
    28: "ui_medium",
    29: "ui_hard",
    30: "ui_polite",
    31: "ui_normal",
    32: "ui_surly",
    33: "ui_erratic",
    34: "ui_user_choice",
    35: "ui_really_overwrite",
    37: "ui_new_game",
    38: "ui_confirm_no",
    39: "ui_confirm_yes",
}


@dataclass
class LocRecord:
    kind: str  # section | entry | raw
    section: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None
    raw: Optional[str] = None
    lineno: int = 0


def unescape_loc_value(raw: str) -> str:
    out: List[str] = []
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch != "\\" or i + 1 >= len(raw):
            out.append(ch)
            i += 1
            continue

        nxt = raw[i + 1]
        if nxt == "n":
            out.append("\n")
        elif nxt == "r":
            out.append("\r")
        elif nxt == "t":
            out.append("\t")
        elif nxt == '"':
            out.append('"')
        elif nxt == "\\":
            out.append("\\")
        else:
            # Keep unknown escape as-is.
            out.append("\\")
            out.append(nxt)
        i += 2
    return "".join(out)


def escape_loc_value(value: str) -> str:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    escaped = normalized.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return escaped


def parse_loc(path: Path) -> List[LocRecord]:
    records: List[LocRecord] = []
    current_section: Optional[str] = None
    text = path.read_text(encoding="utf-8")
    for lineno, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.lstrip("\ufeff")
        stripped = line.strip()

        sm = SECTION_RE.match(stripped)
        if sm:
            current_section = sm.group("section")
            records.append(LocRecord(kind="section", section=current_section, lineno=lineno))
            continue

        em = ENTRY_RE.match(stripped)
        if em and current_section is not None:
            key = em.group("key").strip()
            value = unescape_loc_value(em.group("value"))
            records.append(
                LocRecord(
                    kind="entry",
                    section=current_section,
                    key=key,
                    value=value,
                    lineno=lineno,
                )
            )
            continue

        records.append(LocRecord(kind="raw", raw=raw_line, lineno=lineno))
    return records


def build_index(records: Iterable[LocRecord]) -> Dict[str, OrderedDict[str, LocRecord]]:
    index: Dict[str, OrderedDict[str, LocRecord]] = OrderedDict()
    for rec in records:
        if rec.kind != "entry":
            continue
        assert rec.section is not None
        assert rec.key is not None
        section_map = index.setdefault(rec.section, OrderedDict())
        section_map[rec.key] = rec
    return index


def serialize_loc(records: Iterable[LocRecord]) -> str:
    out: List[str] = []
    for rec in records:
        if rec.kind == "entry":
            assert rec.key is not None and rec.value is not None
            out.append(f'{rec.key} = "{escape_loc_value(rec.value)}"')
        elif rec.kind == "section":
            assert rec.section is not None
            out.append(f"[{rec.section}]")
        else:
            out.append(rec.raw or "")
    return "\r\n".join(out) + "\r\n"


def normalize_text(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def detect_delimiter(path: Path) -> str:
    default = "\t" if path.suffix.lower() == ".tsv" else ","
    sample = path.read_text(encoding="utf-8-sig", errors="replace")[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",\t")
        return dialect.delimiter
    except csv.Error:
        return default


def read_id_text_table(path: Path) -> Dict[int, str]:
    rows: Dict[int, str] = {}
    delimiter = detect_delimiter(path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        if reader.fieldnames is None:
            return rows
        id_col = "ID" if "ID" in reader.fieldnames else reader.fieldnames[0]
        text_col = "Text" if "Text" in reader.fieldnames else reader.fieldnames[-1]
        for row in reader:
            raw_id = (row.get(id_col) or "").strip()
            if raw_id == "":
                continue
            try:
                idx = int(raw_id)
            except ValueError:
                continue
            rows[idx] = normalize_text((row.get(text_col) or ""))
    return rows


def read_ingame_table(path: Path) -> Dict[str, str]:
    result: Dict[str, str] = {}
    delimiter = detect_delimiter(path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            filename = (row.get("Filename") or "").strip()
            ko = normalize_text(row.get("KO") or "")
            if not filename:
                continue
            m = AUD_RE.match(filename)
            if not m:
                continue
            key = str(int(m.group("bank")) * 10000 + int(m.group("id")))
            result[key] = ko
    return result


def read_cutscene_ko(path: Path) -> List[str]:
    lines: List[str] = []
    delimiter = detect_delimiter(path)
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            lines.append(normalize_text(row.get("KO") or ""))
    return lines


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


def extract_tokens(value: str) -> List[str]:
    return TOKEN_RE.findall(value)


def token_type(token: str) -> str:
    if token.startswith("<") and token.endswith(">"):
        return "<>"
    if token.startswith("$") and token.endswith("$"):
        return "$$"
    if token.startswith("%") and token.endswith("%"):
        return "%%"
    return "??"


def missing_tokens_by_type(source: str, translated: str) -> List[str]:
    source_tokens = extract_tokens(source)
    if not source_tokens:
        return []

    src_count: Dict[str, int] = defaultdict(int)
    dst_count: Dict[str, int] = defaultdict(int)
    for tok in source_tokens:
        src_count[token_type(tok)] += 1
    for tok in extract_tokens(translated):
        dst_count[token_type(tok)] += 1

    missing: List[str] = []
    for t, need in src_count.items():
        lack = need - dst_count.get(t, 0)
        if lack <= 0:
            continue
        samples = [tok for tok in source_tokens if token_type(tok) == t][:lack]
        missing.extend(samples)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Korean loc file from TransProcess table data (TSV/CSV)")
    parser.add_argument(
        "--template",
        default=r".tmp\kpf_unpacked\BladeRunnerEngine\text_like\loc_en.txt",
        help="Input loc template path (default: extracted loc_en.txt)",
    )
    parser.add_argument(
        "--transprocess-source",
        default=r".ref\TransProcess\source",
        help="TransProcess source root (contains ui/cutscene/ingame)",
    )
    parser.add_argument(
        "--output-dir",
        default=r".tmp\remaster_patch",
        help="Output directory for generated loc files and reports",
    )
    parser.add_argument(
        "--output-name",
        default="loc_ko.txt",
        help="Generated Korean loc filename",
    )
    parser.add_argument(
        "--slot-alias",
        default="it",
        help="Also emit a copy as loc_<alias>.txt for in-game slot replacement (empty to disable)",
    )
    args = parser.parse_args()

    template = Path(args.template).resolve()
    source_root = Path(args.transprocess_source).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    ui_ko_root = source_root / "ui" / "ko_work"
    ingame_ko_root = source_root / "ingame" / "ko_work"
    cutscene_ko_root = source_root / "cutscene" / "ko_work"
    ingame_ko_table = find_table_by_stem(ingame_ko_root, "INGQUO")
    cutscene_tables = collect_table_files(cutscene_ko_root)

    required = [template, ui_ko_root, ingame_ko_root, cutscene_ko_root]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Required path not found: {missing}")
    if ingame_ko_table is None:
        raise FileNotFoundError(
            f"Required INGQUO table not found under {ingame_ko_root} (expected INGQUO.tsv or INGQUO.csv)"
        )

    records = parse_loc(template)
    loc_index = build_index(records)

    original_values: Dict[Tuple[str, str], str] = {}
    for section, section_map in loc_index.items():
        for key, rec in section_map.items():
            original_values[(section, key)] = rec.value or ""

    stats: Dict[str, Dict[str, object]] = defaultdict(
        lambda: {"replaced": 0, "missing_keys": [], "extra_rows": []}
    )
    missing_markup: List[Tuple[str, str, str, str, List[str]]] = []

    def apply_with_audit(section: str, key: str, translated: str) -> bool:
        section_map = loc_index.get(section)
        if section_map is None:
            stats[section]["missing_keys"].append(key)
            return False
        rec = section_map.get(key)
        if rec is None:
            stats[section]["missing_keys"].append(key)
            return False

        source = rec.value or ""
        miss = missing_tokens_by_type(source, translated)
        if miss:
            missing_markup.append((section, key, source, translated, miss))

        rec.value = translated
        stats[section]["replaced"] += 1
        return True

    # 1) Direct numeric sections from UI tables.
    missing_ui_tables: List[str] = []
    for section, stem in DIRECT_SECTION_CSV.items():
        table_path = find_table_by_stem(ui_ko_root, stem)
        if table_path is None:
            missing_ui_tables.append(stem)
            continue
        rows = read_id_text_table(table_path)
        for idx, text in rows.items():
            key = str(idx)
            if not apply_with_audit(section, key, text):
                stats[section]["extra_rows"].append(key)

    # 2) KIA -> ui key set.
    kia_table = find_table_by_stem(ui_ko_root, "KIA")
    if kia_table is None:
        raise FileNotFoundError(f"KIA table not found in {ui_ko_root} (expected KIA.tsv or KIA.csv)")
    kia_rows = read_id_text_table(kia_table)
    for idx, key in enumerate(KIA_UI_KEYS):
        if idx not in kia_rows:
            stats["ui"]["missing_keys"].append(key)
            continue
        apply_with_audit("ui", key, kia_rows[idx])

    # 3) Partial OPTIONS -> ui mapping.
    options_table = find_table_by_stem(ui_ko_root, "OPTIONS")
    if options_table is None:
        raise FileNotFoundError(
            f"OPTIONS table not found in {ui_ko_root} (expected OPTIONS.tsv or OPTIONS.csv)"
        )
    options_rows = read_id_text_table(options_table)
    for idx, key in OPTIONS_UI_KEY_MAP.items():
        text = options_rows.get(idx)
        if text is None:
            stats["ui"]["missing_keys"].append(key)
            continue
        apply_with_audit("ui", key, text)

    # 4) In-game subtitles.
    ingame_rows = read_ingame_table(ingame_ko_table)
    for key, text in ingame_rows.items():
        apply_with_audit("subtitles", key, text)

    # 5) Cutscene sections (order-based mapping).
    missing_cutscene_sections: List[str] = []
    count_mismatch_sections: List[Tuple[str, int, int]] = []
    for table_path in cutscene_tables:
        section = f"{table_path.stem}_E"
        section_map = loc_index.get(section)
        if section_map is None:
            missing_cutscene_sections.append(section)
            continue

        ko_lines = read_cutscene_ko(table_path)
        keys = list(section_map.keys())
        if len(ko_lines) != len(keys):
            count_mismatch_sections.append((section, len(ko_lines), len(keys)))

        limit = min(len(ko_lines), len(keys))
        for i in range(limit):
            apply_with_audit(section, keys[i], ko_lines[i])

    # 6) Write outputs.
    output_main = output_dir / args.output_name
    output_main.write_text(serialize_loc(records), encoding="utf-8", newline="")

    alias_path: Optional[Path] = None
    slot_alias = (args.slot_alias or "").strip()
    if slot_alias:
        alias_path = output_dir / f"loc_{slot_alias}.txt"
        alias_path.write_text(serialize_loc(records), encoding="utf-8", newline="")

    # 7) Build coverage/report.
    section_coverage: Dict[str, Dict[str, int]] = {}
    for section, section_map in loc_index.items():
        total = len(section_map)
        changed = 0
        for key, rec in section_map.items():
            old = original_values.get((section, key), "")
            if (rec.value or "") != old:
                changed += 1
        replaced = int(stats.get(section, {}).get("replaced", 0))
        section_coverage[section] = {"changed": changed, "replaced": replaced, "total": total}

    # 8) Extra TODO artifacts for manual pass.
    markup_todo_csv = output_dir / "markup_todo.csv"
    with markup_todo_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Section", "Key", "MissingTokens", "SourceEN", "CurrentKO"])
        for section, key, src, dst, miss in missing_markup:
            writer.writerow([section, key, "|".join(miss), src, dst])

    ui_todo_csv = output_dir / "ui_todo.csv"
    ui_pending_count = 0
    with ui_todo_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Key", "CurrentText", "Reason"])
        for key, rec in (loc_index.get("ui") or {}).items():
            before = original_values.get(("ui", key), "")
            after = rec.value or ""
            if after == before:
                ui_pending_count += 1
                writer.writerow([key, after, "Unchanged from template"])

    report = {
        "template": str(template),
        "source_root": str(source_root),
        "output_main": str(output_main),
        "output_alias": str(alias_path) if alias_path else None,
        "section_coverage": section_coverage,
        "apply_stats": stats,
        "markup_todo_csv": str(markup_todo_csv),
        "ui_todo_csv": str(ui_todo_csv),
        "missing_markup_count": len(missing_markup),
        "missing_markup_examples": [
            {
                "section": section,
                "key": key,
                "missing_tokens": miss,
                "source": src,
                "translated": dst,
            }
            for section, key, src, dst, miss in missing_markup[:40]
        ],
        "missing_cutscene_sections": missing_cutscene_sections,
        "missing_ui_tables": missing_ui_tables,
        "input_tables": {
            "ingame": str(ingame_ko_table),
            "cutscene_count": len(cutscene_tables),
            "kia": str(kia_table),
            "options": str(options_table),
        },
        "cutscene_count_mismatch": [
            {"section": sec, "ko_rows": ko_rows, "loc_rows": loc_rows}
            for sec, ko_rows, loc_rows in count_mismatch_sections
        ],
    }

    report_json = output_dir / "build_report.json"
    report_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="",
    )

    lines: List[str] = []
    lines.append("# Korean LOC Build Report")
    lines.append("")
    lines.append(f"- Template: `{template}`")
    lines.append(f"- Source root: `{source_root}`")
    lines.append(f"- Output: `{output_main}`")
    if alias_path:
        lines.append(f"- Slot alias output: `{alias_path}`")
    lines.append(f"- Markup TODO CSV: `{markup_todo_csv}`")
    lines.append(f"- UI TODO CSV: `{ui_todo_csv}`")
    lines.append("")
    lines.append("## Section Coverage (changed/replaced/total)")
    lines.append("")
    for section, cov in section_coverage.items():
        lines.append(f"- {section}: {cov['changed']}/{cov['replaced']}/{cov['total']}")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(f"- Missing cutscene sections: {len(missing_cutscene_sections)}")
    if missing_cutscene_sections:
        lines.append(f"  - {', '.join(missing_cutscene_sections)}")
    lines.append(f"- Missing UI tables: {len(missing_ui_tables)}")
    if missing_ui_tables:
        lines.append(f"  - {', '.join(missing_ui_tables)}")
    lines.append(f"- Cutscene row-count mismatches: {len(count_mismatch_sections)}")
    if count_mismatch_sections:
        for sec, ko_rows, loc_rows in count_mismatch_sections:
            lines.append(f"  - {sec}: table={ko_rows}, loc={loc_rows}")
    lines.append(f"- Lines with missing markup tokens: {len(missing_markup)}")
    lines.append(f"- UI keys still unchanged from template: {ui_pending_count}")
    lines.append("")
    lines.append("## Missing Markup Examples (first 20)")
    lines.append("")
    for section, key, _src, _dst, miss in missing_markup[:20]:
        lines.append(f"- {section}:{key} -> {', '.join(miss)}")
    lines.append("")
    lines.append(f"`build_report.json` contains full detail.")
    lines.append("")

    report_md = output_dir / "build_report.md"
    report_md.write_text("\n".join(lines), encoding="utf-8", newline="")

    print(f"[OK] Wrote: {output_main}")
    if alias_path:
        print(f"[OK] Wrote: {alias_path}")
    print(f"[OK] Wrote: {report_json}")
    print(f"[OK] Wrote: {report_md}")
    print(f"[INFO] Missing markup lines: {len(missing_markup)}")
    print(f"[INFO] Missing cutscene sections: {len(missing_cutscene_sections)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
