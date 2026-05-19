#!/usr/bin/env python3
"""apple-touch-icon.png 180×180 생성.

iOS 홈 화면에 추가 시 표시. 워터틸 둥근 사각 + 명조 ? 글리프.
재생성: python scripts/gen_apple_touch_icon.py
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

PAPER = (251, 247, 240)
TEAL  = (14, 124, 114)

S = 180
RADIUS = 38  # iOS 자체적으로 마스킹하지만 안전하게 borderRadius도 적용

img = Image.new("RGB", (S, S), PAPER)
d = ImageDraw.Draw(img)

# 둥근 사각 배경 (워터틸)
d.rounded_rectangle([(0, 0), (S, S)], radius=RADIUS, fill=TEAL)

try:
    f = ImageFont.truetype("C:/Windows/Fonts/batang.ttc", 130)
except OSError:
    f = ImageFont.load_default()

bbox = d.textbbox((0, 0), "?", font=f)
w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
d.text(((S - w) / 2 - 2, (S - h) / 2 - 20), "?", font=f, fill=PAPER)

out = Path("public/apple-touch-icon.png")
img.save(out, "PNG", optimize=True)
print(f"wrote {out} ({out.stat().st_size} bytes, {S}x{S})")
