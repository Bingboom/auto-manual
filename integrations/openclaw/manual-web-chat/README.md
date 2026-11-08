# HT-Docs manual web Q&A

The manual's **问 HT-Docs bot** button opens a sidebar bound to that exact
publication. This small read-only service reuses the existing receipt-verified
EU manual query client and an OpenAI-compatible model connection. It does not
forward website questions to the general operator agent or share its chat
history. No new model subscription or Node dependency is required.

## Run on the Hello-Docs Mac

Use Node 22 or later. Pull the reviewed engineering change and its normal mirror
sync into the Hello-Docs checkout; keep this service on the Mac that hosts the
business-side runtime. Configure a private environment file from
[`.env.example`](.env.example), outside the repository, with mode `600`.

- `HT_DOCS_CHAT_ALLOWED_ORIGINS`: exact website origins, comma separated; no `*`.
- `HT_DOCS_CHAT_PASSWORD_SHA256`: SHA-256 of a strong, separately chosen Q&A
  access password. Set it privately on that host. Do not commit the password,
  hash, model key, RTD token or real environment file.
- `HT_DOCS_CHAT_MANUAL_BASE_URL`: the canonical HTTPS RTD root including
  `/en/latest`; the deployment receipt and corpus must be accessible here.
- `HT_DOCS_CHAT_RTD_TOKEN`: for a private RTD project, create an HTTP-header
  sharing token in RTD and store it here. The reader's browser never receives it.
- `HT_DOCS_CHAT_MODEL_URL`: a trusted OpenAI-compatible **chat completions**
  endpoint (the full URL ending in `/chat/completions`), with the existing model
  and API key in `HT_DOCS_CHAT_MODEL` / `HT_DOCS_CHAT_MODEL_KEY`. HTTPS is required
  except for a loopback model server. This is a direct model call without tools,
  not the general OpenClaw operator gateway. JSON object responses are required.

From the checkout, run:

```sh
node --env-file=/absolute/private/path/manual-chat.env integrations/openclaw/manual-web-chat/server.mjs
```

The listener binds only to `127.0.0.1:8793`. Put an existing HTTPS reverse proxy
in front of it, proxying only `/api/session`, `/api/chat`, `/api/logout` and
optionally `/health`. Allow at least 100 seconds for a chat response. Do not
expose the operator gateway, provider keys or an unrestricted tools endpoint.
Use the Mac's existing process supervisor to keep the service running.
Do not log request bodies or Authorization headers in the proxy.

`GET /health` checks that the process is running; it does not prove corpus or
model availability. Acceptance requires an authenticated real question.
Authentication attempts are limited by the socket peer address (10/minute);
behind a proxy this is a shared limit. Add per-client limits at the trusted proxy
as needed; the service deliberately does not trust `X-Forwarded-For`.

## Enable the website

After the HTTPS service is ready, set **`HT_DOCS_CHAT_URL=https://your-qa-host`**
on the target RTD project and rebuild it. It is an HTTPS origin, with no path,
token, username, query or fragment. Sphinx's equivalent is
`rtd_manual_chat_url`. An empty setting omits the widget and its scripts.
The same opt-in can be used on private or public manual projects; the service
has its own authentication and exact origin allowlist either way.

The RTD project password does not automatically authenticate a different
service. Readers enter the separate Q&A password once per page/session. The
service returns a random 30-minute bearer token, kept only in page memory.
Questions, responses and tokens are not persisted by this implementation.
The configured model provider receives the current question, limited prior
conversation for retrieval planning, and the relevant manual evidence.

The entry is only rendered on verified single-language manual pages, not the
catalog, aliases or legacy language-unverified manuals. Non-EU pages explicitly
state that Q&A is not yet available. The server verifies model, market, locale,
version and canonical page against the current receipt-verified corpus before
calling the model. The model turns the question into keywords, the service
reads complete matching sections including pagination, then the model answers
from that evidence. Incomplete/oversized sections link to the original instead
of presenting a partial procedure as complete. Citations come from the corpus;
model-supplied URLs never become clickable links.

## Validate and roll back

```sh
node --test integrations/openclaw/manual-web-chat/server.test.mjs
python3 -m unittest tests.test_rtd_manual_chat
```

Check desktop/mobile layout, keyboard focus/Escape, correct and incorrect
passwords, expired sessions, missing/withdrawn publications, exact version and
language matching, source links and provider/network failure. The deterministic
service tests use a fake model and corpus; they are not live-model acceptance.
Clear `HT_DOCS_CHAT_URL` and rebuild to remove the website entrance. Stop this
dedicated service to revoke all in-memory sessions. Reader help and build
integration are in the [portal guide](../../../code-as-doc/dev/rtd_manual_portal/manual-chat.md).
