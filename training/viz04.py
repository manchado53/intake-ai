"""Side-by-side: label (left) vs v1 prediction (right) on meal_04 valid images.
Run on Rosie from ~/intake-train: srun -p dgxh100 --gres=gpu:h100:1 python viz04.py
"""
import json, sys, cv2, numpy as np
from pathlib import Path
import rfdetr
from pycocotools import mask as mu

ROOT = Path.home() / "intake-train"
val = ROOT / "export_v2/valid"
coco = json.load(open(val / "_annotations.coco.json"))
cats = {c["id"]: c["name"] for c in coco["categories"]}
by_img = {}
for a in coco["annotations"]:
    by_img.setdefault(a["image_id"], []).append(a)
imgs = sorted(coco["images"], key=lambda i: i["file_name"])
pick = [imgs[i] for i in np.linspace(0, len(imgs) - 1, 6).astype(int)]

model = rfdetr.RFDETRSegSmall(pretrain_weights=str(ROOT / "runs/v1/checkpoint_best_total.pth"))
names = getattr(model, "class_names", None)
print("class_names", names)

FOOD, PLATE = (60, 200, 60), (255, 140, 0)

def draw(img, masks_kinds, title):
    out = img.copy()
    over = img.copy()
    for m, kind in masks_kinds:
        col = PLATE if kind == "plate" else FOOD
        if kind != "plate":
            over[m] = col
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(out, cs, -1, col, 2)
    out = cv2.addWeighted(over, 0.35, out, 0.65, 0)
    for m, kind in masks_kinds:
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(out, cs, -1, PLATE if kind == "plate" else FOOD, 2)
    nf = sum(k != "plate" for _, k in masks_kinds)
    cv2.rectangle(out, (0, 0), (out.shape[1], 30), (0, 0, 0), -1)
    cv2.putText(out, f"{title}  food blobs={nf}", (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    return out

rows = []
for im in pick:
    bgr = cv2.imread(str(val / im["file_name"]))
    h, w = bgr.shape[:2]
    gt = []
    for a in by_img.get(im["id"], []):
        rle = mu.frPyObjects(a["segmentation"], h, w)
        m = mu.decode(mu.merge(rle)).astype(bool)
        gt.append((m, "plate" if cats[a["category_id"]] == "plate" else "food"))
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    d = model.predict(rgb, threshold=0.5)
    pr = []
    for m, cid, conf in zip(d.mask, d.class_id, d.confidence):
        n = names[cid] if names is not None and cid < len(names) else str(cid)
        if isinstance(names, dict): n = names.get(cid, str(cid))
        pr.append((m.astype(bool), "plate" if "plate" in str(n) else "food"))
    tag = im["file_name"].split("_color")[0]
    rows.append(np.hstack([draw(bgr, gt, f"{tag} LABEL"), np.full((h, 8, 3), 255, np.uint8),
                           draw(bgr, pr, f"{tag} MODEL v1")]))
    print(tag, "gt", len(gt), "pred", len(pr), [str(names[c]) if names is not None else c for c in d.class_id])

pad = lambda r: np.vstack([r, np.full((8, r.shape[1], 3), 255, np.uint8)])
for k in range(0, 6, 3):
    cv2.imwrite(str(ROOT / f"viz_meal04_{k//3}.jpg"), np.vstack([pad(r) for r in rows[k:k+3]]), [cv2.IMWRITE_JPEG_QUALITY, 85])
print("ok")
