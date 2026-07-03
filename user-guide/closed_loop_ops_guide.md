# 闭环运营手册（操作者版）

Updated: 2026-07-02

这是 Milestone G（G0–G7，PR #514–#521）交付的闭环机制的**操作者视角**说明：
日常要跑什么命令、什么时候跑、看到什么算正常。实现细节和字段含义在
[`../code-as-doc/dev/revision_ledger.md`](../code-as-doc/dev/revision_ledger.md)（维护者向），
本文只讲"人怎么用"。

一句话背景：从 Milestone G 起，**评审者对文档的每一条修改都会自动记账、
自动结清，被采纳的翻译修正可以一键收割进语料库**。系统自动做大部分事，
留给人的只有"过目并批准"这一类不该自动的决定。

---

## 1. 修订回灌账本（revision ledger）

### 1.1 哪些是全自动的（不用管）

- **记账**：每次跑 `cloud_doc_backport.py run-review-branch`，评审者的每条修改
  （机器原文 → 评审者改文，带型号/区域/文件出处）自动追加到
  `reports/revision_ledger/ledger.jsonl`。
- **结清**：下一轮跑 backport（或手动跑 `reconcile`）时，系统自动回看之前
  的账：评审者的改法最终留在文档里了吗？自动打上判决——
  `accepted_as_proposed`（采纳）/ `rejected`（被拒）/ `edited_further`（又被改了），
  并从 git 查出合并 PR、时间、作者一并记录。标点/换行级别的差异不会误判
  （相似度匹配，阈值 0.90）。

> 账本是**本机文件**，不进 git、CI 也看不到。它跟着跑 backport 的那台机器走。

### 1.2 三个人工命令

**① 看健康度（想看就看，建议每月至少一次）**

```bash
python3 -m tools.revision_ledger stats
```

看三个数字：

- `reflow_rate` **回灌率**：多少账已经结清。健康线 > 0.9；长期偏低说明
  评审分支合并后没有下一轮 backport 去结账（跑一次
  `python3 -m tools.revision_ledger reconcile --auto` 即可手动结清）。
- `acceptance_rate` **采纳率**：结清的账里，评审者的修正有多少原样留住了。
- `top_corrected_sources` **被改最多的文件**：同一个文件反复被改，是
  "模板本身该改了"的信号（这是未来"语料驱动模板优化"的输入）。

**② 收割语料候选（每轮评审收尾后跑一次）**

```bash
python3 -m tools.revision_ledger tm-candidates
```

把所有"被采纳的翻译修正"投射成候选清单，写到
`reports/revision_ledger/tm_candidates.jsonl`。每行一对句子：

- `old_text`：机器/旧的译文
- `new_text`：评审者改后的译文
- `lang`：目标语言；`provenance`：出处（哪个型号/区域/文件/PR）
- `delta_hash`：这条候选的编号，批准时用它

**③ 批准并写入语料库（人批门——只有这一步会写飞书）**

过目候选清单，把要采纳的 `delta_hash` 交给 `tm-apply`：

```bash
# 先空跑看计划（不带 --write，什么都不会动）：
python3 -m tools.revision_ledger tm-apply --approve <delta_hash>

# 确认后真写（B 库 = $FEISHU_TRANSLATION_MEMORY_BASE_TOKEN 指向的规范库）：
python3 -m tools.revision_ledger tm-apply \
  --approve-file approved.txt \
  --tm-binding "$FEISHU_TRANSLATION_MEMORY_BASE_TOKEN:<Translation_Memory表id>" --write
```

规则（都是系统强制的，列出来是让你放心）：

- 没批准的哈希**一律不写**；重复批准是幂等的（已写过的显示 `already`）。
- 写入按"旧译文精确匹配 TM 行"定位，找不到就**弃权**（`unresolved`），
  绝不猜行乱写。弃权的候选留在清单里，走人工的
  `bilingual-tm-maintenance` 流程补录。
- 每条写入后 GET 回读校验。

**走一遍完整例子**：KR 手册评审 → 评审者把某句韩文改得更地道 → backport
收回（自动入账）→ 下轮自动结清为"采纳" → `tm-candidates` 列出这对句子 →
你过目说 OK → `tm-apply --write` 写进 TM → **下次韩文预翻译直接命中新译法**。
评审者的智慧从此不再流失。

---

## 2. TM 命中率台账

每次跑 docx 预翻译（`lark-tm-translation-preprocess` skill），运行结果里
自动多了三个数字：`units_total`（尝试翻译的句子数）、`units_matched`
（命中语料库的句子数）、`hit_rate`（命中率），并自动累计到
`reports/tm_hit_rate/ledger.jsonl`。

看趋势：

```bash
python3 -m tools.tm_hit_rate stats
```

按语言对分桶（如 `en->ko`）。**第一次真实预翻译跑完就有基线数字**；
之后每次语料入库（上面的 ③），都应该在这条曲线上看到回报。
命中率不涨 = 入库的语料没用在刀刃上，值得回头看候选的筛选标准。

---

## 3. 回收提醒哨兵（不用记得跑 backport 了）

每天 02:00 UTC，`backport-reminder.yml` 自动比对每个**评审中**云文档的
现文本和它上次回收的基线：

- 有没回收的编辑 → 仓库里自动开/更新一个
  **`[backport-reminder]`** issue，列出哪些文档、哪个分支、云文档链接。
- **你要做的**：看到 issue，对着列出的文档跑
  `python tools/cloud_doc_backport.py run-review-branch --doc-name <名> --cloud-doc <链接>`。
  回收完成后，下一次哨兵运行会自动把 issue 关掉——不用手动关。
- 从没回收过的评审文档会标 `no_baseline`（评审开始后一次 backport 都没跑），
  处理方式相同。

> 哨兵只报不动手，也不写任何飞书数据。首次启用建议在 GitHub Actions 页面
> 手动 `Run workflow` 跑一遍验证凭据（见 §5）。

---

## 4. 给审核人出带批注的 PDF

当审核方只看 PDF 时，把 QC 结果直接印在 PDF 上：

```bash
# ① 先出 QC 结果（已有流程）：
python tools/content_lint.py --data-root data/phase2 --json --write-report

# ② 渲染到构建好的 PDF 上：
python tools/pdf_annotate.py \
  --pdf docs/_build/<model>/<region>/pdf/<manual>.pdf \
  --findings reports/content_qc/<run-id>/findings.json
```

得到 `<manual>_annotated.pdf`（原 PDF 一个字节都不动）。每个高亮带批注：
什么问题、**源头在哪张表哪个字段**、建议动作。定位不到的问题会汇总在
第 1 页的批注里，不会错标。

**铁律：批注只是给人看的呈现。改错永远回到源头**（云文档/修订 docx →
backport），不要在 PDF 上改。

---

## 4.5 模板更新 × 在飞评审（跨面协作的唯一日常场景）

模板只能在 **auto-manual** 改（PR 合入 main 后由镜像自动带到 Hello-Docs
main，分钟级、零手工）；但**在飞的评审分支不会自动吃到新模板**。按改动
性质二选一：

**情况 A：不急着进本轮评审（默认，适合措辞/错别字级改动）**
什么都不用做——本轮按旧模板走完，下一次 Start Review / 构建自然用新模板。
评审中途换底会给评审者制造困惑，小改动一律走这条。

**情况 B：必须进在飞评审（模板有实质错误）**，严格按序：

1. **先收干净**：对该评审跑一次 backport，把云文档未回收的修订收进
   账本/源表（回收哨兵 issue 就是检查单）。
2. 合模板 PR → 自动镜像到 Hello-Docs main。
3. **重触发该行 Start Review**（重新勾"是否进入Review"）——语义是
   force restart：评审分支从最新模板+数据状态强制重播种。
4. 评审继续。安全性由分工保证：已进**源表**的修正重播种会带回来；
   评审者的文字修订不丢——**云文档才是评审者的真身**，重播种后
   backport 会拿新渲染重新 diff 云文档、把修订重新收集归位。
   跳过第 1 步的代价：修订仍在云文档里能重收，但账本少一轮记录。

背景：评审中发现"这句该改模板"（Class T）时，backport 不直接写模板，
而是产出 `template_sync_proposal` → 模板修改回 auto-manual 走 PR——
本节描述的就是这条回路的下半程。

## 5. 首跑清单（一次性，做完划掉）

- [ ] **命中率基线**：跑一次真实的 docx 预翻译，`tm_hit_rate stats` 出现
      第一个基线数字
- [ ] **哨兵首跑**：GitHub Actions → Backport Reminder → Run workflow，
      确认凭据链路通（未配置时它会在 Summary 里列出缺哪个 secret）
- [ ] **A 库迁移**：把旧 A/wiki 归档库（`X3O8…`）里 B 库没有的句对迁到
      B 库（可用 `bilingual-tm-maintenance` 流程）。迁移完成前，
      **不要放量跑 ③ 语料写入**——新语料写进分裂的库会变烂账

## 6. 运营节奏（建议）

| 频率 | 做什么 |
| --- | --- |
| 每轮评审收尾 | `tm-candidates` → 过目 → `tm-apply`（§1.2 ②③） |
| 有 `[backport-reminder]` issue 时 | 对着清单跑回收（§3） |
| 每月 | `revision_ledger stats` + `tm_hit_rate stats`，看回灌率/命中率曲线；`top_corrected_sources` 里反复出现的文件记下来（模板优化候选） |

跑了 2–3 轮、流程顺手之后，这套程序会固化成 skill（届时本文档仍是底层参考）。
