# JE-3000C EU Dutch approved errata

Operator decision, 2026-10-01: “确认这两项按 AC、8 A 修正，并记录勘误”.

Scope: correct AC-button labels on source pages 122/127/128/134 and combined car input current on 122/132. Preserve DC/USB labels, DC input naming, PV 24 A and all other locales.

Plan: record exact native-field changes before component construction; correct only two localized overview image labels using original PDF glyphs; regenerate Dutch with the existing shared renderer; publish after engineering and release checks. The raw AI and previous frozen package stay unchanged.

Safety net: exact-before matches and approved source hash fail closed, deterministic artwork recipes, rendered source comparison, strict Sphinx and cold replay, unchanged PT/PL and prior six languages.

Validation: targeted errata and native-reference tests; full unittest, Ruff, maintainability and doc links; source/asset inventories; desktop/mobile browser checks.

Workspace: isolated clean managed worktree at a74513acc; branch created directly because the shared main checkout is already occupied. Prior preview worktree and its generated index remain untouched.

Implementation: 14 exact component input fields; two localized overview assets corrected with native glyphs. The page-134 App AC label is the same approved button correction; its selection rectangle also now includes the full initial A.
