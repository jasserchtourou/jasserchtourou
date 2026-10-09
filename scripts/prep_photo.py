"""Prepare the portrait: (optional) background removal + CLAHE contrast boost.

Input:  assets/source.jpg
Output: assets/source-prepped.png  (subject on pure white)

rembg is only used if installed; the current photo already has a white background.
"""
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "source.jpg"
OUT = ROOT / "assets" / "source-prepped.png"


def main() -> None:
    img = cv2.imread(str(SRC))
    try:
        from rembg import remove  # optional, heavy dependency

        rgba = remove(cv2.cvtColor(img, cv2.COLOR_BGR2RGBA))
        alpha = rgba[..., 3:4].astype(np.float32) / 255
        rgb = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR).astype(np.float32)
        img = (rgb * alpha + 255 * (1 - alpha)).astype(np.uint8)
        print("background removed with rembg")
    except ImportError:
        print("rembg not installed - keeping original background")

    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(6, 6)).apply(l)
    img = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)

    cv2.imwrite(str(OUT), img)
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
