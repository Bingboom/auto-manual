# JBP-3600A EU/en Git-only Web release readiness

Date: 2026-09-06

Target: `JBP-3600A / EU / en` (`HTP011`, Jackery Battery Pack 3600)

Engineering content baseline: `9b356ecadfe355aae0eb474ef4c49bf168a01e4c`

Formal source commit: `d25a34eb5f2199d8f414eb682241452b58698662`

Status: **the target-specific Git-only release root and single-target
`docs/publish/**` candidate are generated and locally accepted.** This batch
does not require or permit a live Bitable write. The central release task owns
the shared Hello-Docs candidate, its `docs/publish/**`-only PR, merge and the
formal RTD readback.

The machine-readable handoff is
[`web_git_release_input_2026-09-06.json`](../../reports/source_intake/JBP-3600A_EU/web_git_release_input_2026-09-06.json).

## Authority and frozen input

The current published booklet is the content authority. Its external title says
`JBP-3000A`, while the visible cover/body and Illustrator source say
`JBP-3600A`; the wrong external filename is retained as naming debt rather than
used as the product identity.

| Evidence | Use | SHA-256 |
| --- | --- | --- |
| [Current DingTalk PDF](https://alidocs.dingtalk.com/i/nodes/NZQYprEoWoeAawzwfBwMeb25J1waOeDk), V2.0-2026-08-04 | cover 1; English preface 2; English body 5-12; EU tail 45 | `084dd4517feddcd9b77da10415a2787ec4427f882a7b819160725fdff679ccfe` |
| `16-0102-000334 说明书 HTP0113600A-EU-JAK RoHS REACH.ai`, 10 pages | source artwork and localized full panels | `e0ccc33427f89c77c30d32e073a3027123f4c8a9c9f5029d2378172a7f0a3761` |
| `configs/config.bp-eu-en-web.yaml` | exact target configuration | `be43f160a88d4d25a0b890288e45a45aa12fe0f546b4d17ee8a0b909e66d4dea` |
| `docs/manifests/manual_bp-eu-en-web.yaml` | BP-specific page structure | `f283ab204f1f95b4640dd30e3978d01eb052de0757d33a72cd30fd33506986bd` |
| `data/asset_recipes/manual_jbp3600a_eu_web.json` | 15 source assets, 23 semantic outputs | `68fdf5c93fe9422e531234d264698709b2da81530690c6d8fbe6d972d34d63d1` |
| `docs/renderers/web/jbp3600a_eu_en_illustrations.json` | eight source-page full-panel bindings | `b4e72a782d9acb6d88a133e53ef445695c375c346371fe0b2ae24e6ce0da47d4` |

The formal build reads
[`manual_sources/JBP-3600A/EU/en/phase2`](../../manual_sources/JBP-3600A/EU/en/phase2),
not `tests/fixtures`. Its
[`source_manifest.json`](../../manual_sources/JBP-3600A/EU/en/source_manifest.json)
locks 23 target/shared input files with inventory SHA-256
`aab46b4bc00aed1209ae4c6657c740875548913e7cae0caac21f3b83437c6574`.
The directory contains 21 specification rows, 8 target Symbol rows plus 5
shared signal rows, 2 LCD rows, 7 troubleshooting rows, the eight used Symbol
attachments, and only the shared dictionaries required to render them. Page
structure remains BP-specific; no table normalization, IR redesign or IDML
pagination was introduced for publication.

Live business-plane reads on 2026-09-06 found no matching target rows. That is
inventory context only, not a release blocker. No staging, source, asset, build
or link table was written, and the Git-only release path performs no live sync
or queue writeback.

### Content-authority gaps

The only confirmed authority defect is the external PDF filename's
`JBP-3000A` model string. The visible manual, source-list identity and source
artwork consistently identify `JBP-3600A`, so no operator choice between two
competing manuscripts is required. No missing English body, specification,
warranty or EU-tail source was found; empty online association fields are not
treated as missing content.

## Accepted target build

The latest-main target build used:

```text
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md \
  --config configs/config.bp-eu-en-web.yaml \
  --model JBP-3600A --region EU --lang en \
  --data-root manual_sources/JBP-3600A/EU/en/phase2 \
  --staging-root <fresh-root>

python -m sphinx -W -b html \
  <fresh-root>/docs/_build/JBP-3600A/EU/en/md \
  <fresh-root>/sphinx
```

| Gate | Result |
| --- | --- |
| Target suite | 7/7 passed |
| Real Pandoc build and Sphinx `-W` | passed |
| Public IR | 15 source fragments, 78 blocks, 21 packaged images |
| Cold replay | passed with `.rst` and `.csv` reads denied |
| Tamper rejection | a changed packaged asset was rejected |
| Finished-panel policy | 5/5 |
| Desktop 1440 × 900 | 21/21 images, 0 px overflow, 3 inbox cards |
| Mobile 375 × 812 | 21/21 images, 0 px overflow, 3 inbox cards |

Core output hashes:

| Artifact | SHA-256 |
| --- | --- |
| Generated MyST manual | `38940fef9baf637f625b0cbc58773b445e88c5e14de3965c5796cff0d79f467d` |
| `manual.ir.json` file | `dace88e79704276b78e4395302c1f6090b966f403be635d4cedf5ee321261c10` |
| IR content | `b457050d47835f8b2dee7f77e6ccdbc84428f6710528ec28b9cd0eed5dc5e594` |
| IR bundle | `78b144f79fcc60c38d1bbc111c8acdfbbfe5da97643d40f892381719f1abf0a3` |

## Git-only release-root handoff

The prepared release root is:

```text
/Users/hello-tech-team/.codex/worktrees/7603/auto-manual-codex/reports/releases
```

Its target contract is:

```text
JBP-3600A/EU/en/latest/web/publish_meta.json
JBP-3600A/EU/en/versions/2.0/web/md/manual_jbp3600a_eu.md
JBP-3600A/EU/en/versions/2.0/web/html/index.html
```

`publish_meta.json` uses `auto-manual-web-publish/v1`, version `2.0`, language
`en`, route `JBP-3600A/EU/md`, exact Git ref
`d25a34eb5f2199d8f414eb682241452b58698662`, and an empty
`queue_record_ids` array. It records no live-sync or queue claim.

The central release task can merge this release root with the other prepared
target roots and run the existing assembler:

```text
python tools/publish_branch_assembly.py \
  --releases-root <combined-release-root> \
  --output-dir <hello-docs-publish-worktree>/docs/publish
```

Minimum interface requirements are therefore only:

1. retain `latest/web/publish_meta.json` plus its versioned MyST and verified
   HTML paths;
2. preserve already published targets while adding this route;
3. build `docs/publish/web` with Sphinx `-W`;
4. reject any Hello-Docs PR path outside `docs/publish/**`;
5. do not write a Bitable row or `HTML_link` in this batch.

This target task did not write or push `Hello-Docs/publish`; that shared branch
is deliberately serialized by the central release task.

## Single-target candidate evidence

The existing assembler produced a self-contained candidate at:

```text
/tmp/jbp3600a-git-publish-20260906/candidate/docs/publish
```

| Output | Result |
| --- | --- |
| Inventory | 73 files plus `publish_manifest.json` |
| Publish manifest SHA-256 | `b0c99d0f42d4a2953d098faca26ee45bd51539a90f9cd4d30ee5f07533514448` |
| Candidate ZIP | `/tmp/jbp3600a-git-publish-20260906/jbp3600a-eu-web-publish-candidate-formal.zip` |
| Candidate ZIP SHA-256 | `3609a1c2dd9457dc8961690fad14088773612b89d4f319c1f4d41e196bda91bf` |
| RTD-source Sphinx `-W` | passed |
| Root alias HTML SHA-256 | `d2638eaf2d6a23034fe61b199b5bc1d05959a8639afc47b0cdd5e7eee2f38480` |

The root alias opened locally and forwarded to
`JBP-3600A/EU/md/manual_jbp3600a_eu.html`. The expected formal route is:

```text
https://ht-doc.readthedocs.io/manual_jbp3600a_eu.html
```

That URL is an expected route, not yet a verified production page. Completion
requires the central task to assemble all target roots, open and review the
Hello-Docs `docs/publish/**`-only PR, merge under the normal authorization rule,
wait for the RTD build, and repeat the image and responsive checks on the real
URL.

## Release checklist

- [x] Published PDF/source artwork identity and hashes locked.
- [x] Audited Git structure source and full-panel artwork inputs identified.
- [x] Target MyST, IR, strict Sphinx and responsive browser acceptance passed.
- [x] Queue-free `publish_meta.json`, versioned release root and frozen candidate generated.
- [x] Candidate root alias opens locally; aggregate RTD source passes Sphinx `-W`.
- [x] No live Bitable write, queue dispatch or shared publish-branch write performed.
- [ ] Central task combines target release roots and opens a `docs/publish/**`-only Hello-Docs PR.
- [ ] Authorized merge and RTD build complete.
- [ ] Real RTD URL passes image, content and responsive readback.
