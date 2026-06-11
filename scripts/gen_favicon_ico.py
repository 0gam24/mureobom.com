#!/usr/bin/env python3
"""favicon.ico 생성 (16/32/48 멀티 사이즈).

구형 UA·브라우저 탭 폴백용 (Base.astro의 `rel="alternate icon"`).
워터틸 둥근 사각 + 명조 ? 글리프 — apple-touch-icon과 동일 모티프.
색 상수는 src/styles/tokens.css의 hex 값 그대로.
재생성: python scripts/gen_favicon_ico.py
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

PAPER = (251, 247, 240)   # --paper #FBF7F0
TEAL  = (14, 124, 114)    # --teal  #0E7C72

S = 256        # 고해상도로 그린 뒤 축소 → 16px에서도 글리프 품질 유지
RADIUS = 54    # apple-touch-icon 비율(38/180) 근사

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# 둥근 사각 배경 (워터틸)
d.rounded_rectangle([(0, 0), (S, S)], radius=RADIUS, fill=TEAL)

try:
    f = ImageFont.truetype("C:/Windows/Fonts/batang.ttc", 185)
except OSError:
    f = ImageFont.load_default()

bbox = d.textbbox((0, 0), "?", font=f)
w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
d.text(((S - w) / 2 - 3, (S - h) / 2 - 28), "?", font=f, fill=PAPER)

# cwd 무관하게 레포 루트 기준으로 저장
out = Path(__file__).resolve().parents[1] / "public" / "favicon.ico"
img.save(out, "ICO", sizes=[(16, 16), (32, 32), (48, 48)])
print(f"wrote {out} ({out.stat().st_size} bytes, sizes 16/32/48)")
