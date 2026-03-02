#!/usr/bin/env python3
"""
Fill token_glossary.csv KO column using:
1) existing SuggestedKO
2) heuristics from loc_en (token source) + generated loc_it/loc_ko (Korean text source).
"""

from __future__ import annotations

import argparse
import csv
import re
import warnings
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


WORD_RE = re.compile(r"[A-Za-z0-9가-힣]+")
PUNCT_STRIP_RE = re.compile(r"[\s\"'`.,;:!?()\[\]{}<>$%]+")
SPACE_RE = re.compile(r"\s+")
SECTION_RE = re.compile(r"^\[(?P<section>[^\]]*)\]\s*$")
ENTRY_RE = re.compile(r'^(?P<key>[^=\r\n]+?)\s*=\s*"(?P<value>(?:\\.|[^"\\])*)"\s*$')


def token_raw(token_type: str, inner: str) -> str:
    if token_type == "<>":
        return f"<{inner}>"
    if token_type == "$$":
        return f"${inner}$"
    if token_type == "%%":
        return f"%{inner}%"
    return inner


def normalize_text(s: str) -> str:
    return SPACE_RE.sub(" ", s.replace("\r\n", "\n").replace("\r", "\n")).strip()


def normalize_candidate(s: str) -> str:
    out = normalize_text(s)
    out = out.strip(" \"'`.,;:!?()[]{}<>$%")
    out = SPACE_RE.sub(" ", out).strip()
    return out


def strip_trailing_josa(text: str) -> str:
    value = normalize_candidate(text)
    if not value:
        return value

    parts = value.split(" ")
    last = parts[-1]
    # Common Korean particles (longest first).
    josa = [
        "으로",
        "에서",
        "에게",
        "한테",
        "께서",
        "까지",
        "부터",
        "처럼",
        "보다",
        "라도",
        "이나",
        "랑",
        "과",
        "와",
        "은",
        "는",
        "이",
        "가",
        "을",
        "를",
        "의",
        "도",
        "만",
        "야",
        "아",
    ]
    for sfx in josa:
        if len(last) > len(sfx) + 1 and last.endswith(sfx):
            last = last[: -len(sfx)]
            break
    parts[-1] = last
    return normalize_candidate(" ".join(parts))


def cleanup_candidate(candidate: str, token_type: str) -> str:
    c = normalize_candidate(candidate)
    if not c:
        return c
    # Token glossary should store base terms, not inflected forms.
    if token_type in {"$$", "<>", "%%"}:
        c = strip_trailing_josa(c)
    return c


def is_punct_only(s: str) -> bool:
    return PUNCT_STRIP_RE.sub("", s) == ""


def words(s: str) -> List[str]:
    return WORD_RE.findall(s)


def first_words(s: str, n: int) -> str:
    ws = words(s)
    if not ws:
        return ""
    return " ".join(ws[:n])


def last_words(s: str, n: int) -> str:
    ws = words(s)
    if not ws:
        return ""
    return " ".join(ws[-n:])


def looks_like_name_candidate(s: str) -> bool:
    if not s:
        return False
    # Avoid capturing very generic Korean function words.
    blacklist = {
        "그",
        "이",
        "저",
        "그녀",
        "그들",
        "우리",
        "당신",
        "아니",
        "아뇨",
        "예",
        "네",
        "응",
        "왜",
        "뭐",
        "무엇",
        "그건",
        "이건",
    }
    return s not in blacklist


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


def parse_loc(path: Path) -> Dict[str, Dict[str, str]]:
    sections: Dict[str, Dict[str, str]] = {}
    current_section = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.lstrip("\ufeff").strip()
        sm = SECTION_RE.match(line)
        if sm:
            current_section = sm.group("section")
            sections.setdefault(current_section, {})
            continue
        em = ENTRY_RE.match(line)
        if em and current_section:
            key = em.group("key").strip()
            value = unescape_loc_value(em.group("value"))
            sections.setdefault(current_section, {})[key] = value
    return sections


def score_candidates_for_row(
    token_type: str,
    inner: str,
    en: str,
    ko: str,
) -> Dict[str, int]:
    raw = token_raw(token_type, inner)
    out: Dict[str, int] = {}
    if raw not in en:
        return out

    ko_norm = normalize_text(ko)
    if not ko_norm:
        return out

    # Heuristic 1: EN line is almost token-only => KO line is direct mapped value.
    en_removed = en.replace(raw, "")
    en_removed = re.sub(r"[\"'`.,;:!?()\[\]\s-]+", "", en_removed)
    if en_removed == "":
        cand = cleanup_candidate(ko_norm, token_type)
        if cand:
            out[cand] = max(out.get(cand, 0), 40)

    # Heuristic 2: token position.
    idx = en.find(raw)
    if idx >= 0:
        before = en[:idx]
        after = en[idx + len(raw) :]
        n_words = max(1, min(3, len(inner.split())))

        if is_punct_only(before):
            cand = cleanup_candidate(first_words(ko_norm, n_words), token_type)
            if cand:
                out[cand] = max(out.get(cand, 0), 8)
        if is_punct_only(after):
            cand = cleanup_candidate(last_words(ko_norm, n_words), token_type)
            if cand:
                out[cand] = max(out.get(cand, 0), 8)

        # If EN has ", $token$,", KO often has comma-separated vocative too.
        if "," in before and "," in after:
            segs = [cleanup_candidate(seg, token_type) for seg in ko_norm.split(",")]
            for seg in segs:
                if seg:
                    out[seg] = max(out.get(seg, 0), 6)

    # Heuristic 3: name-like top words from KO line.
    if token_type == "$$":
        for w in words(ko_norm):
            c = cleanup_candidate(w, token_type)
            if looks_like_name_candidate(c):
                out[c] = max(out.get(c, 0), 1)

    return out


def pick_best(counter: Counter[str]) -> Tuple[str, int, int]:
    if not counter:
        return "", 0, 0
    ranked = counter.most_common(2)
    best, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0
    return best, best_score, second_score


def main() -> int:
    parser = argparse.ArgumentParser(description="Fill token glossary KO values from translated CSV")
    parser.add_argument(
        "--glossary",
        default=r".tmp\remaster_patch\token_glossary.csv",
        help="Input/output glossary CSV",
    )
    parser.add_argument(
        "--template-loc",
        default=r".tmp\kpf_unpacked\BladeRunnerEngine\text_like\loc_en.txt",
        help="Template loc file (token source)",
    )
    parser.add_argument(
        "--target-loc",
        default=r".tmp\remaster_patch\loc_it.txt",
        help="Generated Korean loc file (text source)",
    )
    parser.add_argument(
        "--section",
        default="subtitles",
        help="Section to extract evidence from (default: subtitles)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze only, do not overwrite glossary file",
    )
    parser.add_argument(
        "--refresh-auto",
        action="store_true",
        help="Recompute rows previously auto-filled (AutoSource != manual)",
    )
    parser.add_argument(
        "--aggressive",
        action="store_true",
        help="Use looser acceptance thresholds for auto-filling",
    )
    parser.add_argument(
        "--machine-translate-empty",
        action="store_true",
        help="Fill any still-empty KO cells with machine translation (Google via deep_translator)",
    )
    args = parser.parse_args()

    glossary_path = Path(args.glossary).resolve()
    template_loc_path = Path(args.template_loc).resolve()
    target_loc_path = Path(args.target_loc).resolve()
    section_name = args.section.strip() or "subtitles"

    if not glossary_path.exists():
        raise FileNotFoundError(f"Glossary not found: {glossary_path}")
    if not template_loc_path.exists():
        raise FileNotFoundError(f"Template loc not found: {template_loc_path}")
    if not target_loc_path.exists():
        raise FileNotFoundError(f"Target loc not found: {target_loc_path}")

    with glossary_path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else ["Type", "InnerEN", "Count", "KO", "SuggestedKO"]

    add_fields = ["AutoSource", "AutoConfidence", "AutoEvidence"]
    for fld in add_fields:
        if fld not in fieldnames:
            fieldnames.append(fld)

    template_sections = parse_loc(template_loc_path)
    target_sections = parse_loc(target_loc_path)
    template_map = template_sections.get(section_name, {})
    target_map = target_sections.get(section_name, {})
    evidence_rows: List[Tuple[str, str]] = []
    for key, en in template_map.items():
        ko = target_map.get(key, "")
        en_norm = normalize_text(en)
        ko_norm = normalize_text(ko)
        if en_norm and ko_norm:
            evidence_rows.append((en_norm, ko_norm))

    filled_from_suggested = 0
    filled_from_loc_context = 0
    filled_from_derived = 0
    filled_from_mt = 0

    for row in rows:
        t = (row.get("Type") or "").strip()
        inner = (row.get("InnerEN") or "").strip()
        auto_source_prev = (row.get("AutoSource") or "").strip()
        ko_manual = normalize_candidate(row.get("KO") or "")
        suggested = normalize_candidate(row.get("SuggestedKO") or "")

        if args.refresh_auto and auto_source_prev and auto_source_prev != "manual":
            ko_manual = ""
            row["KO"] = ""
            row["AutoSource"] = ""
            row["AutoConfidence"] = ""
            row["AutoEvidence"] = ""

        if ko_manual:
            row["KO"] = ko_manual
            row["AutoSource"] = row.get("AutoSource") or "manual"
            row["AutoConfidence"] = row.get("AutoConfidence") or "manual"
            continue

        # 1) SuggestedKO first (already inferred from reliable token-only rows).
        if suggested:
            row["KO"] = suggested
            row["AutoSource"] = "suggested"
            row["AutoConfidence"] = "high"
            row["AutoEvidence"] = "suggested_ko"
            filled_from_suggested += 1
            continue

        # 2) loc_en + generated loc_ko context heuristics.
        counter: Counter[str] = Counter()
        evidence: Dict[str, List[str]] = defaultdict(list)
        for en, ko in evidence_rows:
            scored = score_candidates_for_row(t, inner, en, ko)
            for cand, score in scored.items():
                if not cand:
                    continue
                counter[cand] += score
                if len(evidence[cand]) < 3:
                    evidence[cand].append(ko)

        best, best_score, second_score = pick_best(counter)
        if not best:
            continue

        # Conservative acceptance:
        # - high if strongly dominant
        # - medium for a clear winner on repeated evidence
        confidence = ""
        if best_score >= 40:
            confidence = "high"
        elif best_score >= 16 and best_score >= second_score + 6:
            confidence = "high"
        elif best_score >= 10 and best_score >= second_score + 4:
            confidence = "medium"
        elif args.aggressive and best_score >= 8 and best_score >= second_score + 2:
            confidence = "medium"
        elif args.aggressive and best_score >= 6 and second_score == 0:
            confidence = "low"

        if not confidence:
            continue

        row["KO"] = best
        row["AutoSource"] = f"loc_context:{section_name}"
        row["AutoConfidence"] = confidence
        row["AutoEvidence"] = " | ".join(evidence.get(best, []))
        filled_from_loc_context += 1

    # 3) Derived pass: inflective EN variants -> reuse already resolved KO.
    resolved: Dict[Tuple[str, str], str] = {}
    for row in rows:
        t = (row.get("Type") or "").strip()
        inner = (row.get("InnerEN") or "").strip()
        ko = normalize_candidate(row.get("KO") or "")
        if t and inner and ko:
            resolved[(t, inner.lower())] = ko

    for row in rows:
        ko_now = normalize_candidate(row.get("KO") or "")
        if ko_now:
            continue
        t = (row.get("Type") or "").strip()
        inner = (row.get("InnerEN") or "").strip()
        if not t or not inner:
            continue
        lower = inner.lower()
        candidates = [lower]

        # Possessive/quote forms.
        for suffix in ["'s", "’s", "'"]:
            if lower.endswith(suffix):
                candidates.append(lower[: -len(suffix)])
            else:
                candidates.append(lower + suffix)

        # Simple plural forms.
        if lower.endswith("es") and len(lower) > 3:
            candidates.append(lower[:-2])
        else:
            candidates.append(lower + "es")
        if lower.endswith("s") and len(lower) > 2:
            candidates.append(lower[:-1])
        else:
            candidates.append(lower + "s")

        # Honorific/title removal.
        title_prefixes = [
            "dr. ",
            "mr. ",
            "mrs. ",
            "miss ",
            "lieutenant ",
            "chief ",
            "governor ",
            "officer ",
            "the ",
        ]
        for pref in title_prefixes:
            if lower.startswith(pref):
                candidates.append(lower[len(pref) :])

        # Punctuation-light variants for initials.
        candidates.append(lower.replace(".", ""))
        candidates.append(lower.replace(".", "").replace("  ", " ").strip())

        # Optional article removal.
        if lower.startswith("the "):
            candidates.append(lower[4:])

        picked = ""
        for c in candidates:
            v = resolved.get((t, c), "")
            if v:
                picked = v
                break
        if not picked:
            continue

        row["KO"] = picked
        row["AutoSource"] = "derived_variant"
        row["AutoConfidence"] = "medium"
        row["AutoEvidence"] = "derived_from_existing_token"
        filled_from_derived += 1

    # 4) Optional machine translation fallback for remaining empty rows.
    if args.machine_translate_empty:
        try:
            from deep_translator import GoogleTranslator  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "deep_translator is required for --machine-translate-empty"
            ) from exc

        # Silence third-party dependency warning noise from requests stack.
        warnings.filterwarnings("ignore")
        translator = GoogleTranslator(source="en", target="ko")

        pending_indexes: List[int] = []
        pending_texts: List[str] = []
        for i, row in enumerate(rows):
            if normalize_candidate(row.get("KO") or ""):
                continue
            inner = normalize_candidate(row.get("InnerEN") or "")
            if not inner:
                continue
            pending_indexes.append(i)
            pending_texts.append(inner)

        translated: List[str] = []
        if pending_texts:
            try:
                # translate_batch can fail on some terms; fallback per-item below.
                translated = translator.translate_batch(pending_texts)  # type: ignore[assignment]
            except Exception:
                translated = []

        if len(translated) != len(pending_texts):
            translated = []
            for text in pending_texts:
                try:
                    translated.append(translator.translate(text))
                except Exception:
                    translated.append(text)

        for idx, tr in zip(pending_indexes, translated):
            row = rows[idx]
            value = normalize_candidate(tr or row.get("InnerEN") or "")
            if not value:
                continue
            row["KO"] = value
            row["AutoSource"] = "mt_google"
            row["AutoConfidence"] = "low"
            row["AutoEvidence"] = "machine_translation_fallback"
            filled_from_mt += 1

    if not args.dry_run:
        with glossary_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)

    total = len(rows)
    total_filled = sum(1 for r in rows if normalize_candidate(r.get("KO") or ""))
    total_unfilled = total - total_filled
    print(f"[INFO] glossary: {glossary_path}")
    print(f"[INFO] template_loc: {template_loc_path}")
    print(f"[INFO] target_loc: {target_loc_path}")
    print(f"[INFO] evidence_section: {section_name}, rows={len(evidence_rows)}")
    print(f"[INFO] rows: {total}")
    print(f"[INFO] KO filled total: {total_filled}")
    print(f"[INFO] filled from SuggestedKO: {filled_from_suggested}")
    print(f"[INFO] filled from loc context: {filled_from_loc_context}")
    print(f"[INFO] filled from derived variants: {filled_from_derived}")
    print(f"[INFO] filled from machine translation: {filled_from_mt}")
    print(f"[INFO] remaining unfilled: {total_unfilled}")
    if args.dry_run:
        print("[INFO] dry-run mode: file not modified")
    else:
        print("[OK] glossary updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
