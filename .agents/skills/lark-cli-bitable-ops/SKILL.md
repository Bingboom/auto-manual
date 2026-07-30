---
name: lark-cli-bitable-ops
description: The single source of truth for reading/writing Feishu Bitable (多维表格) with lark-cli in this repo — command shapes, field-type traps, attachment uploads, the most-used base/table coordinates, and the mandatory write-readback discipline. Load it BEFORE any direct lark-cli base read/write (spec intake, backport source-table writes, TM maintenance, asset registry, build-table rows). Other skills reference this one instead of restating payload shapes. NOT a business workflow — intake/backport/TM flows live in their own skills.
---

# lark-cli Bitable Ops

Every skill that touches a live Feishu table shares the same failure modes:
payload shapes recalled slightly wrong, silent write failures on special field
types, and "the API said ok" standing in for proof. This skill is the one place
those facts live. If a recipe here disagrees with `lark-cli --help`, trust the
CLI and fix this skill in the same change.

## The write-readback discipline (mandatory)

**Before writing — three questions, answered with live data, not memory:**

1. **Does the target already exist?** Filter-query the table for the key you
   are about to create/update (both tables, when a document_key spans two). A
   blind clone onto existing rows has doubled a target's row set before.
2. **Does the table shape match your assumption?** Pull ONE record and check
   the actual field names/types (case differs between sibling tables: the
   footnotes table has lowercase `type`, notes has `Type`). Never batch-write
   against a shape you haven't seen this session.
3. **Is the operation additive or replacing?** A "mirror/sync" that replaces
   must first prove it deletes nothing native — querying the live table before
   designing the write once saved 72 registry rows from silent deletion.
   Prefer merge/append + never-delete unless deletion is the explicit task.

**Around writing:**

- Writes to live source tables are **operator-gated**: stage/present the exact
  rows and values, get explicit confirmation (「确认/入库」, numbered picks
  count), then write. This repo has zero tolerance for unapproved source-table
  writes.

**After writing — no exceptions:**

- GET the same record back and confirm the field value; **report record_id +
  field + value** (a filtered view link when helpful) to the operator.
- Writes land with **seconds of lag** — sleep briefly before the verify read.
- Attachment fields: confirm the file token is non-empty after upload.
- Batch writes: verify per record (spot-check at minimum, full readback for
  source tables), and count rows before/after.
- **Never assert "it doesn't exist / query returns nothing" from one script
  run or inference** — query the live Base directly (or build a minimal repro)
  first. Two such assertions were disproven by the operator's screenshots.

## Use bundled resources

- `references/cli-recipes.md` — read/write command shapes, field-type traps
  (formula/lookup/link/select), attachments, identity, doc export/copy, CLI
  version-change history. Read before composing any payload.
- `references/coordinates.md` — the most-used base/table/node ids. The
  authoritative full inventory is `user-guide/two_plane_map.md` §1.1; the
  reference holds only the working set and points there.
