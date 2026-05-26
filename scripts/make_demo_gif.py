#!/usr/bin/env python3
"""Generate assets/demo/demo.gif — terminal-style demo animation."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Install Pillow: pip install pillow", file=sys.stderr)
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "demo" / "demo.gif"

# Brand palette
BG = (15, 23, 42)          # #0F172A
PANEL = (2, 6, 23)         # #020617
BORDER = (51, 65, 85)      # #334155
CYAN = (34, 211, 238)      # #22D3EE
MINT = (0, 212, 170)       # #00D4AA
WHITE = (248, 250, 252)
MUTED = (148, 163, 184)
RED = (239, 68, 68)
AMBER = (245, 158, 11)
GREEN = (34, 197, 94)

W, H = 720, 400
FRAMES: list[tuple[str, list[tuple[str, tuple[int, int, int], bool]]]] = [
    (
        "$ gitkey",
        [
            ("Available SSH profiles:", MUTED, False),
            ("  1) personal  (folder: personal)", WHITE, False),
            ("  2) clientA   (folder: clientA)", WHITE, False),
            ("", WHITE, False),
            ("Select profile: 1", CYAN, True),
        ],
    ),
    (
        "$ gitkey -p personal",
        [
            ("✓ Active SSH profile: personal", MINT, False),
            ("✓ Git user.name → Your Name", MINT, False),
            ("✓ Git user.email → you@example.com", MINT, False),
        ],
    ),
    (
        "$ cd ~/work/client-repo",
        [
            ("$ gitkey --bind -p clientA", CYAN, False),
            ("🔗 Bound 'clientA' → ~/work/client-repo", MINT, False),
            ("   Global default key was not changed.", MUTED, False),
        ],
    ),
    (
        "$ git push",
        [
            ("Enumerating objects…", MUTED, False),
            ("Writing objects: 100%", MINT, False),
            ("To github.com:client/project.git", WHITE, False),
            ("   abc1234..def5678  main -> main", GREEN, False),
        ],
    ),
]


def load_font(size: int, mono: bool = True) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = []
    if mono:
        candidates = [
            "/System/Library/Fonts/SFNSMono.ttf",
            "/System/Library/Fonts/Menlo.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "C:\\Windows\\Fonts\\consola.ttf",
        ]
    else:
        candidates = [
            "/System/Library/Fonts/SFNS.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    for path in candidates:
        p = Path(path)
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size=size)
            except OSError:
                continue
    return ImageFont.load_default()


def draw_frame(title: str, lines: list[tuple[str, tuple[int, int, int], bool]]) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    font_title = load_font(22, mono=False)
    font_mono = load_font(15, mono=True)
    font_mono_bold = load_font(15, mono=True)

    # outer glow bar
    draw.rounded_rectangle((24, 24, W - 24, H - 24), radius=14, fill=PANEL, outline=BORDER, width=2)

    # traffic lights
    for i, color in enumerate((RED, AMBER, GREEN)):
        draw.ellipse((48 + i * 22, 44, 58 + i * 22, 54), fill=color)

    draw.text((48, 72), "gitkey demo", font=font_title, fill=WHITE)

    # command line
    draw.text((48, 108), title, font=font_mono_bold, fill=CYAN)

    y = 148
    for text, color, cursor in lines:
        if not text:
            y += 8
            continue
        draw.text((48, y), text, font=font_mono, fill=color)
        if cursor:
            bx = 48 + font_mono.getlength(text) + 6
            draw.rectangle((bx, y + 2, bx + 8, y + 16), fill=CYAN)
        y += 28

    # watermark
    draw.text((48, H - 52), "github.com/geovanent/gitkey", font=load_font(12, mono=False), fill=MUTED)

    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    images = [draw_frame(title, lines) for title, lines in FRAMES]
    # hold last frame longer
    images = images + [images[-1]] * 2

    images[0].save(
        OUT,
        save_all=True,
        append_images=images[1:],
        duration=1800,
        loop=0,
        optimize=True,
    )
    print(f"✓ Wrote {OUT} ({OUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
