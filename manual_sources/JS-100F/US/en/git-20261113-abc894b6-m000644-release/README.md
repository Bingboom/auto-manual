# JS-100F US/en - authorized Git-only release

Approval: MA-438, operator publication instruction 「全部你都照写上线 问题可以记录在pr里」 dated 2026-11-13.

This immutable copy preserves all reviewed native pages, the original PDF, tables, artwork and shared styling. Only release approval and source identity metadata change. The complete candidate remains at [git-20261113-abc894b6-m000644](../git-20261113-abc894b6-m000644/README.md); its README documents the source, conversion, artwork and evidence.

Every review decision item is kept at its candidate default and the copy stays as printed. The source issues are recorded in the engineering PR and in `source_concerns` of [source/transcription.json](source/transcription.json).

Replay the approved `web/en/manual.ir.json` with the existing `tools.web.frozen_ai_web.replay_package` function. The retained candidate renderer and extraction scripts are historical recipes; their candidate-only approval guard is retained and is not the release replay entrypoint.

`source/release_approval.json` binds the directive and the candidate hashes. `evidence/release_derivation.json` proves the unchanged body, assets, CSS and Markdown. The non-serving shared-style audit JSON is kept byte-identically in `evidence/publish_shared_style_admission.json`, outside the locale delivery root, so the assembler copies the serving inventory exactly (`evidence/publish_packaging.json`). Historical preparation and QC receipts keep their original candidate status. The current publication authority is `frozen_source_manifest.json`. No table, queue or global asset-registry writes are part of this release.

**Edition:** Operator 2026-11-13: 「JS-100F：这本是墨西哥版= 和美规共用」. The booklet is a shared US/MX edition, published as US/en with the copy as printed.
