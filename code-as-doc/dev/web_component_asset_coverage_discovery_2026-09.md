# Web Component and Figure Asset Coverage Discovery (2026-09)

## Scope

This discovery covers the responsive Web manual path after the current Web
component PRs landed. It answers two questions:

1. why the shared warranty number treatment is missing from JE-1000F EU,
   including German and Italian; and
2. whether overview, operation and charging figures consistently reuse approved
   finished panels instead of rebuilding target-specific presentation logic.

No live Feishu data, review source, public CLI, schema or approved artwork is
changed by this workstream.

## Findings

### Warranty is incorrectly coupled to the frozen-figure allowlist

`tools/web_presentation.py::transform_web_fragment` detects warranty pages but
returns before `_transform_warranty` whenever `supports_figure_contract` is
false. The allowlist in `docs/renderers/contracts/web_manual.json` currently
contains only `JE-1000F / US`, so the reusable semantic warranty component is
silently skipped for every EU locale.

The existing parser already accepts the localized source structure. When the
unrelated target gate is removed, the same component produces the governed
`3 / 2` badges and preserves the localized units and labels:

| Locale | Unit |
| --- | --- |
| English | `YEARS` |
| French | `ANS` |
| Spanish | `AÑOS` |
| German | `JAHRE` |
| Italian | `ANNI` |

Conclusion: warranty is a shared semantic composition. It must run before the
frozen-figure target gate. The gate remains authoritative for target geometry
and approved composites.

### Two approved-artwork mechanisms exist but have no shared coverage view

The Web source adapter supports two intentionally different asset carriers:

- `web-illustrations/v1` replaces source images with one hash-verified finished
  panel and records `illustration_provenance`. JBP-2000B / JP uses this path.
- `web-composite-manifest/v1` binds an approved localized composite to a
  semantic component by replace key, target, locale and source-fragment hash.
  JE-1000F / US uses this path for part of its figure inventory.

Both mechanisms are valid, but callers currently have to inspect different IR
fields and infer missing coverage. A new target can therefore build successfully
while still falling back to editable HTML or plain source figures without a
single, reviewable inventory.

### Approved asset coverage is incomplete

The current committed asset state is:

| Target | Overview | Operation | Charging |
| --- | --- | --- | --- |
| JBP-2000B / JP | finished panels | finished panels | finished panels |
| JE-1000F / US | approved composites | partial approved composites | partial approved composites |
| JE-1000F / EU | no approved finished/composite artwork | none | none |
| JE-2000E / CN | no approved finished/composite artwork | none | none |
| JE-3000C / KR | no approved finished/composite artwork | none | none |

JE-1000F / US still lacks composites for AC wall charging, direct solar
charging and solar-adapter charging. EU/CN/KR have neither an illustration
manifest nor composite entries in their current IR. Those gaps cannot be
correctly closed by copying US art or generating new screenshots: localized
copy, source identity and approval hashes would be false.

## Root cause and architecture boundary

The defect is not CSS inheritance. Shared semantic components and approved
finished artwork were placed behind the same target gate even though they have
different authority:

- semantic components inherit across targets and preserve source-owned copy;
- target geometry is selected by an explicit target instance;
- finished panels and composites override semantic presentation only after
  target, locale, source identity, hash and approval checks pass.

The repair must preserve that order. New manuals should reuse component
semantics by default, while artwork overrides remain explicit and fail closed.

## Safety net

The change will add tests proving:

- warranty transforms for a target outside `figure_targets`;
- JE-1000F EU English, French, Spanish, German and Italian keep their localized
  unit and label while sharing the same number-badge component;
- frozen figure composition remains blocked outside `figure_targets`;
- a single coverage inventory classifies both approved asset carriers and
  distinguishes editable fallback from a true missing slot.

## Deferred asset work

Approved localized panels for EU/CN/KR and the missing US charging panels remain
a separate asset-intake task. They should enter through a committed manifest or
asset recipe and hash verification, not through page-specific Python or CSS.
