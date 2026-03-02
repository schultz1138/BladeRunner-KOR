#!/usr/bin/env python3
"""
Unified translation pipeline for Blade Runner classic and enhanced workflows.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CLASSIC_PIPELINE = ROOT / ".ref" / "TransProcess" / "tools" / "pipeline.py"
MASTER_PIPELINE = ROOT / "tools" / "translation_pipeline.py"
DEFAULT_ENHANCED_TEMPLATE = r".tmp\kpf_unpacked\BladeRunnerEngine\text_like\loc_en.txt"

REMASTER_BUILD = ROOT / "tools" / "remaster" / "build_loc_ko.py"
REMASTER_TOKEN_FIX = ROOT / "tools" / "remaster" / "fix_markup_tokens.py"
REMASTER_PATCH_LOC = ROOT / "tools" / "remaster" / "patch_kpf_loc.py"
REMASTER_PATCH_FONTS = ROOT / "tools" / "remaster" / "patch_kpf_fonts_ko.py"


def run(cmd: list[str]) -> None:
    print("[RUN]", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True, cwd=ROOT)


def run_classic(
    profile_mode: str,
    source_root: Path | None = None,
    work_root: Path | None = None,
) -> None:
    common_args: list[str] = []
    if source_root is not None:
        common_args.extend(["--source-root", str(source_root.resolve())])
    if work_root is not None:
        common_args.extend(["--work-root", str(work_root.resolve())])

    if profile_mode == "validate":
        run([sys.executable, str(CLASSIC_PIPELINE), "validate", *common_args])
        return
    if profile_mode == "windows_full":
        run([sys.executable, str(CLASSIC_PIPELINE), "build", "--profile", "windows_full", *common_args])
        return
    if profile_mode == "subs_only":
        run([sys.executable, str(CLASSIC_PIPELINE), "build", "--profile", "subs_only", *common_args])
        return
    if profile_mode == "both":
        run([sys.executable, str(CLASSIC_PIPELINE), "build-all", *common_args])
        return
    raise ValueError(f"Unknown classic profile_mode: {profile_mode}")


def build_enhanced(args: argparse.Namespace, source_override: Path | None = None) -> None:
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    transprocess_source = source_override.resolve() if source_override else Path(args.transprocess_source).resolve()
    template_path = Path(args.template).resolve()

    cmd_build = [
        sys.executable,
        str(REMASTER_BUILD),
        "--template",
        str(template_path),
        "--transprocess-source",
        str(transprocess_source),
        "--output-dir",
        str(output_dir),
        "--output-name",
        args.output_name,
        "--slot-alias",
        args.slot_alias,
    ]
    run(cmd_build)

    source_loc = output_dir / args.output_name
    if args.slot_alias:
        source_loc = output_dir / f"loc_{args.slot_alias}.txt"

    patch_loc_source = source_loc
    if not args.skip_token_fix:
        token_fixed = output_dir / f"{source_loc.stem}.tokenfix.txt"
        cmd_token_fix = [
            sys.executable,
            str(REMASTER_TOKEN_FIX),
            "--template",
            str(template_path),
            "--input-loc",
            str(source_loc),
            "--output-loc",
            str(token_fixed),
            "--sections",
            args.fix_sections,
            "--glossary",
            str((output_dir / "token_glossary.csv").resolve()),
        ]
        if args.append_unresolved:
            cmd_token_fix.append("--append-unresolved")
        run(cmd_token_fix)
        patch_loc_source = token_fixed

    if not args.skip_patch_loc:
        entry_name = args.output_name
        if args.slot_alias:
            entry_name = f"loc_{args.slot_alias}.txt"
        output_kpf = output_dir / f"BladeRunnerEngine_poc_{Path(entry_name).stem}.kpf"
        run(
            [
                sys.executable,
                str(REMASTER_PATCH_LOC),
                "--input-kpf",
                str(Path(args.engine_kpf).resolve()),
                "--output-kpf",
                str(output_kpf),
                "--loc-file",
                str(patch_loc_source),
                "--entry-name",
                entry_name,
            ]
        )

    if not args.skip_patch_fonts:
        run(
            [
                sys.executable,
                str(REMASTER_PATCH_FONTS),
                "--input-kpf",
                str(Path(args.fonts_kpf).resolve()),
                "--output-kpf",
                str((output_dir / "fonts_poc_ko.kpf").resolve()),
                "--font-file",
                str(Path(args.font_file).resolve()),
            ]
        )


def run_master_bootstrap_and_split(args: argparse.Namespace) -> Path:
    master_path = Path(args.master).resolve()
    split_source_root = Path(args.split_source_root).resolve()

    if args.bootstrap_master or not master_path.exists():
        cmd_bootstrap = [
            sys.executable,
            str(MASTER_PIPELINE),
            "bootstrap-master",
            "--source-root",
            str(Path(args.master_source_root).resolve()),
            "--output",
            str(master_path),
        ]
        if args.master_report_json:
            cmd_bootstrap.extend(["--report-json", str(Path(args.master_report_json).resolve())])
        else:
            cmd_bootstrap.extend(["--report-json", ""])
        if args.without_en_master:
            cmd_bootstrap.append("--without-en")
        run(cmd_bootstrap)

    if not master_path.exists():
        raise FileNotFoundError(f"master TSV not found: {master_path}")

    cmd_split = [
        sys.executable,
        str(MASTER_PIPELINE),
        "split-master",
        "--master",
        str(master_path),
        "--output-source-root",
        str(split_source_root),
        "--base-source-root",
        str(Path(args.base_source_root).resolve()),
    ]
    if args.split_report_json:
        cmd_split.extend(["--report-json", str(Path(args.split_report_json).resolve())])
    else:
        cmd_split.extend(["--report-json", ""])
    if args.copy_reference:
        cmd_split.append("--copy-reference")
    if args.translated_only:
        cmd_split.append("--translated-only")
    if args.skip_empty_ko:
        cmd_split.append("--skip-empty-ko")
    run(cmd_split)
    return split_source_root


def run_extract_local(args: argparse.Namespace) -> Path:
    extract_output_root = Path(args.extract_output_root).resolve()
    cmd = [
        sys.executable,
        str(MASTER_PIPELINE),
        "extract-local",
        "--output-root",
        str(extract_output_root),
        "--seed-ko-mode",
        args.seed_ko_mode,
    ]
    if args.classic_startup_mix:
        cmd.extend(["--classic-startup-mix", str(Path(args.classic_startup_mix).resolve())])
    if args.classic_game_dir:
        cmd.extend(["--classic-game-dir", str(Path(args.classic_game_dir).resolve())])
    if args.enhanced_engine_kpf:
        cmd.extend(["--enhanced-engine-kpf", str(Path(args.enhanced_engine_kpf).resolve())])
    if args.extract_report_json:
        cmd.extend(["--report-json", str(Path(args.extract_report_json).resolve())])
    else:
        cmd.extend(["--report-json", ""])
    if args.clean_extract_output:
        cmd.append("--clean-output")
    run(cmd)
    return extract_output_root


def build_from_master(args: argparse.Namespace) -> None:
    split_source_root = run_master_bootstrap_and_split(args)

    if args.target in ("both", "classic"):
        run_classic(
            profile_mode=args.classic_profile,
            source_root=split_source_root,
            work_root=Path(args.classic_work_root).resolve(),
        )

    if args.target in ("both", "enhanced"):
        build_enhanced(args, source_override=split_source_root)


def build_from_local(args: argparse.Namespace) -> None:
    if not args.classic_startup_mix and not args.classic_game_dir:
        raise ValueError("build-from-local requires --classic-startup-mix or --classic-game-dir")

    extract_root = run_extract_local(args)
    extracted_source_root = extract_root / "source"
    if not extracted_source_root.exists():
        raise FileNotFoundError(f"Extracted source root not found: {extracted_source_root}")

    args.bootstrap_master = True
    args.master_source_root = str(extracted_source_root)
    args.base_source_root = str(extracted_source_root)

    extracted_loc_en = extract_root / "enhanced" / "loc_en.txt"
    if extracted_loc_en.exists() and args.template == DEFAULT_ENHANCED_TEMPLATE:
        args.template = str(extracted_loc_en)

    build_from_master(args)


def add_enhanced_args(parser: argparse.ArgumentParser, include_transprocess_source: bool = True) -> None:
    parser.add_argument(
        "--template",
        default=DEFAULT_ENHANCED_TEMPLATE,
        help="Enhanced loc template path",
    )
    if include_transprocess_source:
        parser.add_argument(
            "--transprocess-source",
            default=r".ref\TransProcess\source",
            help="Classic translation table source root",
        )
    parser.add_argument(
        "--output-dir",
        default=r".tmp\remaster_patch",
        help="Output directory for enhanced artifacts",
    )
    parser.add_argument(
        "--output-name",
        default="loc_ko.txt",
        help="Generated loc filename",
    )
    parser.add_argument(
        "--slot-alias",
        default="it",
        help="Alias slot for runtime replacement (loc_<alias>.txt)",
    )
    parser.add_argument(
        "--fix-sections",
        default="subtitles",
        help="Sections to token-fix (comma-separated)",
    )
    parser.add_argument(
        "--skip-token-fix",
        action="store_true",
        help="Skip token-preservation pass",
    )
    parser.add_argument(
        "--append-unresolved",
        action="store_true",
        help="Append unresolved tokens during token-fix",
    )
    parser.add_argument(
        "--skip-patch-loc",
        action="store_true",
        help="Skip BladeRunnerEngine.kpf patch output",
    )
    parser.add_argument(
        "--skip-patch-fonts",
        action="store_true",
        help="Skip fonts.kpf patch output",
    )
    parser.add_argument(
        "--engine-kpf",
        default=r".ref\BladeRunner_Enhanced\BladeRunnerEngine.kpf",
        help="Source BladeRunnerEngine.kpf path",
    )
    parser.add_argument(
        "--fonts-kpf",
        default=r".ref\BladeRunner_Enhanced\fonts.kpf",
        help="Source fonts.kpf path",
    )
    parser.add_argument(
        "--font-file",
        default=r".ref\TransProcess\assets\fonts\Kor_font.ttf",
        help="Korean TTF file for font patching",
    )


def add_build_from_master_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--target",
        choices=["both", "classic", "enhanced"],
        default="both",
        help="Which outputs to build from master TSV",
    )
    parser.add_argument(
        "--master",
        default=r".tmp\translation_pipeline\master_translation.tsv",
        help="Input master TSV path",
    )
    parser.add_argument(
        "--bootstrap-master",
        action="store_true",
        help="Rebuild master TSV before splitting",
    )
    parser.add_argument(
        "--without-en-master",
        action="store_true",
        help="Use --without-en when bootstrapping master TSV",
    )
    parser.add_argument(
        "--master-source-root",
        default=r".ref\TransProcess\source",
        help="Source root used by bootstrap-master",
    )
    parser.add_argument(
        "--master-report-json",
        default=r".tmp\translation_pipeline\master_report.from_master.json",
        help="Report path for bootstrap-master (empty to disable)",
    )
    parser.add_argument(
        "--split-source-root",
        default=r".tmp\translation_pipeline\source_split",
        help="Split output source root passed to classic/enhanced builds",
    )
    parser.add_argument(
        "--base-source-root",
        default=r".ref\TransProcess\source",
        help="Base source root for split reference copy",
    )
    parser.add_argument(
        "--split-report-json",
        default=r".tmp\translation_pipeline\split_report.from_master.json",
        help="Report path for split-master (empty to disable)",
    )
    parser.add_argument(
        "--copy-reference",
        dest="copy_reference",
        action="store_true",
        default=True,
        help="Copy reference folders into split source root (default: on)",
    )
    parser.add_argument(
        "--no-copy-reference",
        dest="copy_reference",
        action="store_false",
        help="Do not copy reference folders into split source root",
    )
    parser.add_argument(
        "--translated-only",
        action="store_true",
        help="Split only rows with status=translated",
    )
    parser.add_argument(
        "--skip-empty-ko",
        action="store_true",
        help="Split while skipping rows with empty KO",
    )
    parser.add_argument(
        "--classic-profile",
        choices=["windows_full", "subs_only", "both"],
        default="both",
        help="Classic build profile",
    )
    parser.add_argument(
        "--classic-work-root",
        default=r".tmp\translation_pipeline\classic_work",
        help="Classic build/dist work root for build-from-master",
    )


def add_extract_local_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--classic-startup-mix",
        default="",
        help="Path to local classic STARTUP.MIX",
    )
    parser.add_argument(
        "--classic-game-dir",
        default="",
        help="Path to local classic game directory containing STARTUP.MIX",
    )
    parser.add_argument(
        "--enhanced-engine-kpf",
        default="",
        help="Path to local enhanced BladeRunnerEngine.kpf",
    )
    parser.add_argument(
        "--extract-output-root",
        default=r".tmp\translation_pipeline\local_extract",
        help="Output root for local extraction artifacts",
    )
    parser.add_argument(
        "--seed-ko-mode",
        choices=["empty", "copy-en"],
        default="empty",
        help="How ko_work is initialized during local extraction",
    )
    parser.add_argument(
        "--clean-extract-output",
        action="store_true",
        help="Clean extraction output root before extract-local",
    )
    parser.add_argument(
        "--extract-report-json",
        default=r".tmp\translation_pipeline\extract_report.from_local.json",
        help="Report path for extract-local (empty to disable)",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified Blade Runner translation pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate", help="Validate classic table inputs only")

    p_classic = sub.add_parser("build-classic", help="Build classic outputs only")
    p_classic.add_argument(
        "--profile",
        choices=["windows_full", "subs_only", "both"],
        default="both",
        help="Classic build profile",
    )

    p_enhanced = sub.add_parser("build-enhanced", help="Build enhanced outputs only")
    add_enhanced_args(p_enhanced, include_transprocess_source=True)

    p_all = sub.add_parser("build-all", help="Build both classic and enhanced outputs")
    p_all.add_argument(
        "--classic-profile",
        choices=["windows_full", "subs_only", "both"],
        default="both",
        help="Classic build profile",
    )
    add_enhanced_args(p_all, include_transprocess_source=True)

    p_master = sub.add_parser("build-from-master", help="Split master TSV then build classic/enhanced")
    add_build_from_master_args(p_master)
    add_enhanced_args(p_master, include_transprocess_source=False)

    p_extract = sub.add_parser("extract-local", help="Extract local original resources only")
    add_extract_local_args(p_extract)

    p_local = sub.add_parser("build-from-local", help="Extract local resources then build from master")
    add_build_from_master_args(p_local)
    add_enhanced_args(p_local, include_transprocess_source=False)
    add_extract_local_args(p_local)

    args = parser.parse_args()

    if args.cmd == "validate":
        run_classic("validate")
        return 0

    if args.cmd == "build-classic":
        run_classic(args.profile)
        return 0

    if args.cmd == "build-enhanced":
        build_enhanced(args)
        return 0

    if args.cmd == "build-all":
        run_classic(args.classic_profile)
        build_enhanced(args)
        return 0

    if args.cmd == "build-from-master":
        build_from_master(args)
        return 0
    if args.cmd == "extract-local":
        run_extract_local(args)
        return 0
    if args.cmd == "build-from-local":
        build_from_local(args)
        return 0

    raise ValueError(f"Unsupported command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())
