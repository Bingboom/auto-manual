#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""corpus_audit_2026-08 确定性统计脚本。

只读本目录四个 CSV（manuals.csv / topics.csv / topic_ledger.csv / reconstruction.csv），
重算盘点报告（manual_ia_audit_2026-08.md）与骨架库设计文档引用的全部核心数字，
并做一致性断言；任何断言失败 exit 1。

用法：python3 stats.py
口径定义见同目录 README.md。
"""
import csv
import os
import sys
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))


def read(name):
    with open(os.path.join(HERE, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


manuals = read("manuals.csv")
topics = read("topics.csv")
ledger = read("topic_ledger.csv")
recon = read("reconstruction.csv")

failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


def pct(a, b):
    return f"{100.0 * a / b:.1f}%"


# ---------------- 分母 ----------------
files = {r["file_seq"] for r in manuals}
independents = [r for r in manuals if r["independent_content"] == "Y"]
pairs = {(r["sku"], r["region"]) for r in manuals}

n_files, n_contents, n_pairs = len(files), len(independents), len(pairs)

print("=" * 62)
print("语料盘点数据集 corpus_audit_2026-08 — 全量重算")
print("=" * 62)
print()
print("[1] 三个分母")
print(f"  磁盘文件            : {n_files}")
print(f"  去重后独立内容      : {n_contents}")
print(f"  (SKU, 区规) 组合    : {n_pairs}")

check(n_files == 59, f"文件数 {n_files} != 59")
check(n_contents == 58, f"独立内容 {n_contents} != 58")
check(n_pairs == 57, f"(SKU,区规) {n_pairs} != 57")

# 折叠对结构校验
alias_rows = [r for r in manuals if r["independent_content"] == "N"]
check(len(alias_rows) == 2, f"别名行数 {len(alias_rows)} != 2")
mx = [r for r in alias_rows if r["region"] == "墨西哥规"]
mis = [r for r in alias_rows if r["region"] == "日规"]
check(len(mx) == 1 and len(mis) == 1, "折叠对行缺失（墨西哥规/错档件）")
if mx and mis:
    us_row = [r for r in manuals if r["slug"] == mx[0]["alias_of"] and r["region"] == "美加规"]
    check(len(us_row) == 1 and us_row[0]["file_seq"] == mx[0]["file_seq"],
          "折叠对1（HTE153 墨=美加）须为 1 文件 2 槽位：两行共 file_seq")
    tgt = [r for r in manuals if r["slug"] == mis[0]["alias_of"]]
    check(len(tgt) == 1 and tgt[0]["file_seq"] != mis[0]["file_seq"],
          "折叠对2（HTE152 错档=HTE154 日规变体）须为 2 文件 1 独立内容：file_seq 各自独立")

# 区规两口径（登记行=槽位口径：墨西哥规与 HTE154 日规变体各占一行；文件总数仍以 file_seq 去重计）
print()
print("  区规分布（登记行口径 / 独立内容口径）：")
reg_rows = Counter(r["region"] for r in manuals)
reg_contents = Counter(r["region"] for r in independents)
# 次键=区规名，保证同计数区规的输出顺序跨运行确定（set 迭代序受哈希随机化影响）
for reg in sorted(set(reg_rows) | set(reg_contents), key=lambda x: (-reg_rows[x], x)):
    print(f"    {reg}: {reg_rows[reg]} 登记行 / {reg_contents.get(reg, 0)} 独立内容")
check(sum(reg_rows.values()) == len(manuals), "区规登记行合计 != 总行数")
check(len(manuals) == n_files + 1, "登记行数应 = 文件数 + 1（墨西哥规槽位别名行共享文件）")

n_no_text = sum(1 for r in manuals if r["has_text_layer"] == "N")
print(f"  转曲件（无文字层）  : {n_no_text}/{n_files}（有文字层 {n_files - n_no_text}）")
check(n_no_text == 8, f"转曲件 {n_no_text} != 8")

# ---------------- 槽位 ----------------
by_book = {}
for t in topics:
    by_book.setdefault(t["slug"], []).append(t)

indep_slugs = [r["slug"] for r in independents]
check(len(set(indep_slugs)) == 58, "独立内容 slug 不唯一")
check(set(by_book) == set(indep_slugs), "topics.csv 的书集合 != 独立内容集合")

raw_total = len(topics)
norm_rows = [t for t in topics if t["topic_id_normalized"]]
norm_total = len(norm_rows)

print()
print("[2] 槽位总账")
print(f"  原始槽位（分解忠实层）: {raw_total}")
print(f"  归一后槽位（骨架统计口径，normalize:topic-ledger）: {norm_total}")
print(f"  归一化删除/收敛槽位   : {raw_total - norm_total}"
      "（HTE156中 重复封底 1 + W7 层级吸收 3 + 同书多实例收敛 3）")
print(f"  平均章/本（归一口径） : {norm_total / n_contents:.1f}")

check(raw_total - norm_total == 7, f"归一删除槽 {raw_total - norm_total} != 7")

# ---------------- 词表与三档 ----------------
tier_of = {r["topic_id"]: r["tier"] for r in ledger}
check(len(tier_of) == 30, f"归一词表 {len(tier_of)} != 30 个 id")
used_ids = {t["topic_id_normalized"] for t in norm_rows}
check(used_ids <= set(tier_of), f"topics 出现词表外 id: {sorted(used_ids - set(tier_of))}")
check(set(tier_of) <= used_ids, f"词表 id 零使用: {sorted(set(tier_of) - used_ids)}")

tier_slots = Counter(tier_of[t["topic_id_normalized"]] for t in norm_rows)
tier_ids = Counter(tier_of.values())
print()
print("[3] 三档复用率（归一口径，按槽位加权）")
for tier in ("universal", "category_common", "specific"):
    print(f"  {tier:16s}: {tier_ids[tier]:2d} id / {tier_slots[tier]:3d} 槽 / {pct(tier_slots[tier], norm_total)}")
check(sum(tier_slots.values()) == norm_total, "三档之和 != 归一槽位总数")

core = tier_slots["universal"] + tier_slots["category_common"]
core_ids = tier_ids["universal"] + tier_ids["category_common"]
print(f"  核心 {core_ids} id（universal+category_common）承担 {core}/{norm_total} = {pct(core, norm_total)}")
check(core_ids == 19, f"核心 id 数 {core_ids} != 19")

# ---------------- 逐 topic 覆盖率（§3 序列） ----------------
presence = Counter()
for slug, ts in by_book.items():
    for tid in {t["topic_id_normalized"] for t in ts if t["topic_id_normalized"]}:
        presence[tid] += 1

print()
print(f"[4] 逐 topic 覆盖率（归一 id，存在性 /{n_contents} 独立内容）")
order = [r["topic_id"] for r in ledger]
for tier in ("universal", "category_common", "specific"):
    print(f"  -- {tier} --")
    ids = [i for i in order if tier_of[i] == tier]
    for tid in sorted(ids, key=lambda x: -presence[x]):
        print(f"    {tid:32s} {presence[tid]:2d}/{n_contents}  {pct(presence[tid], n_contents)}")

# ---------------- 五格成员 ----------------
cell_members = Counter(r["cell"] for r in independents)
print()
print("[5] 五格成员数（独立内容口径）")
CELLS = ["MAIN@INTL", "MAIN@JP", "MAIN@CN", "BP@INTL", "BP@JP"]
for c in CELLS:
    print(f"  {c:10s}: {cell_members[c]}")
print(f"  outlier   : {cell_members['outlier']}")
check(sum(cell_members[c] for c in CELLS) + cell_members["outlier"] == n_contents,
      "格成员之和 + outlier != 独立内容数")
check(cell_members["outlier"] == 3, f"outlier {cell_members['outlier']} != 3")
check(set(cell_members) <= set(CELLS) | {"outlier"}, f"未知 cell 值: {set(cell_members) - set(CELLS) - {'outlier'}}")

# ---------------- 重构测试 ----------------
check(len(recon) == n_contents, "reconstruction.csv 行数 != 独立内容数")
check({r["slug"] for r in recon} == set(indep_slugs), "reconstruction slug 集合 != 独立内容集合")
mcell = {r["slug"]: r["cell"] for r in independents}
for r in recon:
    check(r["cell"] == mcell[r["slug"]], f"cell 不一致: {r['slug']}")

pure = [r for r in recon if r["pure_deletion"] == "Y"]
outl = [r for r in recon if r["outlier"] == "Y"]
overlay1 = [r for r in recon if r["pure_deletion"] == "N" and r["outlier"] == "N"]
CLOSED_SET = {"T1", "T2", "T3", "T4", "T6", "T7"}
for r in overlay1:
    check(r["overlays_used"] in CLOSED_SET,
          f"{r['slug']} overlay『{r['overlays_used']}』不在封闭集 {sorted(CLOSED_SET)}")
for r in pure:
    check(r["overlays_used"] == "", f"纯通过成员带 overlay: {r['slug']}")
for r in outl:
    check(r["pure_deletion"] == "N" and r["cell"] == "outlier", f"outlier 行不自洽: {r['slug']}")

print()
print("[6] 重构测试汇总（印刷页序口径：同页不计先后；fcc/regulatory 浮动片段与 T5 槽位对参数豁免）")
print(f"  纯删除通过      : {len(pure)}/{n_contents} = {pct(len(pure), n_contents)}")
print(f"  ≤1 条 overlay   : {len(pure) + len(overlay1)}/{n_contents} = {pct(len(pure) + len(overlay1), n_contents)}")
ov_counts = Counter(r["overlays_used"] for r in overlay1)
print(f"  需 1 条 overlay : {len(overlay1)} 本（"
      + "、".join(f"{k}×{v}" for k, v in sorted(ov_counts.items())) + "）")
print(f"  无法重构 outlier: {len(outl)} 本")
check(len(pure) + len(overlay1) + len(outl) == n_contents, "纯删除 + overlay + outlier != 独立内容数")
check(len(outl) == 3, f"outlier {len(outl)} != 3")

print()
print("  逐格通过率（纯删除 / 成员）：")
for c in CELLS:
    mem = [r for r in recon if r["cell"] == c]
    p = sum(1 for r in mem if r["pure_deletion"] == "Y")
    print(f"    {c:10s}: {p}/{len(mem)} = {pct(p, len(mem))}")

src = Counter(r["verdict_source"] for r in recon)
print(f"  判定来源: " + ", ".join(f"{k}={v}" for k, v in sorted(src.items())))
check(set(src) <= {"phaseA", "phaseB-remeasure", "hte152-round", "hte153-round"},
      f"未知 verdict_source: {set(src)}")

# ---------------- 多实例收敛抽查 ----------------
hp15 = [t for t in by_book.get("HTP015-Jackery-Battery-Pack-V2-0-2026-07-29", [])
        if t["topic_id_raw"] == "symbol_meaning"]
check(len(hp15) == 2 and sum(1 for t in hp15 if t["topic_id_normalized"]) == 1,
      "HTP015 日规 symbol_meaning 应为 2 原始实例收敛 1 槽位")

# ---------------- 结果 ----------------
print()
if failures:
    print("!! 一致性断言失败：")
    for m in failures:
        print("   -", m)
    sys.exit(1)
print("全部一致性断言通过。")
