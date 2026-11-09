# HT-Docs bot manual Q&A sidebar

Status: active

Implemented, opt-in; deployment and live-model acceptance are separate.

## Reader behavior

On a verified single-language manual, **问 HT-Docs bot** opens a right-side
dialog (full width on small screens). Questions automatically carry the frozen
model, market, language, version and canonical manual page. Readers can ask
about specifications, operations and troubleshooting, then open cited original
chapters. This first version is bound to the current manual; cross-product
comparison and non-EU query coverage are not added.

Readers enter a separate Q&A access password. A dialog remains usable after a
network error and requests the password again when its short-lived session
expires. Closing/reopening preserves the current page's conversation; clearing
removes it. No messages or credentials are stored in browser persistent storage.
The footer explains that questions go to the configured Q&A service; the model
provider receives the question, limited history for keyword planning and source
evidence. No personal details are needed to ask a manual question.

The catalog and legacy language-unverified pages have no entry. A configured
non-EU manual reports the coverage boundary. Without JavaScript, the original
manual and its navigation remain readable.

## Build and runtime boundary

`tools/rtd/manual_chat.py` renders the escaped context; `tools/rtd/portal.py`
adds the widget and shared CSS/JS only when `HT_DOCS_CHAT_URL` (Sphinx
`rtd_manual_chat_url`) is set to an HTTPS service origin. Builds make no calls
to the model, Mac service or live Feishu. No secret goes into the HTML.

The service runs independently on the Hello-Docs Mac, using the existing
[EU manual query](../eu_manual_query.md) receipt/hash validation and pagination.
Before either model call, the current document must exactly match the page's
model, EU region, verified language, version and canonical path. Refresh or
withdrawal failures do not fall back to remembered facts. Long sections that
cannot be fully read return original links, not partial procedural answers.

This is a dedicated read-only Q&A interface. It calls the configured model
without tools and has no build, publish, shell or general agent endpoints.
Website privacy does not authenticate the separate API: it has an exact
origin allowlist, separate password verification, expiring in-memory sessions,
request/rate/concurrency limits and generic upstream errors. Citations are
constructed from the verified corpus and restricted to the current page in the
browser. Model prose is rendered as plain text.

## Activation and acceptance

1. Review/merge the engineering change and complete the normal Hello-Docs mirror
   sync. Pull it on the Hello-Docs Mac.
2. Configure the service, RTD private source access and existing model endpoint
   as described in the [service runbook](../../../integrations/openclaw/manual-web-chat/README.md).
3. Expose only this service behind HTTPS, then set `HT_DOCS_CHAT_URL` on the RTD
   project and rebuild. An empty value disables the entrance.
4. Verify desktop/mobile interaction, authenticated real-model answers, correct
   market/language/version and working source chapter links. Check missing
   evidence, wrong password, expired session, server/model failure and a
   republished/withdrawn manual.

Local tests and fixture screenshots prove narrower implementation behavior.
They do not prove mirror synchronization, RTD deployment, connectivity to the
Mac, model grounding quality or live source-link acceptance. Removing the RTD
setting and rebuilding rolls the entrance back; stopping the service revokes
its in-memory sessions.
