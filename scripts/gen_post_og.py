#!/usr/bin/env python3
"""글별 OG 이미지 일괄 생성 — public/og/{slug}.png (1200×630).

동작:
1. src/content/answers/*.md 모두 스캔
2. frontmatter에서 title·cluster·summary 추출
3. PNG 생성 → public/og/{slug}.png
4. frontmatter에 `image: "/og/{slug}.png"` 자동 삽입 (이미 있으면 skip)

재실행 시 PNG 덮어쓰기. 글 제목·요약 변경 후 본 스크립트 재실행하면 OG도 갱신.

실행: python scripts/gen_post_og.py --slug {slug}   (전체: --all)
"""
from __future__ import annotations
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import re

# tokens.css 색
PAPER = (251, 247, 240)
PAPER2 = (244, 238, 226)
INK = (26, 43, 42)
SOFT = (74, 88, 86)
TEAL = (14, 124, 114)
LINE = (227, 220, 207)

W, H = 1200, 630

CLUSTER_LABEL = {
    "tax":       "세금",
    "support":   "정부지원금",
    "loan":      "대출·신용",
    "insurance": "보험·연금",
}

# 폰트: 레포에 동봉한 OFL 폰트(scripts/fonts) — 로컬 Windows·클라우드 Linux 출력 동일.
# (구 버전은 C:/Windows/Fonts 바탕·맑은고딕에 의존해 클라우드에서 폴백 렌더가 갈렸다.)
FONT_DIR = Path(__file__).resolve().parent / "fonts"
FONT_BRAND   = str(FONT_DIR / "GowunBatang-Regular.ttf")
FONT_BRAND_B = str(FONT_DIR / "GowunBatang-Bold.ttf")
FONT_BODY    = str(FONT_DIR / "IBMPlexSansKR-Regular.ttf")
FONT_BODY_B  = str(FONT_DIR / "IBMPlexSansKR-Bold.ttf")

def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()

def text_w(draw, s, fnt):
    b = draw.textbbox((0, 0), s, font=fnt)
    return b[2] - b[0]

def wrap_korean(draw, text, fnt, max_w):
    """한국어 글자 단위 wrap (공백 + 글자). max_w 안에 들어가도록 줄 분리."""
    lines = []
    cur = ""
    for ch in text:
        nxt = cur + ch
        if text_w(draw, nxt, fnt) > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = nxt
    if cur:
        lines.append(cur)
    return lines


def render_og(title: str, cluster: str, slug: str, out: Path) -> None:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # 좌측 워터틸 강조 바
    d.rectangle([(0, 0), (16, H)], fill=TEAL)

    # 카테고리 라벨
    f_cat = font(FONT_BODY_B, 36)
    d.text((100, 100), CLUSTER_LABEL.get(cluster, cluster), font=f_cat, fill=TEAL)

    # 제목 — 명조 자동 줄바꿈 (1~3 줄, 우측 ? 원 피하기)
    # 글자 수에 따라 폰트 사이즈 동적 조정
    if len(title) <= 18:
        size = 100
    elif len(title) <= 30:
        size = 86
    else:
        size = 72
    f_title = font(FONT_BRAND, size)
    max_title_w = 870   # 우측 ? 원(반지름 90, 중심 x=1050) 피해 870px 여백
    lines = wrap_korean(d, title, f_title, max_title_w)
    # 너무 많으면 ...로 자르기
    if len(lines) > 4:
        lines = lines[:4]
        lines[-1] = lines[-1][:-1] + "…"
    line_h = int(size * 1.25)
    y_start = 180
    for i, line in enumerate(lines):
        d.text((100, y_start + i * line_h), line, font=f_title, fill=INK)

    # 워터틸 짧은 separator
    d.rectangle([(100, 510), (180, 514)], fill=TEAL)

    # 도메인
    f_dom = font(FONT_BODY_B, 32)
    d.text((100, 528), "mureobom.com", font=f_dom, fill=TEAL)

    # 우하단 ? 원 — sub-CTA
    cx, cy, r = 1050, 470, 90
    d.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=TEAL)
    f_q = font(FONT_BRAND, 130)
    qb = d.textbbox((0, 0), "?", font=f_q)
    qw = qb[2] - qb[0]
    qh = qb[3] - qb[1]
    d.text((cx - qw / 2 - 4, cy - qh / 2 - 18), "?", font=f_q, fill=PAPER)

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)


# ── frontmatter 파서 (간이) ──
FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)

def parse_frontmatter(text: str) -> tuple[dict, str, str]:
    m = FM_RE.match(text)
    if not m:
        return {}, "", text
    fm_text = m.group(1)
    body = text[m.end():]
    data: dict = {}
    for line in fm_text.splitlines():
        m2 = re.match(r'^([a-zA-Z_]+):\s*(.+?)\s*$', line)
        if m2:
            k, v = m2.group(1), m2.group(2)
            data[k] = v.strip('"').strip("'")
    return data, fm_text, body


def ensure_image_field(md_path: Path, slug: str) -> bool:
    """frontmatter에 image 필드가 없으면 추가. 변경했으면 True."""
    text = md_path.read_text(encoding="utf-8")
    m = FM_RE.match(text)
    if not m:
        return False
    fm = m.group(1)
    if re.search(r"^image:", fm, re.MULTILINE):
        return False
    # disclaimer 라인 뒤에 image 추가 (Zod 순서 의식)
    new_line = f'image: "/og/{slug}.png"'
    if re.search(r"^disclaimer:", fm, re.MULTILINE):
        new_fm = re.sub(
            r"(^disclaimer:.*$)", r"\1\n" + new_line,
            fm, count=1, flags=re.MULTILINE
        )
    else:
        new_fm = fm.rstrip() + "\n" + new_line
    new_text = text[: m.start(1)] + new_fm + text[m.end(1):]
    md_path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="글별 OG PNG 생성 (public/og/{slug}.png)")
    ap.add_argument("--slug", action="append", default=[], help="대상 슬러그 (여러 번 지정 가능)")
    ap.add_argument("--all", action="store_true", help="전체 글 재생성 (290편 PNG가 모두 바뀌므로 신중히)")
    args = ap.parse_args()
    if not args.slug and not args.all:
        ap.error("--slug {slug} 또는 --all 을 지정하세요 (publish-daily는 --slug 사용)")

    root = Path(__file__).resolve().parent.parent
    answers_dir = root / "src" / "content" / "answers"
    out_dir = root / "public" / "og"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(answers_dir.glob("*.md")) if args.all else [answers_dir / f"{s}.md" for s in args.slug]
    missing = [f for f in files if not f.exists()]
    if missing:
        raise SystemExit(f"  ✗ 없는 글: {', '.join(str(m) for m in missing)}")
    print(f"  scanning {len(files)} posts...")
    for md in files:
        slug = md.stem
        text = md.read_text(encoding="utf-8")
        fm_data, _, _ = parse_frontmatter(text)
        title = fm_data.get("title", slug)
        cluster = fm_data.get("cluster", "support")
        out_png = out_dir / f"{slug}.png"
        render_og(title, cluster, slug, out_png)
        added = ensure_image_field(md, slug)
        flag = " (+ frontmatter image:)" if added else ""
        print(f"  ✓ {out_png}  ({out_png.stat().st_size} B) — {title[:30]}{flag}")
    print(f"\n  완료: {len(files)} OG 이미지 → public/og/")


if __name__ == "__main__":
    main()
