# Confirm before scanning + before/after side by side

The station scans on its own as soon as a QR card holds still for 1 s. In a live demo that fires
too early (card still moving, plate half in view). Staff should press a button when the plate is
ready. And the AFTER result should sit next to the BEFORE picture, so anyone can see what changed.

- **Confirm:** a steady card no longer scans. The screen turns to "Mary R. – lunch: press SCAN"
  and shows a big SCAN button (touch on the robot screen, click on the laptop, or Space/Enter).
  The press scans the newest camera frame with that card. No card seen, no button.
- **Side by side:** the station keeps the annotated BEFORE picture of the open meal. The screen
  shows three panels: live camera | BEFORE | AFTER. After a BEFORE scan the BEFORE panel fills;
  after an AFTER scan the AFTER panel fills, with the per-item % bars under them.
- The BEFORE picture is kept in station.db (stays on the box), so a restart still shows it.

Tests: pytest for the confirm flag and for the stored BEFORE picture; then a live run on the Orin.
