#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict


REQUIRED_PREFIXES = ("PZ", "KZ", "FS")
OUTPUT_PREFIX = "COMBINED"


def collect_files(folder: Path) -> Dict[str, Dict[str, Path]]:
    files_by_prefix: Dict[str, Dict[str, Path]] = {prefix: {} for prefix in REQUIRED_PREFIXES}

    for path in folder.glob("*.DOZ"):
        if "_" not in path.name:
            continue

        prefix, suffix = path.stem.split("_", 1)
        if prefix in files_by_prefix:
            files_by_prefix[prefix][suffix] = path

    return files_by_prefix


def merge_folder(folder: Path) -> tuple[int, list[str]]:
    files_by_prefix = collect_files(folder)
    all_suffixes = set()
    for paths in files_by_prefix.values():
        all_suffixes.update(paths)

    output_dir = folder / "merged"
    output_dir.mkdir(exist_ok=True)

    merged_count = 0
    issues: list[str] = []

    for suffix in sorted(all_suffixes):
        missing = [prefix for prefix in REQUIRED_PREFIXES if suffix not in files_by_prefix[prefix]]
        if missing:
            issues.append(f"{folder.name}:{suffix} missing {', '.join(missing)}")
            continue

        merged_bytes = b"".join(
            files_by_prefix[prefix][suffix].read_bytes() for prefix in REQUIRED_PREFIXES
        )
        output_path = output_dir / f"{OUTPUT_PREFIX}_{suffix}.DOZ"
        output_path.write_bytes(merged_bytes)
        merged_count += 1

    return merged_count, issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create merged .DOZ files for each folder by concatenating matching "
            "PZ, KZ, and FS files in that order."
        )
    )
    parser.add_argument(
        "folders",
        nargs="+",
        help="One or more folders containing PZ_*.DOZ, KZ_*.DOZ, and FS_*.DOZ files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    had_issues = False

    for folder_arg in args.folders:
        folder = Path(folder_arg).expanduser().resolve()
        if not folder.is_dir():
            print(f"{folder_arg}: not a directory")
            had_issues = True
            continue

        merged_count, issues = merge_folder(folder)
        print(f"{folder.name}: created {merged_count} merged files in {folder / 'merged'}")
        if issues:
            had_issues = True
            for issue in issues:
                print(f"  warning: {issue}")

    return 1 if had_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
