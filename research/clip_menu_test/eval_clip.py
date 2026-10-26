"""CLIP zero-shot menu-matching test on Food-101 subset.
Usage: python eval_clip.py ViT-B-32 [ViT-B-16 ...]
"""
import os, sys, json, random, time
import numpy as np, torch
from transformers import CLIPModel, CLIPProcessor
HF = {'ViT-B-32': 'openai/clip-vit-base-patch32', 'ViT-B-16': 'openai/clip-vit-base-patch16', 'ViT-L-14': 'openai/clip-vit-large-patch14'}
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
torch.set_num_threads(os.cpu_count() or 4)

GROUPS = {
    "protein": ["pork_chop", "steak", "filet_mignon", "grilled_salmon", "chicken_wings", "chicken_curry", "baby_back_ribs"],
    "starch": ["fried_rice", "risotto", "macaroni_and_cheese", "spaghetti_bolognese", "lasagna", "french_fries"],
    "breakfast": ["omelette", "eggs_benedict", "pancakes"],
    "salad_soup": ["caesar_salad", "greek_salad", "clam_chowder"],
    "dessert": ["apple_pie", "carrot_cake", "chocolate_cake", "cheesecake", "ice_cream"],
}
CLASSES = [c for g in GROUPS.values() for c in g]
GROUP_OF = {c: g for g, cs in GROUPS.items() for c in cs}
PROMPTS = {
    "plain": "{}",
    "photo": "a photo of {}",
    "photo_food": "a photo of {}, a type of food",
}

def load_images():
    items = []
    for ci, c in enumerate(CLASSES):
        d = os.path.join(DATA, c)
        for f in sorted(os.listdir(d)):
            items.append((os.path.join(d, f), ci))
    return items

def scrap_crop(img, rng):
    """Random crop with 15-25% of the area, then 2x downscale (small leftover scrap)."""
    W, H = img.size
    frac = rng.uniform(0.15, 0.25)
    ar = rng.uniform(0.75, 1.33)
    w = int(min(W, np.sqrt(frac * W * H * ar))); h = int(min(H, frac * W * H / max(w, 1)))
    x = rng.randint(0, W - w); y = rng.randint(0, H - h)
    c = img.crop((x, y, x + w, y + h))
    return c.resize((max(1, w // 2), max(1, h // 2)), Image.BICUBIC)

def _feat(o):
    return o if torch.is_tensor(o) else o.pooler_output

def _img(model, pre, ims):
    return _feat(model.get_image_features(**pre(images=ims, return_tensors="pt")))

@torch.no_grad()
def embed_images(model, pre, items, crop):
    rng = random.Random(0)
    feats = []
    batch = []
    for p, _ in items:
        im = Image.open(p).convert("RGB")
        if crop:
            im = scrap_crop(im, rng)
        batch.append(im)
        if len(batch) == 32:
            feats.append(_img(model, pre, batch)); batch = []
    if batch:
        feats.append(_img(model, pre, batch))
    f = torch.cat(feats)
    return (f / f.norm(dim=-1, keepdim=True)).numpy()

@torch.no_grad()
def embed_text(model, tok, template):
    t = tok(text=[template.format(c.replace("_", " ")) for c in CLASSES], return_tensors="pt", padding=True)
    f = _feat(model.get_text_features(**t))
    return (f / f.norm(dim=-1, keepdim=True)).numpy()

def make_menus(labels, n_per_img=4, similar=False, seed=1):
    rng = random.Random(seed)
    menus = []
    for i, y in enumerate(labels):
        for _ in range(n_per_img):
            k = rng.choice([3, 4])
            if similar:
                pool = [CLASSES.index(c) for c in GROUPS[GROUP_OF[CLASSES[y]]] if CLASSES.index(c) != y]
            else:
                pool = [j for j in range(len(CLASSES)) if j != y]
            others = rng.sample(pool, min(k - 1, len(pool)))
            menus.append((i, [y] + others))
    return menus

def acc_all(S, labels):
    return float((S.argmax(1) == labels).mean())

def acc_menus(S, labels, menus):
    ok = 0
    for i, m in menus:
        ok += m[int(np.argmax(S[i, m]))] == labels[i]
    return ok / len(menus)

def main():
    items = load_images()
    labels = np.array([y for _, y in items])
    print(f"{len(items)} images, {len(CLASSES)} classes")
    menus_rand = make_menus(labels, similar=False)
    menus_sim = make_menus(labels, similar=True)
    print(f"{len(menus_rand)} random menus, {len(menus_sim)} similar menus")
    results = {}
    for arch in sys.argv[1:] or ["ViT-B-32"]:
        t0 = time.time()
        model = CLIPModel.from_pretrained(HF[arch]).eval(); pre = CLIPProcessor.from_pretrained(HF[arch]); tok = pre
        T = {k: embed_text(model, tok, v) for k, v in PROMPTS.items()}
        T["ensemble"] = sum(T.values()); T["ensemble"] /= np.linalg.norm(T["ensemble"], axis=1, keepdims=True)
        for cond in ["full", "scrap"]:
            I = embed_images(model, pre, items, crop=(cond == "scrap"))
            for pk, Tk in T.items():
                S = I @ Tk.T
                r = dict(all24=acc_all(S, labels), menu_rand=acc_menus(S, labels, menus_rand),
                         menu_similar=acc_menus(S, labels, menus_sim))
                results[f"{arch}|{cond}|{pk}"] = r
                print(f"{arch:9s} {cond:5s} {pk:10s} all24={r['all24']:.3f} rand3-4={r['menu_rand']:.3f} similar3-4={r['menu_similar']:.3f}", flush=True)
            if cond == "full":
                # per-group similar-menu accuracy with best default prompt
                S = I @ T["photo_food"].T
                for g in GROUPS:
                    idx = [k for k, (i, m) in enumerate(menus_sim) if GROUP_OF[CLASSES[labels[i]]] == g]
                    a = acc_menus(S, labels, [menus_sim[k] for k in idx])
                    print(f"   similar-menu acc group={g}: {a:.3f}")
                pred = S.argmax(1)
                conf = {}
                for y, p in zip(labels, pred):
                    if y != p:
                        conf[(CLASSES[y], CLASSES[p])] = conf.get((CLASSES[y], CLASSES[p]), 0) + 1
                top = sorted(conf.items(), key=lambda x: -x[1])[:8]
                print("   top confusions (all24):", top)
        print(f"{arch} done in {time.time()-t0:.0f}s", flush=True)
    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(results, f, indent=1)

if __name__ == "__main__":
    main()
