# JBP-2000B JP R3c native IDML validation (2026-09)

**2026-09-04 design Mac / 2026-09-05 UTC: native engineering acceptance
complete, with the explicit debt below.** R3 was opened from the portable
handoff package, saved, closed, reopened and exported by InDesign. All twelve
physical pages were reviewed. This is evidence for the main PR, not a claim
that product facts, asset approval or legal release approval have been signed.

## Scope and lineage

PR #1027 merged first into `feat/bp-jp-target-onboarding` as `fe25a8f8`.
PR #1028 was retargeted to that branch before the parent branch was deleted,
aligned with the new base, and merged as `2c6315ff`. Both had all 17 checks
successful on their final heads, with no unresolved review threads or
changes-requested reviews. No force push was used.

R1 used the exact #1028 freeze. The first native export passed its mechanical
gates but visual inspection found defects; it was never accepted as the final
book. A later `build.py idml` preparation cleaned that first export directory.
R1 was rerun from the unchanged frozen input, and all subsequent evidence was
archived outside the build target so another build cannot remove it.

The source snapshot was copied locally, without a live Base write. Before any
renderer edit, a rebuild differed from the freeze in 15 XML members, exclusively
in `LinkResourceURI` paths; every other member byte and all visible story
content matched. R3 changes nine source IDML members for the fixes below.
Packaging changes only link URIs and collects their files. It does not alter
story copy or geometry.

All paths below are relative to this checkout. Evidence root:
`.tmp/native-acceptance/`. Current extracted candidate: `r3/`.
`r3/acceptance_inputs.json` records the 77 snapshot-file hashes and reference
PDF SHA; `artifact_manifest.json` records the input and native artifact hashes.

| Package | Members / spreads / stories | Member-name + content SHA-256 |
| --- | --- | --- |
| Original freeze, `r1/manual_jbp2000b_jp.idml` | 107 / 12 / 88 | `a7cc780f2fb6a6ce299cec6cb7027df8b08ec8c2810b0473165a0b5eefd7ebf1` |
| R3 source, `source_r3.idml` | 107 / 12 / 88 | `91d726cc302fe6613c4b128c2f3dc98263e796bfeaf6aa8d6c07055ba91019be` |
| R3 packaged, `r3/manual_jbp2000b_jp.idml` | 107 / 12 / 88 | `7feafa1a114289641a33b9bf027fb1641a41705697b64f11f7d727f95130bb0c` |

The handoff carries 31 linked assets, zero missing packaged links, seven OFL
font files and their license. Gilroy is available on this licensed design Mac;
no commercial font file was copied into the package. This run does not prove
that a different host without Gilroy produces the same typography.

## Native result

```bash
python tools/indesign_finalize.py \
  --idml .tmp/native-acceptance/r3/manual_jbp2000b_jp.idml \
  --indd .tmp/native-acceptance/r3/manual_jbp2000b_jp_r3.indd \
  --pdf .tmp/native-acceptance/r3/manual_jbp2000b_jp_r3.pdf \
  --report .tmp/native-acceptance/r3/finalize_report_r3.json
```

| Native gate | R3 measured result |
| --- | --- |
| InDesign version | Adobe InDesign 2026 **21.0.1.6**, committed pin matches |
| Pages / stories, including reopen | **12 / 88** |
| Overset stories / nested table cells, including reopen | **0 / 0** |
| Missing fonts / PDF missing glyphs / bad links | **0 / 0 / 0** |
| PDF glyph validation | pass, zero replacement or `.notdef` glyphs |
| PDF standard | **PDF/X-4**, independently validated after export |
| Output intent / condition | **Japan Color 2001 Coated / JC200103**, both match |
| Japanese font rebind | 3,196 characters; Bold 346, Medium 69, DemiLight 1,255, Regular 1,526 |
| INDD SHA-256 | `fbff4844a6d7f0ec762b73d429a9515babb4d08b206d470dd925fc33b805b71e` |
| PDF SHA-256 | `06e154ec8fee3d10c363e92dc3c58fa7083c183eb8d1b50b59867dd3801b9c33` |
| Finalize-report SHA-256 | `cc6e4963f33dfdddc79d7d2fba31042902530d0888050d7763ca8517135d9034` |

## Repairs verified in native output

| Finding in R1 | Change and measured closure |
| --- | --- |
| Japanese headings become Regular even when the IDML requests Bold | The finalizer preserves each character's original face during portable-font rebinding and stops if a required face is unavailable. Native PDF `目次` changes from HBManualSansJP-Regular to HBManualSansJP-Bold; the report records all four weights. |
| Single-column TOC leader lines sit below the text | Use the paragraph's native tab leader and remove the separately positioned lines. All ten entries and folios align in R2/R3. Multicolumn TOCs retain their existing geometry. |
| `ソーラー充電` and `（別売）` wrap inside a single-line heading/pill | The shared width estimator reserves one em for wide/fullwidth glyphs while retaining the Latin advances. Both strings fit on one line in R2/R3. |
| Empty specification group title emits an orphan circle | Omit the entire empty section heading and its marker; all eleven table rows remain. R2/R3 has no circle between `主な仕様` and its table. |
| Warranty lists add a bullet before source numbering or nested dashes | Preserve the source marker once, with the existing hanging-tab layout. R3 pages 11/12 contain single numbered/dash markers. R3 native rasters for pages 1–10 are byte-identical to R2 rasters at 180 dpi. |

Regression checks execute the actual font-rebinding JavaScript with a simulated
InDesign face reset, cover missing-face failure, and exercise actual TOC,
specification and warranty rendering. Final local suite: **3,564 tests passed,
2 skipped**. Ruff, mypy (`tools/utils`, 14 files), maintainability guardrails,
and BP-JP / JE-1000F-US / JE-1000F-JP build checks passed. Documentation link
validation accompanies this evidence change.

## Twelve-page visual ledger

Page means the **physical PDF page**, not the source-template index. R2 was
inspected on all twelve pages; R3 pages 11/12 were inspected after the marker
repair and pages 1–10 were proven raster-identical. Reference and R3 renders
are in `r3/reference_pages/` and `r3/pages/`, at 180 dpi. The paired overview is
`r3/twelve_page_reference_vs_r3.png`.

| Physical page / printed folio | Role | Result and observation |
| --- | --- | --- |
| 01 / — | Cover | Pass: JP Battery Pack 2000 / JBP-2000B cover, product illustration and contact information visible. Cover remains placed artwork. |
| 02 / — | Contents | Pass: ten entries, correct `01–10` range, Bold title, Medium entries, native leaders and right-aligned folios. |
| 03 / 01 | Safety + signal definitions | Pass: eleven safety bullets, section capsule and four signal rows visible and legible. The older claim that the reference has no safety list is incorrect. |
| 04 / 02 | Symbols | Pass: seven symbol rows, captions and enclosing shell fit; native symbol-shell fitting records one adjustment. |
| 05 / 03 | In-box + product overview | Pass: three supplied-item cards, notice panel, front/rear controls and callouts visible. Shared styles retained. |
| 06 / 04 | LCD + operation | Layout pass; product-fact debt D1 retained by operator instruction. LCD table and both operation panels fit. |
| 07 / 05 | Connections, first page | Layout pass with asset annotation follow-up D2: prose retains the 20 cm ventilation clearance; the figure lacks its reference label. |
| 08 / 06 | Connections, second page | Pass: correct/incorrect stacking diagrams, caution text, lock/unlock steps and resulting connection diagram visible. |
| 09 / 07 | Charging | Pass: AC/solar diagrams and cable labels visible; solar title and suffix pill remain on one line. |
| 10 / 08 | Troubleshooting + specifications | Pass: all 13 error rows and 11 spec rows present; no orphan group marker, clipped row or overflow. |
| 11 / 09 | Warranty, first page | Pass: lead and five sections readable; numbered items no longer receive extra bullets. Retained shared leading is not a new reference-matched measurement. |
| 12 / 10 | Warranty, second page | Pass: service/disclaimer sections and contact rows readable; numbered and nested markers occur once. |

The approved PDF is a structural/style-role reference, **not geometry to copy**
(the operator's #1015 ruling). Shared spacing or type-size differences are not
silently promoted to new JP-only tokens. This is not a pixel-parity claim or a
human product/legal sign-off.

## Explicit debt and next boundary

| ID | Debt / owner | Current treatment and closure evidence |
| --- | --- | --- |
| D1 | Power-button behavior / product owner | Current structured source says short press on, hold 3 seconds off; the reference PDF places these actions oppositely. Operator: “开关机操作与参考 PDF 相反，这个你直接做 保留债务就行” (2026-09-04). Retain the current source, record the conflict, and proceed with engineering review. Close only with a device check or approved product specification and matching source update; it is not a verified product fact. |
| D2 | Figure clearance annotation / asset + document owner | Reference physical page 7 has `≥ 20cm`; the current figure has no label. Adjacent warning text explicitly retains at least 20 cm. Restore a source-backed editable callout or approved asset in a focused follow-up; no safety requirement was deleted from the prose. |
| D3 | Warranty lead height / shared layout owner | `lang_jp_idml_warranty_lead_height=40` remains a candidate allowance, not a measured reference value. |
| D4 | Warranty section allowance / shared layout owner | `lang_jp_idml_warranty_panel_height_adjust_7=5.5` remains declared compensation. Its retirement needs a shared budget/render investigation and sibling native evidence, not another JP-only constant. |

The next review is the **whole JP line into main**. Keep product/legal/asset
approval status explicit; this evidence does not promote `production_eligible`.
Public IR, Web and data-reading work must start from the same merged main SHA,
in separate worktrees, after that PR lands. No implementation of those three
workstreams was added during this acceptance round.

## Digest method

Two digests, because the raw one pins the machine as well as the book.

**The raw digest is not portable.** All 25 `LinkResourceURI` values in a built
package are absolute `file:///` paths into whatever checkout produced it, so the
same book built from a different worktree gives a different raw digest. That is
the "15 XML members differing exclusively in `LinkResourceURI`" recorded under
Scope and lineage: 15 of the 107 members carry a link URI, and normalising it is
exactly what makes the remaining comparison meaningful.

Use the **portable** digest to answer "is this the same book"; use the raw one
only to compare two artefacts produced on the same host.

```python
import hashlib, re, zipfile

LINK = re.compile(rb'LinkResourceURI="[^"]*/([^"/]+)"')

def digests(path):
    raw, portable = hashlib.sha256(), hashlib.sha256()
    with zipfile.ZipFile(path) as package:
        for name in sorted(package.namelist()):
            blob = package.read(name)
            raw.update(name.encode()); raw.update(hashlib.sha256(blob).digest())
            normalised = LINK.sub(rb'LinkResourceURI="\1"', blob)
            portable.update(name.encode())
            portable.update(hashlib.sha256(normalised).digest())
    return raw.hexdigest(), portable.hexdigest()
```

### Which digest a rebuild should match

| Rebuilt from | Expect | Note |
| --- | --- | --- |
| current `main` | portable `0da6b51929d7030013460f7d863c4b13f650fe008533b3bcb912972f0c1533b1` | measured on `main` `f36711bf`; the raw digest on that host was `a0587ff5aa1db7197dd361621b5e99cc8804c9ce1b942377300e611f2ed2fc43` |
| the R1 freeze `a7cc780f…` | **will not reproduce, and should not** | R1 was the input to the native round, not its result. The five repairs verified above changed nine members: the TOC spread and story, the charging story, the specification story, and five `warranty_ja` stories. A rebuild that still matched `a7cc780f…` would mean the repairs are missing. |

`#1037` was checked against this and changes nothing here: JP rebuilt on either
side of it is identical member for member, 107/107, zero changed.
