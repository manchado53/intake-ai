"""Extended CLIP menu-matching test: (a)-(f). Usage: python eval2.py ViT-B-32 [ViT-B-16]"""
import os, sys, json, random, time
import numpy as np, torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_clip import (HF, DATA, HERE, GROUPS, CLASSES, GROUP_OF, PROMPTS, scrap_crop, acc_all, acc_menus, make_menus)
torch.set_num_threads(os.cpu_count() or 4)


def load_items():
    items = []
    for ci, c in enumerate(CLASSES):
        d = os.path.join(DATA, c)
        for f in sorted(os.listdir(d)):
            items.append((os.path.join(d, f), ci))
    return items


def _f(o):
    return o if torch.is_tensor(o) else o.pooler_output


@torch.no_grad()
def embed(model, pre, ims):
    out = []
    for i in range(0, len(ims), 32):
        out.append(_f(model.get_image_features(**pre(images=ims[i:i + 32], return_tensors="pt"))))
    f = torch.cat(out)
    return (f / f.norm(dim=-1, keepdim=True)).numpy()


@torch.no_grad()
def embed_text(model, pre, tmpl):
    t = pre(text=[tmpl.format(c.replace("_", " ")) for c in CLASSES], return_tensors="pt", padding=True)
    f = _f(model.get_text_features(**t))
    return (f / f.norm(dim=-1, keepdim=True)).numpy()


def side_by_side(a, b):
    h = 224
    a = a.resize((int(a.width * h / a.height), h)); b = b.resize((int(b.width * h / b.height), h))
    if a.width > 224: a = a.crop((a.width // 2 - 112, 0, a.width // 2 + 112, h))
    if b.width > 224: b = b.crop((b.width // 2 - 112, 0, b.width // 2 + 112, h))
    im = Image.new("RGB", (a.width + b.width, h)); im.paste(a, (0, 0)); im.paste(b, (a.width, 0))
    return im


def offmenu(S, labels, N, seed=4):
    """S: 100*cosine. Returns on/off arrays of (correct, top, margin, softmax_p, vocab_flag)."""
    rng = random.Random(seed); on, off = [], []
    C = len(CLASSES)

    def feats(i, menu, true_in):
        s = S[i, menu]; o = np.sort(s)[::-1]; p = np.exp(s - s.max()); p /= p.sum()
        pred = menu[int(np.argmax(s))]
        vocab_flag = int(np.argmax(S[i])) not in menu  # kitchen-wide vocab = all dishes
        return (float(true_in and pred == labels[i]), o[0], o[0] - o[1], p.max(), float(vocab_flag))

    for i in range(N):
        y = labels[i]
        for _ in range(3):
            k = rng.choice([3, 4])
            on.append(feats(i, [y] + rng.sample([c for c in range(C) if c != y], k - 1), True))
            off.append(feats(i, rng.sample([c for c in range(C) if c != y], k), False))
    return np.array(on), np.array(off)


def summarize_off(on, off):
    base = on[:, 0].mean(); out = dict(on_menu_acc=round(float(base), 3))
    for name, col in [("top_score", 1), ("margin", 2), ("softmax_p", 3)]:
        best = {}
        for t in np.unique(np.concatenate([on[:, col], off[:, col]])):
            acc = (on[:, 0] * (on[:, col] >= t)).mean(); fl = (off[:, col] < t).mean()
            for tgt in (0.95, 0.90):
                if acc >= tgt * base and fl > best.get(tgt, (0, -1))[1]:
                    best[tgt] = (acc, fl, t)
        a = on[on[:, 0] == 1][:, col]; b = off[:, col]
        auroc = float((a[:, None] > b[None, :]).mean())
        out[name] = dict(auroc=round(auroc, 3), **{f"keep{int(k * 100)}pct": dict(on_acc=round(float(v[0]), 3), off_flagged=round(float(v[1]), 3), thr=round(float(v[2]), 3)) for k, v in best.items()})
    out["vocab_anchor"] = dict(on_acc=round(float((on[:, 0] * (1 - on[:, 4])).mean()), 3), off_flagged=round(float(off[:, 4].mean()), 3))
    return out


def main():
    items = load_items(); labels = np.array([y for _, y in items]); N = len(items)
    print(f"{N} images, {len(CLASSES)} classes", flush=True)
    imgs = [Image.open(p).convert("RGB") for p, _ in items]
    rng = random.Random(0); scraps = [scrap_crop(im, rng) for im in imgs]
    rng = random.Random(2); pairs = []
    while len(pairs) < 300:
        i, j = rng.randrange(N), rng.randrange(N)
        if labels[i] != labels[j]: pairs.append((i, j))
    merged = [side_by_side(imgs[i], imgs[j]) for i, j in pairs]
    mr, ms = make_menus(labels), make_menus(labels, similar=True)
    print(f"{len(mr)} random menus, {len(ms)} similar menus, {len(pairs)} merged pairs", flush=True)
    res = {}
    for arch in sys.argv[1:] or ["ViT-B-32"]:
        t0 = time.time()
        model = CLIPModel.from_pretrained(HF[arch]).eval(); pre = CLIPProcessor.from_pretrained(HF[arch])
        T = {k: embed_text(model, pre, v) for k, v in PROMPTS.items()}
        e = sum(T.values()); T["ensemble"] = e / np.linalg.norm(e, axis=1, keepdims=True)
        t1 = time.time()
        IF, IS, IM = embed(model, pre, imgs), embed(model, pre, scraps), embed(model, pre, merged)
        tt = time.time() - t1
        R = res[arch] = {}
        for pk, Tk in T.items():
            for cond, I in [("full", IF), ("scrap", IS)]:
                S = I @ Tk.T
                R[f"{cond}|{pk}"] = r = dict(all=acc_all(S, labels), rand=acc_menus(S, labels, mr), similar=acc_menus(S, labels, ms))
                print(f"{arch} {cond:5s} {pk:10s} all{len(CLASSES)}={r['all']:.3f} rand3-4={r['rand']:.3f} sim3-4={r['similar']:.3f}", flush=True)
        Tk = T["photo_food"]
        for cond, I in [("full", IF), ("scrap", IS)]:
            S = I @ Tk.T
            g = {g: round(acc_menus(S, labels, [m for m in ms if GROUP_OF[CLASSES[labels[m[0]]]] == g]), 3) for g in GROUPS}
            R[f"simgroup|{cond}"] = g; print(f"   sim-menu by group ({cond}):", g, flush=True)
        # e) merged: menu = both foods + 1-2 random others
        SM = IM @ Tk.T; SF = IF @ Tk.T; rng = random.Random(3)
        cnt = dict(left=0, right=0, other=0, top2_both=0, winner_is_stronger_single=0)
        for k, (i, j) in enumerate(pairs):
            for _ in range(2):
                pool = [c for c in range(len(CLASSES)) if c not in (labels[i], labels[j])]
                menu = [labels[i], labels[j]] + rng.sample(pool, rng.choice([1, 2]))
                order = np.argsort(-SM[k, menu]); p = menu[order[0]]
                if p == labels[i]: cnt["left"] += 1
                elif p == labels[j]: cnt["right"] += 1
                else: cnt["other"] += 1
                cnt["top2_both"] += set(menu[o] for o in order[:2]) == {labels[i], labels[j]}
                stronger = labels[i] if SF[i, labels[i]] >= SF[j, labels[j]] else labels[j]
                cnt["winner_is_stronger_single"] += p == stronger
        tot = 2 * len(pairs)
        R["merged"] = {k: round(v / tot, 3) for k, v in cnt.items()}
        R["merged"]["one_of_two"] = round((cnt["left"] + cnt["right"]) / tot, 3)
        print("   merged:", R["merged"], flush=True)
        for cond, I in [("full", IF), ("scrap", IS)]:
            on, off = offmenu(100 * (I @ Tk.T), labels, N)
            R[f"offmenu|{cond}"] = o = summarize_off(on, off)
            print(f"   off-menu {cond}:", json.dumps(o), flush=True)
        R["embed_seconds_cpu"] = round(tt, 1); R["n_embedded"] = 2 * N + len(pairs)
        print(f"{arch} done {time.time() - t0:.0f}s (embed {tt:.0f}s for {2 * N + len(pairs)} imgs)", flush=True)
        json.dump(res, open(os.path.join(HERE, "results2.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
