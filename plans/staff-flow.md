# Station flow that matches how staff really work

Today the screen shows empty BEFORE and AFTER boxes from the start, and once a meal has a BEFORE
every later scan is an AFTER forever. A dining aide doesn't think in "phases". They put a plate
and a card down, see who it is, press one button, and walk away. Later they bring the plate back.

New flow, one card at a time:

- **Card seen:** "Welcome, Mary R. – lunch". The screen says what the next press will do:
  "SCAN = BEFORE" (no open plate) or "SCAN = AFTER" (her BEFORE is waiting, shown next to the camera).
- **BEFORE scanned:** only the BEFORE picture shows. No empty AFTER box.
- **AFTER scanned:** BEFORE and AFTER side by side with the % bars. The meal is now closed.
- **Next scan of the same card + meal** starts a new BEFORE (second plate). Order is always
  before -> after -> before -> after.
- **The result stays on screen** after the card leaves, until a different card shows up.
- **REDO LAST button:** for a bad shot (hand in the way, plate cut off). Throws away that
  person's last scan and takes it again as the same phase. The dashboard drops the thrown-away one.

Changes: `station/station.py` (phase rule, redo, screen state), `station/store.py` (meal is
open only if its newest ok scan is a BEFORE; mark a scan void), `station/screen.html` (welcome
line, hide empty panels, REDO button), contract 2 gets an optional `replaces` scan_id, and the
dashboard ignores a scan that a later one replaces. Tests for the cycle, redo, and the dashboard
drop.
