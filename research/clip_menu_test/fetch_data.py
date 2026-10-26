"""Fetch Food-101 validation images for nursing-home-like classes via the HF dataset-server /rows API.
(datasets/pyarrow fails here: Windows long-path DLL issue; /filter endpoint returned 500s.)
Validation rows are grouped in class blocks of ~250, so read a window from each block."""
import os, sys, io, json, time, requests
from PIL import Image

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PER_CLASS = int(sys.argv[1]) if len(sys.argv) > 1 else 20
API = "https://datasets-server.huggingface.co/rows"
Q = dict(dataset="ethz/food101", config="default", split="validation")

CLASSES = [
    "pork_chop", "steak", "filet_mignon", "grilled_salmon", "chicken_wings", "chicken_curry", "baby_back_ribs",
    "fried_rice", "risotto", "macaroni_and_cheese", "spaghetti_bolognese", "lasagna", "french_fries",
    "omelette", "eggs_benedict", "pancakes",
    "caesar_salad", "greek_salad", "clam_chowder",
    "apple_pie", "carrot_cake", "chocolate_cake", "cheesecake", "ice_cream",
]

def get(url, **kw):
    for a in range(5):
        try:
            r = requests.get(url, timeout=120, **kw); r.raise_for_status(); return r
        except Exception as e:
            print("retry", a, e, flush=True); time.sleep(3 * (a + 1))
    raise RuntimeError(url)

first = get(API, params={**Q, "offset": 0, "length": 1}).json()
names = first["features"][1]["type"]["names"]
want = {names.index(c): c for c in CLASSES}
counts = {c: 0 for c in CLASSES}
for off in range(100, 25250, 250):
    if all(v >= PER_CLASS for v in counts.values()):
        break
    rows = get(API, params={**Q, "offset": off, "length": PER_CLASS + 10}).json()["rows"]
    for row in rows:
        c = want.get(row["row"]["label"])
        if not c or counts[c] >= PER_CLASS:
            continue
        d = os.path.join(OUT, c); os.makedirs(d, exist_ok=True)
        im = Image.open(io.BytesIO(get(row["row"]["image"]["src"]).content)).convert("RGB")
        im.save(os.path.join(d, f"{counts[c]:03d}.jpg"), quality=92); counts[c] += 1
print(json.dumps(counts))
