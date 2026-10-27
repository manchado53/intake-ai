"""Paste a generated QR card (resident id) onto an empty corner of a plate photo.

  .venv-app/Scripts/python workflow/make_test_image.py [--src data/raw/meal_03/s0_1_color.png]
                                                         [--text R01] [--out data/raw/test/...]

Paths are relative to the main checkout (data/ is gitignored). The card is a white square with a
quiet zone, placed bottom-right where meal_03 shows only countertop.
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
import qrcode

HERE = Path(__file__).resolve().parent


def main_checkout():
    for d in [HERE.parent, *HERE.parent.parents]:
        if (d / "data" / "raw").is_dir():
            return d
    return HERE.parent


def qr_card(text, size):
    qr = qrcode.QRCode(border=4, box_size=10, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(text)
    qr.make(fit=True)
    img = np.array(qr.make_image(fill_color="black", back_color="white").convert("L"))
    img = cv2.resize(img, (size, size), interpolation=cv2.INTER_NEAREST)
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)


def main():
    root = main_checkout()
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(root / "data/raw/meal_03/s0_1_color.png"))
    ap.add_argument("--text", default="R01")
    ap.add_argument("--size", type=int, default=116)
    ap.add_argument("--x", type=int, default=516, help="top-left x of the card")
    ap.add_argument("--y", type=int, default=240, help="top-left y of the card")
    ap.add_argument("--out", default=str(root / "data/raw/test/meal_03_s0_1_qr_R01.png"))
    a = ap.parse_args()

    img = cv2.imread(a.src)
    card = qr_card(a.text, a.size)
    img[a.y:a.y + a.size, a.x:a.x + a.size] = card
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(a.out, img)
    text, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
    print(f"wrote {a.out}; local decode = {text!r}")


if __name__ == "__main__":
    main()
