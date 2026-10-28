# % eaten vs scale on FLIC (bigger, real-world check)

Our own % eaten error (16 points) comes from 4 staged meals. FLIC has ~400 real canteen trays,
photographed before and after eating, with every course weighed before and after. Run the same
Workflow on FLIC's 4 holdout days (never trained on), pair each dish's before and after plate crops
by course, and compare camera % eaten with grams % eaten. Also score FLIC's own hand masks on the
same dishes, so we can tell model error apart from the error of the area method itself.
Offline only: the demo setup does not change.
