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

`tools.rtd_deployment_receipt.verify_deployment(web_root, base_url, routes)`
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

Limits: 10,000 files, 32 MiB per file, 512 MiB per source/output inventory and
per verification traversal; each network request has a 15-second timeout.
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
