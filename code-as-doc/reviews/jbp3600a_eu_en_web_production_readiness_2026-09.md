# JBP-3600A EU/en Git-only Web release readiness

Date: 2026-09-06

Target: `JBP-3600A / EU / en` (`HTP011`, Jackery Battery Pack 3600)

Engineering content baseline: `9b356ecadfe355aae0eb474ef4c49bf168a01e4c`

Formal source commit: `3609e42f4a506870c250b40172c77029c3689ed1`

Final release build Git ref: `359c7edc833d659aaf78e0b128eea595c3ce58e4`

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
| `data/asset_recipes/manual_jbp3600a_eu_web.json` | 16 source assets, 25 semantic outputs, including the JBP-specific LCD hero override | `89db92842423a202701493b76ae954d3308d5be8572589fc649a9c32e975c591` |
| `docs/renderers/web/jbp3600a_eu_en_illustrations.json` | eight source-page full-panel bindings | `b4e72a782d9acb6d88a133e53ef445695c375c346371fe0b2ae24e6ce0da47d4` |

The formal build reads
[`manual_sources/JBP-3600A/EU/en/phase2`](../../manual_sources/JBP-3600A/EU/en/phase2),
not `tests/fixtures`. Its
[`source_manifest.json`](../../manual_sources/JBP-3600A/EU/en/source_manifest.json)
locks 24 target/shared input files with inventory SHA-256
`b3f0f0021a85e5fa6a0b8bd0bce0a68bf49d8806105af74bac72d5c70a5ecc56`.
The target-local `.gitattributes` pins all formal CSV inputs to LF; a detached
clean checkout confirmed both the attributes and the raw manifest hashes.
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

The exact 45-page published PDF was also re-downloaded and rendered. Page 45
visibly states that Jackery Battery Pack 3600 with Bluetooth and Wi-Fi,
JBP-3600A, is covered by the RED declaration. That wording is therefore
published-manual authority and is retained even though the separate 10-page
Illustrator source does not contain the EU tail.

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
| LCD hero | JBP-3600A override `5e793d99`; percentage and charging icon only |
| Cold replay | passed with `.rst` and `.csv` reads denied |
| Tamper rejection | a changed packaged asset was rejected |
| Finished-panel policy | 5/5 |
| Desktop 1440 × 900 | 21/21 images, 0 px overflow, 3 inbox cards |
| Mobile 375 × 812 | 21/21 images, 0 px overflow, 3 inbox cards |

Core output hashes:

| Artifact | SHA-256 |
| --- | --- |
| Generated MyST manual | `dec447799ba563640061d77fa2a11e5534b478ed04aee3ac7dc01e84db9a1c79` |
| `manual.ir.json` file | `6360e8b42b19424137f42ff74078ef764bd230e3fbd11cfd501526d83b1ac67d` |
| IR content | `7c63e9a22bf065a50137e136f9654ed61049f4c15cffee77f4fa627132788199` |
| IR bundle | `63dbc0bccd6ad521786e2bf58dcd6a6587971464b2396f67548023977c60f67c` |

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
`359c7edc833d659aaf78e0b128eea595c3ce58e4`, and an empty
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
/tmp/jbp3600a-git-publish-20260907-final-main/candidate/docs/publish
```

| Output | Result |
| --- | --- |
| Inventory | 73 files plus `publish_manifest.json` |
| Publish manifest SHA-256 | `f72c5e1377051c217a2cf597421906d78ba4504c27d6d2bdd73d5d05bb86a28c` |
| Candidate ZIP | `/tmp/jbp3600a-git-publish-20260907-final-main/jbp3600a-eu-web-publish-candidate-final-main.zip` |
| Candidate ZIP SHA-256 | `8e4eeb18d9a5b2aa86f455cb64295724146ad88288512d9bc567a9d304f92cc5` |
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
