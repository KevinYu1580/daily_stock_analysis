#!/usr/bin/env python3
"""簡轉繁（台灣慣用詞 s2twp）批次轉換工具。

只轉指定檔案清單；對 PRESERVE 清單中的字串原樣保留（避免破壞跨界比對）。
用法：
    python scripts/s2twp_convert.py --frontend     # 轉前端 apps/dsa-web
    python scripts/s2twp_convert.py --files a.py b.py ...
    python scripts/s2twp_convert.py --dry-run --frontend
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import opencc

ROOT = Path(__file__).resolve().parent.parent
CONVERTER = opencc.OpenCC("s2twp")

# 這些字串原樣保留（跨界比對用，前後端必須一致）
PRESERVE = [
    "必须提供 stock_code 或 stock_codes",
]

FRONTEND_DIR = ROOT / "apps" / "dsa-web"
FRONTEND_GLOBS = ["src/**/*.ts", "src/**/*.tsx", "src/**/*.css", "src/**/*.html",
                  "index.html", "e2e/**/*.ts"]
FRONTEND_EXCLUDE_PARTS = {"node_modules", "dist", "coverage"}

HAN_RANGE = range(0x4E00, 0x9FFF + 1)


def has_han(text: str) -> bool:
    return any(ord(ch) in HAN_RANGE for ch in text)


def convert_text(text: str) -> str:
    if not has_han(text):
        return text
    # 用佔位符保護 PRESERVE 字串（純 ASCII，OpenCC 不會動；勿用 \x00 會截斷 C 字串）
    placeholders: dict[str, str] = {}
    for i, s in enumerate(PRESERVE):
        if s in text:
            ph = f"ZZQPRESERVEQZZ{i}ZZ"
            placeholders[ph] = s
            text = text.replace(s, ph)
    converted = CONVERTER.convert(text)
    for ph, s in placeholders.items():
        converted = converted.replace(ph, s)
    return converted


def iter_frontend_files() -> list[Path]:
    files: list[Path] = []
    for g in FRONTEND_GLOBS:
        for p in FRONTEND_DIR.glob(g):
            if not p.is_file():
                continue
            if FRONTEND_EXCLUDE_PARTS & set(p.parts):
                continue
            files.append(p)
    return sorted(set(files))


def process(files: list[Path], dry_run: bool) -> int:
    changed = 0
    for p in files:
        try:
            original = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as e:
            print(f"  skip {p}: {e}", file=sys.stderr)
            continue
        converted = convert_text(original)
        if converted != original:
            changed += 1
            rel = p.relative_to(ROOT)
            if dry_run:
                print(f"  WOULD CHANGE {rel}")
            else:
                p.write_text(converted, encoding="utf-8")
                print(f"  converted {rel}")
    return changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frontend", action="store_true", help="轉 apps/dsa-web 前端")
    ap.add_argument("--files", nargs="*", help="明確指定要轉的檔案")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files: list[Path] = []
    if args.frontend:
        files += iter_frontend_files()
    if args.files:
        files += [Path(f).resolve() for f in args.files]
    if not files:
        ap.error("需指定 --frontend 或 --files")

    print(f"目標 {len(files)} 個檔案，dry_run={args.dry_run}")
    changed = process(files, args.dry_run)
    print(f"完成，{changed} 個檔案{'將' if args.dry_run else '已'}變更")


if __name__ == "__main__":
    main()
