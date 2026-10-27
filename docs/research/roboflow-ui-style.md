# Roboflow UI style (for Intake.ai look, not a copy)

Goal: Intake.ai should feel at home next to Roboflow's product on a Zoom share.
We borrow the visual language (purple accent, deep-ink dark, warm off-white light, small radii,
mono labels). We do **not** use their logo, wordmark, name, or fonts (Suisse is licensed).

Checked 2026-10-27.

## What Roboflow uses

| Token | Value | Source |
|---|---|---|
| Primary purple (docs) | `#8315F9` (rgb 131,21,249) | supervision `docs/stylesheets/extra.css`; inference `docs/styles.css` |
| Primary dark / link | `#5B21B6`, `#6706CE` | inference `docs/styles.css` |
| Primary light | `#DDD6FE` | inference `docs/styles.css` |
| Brand 1 / strong / soft | `#8033EB` / `#6329B7` / `#934DF6` | roboflow.com CSS (`--color-brand-1*`) |
| Brand 2 (lilac) | `#C29AF6`, soft `#DFCFF6` | roboflow.com CSS (`--color-brand-2*`) |
| Light surface | `#F4F2EC` (warm off-white), `#FCFBF9`, `#ECEAE6` | roboflow.com `--rf-surface*` (light) |
| Dark surfaces | `#120D1F`, `#161026`, `#251742`, `#3E216B` | roboflow.com `--rf-surface-1..4` (dark) |
| Ink text | `#161026` (light), `#F4F2EC` (dark) | roboflow.com `--rf-on-surface` |
| Docs text / header | `#6F6C79` / `#1D1D1F` | inference `docs/styles.css` |
| Docs header bg | gradient `#F3EEFF -> #FFFFFF`, border `#E7E4F0` | inference `docs/styles.css` |
| Radii | 2 / 4 / 6 px; cards 8 px; outcome cards 16 px | roboflow.com `--radius-*`; supervision css |
| Fonts | Suisse (sans, licensed) + Geist Mono (labels) | roboflow.com `--font-primary`, `--font-secondary` |
| Light vs dark | Site has both themes; docs + app default light | roboflow.com `[data-theme]`; docs |

Sources: https://roboflow.com (Next.js CSS chunks),
https://github.com/roboflow/supervision/blob/develop/docs/stylesheets/extra.css,
https://github.com/roboflow/inference/blob/main/docs/styles.css.
app.roboflow.com is a login-gated SPA; nothing useful in public HTML.

## What Intake.ai uses

| Use | Value |
|---|---|
| Accent | `#8315F9`; strong `#6329B7`; soft lilac `#C29AF6` |
| Station (dark, TV) | bg `#120D1F`, panel `#1B1430`, bar `#2E2349`, text `#F4F2EC` |
| Dashboard (light) | bg `#FCFBF9`, secondary `#F3EEFF`, text `#1D1D1F`, border `#E7E4F0` |
| Status: idle / ready / ok / review / error | `#3A3644` / `#6329B7` / `#15803D` / `#F5A524` (dark text) / `#D92D20` |
| Fonts | Inter (dashboard, Google Fonts) or system sans; mono labels (Geist Mono / ui-monospace) |
| Radius | 8 px |

## Update 2026-10-27: follow summit.roboflow.com

The user preferred the Visual Intelligence Summit site, so both UIs now follow its tokens, read
from its stylesheet (`/_next/static/immutable/chunks/3ibrnkhpeeptj.css`):

| Token | Value | Summit CSS name |
|---|---|---|
| Ink (dark bg / text) | `#121110` | `--color-ink` |
| Cream (light bg) | `#F4F2EC` | `--color-cream` |
| Lavender (accent) | `#C29AF6` | `--color-lavender`, `--primary` |
| Lines / soft fills | `#E6E3DC`, `#D9C1F3`, `#2A2725`, `#1C1A19` | ring / surface colours |
| Corners | `0` (square) | `--radius: 0rem` |
| Sans | Suisse (licensed) -> we use Inter Tight | `--font-suisse` |
| Mono | Geist Mono, uppercase labels, `.08-.1em` tracking | `--font-geist-mono` |
| Headlines | tight, `-.03em` tracking | `letter-spacing:-.03em` |

Look on the page: ink sections with huge lavender type, cream sections, dotted grids, and
lavender "viewfinder" corner brackets around media. The station screen uses ink + dot grid +
bracketed panels; the dashboard uses cream + ink sidebar.

## Update 2026-10-27 (2): more purple + Roboflow logo

- Surfaces moved from ink to summit's deep purple: station bg `#120B22`, panels/idle `#251742`,
  lines `#3A2766`; dashboard paper `#F7F3FE`, fills `#ECE1FC`, sidebar `#251742`, buttons `#6F3FD8`,
  progress bars `#6F3FD8 -> #C29AF6`.
- Logo: `app/assets/roboflow-logo.svg` (cream, for dark) and `roboflow-logo-ink.svg`, downloaded
  from roboflow.com (`/_next/static/immutable/media/roboflow-logo*.svg`). Used as "powered by"
  next to the Intake.ai name (station top bar, inlined so it works offline; dashboard `st.logo`).
