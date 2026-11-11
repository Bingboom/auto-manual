# JS-100I EU English source-layout corrections

Status: local review candidate; no merge or publication authority is inherited.

## Discovery and bounded plan

Operator screenshots of the live `git-20261001-b68ca567` English route identify clipped Front/Rear View initials and folding arrow, lost Note frames, one-column safety, five-across Inbox, below-image step copy with missing outlines, missing gray connection/angle/device/dust panels, stacked angle examples, and flattened warranty sections.

1. Restore the source 12/6 safety columns (stack in source order on phones), opt-in three-column Inbox (3+2), seven outlined steps with native text above the art, shared Note tables and shared warranty years/sections. Keep all existing native wording and technical data.
2. Preserve complete own-source panels for English figure labels, native gray backgrounds, magnifier leaders, white product surfaces and the angle comparison. Retain selectable captions as non-visible duplicate descriptions only where those exact labels are already in the finished panel.
3. Rebuild with the existing Solar@INTL `build.py md` route and strict Sphinx. Verify actual desktop/phone output, native copy, source hashes, source/IR cold replay and regression checks. No online source-table/asset-registry write or publication is part of this patch.

## Reuse and source identity (before extraction)

Existing inventories checked: the English illustration manifest, its five Inbox and product-view crops, 16 shared operation crops, the legacy English recipe, the nine-language recipe, and the committed shared/template asset paths. Inbox and unmodified operation crops are reused byte-identically. The original English recipe stays hash-locked; a separate correction recipe owns new crops.

The existing product crop clips letters at x=30; the corresponding native labels begin at x=28.5962. The storage crop begins at y=411 and clips its arrow. Existing shared operation art deliberately removed backdrop paths and label text, so those files cannot restore the reported complete panel appearance. No intact equivalent panel exists in those candidates.

The local operator-workspace file `reports/eu-nine-language-ai-audit/attachments/JS-100I.ai` has SHA-256 `3c13c944a37ea2b4433e4dbe1e9116c3d8c77091da1a6a93f0b27d61c48ea907` and 87 pages. This differs from the historical source file hash, so it is recorded as a distinct source, never relabelled as the old master. Its English panel geometry/text was checked against the prior art and operator screenshots. For the old product-view rectangle, white-composited mean RGB error is under 0.026/255 per channel; crop geometry, line work and all English labels agree. The repair expands left to x=27.

The existing `tools.asset_intake` pipeline generated 11 bounded native crops: product views, storage arrow, four connections, angle diagram, two comparison cards, device and dust panel. Full gray backgrounds and four rounded corners remain; no synthetic illustration or redrawing is used. Exact old/new paths, hashes and source boxes are in [asset-decisions.json](asset-decisions.json). These corrections bind only the requested English route; other locales retain their existing inputs. No approved asset promotion contract or live registry is changed.

## Verification

The real `build.py md` entrypoint and strict Sphinx succeeded. The 68 Solar/whole-Web regression tests, Ruff, documentation integrity and maintainability guardrails passed. Native body text matches the pre-change baseline after ignoring decorative separators and whitespace (5,715 alphanumeric characters); all specification CSV files and both historical recipes are unchanged. Desktop 1280px and phone 390px metrics/screenshots are in [verification.json](verification.json). Dense mobile panels pan internally with no document overflow.

Visual evidence: [safety](safety-fixed.jpg), [Inbox](inbox-fixed.jpg), [steps](unfold-fixed.jpg), [charging](charging-fixed.jpg), [angle comparison](angle-fixed.jpg), [warranty](warranty-fixed.jpg), [phone](mobile-fixed.jpg).

The generic US quality command initially lacked the ignored phase2 snapshot in the new worktree; the same command with the existing original checkout's read-only `--data-root` snapshot passed. Full suite: 6,250 tests, 84 failures, 46 errors and 96 skipped in 1,032.544 seconds. The directly related selector/structure cases were corrected and the final 77-test direct suite passes. Ten representative residual failures reproduce on clean origin/main under this local Python 3.14 environment, including legacy frozen replay, CLI help wrapping, temporary-path handling and golden characterizations. See [full-suite-failures.json](full-suite-failures.json). The full suite remains non-green; no PR or publication is performed. No PR is opened while a required check remains failing.

The `page_solar` structure grouping baseline changes deliberately for English only: source safety columns, paired angle examples, and the 1+2 warranty-period table now match the requested source layout. Other languages and template trees keep their prior grouping. The full suite rewrote ten unrelated historical AD500A manifests as a side effect; these were restored byte-identically and are excluded from this patch.

Shared-carrier impact: JS-40C EU English also consumes `page_solar/en/01_safety_tips.rst`, so a future fresh JS-40C build receives the same responsive safety columns. Its published snapshot, product figures, inventory, warranty and wording are not changed. The JS-40C target regression is checked as the existing shared-template consumer; other solar targets use their own safety carrier.

The seven JS-40C shared-consumer tests passed. The final pinned `asset_intake` replay reproduced all eleven committed correction PNGs byte-identically.

Follow-up: the [test repair and additional screenshot corrections](../manual-layout-test-repair-20261110/README.md) supersede the non-green status above. CI-Python full regression now passes all 6,253 tests (92 conditional skips), with zero failures/errors. The complete bag crop and semantic safety subscripts are included; the correction recipe now replays twelve PNGs byte-identically. The original failed run remains recorded for traceability.
