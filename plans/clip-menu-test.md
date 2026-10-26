# CLIP menu test

**Goal:** before we have our own photos, check whether CLIP can name a cut-out food when it only
chooses from that meal's menu, and find where it breaks (leftover scraps, merged crops, food not
on the menu).

**Why:** the design is a class-agnostic `food-item` seg model + CLIP naming each crop from the
tray-ticket menu. If CLIP can't do that, we would need one trained class per food instead.

**How:** public Food-101 photos (24 nursing-home-like foods), fake scraps/merges/off-menu cases,
two CLIP sizes. Write-up in `docs/clip-menu-test.md`; rerun later on our own crops.
