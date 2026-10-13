# Web Publish pipeline: operator contract and rollback (§4, §5)

Status: active · Part of the [Web Publish pipeline](../web_publish_pipeline.md) contract; its index lists the
other sections. Change this part of the contract here, not in the hub.

## 4. Operator contract

The requirements below apply to the queue-driven path only.

Before dispatch, the `Document_link` row must have:

- `Workflow_action = Web Publish`
- `Git_ref = <review branch>`
- `是否触发文档构建 = Y`
- `是否立即构建 = checked` when immediate dispatch is required

For a composite figure plus its governed copy, the matching
`04_资产导出物` row must have one `export_file`, a selected `web_locale`, valid
`content_sha256` and `source_fragment_sha256`,
`artifact_kind = web-composite`, `gate_status = approved`,
`build_eligible = true`, and `visual_review_required = false`.

Success requires all three pieces of evidence:

- the GitHub run is green;
- `Hello-Docs/publish` contains the expected target and manifest hashes, and the
  open `publish -> main` PR contains no path outside `docs/publish/**`;
- after that PR is merged, `Hello-Docs/main` contains the same manifest, the
  `Web Publish Receipt` run is green, and the RTD page opens at the registered
  `HTML_link` route.

### 4.1 Receipt timing: three timestamps, kept separate

Following the revitalization plan §5.1, the release records three distinct
facts and never lets one stand in for another:

| Fact | Proven by | Recorded where |
| --- | --- | --- |
| Approval | the human merge of `publish -> main` | PR merge commit on Hello-Docs `main` |
| Deployment | the RTD build of that `main` push | RTD build history; receipt-lane verify attempts |
| Online verification | `verify_deployment` passing against the live site | `web-publish-receipt.yml` run + `HTML_link` write with same-record readback |

`HTML_link` is written only after the third fact: a merged PR proves the
candidate was accepted, an RTD build proves the deploy pipeline ran, and only
the live-content verification proves readers actually reach the target version.
A deployment that fails verification is never registered as online; a failed
registration goes to an independent retry (re-run the receipt workflow),
never to a re-publish of the manual.

For the Git-only path, use the evidence contract in section 2.2. Do not create
placeholder online records or write `HTML_link` to imitate queue completion.

The receipt lane proves the link was correct at registration time; it does not
watch for later drift.
[`verify-web-deployment.yml`](../../../.github/workflows/verify-web-deployment.yml)
is the independent detector: a daily scheduled run on the Hello-Docs business
plane feeds every target of `Hello-Docs/main:docs/publish/publish_manifest.json`
through [`tools/verify_web_deployment_targets.py`](../../../tools/verify_web_deployment_targets.py),
which runs the full `tools.rtd.deployment_receipt.verify_deployment` check per
canonical nested page — frozen-source byte identity plus the expected RTD
project slug derived from the base URL — and fails the run on any unreachable
page, drifted bytes, or wrong-site deployment. Failures open the
`web-deployment-verify` sentinel issue through the shared
`queue-sentinel-issue` action; the next fully green run closes it.

The whole catalog shares one paced, caching transport session (`--rps`, default
2 req/s, overridable per dispatch or via the `AUTO_MANUAL_RTD_VERIFY_RPS` repo
variable), and the nightly run uses `--asset-scope markup`: each page and its
HTML/CSS/JS are byte-checked and every other referenced resource must exist in
the served receipt, which keeps one sweep near 65 requests instead of ~2,300.
Dispatch with `asset-scope: full` for an on-demand deep run that re-downloads
every binary asset. Rate-limited targets are reported **throttled** and exit 75, kept
separate from mismatches at exit 1: a 429 leaves a target undecided, so a
throttled-only run is a re-run signal, not a content incident. Both still fail
the job and open the sentinel — fail-closed is preserved — but the issue body
states which of the two happened, with per-class counts.

## 5. Rollback

Do not force-push `publish`. For the queue-driven path, re-run Web Publish from
the approved review ref and asset rows. For the Git-only path, rebuild from the
recorded source Git ref and release metadata. In either case, append a corrected
candidate snapshot or prepare a `docs/publish/**`-only revert PR into `main`,
verify the generated manifest, merge it, and let the `main` webhook rebuild RTD.
