# Web Publish pipeline: repository and hosting boundaries (§3)

Status: active · Part of the [Web Publish pipeline](../web_publish_pipeline.md) contract; its index lists the
other sections. Change this part of the contract here, not in the hub.

## 3. Repository and hosting boundaries

- Code changes land only in `Bingboom/auto-manual`, then
  `sync-hello-docs.yml` mirrors the engineering tree into
  `Bingboom/Hello-Docs/main` while preserving the business-owned
  `docs/publish/**` subtree already merged there.
- `Hello-Docs/publish` is a generated release-candidate branch. It is produced
  by the Web Publish workflow or by the same assembler in an isolated Git-only
  checkout. Operators do not edit its generated files by hand, and it is not
  the GitHub repository's development or production branch.
- The only release PR into `Hello-Docs/main` is `publish -> main`, and its diff
  must contain only `docs/publish/**`. A whole `review/*` branch is never a
  release PR and must never be merged into `main`.
- `docs/publish/**` is a Web-only Git surface: it may contain only frozen Web
  source/assets, the assembled Sphinx source, and `publish_manifest.json`.
  The assembler rejects IDML, InDesign, LaTeX, PDF, DOCX, source-artwork, and
  archive files before the candidate branch can be pushed. Print artifacts
  remain under release storage and short-lived GitHub Actions artifacts.
- The assembled Sphinx source keeps one physical copy of each asset. A manual
  used to carry its artwork beside the Markdown, again under
  `_static/manual-assets/<model>/<region>/<lang>/`, and again for every sibling
  language that shares the same picture, so the frozen tree grew to several
  times the content it holds. `tools/publish_asset_pool.py` stores one copy per
  unique content hash under
  `docs/publish/web/_static/manual-assets/_pool/<aa>/<sha256><ext>` and repoints
  every HTML `<img src>` and Markdown image at it. Only `src` is rewritten:
  `data-web-finished-panel-path` is the logical identity the published
  stylesheet selects on, so it stays exactly as authored. Copies that no manual
  references are dropped rather than pooled. `docs/publish/sources` is never
  touched and remains the self-contained replayable bundle; `docs/publish/web`
  is a render tree.
- Pooling is self-verifying and fail-closed. It records, per manual, the content
  hash every reference resolves to, repeats the measurement after rewriting, and
  refuses to finish if any manual would point at different bytes — so a rewrite
  that lost or swapped a picture fails assembly instead of shipping. References
  that were already broken stay broken and are not turned into a new assembly
  failure. Pooling an already-pooled tree is rejected outright.
- Deployment size is shared infrastructure, not a per-target budget. The
  [deployment receipt](../rtd_deployment_receipt.md) inventories the built output
  *and* the whole `docs/publish/` source tree against a fixed ceiling, and a
  build that exceeds it fails RTD for every later publisher until someone
  reverts. Check the remaining headroom before adding a target or raising an
  asset resolution, and prefer reducing duplication over reducing quality.
- The Read the Docs project uses `main` as its default build branch and builds
  `docs/publish/web/` through `.readthedocs.yaml`.
- RTD never receives Feishu credentials and never reads mutable attachments.
  It renders only the frozen, hash-inventoried Git snapshot.

The first Web Publish creates `publish` from the current business-plane `main`.
Later runs retain the existing target sources, record current `main` as an
ancestor, refresh the tracked code/config tree to current `main`, replace only
the newly published target, and append normal commits. A non-fast-forward push
fails instead of overwriting another publisher. The three-dot PR diff is checked
before the push so branch-history drift cannot smuggle code or review files into
the release PR.

### 3.1 Hosting convergence and legacy entry review

The shared outlet above is the code/release contract; it does not establish that
every historical RTD project follows that contract. The operator-supplied
2026-09-17 investigation reports HT-Manuals on `Hello-Docs/publish` and HT-Doc on
`Hello-Docs/main`, with overlapping targets at different versions. This docs-only
change has not rechecked the RTD dashboard or moved either site. The
[revitalization plan](../../manual_production_revitalization_plan.md) registers that
reconciliation as WP1.

Before an authorized hosting migration:

1. Capture each project's actual branch, build commit, publication identities,
   versions and URLs at the same time. Map every old URL to its intended content
   and version; distinguish latest-entry aliases from version-bound history.
2. Read existing `HTML_link`, printed QR and delivery references. Preserve the
   original values and record missing/ambiguous mappings. Git-only publication
   itself still makes no online writes; any catalog/link migration is a separate
   scoped operation with same-record readback.
3. Verify the proposed redirects or compatibility pages using supported hosting
   facilities, including body, images, language routes, downloads where present,
   and desktop/mobile access. Preserve historical version meaning; a blanket
   redirect to the newest manual is not sufficient.
4. After compatibility acceptance and approval for the concrete hosting change,
   stop the old project's independent updates while preserving its usable entry
   behavior. Keep `Hello-Docs/publish`: retiring an RTD build trigger does not
   retire the release-candidate branch.
5. For both input paths, record the agreed site, actual deployed commit/release
   and URL verification separately from PR merge. Until a machine gate exists,
   retain this as a manual release acceptance check; do not claim it is automated.
   On migration failure restore the captured mappings/configuration and approved
   snapshot, and leave unresolved entries visible with an owner and next action.

First-time onboarding of a new portal region or publication language also has a
three-place registration in this repository, verified by the JP trial and its
revert: the `regions` and `language_labels` maps in
`tools/rtd_portal_assets/settings.json`, the region list in the portal template
`manual_portal.html`, and the market hint strings in `portal.js`. A missing
`language_labels` entry fails the aggregated portal build outright; a missing
region entry or hint string leaves the new market invisible in the portal UI. A
regional pilot (REV-19) that introduces a new region or language updates all
three together.

The current HT-Doc consolidation target is separate from the already-selected
custom domain's [DNS handoff](../rtd_custom_domain_runbook.md). A documentation PR
neither changes hosting configuration nor approves online writes.
