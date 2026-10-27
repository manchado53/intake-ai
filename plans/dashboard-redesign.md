# Dashboard redesign: one "Today" screen instead of three tabs

The dashboard is split into Live feed / Residents / QR cards behind a sidebar radio. A dietitian
opening it wants one answer first: who needs me today? Today that answer is spread over two tabs
(alert banner on top, table on another tab, trend behind a dropdown), and the live feed is a long
list of big cards.

New layout, one screen, read top to bottom (See -> Understand -> Act):

- **Top strip:** today's numbers: meals scanned, average % eaten, residents at risk, scans to review.
- **Needs attention (left, wide):** one card per at-risk resident (3 low meals in a row) and per
  scan flagged for review, with the reason, a small trend, and an action button ("Notify RD",
  "Mark reviewed"). Empty state says "Nobody needs attention".
- **Residents (left, under it):** a grid of resident cards: name, room, today's breakfast /
  lunch / dinner as colored chips (blank = not scanned), last-8-meals sparkline, 3-day kcal and
  protein. Click a card -> a side dialog with the full trend and that resident's meals, each with
  BEFORE | AFTER photos side by side.
- **From the kitchen (right, narrow):** the live feed, compact: thumbnail, name, meal, % eaten,
  one line each; newest on top; updates every 2 s.
- **QR cards** leave the main nav: a "Print QR cards" button in the sidebar opens them.

Data logic, the API and the alert rule stay the same; only `app/dashboard.py` layout changes.
"Notify RD" / "Mark reviewed" only mark it in the dashboard DB for the demo (no real messages).
