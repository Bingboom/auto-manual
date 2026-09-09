# JS-100F EU English Web intake — 2026-09

## Target checklist

- [x] Confirm isolated worktree, branch, clean starting tree and latest fetched `origin/main`.
- [x] Verify `JS-100F / EU / en`, source coordinates and the supplied SHA-256.
- [x] Render the PDF-compatible AI and locate the three-page English panel inside the oversized artboard.
- [x] Map only source-backed chapters; do not inherit JS-100I facts or power-station-only sections.
- [x] Keep specifications, safety, notes and warranty as semantic RST/HTML components.
- [x] Extract only four image-owned diagrams; exclude adjacent prose and whole-page screenshots.
- [x] Replay the approved asset recipe and inspect every crop at 12x.
- [x] Verify the frozen source manifest, target build, cold IR replay and tamper rejection.
- [x] Run strict Sphinx, image/link/secret checks, full required tests and responsive browser review.
- [ ] Build the independent handoff package, merge latest `origin/main`, commit, push and open the PR.

## Authority and target identity

- Target: `JS-100F / EU / en`; product: `Jackery SolarSaga 100`.
- DingTalk Base/table/record: `YndMj49yWjP03jNjCDojvAQdJ3pmz5aA` / `97v7518` / `UH5XSMZwqi`.
- Supplied source: `JS-100F-eu-source.ai`; SHA-256 `2074ddc390cf0e218a94a6ad267721c6f85cb5a34a29c96e45093791602f8952`.
- Illustrator metadata: `Adobe Illustrator 30.0 (Macintosh)`; one PDF-compatible artboard, `5636.82 × 3978.88 pt`.
- English body: three adjacent pages at approximately `x=1712–2861 pt`, `y=600–1120 pt`; cover version `JAK-UM-V1.0`.

The user selected this exact attachment and explicitly waived version
comparison. It is therefore the direct authority for this target. The source
was read locally only; no DingTalk, Feishu or other live table was changed.

## Semantic and image ownership

The target stays on shared `config.solar-eu-en.yaml` and uses a target-resolved
manifest. Native components own Technical Parameters, Safety Tips, How to Use
copy, the cable-compatibility note, Sun Angle prose, Warranty, Contact Us and
Customer Service. The four source crops own only the illustrated DC connection,
solar connector, sun-angle and device-powering diagrams and their embedded
English labels/product markings. No complete page, specification table,
warranty text or surrounding paragraph is rasterized. This model has no LCD,
Inbox, UPS or App chapter.

## Publication boundary

Local build, localhost preview, pushed branch and an open engineering PR are
review evidence only. This task does not write live tables, upload OSS, edit
Hello-Docs, merge the PR or publish a formal Web route.

## Acceptance evidence

| Gate | Result |
| --- | --- |
| Target build/check | Passed from frozen `data/manual_sources/JS-100F/EU/en/1.0/phase2`; six pages, three semantic specification groups, three NOTE boxes and four finished illustrations. |
| Frozen source | Source manifest hashes, aggregate snapshot hash, recipe hash and illustration-manifest hash passed; cold public-IR replay denied `.rst`/`.csv` reads and a changed packaged image was rejected. |
| Asset intake | One-page archive plus four deterministic crops replayed from the supplied AI; all crops were inspected at 12x and matched their declared hashes. |
| Direct Web build | Sphinx 8.2.3 with `-W --keep-going` passed. |
| Shared Web assembly | Target-only `auto-manual-web-publish/v1` release root assembled successfully; the assembled candidate also passed strict Sphinx and contains no print/source formats. |
| Image and identity | Four of four image tags resolve to packaged hash-addressed assets; no JS-100I, Air, LCD, UPS, App, Inbox or missing-placeholder leakage. |
| Browser review | Final full-page screenshots passed at 1440 px and 500 px widths; illustrations stay proportional, NOTE boxes remain semantic and readable, and specification tables retain the shared narrow-screen horizontal-scroll behavior. |
| Repository gates | 27 focused tests and all 3,911 unit tests passed (22 skipped); Ruff, documentation links (178 files, 1,753 links, zero broken), `git diff --check`, registry asset check and gitleaks passed. |
| Base freshness | `origin/main` was fetched immediately before closeout and matched the implementation base `d1eeb282ef871891f8aa65555a4ede29c4bbc1ea`. |
