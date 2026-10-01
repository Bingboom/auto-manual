# JE-3000C EU Dutch approved corrections

Derived from the original three-language intake without changing that snapshot.
Operator confirmed AC and 8 A corrections on 2026-10-01. `source/errata.json` records the approval, original source hash, exact native fields and before/after copy. AC labels cover physical source pages 122, 127, 128 and the same AC button on App page 134. Combined car input current is corrected on pages 122 and 132. DC/USB and PV 24 A remain unchanged.

The two localized overview pictures are corrected using native same-page PDF glyphs through `extraction_recipes/nl-approved-labels.json`. Device geometry and leader lines remain byte-identical outside the two label areas. Original artwork and its recipe remain available. Other diagrams retain their already reviewed textless shared assets and CSS text containers.

The native adapter applies exact approved fields before shared component construction, keeps raw extraction evidence, and fails if approval/source hash/original text drift. The App AC label selection rectangle includes its complete initial A. This package unlocks Dutch publication; original PT/PL candidates are unchanged.
