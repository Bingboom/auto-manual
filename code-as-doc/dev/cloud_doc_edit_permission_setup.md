# Cloud-doc operator edit-access setup

How to make the built Feishu cloud docs **editable by the operator** on a given
machine / repo (e.g. when bringing up the **Hello-Docs mirror** host). Without
this, the build imports the doc **as the bot**, the bot owns it, and the operator
can only make a 副本.

This is a per-machine / per-repo setup because the operator's id, the bot app, and
the GitHub secret all differ between the primary repo and the mirror. Nothing here
is hardcoded in committed files — that is deliberate (see §6).

## 1. How it works (one paragraph)

The build queue imports the cloud doc with `FEISHU_PHASE2_IDENTITY=bot`, then the
leaf calls [`../../tools/queue_cloud_doc_finalize.py`](../../tools/queue_cloud_doc_finalize.py)
`finalize_cloud_doc`, which grants the operator `full_access` (so they edit the
registered doc directly) and co-locates it in the Word's wiki node. The grantee is
resolved by `resolve_cloud_doc_grantee`: the build row's `operator_union_id` when
present, **else** the configured `FEISHU_CLOUD_DOC_DEFAULT_EDITOR`. Because
`operator_union_id` is unpopulated on every build row today, you set the default
editor. The grant is best-effort — if it is unset/empty the build still succeeds,
the doc is just bot-only.

## 2. Prerequisites

- The Feishu app on this host has the **`drive:drive` (application identity)** scope
  — the broad "manage all files" scope already covers adding collaborators. (On a
  test enterprise all permissions are 免审/exempt, so this is automatic.)
- `lark-cli` works with **both** identities here: `lark-cli auth status` shows
  `identities.bot.available: true` and a ready `user`. The bot needs
  `FEISHU_APP_ID` / `FEISHU_APP_SECRET` configured.

## 3. Find the operator's open id (the value to configure)

Use **this host's** operator — not another repo's. With the operator logged in to
`lark-cli`:

```sh
lark-cli auth status        # -> identities.user.openId  (an ou_… value)
# or
lark-cli auth list          # -> userOpenId
```

`ou_…` is an open id, `on_…` is a union id. Either works as the value below
(`resolve_cloud_doc_grantee` infers the type from the prefix; you may also pass an
explicit `openid:ou_…` / `unionid:on_…`).

## 4. Configure the default editor (two places)

### 4a. Remote / GitHub-hosted builds — repo secret

The workers reference `${{ secrets.FEISHU_CLOUD_DOC_DEFAULT_EDITOR }}` (in
`feishu-build-queue.yml` and `feishu-draft-build-queue.yml`). Set the secret on
**this repo**:

```sh
gh secret set FEISHU_CLOUD_DOC_DEFAULT_EDITOR --body "<operator open id>" --repo <owner>/<repo>
gh secret list --repo <owner>/<repo> | grep FEISHU_CLOUD_DOC_DEFAULT_EDITOR   # verify
```

> Mirror note: the secret is **per repo**. The primary repo and the Hello-Docs
> mirror each set their own (or the mirror leaves it unset → the ref is empty →
> grant skipped, no error). Never hardcode the id in the workflow YAML — it would
> travel through `sync-hello-docs.yml` to the mirror.

### 4b. Local / BlockClaw builds — local env file

Local builds read `~/.auto_manual_feishu_phase2_env.sh` (the same file that holds
`FEISHU_PHASE2_IDENTITY=bot`). Append:

```sh
echo 'export FEISHU_CLOUD_DOC_DEFAULT_EDITOR=<operator open id>' >> ~/.auto_manual_feishu_phase2_env.sh
bash -n ~/.auto_manual_feishu_phase2_env.sh && echo "syntax OK"
```

Then restart whatever sources it (the build-queue listener / the OpenClaw gateway)
so the new value is picked up.

## 5. One-time backfill of existing docs

The default editor only applies to **new** builds. Docs that were already built are
still bot-only. Grant the operator on each registered doc once. The cloud-doc tokens
live in the `文档构建表` (`飞书云文档` column):

```sh
# per doc — type is docx for a /docx/<token> URL, wiki for /wiki/<token>
lark-cli drive permission.members create --as bot --yes \
  --params '{"token":"<doc_token>","type":"docx"}' \
  --data '{"member_type":"openid","member_id":"<operator open id>","perm":"full_access"}'
```

To loop over the whole table, list it (`lark-cli base +record-list --base-token
<phase2 base> --table-id <document_link table> --format json --as user`), extract
each `飞书云文档` token, and run the grant per token. Re-running is safe (idempotent).

## 6. Verify

```sh
lark-cli api GET "/open-apis/drive/v1/permissions/<doc_token>/members" \
  --params '{"type":"docx"}' --as bot
# -> the operator listed with perm=full_access
```

Then open the registered doc as the operator — it should be **editable**, and no 副本
is needed. New builds will auto-share going forward, and `tools/cloud_doc_backport.py`
resolves the doc by URL.

## 7. Why nothing is hardcoded

The id is operator- and tenant-specific. It lives only in (a) the repo secret and
(b) the per-host env file — both per-machine. Committed files reference the secret,
so `sync-hello-docs.yml` mirroring the workflows to `Bingboom/Hello-Docs` carries no
operator identity. The mirror configures its own.

## References

- Executor: [`../../tools/queue_cloud_doc_finalize.py`](../../tools/queue_cloud_doc_finalize.py)
- Build flow context: [`../build_doc_guide.md`](../build_doc_guide.md)
- Backport interaction (why URL resolution depends on this): [`../architecture/Feishu_Cloud_Doc_Backport_Design.md`](../architecture/Feishu_Cloud_Doc_Backport_Design.md)
