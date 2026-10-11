"""앱 아이콘(PNG) 생성: docs/icon-192.png, icon-512.png, icon-maskable-512.png"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DOCS = Path(__file__).parent / "docs"
BG, ACCENT, INK = "#0f1419", "#f2b33d", "#1a1203"


def draw(size, maskable):
    img = Image.new("RGB", (size, size), BG)
    d = ImageDraw.Draw(img)
    s = size / 512
    scale = 0.78 if maskable else 1.0  # maskable은 안전 영역(가운데 80%) 안에만 그린다
    cx = cy = size / 2

    def p(x, y):  # 512 기준 좌표를 중심 기준으로 축소
        return (cx + (x - 256) * s * scale, cy + (y - 256) * s * scale)

    r = 150
    d.ellipse([*p(256 - r, 210 - r), *p(256 + r, 210 + r)], fill=ACCENT)
    d.polygon([p(215, 140), p(215, 280), p(330, 210)], fill=INK)
    font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", int(96 * s * scale))
    d.text(p(256, 430), "800", font=font, fill=ACCENT, anchor="mm")
    return img


DOCS.mkdir(exist_ok=True)
draw(192, False).save(DOCS / "icon-192.png")
draw(512, False).save(DOCS / "icon-512.png")
draw(512, True).save(DOCS / "icon-maskable-512.png")
print("icons ok")
