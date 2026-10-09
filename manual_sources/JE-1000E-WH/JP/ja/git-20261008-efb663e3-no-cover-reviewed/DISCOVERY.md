# JE-1000E-WH JP native Web intake

Source: `Jackery SlimPower H1取扱説明書V2.0-2026-07-29.pdf`, 27 pages,
SHA256 `efb663e3b22fec90bb8d4f602cb830471360034d9ead9293168f708ce937c3be`.
Cover and specification both say JE-1000E-WH; cover says Japan only. Japanese
body is physical pages 3–26 (printed 01–24); cover 1, TOC 2, back cover 27 with native QR.
V2.0/2026-07-29 is filename provenance; no printed version found in PDF text.
PDF metadata says HTE1511000A-JP-JAK and creation 2026-07-28.

No existing JP target package/config was found in the current engineering tree.
US JE-1000E-SIL is a different target. Its shared construction drawings can be
reused only after comparing the JP drawing; US body/labels/specs are not inputs.
Root checkout has foreign tmp/ and is untouched. Managed worktree owns branch
feat/web-je1000e-wh-jp-intake from origin/main. The branch wrapper was attempted,
but cannot switch to main while another worktree owns main; branch creation
used the fetched origin/main directly in the clean managed worktree.

Plan: freeze native text/coordinates and exact glyph recovery; record each
artwork reuse/extraction decision; bind neutral flow and shared ComponentSpecs;
package local assets, manual-ir/v2 and MyST; source/asset checks; cold replay;
strict Sphinx; actual desktop/390px browser checks; engineering draft PR.

Non-goals: phase2 registration, Base/queue writes, asset registry promotion,
merge, Hello-Docs/RTD publication, translation, modifying other source targets.
The existing EU PDF adapter assumes symbol/auto-resume/key-combination chapters
absent from this source, and includes an EU declaration. Reuse its neutral flow,
shared table/media components and public IR consumer, rather than inventing
missing chapters. Candidate admission checks use the exact source chapter map.
Production prepared-component enrollment remains a release-stage obligation
once the operator has reviewed this JP candidate; this is not a release receipt.

Verification: hash/source/line coverage and component contracts; cold IR replay
in a new directory; corruption rejection; strict Sphinx; doc link integrity;
JP build.py check (regression only, JE-1000F); all 17 section anchors, local image
loading and image edges, readable desktop/mobile tables and live labels.
