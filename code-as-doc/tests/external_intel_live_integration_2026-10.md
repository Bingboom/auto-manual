# External Intelligence Live Integration — 2026-10

Status: proposed · Owner: operator (夏冰) · Created: 2026-10-22 · PR: [Bingboom/auto-manual#1585](https://github.com/Bingboom/auto-manual/pull/1585)

Gate revised: 2026-10-21 (America/Los_Angeles). Original creation date and file
name retained for traceability; neither is a scheduled test date. Live date: TBD.

## Execution gate — pending migration

**Do not execute T0–T5 in auto-manual, PR #1585 or its incubation branch.** This
file is a runbook awaiting migration, not an active test assignment or permission.
Only static, fixture/fake-transport and standalone tests are allowed here. This
includes no real Feishu table read even via `sync` dry run, no table write, test
Base/group creation or group message send. Do not probe credentials or Feishu
endpoints as a workaround.

Before any operator setup or live call, all of these must be recorded in the new
independent `research-intelligence` repository:

1. Core, tests, fixtures, contracts, Agent context and this runbook have migrated;
   source commit and file manifest are recorded, imports/cache paths updated,
   and clean-environment standalone and contract tests pass without Hello-Docs.
2. The runbook lives at `code-as-doc/tests/external_intel_live_integration_2026-10.md`
   **in that new repository** (or its explicitly recorded replacement path).
   Its commands, module name, test names and links have been checked against the
   migrated code. No checkout of an auto-manual branch is used for the run.
3. The operator confirms test data custodian, storage/retention and exact isolated
   test targets/permissions in the new repository. Only then create a test Base
   and group; obtain the migration-specific go-ahead there. Business data
   sovereignty remains a separate open decision, not a default Hello-Docs write.

The [charter](../dev/research-intelligence-charter.md) owns the sequence and
rollback policy. An incubation merge alone does not satisfy this gate.

## Scope

This describes a future first live run of the migrated Research & Intelligence
loop. It uses a recorded commit of the independent repository, after migration
and the gate above, not PR #1585's head. The original rehearsal used lark-cli
1.0.49; revalidate that version and its contract in the new repository before
running as the dedicated test bot:

1. **Table read.** `sync` reads a test 外部情报 table into `events.json`.
2. **Judgment round trip.** A person fills 人工判断, 复核人 and 复核日期 in the
   table, and the next sync records the judgment. A fact edit reopens the event,
   and an edited judgment confirms it again.
3. **Push.** The digest is sent to a test group and read back by message ID. A
   same-day resend is deduplicated.
4. **Markdown view.** `wiki` generates the view from the result, and `--check`
   then passes.

Out of scope: scheduling (no workflow exists), Hello-Docs commits, the
production table and group, and the research-page build. The code stays as it
is during the run. Any defect is repaired with a regression test in the new
repository and listed under [Results](#results); it does not reopen live testing
in auto-manual.

A historical rehearsal of these steps against a fake table passed on
`ac714048`. A probe with a fake app ID against `open.feishu.cn` showed that
lark-cli 1.x exits 3 and prints the Feishu code under `error` on stderr.
`ac714048` makes failures print that code. This earlier network probe is not
live table/group acceptance and is not to be repeated under the current gate.

## Rules for this run

- **Secrets.** They come only from the environment. Never print them or type
  their values into a command, and pipe every live command through `red`
  (T0).
- **Table writes.** After the gate, obtain the operator's test-scope authorization
  in the independent repository; this document does not grant it. The scope is:
  creating it, seeding four rows and one fact edit. Each write is read back,
  with its record_id and field.
- **Messages.** They go only to the test group, and only after its exact name
  matched exactly one chat.
- **Local files.** The knowledge copy, the pending-push state and raw lark-cli
  output stay in the session's scratchpad, `$W`. Nothing is committed to
  Hello-Docs.
- **Deletes.** Nothing is deleted. The operator removes the test table and
  group afterwards.
- **Egress.** All outbound HTTPS from a cloud session passes the environment's
  proxy, and lark-cli warns about this. Do not set `LARK_CLI_NO_PROXY`; the
  proxy is the only route out.

## Operator setup

Future steps in the independent repository, only after the execution gate:

1. **Test Base.** Create one in Feishu. Add the bot app with edit access
   (… → 更多 → 添加文档应用 → 可编辑).
2. **Test group.** Create one with a unique name, for example
   `外部情报联调测试`, and add the bot (群设置 → 群机器人).
3. **Environment variables.** In the cloud environment's settings, add:
   - `FEISHU_APP_ID` and `FEISHU_APP_SECRET`: the bot app's credentials;
   - `FEISHU_EXTERNAL_INTEL_BASE_TOKEN`: the test Base's token, the part after
     `/base/` in its link.

   Then start a new session. Variables reach only sessions started after they
   are saved.

When a call fails, the command prints Feishu's code. The usual ones:

| Code | Usual meaning |
| --- | --- |
| 10014 | The app ID is wrong. |
| 91403 | The bot is not on the Base. |
| 230002 | The bot is not in the group. |
| 99991672 | The app lacks an API scope. |

## T0 Workspace

1. **Repository.** Check out the migrated independent `research-intelligence`
   repository and record its URL, branch and `git rev-parse HEAD`, plus the
   migration source commit. Confirm this is not an auto-manual checkout or
   worktree. Record the validated module/test paths before running commands.
2. **lark-cli.** Run `npm install --prefix "$W/larkcli" @larksuite/cli@1.0.49`.
3. **Knowledge copy.** Prepare a synthetic `market-policy/records.json` in the
   migrated fixtures using the `nl-net-metering` test record from
   `tests/test_intel_wiki.py` (`POLICY`), and seed `$W/knowledge/market-policy/`
   from it. Record this fixture's hash in the new repository. Start with no
   `external-intel/`. Hello-Docs is not required; any separately approved frozen
   external input must have its provenance recorded and is not the platform's
   default data store.
4. **`$W/red.py`.** It replaces each secret's value with its name:

   ```python
   import os, sys
   text = sys.stdin.read()
   for name in ("FEISHU_APP_SECRET", "FEISHU_EXTERNAL_INTEL_BASE_TOKEN", "FEISHU_APP_ID"):
       if len(value := os.environ.get(name, "")) >= 6:
           text = text.replace(value, f"<{name}>")
   sys.stdout.write(text)
   ```

5. **`$W/env.sh`.** Source it at the start of every shell call. It holds no
   secret. `$W/ids.sh` collects the non-secret IDs as they are learned:
   `FEISHU_EXTERNAL_INTEL_TABLE_ID`, `FEISHU_EXTERNAL_INTEL_CHAT_ID` and
   `INTEL_HOST`.

   ```sh
   set -o pipefail
   W=<the scratchpad path>; KNOW="$W/knowledge"
   export PATH="$W/larkcli/node_modules/.bin:$PATH" EXTERNAL_INTEL_STATE_DIR="$W/state"
   [ -f "$W/ids.sh" ] && . "$W/ids.sh"
   [ -n "${INTEL_HOST:-}" ] && export FEISHU_EXTERNAL_INTEL_RECORD_URL="https://$INTEL_HOST/base/$FEISHU_EXTERNAL_INTEL_BASE_TOKEN?table=$FEISHU_EXTERNAL_INTEL_TABLE_ID&record={record_id}"
   red() { python3 -I "$W/red.py"; }
   ```

6. **Checks.**
   - Each of the three variables is set. Test with `[ -n "${!name}" ]` and
     print only the name.
   - `printf '%s' "$FEISHU_APP_SECRET" | lark-cli config init --app-id
     "$FEISHU_APP_ID" --app-secret-stdin --brand feishu 2>&1 | red` exits 0.
   - `lark-cli base +table-list --base-token "$FEISHU_EXTERNAL_INTEL_BASE_TOKEN"
     --as bot 2>&1 | red` reports `"ok": true`.
   - `python3 -m unittest tests.test_intel_feishu tests.test_intel_sync
     tests.test_intel_cli tests.test_external_intel_boundary` passes.

## T1 Table read

Live commands below run only from the gated independent repository, are written short and
end in `| red`. For example, `sync --write` means
`python3 -m tools.intel sync --knowledge-dir "$KNOW" --write 2>&1 | red`.

1. **Create the table.** Run `base +table-create --name 外部情报联调测试`
   with these fields, 标题 first, because the first field replaces the default
   primary field. Select options are objects (`{"name": "政策"}`):
   - text: 标题, 事件ID, 市场, 政策记录ID, 发生了什么, 适用边界, 来源, 需要决策,
     决策人, 可能影响, 待核实, 人工判断 and 变更说明;
   - single select (`"multiple": false`):
     - 类型: 政策, 市场, 竞品;
     - 来源类型: 外部事件, 市场政策记录;
     - 来源状态: 已核实, 未核实, 需求;
   - datetime: 发生日期, 截止日期 and 复核日期.

   Then add 复核人 with `base +field-create` as
   `{"name": "复核人", "type": "user", "multiple": false}`. If that type is
   refused, add it as text and note this in the results.

   Save the table ID to `ids.sh`. `+field-list` must show the 20 columns of
   `tools/intel/sync.py` `COLUMNS`.
2. **Seed rows.** Add four rows with `base +record-batch-create`. Write dates
   as `YYYY-MM-DD 00:00:00`, counted from today in China Standard Time (*D*),
   and mark every text as test data:

   | Row | 事件ID | 类型 · 市场 · 发生日期 | 来源类型 · 来源状态 | Also |
   | --- | --- | --- | --- | --- |
   | A | `test-a-verified` | 政策 · EU · D−7 | 外部事件 · 已核实 | 来源 `官方 \| Regulation (EU) 2023/1542 \| https://eur-lex.europa.eu/eli/reg/2023/1542/oj \| 联调测试引用 \| D`; 决策人; 截止日期 D+5; two 可能影响 lines; one 待核实 line |
   | B | blank | 竞品 · US · D−3 | 外部事件 · 未核实 | no 来源, 决策人 or 截止日期 |
   | C | `test-c-policy` | 政策 · NL · D−20 | 市场政策记录, 政策记录ID `nl-net-metering` | 来源状态, 发生了什么, 适用边界 and 来源 left blank; 截止日期 D−1 |
   | D | blank | 市场 · DE · D−5 | 外部事件 · 已核实 | 来源 has one 二手 line and no 官方 line: `二手 \| 测试报道 \| http://example.com/report \| 非 HTTPS \| D` |

   Every row has a 标题 that starts with `【联调测试】` and a 需要决策.
   External rows also have 发生了什么 and 适用边界.

   Read the rows back with `base +record-list --format json --limit 200` into
   `$W/raw-t1.json`. Report each record_id, and that every seeded field came
   back.
3. **Cell shapes.** Print the shape of every cell: its JSON type, the item
   types of a list and the keys of an object, but never a value. Copy the
   shapes to the results.

   ```sh
   python3 -I - "$W/raw-t1.json" <<'EOF'
   import json, sys
   data = json.load(open(sys.argv[1]))["data"]
   names = [f if isinstance(f, str) else f.get("field_name") or f.get("name") for f in data["fields"]]
   def shape(v):
       if isinstance(v, list):
           return "list[" + ",".join(sorted({shape(x) for x in v})) + "]"
       return "dict{" + ",".join(sorted(v)) + "}" if isinstance(v, dict) else type(v).__name__
   for i, name in enumerate(names):
       print(name, sorted({shape(r[i]) for r in data["data"] if i < len(r) and r[i] is not None}))
   EOF
   ```

4. **First dry run.** `sync` prints `added 3`: A, B (`ev-` plus 10 hex
   digits) and C. It also prints `1 not used`: D, with the HTTPS-source reason
   and `已核实的事件至少需要一条官方来源`. It ends in `would change`, and
   nothing is written.
5. **Write.** `sync --write` prints `written (3 events)`. In `events.json`:
   - each event's `intake_record_id` is its row's record_id;
   - C carries `source_record_id: nl-net-metering`;
   - every `occurred_on` and `decide_by` equals its seeded date, which is the
     date-handling check.
6. **Rerun.** `sync` prints `unchanged 3` and `unchanged`.

## T2 Judgment round trip

1. **The operator fills judgments in the Feishu UI.**
   - Row A: 人工判断 `联调测试：需要跟进。`; 复核人 themselves; 复核日期 today.
   - Row B: 人工判断 only.

   Also ask for the Base link's domain only, for example `xxx.feishu.cn`, and
   never the full link, which contains the token. Save it as `INTEL_HOST` in
   `ids.sh`.
2. **Record the judgment.** Capture the shapes of A's three cells again into
   `$W/raw-t2.json`. Then `sync --write` prints:
   - `judged 1`: A;
   - `2 not used`: B, with `人工判断、复核人和复核日期要一起填写`, and D.

   A's revision 2 has `review.status: reviewed`, `reviewed_by` set to the
   person's name and `reviewed_on` set to today.
3. **Edit A's facts.** As the bot, run `base +record-batch-update` on A:
   append `（事实已补充）` to 发生了什么 and set 变更说明 to
   `联调测试：补充事实`. Read A back with `+record-get`. Then `sync --write`
   prints `revised 1` and a notice for A:
   `事实已变化，原人工判断未重新确认；请更新判断内容或复核日期后再同步`.
   A's revision 3 is `pending`, with reason `联调测试：补充事实`.
4. **Confirm again.** The operator appends `（已重新核对）` to A's 人工判断
   and clears B's. `sync --write` prints `judged 1` (A) and `1 not used`
   (D only).

## T3 Push

1. **Find the chat.** List the bot's groups, every page of
   `im +chat-list --as bot --page-size 100`, and keep chats whose `name`
   equals the test group's name exactly. Exactly one must match. Save its
   chat_id to `ids.sh`, and print only the count.
2. **Dry run.** `sync --push` writes and sends nothing. Its preview, titled
   `外部情报待决策 · <today>`, shows:
   - `【已逾期（1）】` C;
   - `【待决策（1）】` B;
   - `【需处理的表格行（1）】` D.

   Each item links to its row as `https://<host>/base/<FEISHU_EXTERNAL_INTEL_BASE_TOKEN>?table=…&record=rec…`,
   with the token redacted by `red`.
3. **Send.** `sync --write --push` prints
   `{"status": "sent", "message_id": "om_…", …}`. Afterwards no
   `pending.json` is left under `$W/state`.
4. **Read back.** `im +messages-mget --message-ids <om_…> --as bot` returns a
   post with that title, from the bot. If a scope is missing, record the code
   and rely on step 7.
5. **Resend.** Within the hour, `sync --write --push` sends the same content
   with the same idempotency key, so Feishu posts no second message. The
   receipt should repeat the first message_id; record what it shows.
6. **Push alone.** `push --dry-run` previews B and C without the table-rows
   section; only a sync has a report to show.
7. **The operator checks the group.** It holds one readable message, and
   C's 去填写判断 opens row C.

## T4 Markdown view

1. **Dry run.** `wiki` lists 9 pages to write and the missing templates
   `purpose.md` and `schema.md`. The 9 pages are 3 events, the index, the
   overview, the log and the markets `market-eu`, `market-nl` and
   `market-us`.
2. **Write.** `wiki --write` writes them.
3. **Check.** `wiki --check` prints `up to date` and exits 0.
4. **Inspect.** A's page quotes the judgment, with the reviewer and the date.
   `log.md` lists A's four revisions.

## T5 Leak check

1. **Files.** For `FEISHU_APP_SECRET` and `FEISHU_EXTERNAL_INTEL_BASE_TOKEN`,
   `grep -rlF -- "${!name}"` over `$KNOW`, `$W/state` and this file finds
   nothing. Print each count, never a value.
2. **Commit.** Before committing, the same check over `git diff --cached`
   finds nothing.

## Results

Not run: deferred until independent-repository migration. Fill this section in
the migrated runbook, then set that copy's Status to `done` after acceptance.
The auto-manual copy remains a planned migration reference.

- **Independent repository URL and runbook path:** —
- **Migration source commit and manifest:** —
- **Gate evidence / test data custodian and approved storage:** —
- **Tested commit:** —
- **Date (CST):** —
- **Python and lark-cli versions:** —

| Step | Expected | Observed | Pass |
| --- | --- | --- | --- |
| T0 Workspace | config init and `+table-list` ok; package tests pass | | |
| T1 Table read | added 3, 1 not used, then unchanged; dates as seeded | | |
| T2 Judgment round trip | judged, then revised with notice, then judged | | |
| T3 Push | one message, read back; resend deduplicated; links open | | |
| T4 Markdown view | 9 pages and 2 templates; `--check` up to date | | |
| T5 Leak check | no secret in files or the commit | | |

Observed cell shapes: —

Defects found and fixes: —

After a full pass, the operator records acceptance in the independent repository.
This is not a merge condition for #1585. A real business-table trial and scheduling
need their own target/data decisions; do not commit intake or Wiki data to
Hello-Docs by default.

On failure, stop live activity, retain redacted evidence and pending state, and
repair/retest or return the independent repository to its recorded migration
baseline. Confirm any remote messages before retrying, particularly outside the
one-hour deduplication window; a code rollback does not undo remote writes or
sends. Do not resume in auto-manual or archive the incubation branch before
acceptance. Optional Hello-Docs adapters can be disabled or use the last verified
frozen export. Test-resource cleanup stays with the operator's authorization.
