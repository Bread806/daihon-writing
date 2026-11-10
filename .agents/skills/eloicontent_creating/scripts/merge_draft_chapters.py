#!/usr/bin/env python3
# .claude/skills/eloicontent_creating/scripts/merge_draft_chapters.py
"""
合併 loop 草稿資料夾中的 ch1～ch6 章節為單一檔案。

用法：
  python merge_draft_chapters.py --dir <草稿資料夾> [--chapters 1-6] [--output <路徑>]

輸出檔名預設：{模型名}_loopN_草稿.md（寫在草稿資料夾內）

支援的章節檔名格式（依優先順序）：
  loop{N}_ch{M}.md / .txt
  ch{M}.md / .txt
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FOLDER_PATTERN = re.compile(r"^(?P<model>.+)_loop(?P<loop>\d+)_草稿$")
CHAPTER_PATTERNS = (
    re.compile(r"^loop\d+_ch(?P<num>\d+)\.(?:md|txt)$", re.IGNORECASE),
    re.compile(r"^ch(?P<num>\d+)\.(?:md|txt)$", re.IGNORECASE),
)


def parse_chapter_range(spec: str) -> list[int]:
    """將 '1-6' 或 '1,2,3' 轉成章節編號列表。"""
    spec = spec.strip()
    if "-" in spec:
        start_s, end_s = spec.split("-", 1)
        start, end = int(start_s), int(end_s)
        if start > end:
            raise ValueError(f"章節範圍無效：{spec}")
        return list(range(start, end + 1))
    return [int(part.strip()) for part in spec.split(",") if part.strip()]


def parse_folder_name(folder: Path) -> tuple[str, int]:
    match = FOLDER_PATTERN.match(folder.name)
    if not match:
        raise ValueError(
            f"資料夾名稱須符合 {{模型名}}_loopN_草稿，目前為：{folder.name}"
        )
    return match.group("model"), int(match.group("loop"))


def find_chapter_file(draft_dir: Path, chapter_num: int) -> Path | None:
    candidates: list[tuple[int, Path]] = []
    for path in draft_dir.iterdir():
        if not path.is_file():
            continue
        for pattern in CHAPTER_PATTERNS:
            m = pattern.match(path.name)
            if m and int(m.group("num")) == chapter_num:
                candidates.append((pattern.__hash__(), path))
                break
    if not candidates:
        return None
    # 同章若有多種命名，取優先順序較前者
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def merge_chapters(
    draft_dir: Path,
    chapters: list[int],
    output_path: Path | None = None,
    separator: str = "\n\n---\n\n",
) -> Path:
    if not draft_dir.is_dir():
        raise FileNotFoundError(f"找不到草稿資料夾：{draft_dir}")

    model, loop_num = parse_folder_name(draft_dir)

    if output_path is None:
        output_path = draft_dir / f"{model}_loop{loop_num}_草稿.md"

    parts: list[str] = []
    missing: list[int] = []

    for num in chapters:
        chapter_file = find_chapter_file(draft_dir, num)
        if chapter_file is None:
            missing.append(num)
            continue
        content = chapter_file.read_text(encoding="utf-8").strip()
        if content:
            parts.append(content)

    if missing:
        raise FileNotFoundError(
            f"缺少章節檔案：{', '.join(f'ch{n}' for n in missing)} "
            f"（目錄：{draft_dir}）"
        )

    if not parts:
        raise ValueError(f"沒有可合併的章節內容：{draft_dir}")

    merged = separator.join(parts) + "\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(merged, encoding="utf-8")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="合併 loop 草稿資料夾中的章節為 {模型名}_loopN_草稿.md"
    )
    parser.add_argument(
        "--dir",
        "-d",
        required=True,
        type=Path,
        help="草稿資料夾路徑，例如 workspace/角色名/model_loop3_草稿",
    )
    parser.add_argument(
        "--chapters",
        "-c",
        default="1-6",
        help="要合併的章節，預設 1-6；可用 1-6 或 1,3,5",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="輸出檔案路徑（預設寫在草稿資料夾內）",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        chapters = parse_chapter_range(args.chapters)
        output = merge_chapters(args.dir.resolve(), chapters, args.output)
    except (ValueError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(output)


if __name__ == "__main__":
    main()
