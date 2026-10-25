# Feishu wiki input and output

All calls use the tenant token of `FEISHU_APP_ID` / `FEISHU_APP_SECRET`
(`scripts/feishu_api.py`); lark-cli is not required.

## Read the draft

```sh
python3 -I scripts/feishu_api.py node <wiki_node_token>        # obj_type file → obj_token
python3 -I scripts/feishu_api.py download <obj_token> <empty_dir>/draft.zip
```

Unzip into its own empty directory (untrusted download); run any Python that
reads it with `-I`. The wiki URL `https://<tenant>.feishu.cn/wiki/<node_token>`
gives the node token. If the operator says the space has no other drafts, do not
hunt for more.

## Upload a new version (operator-requested only)

```sh
python3 -I scripts/feishu_api.py upload-to-wiki <zip> <space_id> [--parent <node_token>]
```

1. uploads to the app's drive root (`/drive/v1/files/upload_all`, ≤20 MB);
2. moves it into the space (`/wiki/v2/spaces/<space>/nodes/move_docs_to_wiki`,
   async task polled until the node exists);
3. reads back the node and re-downloads the file, printing `sha256_match`.

Upload next to the original as a new versioned file; never overwrite the
operator's file. Report the wiki link, node token, and the SHA-256 match. The
node's creator/owner is the app — tell the operator, who can transfer ownership.

## Bitable reads used by the skill

```sh
python3 -I scripts/feishu_api.py bitable-dump Ji1hb5ub1aUbewsTljGccvx5nhc tblzerRpOEuDIkKA terms.json
python3 -I scripts/feishu_api.py bitable-dump Ji1hb5ub1aUbewsTljGccvx5nhc tblqtvNbgjDwR4ya pairs.json
python3 -I scripts/feishu_api.py bitable-dump LD3lb4G1ua4GOVs1vxAc9W2enje tblPUFJqt2uGGvTT specs.json
python3 -I scripts/feishu_api.py bitable-dump LD3lb4G1ua4GOVs1vxAc9W2enje tblW5fCuJ6YdAcND lcd.json
```

These are read-only. Any write to a live table follows
`.agents/skills/lark-cli-bitable-ops/SKILL.md` (operator gate + read-back).
