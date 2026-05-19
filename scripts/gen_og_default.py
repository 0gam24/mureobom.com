#!/usr/bin/env python3
"""1200×630 OG default image generator — public/og-default.png 생성.

브랜드 컨셉(물어봄): 워터틸 + 크림 종이 + 명조 헤드라인 + sprout 글리프.
디자인 소스 og-default.svg와 동일 구도. PNG는 SNS 미리보기 호환 필수.

실행:
    pip install Pillow
    python scripts/gen_og_default.py
재생성 필요 시 (예: 브랜드 색 변경) 본 스크립트만 다시 돌리면 됨.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# tokens.css와 동일 색
PAPER  = (251, 247, 240)  # #FBF7F0
PAPER2 = (244, 238, 226)  # #F4EEE2
INK    = (26, 43, 42)     # #1A2B2A
SOFT   = (74, 88, 86)     # #4A5856
TEAL   = (14, 124, 114)   # #0E7C72

W, H = 1200, 630

# Windows 기본 폰트 (모든 Windows 머신에 설치돼 있음)
FONT_BRAND = "C:/Windows/Fonts/batang.ttc"     # 바탕체 (명조) — 헤드라인
FONT_BODY  = "C:/Windows/Fonts/malgun.ttf"     # 맑은고딕 — 본문/도메인

def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()

def text_size(draw, text, fnt):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def main() -> None:
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # 좌측 워터틸 강조 바
    d.rectangle([(0, 0), (16, H)], fill=TEAL)

    # ── 브랜드 로고 — 명조 ──
    f_brand = font(FONT_BRAND, 160)
    f_lead  = font(FONT_BODY,  46)
    f_dom   = font(FONT_BODY,  32)
    f_q     = font(FONT_BRAND, 130)

    # "물어" + "봄" — 봄만 워터틸
    x_brand = 100
    y_brand = 170
    mueo_w, _ = text_size(d, "물어", f_brand)
    d.text((x_brand, y_brand), "물어", font=f_brand, fill=INK)
    d.text((x_brand + mueo_w, y_brand), "봄", font=f_brand, fill=TEAL)

    # sprout 글리프 (봄 우측, 잎사귀 형태로 살짝)
    bom_w, _ = text_size(d, "봄", f_brand)
    sx = x_brand + mueo_w + bom_w + 18
    sy = y_brand + 30
    # 작은 잎 모양 — 삼각형 + 둥근 보정
    d.polygon([(sx, sy + 40), (sx + 60, sy + 10), (sx + 56, sy + 60)], fill=TEAL)
    d.ellipse([(sx + 10, sy + 22), (sx + 38, sy + 50)], fill=PAPER)
    d.ellipse([(sx + 12, sy + 24), (sx + 36, sy + 48)], fill=TEAL)

    # ── 한 줄 설명 ──
    d.text((x_brand, 380), "세금·정부지원금·대출·보험", font=f_lead, fill=SOFT)
    d.text((x_brand, 446), "공식 자료로 확인한 답.",   font=f_lead, fill=SOFT)

    # 하단 가로줄 (페이퍼-2)
    d.rectangle([(x_brand, 535), (x_brand + 200, 538)], fill=TEAL)

    # 도메인
    d.text((x_brand, 555), "mureobom.com", font=f_dom, fill=TEAL)

    # ── 우하단 "?" 원 ──
    cx, cy, r = 1050, 470, 90
    d.ellipse([(cx - r, cy - r), (cx + r, cy + r)], fill=TEAL)
    qw, qh = text_size(d, "?", f_q)
    d.text((cx - qw / 2 - 4, cy - qh / 2 - 18), "?", font=f_q, fill=PAPER)

    out = Path("public/og-default.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print(f"wrote {out} ({out.stat().st_size} bytes, {W}x{H})")


if __name__ == "__main__":
    main()
