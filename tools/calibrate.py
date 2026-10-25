"""One-time depth -> color calibration for the Orbbec DaBai DCW.

Depth sees a wider view than color, so the same plate sits in different pixels.
Click the SAME physical point in both views (color left, depth right), 6+ pairs spread
over the whole plate area: corners of small light, matte boxes work best.
A homography (a plane-to-plane stretch + shift) is fit from depth pixels to color pixels.

    .venv/Scripts/python tools/calibrate.py

Keys: click color point, then depth point (repeat) | u undo | r new frames
      f fit + show overlay | s save calib/depth_to_color.json | q quit
"""
import json
import os
from datetime import datetime

import cv2
import numpy as np

from preview import open_color, open_depth

W, H = 640, 480
OUT = os.path.join(os.path.dirname(__file__), "..", "calib", "depth_to_color.json")


def grab(cap, depth, n=10):
    """Color frame + depth averaged over n frames (holes ignored)."""
    frames = []
    for _ in range(n + 3):
        f = depth.read_frame()
        frames.append(np.frombuffer(f.get_buffer_as_uint16(), np.uint16).reshape(f.height, f.width))
    stack = np.stack(frames[3:]).astype(np.float32)
    valid = stack > 0
    z = np.where(valid.any(0), stack.sum(0) / np.maximum(valid.sum(0), 1), 0)
    for _ in range(5):  # flush stale webcam frames
        ok, color = cap.read()
    if not ok:
        raise SystemExit("color camera gave no frame")
    return cv2.resize(color, (W, H)), z


def show_depth(z):
    """Color map stretched around the table level, so a few mm of height shows up."""
    base = np.median(z[z > 0])
    near, far = base - 60, base + 5
    scaled = (255 * (np.clip(z, near, far) - near) / (far - near)).astype(np.uint8)
    img = cv2.applyColorMap(255 - scaled, cv2.COLORMAP_JET)
    img[z == 0] = 0
    return cv2.resize(img, (W, H), interpolation=cv2.INTER_NEAREST)


def depth_edges(z):
    zs = cv2.medianBlur(z.astype(np.float32), 5)
    g = np.hypot(cv2.Sobel(zs, cv2.CV_32F, 1, 0, 3), cv2.Sobel(zs, cv2.CV_32F, 0, 1, 3))
    return ((g > 60) & (z > 0)).astype(np.uint8) * 255


def fit(color_pts, depth_pts):
    src, dst = np.float32(depth_pts), np.float32(color_pts)
    method = cv2.RANSAC if len(src) >= 6 else 0
    hom, inliers = cv2.findHomography(src, dst, method, 4.0)
    if hom is None:
        return None, None
    err = np.linalg.norm(cv2.perspectiveTransform(src[None], hom)[0] - dst, axis=1)
    return hom, err


def main():
    cap, depth = open_color(), open_depth()
    color, z = grab(cap, depth)
    sx, sy = z.shape[1] / W, z.shape[0] / H  # depth panel is resized to W x H
    color_pts, depth_pts = [], []
    hom, err = None, None

    def on_mouse(event, x, y, *_):
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        if x < W and len(color_pts) == len(depth_pts):
            color_pts.append((x, y))
        elif x >= W and len(depth_pts) == len(color_pts) - 1:
            depth_pts.append(((x - W) * sx, y * sy))

    win = "Calibrate depth -> color  (click color, then depth | f fit | s save | q quit)"
    cv2.namedWindow(win)
    cv2.setMouseCallback(win, on_mouse)
    dimg = show_depth(z)
    while True:
        left, right = color.copy(), dimg.copy()
        if hom is not None:  # warped depth edges on color: should sit on the real edges
            warped = cv2.warpPerspective(depth_edges(z), hom, (W, H), flags=cv2.INTER_NEAREST)
            left[warped > 0] = (0, 0, 255)
        for i, (cx, cy) in enumerate(color_pts):
            cv2.drawMarker(left, (int(cx), int(cy)), (0, 255, 0), cv2.MARKER_CROSS, 14, 2)
            cv2.putText(left, str(i + 1), (int(cx) + 6, int(cy) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        for i, (dx, dy) in enumerate(depth_pts):
            p = (int(dx / sx), int(dy / sy))
            cv2.drawMarker(right, p, (255, 255, 255), cv2.MARKER_CROSS, 14, 2)
            cv2.putText(right, str(i + 1), (p[0] + 6, p[1] - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        status = f"pairs {len(depth_pts)}"
        if len(color_pts) > len(depth_pts):
            status += "  -> now click point %d on DEPTH" % len(color_pts)
        if err is not None:
            status += f"  | error mean {err.mean():.1f}px max {err.max():.1f}px"
        cv2.putText(left, status, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.imshow(win, np.hstack([left, right]))

        key = cv2.waitKey(30) & 0xFF
        if key == ord("q"):
            break
        if key == ord("u"):
            if len(color_pts) > len(depth_pts):
                color_pts.pop()
            elif depth_pts:
                color_pts.pop()
                depth_pts.pop()
            hom = err = None
        elif key == ord("r"):
            color, z = grab(cap, depth)
            dimg = show_depth(z)
        elif key == ord("f"):
            if len(depth_pts) < 4:
                print("need 4+ pairs, have", len(depth_pts))
                continue
            hom, err = fit(color_pts[:len(depth_pts)], depth_pts)
            if hom is not None:
                print("per-point error px:", np.round(err, 1).tolist())
        elif key == ord("s") and hom is not None:
            os.makedirs(os.path.dirname(OUT), exist_ok=True)
            with open(OUT, "w") as fh:
                json.dump({
                    "created": datetime.now().isoformat(timespec="seconds"),
                    "homography_depth_to_color": hom.tolist(),
                    "depth_size": [z.shape[1], z.shape[0]],
                    "color_size": [W, H],
                    "pairs": [{"color": list(c), "depth": list(d)}
                              for c, d in zip(color_pts, depth_pts)],
                    "error_px": {"mean": float(err.mean()), "max": float(err.max())},
                }, fh, indent=2)
            print("saved", os.path.abspath(OUT))
    cap.release()
    depth.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
