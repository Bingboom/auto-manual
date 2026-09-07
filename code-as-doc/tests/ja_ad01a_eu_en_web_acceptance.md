# JA-AD01A / EU / en Web acceptance — 2026-09-06

Engineering candidate is ready for review. This batch uses Git-frozen structure
and assets followed by a docs/publish snapshot PR and Read the Docs. No online
Bitable writes or build queue are required or permitted. Source authority is the user-designated intake AI; formal RTD deployment
remains pending. The current printed-manual version is unknown.

## Scope and baseline

- Current main verified after fetch: `9b356ecadfe355aae0eb474ef4c49bf168a01e4c`.
- Migrated the sole target commit `a32abf055bae8445868cbbc55dcaeb144d11183c`
  into independent branch `codex/web-ja-ad01a-eu-en-closeout`; the original
  worktree was not edited. No pre-existing PR was found for the old branch.
- The branch wrapper was attempted but could not switch to main because another
  worktree owns it. Created this branch directly from fetched `origin/main` in
  the clean independent checkout.
- Reuses merged shared IR/Inbox/asset-copy/navigation work; no shared Python,
  CSS, workflow, JP or IDML implementation changed. Registry/family test counts
  include both existing Solar/BP additions and these five charger assets.
- The charger family has seven content blocks: Inbox, overview, specifications,
  usage, warning, warranty, legal tail. No LCD, UPS or App chapters.

## Source and live business evidence

[Exact intake view](https://alidocs.dingtalk.com/i/nodes/YndMj49yWjP03jNjCDojvAQdJ3pmz5aA?entrance=data&sheetId=97v7518&viewId=xWo5UbG)
was read live, including a second selected-field read of record `xG4bYnERxR`.

- `Ai文件` / `Lklgsec`: resource
  `ea84efd5-f2a9-43fc-ba19-16788f488cf3`, 918848 bytes.
- Filename: `(翻译用）38-0001-000880 HTO847-EU-JAK 102W充电器 说明书 RoSH REACH.ai`.
- Local byte recomputation: SHA256
  `0252cb5db68fb67b3fe0947824de4655e13e26f90b3dde1f6bada3b64aa390fc`.
  This matches the cached downloaded file and recipe, rather than the typo in
  the initial task prompt. The existing cache was hashed; no fresh download
  is claimed in this closeout.
- `当前纸质说明书` / `W7Skax1`, `文档业务` / `MqRDuc9`,
  `发布资料（自动）` / `O3QP6wT`, `当前说明书 副本` / `OSqfpzv`,
  `英文文案` / `cLWX441`, `当前说明书料号` / `UHqmpJp`: absent in readback.
- `是否有说明书` is a lookup containing “最新说明书”; this label alone does
  not establish a published version or authoritative file link.
- Feishu published-manual catalog: skill query and direct full-table read,
  45 records, no JA-AD01A/HTO847 match. DingTalk `05-01-发布资料` (`6yVXdVK`)
  keyword queries for both codes returned zero records.
- Business Base `LD3lb4G1ua4GOVs1vxAc9W2enje` was queried with the configured
  bot profile `cli_aaa0db0d4b39dcca` (this machine has no `prod` alias).
  Exact field shapes were read before filters were composed. The target
  Document_key, queue Document_ID, spec and placeholder document_key queries
  each returned zero rows with `has_more=false`. Asset source model/hash and
  definition/export asset-key queries also returned zero rows. These are
  explicit query results, not a claim about undiscovered aliases.
- No live source-table, attachment, queue or publication-link writes occurred.

The user designated the intake AI files for this batch. Since no conflicting
current published source was identified, this exact AI is the authorized Web
input; another adoption approval is not required. If a current published source
is found, it takes precedence where it overlaps; no historical comparison is
requested. The [source candidate](ja_ad01a_eu_en_source_candidate.json)
contains the 21 specification lines and five assets for content review, plus
historical read-only query results. They are not online ingestion prerequisites.
The six CSVs were moved unchanged into `data/manual_sources/ja_ad01a_eu_en`;
`source_manifest.json` locks their bytes plus target templates, config, manifest
and assets. The technical snapshot version is `git-20260906-0252cb5d`, derived
from the source hash; no historical paper version is invented.

AI pages 4-5 (power profiles), 7-8 (all warning items and 24-month warranty),
and 9 (legal contacts) were rendered and visually reviewed in this closeout.
The source’s malformed extracted DC glyph is normalized to ⎓, without changing
voltage/current numbers. Paper cover/contents/page numbers and the unverified
QR destination are excluded; warning item 11 also appears as Inbox TIP.
Source limitation: the AI filename contains “翻译用” and no independent current
printed version is identified. This does not block the user-designated Web
conversion. Empty online links do not block Git publication.

## Acceptance checklist

- [x] Target migration preserves merged shared work and existing manifest anchors.
- [x] Runtime `build.py md` invokes the charger config with EU/en and isolated
  Git release inputs. Real Pandoc conversion and `sphinx -W -b html` pass.
- [x] Seven blocks produce `whole-document-components/v1` IR.
- [x] Three-card `HB-SPECIAL-INBOX` with TIP and `HB-CALLOUT-STRIP` warning
  are present in actual runtime IR; warning retains all 11 list items.
- [x] Four native specification tables preserve 21 structured source lines:
  single C1/C2 100W profiles, USB-A 18W, the distinct C1+C2 and C1+A profiles,
  C2+A shared 5V/3A, triple C1 20V/4.35A plus C2+A 5V/3A, and all PPS lines.
  Total product power is not substituted for each port.
- [x] All five actual image URLs are bound in the illustration manifest and
  match file hashes. Two finished diagrams retain their product labels;
  Inbox pictures are assets inside native cards. No full-page screenshot is
  used as content and no Web illustration is made textless.
- [x] Relocated serialized IR replays seven fragments while `.rst`, `.csv`
  and renderer-contract reads are denied. Packaged-asset tampering is rejected.
- [x] Final Sphinx HTML: all five image URLs resolve to files; Chrome loads all
  five at 1440px and 375px. Zero broken images and zero whole-page overflow.
  Mobile specification tables retain local horizontal scrolling; they do not
  force the document wider than the viewport. Screenshot visually inspected.
- [x] JE-1000F EU frozen-review regression: 76 fragments, 340 images, five-language
  anchors, cold replay and tamper rejection, real Pandoc/Sphinx, both viewports
  with zero broken images and whole-page overflow.
- [x] Full unit suite: 3855 tests pass, 22 skipped. Target suite: 8 pass.
- [x] Ruff, maintainability guardrails, document links, JA target check and
  JE-1000F US/en baseline check pass. Mypy also passes all 16 utils files;
  its missing local dependency was installed only into the isolated evidence
  directory, without changing project dependencies.
- [x] User-designated intake AI authority established for this Web batch;
  paper version remains unknown, not fabricated.
- [x] Exact Git structure source, source hash and asset manifest prepared; no
  online tables are written.
- [ ] Engineering PR centrally reviewed and merged; mirror sync verified again.
- [ ] Git-frozen release bundle centrally combined into Hello-Docs snapshot PR.
- [ ] `docs/publish/**`-only snapshot PR merged and real RTD URL verified.
  No online release-link field writeback is performed.

## Reproduction and evidence

Use the existing Python 3.12 environment (system Python 3.9 is not supported).
Run from repository root; `$PY` below means that environment's Python.

```bash
export AUTO_MANUAL_PRESENTATION_PROFILE=web
$PY build.py check --config configs/config.charger-eu-en.yaml --model JA-AD01A --region EU --lang en --data-root data/manual_sources/ja_ad01a_eu_en --staging-root /tmp/ja-ad01a-closeout/check
$PY build.py md --config configs/config.charger-eu-en.yaml --model JA-AD01A --region EU --lang en --data-root data/manual_sources/ja_ad01a_eu_en --staging-root /tmp/ja-ad01a-closeout/staging
$PY -m sphinx -W -b html /tmp/ja-ad01a-closeout/staging/docs/_build/JA-AD01A/EU/en/md /tmp/ja-ad01a-closeout/html
$PY -m unittest
$PY -m ruff check build.py integrations tools tests scripts
$PY tools/check_maintainability_guardrails.py
$PY tools/check_doc_link_integrity.py
$PY build.py check --config configs/config.us-en.yaml --model JE-1000F --region US --data-root tests/fixtures/phase2 --staging-root /tmp/ja-ad01a-closeout/us-check
```

JE regression uses frozen review `7d764e22c3050103d59e96268dc43ac9f181a1c9`,
not generic runtime fixtures or current live data. The review files were copied
into this independent checkout for the run, then preserved outside the checkout
at `/tmp/ja-ad01a-closeout/frozen-je-review`. Its exact data-root is
`/tmp/web-stage-je-source`. Command: `build.py md --config configs/config.eu.yaml
--model JE-1000F --region EU --source review-asis --data-root
/tmp/web-stage-je-source --staging-root /tmp/ja-ad01a-closeout/je-regression`.
The first attempt with the main checkout's current attachment cache failed
closed on ambiguous WEEE aliases; selecting the accepted frozen cache resolved
it without code changes or resetting hashes.

[Tracked measurements](ja_ad01a_eu_en_web_evidence.json) include every JA final
image URL. Full JE/JA image URL inventories, browser results, screenshots and
command logs are preserved in `/tmp/ja-ad01a-closeout/`. Browser script:
`browser.cjs`; machine-readable data: `verification.json` and `browser.json`.
The local preview at `http://127.0.0.1:18779/html/manual_jaad01a_eu_en.html`
is an engineering candidate, not the formal site.

## Git-only formal publication handoff

The earlier Bitable/queue prerequisites are superseded by the operator’s updated
instruction. No staging/source/asset/build/link table writes are permitted.
The `hello-docs-pipeline-dispatch-triage` skill supplied mirror/snapshot boundaries;
its queue-driven forced sync is not used in this batch.

Read-only readiness snapshot: Hello-Docs main
`f6df757e601ef505446828118b2d3aa272822be6` mirrors engineering `9b356eca`.
Its complete recursive tree contains no JA target snapshot. No open `publish`
PR was present. These facts must be refreshed by the central publisher.

Existing `tools/publish_branch_assembly.py` accepts a local release-root via
`auto-manual-web-publish/v1` metadata at
`JA-AD01A/EU/en/latest/web/publish_meta.json`. This adapter requires a real
verified Markdown package and HTML `index.html`, both inside releases-root;
it does not require any Bitable row or queue. The central task preserves existing
Hello-Docs publications and combines all three targets serially.

- Release-root: `/tmp/ja-ad01a-closeout/releases`
- Independent publish tree: `/tmp/ja-ad01a-closeout/frozen/docs/publish`
- Version: `git-20260906-0252cb5d` (technical Git snapshot of the identified AI)
- Stored source route: `sources/web/JA-AD01A/EU/md`
- RTD route: `JA-AD01A/EU/md/manual_jaad01a_eu_en.html`
- Root alias: `manual_jaad01a_eu_en.html`
- Expected formal alias: `https://ht-doc.readthedocs.io/manual_jaad01a_eu_en.html`
  (expected route only; this report does not claim it has deployed).

```bash
$PY tools/publish_branch_assembly.py --releases-root /tmp/ja-ad01a-closeout/releases --output-dir /tmp/ja-ad01a-closeout/frozen/docs/publish
$PY -m sphinx -W -b html /tmp/ja-ad01a-closeout/frozen/docs/publish/web /tmp/ja-ad01a-closeout/frozen-html
```

`input_manifest.json` in the release-root identifies Git ref, all source inputs,
source authority status and all output hashes. The assembler’s manifest inventories
the resulting Web snapshot. The existing assembler does not copy `manual.ir.json`
or arbitrary sidecars into the site; those remain in the release-root evidence,
while the Git ref and source manifest permit reconstruction. No shared adapter
change is needed for this target’s webpage.

After engineering merge/mirror sync, the main task
owns the docs/publish-only snapshot PR and RTD deployment/URL verification. This
task does not mutate the shared publish branch. A technical package ready for
assembly is distinct from a deployed page.
