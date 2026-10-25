"""Measure height and volume of an object with the Orbbec depth camera.

Drag a box around an object on the DEPTH side (right). The surface just outside the box
(plate or table) is the base. Height = base - object top. Volume = height x pixel area,
summed over the pixels that stand above the base.

Also shows noise: how much the reading at the cross jumps over the last ~1 s.

    .venv/Scripts/python tools/measure.py      (q = quit, c = clear box)
"""
import math
from collections import deque

import cv2
import numpy as np

from preview import colorize, open_color, open_depth

W, H = 640, 480
MIN_HEIGHT_MM = 3   # ignore pixels closer than this to the base (noise floor)
BORDER_PX = 12      # width of the ring around the box used as the base


class Box:
    def __init__(self):
        self.start = self.end = None
        self.dragging = False

    def on_mouse(self, event, x, y, *_):
        x -= W  # depth panel is the right half
        if x < 0:
            return
        if event == cv2.EVENT_LBUTTONDOWN:
            self.start, self.end, self.dragging = (x, y), (x, y), True
        elif event == cv2.EVENT_MOUSEMOVE and self.dragging:
            self.end = (x, y)
        elif event == cv2.EVENT_LBUTTONUP:
            self.end, self.dragging = (x, y), False

    def rect(self):
        if not self.start or not self.end:
            return None
        (x0, y0), (x1, y1) = self.start, self.end
        x0, x1 = sorted((max(0, x0), min(W - 1, x1)))
        y0, y1 = sorted((max(0, y0), min(H - 1, y1)))
        return (x0, y0, x1, y1) if x1 - x0 > 4 and y1 - y0 > 4 else None


def measure(z, rect, hfov, vfov):
    """Height (mm) and volume (cm^3) of what stands above the ring around rect."""
    x0, y0, x1, y1 = rect
    outer = z[max(0, y0 - BORDER_PX):y1 + BORDER_PX, max(0, x0 - BORDER_PX):x1 + BORDER_PX]
    inner = z[y0:y1, x0:x1].astype(np.float64)
    ring = outer.astype(np.float64).copy()
    oy, ox = min(BORDER_PX, y0), min(BORDER_PX, x0)
    ring[oy:oy + inner.shape[0], ox:ox + inner.shape[1]] = 0  # keep only the ring
    ring = ring[ring > 0]
    if ring.size < 20:
        return None
    base = np.median(ring)

    valid = inner > 0
    heights = np.where(valid, base - inner, 0)
    above = heights > MIN_HEIGHT_MM
    # each pixel covers (distance * 2 tan(fov/2) / pixels) mm on each side
    px_w = inner * 2 * math.tan(hfov / 2) / W
    px_h = inner * 2 * math.tan(vfov / 2) / H
    volume_cm3 = float(np.sum(heights[above] * px_w[above] * px_h[above])) / 1000
    return {
        "base_mm": base,
        "max_mm": float(np.percentile(heights[above], 95)) if above.any() else 0.0,
        "median_mm": float(np.median(heights[above])) if above.any() else 0.0,
        "volume_cm3": volume_cm3,
        "holes_pct": 100 * (1 - valid.mean()),
    }


def main():
    cap, depth = open_color(), open_depth()
    hfov, vfov = depth.get_horizontal_fov(), depth.get_vertical_fov()
    print("depth FOV: %.1f x %.1f deg" % (math.degrees(hfov), math.degrees(vfov)))
    box, history = Box(), deque(maxlen=30)
    win = "Plate Check measure  (drag box on depth | c = clear | q = quit)"
    cv2.namedWindow(win)
    cv2.setMouseCallback(win, box.on_mouse)

    while True:
        ok, color = cap.read()
        f = depth.read_frame()
        z = np.frombuffer(f.get_buffer_as_uint16(), dtype=np.uint16).reshape(f.height, f.width)
        z = cv2.resize(z, (W, H), interpolation=cv2.INTER_NEAREST)
        color = cv2.resize(color, (W, H)) if ok else np.zeros((H, W, 3), np.uint8)
        dimg = colorize(z)

        center = z[H // 2 - 30:H // 2 + 30, W // 2 - 30:W // 2 + 30]
        if (center > 0).any():
            history.append(float(np.median(center[center > 0])))
        noise = (max(history) - min(history)) / 2 if len(history) > 5 else 0
        center_mm = history[-1] if history else 0
        cv2.drawMarker(dimg, (W // 2, H // 2), (255, 255, 255), cv2.MARKER_CROSS, 20, 2)
        cv2.putText(dimg, f"center {center_mm:.0f} mm  noise +/-{noise:.1f} mm", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        rect = box.rect()
        if rect:
            cv2.rectangle(dimg, rect[:2], rect[2:], (255, 255, 255), 2)
            m = measure(z, rect, hfov, vfov)
            lines = ["base not visible - widen box"] if m is None else [
                f"height max {m['max_mm']:.1f} mm  median {m['median_mm']:.1f} mm",
                f"volume {m['volume_cm3']:.1f} cm3   base {m['base_mm']:.0f} mm",
                f"holes {m['holes_pct']:.0f}%",
            ]
            for i, line in enumerate(lines):
                cv2.putText(dimg, line, (10, H - 70 + 25 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            (255, 255, 255), 2)

        cv2.imshow(win, np.hstack([color, dimg]))
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("c"):
            box.start = box.end = None
    cap.release()
    depth.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
