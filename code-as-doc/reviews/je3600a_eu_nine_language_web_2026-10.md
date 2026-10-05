# JE-3600A EU nine-language Git-only Web release

Operator scope (2026-10-04): complete en/fr/es/de/it/uk/pt/nl/pl from the local
161-page HTE139 source, fix the accessory kit frame, merge and publish. MA-256
records the engineering and publication authorization. No live Base writes.

## Discovery and plan

The published historical accessory PNG clips the top dashed edge. PR #1403
already contains a complete textless native accessory panel and selectable
English labels, plus the confirmed English component layout. Reuse that asset
byte-identically instead of the discarded CSS patch or a new language crop.
The current main routes and PR #1403 candidate are distinct versions; do not
mix historical technical values with the 0924 native source.

1. Import the preserved English candidate into this task branch without
   modifying the other worktree. Sync current main and resolve composition.
2. Inventory the nine source blocks and freeze native text/provenance. Reuse
   English semantic components and neutral artwork; source-owned wording,
   values, warnings and legal text remain per language.
3. Replay all nine packages through the shared renderer and strict Sphinx;
   validate component coverage, asset identity, source fidelity and layout.
4. Pass applicable local and remote gates, squash merge engineering, verify
   mirror sync, assemble only docs/publish changes, merge and inspect RTD.

Safety nets: preserve root tmp, the original English source package, prior
JBP packages, other worktree reports and the persistent publish branch.
No workflows, dependencies, public CLI flags or schemas change.

## Accessory artwork reuse

| Candidate | Identity/content | Decision |
| --- | --- | --- |
| Historical connections_accessories-en.png | JBP-3600A art, English labels; cropped top frame | Reject incomplete panel |
| JE-2000E battery_pack_kit.png | Complete frame, different battery model | Layout reference only |
| PR #1403 assets/battery-accessories.png | JE-3600A companion JBP-3600A; complete native frame, cart badge, external wording removed | Byte-identical multilingual reuse; selectable localized captions |

The complete labelled scratch crop and CSS border experiment are discarded.
The artwork is a complete white/gray panel, not a transparent standalone icon.
