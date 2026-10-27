"""Score the v1b recipe at every Seg size (Nano..XLarge) on FLIC + MFR holdouts and meal_03 test.
Run on Rosie from ~/intake-train after sizes.sbatch (needs export_v2/, lists/, runs/v1b*): sbatch eval_sizes.sbatch
"""
import json, cv2, numpy as np
from pathlib import Path
import rfdetr, supervision as sv
from supervision.metrics import MeanAveragePrecision, MetricTarget
from pycocotools import mask as mu

ROOT = Path.home() / "intake-train"
EXP = ROOT / "export_v2"

def orig(fn):
    base = fn.split(".rf.")[0]
    for ext in ("png", "jpg", "jpeg"):
        if base.endswith("_" + ext):
            return base[: -len(ext) - 1] + "." + ext
    return base

def names(p):
    return {l.strip() for l in open(p) if l.strip() and not l.startswith("#")}

excl = names(ROOT / "lists/exclude.txt")
sets = {"flic": names(ROOT / "lists/holdout_flic.txt") - excl, "mfr": names(ROOT / "lists/holdout_mfr.txt") - excl}

def load(split, keep=None):
    d = json.load(open(EXP / split / "_annotations.coco.json"))
    cls = {c["id"]: (1 if c["name"] == "plate" else 0) for c in d["categories"]}
    anns = {}
    for a in d["annotations"]:
        anns.setdefault(a["image_id"], []).append(a)
    out = []
    for im in d["images"]:
        if keep is not None and orig(im["file_name"]) not in keep:
            continue
        out.append((EXP / split / im["file_name"], im, anns.get(im["id"], []), cls))
    return out

def gt_det(im, anns, cls):
    h, w = im["height"], im["width"]
    if not anns:
        return sv.Detections(xyxy=np.zeros((0, 4)), mask=np.zeros((0, h, w), bool), class_id=np.zeros(0, int))
    ms = np.stack([mu.decode(mu.merge(mu.frPyObjects(a["segmentation"], h, w))).astype(bool) for a in anns])
    xyxy = np.array([[a["bbox"][0], a["bbox"][1], a["bbox"][0] + a["bbox"][2], a["bbox"][1] + a["bbox"][3]] for a in anns], float)
    return sv.Detections(xyxy=xyxy, mask=ms, class_id=np.array([cls[a["category_id"]] for a in anns]))

data = {"flic": load("train", sets["flic"]), "mfr": load("train", sets["mfr"]), "meal03": load("test")}
print({k: len(v) for k, v in data.items()})

FOOD, PLATE = (60, 200, 60), (255, 140, 0)
def draw(img, det, title):
    over, out = img.copy(), img.copy()
    for m, c in zip(det.mask, det.class_id):
        if c == 0: over[m] = FOOD
    out = cv2.addWeighted(over, 0.35, out, 0.65, 0)
    for m, c in zip(det.mask, det.class_id):
        cs, _ = cv2.findContours(m.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(out, cs, -1, PLATE if c == 1 else FOOD, 2)
    cv2.rectangle(out, (0, 0), (out.shape[1], 26), (0, 0, 0), -1)
    cv2.putText(out, f"{title} food={int((det.class_id == 0).sum())}", (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    return out

results = {}
for v in ("v1b", "v1b_nano", "v1b_medium", "v1b_large", "v1b_xlarge"):
    size = "Small" if v == "v1b" else v.split("_")[1].capitalize().replace("Xlarge", "XLarge")
    model = getattr(rfdetr, f"RFDETRSeg{size}")(pretrain_weights=str(ROOT / f"runs/{v}/checkpoint_best_total.pth"))
    for name, items in data.items():
        mp = MeanAveragePrecision(metric_target=MetricTarget.MASKS, class_agnostic=False)
        cnt_err, rows = [], []
        pick = set(np.linspace(0, len(items) - 1, 6).astype(int)) if False else set()
        for i, (p, im, anns, cls) in enumerate(items):
            bgr = cv2.imread(str(p))
            gt = gt_det(im, anns, cls)
            pr = model.predict(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), threshold=0.3)
            mp.update(pr, gt)
            p5 = pr[pr.confidence >= 0.5]
            cnt_err.append(abs(int((p5.class_id == 0).sum()) - int((gt.class_id == 0).sum())))
            if i in pick:
                tag = orig(p.name).rsplit(".", 1)[0][:28]
                h = bgr.shape[0]
                rows.append(np.hstack([draw(bgr, gt, f"{tag} LABEL"), np.full((h, 8, 3), 255, np.uint8), draw(bgr, p5, "MODEL v1")]))
        r = mp.compute()
        ce = np.array(cnt_err)
        results[(v, name)] = (r.map50_95, r.map50, ce.mean(), (ce == 0).mean())
        print(f"{v:4s} {name:7s} segm mAP50:95={r.map50_95:.3f} mAP50={r.map50:.3f} blobcount_err={ce.mean():.2f} exact={100*(ce==0).mean():.0f}%", flush=True)
        if rows:
            W = max(r_.shape[1] for r_ in rows)
            rows = [cv2.copyMakeBorder(r_, 0, 8, 0, W - r_.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for r_ in rows]
            for k in range(0, len(rows), 3):
                cv2.imwrite(str(ROOT / f"viz_{name}_{k//3}.jpg"), np.vstack(rows[k:k+3]), [cv2.IMWRITE_JPEG_QUALITY, 85])
print("done")
