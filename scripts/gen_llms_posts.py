#!/usr/bin/env python3
"""public/llms.txt 발행 글 블록 재생성 — POSTS:auto 마커 사이를 전부 다시 쓴다.

src/content/answers/*.md 프론트매터(title·summary·cluster)를 파싱해
`<!-- POSTS:auto -->` ~ `<!-- /POSTS:auto -->` 사이를 절대 URL 항목으로 재생성.
마커 밖(헤더·카테고리 등 정적 섹션)은 그대로 보존한다.

항목 형식 (기존 llms.txt 스타일 + 절대 URL):
    - https://mureobom.com/{cluster}/{slug}/ — {title} : {summary}

정렬: updated 오름차순 → slug (발행 순서 근사, 결정적 출력).
글 수 != 생성 항목 수면 에러 출력 후 exit 1.

실행:
    python scripts/gen_llms_posts.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

# Windows 콘솔(cp949)에서도 한국어/대시 출력이 깨지지 않도록
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
ANSWERS_DIR = ROOT / "src" / "content" / "answers"
LLMS_TXT = ROOT / "public" / "llms.txt"

SITE = "https://mureobom.com"
BEGIN_MARK = "<!-- POSTS:auto -->"
END_MARK = "<!-- /POSTS:auto -->"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(path: Path) -> dict:
    """*.md 상단 YAML 프론트매터를 dict로. 필수 필드 누락 시 ValueError."""
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"{path.name}: 프론트매터 블록(---) 없음")
    fm = yaml.safe_load(m.group(1))
    if not isinstance(fm, dict):
        raise ValueError(f"{path.name}: 프론트매터가 매핑이 아님")
    for key in ("title", "summary", "cluster"):
        if not fm.get(key):
            raise ValueError(f"{path.name}: 필수 필드 누락 — {key}")
    return fm


def build_entries() -> list[str]:
    """answers 전체를 '- {url} — {title} : {summary}' 줄 목록으로."""
    posts = []
    errors = []
    md_files = sorted(ANSWERS_DIR.glob("*.md"))
    for path in md_files:
        try:
            fm = parse_frontmatter(path)
        except ValueError as e:
            errors.append(str(e))
            continue
        posts.append(
            {
                "slug": path.stem.lower(),  # Astro 슬러그 정규화(소문자)와 일치
                "cluster": fm["cluster"],
                "title": str(fm["title"]).strip(),
                "summary": str(fm["summary"]).strip(),
                "updated": str(fm.get("updated", "")),
            }
        )
    if errors:
        for e in errors:
            print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)

    posts.sort(key=lambda p: (p["updated"], p["slug"]))
    entries = [
        f"- {SITE}/{p['cluster']}/{p['slug']}/ — {p['title']} : {p['summary']}"
        for p in posts
    ]

    if len(entries) != len(md_files):
        print(
            f"[ERROR] 글 수({len(md_files)}) != 항목 수({len(entries)})",
            file=sys.stderr,
        )
        sys.exit(1)
    return entries


def main() -> None:
    # read_text는 universal newlines로 \r\n을 \n으로 바꿔버리므로 bytes로 판별
    raw = LLMS_TXT.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in raw else "\n"  # 기존 줄바꿈 보존 (Windows 호환)
    text = raw.replace("\r\n", "\n")

    begin = text.find(BEGIN_MARK)
    end = text.find(END_MARK)
    if begin == -1 or end == -1 or end < begin:
        print(
            f"[ERROR] {LLMS_TXT.name}에 {BEGIN_MARK} / {END_MARK} 마커 필요",
            file=sys.stderr,
        )
        sys.exit(1)

    entries = build_entries()
    block = BEGIN_MARK + "\n" + "\n".join(entries) + "\n" + END_MARK
    new_text = text[:begin] + block + text[end + len(END_MARK):]

    LLMS_TXT.write_text(new_text.replace("\n", eol), encoding="utf-8", newline="")

    n_files = len(list(ANSWERS_DIR.glob("*.md")))
    print(f"[OK] llms.txt 재생성 — 글 {n_files}편 / 항목 {len(entries)}건")


if __name__ == "__main__":
    main()
