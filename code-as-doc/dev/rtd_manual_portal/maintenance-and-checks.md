# RTD portal: maintenance surface, feedback and local verification

Status: active · Part of the [RTD manual-center entrance](../rtd_manual_portal.md); its index lists the
other portal surfaces. Add new notes for this surface here, not to the hub.

## Maintenance surface

Product improvement suggestions use an independent opt-in `product_voc_endpoint`
and narrow bot receiver; see [product VOC](../product_voc.md). This is not the
documentation issue channel below. RTD only builds the form; it never reads
Feishu credentials or runs the receiver.

- `tools/rtd/portal.py` reads explicit frozen index links and only existing
  local packing-list product assets. It does not scrape the live website.
- `tools/rtd_portal_assets/settings.json` owns the temporary default, entrance
  bindings, category-prefix presentation rules and twelve planned labels.
  These category rules are navigation hints, not new product master data.
- `.readthedocs.yaml` activates the extension for frozen and bootstrap builds.
  This is needed for old frozen configs as well as future publications.
- The portal template renders real links before JavaScript; scripts only enhance
  filtering and the language dialog. The search template keeps Sphinx's native
  result container and scripts, and adds a visible query form so a direct visit
  to `/search.html` is usable before a query is present. Alias and manual bodies
  remain unchanged.
- Feedback is configured by `feedback_channels` in
  `tools/rtd_portal_assets/settings.json`. The consumer-facing channel is the
  after-sales mailbox `hello@jackery.com` already printed in shipped manuals
  (growth-plan decision D2); [GitHub Issues](https://github.com/Bingboom/auto-manual/issues)
  remains the internal/dealer triage board and is no longer linked on manual
  pages. Setting the list to `[]` disables the block. Channels are
  fixed HTTPS URLs without query strings, fragments or credentials, or a
  single plain `mailto:` address without headers or extra recipients. When
  enabled, a single-language page shows frozen model/region/language/version
  and relative page context for the user to copy; it never sends context or
  adds user identity to a link. The visible text block remains the no-JS
  fallback.
- Optional visit analytics is configured by `analytics_beacon_token` in
  `tools/rtd_portal_assets/settings.json` and defaults to `""` (off,
  byte-identical output). A configured token must be 32 lowercase hex
  characters and enables the cookieless Cloudflare Web Analytics beacon on
  the portal root and single-language manual pages; the token is the only
  payload, and the beacon collects no cookies or user identity under the
  operator's Cloudflare account. Growth-plan decision D1 selected this
  channel; activation is a separate settings change once the operator
  creates the Web Analytics site and provides its token. Activated
  2026-09-15 for the `ht-doc.readthedocs.io` Web Analytics site (custom
  domain deferred). Since 2026-10-13 the site is served from
  `ht-docs-ht-manuals.readthedocs-hosted.com`; the Cloudflare site must cover
  that hostname (edit its hostname, or create a site for it and replace the
  token), which is a dashboard change outside this repository. The committed
  token is that site's public identifier,
  embedded verbatim in every rendered page by design — not a Cloudflare
  API credential. Token self-service: Cloudflare → Analytics → Web
  Analytics → Manage site → Install JS Snippet. Collection starts after
  the next RTD publish; verify by viewing page source for the beacon and
  the Web Analytics dashboard for visits.
- Page head metadata is derived, never hand-written: on verified
  single-language pages the extension sets a search-legible `<title>`
  (product name, model, market, language), meta description, Open Graph
  tags, canonical and a self-inclusive `hreflang` group — all computed from
  the frozen publication identity and the catalog's `language_options`.
  Absolute URLs come from `site_base_url` in the portal settings (an
  HTTPS origin plus an optional serving prefix such as `/en/latest`;
  empty omits canonical/hreflang/og:url) — this is the single switch to
  flip when the domain changes. It currently points at the private Read
  the Docs for Business project
  `https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest`. The portal home gets
  canonical/OG through its own template; legacy pages and the title of any
  page without a verified identity stay byte-identical via the shadow
  `page.html`'s fallback to the theme block.
- Root aliases are the countable print/QR entry layer (growth-plan L2).
  At build time every alias page gets `noindex` plus a canonical link to its
  nested route; when the analytics beacon is configured, the generated
  instant forward becomes a short beacon send window (JS navigates ~200ms
  after load, hard cap 2.5s, no-JS meta refresh at 4s, visible link
  unchanged) so the alias pageview is recorded. Reading attribution in Web
  Analytics: root-level `manual_*` paths ≈ printed/QR entries, nested
  `MODEL/REGION/...` paths ≈ web navigation and search. With analytics off
  the alias keeps its instant forward; an unrecognized alias body shape is
  left unchanged.
- Tabular traffic reads: `python -m tools.cwa_report --days 7` prints the
  taxonomy totals (print/QR alias entries, in-site manual routes, portal
  home) and a top-pages table from the Web Analytics GraphQL API. It needs
  `CLOUDFLARE_API_TOKEN` (Account Analytics: Read), `CLOUDFLARE_ACCOUNT_ID`
  and `CLOUDFLARE_SITE_TAG` in the environment. The site tag is the Web
  Analytics site's own id — the `siteTag` parameter in the dashboard URL,
  NOT the page beacon token. Read-only; the dashboard stays untouched.
- Outbound link policy (链接归一): print/QR and the persisted `HTML_link`
  records use the root alias; in-site navigation and search engines use the
  nested canonical route; marketing and support signatures point at the
  portal home. Do not hand out a third link shape.

## Feedback and publication checks

The operator has assigned Xia Bing (GitHub `Bingboom`, verified with
`gh api user`) to handle manual feedback and check publication health after
each release. The event triggers a manual check, not a new scheduled service.
First response within 3 business days (growth-plan decision D4, 2026-09-15);
a resolution SLA remains unassigned.

On a verified single-language page with a version, the reader copies the
visible model, market, language, version and relative page context, then opens
GitHub Issues and submits the problem and expected result. Submission requires
the reader's GitHub access and an explicit action; opening the link or copying
context sends nothing. Legacy pages without verified single-language identity
keep their existing behavior and do not receive the feedback block.

Xia Bing records receipt in the Issue, locates the source, links the approved
fix PR and subsequent release commit, verifies the deployed revision and
health checks, and replies in the Issue with the result and final page URL.
Keep those links as the feedback closure evidence. Configuration alone is not
a completed real feedback round; it does not create an Issue or send a reply.
Use the [local health](../manual_operations_health_report.md) and
[HTTP health](../manual_operations_online_health.md) runbooks after each release.

Current implementation is the entrance slice only. The language dialog keeps
the existing publication available and does not enable invented locale URLs.
Independent locale storage and real locale links remain a separate milestone.

## Local verification

GitHub channel activation (2026-09-13): 42 existing feedback, portal, catalog
and health tests pass. Strict Sphinx over the actual 23-publication frozen
snapshot shows the configured Issue link and all five context fields on both
verified single-language pages; all 21 legacy pages omit the feedback block.
This is local HTML verification, not browser, deployment or real-feedback
closure evidence. Ruff, maintainability and documentation link checks pass.

- `python3 -m unittest`: 3,975 tests run, OK, 22 skipped.
- Portal + RTD source targeted tests: 8 run, OK; real Sphinx fixture builds
  preserve all three manual pages and three QR aliases byte-for-byte, and leave
  the entire source tree unchanged.
- Ruff, maintainability guardrails, JS syntax and documentation links passed.
- `build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
  --data-root tests/fixtures/phase2` passed. The initial command without an
  explicit data root stopped on the intentionally absent local phase2 snapshot;
  no live-data sync was performed.
- Production corpus comparison passed on Hello-Docs snapshot
  `70bb408a059b8bd5f0c666b9d153354fb856f66a`: 1,028 files fetched and checked
  against their Git blob hashes; all source files remain unchanged after both
  Sphinx builds. Of 66 HTML pages, only `index.html` changes; the other 65 are
  byte-identical. The catalog has 21 publications (US 1, shared EU/UK 20).
- Actual RTD rollout is tracked in the implementing PR; local parity is not an
  online acceptance claim.
