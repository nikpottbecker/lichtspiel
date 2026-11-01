"""Regenerate the bundled 1920 × 1080 projector test card (requires Pillow)."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1920, 1080
BACKGROUND = "#101112"
WHITE = "#f3f1eb"
MUTED = "#a9adae"
ACCENT = "#d6a56a"
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "electron" / "assets" / "projection-test.png"

image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
draw = ImageDraw.Draw(image)


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(name, size)


def center(text, y, size, color=WHITE, bold=False):
    face = font(size, bold)
    box = draw.textbbox((0, 0), text, font=face)
    draw.text(((WIDTH - (box[2] - box[0])) / 2, y), text, fill=color, font=face)


# The outer and inner frames reveal overscan, cropping, and focus falloff.
draw.rectangle((24, 24, WIDTH - 25, HEIGHT - 25), outline=WHITE, width=2)
draw.rectangle((72, 72, WIDTH - 73, HEIGHT - 73), outline="#666b6d", width=1)
for x in range(120, WIDTH, 120):
    draw.line((x, 72, x, HEIGHT - 73), fill="#292d2e", width=1)
for y in range(120, HEIGHT, 120):
    draw.line((72, y, WIDTH - 73, y), fill="#292d2e", width=1)

for x, y in ((24, 24), (WIDTH - 25, 24), (24, HEIGHT - 25), (WIDTH - 25, HEIGHT - 25)):
    draw.ellipse((x - 9, y - 9, x + 9, y + 9), fill=ACCENT)

center("LICHTSPIEL", 122, 52, WHITE, True)
center("LEINWANDTEST  ·  1920 × 1080  ·  16:9", 198, 26, MUTED)
center("Sind alle vier Ecken und der äußere Rahmen sichtbar?", 261, 28)

draw.ellipse((730, 340, 1190, 800), outline=WHITE, width=3)
draw.ellipse((820, 430, 1100, 710), outline="#808688", width=2)
draw.line((960, 330, 960, 810), fill=ACCENT, width=2)
draw.line((720, 570, 1200, 570), fill=ACCENT, width=2)
draw.ellipse((950, 560, 970, 580), fill=WHITE)

# One-pixel and two-pixel alternating lines make blur and scaling apparent.
for x in range(172, 432, 2):
    draw.line((x, 388, x, 604), fill=WHITE, width=1)
for x in range(1488, 1748, 4):
    draw.rectangle((x, 388, x + 1, 604), fill=WHITE)
center("Schärfe · Geometrie · Ausschnitt", 846, 28)

colors = ["#ffffff", "#ffff00", "#00ffff", "#00ff00", "#ff00ff", "#ff0000", "#0000ff"]
bar_left, bar_right, top, bottom = 196, 1724, 906, 948
bar_width = (bar_right - bar_left) / len(colors)
for index, color in enumerate(colors):
    draw.rectangle(
        (round(bar_left + index * bar_width), top, round(bar_left + (index + 1) * bar_width) - 1, bottom),
        fill=color,
    )
for index in range(11):
    shade = round(index * 255 / 10)
    left = round(bar_left + index * (bar_right - bar_left) / 11)
    right = round(bar_left + (index + 1) * (bar_right - bar_left) / 11) - 1
    draw.rectangle((left, 958, right, 984), fill=(shade, shade, shade))

center("Test endet nach 12 Sekunden  ·  Kein Ton", 1006, 20, MUTED)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
image.save(OUTPUT, optimize=True)
print(OUTPUT)
