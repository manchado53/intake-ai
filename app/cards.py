"""Printable QR cards: the QR holds only the resident id; name + room are printed under it."""
import io

import qrcode
from PIL import Image, ImageDraw, ImageFont

CARD_W, CARD_H = 600, 760


def _font(size: int):
    for name in ("arialbd.ttf", "arial.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def card(resident: dict) -> Image.Image:
    qr = qrcode.QRCode(border=2, box_size=10, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(resident["id"])
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB").resize((500, 500), Image.NEAREST)
    img = Image.new("RGB", (CARD_W, CARD_H), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([2, 2, CARD_W - 3, CARD_H - 3], outline="#999999", width=3)
    img.paste(qr_img, (50, 40))
    d.text((CARD_W // 2, 600), resident["name"], fill="black", font=_font(56), anchor="mm")
    d.text((CARD_W // 2, 670), f"Room {resident['room']}  ·  {resident['id']}", fill="#444444",
           font=_font(36), anchor="mm")
    return img


def sheet(residents: list[dict], cols: int = 2) -> Image.Image:
    rows = (len(residents) + cols - 1) // cols
    gap = 40
    out = Image.new("RGB", (cols * CARD_W + (cols + 1) * gap, rows * CARD_H + (rows + 1) * gap), "white")
    for i, r in enumerate(residents):
        x = gap + (i % cols) * (CARD_W + gap)
        y = gap + (i // cols) * (CARD_H + gap)
        out.paste(card(r), (x, y))
    return out


def to_bytes(img: Image.Image, fmt: str) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt, **({"resolution": 150.0} if fmt == "PDF" else {}))
    return buf.getvalue()
