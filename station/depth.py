"""Depth for the station: food volume above the plate's real shape (same math as eval/depth_vs_area.py).

    cam = DepthCam.open()                  # OpenNI depth, or None (no driver / camera) -> area only
    z = cam.grab()                         # depth (mm, float32) warped onto the 640x480 color image
    plate, foods = masks(workflow_out, z.shape)            # from the Workflow's `plate` / `foods` outputs
    profile = plate_profile(z, plate, foods)              # EMPTY PLATE scan: the dish's depth vs radius
    vols = volumes(z, plate, foods, profile)              # {name: mm^3-ish} per menu item

A plate is a shallow dish (centre ~15 mm below the rim), so food height is measured from the
empty plate's own shape, lined up by the plate circle, not from a flat floor at rim level.
OpenNI libs: OPENNI2_LIBS, else ~/intake/openni/sdk/libs (Orin) or the Windows SDK in ~/Downloads.
"""
import ctypes
import json
import os

import cv2
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CALIB = os.path.join(ROOT, "calib", "depth_to_color.json")
SIZE = (640, 480)        # color image the masks live on
FRAMES = 10              # depth frames averaged per scan, to cut noise
BINS_R = np.linspace(0, 1.0, 26)
MAX_H = 120              # mm; taller = a reading error, not food
DEFAULT_LIBS = (os.path.expanduser("~/intake/openni/sdk/libs") if os.name != "nt" else os.path.expanduser(
    r"~\Downloads\orbbec_openni\sdk\OpenNI_2.3.0.86_202210111950_4c8f5aa4_beta6_windows\Win64-Release\sdk\libs"))


def homography():
    with open(CALIB) as fh:
        return np.array(json.load(fh)["homography_depth_to_color"])


def average_depth(frames):
    """Mean of the valid (non-zero) readings per pixel; 0 where no frame had a reading."""
    stack = np.stack(frames).astype(np.float32)
    valid = stack > 0
    return np.where(valid.any(0), stack.sum(0) / np.maximum(valid.sum(0), 1), 0).astype(np.float32)


def warp(z, h=None):
    """Raw depth -> color image coordinates (nearest, so holes stay 0)."""
    return cv2.warpPerspective(z, homography() if h is None else h, SIZE, flags=cv2.INTER_NEAREST)


class _Frame(ctypes.Structure):
    """Leading fields of OpenNI's OniFrame (OniCTypes.h); only these are read."""
    _fields_ = [("dataSize", ctypes.c_int), ("data", ctypes.c_void_p), ("sensorType", ctypes.c_int),
                ("timestamp", ctypes.c_uint64), ("frameIndex", ctypes.c_int),
                ("width", ctypes.c_int), ("height", ctypes.c_int)]


class DepthCam:
    """OpenNI depth stream, called straight through ctypes. The `openni` pip wrapper corrupts memory
    on the Orin (malloc crash within ~300 frames); these 8 C calls ran 3000 frames clean.
    Only the depth chip is opened, so the station keeps its color camera."""
    ONI_API, SENSOR_DEPTH, PROP_MIRRORING = 2003, 3, 7

    def __init__(self, libs=None):
        libs = libs or os.environ.get("OPENNI2_LIBS", DEFAULT_LIBS)
        if os.name == "nt":
            os.add_dll_directory(libs)
            os.add_dll_directory(os.path.join(libs, "OpenNI2", "Drivers"))
        cwd = os.getcwd()
        os.chdir(libs)  # OpenNI.ini finds its Drivers folder relative to here
        try:
            lib = ctypes.CDLL(os.path.join(libs, "OpenNI2.dll" if os.name == "nt" else "libOpenNI2.so"))
            self._check(lib.oniInitialize(self.ONI_API), "initialize")
        finally:
            os.chdir(cwd)
        lib.oniStreamReadFrame.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.POINTER(_Frame))]
        lib.oniFrameRelease.argtypes = [ctypes.POINTER(_Frame)]
        self.lib, self.dev, self.stream = lib, ctypes.c_void_p(), ctypes.c_void_p()
        self._check(lib.oniDeviceOpen(None, ctypes.byref(self.dev)), "open device (plugged in?)")
        self._check(lib.oniDeviceCreateStream(self.dev, self.SENSOR_DEPTH, ctypes.byref(self.stream)), "depth stream")
        off = ctypes.c_int(0)  # OpenNI mirrors by default; the color camera doesn't
        lib.oniStreamSetProperty(self.stream, self.PROP_MIRRORING, ctypes.byref(off), 4)
        self._check(lib.oniStreamStart(self.stream), "start")
        self.h = homography()

    @staticmethod
    def _check(rc, what):
        if rc != 0:
            raise RuntimeError(f"OpenNI {what} failed ({rc})")

    def _frame(self):
        idx = ctypes.c_int()
        if self.lib.oniWaitForAnyStream(ctypes.byref(self.stream), 1, ctypes.byref(idx), 500) != 0:
            return None
        fp = ctypes.POINTER(_Frame)()
        if self.lib.oniStreamReadFrame(self.stream, ctypes.byref(fp)) != 0:
            return None
        f = fp.contents
        z = np.ctypeslib.as_array(ctypes.cast(f.data, ctypes.POINTER(ctypes.c_uint16)), (f.height, f.width)).copy()
        self.lib.oniFrameRelease(fp)
        return z

    @classmethod
    def open(cls):
        """A DepthCam, or None (and why) when there's no driver or camera: the station stays area-only."""
        try:
            return cls()
        except Exception as ex:
            print(f"depth off: {type(ex).__name__}: {ex}")
            return None

    def grab(self, n=FRAMES):
        frames = []
        for _ in range(n * 3):
            if len(frames) == n:
                break
            z = self._frame()
            if z is not None:
                frames.append(z)
        return warp(average_depth(frames), self.h) if frames else None

    def close(self):
        self.lib.oniStreamStop(self.stream)
        self.lib.oniStreamDestroy(self.stream)
        self.lib.oniDeviceClose(self.dev)
        self.lib.oniShutdown()


# --- masks from the Workflow ---------------------------------------------------
def _poly_mask(pred, shape):
    m = np.zeros(shape[:2], np.uint8)
    pts = np.array([[p["x"], p["y"]] for p in pred.get("points", [])], np.int32)
    if len(pts) >= 3:
        cv2.fillPoly(m, [pts.reshape(-1, 1, 2)], 1)
    return m.astype(bool)


def _preds(v):
    return (v or {}).get("predictions", []) if isinstance(v, dict) else (v or [])


def masks(out, shape=(SIZE[1], SIZE[0])):
    """(plate mask or None, {name: mask}) from a Workflow result's `plate` and `foods` outputs."""
    plates = [_poly_mask(p, shape) for p in _preds(out.get("plate"))]
    plate = max(plates, key=lambda m: int(m.sum())) if plates else None
    foods = {}
    for p in _preds(out.get("foods")):
        m = _poly_mask(p, shape)
        foods[p.get("class")] = foods.get(p.get("class"), np.zeros(shape[:2], bool)) | m
    return plate, foods


# --- the math (eval/depth_vs_area.py) ------------------------------------------
def _all(foods, like):
    allfood = np.zeros_like(like, dtype=bool)
    for m in foods.values():
        allfood |= m
    return allfood


def radius_map(plate):
    """Distance from the plate centre / plate radius, per pixel (circle from the mask's area)."""
    ys, xs = np.nonzero(plate)
    cy, cx, r = ys.mean(), xs.mean(), np.sqrt(plate.sum() / np.pi)
    yy, xx = np.mgrid[0:plate.shape[0], 0:plate.shape[1]]
    return np.hypot(xx - cx, yy - cy) / r


def plate_profile(z, plate, foods=None):
    """Empty plate's depth vs normalized radius, as [[r, depth_mm], ...] (JSON-able), or None.
    Crumbs the Workflow still sees are skipped."""
    if plate is None or z is None or not plate.any():
        return None
    near_food = cv2.dilate(_all(foods or {}, plate).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)
    ok = plate & (z > 0) & ~near_food
    r, d = radius_map(plate)[ok], z[ok]
    idx = np.digitize(r, BINS_R) - 1
    mids = (BINS_R[:-1] + BINS_R[1:]) / 2
    prof = [[round(float(mids[i]), 3), round(float(np.median(d[idx == i])), 1)]
            for i in range(len(mids)) if (idx == i).sum() > 20]
    return prof if len(prof) >= 5 else None


def volumes(z, plate, foods, profile):
    """{name: volume} (sum of food height in mm over its pixels), or None if it can't be measured.
    The floor is the empty plate's shape, lined up by this shot's plate circle and shifted to its
    visible plate (the camera-to-plate distance can differ by a few mm). Holes get the mean height."""
    if z is None or plate is None or not plate.any() or not profile:
        return None
    r, d = np.array(profile, np.float32).T
    ref = np.interp(radius_map(plate), r, d)
    allfood = _all(foods, plate)
    vis = plate & (z > 0) & ~cv2.dilate(allfood.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    if vis.sum() > 200:
        ref = ref + np.median(z[vis] - ref[vis])
    h = np.clip(ref - z, 0, MAX_H)
    out = {}
    for name, m in foods.items():
        valid = m & (z > 0)
        mean_h = h[valid].mean() if valid.any() else 0.0
        out[name] = round(float(h[valid].sum() + mean_h * (m & ~valid).sum()), 1)
    return out
