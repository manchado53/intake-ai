"""Build a filtered dataset from the Roboflow COCO export and train RF-DETR Seg.
Usage: python train_variant.py <export_dir> <variant: v0|v1|v1b> [epochs]
  v0  = our meals only (file names start with meal_)
  v1  = all train minus holdout + exclude lists
  v1b = v1 + AUG_CONSERVATIVE (colour / brightness)
Env SIZE = Nano|Small|Medium|Large|XLarge (default Small); runs go to runs/<variant>[_<size>].
Valid (meal_04) and test (meal_03) are copied unchanged.
"""
import json, os, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
export, variant = Path(sys.argv[1]), sys.argv[2]
epochs = int(sys.argv[3]) if len(sys.argv) > 3 else 50

def orig(fn):
    """Roboflow renames 'x_png.rf.<hash>.jpg' -> back to 'x.png'."""
    base = fn.split(".rf.")[0]
    for ext in ("png", "jpg", "jpeg"):
        if base.endswith("_" + ext):
            return base[: -len(ext) - 1] + "." + ext
    return base

def names(p):
    return {l.strip() for l in open(p) if l.strip() and not l.startswith("#")}

holdout = names(ROOT / "lists/holdout_flic.txt") | names(ROOT / "lists/holdout_mfr.txt")
exclude = names(ROOT / "lists/exclude.txt")

size = os.environ.get("SIZE", "Small")
tag = variant if size == "Small" else f"{variant}_{size.lower()}"
out = ROOT / f"data_{tag}"  # per run, so parallel jobs don't clobber each other
shutil.rmtree(out, ignore_errors=True)
for split in ("train", "valid", "test"):
    src = export / split
    d = json.load(open(src / "_annotations.coco.json"))
    keep = []
    for im in d["images"]:
        o = orig(im["file_name"])
        if o in exclude:
            continue
        if split == "train":
            if o in holdout:
                continue
            if variant == "v0" and not o.startswith("meal_"):
                continue
        keep.append(im)
    ids = {im["id"] for im in keep}
    d["images"], d["annotations"] = keep, [a for a in d["annotations"] if a["image_id"] in ids]
    (out / split).mkdir(parents=True)
    for im in keep:
        os.link(src / im["file_name"], out / split / im["file_name"])
    json.dump(d, open(out / split / "_annotations.coco.json", "w"))
    left = sum(orig(im["file_name"]) in holdout for im in keep) if split == "train" else 0
    print(f"{split}: {len(keep)} images, {len(d['annotations'])} annotations, holdout names left: {left}", flush=True)
    if split == "train":
        assert left == 0, "holdout image leaked into train"

if os.environ.get("DRY"):
    sys.exit(0)
import rfdetr
kw = {}
if variant == "v1b":
    from rfdetr.datasets.aug_configs import AUG_CONSERVATIVE
    kw["aug_config"] = AUG_CONSERVATIVE
t0 = time.time()
getattr(rfdetr, f"RFDETRSeg{size}")().train(dataset_dir=str(out), output_dir=str(ROOT / f"runs/{tag}"),
                                           epochs=epochs, batch_size=8, grad_accum_steps=2, **kw)
print(f"TRAIN_SECONDS {tag} {time.time() - t0:.0f}", flush=True)
