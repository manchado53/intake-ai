# Fix the depth % eaten: measure height from the real plate shape

Area reads low on piles (food eaten off the top keeps its outline). The first depth try read high
because it measured height from the plate rim, but a plate is a dish ~15 mm deeper in the middle.
Use the cleared plate's own depth profile (centre to rim), lined up by the plate circle, as the
floor. Offline on our 4 weighed meals; compare area, old depth and new depth. Demo unchanged.
