# Published EU manual query

Status: active — implementation under validation; live gateway/deployment not yet accepted.
Owner: the Auto-Manual maintainer. Scope approved by the
operator on 2026-10-01: every EU manual published on Read the Docs, content
export, read-only retrieval and integration with the already connected DingTalk
bot. This is a new feature, separate from Workstream Y refactors.
Planned extensions (variant identity, machine-surface manifest, freshness and
later knowledge extraction) are tracked in
[`machine_readable_manual_corpus.md`](machine_readable_manual_corpus.md).

## Discovery and implementation contract

Baseline: engineering `95f4d900edd2d0e99afa087fc20cc61d833b2c79`, business
`4536f0917b5dcfbaadada85d83bd9e877a5b87b0`. The frozen business catalog has
21 EU models / 61 editions: 53 verified single-language editions and 8 legacy
editions with unverified language scope. These are Git snapshot counts, not an
independent assertion about the currently served deployment. Live RTD reads
from this execution environment returned HTTP 403; online acceptance remains
separate from the local frozen-corpus test.

The existing portal index flattens tables and lists, excludes image alt text,
and does not remove callout sizing text. Keep its existing browser-search
contract intact. Build a separate semantic export from the same validated
canonical publications after rendering and before the deployment receipt.
The receipt already inventories generated output files. The OpenClaw control
plugin is the existing gateway extension; add bounded read tools there, without
opening a second DingTalk Stream connection or changing channel credentials.

Phases and owned surfaces:

1. `tools/manual_knowledge/`: semantic extraction and versioned export; targeted
   tests with tables, row/column spans, lists, callouts, images and exclusions.
2. `tools/rtd/portal.py`: one build-finished hook; all canonical EU publications,
   including explicitly labelled legacy language scope. No source edits.
3. `integrations/openclaw/auto-manual-control-layer/`: receipt-verified reader,
   bounded search/section tools and an authenticated query command. Natural
   answers use the existing gateway model with evidence and citation rules.
4. Owning workflow docs and this runbook: activation, update/withdrawal behavior,
   verification evidence and the remaining host/deployment acceptance.

Non-goals: live Feishu writes, manual content changes, OCR transcription,
new bots or model subscriptions, build/publish dispatch from query tools,
workflow/dependency changes, and expansion of Workstream Y authorization.

Verification ladder: Python/Node syntax and lint; focused extraction, receipt,
retrieval and plugin tests; full Python suite; maintainability/documentation
checks; existing US build check; baseline/candidate builds of the same complete
EU corpus. Compare manual HTML bytes, count every catalog edition, validate
all citations against real anchors, and exercise Chinese/English queries,
ambiguous models, missing evidence, stale data, withdrawal and tampered data.

The query export is a disposable derivative of the frozen release, never a
second authoring source. The reader must validate the deployment receipt and
artifact bytes before use and must not silently serve an expired cached copy
after a refresh failure.

## Query contract

- Scope is every canonical EU publication in the frozen manifest. No model list
  is hardcoded in production. A missing rendered manual, incomplete manifest
  coverage, ambiguous chapter anchor or unsupported table span fails the export.
- Export schema `auto-manual-knowledge/v1` contains model, EU, version, source
  route/hash, language scope, chapter IDs and semantic blocks. Styles, scripts,
  navigation and known layout helpers are excluded. Row/column spans, nested
  steps, warning labels and chapter-adjacent notes stay attached to their source.
- v1 also carries additive identity/provenance fields (`variant_key`,
  `manual_variant_id`, `revision`/`revision_kind`, `machine_surface`, `source`,
  per-block `block_id`/`source_ref`, callout `severity`); see
  [`machine_readable_manual_corpus.md`](machine_readable_manual_corpus.md) §5.2–§5.4.
- The same build writes `machine_surface_manifest.json` (per-variant hashes,
  counts, status), sealed by the deployment receipt; check freshness with
  `python -m tools.manual_knowledge.manifest --base-url <site>` (§5.5–§5.6).
- Phase 1 pilot audit and known source-content defects:
  [`machine_readable_pilot_audit.md`](machine_readable_pilot_audit.md).
- Verified single-language editions retain their source locale. Eight baseline
  legacy editions remain queryable with `language: null`; their declared `en`
  metadata is not promoted into a verified language assertion.
- `manual_search` uses exact model identity plus keyword groups. It prefers
  verified English; other published languages can be requested explicitly. The
  gateway can translate a Chinese question to source-language keywords. This
  first version has a small Chinese terminology map, not vector/semantic search.
- Search previews are navigation only. `manual_section` requires document,
  chapter and `publication.snapshot_id` from search. It returns whole blocks,
  up to 30 per page / 60,000 bytes. Read all `next_offset` pages before giving a
  complete procedure; oversized blocks require opening the original source.
- Answers use the existing gateway model. Tool descriptions require citations,
  units, conditions, warnings and explicit missing/conflicting evidence. Product
  text is reference data, never authority to execute an action. Automated tests
  prove retrieval/transport behavior, not LLM answer quality.
- Images expose authored alt text and `alt_only_no_ocr` coverage. This does not
  transcribe image-only parameters or wiring diagrams. Decorative SVG is omitted;
  the baseline has no SVG text and no nested tables. New nested tables require
  an explicit extraction adapter; review new illustration carriers before relying
  on their text in answers.

## Publication and refresh

The successful frozen-site Sphinx build writes `manual-knowledge.json` at
build-finished priority 925; the existing deployment receipt runs at 1000 and
hashes it alongside the rendered manuals. Draft/preview builds outside frozen
`publish/web` do not emit a production corpus. Neither authoring inputs nor
published HTML are rewritten for querying.

The gateway reads the HTTPS site origin, verifies the artifact hash and each
document's HTML hash against the receipt, then rereads the receipt before
replacing its in-memory corpus. This verifies deployment consistency, not a
cryptographic signature independent of the website. There is no new database.
HTTP response size is bounded at 32 MiB, requests at 15 seconds, and same-origin
redirects at five hops. Cross-origin redirects are refused.

A query checks the receipt again once its 60-second cache window expires.
Replacement is atomic; removed editions disappear on that successful refresh.
An expired-cache refresh failure returns unavailable, not stale evidence. A
search/read or pagination sequence that crosses an updated artifact returns
`publication_changed`; the model must discard previous fragments and search
again. This is demand-driven refresh, not a scheduled background job. Rollback
to a valid earlier website deployment intentionally follows that deployed version.

## Activation on the existing gateway

1. Review and merge the engineering change under the repository's normal PR
   rules. Let the existing engineering mirror and RTD build finish. Verify that
   the served `manual-deployment.json` includes `manual-knowledge.json`; a mirror
   success alone does not prove the query export is deployed.
2. Update the already installed `auto-manual-control-layer` package from this
   revision using the host's existing installation method. If its installation
   uses a copied package, updating the workspace alone does not update the
   installed copy. Preserve the current DingTalk channel and plugin credentials.
3. Merge this single property into the existing plugin config, without replacing
   the surrounding config or existing required fields:

   ```json
   {
     "plugins": {
       "entries": {
         "auto-manual-control-layer": {
           "config": {
             "manualQueryBaseUrl": "https://ht-doc.readthedocs.io"
           }
         }
       }
     }
   }
   ```

4. If the agent has an explicit tool allowlist, add `manual_search` and
   `manual_section` to that existing list, preserving other policies. The query
   feature does not widen channel membership or grant build/publish rights to
   new colleagues. Restart the existing gateway with `openclaw gateway restart`
   and check that these two tools and `/manual-query` are registered. Older
   gateways without `registerTool` retain only the deterministic query command.
5. In the already connected bot, check `/manual-query JE-2000F USB-C输出`, then
   ask “JE-2000F 欧规 USB-C 输出功率是多少？” and “JE-2000F 节能模式怎么关闭？”.
   Verify the answer's values and complete conditions against the linked source.
   Also try a missing model, a US question and an unsupported concept; it should
   clarify or report no evidence, without inventing product facts. Confirm one
   controlled website update and refresh before opening the pilot to colleagues.

No live host was available in this execution environment, and its RTD reads
returned 403. Host configuration, live model tool selection, DingTalk message
delivery and live refresh acceptance remain explicit rollout checks. Do not put
channel secrets into a PR or chat to complete them.

To disable querying on the existing deployment, remove `manualQueryBaseUrl`
and restart the gateway; operation commands remain installed. Reverting this
feature commit removes the export and registered query entrypoints.

## Reproducible verification

Prepare the repository environment, then build a frozen Hello-Docs checkout
with the candidate engineering module on `PYTHONPATH` (the paths below assume
sibling checkouts):

```bash
PYTHONPATH="$PWD" .venv/bin/python -m sphinx -E -q -b html \
  -D extensions=myst_parser,tools.rtd.portal \
  -D rtd_knowledge_dir=../Hello-Docs/docs/knowledge \
  ../Hello-Docs/docs/publish/web .tmp/eu-query/candidate
.venv/bin/python -m unittest tests.test_manual_knowledge
npm test --prefix integrations/openclaw/auto-manual-control-layer
node integrations/openclaw/auto-manual-control-layer/test/verify-published-corpus.mjs \
  .tmp/eu-query/candidate
```

The opt-in real-corpus audit verifies receipt/artifact/manual hashes, every
edition, every chapter anchor and lossless pagination, then checks 25 positive
queries spanning all 21 baseline models plus six uncertainty/negative cases.
The static query cases are regression evidence for the pinned business snapshot;
they are not a production scope filter.

Measured against the baseline above: 61 EU editions / 786 chapters,
4,704,903-byte export, 817 evidence pages, 630 tables and 680 callouts. All 31
query cases pass. All 65 canonical manual HTML files across regions are
byte-identical to the pre-change build. The only other HTML difference is the
system-workspace page, which reflects engineering inventory/revision metadata.
Existing browser search retains its separate extraction contract.

Repository-wide gates and PR/CI results are recorded in the PR validation block.
