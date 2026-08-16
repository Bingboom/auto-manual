#!/usr/bin/env python3
"""数据入库驱动：把入库暂存表里已确认的行搬进两张 phase2 源表。

契约（与 spec-sheet-structured-intake 技能一致）：
  - 只搬 确认=True 且 入库结果 为空的暂存行（表内门；对话门在桥层 confirm_ingest）。
  - 路由：Page=specifications → 规格参数明细；其余 → 页面占位参数。
  - 已有行（document_key+Row_key+Slot_key+Line_order 匹配）→ UPDATE Value_source。
  - 不存在的行 → 按姊妹机克隆 CREATE：复用姊妹行的结构列 + Row_key_link/Slot_key_link，
    Document_key_link 指向目标字典行（字典无行 = 该行失败，不自动建字典）。
  - KR 使用 kr-structured-source-first-v2：首次入库要求英文
    Value_source/Row_label_source 与 Source_lang=en，并按显式姊妹目标校验
    Page+Row_key+Slot_key+Section+Line_order；Value_ko/Row_label_ko 是可选
    后续本地化层。
  - 每写必按完整键读回；只有读回字段全部相等才回填“已入库”；收尾 sync-data +
    build.py check（作业内快照，不动仓库）。
结果写 <job_dir>/result.json。
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

from intake_contract import (
    KR_CONTRACT_VERSION,
    KR_SOURCE_REQUIRED_FIELDS,
    KR_STAGING_REQUIRED_FIELDS,
    is_kr_document_key,
    missing_fields,
    structure_identity,
    validate_kr_candidate,
    validate_sibling_structure,
)

DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = Path(os.environ.get(
    "AUTO_MANUAL_REPO_ROOT",
    os.environ.get("HELLO_DOCS_REPO_ROOT", str(DEFAULT_REPO_ROOT)),
))
VENV_PY = Path(os.environ.get("AUTO_MANUAL_PYTHON", sys.executable))
LARK_CLI = os.environ.get("LARK_CLI") or shutil.which("lark-cli") or "lark-cli"
LARK_CLI_PROFILE = os.environ.get("LARK_CLI_PROFILE", "prod")
LARK_CLI_IDENTITY = os.environ.get("LARK_CLI_IDENTITY", "bot")

BASE = "LD3lb4G1ua4GOVs1vxAc9W2enje"
STAGING_TABLE = "tblIi0BEufjvGLIU"      # 数据入库表（staging）
SPEC_TABLE = "tblPUFJqt2uGGvTT"         # 规格参数明细
PLACEHOLDER_TABLE = "tblEhqJVXiyKtnwq"  # 页面占位参数
DOCKEY_DICT_TABLE = "tbltnkDIdwiDOP7d"  # 02_主数据_Document_key

# CREATE 时从姊妹行复制的结构列（值列/链接列单独处理；公式与 lookup 不可写）。
CLONE_SCALARS = ["Page", "Section", "Section_order", "Row_order", "Line_order",
                 "Param_source", "Version", "Is_Latest"]
CLONE_LINKS = ["Row_key_link", "Slot_key_link"]
LANG_VALUE_COLUMNS = ["Value_fr", "Value_es", "Value_br", "Value_de", "Value_it",
                      "Value_uk", "Value_ko"]


def sh(args: list[str], timeout: int = 120) -> dict:
    proc = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                          timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"lark-cli failed rc={proc.returncode}: "
                           f"{(proc.stderr or proc.stdout)[-800:]}")
    payload = json.loads(proc.stdout)
    if payload.get("ok") is False:
        raise RuntimeError(f"lark-cli error: {json.dumps(payload.get('error'))[:600]}")
    return payload.get("data", {})


def lark_args(args: list[str]) -> list[str]:
    argv = [LARK_CLI, "--profile", LARK_CLI_PROFILE, *args]
    if "--as" not in args:
        argv.extend(["--as", LARK_CLI_IDENTITY])
    return argv


def read_rows(table_id: str, document_key: str | None = None) -> dict:
    """整表/按 document_key 读取（分页），返回 columns/rows/record_ids。"""
    columns: list[str] = []
    rows: list[list] = []
    record_ids: list[str] = []
    offset = 0
    while True:
        args = ["base", "+record-list", "--base-token", BASE,
                "--table-id", table_id, "--format", "json",
                "--limit", "200", "--offset", str(offset)]
        if document_key:
            args += ["--filter-json", json.dumps(
                {"logic": "and", "conditions": [["document_key", "is", document_key]]})]
        data = sh(lark_args(args))
        columns = data.get("fields") or columns
        page = data.get("data") or []
        rows.extend(page)
        record_ids.extend(data.get("record_id_list") or [])
        if len(page) < 200:
            return {"columns": columns, "rows": rows, "record_ids": record_ids}
        offset += 200


def norm(value) -> str:
    """把 select/lookup 的 list 包装与 None 统一成纯字符串。"""
    if value is None:
        return ""
    if isinstance(value, list):
        if len(value) == 1 and isinstance(value[0], (str, int, float)):
            return str(value[0]).strip()
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, dict):
        return str(value.get("name", "")).strip()
    return str(value).strip()


class Table:
    def __init__(self, table_id: str, document_key: str):
        data = read_rows(table_id, document_key)
        self.table_id = table_id
        self.columns = data["columns"]
        self.rows = data["rows"]
        self.record_ids = data["record_ids"]

    def cell(self, row: list, name: str):
        try:
            return row[self.columns.index(name)]
        except (ValueError, IndexError):
            return None

    def match_key(self, row: list) -> tuple:
        return structure_identity({
            "Page": self.cell(row, "Page"),
            "Row_key": self.cell(row, "Row_key"),
            "Slot_key": self.cell(row, "Slot_key"),
            "Section": self.cell(row, "Section"),
            "Line_order": self.cell(row, "Line_order"),
        })

    def index(self) -> dict:
        return {self.match_key(r): (rid, r)
                for rid, r in zip(self.record_ids, self.rows)}

    def matches(self, key: tuple) -> list[tuple[str, list]]:
        return [(rid, row) for rid, row in zip(self.record_ids, self.rows)
                if self.match_key(row) == key]


def staging_key(columns: list[str], row: list) -> tuple:
    def cell(name):
        try:
            return row[columns.index(name)]
        except (ValueError, IndexError):
            return None
    return structure_identity({
        "Page": cell("Page"),
        "Row_key": cell("Row_key"),
        "Slot_key": cell("Slot_key"),
        "Section": cell("章节"),
        "Line_order": cell("Line_order"),
    })


def table_structure_rows(table: Table) -> list[dict]:
    return [
        {
            "Page": table.cell(row, "Page"),
            "Row_key": table.cell(row, "Row_key"),
            "Slot_key": table.cell(row, "Slot_key"),
            "Section": table.cell(row, "Section"),
            "Line_order": table.cell(row, "Line_order"),
        }
        for row in table.rows
    ]


def upsert(table_id: str, record_id: str, payload: dict) -> None:
    sh(lark_args(["base", "+record-upsert", "--base-token", BASE,
        "--table-id", table_id, "--record-id", record_id,
        "--json", json.dumps(payload, ensure_ascii=False)]))


def batch_create(table_id: str, fields: list[str], rows: list[list]) -> None:
    sh(lark_args(["base", "+record-batch-create", "--base-token", BASE,
        "--table-id", table_id,
        "--json", json.dumps({"fields": fields, "rows": rows}, ensure_ascii=False)]))


def find_dockey_record(document_key: str) -> str:
    """在 Document_key 字典表里找目标 key 的 record_id（公式列，只能全读匹配）。"""
    data = read_rows(DOCKEY_DICT_TABLE)
    try:
        idx = data["columns"].index("Document_key")
    except ValueError:
        return ""
    for rid, row in zip(data["record_ids"], data["rows"]):
        if idx < len(row) and norm(row[idx]) == document_key:
            return rid
    return ""


def run_close_checks(document_key: str, job_dir: Path) -> dict:
    """sync-data + check，用作业内快照，不动仓库工作区。失败不致命，只记录。"""
    model, _, region = document_key.rpartition("_")
    outcome: dict = {"model": model, "region": region}
    try:
        stdout = subprocess.run(
            [str(VENV_PY), "-c",
             "import sys; sys.path.insert(0, '.'); "
             "from tools.target_defaults import FAMILY_DEFAULT_CONFIGS as F; "
             f"print(F.get('{region}') or F.get('{region.upper()}') or '')"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60).stdout.strip()
        if not stdout:
            outcome["skipped"] = f"region {region!r} 没有默认 config，跳过 sync/check"
            return outcome
        config = stdout
        snapshot = job_dir / "phase2"
        for label, args in (
            ("sync_data", ["build.py", "sync-data", "--config", config,
                           "--data-root", str(snapshot)]),
            ("check", ["build.py", "check", "--config", config, "--model", model,
                       "--region", region, "--data-root", str(snapshot)]),
        ):
            proc = subprocess.run([str(VENV_PY), *args], cwd=REPO_ROOT,
                                  capture_output=True, text=True, timeout=1500)
            outcome[label] = {"ok": proc.returncode == 0,
                              "tail": (proc.stdout + proc.stderr)[-600:]}
            if proc.returncode != 0:
                break
    except Exception as exc:  # noqa: BLE001
        outcome["error"] = str(exc)[-500:]
    return outcome


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--document-key", required=True)
    parser.add_argument("--sibling-document-key", default="")
    parser.add_argument("--approved-by", required=True)
    parser.add_argument("--job-dir", required=True)
    args = parser.parse_args()
    job_dir = Path(args.job_dir)
    target_key = args.document_key.strip()
    sibling_key = args.sibling_document_key.strip()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    is_kr = is_kr_document_key(target_key)
    result: dict = {"job_kind": "intake_commit", "document_key": target_key,
                    "sibling_document_key": sibling_key,
                    "approved_by": args.approved_by,
                    "contract_version": KR_CONTRACT_VERSION if is_kr else None,
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "updated": [], "created": [], "failed": [], "skipped": [],
                    "contract_violations": [], "readback_failures": [],
                    "warnings": [], "writes_started": False}
    try:
        staging = read_rows(STAGING_TABLE, target_key)
        cols = staging["columns"]

        def s_cell(row, name):
            try:
                return row[cols.index(name)]
            except (ValueError, IndexError):
                return None

        if is_kr:
            absent = missing_fields(cols, KR_STAGING_REQUIRED_FIELDS)
            if absent:
                result.update(
                    status="rejected",
                    error="KR 入库预检失败：暂存表缺少 source-first 必需字段",
                    missing_fields=absent,
                    formal_source_writes=0,
                )
                return

        eligible: list[tuple[str, list]] = []
        for rid, row in zip(staging["record_ids"], staging["rows"]):
            outcome = norm(s_cell(row, "入库结果"))
            if outcome:
                result["skipped"].append({"staging": rid, "reason": "已有入库结果"})
                continue
            if is_kr:
                violations = validate_kr_candidate(target_key, {
                    "Row_key": s_cell(row, "Row_key"),
                    "Line_order": s_cell(row, "Line_order"),
                    "行标签": s_cell(row, "行标签"),
                    "手册值": s_cell(row, "手册值"),
                    "规格书原值": s_cell(row, "规格书原值"),
                    "Source_lang": s_cell(row, "Source_lang"),
                })
                if violations:
                    result["contract_violations"].append({
                        "staging": rid,
                        "row_key": norm(s_cell(row, "Row_key")),
                        "match_key": staging_key(cols, row),
                        "violations": violations,
                    })
                    continue
            if s_cell(row, "确认") is not True:
                result["skipped"].append({"staging": rid, "reason": "未勾确认"})
            elif not norm(s_cell(row, "手册值")):
                result["skipped"].append({"staging": rid, "reason": "手册值为空"})
            else:
                eligible.append((rid, row))
        result["staging_total"] = len(staging["rows"])
        result["eligible"] = len(eligible)
        if result["contract_violations"]:
            result.update(
                status="rejected",
                error="KR 入库预检失败：存在 source-first 合同违规暂存行",
                formal_source_writes=0,
            )
            return
        if not eligible:
            result.update(status="done",
                          summary=f"{target_key} 没有待入库的已确认行（表内勾「确认」且入库结果为空才会搬）。")
            return

        spec = Table(SPEC_TABLE, target_key)
        holder = Table(PLACEHOLDER_TABLE, target_key)
        sib_spec = sib_holder = None
        if sibling_key:
            sib_spec = Table(SPEC_TABLE, sibling_key)
            sib_holder = Table(PLACEHOLDER_TABLE, sibling_key)

        if is_kr:
            if not sibling_key or sib_spec is None or sib_holder is None:
                result.update(
                    status="rejected",
                    error="KR 入库预检失败：必须指定姊妹目标作为两张源表结构基线",
                    formal_source_writes=0,
                )
                return
            reference_rows = [
                *table_structure_rows(sib_spec),
                *table_structure_rows(sib_holder),
            ]
            candidate_by_identity = {
                structure_identity(row): row
                for row in [*table_structure_rows(spec), *table_structure_rows(holder)]
            }
            for _rid, row in eligible:
                candidate = {
                    "Page": s_cell(row, "Page"),
                    "Row_key": s_cell(row, "Row_key"),
                    "Slot_key": s_cell(row, "Slot_key"),
                    "Section": s_cell(row, "章节"),
                    "Line_order": s_cell(row, "Line_order"),
                }
                candidate_by_identity[structure_identity(candidate)] = candidate
            structure_preflight = validate_sibling_structure(
                candidate_by_identity.values(), reference_rows, require_complete=True
            )
            result["structure_preflight"] = structure_preflight
            if structure_preflight["violations"]:
                result.update(
                    status="rejected",
                    error="KR 入库结构/完整性预检失败；正式源表零写入",
                    formal_source_writes=0,
                )
                return
            used_tables = {
                SPEC_TABLE if norm(s_cell(row, "Page")).strip().lower() ==
                "specifications" else PLACEHOLDER_TABLE
                for _rid, row in eligible
            }
            target_tables = {SPEC_TABLE: spec, PLACEHOLDER_TABLE: holder}
            shape_errors = {
                table_id: missing_fields(target_tables[table_id].columns,
                                         KR_SOURCE_REQUIRED_FIELDS)
                for table_id in used_tables
                if missing_fields(target_tables[table_id].columns,
                                  KR_SOURCE_REQUIRED_FIELDS)
            }
            if shape_errors:
                result.update(
                    status="rejected",
                    error="KR 入库预检失败：正式源表缺少 source-first 必需字段",
                    source_shape_errors=shape_errors,
                    formal_source_writes=0,
                )
                return

        dockey_record = ""
        dockey_missing = False
        update_plan: list[dict] = []
        create_plan: list[dict] = []

        for rid, row in eligible:
            key = staging_key(cols, row)
            page = norm(s_cell(row, "Page"))
            is_spec = page.strip().lower() == "specifications"
            table = spec if is_spec else holder
            sibling = sib_spec if is_spec else sib_holder
            manual_value = norm(s_cell(row, "手册值"))
            manual_value_ko = norm(s_cell(row, "手册值_ko"))
            row_label_source = norm(s_cell(row, "行标签"))
            row_label_ko = norm(s_cell(row, "行标签_ko"))
            source_lang = norm(s_cell(row, "Source_lang"))
            hits = table.matches(key)
            if len(hits) > 1:
                result["failed"].append({
                    "staging": rid, "row_key": key[1], "match_key": key,
                    "reason": "目标正式源表存在重复完整键，拒绝猜测更新对象",
                })
                continue
            if hits:
                target_rid, target_row = hits[0]
                patch = {"Value_source": manual_value}
                if is_kr:
                    patch["Row_label_source"] = row_label_source
                    patch["Source_lang"] = source_lang
                    if manual_value_ko:
                        patch["Value_ko"] = manual_value_ko
                    if row_label_ko:
                        patch["Row_label_ko"] = row_label_ko
                else:
                    if manual_value_ko:
                        patch["Value_ko"] = manual_value_ko
                    if row_label_ko:
                        patch["Row_label_ko"] = row_label_ko
                    if row_label_source:
                        patch["Row_label_source"] = row_label_source
                locals_present = [c for c in LANG_VALUE_COLUMNS
                                  if norm(table.cell(target_row, c))]
                unsynced_locals = [c for c in locals_present
                                   if c != "Value_ko" or not manual_value_ko]
                if unsynced_locals:
                    result["warnings"].append(
                        f"{key[1]}/{key[2] or '-'}: 该行带本地化列 "
                        f"{','.join(unsynced_locals)}，本次未同步这些本地化值，"
                        f"本地化值需人工同步（技能硬门 5）。")
                update_plan.append({
                    "staging": rid, "table": table.table_id,
                    "record_id": target_rid, "match_key": key,
                    "row_key": key[1], "slot_key": key[2],
                    "section": key[3], "line_order": key[4],
                    "expected_fields": patch,
                })
                continue
            # CREATE：克隆姊妹行
            if dockey_missing:
                result["failed"].append({"staging": rid, "row_key": key[1],
                                         "reason": f"Document_key 字典无 {target_key} 行，CREATE 已中止"})
                continue
            if sibling is None:
                result["failed"].append({"staging": rid, "row_key": key[1],
                                         "reason": "目标无此行且未指定姊妹机，无法克隆新建"})
                continue
            sibling_hits = sibling.matches(key)
            if len(sibling_hits) > 1:
                result["failed"].append({
                    "staging": rid, "row_key": key[1], "match_key": key,
                    "reason": f"姊妹机 {sibling_key} 存在重复完整键，拒绝猜测克隆对象",
                })
                continue
            if not sibling_hits:
                result["failed"].append({"staging": rid, "row_key": key[1],
                                         "reason": f"姊妹机 {sibling_key} 也没有该行，无法克隆"})
                continue
            if not dockey_record:
                dockey_record = find_dockey_record(target_key)
                if not dockey_record:
                    dockey_missing = True
                    result["failed"].append({"staging": rid, "row_key": key[1],
                                             "reason": f"Document_key 字典无 {target_key} 行"
                                                       "（字典建行是人工步骤），整批 CREATE 中止"})
                    continue
            _, sib_row = sibling_hits[0]
            payload: dict = {}
            for col in CLONE_SCALARS:
                value = sibling.cell(sib_row, col)
                if value not in (None, "", []):
                    payload[col] = norm(value) if not isinstance(value, (int, float)) \
                        else value
            for col in CLONE_LINKS:
                value = sibling.cell(sib_row, col)
                if isinstance(value, list) and value:
                    payload[col] = [{"id": item.get("id")} for item in value
                                    if isinstance(item, dict) and item.get("id")]
            payload["Document_key_link"] = [{"id": dockey_record}]
            payload["Source_lang"] = source_lang or \
                norm(sibling.cell(sib_row, "Source_lang"))
            payload["Row_label_source"] = row_label_source or \
                norm(sibling.cell(sib_row, "Row_label_source"))
            payload["Value_source"] = manual_value
            if manual_value_ko:
                payload["Value_ko"] = manual_value_ko
            if row_label_ko:
                payload["Row_label_ko"] = row_label_ko
            expected_fields = {"Value_source": manual_value}
            if is_kr:
                expected_fields.update({
                    "Row_label_source": row_label_source,
                    "Source_lang": source_lang,
                })
                if manual_value_ko:
                    expected_fields["Value_ko"] = manual_value_ko
                if row_label_ko:
                    expected_fields["Row_label_ko"] = row_label_ko
            elif manual_value_ko:
                expected_fields["Value_ko"] = manual_value_ko
            create_plan.append({
                "staging": rid, "table": table.table_id, "match_key": key,
                "row_key": key[1], "slot_key": key[2], "section": key[3],
                "line_order": key[4],
                "payload": payload, "expected_fields": expected_fields,
            })

        if is_kr and result["failed"]:
            result.update(
                status="rejected",
                error="KR 入库结构预检失败；source-first 要求整批正式源表零写入",
                formal_source_writes=0,
            )
            return

        result["writes_started"] = bool(update_plan or create_plan)
        for entry in update_plan:
            upsert(entry["table"], entry["record_id"], entry["expected_fields"])
            result["updated"].append(dict(entry))
        for entry in create_plan:
            fields = list(entry["payload"].keys())
            batch_create(entry["table"], fields,
                         [[entry["payload"][field] for field in fields]])
            public = {key: value for key, value in entry.items() if key != "payload"}
            result["created"].append(public)

        # 读回验证：按完整四元键命中唯一行，并核验所有合同字段。
        spec_after = Table(SPEC_TABLE, target_key)
        holder_after = Table(PLACEHOLDER_TABLE, target_key)
        after_tables = {SPEC_TABLE: spec_after, PLACEHOLDER_TABLE: holder_after}
        for entry in result["updated"] + result["created"]:
            table_after = after_tables[entry["table"]]
            hits = table_after.matches(tuple(entry["match_key"]))
            if len(hits) != 1:
                entry["readback_ok"] = False
                failure = {"staging": entry["staging"],
                           "match_key": entry["match_key"],
                           "reason": f"完整键读回命中 {len(hits)} 行，期望 1 行"}
                result["readback_failures"].append(failure)
                continue
            readback_id, readback_row = hits[0]
            actual_fields = {
                field: norm(table_after.cell(readback_row, field))
                for field in entry["expected_fields"]
            }
            expected_fields = {
                field: norm(value) for field, value in entry["expected_fields"].items()
            }
            mismatches = {
                field: {"expected": expected_fields[field],
                        "actual": actual_fields[field]}
                for field in expected_fields
                if expected_fields[field] != actual_fields[field]
            }
            entry["readback_record_id"] = readback_id
            entry["readback_fields"] = actual_fields
            entry["readback_ok"] = not mismatches
            if mismatches:
                result["readback_failures"].append({
                    "staging": entry["staging"],
                    "record_id": readback_id,
                    "match_key": entry["match_key"],
                    "field_mismatches": mismatches,
                })

        # 只有正式源表读回完全一致，才允许暂存行回填“已入库”。
        for entry in result["updated"] + result["created"]:
            if not entry.get("readback_ok"):
                upsert(STAGING_TABLE, entry["staging"],
                       {"入库结果": f"失败:正式源表读回不匹配 {today}"})
                continue
            action = "update" if "record_id" in entry else "create"
            source_record_id = entry["readback_record_id"]
            suffix = f" 克隆自 {sibling_key}" if action == "create" else ""
            upsert(STAGING_TABLE, entry["staging"],
                   {"入库结果": f"已入库 {action} {source_record_id}{suffix} {today}"})
        for entry in result["failed"]:
            upsert(STAGING_TABLE, entry["staging"],
                   {"入库结果": f"失败:{entry['reason'][:60]} {today}"})

        if result["readback_failures"]:
            result.update(
                status="failed",
                error="正式源表写后读回不满足合同；未对相关暂存行声称入库成功",
                summary=(f"{target_key}: 写后读回失败 "
                         f"{len(result['readback_failures'])} 行，见 readback_failures。"),
            )
            return

        result["close_checks"] = run_close_checks(target_key, job_dir)
        check_ok = (result["close_checks"].get("check") or {}).get("ok")
        result.update(status="done", summary=(
            f"{target_key}: 更新 {len(result['updated'])} 行、新建 {len(result['created'])} 行、"
            f"失败 {len(result['failed'])} 行、跳过 {len(result['skipped'])} 行；"
            f"sync+check {'通过' if check_ok else '未通过/未跑，见 close_checks'}。"
            f"{' 警告 ' + str(len(result['warnings'])) + ' 条。' if result['warnings'] else ''}"))
    except Exception as exc:  # noqa: BLE001
        result.update(status="failed", error=str(exc)[-1500:],
                      trace=traceback.format_exc()[-1500:])
    finally:
        result["finished_at"] = datetime.now(timezone.utc).isoformat()
        (job_dir / "result.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
