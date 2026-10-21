"""Feishu Open API helper for the US→JP review-draft workflow (works without lark-cli).

Uses the app credentials in FEISHU_APP_ID / FEISHU_APP_SECRET (tenant token).

  python3 -I feishu_api.py node <wiki_node_token>
  python3 -I feishu_api.py download <file_token> <out_path>
  python3 -I feishu_api.py bitable-dump <app_token> <table_id> <out_json>
  python3 -I feishu_api.py upload-to-wiki <file> <space_id> [--parent <wiki_node_token>]

``upload-to-wiki`` uploads to the app's drive root, moves the file into the wiki
space, then reads back the node and re-downloads the file to compare SHA-256.
It is a live write: run it only after the operator asked for the upload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from urllib.parse import urlencode

BASE = "https://open.feishu.cn/open-apis"


def req(method: str, path: str, data: dict | None = None, token: str | None = None,
        params: dict | None = None) -> dict:
    url = BASE + path + ("?" + urlencode(params) if params else "")
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, method=method)
    r.add_header("Content-Type", "application/json; charset=utf-8")
    if token:
        r.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"HTTP {exc.code} {path}: {exc.read().decode()[:400]}") from exc


def token() -> str:
    j = req("POST", "/auth/v3/tenant_access_token/internal",
            {"app_id": os.environ["FEISHU_APP_ID"], "app_secret": os.environ["FEISHU_APP_SECRET"]})
    return j["tenant_access_token"]


def get_node(t: str, node_token: str) -> dict:
    return req("GET", "/wiki/v2/spaces/get_node", token=t, params={"token": node_token})["data"]["node"]


def download(t: str, file_token: str, out: str) -> str:
    r = urllib.request.Request(f"{BASE}/drive/v1/files/{file_token}/download")
    r.add_header("Authorization", "Bearer " + t)
    with urllib.request.urlopen(r, timeout=300) as resp, open(out, "wb") as f:
        f.write(resp.read())
    return out


def bitable_dump(t: str, app: str, table: str) -> list[dict]:
    items: list[dict] = []
    page = None
    while True:
        params = {"page_size": 500, **({"page_token": page} if page else {})}
        j = req("GET", f"/bitable/v1/apps/{app}/tables/{table}/records", token=t, params=params)
        if j.get("code"):
            raise SystemExit(json.dumps(j, ensure_ascii=False))
        items += j["data"].get("items") or []
        if not j["data"].get("has_more"):
            return items
        page = j["data"]["page_token"]


def upload_to_drive_root(t: str, path: str) -> str:
    root = req("GET", "/drive/explorer/v2/root_folder/meta", token=t)["data"]["token"]
    name, data = os.path.basename(path), open(path, "rb").read()
    boundary = uuid.uuid4().hex
    fields = (("file_name", name), ("parent_type", "explorer"), ("parent_node", root), ("size", str(len(data))))
    parts = [f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode() for k, v in fields]
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
                 "Content-Type: application/octet-stream\r\n\r\n".encode() + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    r = urllib.request.Request(f"{BASE}/drive/v1/files/upload_all", data=b"".join(parts), method="POST")
    r.add_header("Authorization", "Bearer " + t)
    r.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(r, timeout=300) as resp:
        j = json.loads(resp.read())
    if j.get("code"):
        raise SystemExit(json.dumps(j, ensure_ascii=False))
    return j["data"]["file_token"]


def move_to_wiki(t: str, space: str, file_token: str, parent: str | None) -> dict:
    body = {"obj_type": "file", "obj_token": file_token, **({"parent_wiki_token": parent} if parent else {})}
    j = req("POST", f"/wiki/v2/spaces/{space}/nodes/move_docs_to_wiki", body, token=t)
    data = j.get("data") or {}
    if data.get("wiki_token"):
        return get_node(t, data["wiki_token"])
    task = data["task_id"]
    for _ in range(20):
        res = req("GET", f"/wiki/v2/tasks/{task}", token=t, params={"task_type": "move"})
        moved = (res.get("data") or {}).get("task", {}).get("move_result") or []
        if moved and moved[0].get("node"):
            return moved[0]["node"]
        time.sleep(3)
    raise SystemExit(f"move task {task} did not finish")


def sha256(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("node").add_argument("node_token")
    d = sub.add_parser("download")
    d.add_argument("file_token")
    d.add_argument("out")
    b = sub.add_parser("bitable-dump")
    b.add_argument("app_token")
    b.add_argument("table_id")
    b.add_argument("out")
    u = sub.add_parser("upload-to-wiki")
    u.add_argument("file")
    u.add_argument("space_id")
    u.add_argument("--parent")
    a = ap.parse_args()
    t = token()
    if a.cmd == "node":
        print(json.dumps(get_node(t, a.node_token), ensure_ascii=False, indent=1))
    elif a.cmd == "download":
        download(t, a.file_token, a.out)
        print(a.out, sha256(a.out))
    elif a.cmd == "bitable-dump":
        items = bitable_dump(t, a.app_token, a.table_id)
        json.dump(items, open(a.out, "w", encoding="utf-8"), ensure_ascii=False)
        print(len(items), "records ->", a.out)
    else:
        file_token = upload_to_drive_root(t, a.file)
        node = move_to_wiki(t, a.space_id, file_token, a.parent)
        back = download(t, node["obj_token"], a.file + ".readback")
        same = sha256(back) == sha256(a.file)
        os.remove(back)
        print(json.dumps({"node_token": node["node_token"], "obj_token": node["obj_token"], "title": node["title"],
                          "space_id": node["space_id"], "sha256_match": same}, ensure_ascii=False, indent=1))
        if not same:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
