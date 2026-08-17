#!/usr/bin/env python3
"""同源门诊断驱动：忠实复现 Publish 束并与已批准参考版式契约逐页比对。

复现方法与 CI 队列一致：镜像 main 代码 worktree + 评审分支内容整体替换 +
新鲜 phase2 快照（runner 已 source env）→ prepare_manual_bundle(review-asis)
→ build_manual_ir → 与契约 pages 比对。结果写 <job_dir>/result.json，
manual.ir.json 留在 job_dir 供重绑驱动使用。worktree 用后即清。
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]
MIRROR = Path(os.environ.get(
    "HELLO_DOCS_MIRROR_ROOT",
    os.environ.get(
        "AUTO_MANUAL_REPO_ROOT",
        os.environ.get("HELLO_DOCS_REPO_ROOT", str(DEFAULT_REPO_ROOT)),
    ),
))
VENV_PY = Path(os.environ.get("AUTO_MANUAL_PYTHON", sys.executable))

ANALYZE_SRC = r'''
import json, sys
sys.path.insert(0, ".")
from pathlib import Path
from tools.check_docs import load_config
from tools.build_docs import prepare_manual_bundle
from tools.manual_ir.builder import build_manual_ir
from tools.manual_ir.serialize import write_manual_ir
from tools.target_defaults import FAMILY_DEFAULT_CONFIGS

params = json.loads(sys.argv[1])
model, region, job_dir = params["model"], params["region"], Path(params["job_dir"])
ROOT = Path(".").resolve()
config_rel = FAMILY_DEFAULT_CONFIGS[region.upper()]
cfg = load_config(ROOT / config_rel)
bundle = prepare_manual_bundle(
    cfg, model=model, region=region, lang=None, data_root=ROOT / "data/phase2",
    source_mode="review-asis", page_selector=None,
    output_root=job_dir / "bundle", write_wrapper_index=False,
    draft_placeholders=False)
ir = build_manual_ir(root=ROOT, bundle_root=bundle.bundle_dir, model=model,
                     region=region, lang="", source="prepared-bundle",
                     data_root=ROOT / "data/phase2")
write_manual_ir(ir, job_dir / "manual.ir.json")

contracts_dir = ROOT / "docs/renderers/contracts/reference_layout"
plan_path, plan = None, None
for candidate in sorted(contracts_dir.glob("*.json")):
    try:
        doc = json.loads(candidate.read_text(encoding="utf-8"))
    except Exception:
        continue
    target = doc.get("target") or {}
    if target.get("model") == model and target.get("region") == region:
        plan_path, plan = candidate, doc
        break
if plan is None:
    print(json.dumps({"no_contract": True}, ensure_ascii=False))
    raise SystemExit(0)

cur = [(p.source_ref, p.source_sha256, p.language) for p in ir.pages]
pin = [(e["source_ref"], e["source_sha256"], e.get("language")) for e in plan["pages"]]
cur_map = {r: (s, l) for r, s, l in cur}
pin_map = {r: (s, l) for r, s, l in pin}
removed = [r for r, _, _ in pin if r not in cur_map]
added = [r for r, _, _ in cur if r not in pin_map]
changed = sorted(r for r, (s, l) in cur_map.items() if r in pin_map and pin_map[r][0] != s)
same = sorted(r for r, (s, l) in cur_map.items() if r in pin_map and pin_map[r][0] == s)
lang_diff = [r for r, (s, l) in cur_map.items()
             if r in pin_map and (pin_map[r][1] or "") != (l or "")]
order_ok = [r for r, _, _ in pin if r in cur_map] == [r for r, _, _ in cur if r in pin_map]
print(json.dumps({
    "pinned_pages": len(pin), "current_pages": len(cur),
    "removed": removed, "added": added, "changed": changed, "same_count": len(same),
    "lang_mismatch": lang_diff, "shared_order_ok": order_ok,
    "plan_rel": str(plan_path.relative_to(ROOT)),
    "old_content_sha": plan["identity"]["content"]["manual_content_sha256"],
}, ensure_ascii=False))
'''


def sh(args, cwd=None, timeout=2400):
    proc = subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True,
                          text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(
            f"command failed ({' '.join(str(a) for a in args)}): {proc.stderr[-1200:]}")
    return proc.stdout


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--job-dir", required=True)
    args = parser.parse_args()
    job_dir = Path(args.job_dir)
    result: dict = {"job_kind": "idml_gate_diff", "model": args.model,
                    "region": args.region,
                    "started_at": datetime.now(timezone.utc).isoformat()}
    worktree = job_dir / "worktree"
    try:
        review_branch = f"review/{args.model}-{args.region}"
        sh(["git", "fetch", "origin", "main"], cwd=MIRROR)
        sh(["git", "worktree", "add", "--force", "--detach", worktree,
            "origin/main"], cwd=MIRROR)
        # 快速无契约路径：先扫契约目录，无该目标的已批准契约就直接收工，
        # 不做 sync-data / bundle / IR 的重活（发布前预检对无契约目标零成本）。
        contracts_dir = worktree / "docs/renderers/contracts/reference_layout"
        has_contract = False
        if contracts_dir.is_dir():
            for candidate in sorted(contracts_dir.glob("*.json")):
                try:
                    doc = json.loads(candidate.read_text(encoding="utf-8"))
                except Exception:
                    continue
                target = doc.get("target") or {}
                if (target.get("model") == args.model
                        and target.get("region") == args.region):
                    has_contract = True
                    break
        if not has_contract:
            # finally 块负责写 result.json 和清理 worktree。
            result.update(status="done", verdict="no_contract",
                          summary="该目标没有已登记的参考版式契约——同源门不适用，可直接派发。")
            return
        try:
            sh(["git", "fetch", "origin", review_branch], cwd=MIRROR)
        except RuntimeError:
            result.update(status="done", verdict="no_review_branch",
                          summary="该目标有版式契约但评审分支不存在——先 Start Review 建立评审内容，再谈发布。")
            return
        sh(["git", "checkout", f"origin/{review_branch}", "--",
            f"docs/_review/{args.model}/{args.region}"], cwd=worktree)
        from_defaults = sh([VENV_PY, "-c",
                            "import sys; sys.path.insert(0, '.'); "
                            "from tools.target_defaults import FAMILY_DEFAULT_CONFIGS; "
                            f"print(FAMILY_DEFAULT_CONFIGS['{args.region.upper()}'])"],
                           cwd=worktree).strip()
        sh([VENV_PY, "build.py", "sync-data", "--config", from_defaults,
            "--data-root", "data/phase2"], cwd=worktree)
        params = json.dumps({"model": args.model, "region": args.region,
                             "job_dir": str(job_dir)})
        stdout = sh([VENV_PY, "-c", ANALYZE_SRC, params], cwd=worktree)
        diff = json.loads(stdout.strip().splitlines()[-1])
        if diff.get("no_contract"):
            result.update(status="done", verdict="no_contract",
                          summary="该目标没有已登记的参考版式契约——同源门不适用，失败原因在别处。")
        else:
            structural = bool(diff["removed"] or diff["added"]
                              or diff["lang_mismatch"]
                              or not diff["shared_order_ok"]
                              or diff["pinned_pages"] != diff["current_pages"])
            if structural:
                verdict = "assembly_changed"
                summary = (f"装配变更（不可自动重绑，需人工排查）：契约 {diff['pinned_pages']} 页 vs 现状 "
                           f"{diff['current_pages']} 页；缺失 {diff['removed'] or '无'}；新增 "
                           f"{diff['added'] or '无'}；页序一致={diff['shared_order_ok']}；"
                           f"语言错配 {diff['lang_mismatch'] or '无'}。")
            elif diff["changed"]:
                verdict = "content_only"
                summary = (f"纯内容变更（可批准自动重绑）：{diff['pinned_pages']} 页结构/页序/语言全部一致；"
                           f"{len(diff['changed'])} 页内容指纹变化，{diff['same_count']} 页未变。"
                           f"变更页：{'、'.join(p.split('/')[-1] for p in diff['changed'][:12])}"
                           f"{' 等' if len(diff['changed']) > 12 else ''}")
            else:
                verdict = "identical"
                summary = "手册 IR 与契约完全一致——同源门不会拦截，失败原因在别处。"
            result.update(status="done", verdict=verdict, summary=summary,
                          diff=diff, ir_path=str(job_dir / "manual.ir.json"))
    except Exception as exc:  # noqa: BLE001
        result.update(status="failed", error=str(exc)[-1500:],
                      trace=traceback.format_exc()[-1500:])
    finally:
        try:
            sh(["git", "worktree", "remove", worktree, "--force"], cwd=MIRROR)
        except Exception:  # noqa: BLE001
            shutil.rmtree(worktree, ignore_errors=True)
        shutil.rmtree(job_dir / "bundle", ignore_errors=True)
        result["finished_at"] = datetime.now(timezone.utc).isoformat()
        (job_dir / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
