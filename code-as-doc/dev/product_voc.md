# Product improvement suggestions

## Scope and current release gate

Operator scope (2026-09-19): collect **product improvement suggestions** into
Feishu Bitable; implement the website and submission behavior first, connect
the Mac agent last. Research ownership, dashboards and contact collection are
deferred. This is independent of documentation issue feedback and visit analytics.

Current operator continuation (2026-09-19): this Mac's existing OpenClaw
`main` agent and Feishu **HT-Docs** identity are the designated Mac agent.
The original PR's other-host handoff is superseded by this designation.
The local HT-Docs CLI profile is `cli_aaa0db0d4b39dcca`; `prod` is not
configured on this host. Bot authentication and read access to the fixed VOC
schema were verified. The receiver was started locally on `127.0.0.1:9198`
and its health endpoint returned HTTP 200. This does not prove create permission, live submission,
public HTTPS reachability, or production activation.

Local receiver lifecycle: [Mac receiver](voc_mac_receiver.md).
Post-intake analysis: [OpenClaw handoff](voc_openclaw_handoff.md).
The two stages are independent: a model failure must not cause a visitor's
verified submission to be inserted again. Analysis remains a reviewable local
result; it does not authorize edits to manuals, source tables, or visitor replies.

Read the Docs hosts the static form and its JavaScript, not a long-running
agent or an API server. The narrow receiver runs outside RTD. It accepts only
append-only suggestions; it never exposes the general OpenClaw gateway.

`product_voc_endpoint` in
[`tools/rtd_portal_assets/settings.json`](../../tools/rtd_portal_assets/settings.json)
is optional and must be a fixed HTTPS URL without credentials, query or fragment.
Absent/empty means **off**, including legacy pages. Do not configure a fictional
endpoint or commit a temporary `trycloudflare.com` address as a permanent service.
This implementation is not activated on the live site until the receiver has a
verified HTTPS address and the code has completed the normal engineering PR →
Hello-Docs mirror → RTD release path. Native Feishu forms are not the anonymous
visitor submission boundary.

## Data and privacy boundary

The dedicated [VOC Base](https://xcn57j1urbe6.feishu.cn/wiki/P2IDw5FWHin0XKkvc9TcaITcnMe)
contains table `tblmN7OHIB0HsC23` (`产品优化建议`). It is separate from build source
tables and Translation Memory. The operator has access; website visitors must
not be granted access to read the Base.

| Website field | Feishu field | Limit |
| --- | --- | --- |
| suggestion | Your suggestion | 5–3000 characters, required |
| model | Product model | 1–100 characters, required |
| use_case | Use case | 0–1000 characters |
| context | Manual context | 0–1500 characters plus server-generated submission reference |
| server-created time | Received at | Feishu `created_at`, never written by the client |

The form appears on the portal home and explicit catalog publication pages.
Frozen model/region/language/version/relative page context is visible before
submission. Legacy unknown language/version are labeled unverified, not guessed.
Context received over HTTP is still untrusted visitor evidence, never authority
to modify a product, source table or manual. Suggestions are preserved as text,
not executed as agent instructions. No LLM is invoked in the submission path.

The user deliberately submits to Feishu after seeing the disclosure. No names,
contact fields, cookies, account identifiers, URL queries/fragments, full
browser URL or analytics data are included. Free text can still contain personal
information despite the warning: restrict researcher access and handle retention
before broadly promoting the collection channel. No automatic PII-cleaning or
compliance claim is made.

## Request and confirmation behavior

The form's fieldset starts disabled and JavaScript enables it. Without compatible
JavaScript, it displays a no-submission message rather than sending a GET query
with user content. Fetch uses JSON POST, omitted credentials and no referrer.
Text remains visible on timeout/failure, and retries reuse the request UUID.
Successful delivery requires the bot's write **and readback of the same fields**.

The receiver has one write route: `POST /api/voc`. It rejects unknown fields,
wrong origins, non-JSON, oversize bodies, invalid UUIDs and filled honeypots.
CORS is not authentication; origin checks deter drive-by browser posts but
cannot prevent direct scripted submissions. Short-lived rate limits cap each
peer at 5 attempts/10 minutes and the process at 100 attempts/10 minutes; one
write runs at a time and at most 16 sockets are handled concurrently. With the
explicit `--cloudflare-tunnel` switch behind a dedicated tunnel, the overwritten
`CF-Connecting-IP` is the rate-limit source; do not deploy behind a proxy that
passes through a spoofed header. The server binds **only 127.0.0.1**.

A private SQLite file stores UUID, payload digest, record ID and verification
state, not raw suggestion text. Verified retries do not insert another record.
If a create response is lost, the UUID remains pending: retries return 409 and
require operator reconciliation, not a blind second insert. If the record ID
was received but readback failed, retries only re-read that record. To reconcile
a pending reference, query `Manual context` for `Submission: <UUID>`, verify
the exact row and payload, then update the local receipt with that record ID;
never clear pending state and re-submit without checking Feishu first.

`/healthz` proves process availability only, not current Feishu write health.
`--preview` exposes only the test form and its two fixed static files; it does
not serve arbitrary files or Base records. Omit it from the final public receiver.

## Mac adapter: final integration step

On the next host, first verify `lark-cli --profile prod auth status --json --verify`
reports the intended HT-Docs bot, then read the named Base/table and its fields.
Do not assume that another host already has this machine's profile or credentials.
If missing, use the established Feishu setup flow; never paste secrets into the PR.

The Mac must remain awake and connected. Credentials stay in its already
authorized `lark-cli --profile prod --as bot` identity (HT-Docs). No secret is
copied to RTD, HTML, JavaScript, a URL, or this repository. No new model-specific
config or project dependency is required. Use the same OS account and keychain
context that can successfully run the verified bot command.

Example **local integration** command (not a persistent production deployment):

```bash
python -m integrations.product_voc.server \
  --base Id29bqWMiaFdNjsuyrAcfrkLnZb --table tblmN7OHIB0HsC23 \
  --state /absolute/private/runtime/voc.sqlite \
  --origin https://ht-doc.readthedocs.io \
  --origin http://127.0.0.1:9198 --preview
```

Startup checks the destination schema as the bot. Use a private, durable runtime
directory outside Git. Do not point `--state` at a shared or disposable database.
For public service, use a dedicated HTTPS tunnel hostname to this port only,
add its exact origin only if it hosts the test form, and retain the RTD origin.
No router port forwarding or broad agent access is needed. A quick tunnel is a
temporary smoke-test URL, not acceptance of persistent availability. Mac startup,
sleep/restart behavior, stable hostname, receipt backup and stronger public abuse
protection must be verified before describing this as an always-on public channel.

Final acceptance order:

1. Test form rendering, keyboard/mobile usability, required fields and error UI.
2. Verify API validation, rate limits and idempotency with fake writer tests.
3. Connect the Mac bot and submit one explicitly marked `TEST` record from the
   browser; read back its exact record ID and all submitted fields.
4. Verify HTTPS from an external visitor without Feishu login, repeat the same
   submission reference without inserting twice, then activate the site setting.
5. Obtain the normal PR merge approval, verify the mirror and RTD build, and
   repeat the entry-to-record test on the real manual page. Code, local tests,
   live write, public reachability and published-site acceptance are distinct.

## Rollback and verification

Implementation handoff checks: real Sphinx opt-in/rollback fixtures and existing
portal tests pass; new intake tests cover schema/origin/size rejection, restart
idempotency and uncertain-write handling. Browser desktop checks covered required
fields, explicit preview-only success, rejected-origin error and preserved input.
The preview used a fake receiver and made no Feishu writes. Narrow-screen browser
inspection was unavailable in that session and remains a next-host acceptance item.

Local full regression: 4,348 tests passed, 19 skipped. The asset tests required
their pinned PyMuPDF 1.28.0 in a temporary test overlay; no repository dependency
or existing virtual environment was changed. Final intake module rerun: 18 tests
passed; frontend behavior: 4 Node tests passed. Ruff, structural guardrails, doc
links and the fixture-backed US build check passed. These are implementation
checks, not a deployed-site or live-bot acceptance claim.

Set the endpoint to empty and rebuild to remove the form; stop the dedicated
receiver/tunnel to stop collection. Preserve receipts and already received rows.
Do not delete the Base or existing suggestions as part of disabling the feature.

```bash
python -m unittest tests.test_product_voc tests.test_rtd_feedback tests.test_rtd_portal
node --check tools/rtd_portal_assets/_static/product-voc.js
node --test tests/product_voc_ui.test.mjs
python -m ruff check build.py integrations tools tests scripts
python -m unittest
python tools/check_maintainability_guardrails.py
python tools/check_doc_link_integrity.py
```

## Deployment-stage trial (2026-09-19)

The operator explicitly requested an online trial during site deployment. For
this trial only, the portal endpoint uses a temporary Cloudflare quick tunnel.
It lasts while this Mac receiver and tunnel remain running; restarting the
tunnel can change the hostname. This is not a permanent production address.
If unavailable, clear `product_voc_endpoint` and rebuild, or replace it with a
verified new endpoint. The receiver retains the RTD origin allowlist, rate
limits, explicit submission, and durable duplicate protection.

Live testing found that the CLI's create response is
`data.record.record_id_list`, not `data.record.id`; the adapter now accepts the
single-record list and rejects ambiguous lists. The first uncertain submission
was matched by UUID and exact fields, read back, and reconciled locally without
creating it again. TEST rows remain visibly labeled in the dedicated VOC table.

Trial evidence: public HTTPS POST and same-UUID retry both returned 200 for
submission `b43d8988-b9d8-4157-ac0f-1bfae5423c97`, stored once as
`recvvJP3TajTEM`. Exact fields were read back by the bot. An explicit analysis
run completed through local OpenClaw `main` in its scoped VOC session and
recognized the record as TEST data. Analysis is operator-triggered, not an
automatic background worker. No visitor message was sent.
