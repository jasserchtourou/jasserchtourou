"""Turn assets/source-prepped.png into an animated ASCII-art SVG (ascii-portrait.svg).

Background (flood-filled from the borders) becomes blank; inside the subject,
brightness maps to character density so it reads correctly on a dark terminal.
Each row is revealed by a clip-path wipe with a block cursor, staggered top to bottom.
"""
import os
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "source-prepped.png"
OUT = ROOT / "ascii-portrait.svg"
STATIC = os.environ.get("STATIC") == "1"

COLS = 100
MAX_ROWS = 56  # crop from the bottom so the face dominates
W, H = 370, 400
PAD_X, TOP = 15, 42
RAMP = " .'`^\",:;Il!i~+_-?][}{1)(|tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
TONES = ["#3d444d", "#6e7681", "#a5adb6", "#e6edf3"]  # shade buckets, dark -> light
ROW_DELAY, ROW_DUR = 0.045, 0.35


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def to_ascii() -> list[str]:
    img = cv2.imread(str(SRC))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # background mask: near-white region connected to the image border
    bg = (cv2.GaussianBlur(gray, (5, 5), 0) > 235).astype(np.uint8)
    flood = np.zeros((gray.shape[0] + 2, gray.shape[1] + 2), np.uint8)
    filled = bg.copy()
    h, w = gray.shape
    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0)]:
        if filled[seed[1], seed[0]] == 1:
            cv2.floodFill(filled, flood, seed, 2)
    subject = (filled != 2).astype(np.float32)

    # crop to subject bounding box (small margin), keep full bottom
    ys, xs = np.where(subject > 0)
    x0, x1 = max(xs.min() - 6, 0), min(xs.max() + 6, w)
    zoom = int((x1 - x0) * 0.12)  # trim shoulders so the face gets more characters
    x0, x1 = x0 + zoom, x1 - zoom
    y0 = max(ys.min() - 6, 0)
    gray, subject = gray[y0:, x0:x1], subject[y0:, x0:x1]

    cw = (W - 2 * PAD_X) / COLS
    lh = cw / 0.6
    rows = int(round(gray.shape[0] / gray.shape[1] * COLS * cw / lh))
    if rows > MAX_ROWS:
        keep = int(gray.shape[0] * MAX_ROWS / rows)
        gray, subject, rows = gray[:keep], subject[:keep], MAX_ROWS
    small = cv2.resize(gray, (COLS, rows), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    mask = cv2.resize(subject, (COLS, rows), interpolation=cv2.INTER_AREA)

    lines, tones = [], []
    n = len(RAMP) - 1
    for r in range(rows):
        chars, shade = [], []
        for c in range(COLS):
            if mask[r, c] < 0.5:
                chars.append(" ")
                shade.append(-1)
            else:
                # brighter -> denser and lighter; floor keeps the dark suit visible
                v = 0.18 + 0.82 * small[r, c] ** 0.9
                chars.append(RAMP[max(1, min(n, int(v * n)))])
                shade.append(min(len(TONES) - 1, int(small[r, c] * len(TONES))))
        lines.append("".join(chars))
        tones.append(shade)
    return lines, tones


def main() -> None:
    lines, tones = to_ascii()
    cw = (W - 2 * PAD_X) / COLS
    lh = cw / 0.6
    fs = cw / 0.6
    rows = len(lines)
    global H
    H = int(TOP + rows * lh + 18)
    full = W - 2 * PAD_X

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="{FONT}">',
        f'<rect width="{W}" height="{H}" rx="10" fill="#0d1117" stroke="#30363d"/>',
        f'<path d="M0 10a10 10 0 0 1 10-10h{W - 20}a10 10 0 0 1 10 10v20H0z" fill="#161b22"/>',
        f'<line x1="0" y1="30" x2="{W}" y2="30" stroke="#30363d"/>',
        '<circle cx="18" cy="15" r="5.5" fill="#ff5f56"/>'
        '<circle cx="36" cy="15" r="5.5" fill="#ffbd2e"/>'
        '<circle cx="54" cy="15" r="5.5" fill="#27c93f"/>',
        f'<text x="{W / 2}" y="19" text-anchor="middle" font-size="12" fill="#8b949e">'
        f"jasser@hannover: ~/whoami</text>",
    ]
    if not STATIC:
        out.append("<defs>")
        for i in range(rows):
            y = TOP + i * lh
            b = i * ROW_DELAY
            out.append(
                f'<clipPath id="r{i}"><rect x="{PAD_X}" y="{y:.2f}" width="0" height="{lh + 0.5:.2f}">'
                f'<animate attributeName="width" from="0" to="{full}" begin="{b:.3f}s" '
                f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
            )
        out.append("</defs>")

    # one text layer per shade bucket; NBSP keeps columns aligned (plain spaces collapse)
    out.append(f'<g font-size="{fs:.2f}">')
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        y = TOP + i * lh + lh * 0.8
        clip = "" if STATIC else f' clip-path="url(#r{i})"'
        out.append(f"<g{clip}>")
        for t, color in enumerate(TONES):
            layer = "".join(ch if tones[i][c] == t else " " for c, ch in enumerate(line)).rstrip(" ")
            if layer:
                out.append(
                    f'<text x="{PAD_X}" y="{y:.2f}" fill="{color}" textLength="{len(layer) * cw:.2f}" '
                    f'lengthAdjust="spacingAndGlyphs">{esc(layer)}</text>'
                )
        out.append("</g>")
    out.append("</g>")

    if not STATIC:
        # block cursor riding the wipe edge of each row
        for i in range(rows):
            y = TOP + i * lh
            b = i * ROW_DELAY
            out.append(
                f'<rect x="{PAD_X}" y="{y:.2f}" width="{cw * 1.4:.2f}" height="{lh:.2f}" '
                f'fill="#7ee787" opacity="0">'
                f'<animate attributeName="x" from="{PAD_X}" to="{PAD_X + full}" begin="{b:.3f}s" '
                f'dur="{ROW_DUR}s" fill="freeze"/>'
                f'<set attributeName="opacity" to="0.9" begin="{b:.3f}s" dur="{ROW_DUR}s"/></rect>'
            )
    out.append("</svg>")

    OUT.write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {OUT.name} ({COLS}x{rows} chars, {W}x{H}px)")


if __name__ == "__main__":
    main()
