#!/usr/bin/env python3
"""Preview and safely apply batch file renames from the command line."""
from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview and batch-rename files. Preview is the default; use --apply to rename files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--prefix", default="", help="Text to add to the beginning of each file name")
    parser.add_argument("--suffix", default="", help="Text to add before each file extension")
    parser.add_argument("--find", default="", help="Text to replace in each file name (case-sensitive)")
    parser.add_argument("--replace", default="", help="Replacement text used with --find")
    parser.add_argument("--number", action="store_true", help="Append a sequence number to each file name")
    parser.add_argument("--start", type=int, default=1, help="First sequence number")
    parser.add_argument("--width", type=int, default=3, help="Minimum number of digits in sequence numbers")
    parser.add_argument("--recursive", action="store_true", help="Include files in subfolders")
    parser.add_argument("--apply", action="store_true", help="Apply the rename plan after confirmation")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation (valid only with --apply)")
    args = parser.parse_args()
    if args.yes and not args.apply:
        parser.error("--yes can only be used with --apply")
    if args.start < 0:
        parser.error("--start must be zero or greater")
    if args.width < 1 or args.width > 12:
        parser.error("--width must be between 1 and 12")
    if args.replace and not args.find:
        parser.error("--replace requires --find")
    return args


def collect_files(folder: Path, recursive: bool) -> list[Path]:
    iterator = folder.rglob("*") if recursive else folder.iterdir()
    return sorted((path for path in iterator if path.is_file()), key=lambda path: str(path).casefold())


def create_plan(files: list[Path], args: argparse.Namespace) -> list[tuple[Path, Path, str]]:
    plan = []
    for index, source in enumerate(files):
        stem = source.stem
        if args.find:
            stem = stem.replace(args.find, args.replace)
        stem = f"{args.prefix}{stem}{args.suffix}"
        if args.number:
            stem = f"{stem}_{args.start + index:0{args.width}d}"
        target = source.with_name(stem + source.suffix)
        plan.append((source, target, "Ready" if target != source else "Unchanged"))

    destinations: dict[str, list[int]] = {}
    for index, (_, target, _) in enumerate(plan):
        destinations.setdefault(os.path.normcase(str(target)), []).append(index)
    for indexes in destinations.values():
        if len(indexes) > 1:
            for index in indexes:
                source, target, _ = plan[index]
                plan[index] = (source, target, "Name conflict")

    moving_sources = {
        os.path.normcase(str(source))
        for source, target, status in plan
        if status == "Ready" and source != target
    }
    for index, (source, target, status) in enumerate(plan):
        if status in ("Name conflict", "Unchanged"):
            continue
        if target.exists() and os.path.normcase(str(target)) not in moving_sources:
            plan[index] = (source, target, "Target already exists")
    return plan


def print_plan(plan: list[tuple[Path, Path, str]]) -> tuple[int, int]:
    print(f"{'STATUS':<22}  {'CURRENT NAME':<48}  NEW NAME")
    print("-" * 112)
    ready = 0
    conflicts = 0
    for source, target, status in plan:
        print(f"{status:<22}  {str(source):<48}  {target}")
        if status == "Ready":
            ready += 1
        elif status in ("Name conflict", "Target already exists"):
            conflicts += 1
    print("-" * 112)
    print(f"Files: {len(plan)} | Changes: {ready} | Conflicts: {conflicts}")
    return ready, conflicts


def apply_plan(plan: list[tuple[Path, Path, str]], skip_confirmation: bool) -> bool:
    changes = [(source, target) for source, target, status in plan if status == "Ready"]
    if not changes:
        print("There are no files to rename.")
        return True
    if not skip_confirmation:
        answer = input(f"Rename {len(changes)} file(s)? Type YES to continue: ").strip()
        if answer != "YES":
            print("Cancelled. No files were renamed.")
            return False

    staged: list[tuple[Path, Path, Path]] = []
    completed: set[Path] = set()
    try:
        # Staging first allows swaps and cyclic renames without overwriting files.
        for source, target in changes:
            temporary = source.with_name(f".bulk-renamer-{uuid.uuid4().hex}.tmp")
            source.rename(temporary)
            staged.append((source, temporary, target))
        for _, temporary, target in staged:
            temporary.rename(target)
            completed.add(target)
    except OSError as exc:
        rollback_errors = []
        for source, temporary, target in reversed(staged):
            current = target if target in completed else temporary
            if current.exists():
                try:
                    current.rename(source)
                except OSError as rollback_exc:
                    rollback_errors.append(f"{current} -> {source}: {rollback_exc}")
        print(f"Error: rename failed: {exc}", file=sys.stderr)
        if rollback_errors:
            print("Rollback issues:", file=sys.stderr)
            for error in rollback_errors:
                print(f"  {error}", file=sys.stderr)
        return False

    print(f"Successfully renamed {len(changes)} file(s).")
    return True


def main() -> int:
    args = parse_args()
    folder = args.folder.expanduser()
    if not folder.is_dir():
        print(f"Error: folder does not exist or is not a directory: {folder}", file=sys.stderr)
        return 2
    try:
        files = collect_files(folder, args.recursive)
    except OSError as exc:
        print(f"Error: cannot read folder: {exc}", file=sys.stderr)
        return 2
    plan = create_plan(files, args)
    ready, conflicts = print_plan(plan)
    if conflicts:
        print("Resolve the conflicts before applying any changes.", file=sys.stderr)
        return 1
    if args.apply:
        return 0 if apply_plan(plan, args.yes) else 1
    if ready:
        print("Preview only. Add --apply to rename these files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
