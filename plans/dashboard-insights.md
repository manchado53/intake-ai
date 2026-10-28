# Dashboard insights the camera alone can give

Today the dashboard repeats what staff already chart by eye: % eaten and a "3 low meals" alert.
The camera knows more: which food was left and how much protein that was. Show that.

Three insights, each tied to someone who acts on it:
- **Protein + kcal vs daily goal** per resident (dietitian adds a shake before weight drops).
  Each resident gets a goal in `profiles.json`. Live demo moment: Mary's protein bar jumps when
  her lunch AFTER lands.
- **What gets left** per resident: an item left (<50% eaten) in most recent meals, e.g.
  "John leaves the meat 5 of 6 meals" -> suggest a texture / soft-diet review.
- **What comes back to the kitchen**: % left per menu item over 7 days and its food cost in $
  (dietary director, the buyer; answers the ROI-in-dollars ask). Portion costs are estimates.

To make it look real the synthetic seed grows to ~10 residents x 7 days plus today's breakfast,
with planted patterns (John leaves meat and stays low; one resident's protein slides), still
tagged synthetic. Math lives in a new pure `app/insights.py` with tests; `dashboard.py` only lays
it out. Contract 3 (`profiles.json`) gains goals, breakfast menus and portion cost.
