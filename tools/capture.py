"""Capture staged meals: raw color + depth + scale grams, one state at a time.

One meal: full plate (s0) -> remove some of ONE food -> s1 -> ... -> s4 -> empty plate.
At each state: weigh the plate, type grams (g), type which food changed (f), take 3 shots
(space), nudging the plate between shots. Files are raw (never resized or warped), so the
calibration can be redone later without reshooting.

    .venv/Scripts/python tools/capture.py            (camera)
    .venv/Scripts/python tools/capture.py --fake     (synthetic frames, no camera)

Keys: n new meal | g grams | f food changed | space shot | right/left next/prev state
      e empty plate | q quit        (while typing: Enter = ok, Esc = cancel)
Saves data/raw/<meal>/<state>_<shot>_color.png, _depth.png (16-bit mm, 0 = hole),
and one row per shot in data/raw/log.csv.
"""
import argparse
import csv
import json
import os
import re
import time
from datetime import datetime

import cv2
import numpy as np

from preview import colorize, open_color, open_depth

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CALIB = os.path.join(ROOT, "calib", "depth_to_color.json")
STATES = ["s0", "s1", "s2", "s3", "s4", "empty"]
SHOTS_PER_STATE = 3
DEPTH_FRAMES = 10   # averaged per shot to cut noise
W, H = 640, 480     # display size only; files keep native size
KEY_RIGHT, KEY_LEFT = 2555904, 2424832  # cv2.waitKeyEx codes on Windows
LOG_FIELDS = ["time", "meal", "state", "shot", "grams", "food_changed", "color_file",
              "depth_file", "color_size", "depth_size", "holes_pct", "center_mm",
              "camera_lock", "calib_created"]


class Camera:
    """Orbbec color (DirectShow) + depth (OpenNI). Exits with a clear message if busy."""

    def __init__(self, lock=True):
        from openni import openni2
        self.openni2 = openni2
        try:
            self.depth = open_depth()
        except Exception as ex:
            raise SystemExit(f"depth camera not available ({ex}). Plugged in? "
                             "Close preview/measure/calibrate first.")
        if openni2.wait_for_any_stream([self.depth], 2.0) is None:
            raise SystemExit("depth camera gave no frame in 2 s - replug it")
        self.cap = open_color()
        for _ in range(30):  # also lets auto exposure settle before locking
            ok, _ = self.cap.read()
        if not ok:
            raise SystemExit("color camera gave no frame - is another program using it?")
        self.lock = self._lock_exposure() if lock else "off"

    def _lock_exposure(self):
        """Freeze exposure + white balance at their settled values, so shots match."""
        exp, wb = self.cap.get(cv2.CAP_PROP_EXPOSURE), self.cap.get(cv2.CAP_PROP_WB_TEMPERATURE)
        ok_e = self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25) and self.cap.set(cv2.CAP_PROP_EXPOSURE, exp)
        ok_w = self.cap.set(cv2.CAP_PROP_AUTO_WB, 0) and self.cap.set(cv2.CAP_PROP_WB_TEMPERATURE, wb)
        return f"exposure {'locked' if ok_e else 'auto'} {exp:g}, wb {'locked' if ok_w else 'auto'} {wb:g}"

    def color(self):
        ok, img = self.cap.read()
        return img if ok else None

    def depth_frame(self):
        if self.openni2.wait_for_any_stream([self.depth], 0.5) is None:
            return None
        f = self.depth.read_frame()
        return np.frombuffer(f.get_buffer_as_uint16(), np.uint16).reshape(f.height, f.width).copy()

    def close(self):
        self.cap.release()
        self.depth.stop()
        self.openni2.unload()


class FakeCamera:
    """Synthetic plate with food piles, for testing without the camera."""
    lock = "fake"

    def __init__(self):
        self.rng = np.random.default_rng(0)

    def color(self):
        img = np.full((H, W, 3), 90, np.uint8)
        cv2.circle(img, (320, 240), 200, (230, 230, 230), -1)
        cv2.circle(img, (250, 200), 60, (60, 120, 200), -1)
        cv2.circle(img, (390, 280), 50, (240, 240, 245), -1)
        return img

    def depth_frame(self):
        z = np.full((H, W), 375.0)
        yy, xx = np.mgrid[:H, :W]
        z[np.hypot(xx - 320, yy - 240) < 200] = 365
        for cx, cy, r, h in [(250, 200, 60, 30), (390, 280, 50, 20)]:
            d = np.hypot(xx - cx, yy - cy)
            z = np.where(d < r, z - h * (1 - (d / r) ** 2), z)
        z += self.rng.normal(0, 1.5, z.shape)
        z[self.rng.random(z.shape) < 0.02] = 0
        return z.astype(np.uint16)

    def close(self):
        pass


def next_meal_id(out):
    nums = [int(m.group(1)) for d in os.listdir(out) if (m := re.fullmatch(r"meal_(\d+)", d))] \
        if os.path.isdir(out) else []
    return f"meal_{max(nums, default=0) + 1:02d}"


def shots_taken(meal_dir, state):
    if not os.path.isdir(meal_dir):
        return []
    return sorted(int(m.group(1)) for f in os.listdir(meal_dir)
                  if (m := re.fullmatch(rf"{state}_(\d+)_color\.png", f)))


def average_depth(frames):
    """Mean of the valid (non-zero) readings per pixel; 0 where no frame had a reading."""
    stack = np.stack(frames).astype(np.float32)
    valid = stack > 0
    mean = stack.sum(0) / np.maximum(valid.sum(0), 1)
    return np.where(valid.any(0), np.round(mean), 0).astype(np.uint16)


def calib_created():
    try:
        with open(CALIB) as fh:
            return json.load(fh)["created"]
    except (OSError, KeyError, ValueError):
        return ""


def save_shot(out, meal, state, grams, food, cam):
    """Grab a fresh color frame + averaged depth, write files and a log row. Never overwrites."""
    frames = [z for z in (cam.depth_frame() for _ in range(DEPTH_FRAMES + 3)) if z is not None][3:]
    if len(frames) < DEPTH_FRAMES // 2:
        return None, "depth frames missing - shot not saved"
    for _ in range(3):  # flush stale webcam frames
        color = cam.color()
    if color is None:
        return None, "no color frame - shot not saved"
    z = average_depth(frames)

    meal_dir = os.path.join(out, meal)
    os.makedirs(meal_dir, exist_ok=True)
    shot = max(shots_taken(meal_dir, state), default=0) + 1
    stem = os.path.join(meal_dir, f"{state}_{shot}")
    if not (cv2.imwrite(stem + "_color.png", color) and cv2.imwrite(stem + "_depth.png", z)):
        return None, "could not write files - shot not saved"

    cy, cx = z.shape[0] // 2, z.shape[1] // 2
    center = z[cy - 30:cy + 30, cx - 30:cx + 30]
    row = {
        "time": datetime.now().isoformat(timespec="seconds"), "meal": meal, "state": state,
        "shot": shot, "grams": grams, "food_changed": food,
        "color_file": f"{meal}/{state}_{shot}_color.png", "depth_file": f"{meal}/{state}_{shot}_depth.png",
        "color_size": f"{color.shape[1]}x{color.shape[0]}", "depth_size": f"{z.shape[1]}x{z.shape[0]}",
        "holes_pct": f"{100 * (z == 0).mean():.1f}",
        "center_mm": int(np.median(center[center > 0])) if (center > 0).any() else 0,
        "camera_lock": cam.lock, "calib_created": calib_created(),
    }
    log = os.path.join(out, "log.csv")
    new = not os.path.exists(log)
    with open(log, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LOG_FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    return row, f"saved {state}_{shot}  ({row['holes_pct']}% holes)"


class Session:
    """What meal/state we are on, what has been typed, and key handling."""

    def __init__(self, out, cam, meal=None):
        self.out, self.cam = out, cam
        self.meal, self.state_i = meal, 0
        self.grams, self.food = "", ""
        self.typing, self.buf = None, ""   # typing: None | "grams" | "food"
        self.msg, self.msg_t = "press n to start a new meal", time.time()

    @property
    def state(self):
        return STATES[self.state_i]

    def say(self, msg):
        self.msg, self.msg_t = msg, time.time()
        print(msg)

    def set_state(self, i):
        self.state_i = max(0, min(len(STATES) - 1, i))
        self.grams, self.food = "", ""

    def handle(self, key):
        """Returns False to quit."""
        if self.typing:
            ch = key & 0xFF if key < 256 else -1
            if ch == 13:  # Enter
                text = self.buf.strip()
                if self.typing == "grams":
                    try:
                        text = f"{float(text):g}"
                    except ValueError:
                        self.typing = None
                        return self.say(f"'{text}' is not a number - press g again") or True
                setattr(self, self.typing, text)
                self.say(f"{self.typing} = {text or '(blank)'}")
                self.typing = None
            elif ch == 27:  # Esc
                self.typing = None
            elif ch == 8:
                self.buf = self.buf[:-1]
            elif ch > 0:
                allowed = "0123456789." if self.typing == "grams" else " -_,"
                if chr(ch) in allowed or (self.typing == "food" and chr(ch).isalnum()):
                    self.buf += chr(ch)
            return True

        if key == ord("q"):
            return False
        if key == ord("n"):
            self.meal = next_meal_id(self.out)
            self.set_state(0)
            self.say(f"new meal {self.meal}: weigh the full plate, press g")
        elif key in (ord("g"), ord("f")):
            self.typing = "grams" if key == ord("g") else "food"
            self.buf = ""
        elif key in (KEY_RIGHT, ord("]")):
            n = len(shots_taken(os.path.join(self.out, self.meal), self.state)) if self.meal else 0
            short = f"(only {n}/{SHOTS_PER_STATE} shots of {self.state}) " if n < SHOTS_PER_STATE else ""
            self.set_state(self.state_i + 1)
            self.say(f"{short}state {self.state}: change ONE food, weigh, press g")
        elif key in (KEY_LEFT, ord("[")):
            self.set_state(self.state_i - 1)
        elif key == ord("e"):
            self.set_state(STATES.index("empty"))
            self.say("empty plate: weigh it, press g")
        elif key == ord(" "):
            self.shoot()
        return True

    def shoot(self):
        if not self.meal:
            return self.say("no meal yet - press n")
        if not self.grams:
            return self.say("type the scale grams first - press g")
        if self.state not in ("s0", "empty") and not self.food:
            return self.say("which food changed? press f")
        _, msg = save_shot(self.out, self.meal, self.state, self.grams, self.food, self.cam)
        self.say(msg)

    def hud(self, color, z):
        left = cv2.resize(color, (W, H)) if color is not None else np.zeros((H, W, 3), np.uint8)
        right = cv2.resize(colorize(z), (W, H), interpolation=cv2.INTER_NEAREST) if z is not None \
            else np.zeros((H, W, 3), np.uint8)
        bar = np.zeros((90, 2 * W, 3), np.uint8)
        n = len(shots_taken(os.path.join(self.out, self.meal), self.state)) if self.meal else 0
        done = (0, 255, 0) if n >= SHOTS_PER_STATE else (255, 255, 255)
        line1 = (f"{self.meal or '-'} | state {self.state} | shots {n}/{SHOTS_PER_STATE} | "
                 f"grams {self.grams or '?'} | changed: {self.food or ('-' if self.state in ('s0', 'empty') else '?')}")
        if self.typing:
            line2 = f"type {self.typing}: {self.buf}_   (Enter = ok, Esc = cancel)"
        else:
            line2 = self.msg if time.time() - self.msg_t < 6 else \
                "n new meal | g grams | f food changed | space shot | -> next state | e empty | q quit"
        cv2.putText(bar, line1, (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.7, done, 2)
        cv2.putText(bar, line2, (10, 72), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        return np.vstack([np.hstack([left, right]), bar])


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fake", action="store_true", help="synthetic frames, no camera")
    ap.add_argument("--out", default=os.path.join(ROOT, "data", "raw"))
    ap.add_argument("--meal", help="continue an existing meal, e.g. meal_03")
    ap.add_argument("--no-lock", action="store_true", help="leave exposure/white balance on auto")
    args = ap.parse_args()

    cam = FakeCamera() if args.fake else Camera(lock=not args.no_lock)
    print("camera:", cam.lock)
    s = Session(os.path.abspath(args.out), cam, args.meal)
    win = "Intake.ai capture"
    try:
        while True:
            cv2.imshow(win, s.hud(cam.color(), cam.depth_frame()))
            key = cv2.waitKeyEx(30)
            if key != -1 and not s.handle(key):
                break
    finally:
        cam.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
