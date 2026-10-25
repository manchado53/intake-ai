"""Live preview of the Orbbec DaBai DCW: color (left) + depth (right).

Color comes through Windows as a normal webcam; depth comes through OpenNI2.
Use it to aim the camera straight down at the plate. Press q to quit.

    .venv/Scripts/python tools/preview.py
"""
import os

import cv2
import numpy as np
from openni import openni2
from pygrabber.dshow_graph import FilterGraph

OPENNI_LIBS = os.environ.get("OPENNI2_LIBS", os.path.expanduser(
    r"~\Downloads\orbbec_openni\sdk\OpenNI_2.3.0.86_202210111950_4c8f5aa4_beta6_windows\Win64-Release\sdk\libs"
))
COLOR_NAME = "Orbbec DaBai DCW RGB Camera"
NEAR_MM, FAR_MM = 250, 500  # depth color scale: plate sits ~350-450 mm away


def open_color():
    names = FilterGraph().get_input_devices()
    if COLOR_NAME not in names:
        raise SystemExit(f"color camera not found, saw: {names}")
    cap = cv2.VideoCapture(names.index(COLOR_NAME), cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap


def open_depth():
    os.add_dll_directory(OPENNI_LIBS)
    os.add_dll_directory(os.path.join(OPENNI_LIBS, "OpenNI2", "Drivers"))
    cwd = os.getcwd()
    os.chdir(OPENNI_LIBS)  # OpenNI.ini finds its Drivers folder relative to here
    openni2.initialize(OPENNI_LIBS)
    os.chdir(cwd)
    dev = openni2.Device.open_any()
    stream = dev.create_depth_stream()
    stream.set_mirroring_enabled(False)  # OpenNI mirrors by default; the color webcam doesn't
    stream.start()
    return stream


def colorize(z):
    clipped = np.clip(z, NEAR_MM, FAR_MM)
    scaled = (255 * (clipped - NEAR_MM) / (FAR_MM - NEAR_MM)).astype(np.uint8)
    img = cv2.applyColorMap(255 - scaled, cv2.COLORMAP_JET)  # red = close, blue = far
    img[z == 0] = 0  # no reading = black
    return img


def main():
    cap, depth = open_color(), open_depth()
    while True:
        ok, color = cap.read()
        f = depth.read_frame()
        z = np.frombuffer(f.get_buffer_as_uint16(), dtype=np.uint16).reshape(f.height, f.width)
        if not ok:
            color = np.zeros((480, 640, 3), np.uint8)
        color = cv2.resize(color, (640, 480))
        dimg = cv2.resize(colorize(z), (640, 480), interpolation=cv2.INTER_NEAREST)

        cy, cx = z.shape[0] // 2, z.shape[1] // 2
        center = z[cy - 30:cy + 30, cx - 30:cx + 30]  # wide patch so one glare spot can't read 0
        center_mm = int(np.median(center[center > 0])) if (center > 0).any() else 0
        valid = 100 * (z > 0).mean()
        for img in (color, dimg):
            cv2.drawMarker(img, (320, 240), (255, 255, 255), cv2.MARKER_CROSS, 20, 2)
        cv2.putText(dimg, f"center {center_mm} mm  valid {valid:.0f}%", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("Plate Check preview  (q = quit)", np.hstack([color, dimg]))
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    depth.stop()
    openni2.unload()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
