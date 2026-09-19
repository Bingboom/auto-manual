# Frozen Git deployment receipt

A successful HTML build of `docs/publish/web` with `tools.rtd_portal` emits
`manual-deployment.json` in its HTML output. The adjacent
`docs/publish/publish_manifest.json` is required. Ordinary source directories,
non-HTML builders and builds ending with an exception do not emit this receipt.

This is the receipt-only OPS-04 engineering slice. It reuses the existing frozen
source and Sphinx pipeline. It neither publishes a candidate nor changes queue
workflow, online source tables, publication metadata or `HTML_link`.

## Contract and verification

The `manual-rtd-deployment/v1` receipt contains a SHA-256 fingerprint of the
complete frozen publish subtree and an output path/SHA-256 inventory. It excludes
only its own output file and build/cache directories (`.doctrees`, `__pycache__`,
`.git`). It publishes hashes and output paths, not queue record IDs or source
content. Existing HTML/assets and frozen inputs are not rewritten by the hook. The hook
runs at priority 1000, after the generated config copies manual assets at the
default priority 500, so those shipped files are included in the receipt.

`tools.rtd_deployment_receipt.verify_deployment(web_root, base_url, routes,
expected_project_slug=None, session=None, include_dependency=None)`
compares the served receipt with the caller's trusted frozen checkout, then
GETs the explicitly selected HTML and recursively referenced same-origin
HTML/CSS resources. It validates their hashes, HTTPS origin and publication
prefix before reporting `status=verified`. Query/fragment suffixes on resource
references do not change the frozen path. Cross-origin CDN resources are
excluded from the verification claim. RTD also injects an addons script and four
platform metadata tags immediately before `</head>`. Only that exact observed
block, with the selected resolver path and HTTP status 200, can be excluded
when comparing served HTML against the frozen output hash. The result lists
these pages in `rtd_proxy_injections_removed`. Manual bytes, other scripts,
unknown injection shapes and all frozen assets remain strictly hashed. A
platform injection change therefore fails verification rather than widening
normalization automatically. Source drift, missing receipt/resources,
changed bytes, unsafe paths, symlinks and request/byte limits fail closed.

Byte identity alone does not prove the bytes were served by the intended RTD
project, so the optional `expected_project_slug` adds that dimension: when
given, every fetched HTML page's RTD-injected `readthedocs-project-slug` meta
must name exactly that project, at least one page must declare it, and a
mismatch fails reporting the actually served slug. When omitted, behavior is
unchanged and no slug key appears in the result. The expectation for the
production site is derivable with
`rtd_project_slug_from_base_url(base_url)` (the `https://<slug>.readthedocs.io`
host shape; other hosts derive `None`), and the production base URL itself has
a single source of truth in `tools.rtd_deployment_receipt.DEFAULT_RTD_BASE_URL`,
which `tools/write_web_publish_html_link.py` reuses as its `--base-url` default.

### Narrowing what gets re-downloaded

`include_dependency` filters which *discovered* resources are re-fetched and
hashed. The default (`None`) fetches everything — the original contract. The
published catalog holds ~2,200 per-model illustration files against ~220 markup
files, so a daily catalog-wide sweep at full scope is ~2,300 requests; the
supplied `markup_dependency` filter (`.html`/`.css`/`.js`) brings one sweep to
roughly 65.

What a filtered run still proves, unchanged:

- the served receipt matches the frozen source fingerprint byte-exactly;
- every selected route and every fetched markup resource matches its recorded
  hash, and a difference fails;
- **every** discovered reference — filtered or not — exists in the served
  receipt, so a removed, renamed or re-pointed asset still fails closed.

What it does not re-prove: that the CDN hands back those exact *binary* bytes
today. The result reports `unfetched_dependencies` so a narrowed run is never
mistaken for a full one, and `verify_web_deployment_targets.py --asset-scope
full` runs the complete check on demand.

### Rate limiting is a third verdict

Verification is read-heavy, and a catalog-wide caller re-walks the same
dependency closure once per target, so the transport must be paced or the host
will rate-limit the run. `FetchSession` is that pacing layer, and `session=`
shares one across calls:

- **One global pace.** `min_interval` (default 0.5 s, i.e. 2 req/s) applies to
  every request the session makes, sequentially. Passing no session still paces
  the single call.
- **One response cache.** A body already fetched and hashed in this run is
  replayed rather than re-requested. This is what keeps a failing 52-target
  catalog at ~62 requests instead of ~570: the per-target attribution pass
  replays the batch's bytes. Identical bytes yield an identical verdict, so
  caching can never turn a mismatch into a pass. Bounded by `MAX_CACHED_BYTES`
  (64 MiB); larger bodies are fetched but not retained.
- **One memoized source fingerprint** per frozen tree, instead of re-hashing a
  ~0.5 GiB publish tree per target.

HTTP 429 and 503 (`RATE_LIMIT_STATUS`) raise `DeploymentThrottled` on the first
attempt — never an immediate in-place retry, which is what turns one rate limit
into a storm. The session then backs off exponentially (`THROTTLE_BACKOFF_BASE`
2 s, doubling, at most `MAX_THROTTLE_ATTEMPTS` 5 attempts) against a shared
`retry_budget` (default 300 s). `Retry-After` is honoured in both the
delta-seconds and HTTP-date forms, capped at `MAX_RETRY_AFTER_SECONDS` (120 s);
it only ever *extends* the wait — the run never retries sooner than either its
own backoff or the server's request. When the shared budget is spent, the
remaining work is abandoned rather than piled onto a host that is already
refusing load.

`DeploymentThrottled` propagates uncaught. A throttled target is **undecided**:
neither verified nor mismatched. Callers must keep the two apart — rate limiting
is evidence about the *client's* request rate, never about the deployment — and
must not swallow it as a pass. `tools/verify_web_deployment_targets.py` reports
it as `throttled` and exits 75 (sysexits `EX_TEMPFAIL`), reserving exit 1 for
real mismatches; a mismatch anywhere in the catalog outranks throttling in the
overall verdict.

Limits: 10,000 files, 32 MiB per file, 512 MiB per source/output inventory and
per verification traversal. Each network request has an I/O timeout of at most
15 seconds. A file read has at most three attempts and a 45-second elapsed budget,
checked before requests and before/after each bounded read; an already blocking
socket operation can take its remaining I/O timeout before that budget is checked.
All chunks are read to EOF within the byte limit, and a supplied Content-Length
must match exactly. Invalid lengths, oversized data, unexpected content encoding,
unsafe URLs and permanent HTTP errors fail immediately. Disconnects, incomplete
bodies, timeouts and selected transient HTTP errors (408/500/502/504) can restart
the read immediately; no partial response is reused. Rate-limit statuses
(429/503) are excluded from that set and handled by the paced backoff above.

Each attempt and same-origin redirect uses an internally generated unique
`receipt_probe` query, plus identity encoding and no-cache/no-transform request
headers. The caller still supplies a canonical HTTPS URL without query or
fragment. Redirect and final-response validation allow only the exact internal
nonce query shape before checking the original HTTPS origin. This prevents a
stale cached receipt or CDN image optimization from being mistaken for the frozen
bytes. If the CDN still returns altered content, exact hash verification fails;
there is no image similarity or recompression tolerance.
This verifies source/output identity through the trusted HTTPS deployment,
not a cryptographically signed release, complete translation, visual acceptance,
uptime or withdrawal. Only selected routes and their resource closure are
verified; other output inventory entries are not downloaded.

## Git-only operator use

After the normal reviewed `docs/publish/**` publication PR is merged and RTD
finishes, use its exact frozen source checkout. Record the business merge SHA,
RTD build ID/commit, base URL and selected canonical route with the result.
Do not confuse the local candidate, a successful HEAD request or the presence
of `HTML_link` with a verified online version.

The existing Sphinx invocation generates the receipt without workflow changes:

```bash
python -m sphinx -W -b html -D extensions=myst_parser,tools.rtd_portal \
  docs/publish/web /tmp/manual-rtd-html
```

Read-only verification from that business checkout, substituting a route
actually present in the frozen catalog:

```bash
python - https://ht-doc.readthedocs.io/ MODEL/REGION/LANG/md/manual.html <<'PYCODE'
import json
from pathlib import Path
import sys
from tools.rtd_deployment_receipt import verify_deployment
from tools.utils.path_utils import PathSegments, Paths

web_root = Paths(Path.cwd()).docs_publish_dir / PathSegments.WEB
result = verify_deployment(web_root, sys.argv[1], sys.argv[2:])
print(json.dumps(result, indent=2))
PYCODE
```

The function has no Base identity, record-ID parameter or writeback path. A
missing receipt on an older deployment requires a real rebuild with the receipt
hook; never author an online receipt manually to pass this check. Publication
record/link updates require their separate exact-record authorization and
same-record readback. Version update, rollback and withdrawal operations remain
separate from this receipt capability. In particular, an absent target is not
a withdrawal request and this verifier does not test a withdrawn route's 404.

## Engineering evidence

The focused regression uses a real Sphinx `-W` frozen-source build, checks the
generated receipt and unchanged source fingerprint, verifies HTML and its actual
local resource closure through a fixture transport, and rejects modified artwork.
Other cases cover source drift, missing assets, unsafe origin/path/base overrides,
limits and excluded build types. Fixture transport is not live RTD evidence.
See also the [local seal](ops_04a_web_version_seal.md),
[locale identity](web_locale_publication_identity.md) and
[HTTP health check](manual_operations_online_health.md) boundaries.


### Production transport reproduction — 2026-09-13

An observed Cloudflare Polish response for the frozen
`app_add_device_steps_9b7e0cf44d0f.png` advertised `cf-polished: ok` and
`orig_size=398750`, but the bare URL returned a 340687-byte optimized PNG.
The approved 398750-byte artifact SHA-256 is
`9b7e0cf44d0f37dc89cc04bb57bba1ebb9c3bbc5db3f0190575dd03e96ab0d0f`.
A unique-query cache miss returned those exact original bytes. The production
reader also encountered incomplete bodies and remote disconnects.

The initial transport regressions failed on missing cache nonces, short reads,
absent length validation and unhandled transient failures. After the bounded
reader fix, two separate real HTTPS reads through the updated `_fetch` each
returned the original 398750-byte PNG and exact approved hash. This proves the
reported asset transport case; it is not a full deployment or content acceptance.
The regression suite retains strict changed-image, unsafe-origin, source-drift
and unknown-HTML-injection rejection.
