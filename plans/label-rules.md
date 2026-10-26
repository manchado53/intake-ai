# Label rules

**Goal:** every image is labeled the same way, so "empty plate" reads 100% eaten and the model
learns one clear idea of what counts as food.

**Classes (2):** `food-item` and `plate`. The model does not name foods; CLIP names each
`food-item` from the meal's menu later (see `docs/clip-menu-test.md`).

## What gets a mask

| Thing | Label | Why |
|---|---|---|
| A food portion or pile (chicken piece, pasta pile, pepper pile) | `food-item`, one mask per piece/pile | This is what we measure |
| Two different foods touching | **two** masks, split at the border | Merged crops break CLIP naming |
| Pieces of the same food far apart (scattered pasta) | one mask per piece/clump | Instance masks; the block groups them by menu item later |
| Sauce pooled on or against a food | part of **that food's** mask | It's eaten with it |
| Crumbs smaller than ~1 cm (~18 px at 37 cm) | **no label** | Leftover dust, not food a person would chart |
| Smears, sauce film, grease on the plate | **no label** | Can't be eaten; would make "empty" read as food |
| Bones, skin left behind, pits, peels | **no label** | Not edible; a bones-only plate must read 100% eaten |
| The plate | `plate`, one mask of the whole disk incl. rim, drawn under the food | Size reference + area for the plate |
| Fork, knife, napkin, hand, cup, table | **no label** | Not food, not plate |
| Frame with no plate (bad shot) | skip, tag `bad-frame` | Not a real scan |

## How the rules reach SAM 3

SAM 3 only takes short prompts and a confidence cutoff, so:
1. **Prompts:** `food` → `food-item`, `plate` → `plate`.
2. **Cutoff:** tune on 3 test images first: a full plate (s0), a bones-only plate (s6), the
   empty plate. Raise it until crumbs and bones mostly drop out but real food stays.
3. **Hand fix in Roboflow:** delete crumb/bone/smear masks, split merged foods, fill sauce into
   its food. These rules are the checklist.

### Tested 2026-10-25 (SAM 3 preview, cutoff 0.5)

| Image | Prompt `food` | Menu prompts (`chicken`, `pasta`, `roasted red peppers`) |
|---|---|---|
| Full plate (s0_1) | 12 food masks | 14 food masks |
| Bones only (s6_1) | 14 (crumbs + bones) | **0** food |
| Empty plate (empty_1) | 27 (crumbs) | **0** food |

A cutoff can't fix the generic prompt (crumbs scored up to 0.79, real pasta down to 0.52).
**Decision: prompt SAM 3 with each meal's menu items, all mapped to `food-item`.** This is the
same menu the tray ticket carries, so it matches the product.

## Scorecard rule that goes with it

% eaten counts the **edible** part only: edible grams = served grams − bones (weighed at the end,
`data/raw/weights.md`). meal_01: chicken 271 g served, 49 g bone → 222 g edible.
