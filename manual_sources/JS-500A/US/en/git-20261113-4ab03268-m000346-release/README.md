# JS-500A US/en - authorized Git-only release

Approval: MA-438, operator publication instruction dated 2026-11-13 (「全部你都照写上线 问题可以记录在pr里」). Every operator decision D1–D9 stays at its default and the copy stays as printed; the decisions and the source issues kept for the source owner are recorded in PR #1718.

This immutable copy preserves all reviewed native pages, the original PDF, tables, artwork and shared styling of the candidate at [git-20261113-4ab03268-m000346](../git-20261113-4ab03268-m000346/README.md). Only release approval and source-identity metadata change. The Web body starts at TECHNICAL PARAMETERS; the shared booklet's cover facts (model JS-85A, version JAK-UM-V1.0) remain in `source/transcription.json` `cover_facts` and the manifest only.

Replay the approved `web/en/manual.ir.json` with the existing `tools.web.frozen_ai_web.replay_package` function. The retained candidate renderer and extraction scripts are historical recipes; their original candidate-only approval guard is retained and is not the release replay entrypoint.

`source/release_approval.json` binds the directive and candidate hashes. `evidence/release_derivation.json` proves unchanged body, assets, CSS and Markdown. The non-serving shared-style audit JSON is kept byte-identical in `evidence/publish_shared_style_admission.json`, outside the locale delivery root, so the assembler copies the serving inventory exactly. Historical QC receipts retain their candidate status. The current publication authority is `frozen_source_manifest.json`; no table/queue writes or global asset promotion are part of this release.
