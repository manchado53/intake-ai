"""Visual check of the CLIP menu test: random examples with CLIP's scores, plus a results chart."""
import os, sys, json, random
import numpy as np, torch
from PIL import Image, ImageDraw, ImageFont
from transformers import CLIPModel, CLIPProcessor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_clip import HF, HERE, GROUPS, CLASSES, GROUP_OF, scrap_crop, load_images

rng = random.Random(7)
model = CLIPModel.from_pretrained(HF["ViT-B-16"]).eval()
pre = CLIPProcessor.from_pretrained(HF["ViT-B-16"])
TMPL = "a photo of {}, a type of food"
F = ImageFont.truetype("arial.ttf", 15); FB = ImageFont.truetype("arialbd.ttf", 17)
name = lambda c: c.replace("_", " ")


def f(o):
    return o if torch.is_tensor(o) else o.pooler_output


@torch.no_grad()
def scores(img, menu):
    t = pre(text=[TMPL.format(name(c)) for c in menu], return_tensors="pt", padding=True)
    i = pre(images=[img], return_tensors="pt")
    a, b = f(model.get_image_features(**i)), f(model.get_text_features(**t))
    a, b = a / a.norm(dim=-1, keepdim=True), b / b.norm(dim=-1, keepdim=True)
    s = (100 * a @ b.T)[0]
    return s.softmax(0).numpy(), s.numpy()


items = load_images()
rng.shuffle(items)
cases = []
# full + scrap with a "similar" menu (same food group = hardest), merged, off-menu
for kind in ["full"] * 4 + ["scrap"] * 4 + ["merged"] * 2 + ["offmenu"] * 2:
    p, y = items.pop()
    img = Image.open(p).convert("RGB")
    truth = CLASSES[y]
    same = [c for c in GROUPS[GROUP_OF[truth]] if c != truth]
    if kind == "full":
        menu = [truth] + rng.sample(same, 2)
    elif kind == "scrap":
        img = scrap_crop(img, rng); menu = [truth] + rng.sample(same, 2)
    elif kind == "merged":
        p2, y2 = next((q, z) for q, z in items if GROUP_OF[CLASSES[z]] != GROUP_OF[truth])
        b = Image.open(p2).convert("RGB").resize((256, 256)); a = img.resize((256, 256))
        img = Image.new("RGB", (512, 256)); img.paste(a, (0, 0)); img.paste(b, (256, 0))
        truth = f"{truth} + {CLASSES[y2]}"; menu = [CLASSES[y], CLASSES[y2], rng.choice(same)]
    else:
        menu = rng.sample(same, min(3, len(same)))
    rng.shuffle(menu)
    prob, raw = scores(img, menu)
    cases.append((kind, img, truth, menu, prob, raw))

TITLES = {"full": "FULL portion, menu of look-alikes", "scrap": "SCRAP (small leftover crop)",
          "merged": "MERGED: 2 foods in one crop", "offmenu": "OFF-MENU: right answer NOT in menu"}
W, H = 330, 360
sheet = Image.new("RGB", (W * 4, H * 3), "white")
d = ImageDraw.Draw(sheet)
for k, (kind, img, truth, menu, prob, raw) in enumerate(cases):
    x0, y0 = (k % 4) * W, (k // 4) * H
    th = img.copy(); th.thumbnail((W - 20, 190))
    sheet.paste(th, (x0 + (W - th.width) // 2, y0 + 30))
    d.text((x0 + 10, y0 + 6), TITLES[kind], font=FB, fill="black")
    d.text((x0 + 10, y0 + 226), "truth: " + name(truth)[:38], font=F, fill="#333")
    best = int(prob.argmax())
    if kind == "offmenu":
        flagged = raw.max() < 27.3  # threshold from the test (keeps 95% of on-menu)
        ok, verdict = flagged, f"top score {raw.max():.1f} -> {'flagged OTHER' if flagged else 'NOT flagged'}"
    elif kind == "merged":
        ok, verdict = menu[best] in truth.split(" + "), "picked one of the two" if menu[best] in truth else "picked neither"
    else:
        ok, verdict = menu[best] == truth, "right" if menu[best] == truth else "WRONG"
    for j, c in enumerate(menu):
        yy = y0 + 250 + j * 24
        col = "#2e7d32" if (c in truth.split(" + ") and kind != "offmenu") else "#9e9e9e"
        d.rectangle([x0 + 10, yy, x0 + 10 + int(150 * prob[j]), yy + 16], fill=col)
        d.text((x0 + 166, yy), f"{prob[j]*100:4.0f}%  {name(c)[:18]}", font=F, fill="black")
    d.text((x0 + 10, y0 + 328), ("OK  " if ok else "MISS  ") + verdict, font=FB,
           fill="#2e7d32" if ok else "#c62828")
    d.rectangle([x0, y0, x0 + W - 1, y0 + H - 1], outline="#ccc")
sheet.save(os.path.join(HERE, "clip-examples.png"))

# results chart from the full test (results2.json)
R = json.load(open(os.path.join(HERE, "results2.json")))
rows = []
for m in ["ViT-B-32", "ViT-B-16"]:
    r = R[m]
    rows.append((m, [("full, random menu", r["full|photo_food"]["rand"]), ("full, look-alike menu", r["full|photo_food"]["similar"]),
                     ("protein full", r["simgroup|full"]["protein"]), ("scrap, random menu", r["scrap|photo_food"]["rand"]),
                     ("scrap, look-alike menu", r["scrap|photo_food"]["similar"]), ("protein scrap", r["simgroup|scrap"]["protein"]),
                     ("merged: names one of the 2 foods", r["merged"]["one_of_two"]),
                     ("merged: both foods in its top 2", r["merged"]["top2_both"]),
                     ("off-menu flagged (full)", r["offmenu|full"]["top_score"]["keep95pct"]["off_flagged"]),
                     ("off-menu flagged (scrap)", r["offmenu|scrap"]["top_score"]["keep95pct"]["off_flagged"])]))
labels = [l for l, _ in rows[0][1]]
ch = Image.new("RGB", (900, 60 + 52 * len(labels)), "white"); d = ImageDraw.Draw(ch)
d.text((20, 12), "CLIP menu test on 480 Food-101 photos, 24 foods (grey = B/32, blue = B/16). Line = 90%", font=FB, fill="black")
for i, lab in enumerate(labels):
    y = 50 + i * 52
    d.text((20, y + 8), lab, font=F, fill="black")
    for k, (m, vals) in enumerate(rows):
        v = vals[i][1]; yy = y + k * 20
        d.rectangle([300, yy, 300 + int(520 * v), yy + 16], fill="#9e9e9e" if k == 0 else "#1565c0")
        d.text((300 + int(520 * v) + 6, yy), f"{v*100:.0f}%", font=F, fill="black")
d.line([300 + int(520 * .9), 45, 300 + int(520 * .9), ch.height - 5], fill="#c62828", width=1)
ch.save(os.path.join(HERE, "clip-results.png"))
print("ok")
