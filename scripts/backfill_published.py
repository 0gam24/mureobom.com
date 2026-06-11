#!/usr/bin/env python3
"""src/content/answers/*.md 프론트매터에 published: 필드 백필.

값은 해당 파일이 git에 처음 추가된 커밋 일자:
    git log --follow --diff-filter=A --format=%as -- {파일}
(출력은 최신순이므로 마지막 줄 = 최초 추가일. 미커밋 신규 파일은 updated 값으로 폴백.)

- 삽입 위치: updated: 줄 바로 다음 (frontmatter 순서 고정).
- updated와 같아도 일관성을 위해 전부 기입.
- 멱등: 이미 published: 가 있으면 건너뜀.

실행:  python scripts/backfill_published.py
"""
from __future__ import annotations

import glob
import io
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANSWERS_DIR = os.path.join(REPO_ROOT, "src", "content", "answers")


def first_commit_date(path: str) -> str | None:
    """파일이 처음 추가된 커밋의 날짜(YYYY-MM-DD). 히스토리 없으면 None."""
    out = subprocess.run(
        ["git", "log", "--follow", "--diff-filter=A", "--format=%as", "--", path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.strip()
    if not out:
        return None
    return out.splitlines()[-1]  # 최신순 출력 → 마지막 줄이 최초 추가일


def backfill(path: str) -> str:
    text = open(path, encoding="utf-8").read()
    fm_match = re.match(r"\A---\n(.*?\n)---\n", text, re.S)
    if not fm_match:
        return "skip(no frontmatter)"
    fm = fm_match.group(1)
    if re.search(r"^published:", fm, re.M):
        return "skip(already)"
    updated_match = re.search(r"^updated:\s*(\S+)\s*$", fm, re.M)
    if not updated_match:
        return "skip(no updated)"
    updated = updated_match.group(1)
    published = first_commit_date(path) or updated
    # datePublished > dateModified 역전 방지 — git 최초 커밋이 updated보다 늦으면 updated로 캡
    if published > updated:
        published = updated
    new_fm = fm.replace(
        updated_match.group(0),
        f"{updated_match.group(0)}\npublished: {published}",
        1,
    )
    open(path, "w", encoding="utf-8", newline="\n").write(
        text.replace(fm, new_fm, 1)
    )
    return f"published: {published}"


def main() -> None:
    files = sorted(glob.glob(os.path.join(ANSWERS_DIR, "*.md")))
    if not files:
        print("no answer files found", file=sys.stderr)
        sys.exit(1)
    for path in files:
        result = backfill(path)
        print(f"{os.path.basename(path)} -> {result}")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
