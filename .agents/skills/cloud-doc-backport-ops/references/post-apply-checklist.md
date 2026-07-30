# Post-apply checklist (mandatory, shared)

Run after EVERY backport apply round — both cloud-doc rounds
(cloud-doc-backport-ops) and .docx revision rounds (manual-revision-backport).
Each item exists because skipping it once shipped a real defect. "Done" claims
without this checklist are not done.

## 1. Deletion sweep (the known blind spot)

The apply/gate machinery is replacement-shaped; pure deletions mis-align or
abstain, and twice a real reviewer deletion survived into the next build.

1. Export the exact doc version the round was based on:
   - wiki URL → `lark-cli wiki +node-get --node-token <url>` → take `obj_token`;
   - `lark-cli drive +export --token <obj_token> --doc-type docx
     --file-extension markdown --output-dir <cwd-relative dir>`.
2. Compare block-by-block (heading + table anchors) against the post-apply
   review pages / source: hunt specifically for **"present in source, absent in
   doc"** blocks — those are reviewer deletions the tool cannot apply.
3. Pull the run report's `abstain` / structural-deletion entries and disposition
   each one explicitly with the operator. An abstained or unapplied `delete`
   delta is NEVER "diff 错位" by assumption — verify against the built
   artifact/cloud doc first (the 「安全上のご注意」 duplication shipped exactly
   this way), then skip or fix.

## 2. Symmetric-term pair check

For every term change applied (e.g. 输入端口→输入), grep the mirror/companion
terms (输出端口, and the whole family across pages/tables). Asymmetric edits are
usually reviewer 漏改 — surface, confirm with the operator, apply the pair
consistently (a confirmed pair may also belong in Translation_Memory for the
whole language family).

## 3. Reviewer-typo normalization

Obvious typos in reviewer text (duplicated tokens like 「最大30W最大30W」, broken
punctuation) are normalized **with operator approval** before entering any
source table or template. The source of truth never inherits a typo verbatim.

## 4. Per-write readback

Every source-table / TM write: GET the same record back, confirm the field
value, and report `record_id` + field + value (attachment fields: confirm the
file token is non-empty). Writes land with seconds of lag — sleep briefly
before verifying. A write without a readback is unproven; "the API returned
ok" has silently not persisted before (link fields).

## 5. Scope closure statement

End the round by stating: deltas applied / abstained-and-dispositioned /
deferred-as-debt, with zero unexplained leftovers. Anything deferred gets a
ledger line (PR body follow-up + build-table remark), not silence.
