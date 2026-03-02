#!/usr/bin/env python3
"""
Token-preservation postprocessor for remaster loc files.

It uses loc_en token markers as the source of truth and tries to re-introduce
missing markers in a generated Korean loc file.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


SECTION_RE = re.compile(r"^\[(?P<section>[^\]]*)\]\s*$")
ENTRY_RE = re.compile(r'^(?P<key>[^=\r\n]+?)\s*=\s*"(?P<value>(?:\\.|[^"\\])*)"\s*$')
TOKEN_RE = re.compile(r"(<[^>]+>|\$[^$]+\$|%[^%]+%)")
PUNCT_ONLY_RE = re.compile(r"^[\s\.,;:!?\"'`~\-\(\)\[\]{}…]+$")


@dataclass
class LocRecord:
    kind: str  # section | entry | raw
    section: Optional[str] = None
    key: Optional[str] = None
    value: Optional[str] = None
    raw: Optional[str] = None


@dataclass
class TokenItem:
    raw: str
    token_type: str  # "<>", "$$", "%%"
    inner: str


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
            out.append("\\")
            out.append(nxt)
        i += 2
    return "".join(out)


def escape_loc_value(value: str) -> str:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def parse_loc(path: Path) -> List[LocRecord]:
    text = path.read_text(encoding="utf-8")
    records: List[LocRecord] = []
    current_section: Optional[str] = None

    for raw_line in text.splitlines():
        stripped = raw_line.lstrip("\ufeff").strip()
        sm = SECTION_RE.match(stripped)
        if sm:
            current_section = sm.group("section")
            records.append(LocRecord(kind="section", section=current_section))
            continue

        em = ENTRY_RE.match(stripped)
        if em and current_section is not None:
            records.append(
                LocRecord(
                    kind="entry",
                    section=current_section,
                    key=em.group("key").strip(),
                    value=unescape_loc_value(em.group("value")),
                )
            )
            continue

        records.append(LocRecord(kind="raw", raw=raw_line))
    return records


def serialize_loc(records: Iterable[LocRecord]) -> str:
    out: List[str] = []
    for rec in records:
        if rec.kind == "section":
            out.append(f"[{rec.section}]")
        elif rec.kind == "entry":
            out.append(f'{rec.key} = "{escape_loc_value(rec.value or "")}"')
        else:
            out.append(rec.raw or "")
    return "\r\n".join(out) + "\r\n"


def build_index(records: Iterable[LocRecord]) -> Dict[str, OrderedDict[str, LocRecord]]:
    index: Dict[str, OrderedDict[str, LocRecord]] = OrderedDict()
    for rec in records:
        if rec.kind != "entry":
            continue
        assert rec.section is not None and rec.key is not None
        index.setdefault(rec.section, OrderedDict())[rec.key] = rec
    return index


def parse_tokens(value: str) -> List[TokenItem]:
    items: List[TokenItem] = []
    for raw in TOKEN_RE.findall(value):
        if raw.startswith("<") and raw.endswith(">"):
            items.append(TokenItem(raw=raw, token_type="<>", inner=raw[1:-1]))
        elif raw.startswith("$") and raw.endswith("$"):
            items.append(TokenItem(raw=raw, token_type="$$", inner=raw[1:-1]))
        elif raw.startswith("%") and raw.endswith("%"):
            items.append(TokenItem(raw=raw, token_type="%%", inner=raw[1:-1]))
        else:
            items.append(TokenItem(raw=raw, token_type="??", inner=raw))
    return items


def token_delims(token_type: str) -> Tuple[str, str]:
    if token_type == "<>":
        return "<", ">"
    if token_type == "$$":
        return "$", "$"
    if token_type == "%%":
        return "%", "%"
    return "", ""


def wrap_first_term(text: str, term: str, token_type: str) -> Tuple[str, bool]:
    if not term:
        return text, False
    open_ch, close_ch = token_delims(token_type)
    if not open_ch:
        return text, False

    for m in re.finditer(re.escape(term), text):
        s, e = m.span()
        already_wrapped = (
            s > 0 and e < len(text) and text[s - 1] == open_ch and text[e] == close_ch
        )
        if already_wrapped:
            continue
        return text[:s] + open_ch + text[s:e] + close_ch + text[e:], True
    return text, False


def append_token(text: str, token_type: str, inner: str) -> str:
    open_ch, close_ch = token_delims(token_type)
    token_raw = f"{open_ch}{inner}{close_ch}"
    stripped = text.rstrip()
    if not stripped:
        return token_raw

    last = stripped[-1]
    if last in ".!?":
        return stripped[:-1] + " " + token_raw + last
    return stripped + " " + token_raw


def section_key_iter(
    template_index: Dict[str, OrderedDict[str, LocRecord]],
    target_index: Dict[str, OrderedDict[str, LocRecord]],
    allowed_sections: Optional[set[str]],
) -> Iterable[Tuple[str, str, LocRecord, LocRecord]]:
    for section, sec_map in template_index.items():
        if allowed_sections and section not in allowed_sections:
            continue
        t_sec = target_index.get(section)
        if not t_sec:
            continue
        for key, src_rec in sec_map.items():
            dst_rec = t_sec.get(key)
            if dst_rec is None:
                continue
            yield section, key, src_rec, dst_rec


def normalize_simple(text: str) -> str:
    out = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    out = out.strip(" \t\n\r\"'`.,;:!?()[]{}<>$%")
    return out


def cleanup_suggested_value(token_type: str, candidate: str) -> str:
    value = candidate.strip()
    if not value:
        return value
    if token_type != "$$":
        return value

    # Remove common polite/copula endings from inferred standalone name lines.
    endings = [
        "입니다",
        "이에요",
        "예요",
        "이야",
        "야",
        "요",
        "네",
    ]
    for suffix in endings:
        if value.endswith(suffix) and len(value) > len(suffix) + 1:
            value = value[: -len(suffix)].rstrip()
            break
    return value


def infer_suggested_glossary(
    template_index: Dict[str, OrderedDict[str, LocRecord]],
    target_index: Dict[str, OrderedDict[str, LocRecord]],
    allowed_sections: Optional[set[str]],
) -> Dict[Tuple[str, str], str]:
    suggestions: Dict[Tuple[str, str], str] = {}
    for _section, _key, src_rec, dst_rec in section_key_iter(
        template_index, target_index, allowed_sections
    ):
        src = src_rec.value or ""
        dst = dst_rec.value or ""
        toks = parse_tokens(src)
        if len(toks) != 1:
            continue

        # Infer only for lines that are effectively "token + punctuation".
        rest = TOKEN_RE.sub("", src)
        if rest and not PUNCT_ONLY_RE.match(rest):
            continue

        dst_toks = parse_tokens(dst)
        if dst_toks:
            continue

        candidate = normalize_simple(dst)
        if not candidate:
            continue
        tok = toks[0]
        cleaned = cleanup_suggested_value(tok.token_type, candidate)
        if cleaned:
            suggestions[(tok.token_type, tok.inner)] = cleaned
    return suggestions


def load_or_create_glossary(
    glossary_path: Path,
    token_counter: Counter[Tuple[str, str]],
    suggestions: Dict[Tuple[str, str], str],
) -> Dict[Tuple[str, str], str]:
    existing_manual: Dict[Tuple[str, str], str] = {}
    if glossary_path.exists():
        with glossary_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                t = (row.get("Type") or "").strip()
                inner = (row.get("InnerEN") or "").strip()
                ko = (row.get("KO") or "").strip()
                if t and inner and ko:
                    existing_manual[(t, inner)] = ko

    rows: List[Tuple[str, str, int, str, str]] = []
    for (t, inner), cnt in sorted(token_counter.items(), key=lambda x: (-x[1], x[0][0], x[0][1])):
        manual = existing_manual.get((t, inner), "")
        suggested = suggestions.get((t, inner), "")
        rows.append((t, inner, cnt, manual, suggested))

    glossary_path.parent.mkdir(parents=True, exist_ok=True)
    with glossary_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Type", "InnerEN", "Count", "KO", "SuggestedKO"])
        for row in rows:
            writer.writerow(row)

    resolved: Dict[Tuple[str, str], str] = {}
    for t, inner, _cnt, manual, suggested in rows:
        chosen = manual or suggested
        if chosen:
            resolved[(t, inner)] = chosen
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description="Restore/enforce markup tokens in loc file")
    parser.add_argument(
        "--template",
        default=r".tmp\kpf_unpacked\BladeRunnerEngine\text_like\loc_en.txt",
        help="Reference loc template (token source of truth)",
    )
    parser.add_argument(
        "--input-loc",
        default=r".tmp\remaster_patch\loc_it.txt",
        help="Input loc file to fix",
    )
    parser.add_argument(
        "--output-loc",
        default=r".tmp\remaster_patch\loc_it.tokenfix.txt",
        help="Output fixed loc path",
    )
    parser.add_argument(
        "--glossary",
        default=r".tmp\remaster_patch\token_glossary.csv",
        help="Token glossary CSV path",
    )
    parser.add_argument(
        "--sections",
        default="subtitles",
        help="Comma separated sections to process (default: subtitles)",
    )
    parser.add_argument(
        "--append-unresolved",
        action="store_true",
        help="Append unresolved tokens at end of line as fallback",
    )
    args = parser.parse_args()

    template_path = Path(args.template).resolve()
    input_loc_path = Path(args.input_loc).resolve()
    output_loc_path = Path(args.output_loc).resolve()
    glossary_path = Path(args.glossary).resolve()
    allowed_sections = {s.strip() for s in args.sections.split(",") if s.strip()}
    if not allowed_sections:
        allowed_sections = None  # type: ignore[assignment]

    if not template_path.exists():
        raise FileNotFoundError(f"Template file not found: {template_path}")
    if not input_loc_path.exists():
        raise FileNotFoundError(f"Input loc file not found: {input_loc_path}")

    template_records = parse_loc(template_path)
    input_records = parse_loc(input_loc_path)
    template_index = build_index(template_records)
    input_index = build_index(input_records)

    token_counter: Counter[Tuple[str, str]] = Counter()
    for section, sec_map in template_index.items():
        if allowed_sections and section not in allowed_sections:
            continue
        for rec in sec_map.values():
            for tok in parse_tokens(rec.value or ""):
                token_counter[(tok.token_type, tok.inner)] += 1

    suggestions = infer_suggested_glossary(template_index, input_index, allowed_sections)
    glossary = load_or_create_glossary(glossary_path, token_counter, suggestions)

    stats = {
        "lines_with_tokens": 0,
        "lines_already_ok": 0,
        "lines_changed": 0,
        "tokens_added_wrap": 0,
        "tokens_added_append": 0,
        "tokens_unresolved": 0,
    }
    unresolved_rows: List[List[str]] = []
    fixed_rows: List[List[str]] = []

    for section, key, src_rec, dst_rec in section_key_iter(template_index, input_index, allowed_sections):
        src = src_rec.value or ""
        dst = dst_rec.value or ""
        src_tokens = parse_tokens(src)
        if not src_tokens:
            continue
        stats["lines_with_tokens"] += 1

        required_by_type = Counter(tok.token_type for tok in src_tokens)
        current_by_type = Counter(tok.token_type for tok in parse_tokens(dst))
        if all(current_by_type[t] >= required_by_type[t] for t in required_by_type):
            stats["lines_already_ok"] += 1
            continue

        changed = False
        current = dst
        seen_needed: Counter[str] = Counter()
        current_by_type = Counter(tok.token_type for tok in parse_tokens(current))

        for tok in src_tokens:
            t = tok.token_type
            seen_needed[t] += 1
            if current_by_type[t] >= seen_needed[t]:
                continue

            mapped = glossary.get((t, tok.inner), "")
            candidates = []
            if mapped:
                candidates.append(mapped)
            if tok.inner not in candidates:
                candidates.append(tok.inner)

            method = ""
            for term in candidates:
                current2, ok = wrap_first_term(current, term, t)
                if ok:
                    current = current2
                    current_by_type[t] += 1
                    changed = True
                    method = f"wrap:{term}"
                    stats["tokens_added_wrap"] += 1
                    break

            if not method and args.append_unresolved:
                inner_for_append = mapped or tok.inner
                current = append_token(current, t, inner_for_append)
                current_by_type[t] += 1
                changed = True
                method = f"append:{inner_for_append}"
                stats["tokens_added_append"] += 1

            if not method:
                stats["tokens_unresolved"] += 1
                unresolved_rows.append(
                    [
                        section,
                        key,
                        t,
                        tok.inner,
                        mapped,
                        src,
                        dst,
                    ]
                )
            else:
                fixed_rows.append([section, key, t, tok.inner, mapped, method])

        if changed and current != dst:
            dst_rec.value = current
            stats["lines_changed"] += 1

    output_loc_path.parent.mkdir(parents=True, exist_ok=True)
    output_loc_path.write_text(serialize_loc(input_records), encoding="utf-8", newline="")

    stem = output_loc_path.stem
    unresolved_csv = output_loc_path.parent / f"{stem}.token_unresolved.csv"
    with unresolved_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Section", "Key", "Type", "InnerEN", "MappedKO", "SourceEN", "CurrentKO"])
        writer.writerows(unresolved_rows)

    fixed_csv = output_loc_path.parent / f"{stem}.token_fixed.csv"
    with fixed_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Section", "Key", "Type", "InnerEN", "MappedKO", "Method"])
        writer.writerows(fixed_rows)

    report = {
        "template": str(template_path),
        "input_loc": str(input_loc_path),
        "output_loc": str(output_loc_path),
        "glossary": str(glossary_path),
        "sections": sorted(list(allowed_sections)) if allowed_sections else None,
        "append_unresolved": bool(args.append_unresolved),
        "stats": stats,
        "unresolved_csv": str(unresolved_csv),
        "fixed_csv": str(fixed_csv),
    }
    report_json = output_loc_path.parent / f"{stem}.token_fix_report.json"
    report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="")

    print(f"[OK] output_loc: {output_loc_path}")
    print(f"[OK] glossary : {glossary_path}")
    print(f"[OK] report   : {report_json}")
    print(f"[OK] fixed    : {fixed_csv}")
    print(f"[OK] unresolved: {unresolved_csv}")
    print(
        "[INFO] "
        f"lines_with_tokens={stats['lines_with_tokens']}, "
        f"lines_changed={stats['lines_changed']}, "
        f"tokens_wrap={stats['tokens_added_wrap']}, "
        f"tokens_append={stats['tokens_added_append']}, "
        f"tokens_unresolved={stats['tokens_unresolved']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
