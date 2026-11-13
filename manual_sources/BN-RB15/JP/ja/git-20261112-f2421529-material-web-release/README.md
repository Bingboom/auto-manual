# BN-RB15 JP Japanese Web release

Approved under MA-433, operator request 2026-11-12: 「审核一下 然后合入 上线发布文档」 for PR #1712.

Derived from [git-20261112-f2421529-material-web](../git-20261112-f2421529-material-web/README.md) at `6abe1128c27a186228185390d26f87adc9d3e2c9`; the original candidate is immutable. Japanese wording, specifications, revision differences, source concerns and the approved recycle-glyph standardization are retained.

`source/approval.json` binds the exact original SHA-256, candidate commit and independent replay result. `source/reviewed-candidate.json` inventories the original Web tree and lists every release difference. Restore the printed unplug glyph alongside the mandatory glyph; all three JVC symbol glyphs use hash-bound native PDF paths because existing shared candidates failed the fixed comparison. Wrap the unchanged native notation/accessory/control/FAQ/warranty tables in the existing shared responsive table container so portal mobile layouts scroll inside the panel.

Cold replay uses `tools.web.frozen_ai_web.replay_package` against `web/ja/`, without reopening the PDF or transcribing content. Source-bound symbol rows are checked by `require_symbol_asset_admission` at fresh sealing; the existing comparison tolerance, canonical choices, existing group members and captions are unchanged.

Publication must seal `source_manifest.json` at its committed Git ref, assemble only `docs/publish/**` in Hello-Docs and verify the actual RTD deployment. No live source, queue, asset-registry or HTML-link write is part of this Git-only release.
