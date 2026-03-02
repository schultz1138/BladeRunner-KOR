#!/usr/bin/env python3
"""
TransProcess build pipeline for Blade Runner Korean localization resources.

Profiles:
- windows_full : includes UI TRE + cutscene TRE + ingame TRE + fixed assets
- subs_only    : includes cutscene TRE + ingame TRE + fixed assets (no UI TRE)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class PipelineContext:
    root: Path
    source_root: Path
    work_root: Path
    src_ui_ko: Path
    src_cut_ko: Path
    src_ing_ko: Path
    src_ing_base: Path
    asset_fixed: Path
    asset_fonts: Path
    build_tre_ui: Path
    build_tre_cut: Path
    build_tre_ing: Path
    build_pack_input: Path
    build_reports: Path
    dist_windows_full: Path
    dist_subs_only: Path
    tool_ui: Path
    tool_cut: Path
    tool_ing: Path
    tool_pack: Path
    tool_validate_ing: Path


def create_context(source_root: Path | None, work_root: Path | None) -> PipelineContext:
    resolved_source_root = source_root.resolve() if source_root else (ROOT / "source")
    resolved_work_root = work_root.resolve() if work_root else ROOT

    return PipelineContext(
        root=ROOT,
        source_root=resolved_source_root,
        work_root=resolved_work_root,
        src_ui_ko=resolved_source_root / "ui" / "ko_work",
        src_cut_ko=resolved_source_root / "cutscene" / "ko_work",
        src_ing_ko=resolved_source_root / "ingame" / "ko_work",
        src_ing_base=resolved_source_root / "ingame" / "en_reference",
        asset_fixed=ROOT / "assets" / "fixed",
        asset_fonts=ROOT / "assets" / "fonts",
        build_tre_ui=resolved_work_root / "build" / "tre" / "ui",
        build_tre_cut=resolved_work_root / "build" / "tre" / "cutscene",
        build_tre_ing=resolved_work_root / "build" / "tre" / "ingame",
        build_pack_input=resolved_work_root / "build" / "pack_input",
        build_reports=resolved_work_root / "build" / "reports",
        dist_windows_full=resolved_work_root / "dist" / "windows_full" / "SUBTITLES.MIX",
        dist_subs_only=resolved_work_root / "dist" / "subs_only" / "M_SUBTITLES.MIX",
        tool_ui=ROOT / "tools" / "converters" / "ui_csv_to_tre.py",
        tool_cut=ROOT / "tools" / "converters" / "cutscene_csv_to_tre.py",
        tool_ing=ROOT / "tools" / "converters" / "ingame_csv_to_tre.py",
        tool_pack=ROOT / "tools" / "pack" / "pack_mix.py",
        tool_validate_ing=ROOT / "tools" / "validate" / "validate_ingame_csv.py",
    )


def run(cmd: list[str]) -> None:
    print("[RUN]", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


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


def find_baseline_table(ctx: PipelineContext, stem: str) -> Path | None:
    tsv = ctx.src_ing_base / f"{stem}.tsv"
    csv_path = ctx.src_ing_base / f"{stem}.csv"
    if tsv.is_file():
        return tsv
    if csv_path.is_file():
        return csv_path
    return None


def validate_ingame(ctx: PipelineContext) -> None:
    table_files = collect_table_files(ctx.src_ing_ko)
    if not table_files:
        print(f"[WARN] no ingame table files (.csv/.tsv) in {ctx.src_ing_ko}")
        return

    for table_file in table_files:
        base = find_baseline_table(ctx, table_file.stem)
        cmd = [sys.executable, str(ctx.tool_validate_ing), str(table_file)]
        if base and base.is_file():
            cmd.extend(["--baseline", str(base)])
        run(cmd)


def convert_all(ctx: PipelineContext) -> None:
    clean_dir(ctx.build_tre_ui)
    clean_dir(ctx.build_tre_cut)
    clean_dir(ctx.build_tre_ing)

    run([sys.executable, str(ctx.tool_ui), str(ctx.src_ui_ko), str(ctx.build_tre_ui)])
    run([sys.executable, str(ctx.tool_cut), str(ctx.src_cut_ko), str(ctx.build_tre_cut)])
    run([sys.executable, str(ctx.tool_ing), str(ctx.src_ing_ko), str(ctx.build_tre_ing)])


def stage_pack_input(ctx: PipelineContext, profile: str) -> list[str]:
    clean_dir(ctx.build_pack_input)

    # fixed assets
    for path in sorted(ctx.asset_fixed.glob("*")):
        if path.is_file():
            shutil.copy2(path, ctx.build_pack_input / path.name)

    # font assets
    for path in sorted(ctx.asset_fonts.glob("*")):
        if path.is_file():
            shutil.copy2(path, ctx.build_pack_input / path.name)

    # subtitle TRE assets
    for path in sorted(ctx.build_tre_cut.glob("*.TRE")):
        shutil.copy2(path, ctx.build_pack_input / path.name)
    for path in sorted(ctx.build_tre_ing.glob("*.TRE")):
        shutil.copy2(path, ctx.build_pack_input / path.name)

    # UI TRE only for full profile
    if profile == "windows_full":
        for path in sorted(ctx.build_tre_ui.glob("*.TRE")):
            shutil.copy2(path, ctx.build_pack_input / path.name)

    names = sorted(p.name for p in ctx.build_pack_input.iterdir() if p.is_file())
    if not names:
        raise RuntimeError("pack_input is empty")

    ctx.build_reports.mkdir(parents=True, exist_ok=True)
    manifest = ctx.build_reports / f"pack_manifest_{profile}.txt"
    manifest.write_text("\n".join(names) + "\n", encoding="utf-8")
    return names


def pack_profile(ctx: PipelineContext, profile: str) -> None:
    stage_pack_input(ctx, profile)

    if profile == "windows_full":
        out_mix = ctx.dist_windows_full
    elif profile == "subs_only":
        out_mix = ctx.dist_subs_only
    else:
        raise ValueError(f"Unknown profile: {profile}")

    out_mix.parent.mkdir(parents=True, exist_ok=True)
    manifest = ctx.build_reports / f"pack_manifest_{profile}.txt"
    run([sys.executable, str(ctx.tool_pack), str(ctx.build_pack_input), str(out_mix), "--manifest", str(manifest)])

    report = ctx.build_reports / f"build_{profile}.txt"
    report.write_text(
        "\n".join(
            [
                f"profile={profile}",
                f"source_root={ctx.source_root}",
                f"work_root={ctx.work_root}",
                f"output={out_mix}",
                f"size={out_mix.stat().st_size}",
                f"manifest={manifest}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"[OK] {profile} -> {out_mix}")


def main() -> None:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--source-root",
        default="",
        help="Override source root containing ui/cutscene/ingame folders",
    )
    parent.add_argument(
        "--work-root",
        default="",
        help="Override work root for build/dist outputs",
    )

    parser = argparse.ArgumentParser(description="TransProcess pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate", help="Validate input table files (TSV/CSV)", parents=[parent])

    p_build = sub.add_parser("build", help="Build one profile", parents=[parent])
    p_build.add_argument("--profile", choices=["windows_full", "subs_only"], default="windows_full")

    sub.add_parser("build-all", help="Build both windows_full and subs_only", parents=[parent])

    args = parser.parse_args()

    source_root = Path(args.source_root) if args.source_root else None
    work_root = Path(args.work_root) if args.work_root else None
    ctx = create_context(source_root=source_root, work_root=work_root)

    if args.cmd == "validate":
        validate_ingame(ctx)
        print("[OK] validation done")
        return

    if args.cmd == "build":
        validate_ingame(ctx)
        convert_all(ctx)
        pack_profile(ctx, args.profile)
        return

    if args.cmd == "build-all":
        validate_ingame(ctx)
        convert_all(ctx)
        pack_profile(ctx, "windows_full")
        pack_profile(ctx, "subs_only")
        return


if __name__ == "__main__":
    main()
