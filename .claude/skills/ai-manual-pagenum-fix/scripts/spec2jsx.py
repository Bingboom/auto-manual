#!/usr/bin/env python3
"""Turn a change spec (JSON, may contain any Unicode) into an ASCII-only ExtendScript file.
Non-ASCII never crosses the osascript/doJavascript bridge: every string is shipped as UTF-16 code arrays.
Usage: python3 spec2jsx.py SPEC.json OUT.jsx [--dry-run]"""
import sys, json, os
spec = json.load(open(sys.argv[1], encoding="utf-8"))
dry = "--dry-run" in sys.argv
def u16(s):
    b = s.encode("utf-16-le"); return [int.from_bytes(b[i:i + 2], "little") for i in range(0, len(b), 2)]
T = []
seen = set()
for c in spec["changes"]:
    assert c["id"] not in seen, "duplicate id " + c["id"]; seen.add(c["id"])
    op = c.get("op", "set")
    assert op in ("set", "replace", "delete_artboard"), op
    t = {"id": c["id"], "ab": c["page"] - 1, "op": op}
    if op != "delete_artboard":
        x0, y0, x1, y1 = c["pdf_bbox"]
        t.update(cx=(x0 + x1) / 2, cy=(y0 + y1) / 2, x0=x0, x1=x1, old=u16(c["old"]), new=u16(c["new"]))
        pos = c.get("pos") or {}
        if "left" in pos: t["tl"] = pos["left"]
        if "right" in pos: t["tr"] = pos["right"]
    T.append(t)
data = json.dumps(T, ensure_ascii=True)
tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "apply_changes.jsx.tpl"), encoding="ascii").read()
out = tpl.replace("__DATA__", data).replace("__DRY__", "true" if dry else "false").replace("__ARTBOARDS__", str(int(spec["artboards"])))
assert out.isascii()
open(sys.argv[2], "w", encoding="ascii").write(out)
print("wrote", sys.argv[2], len(T), "changes", "(DRY RUN)" if dry else "")
