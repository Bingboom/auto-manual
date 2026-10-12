# JE-1000F EU: four new Web languages from the nine-language AI

Status: active

## Scope

The requested increment is **uk (Ukrainian), pt, nl, and pl**. The already
published en/fr/es/de/it v2.7 editions are preserved byte-for-byte. A local
nine-language shell was useful to check source page mapping and navigation;
it is not the release candidate and must not replace the five existing books.

## Authority and baseline

- Designated source: DingTalk first-row JE-1000F / HTE153 attachment
  `HTE153-EU-9国语言-0923.ai` in the operator-provided table. Downloaded exact
  bytes are 67,836,099 bytes, SHA-256
  `c38415f5c2d96832119105d963737a10901e470f70c5e7518ef6404f83625eb2`.
  This is a PDF-compatible Illustrator PDF/X-4 file with 161 physical pages.
  The source record labels it `最新`; that label does not establish approved
  paper version or publication approval. Do not substitute JE-2000F or the
  older JE-1000F six-language review bundle.
- Engineering source branch: `feat/web-je1000f-eu-four-languages`, based on
  `origin/main` at `9122b958` on 2026-09-27. The earlier nine-language shell
  was exploratory and is not the release input.
- Existing `configs/config.eu.yaml` names six languages while
  `data/model_languages.csv` currently names five for JE-1000F/EU and says
  Ukrainian is absent. The current **published** source is more specific:
  Hello-Docs `main` at `6d71003a7fcc0b8852cda02880a592830cc3e763`
  records exactly en/fr/es/de/it as JE-1000F/EU single-language v2.7 targets.
  Their five canonical RTD URLs returned HTTP 200; uk/pt/nl/pl returned 404.
  The existing five source inventories are pinned in
  `je1000f_eu_existing_five_baseline_2026-09.json` for non-regression.
- The source inventory identifies nine 17-page bodies: en 8-24, fr 25-41,
  es 42-58, de 59-75, it 76-92, uk (Ukrainian) 93-109, pt 110-126,
  nl 127-143, pl 144-160. The source uses `UA` for Ukrainian, not a UK
  market. Physical page 1 is the cover, 2-4 contain multilingual prefaces,
  5-7 the contents, and 161 the common declaration/contact tail.
- The EN PDF-compatible text layer omits printed copy on multiple pages.
  That finding does not transfer to the four new languages: all 68 body pages
  contain selectable text. Native text frames and 84 page crops plus 28 paired
  pictogram crops passed the source extraction and crop-boundary audit. The
  original AI remains the visual authority because the local Illustrator
  installation reports missing fonts during export.

## Existing outlet

The supported Git-only route is frozen target source and hash inventory, local
Web build to MyST and strict Sphinx HTML, an isolated release record, then the
existing `publish_branch_assembly.py` outlet into Hello-Docs `docs/publish`.
The requested completion includes a four-language `docs/publish/**` content PR
and, after an authorized merge, RTD route verification. It does not include
online-table writes, source schema, dependency, or workflow changes. The
existing five target sources, figures, and URLs must remain unchanged.

## Local candidate status (2026-09-28)

The source extractor produced 21 locale-page crops plus seven individually
paired pictogram crops per new language from the exact AI, with per-file
hashes. A source-local adapter builds selectable MyST/HTML from direct AI text
objects and geometry; the LCD, symbol, troubleshooting, specification,
warranty, App and operating tables/lists are structured. The original nine-
language shell remains excluded from release. The candidate contains only four
new language targets. Its 276 input files are inventoried by SHA-256.

| Language | Content | Figures | Local build | Browser | Publication |
| --- | --- | --- | --- | --- | --- |
| uk (Ukrainian) | 13 chapters, structured dense regions; approved source erratum recorded | 21 source-page crops + 7 icons; crop QA passed | Strict Sphinx passes; 28/28 image paths exist | Portal review passed; approved errata rechecked | Not published |
| pt | 13 chapters, structured dense regions | 21 source-page crops + 7 icons; crop QA passed | Strict Sphinx passes; 28/28 image paths exist | Portal review passed; approved errata rechecked | Not published |
| nl | 13 chapters, structured dense regions; approved source erratum recorded | 21 source-page crops + 7 icons; crop QA passed | Strict Sphinx passes; 28/28 image paths exist | Portal review passed; approved errata rechecked | Not published |
| pl | 13 chapters, structured dense regions | 21 source-page crops + 7 icons; crop QA passed | Strict Sphinx passes; 28/28 image paths exist | Portal review passed; approved errata rechecked | Not published |

Four-language candidate source: `manual_sources/JE-1000F/EU/nine-language/git-20260927-c38415f5/four-language/web`; local served HTML:
`/tmp/je1000f-four-candidate/html`. Each local page has a locale root HTML
attribute. A provisional 58-target Hello-Docs assembly and strict portal
Sphinx build passed. The five existing JE-1000F/EU source subtrees matched the
Hello-Docs main baseline file by file. Formal release evidence must be sealed
against the final remote engineering commit after the source errata decisions;
the Hello-Docs PR, merge, and RTD acceptance remain separate gates.

## Implementation phases

### Confirmed source errata, 2026-09-28

The operator approved the two source errata with “可以按这个处理 这个 错误会记录的吧？”.
The next bounded change records them in `four-language/source/errata.json`:
the Ukrainian USB-C sentence on physical page 99 uses the already verified
Ukrainian template wording; Dutch AC labels on physical pages 129, 135 and 142 are
corrected using the original AC button faces and the reviewed image candidate.
The raw extraction and `figures/nl/p142_app_control.png` stay immutable. A
separate corrected image and its hash are used only by the Web renderer.

Verification proceeds from exact source/hash assertions and generated-content
comparisons to four strict Sphinx builds, the frozen-evidence focused tests,
and the assembled portal browser review. MA-195 covers only #1315 and its
four-language Hello-Docs publication. Final receipts bind the remote source
commit and version `git-20260927-c38415f5`; all five existing source trees and
all unrelated targets are compared before publication.

1. **Baseline:** pin Hello-Docs main, the current publish manifest, and the
   five existing source inventories. Require a four-target additive diff.
2. **Four-language source:** reconcile uk/pt/nl/pl pages, tables, warnings,
   source figures and gaps against the exact AI; retain physical-page refs.
3. **Frozen Web input:** package each new language with independent,
   selectable/searchable text and source-matched finished illustrations.
   Keep the Illustrator binary in the existing archive pattern rather than
   placing an oversized binary directly in the Web tree. Record hashes and
   any excluded/normalized source material in `source_manifest.json`.
4. **Build and navigation:** use the existing MyST/Sphinx and Web styling
   outlet. Give each new language chapter navigation and locale access through
   the existing portal, with verified routes. Keep figures responsive and text
   outside whole-page screenshots.
5. **Verification:** check source hashes and section/figure counts, run strict
   Sphinx, verify every local asset URL, inspect desktop and phone widths in a
   browser, and run applicable repository validation. Assemble only four new
   targets over current Hello-Docs/main `docs/publish`; verify the five pinned
   source inventories are unchanged and open the content PR for review. Merge
   only under the repository's live authorization protocol, then verify RTD.

## Safety net and limits

- Before editing target content, compare a representative existing frozen Web
  target's MyST/Sphinx build shape and record the target-specific expected
  sections from the designated AI inventory.
- Baseline probe: the existing, older Hello-Docs JE-1000F/EU/en frozen MyST
  package built with `python -m sphinx -W -q -b html` into an isolated
  `/tmp/je1000f-web-qa/baseline-old-en-html` directory. This proves the local
  Sphinx toolchain and package shape, not that its content matches the new AI.
- Shared Web renderer work belongs to PR #1310; report any shared defect to
  its owner instead of changing its code in this branch.
- Keep every generated file under an isolated staging root. Preserve existing
  `_build`, review, and release outputs.
- A successful local HTML build is an engineering candidate only. The source
  record's `最新` status does not establish paper-version or publication
  approval. PR merge, RTD build, and live browser acceptance are separate.
