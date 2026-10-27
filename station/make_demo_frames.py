"""Build a folder of station test frames: meal_03 photos with a resident QR card pasted on.

    .venv-app/Scripts/python station/make_demo_frames.py [--src data/raw/meal_03] [--out data/raw/test_station]

Writes 01_R01_s0.png (before), 02_noqr_s4.png (no card), 03_R01_s4.png (after),
04_R01_s9.png (after, plate cleared). Also writes card_R01.png to print.
"""
import argparse
import os

import cv2
import numpy as np
import qrcode

from workflow_client import MAIN_ROOT, read_qr


def qr_card(text, size=150):
    """White card with a QR code, as a BGR image."""
    q = qrcode.QRCode(border=2, box_size=10)
    q.add_data(text)
    q.make(fit=True)
    img = np.array(q.make_image(fill_color="black", back_color="white").convert("L"))
    img = cv2.resize(img, (size, size), interpolation=cv2.INTER_NEAREST)
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)


def paste(frame, card, x=4, y=300):
    out = frame.copy()
    h, w = card.shape[:2]
    out[y:y + h, x:x + w] = card
    return out


def main():
    data = os.path.join(MAIN_ROOT, "data", "raw")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", default=os.path.join(data, "meal_03"))
    ap.add_argument("--out", default=os.path.join(data, "test_station"))
    ap.add_argument("--resident", default="R01")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    card = qr_card(args.resident)
    cv2.imwrite(os.path.join(args.out, f"card_{args.resident}.png"), qr_card(args.resident, 600))
    plan = [("01_{r}_s0.png", "s0_1", True), ("02_noqr_s4.png", "s4_2", False),
            ("03_{r}_s4.png", "s4_1", True), ("04_{r}_s9.png", "s9_1", True)]
    for name, src, with_card in plan:
        frame = cv2.imread(os.path.join(args.src, f"{src}_color.png"))
        if frame is None:
            raise SystemExit(f"missing {src}_color.png in {args.src}")
        if with_card:
            frame = paste(frame, card)
        path = os.path.join(args.out, name.format(r=args.resident))
        cv2.imwrite(path, frame)
        print(f"{os.path.basename(path)}: qr={read_qr(frame)}")


if __name__ == "__main__":
    main()
