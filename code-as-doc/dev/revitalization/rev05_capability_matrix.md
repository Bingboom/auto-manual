# REV-05 现有能力矩阵：命令 / 调度 / 归档 / 目录同步

- 台账项：REV-05（`code-as-doc/dev/manual_revitalization_execution.md` 第 48 行，PR #1188 分支 `docs/manual-revitalization-plan`）
- 口径时点：**2026-09-19T03:10:08Z – 2026-09-19T03:17:23Z（UTC）**，全部数据在此窗口内抓取
- 基线 ref：`origin/main` = **58767931ba8f8b5d35fff2a725febce8fba66c28**（`revert(web): withdraw the sideload conveyor lane (#1186)`，2026-09-17 03:50:34 -0700）
- 读取方式：只读，`git -C <repo> show origin/main:<path>`、`git ls-tree origin/main`、`git grep <pat> origin/main`；未 checkout、未写任何仓库文件或飞书表。行号均指 origin/main 版本（快照副本在本目录 `snapshot/` 下，可逐行复核）
- 状态标记：**已有** = 主线存在且有调用者/入口；**部分** = 存在但缺一环；**缺口** = 两个正交手段核实不存在；**待核实** = 仓库内查不到、需仓库外确认

---

## 1. CLI 动作全集（build.py，34 个动作，全部「已有」）

动作清单来源：`tools/build_cli.py:18-51`（choices 元组）+ `build.py:105`（`BUILD_ACTIONS = ("rst","word","html","pdf","md","all")` 注入 `*build_actions`，`build.py:122/244`）。分发：`tools/build_dispatch.py:351-378`（`ACTION_HANDLERS`）；未注册的动作（六个构建产物动作 + `preview`/`fast`）回落到默认构建处理器 `_dispatch_build_action`（`build_dispatch.py:450`，`preview`/`fast` 的行为注释见 `build_dispatch.py:253-262`）。入口装配：`tools/build_main.py:12-95`。

| 动作 | 一句话用途 | 证据 |
| --- | --- | --- |
| validate | 校验 config 与数据快照的结构/必填值（可 --model/--region 单目标） | build_dispatch.py:146-152 |
| doctor | 环境与目标预检；`--data-plane` 做单目标 phase2 快照只读预检 | build_cli.py:85-89 |
| asset-check | 资产注册表键解析与哈希核对；`--publish` 要求✅成品，`--refresh --write` 重算哈希 | build_cli.py:355-380 |
| asset-intake | 从 .ai/PDF 母版按版本化配方提取无字化资产到隔离目录 | build_cli.py:382-403 |
| new-line | 新产线脚手架：config+manifest+overrides+F6 只读 seed plan | build_cli.py:292-354 |
| rst / word / html / pdf / md / all | 六个构建产物动作（BUILD_ACTIONS），默认分发到 build_docs_command | build.py:105; build_dispatch.py:253-263 |
| idml | InDesign 生产 IDML / flow 交接导出（`--idml-mode production/flow/both`） | build_dispatch.py:283-348; build_cli.py:91-99 |
| review | runtime RST 构建 + review bundle 物化 | build_dispatch.py:159-161 |
| check | 质量门（run_check；`--refresh-review` 为参数预同步显式开关） | build_cli.py:107-115 |
| sync-review | 数据驱动刷新在审 review 派生物（`--sync-scope generated/params`） | build_cli.py:116-127 |
| sync-data | 飞书 phase2 源表全量快照同步（`--table` 选表，`--dry-run`） | build_cli.py:160,453-457 |
| spec-master-rebuild | 由拆分源表重建/回写 spec_master 总表（bootstrap/force-reseed/write-back） | build_cli.py:161-197 |
| translation-memory | TM 查询（--table/--section/--row-key/--lang/--limit） | build_cli.py:198-199,286-289 |
| queue-query | 飞书构建队列/评审队列只读查询（document-id/key、market、langs 等过滤） | build_cli.py:200-277 |
| queue-resolve-action | 把查询解析成唯一可执行队列动作（`--allow-multiple` 批量） | build_cli.py:278-283 |
| queue-execute | 解析队列行→dispatch 对应 GitHub workflow→等待→回读行返回终值 | build_cli.py:404-427; user-guide/hello_auto-doc.md:688 |
| process-review-start-queue | 消费 review-init 队列行（Start Review worker） | build_dispatch.py:217-218 |
| process-build-queue | 消费 Document_link 构建队列行；`--workflow-action build-draft-package/publish/web-publish` | build_cli.py:428-436 |
| listen-build-queue | 常驻监听构建队列（配套 scripts/listen_build_queue.ps1） | build_dispatch.py:225-226 |
| listen-message-control | 常驻监听 IM 消息控制通道 | build_dispatch.py:229-230 |
| publish | 发布 lane（run_publish，JP publish 等） | build_dispatch.py:233-234 |
| clean | 清理当前目标构建产物 | build_dispatch.py:249-250 |
| diff-report | 跟踪子树 git 差异报表 CSV/HTML（--from-ref/--to-ref/--report-dir） | build_cli.py:129-149 |
| release-manifest | 版本化发布追溯清单 | build_dispatch.py:241-242 |
| release-rebuild-verify | 按 manifest 重建并验证可复现（--manifest/--report） | build_cli.py:150-159 |
| preview | 单页快速物化预览（`--page`） | build_cli.py:128 |
| fast | runtime 源、免清理快速构建 | build_dispatch.py:253-262 |
| message-control-dry-run | IM 消息意图解析干跑（--message/--confirmed 等） | build_cli.py:200-232 |
| manual-index-query | 说明书目录/索引自然语言查询（--query-text） | build_cli.py:239-246; tools/manual_index_query.py:225-235 |

### 1.1 #1186 撤回动作核实（web-release / web-sideload / web-assemble / web-receipt：**不存在于 main，已确认**）

两个正交面 + 一个阳性对照：

1. **面 1 — CLI 选项面**：`tools/build_cli.py:18-51` 的 action choices 与 `build_dispatch.py:351-378` 的 `ACTION_HANDLERS` 均无这四个动作（逐行读取快照 `snapshot/tools_build_cli.py`、`snapshot/tools_build_dispatch.py`）。
2. **面 2 — 模块/全树内容面**：`git grep -c -e "<action>" origin/main` 四个词在全树命中仅两个历史文档（`code-as-doc/dev/merge_authorizations.md`；`code-as-doc/dev/js100i_eu_en_web_release_readiness.md` 命中 web-release），**代码目录（build.py、tools/、.github/）零命中**；`git ls-tree origin/main tools/` 过滤 `release|sideload|assemble|receipt` 只有 `release_*`（印刷发布追溯族）与 `rtd_deployment_receipt.py`，无 web-release/web-sideload 等动作模块。
3. **阳性对照**：同一 grep 形式对 `web-publish` 命中 `tools/build_cli.py`（2 处），证明检索方法有效。

### 1.2 队列模式 web-publish：**已有**

- `tools/build_cli.py:428-436`：`process-build-queue --workflow-action` choices 含 `web-publish`；`build_cli.py:263-270`：`--query-workflow-action` 帮助文本列出 `web-publish`。
- 运行入口：`.github/workflows/feishu-web-publish-queue.yml:114`（`python build.py process-build-queue ... --workflow-action web-publish`）。
- 注意执行平面：该 workflow 第 83-86 行硬校验 `GITHUB_REPOSITORY == Bingboom/Hello-Docs`，即 web-publish 队列**只在 Hello-Docs 业务面镜像上执行**；auto-manual 主仓只承载定义。

---

## 2. GitHub workflows（origin/main `.github/workflows/`，14 个）

来源：`git ls-tree origin/main .github/workflows/`；触发器逐个读取 on: 块（快照 `snapshot/workflows/`）。

| Workflow | 触发器 | 用途一句话 | 备注 |
| --- | --- | --- | --- |
| backport-reminder.yml | **cron 每日 02:00 UTC** + dispatch | 只读提醒：在审云文档有未回收编辑（回写本身 CLI-only） | 文件头注释（Milestone G6） |
| cred-health-check.yml | **cron 每日 07:00 UTC** + dispatch | `tools/cred_health_check.py` 凭据健康巡检 | — |
| feishu-build-queue.yml | dispatch（**cron 有意禁用**，yml:4-8 注释） | 消费队列 `--workflow-action publish`（印刷 publish lane） | 调度缺口的现状证据 |
| feishu-draft-build-queue.yml | dispatch | 消费队列 `--workflow-action build-draft-package` | — |
| feishu-schema-parity.yml | **cron 每日 01:00 UTC** + dispatch | PROD/DEV Bitable 结构差异告警（只读） | — |
| feishu-start-review.yml | dispatch | 消费 review-init 队列（process-review-start-queue） | — |
| feishu-web-publish-queue.yml | dispatch | web-publish 队列→publish 分支装配→PR→HTML_link 回写 | 仅 Hello-Docs 平面（yml:83-86）；详见 §5 |
| manifest-regenerate-diff.yml | PR（configs/manifests 路径）+ dispatch | manifest lint + fold 再生成 diff 护栏 | — |
| manual-validation.yml | **push main + 所有 PR** | CI 验证（ruff/unittest/guardrails/gitleaks 等） | — |
| nightly-render.yml | **cron 每日 08:45 UTC** + dispatch | 固定 fixture 上全 config doctor 扫 + IDML 冒烟（渲染漂移监测） | tools/nightly_render.py 首部 docstring |
| phase2-content-backup.yml | **cron 每日 00:30 UTC** + dispatch | Bitable 源内容 point-in-time 导出为带日期 artifact（K4，归档能力之一） | 文件头注释 |
| review-branch-sync-check.yml | **cron 每日 02:30 UTC** + dispatch | review 分支漂移检查（--strict，出漂移开 sentinel） | — |
| review-preview.yml | PR（review/模板/数据路径）+ dispatch | review 预览包构建 | — |
| sync-hello-docs.yml | **push main** + dispatch | 主线代码同步到 Hello-Docs 镜像（对象级导入） | — |

**cron 全景（用于 §4 月报核实）**：6 个 cron 全部是**每日**（`0 2`、`0 7`、`0 1`、`45 8`、`30 0`、`30 2`），**无任何月度 cron**（day-of-month 位全为 `*`）。

---

## 3. RTD 工具族（tools/rtd_*.py，逐文件首行 docstring）

| 文件 | 职责（docstring 原文义） | 状态 |
| --- | --- | --- |
| tools/rtd_portal.py:1 | 冻结出版物之上的根级 Sphinx 门户；不读活数据不写库。`setup()` 挂 search index（:208）与 deployment receipt（:209） | 已有 |
| tools/rtd_portal_search.py:1 | 从渲染后的正式手册构建门户本地关键词索引 | 已有 |
| tools/rtd_alias_entry.py:1 | 根别名页 = 印刷/QR 可计数入口层，指向嵌套正式路由（noindex + canonical，:19-25） | 已有（M4 可复用件） |
| tools/rtd_page_metadata.py:1 | 页面 head 元数据全部派生自冻结出版身份，无手写 | 已有 |
| tools/rtd_deployment_receipt.py:1 | 把一次成功的冻结 Sphinx 部署绑定到源与线上字节：构建期写 `manual-deployment.json`（write_deployment_receipt :69-81），事后 `verify_deployment` 拉线上字节逐哈希核对（:239-285） | 已有（但见 §6 缺口） |
| tools/rtd_analytics.py:1 | 可选、无 cookie 的 Cloudflare Web Analytics beacon 注入（仅 32hex token 校验 + script 标签，:12-36）——**是采集端不是报表端** | 已有 |
| tools/rtd_publication_catalog.py:1 | 对冻结 RTD 链接做目录分组，不把 legacy 语言槽当译文；唯一调用者是 rtd_portal.py:12,98（门户构建期） | 已有 |
| tools/rtd_feedback.py:1 | 冻结 Web 页的可选本地反馈入口（固定 HTTPS/mailto，不携带出版物数据） | 已有 |
| tools/rtd_portal_assets/（目录树） | 门户静态资产 | 已有 |

相邻的运维只读件：`tools/manual_operations_health.py:1`（冻结 Web 产物只读健康报告，schema manual-operations-health/v2）、`tools/manual_operations_online_health.py:1`（有界 HTTP 可达性检查，「never deployment or translation proof」）、`tools/printed_url_inventory.py:3-12`（印刷 URL 清单 + liveness，注明 monthly ops 人工节奏）、`tools/flow_dashboard.py:3-12`（三流仪表，按月分桶）。

---

## 4. 月报调度核实（方案存疑项「月报 10-01 首跑，未核实」）

**结论：报表实现「已有」；调度「不在仓库内」——调度位置未在仓库内，待操作者确认。**

- **实现已有**：`tools/cwa_report.py`（docstring :1-13——Cloudflare Web Analytics GraphQL 只读表格化报表，凭据仅环境变量，site-tag ≠ beacon token）。参数只有 `--days/--top/--site-tag/--json`（:111-114），输出打印到 stdout，**无落盘/存档参数**。文档入口：`code-as-doc/dev/rtd_manual_portal.md:104`（`python tools/cwa_report.py --days 7`）。
- **调度不存在于仓库，三个独立面核实**：
  1. `.github/workflows/` 6 个 cron 全部是每日，无月度 cron（§2 全景表，逐文件读 on: 块）；
  2. `git grep -c -e "月报" origin/main` 全树**零命中**（同轮阳性对照：`月度` 在 `code-as-doc/manual_operations_growth_plan.md:75` 命中「月度内容运营例会」，证明中文检索有效）；
  3. 合并授权登记行 MA-086（`code-as-doc/dev/merge_authorizations.md:224`）明文记载 #1163（cwa_report 合入，2026-09-16）范围**「不含：定时任务/工作流」**，操作者原话「合了 顺便把月度报表做成定时任务」——即定时化被显式留在 #1163 之外。
- 「10-01 首跑」出处是方案侧记载（PR 分支 `code-as-doc/manual_production_revitalization_plan.md:37`：本次未核实任务是否启用、执行凭据、输出位置及失败处理）。仓库内查不到任何 launchd/OpenClaw/Claude scheduled task 配置（`git grep -i "launchd\|crontab\|schedule" origin/main -- scripts/ integrations/` 零有效命中）。**是否已在操作者本机/Claude 排程建立、是否 10-01 首跑：未能确认（原因：调度若存在则在仓库外，本轮只读仓库）→ 待操作者确认。**

---

## 5. 目录 / 回执 / 归档能力

| 部件 | 谁调用 | 写后回读 | 状态 |
| --- | --- | --- | --- |
| tools/write_web_publish_html_link.py（web-publish 队列回执写入器：由 publish_meta 确定性拼 RTD URL 写回 Document_link.HTML_link） | `.github/workflows/feishu-web-publish-queue.yml:270`（唯一自动调用者，git grep 全树核实） | **无**：写链为 `write_html_link_records`（write_publish_html_link.py:184-201）→ `LarkCliSource.upsert_record`（sync_data.py:480-520，`+record-upsert`），只依赖 CLI 返回，无写后 GET 校验 | 部分 |
| tools/write_publish_html_link.py（印刷 publish 链接写入器 + 上表的库依赖） | 仅 write_web_publish_html_link.py:25 导入 + 自身 CLI main（:347）；workflows 无直接调用（git grep `.github/` 零命中） | 同上，无 | 部分 |
| tools/rtd_publication_catalog.py（门户目录分组） | tools/rtd_portal.py:12,98（Sphinx 构建期） | 只读，不适用 | 已有 |
| 目录同步（Feishu 发布文档管理/运营表方向） | 只读查询 skill `.agents/skills/product-manual-catalog/scripts/query_product_manuals.py`；**写入器不存在**（面 1：`git grep -l "发布文档管理\|运营表" origin/main -- tools/` 零命中；面 2：tools/ ls-tree 无 catalog 写模块） | — | **缺口**（M2 的「Git-only 在线目录登记」在方案里也定义为单独获批的后置事务） |
| 归档 A：飞书源内容备份 | phase2-content-backup.yml（每日 00:30 UTC，`tools/bitable_content_backup.py export`，带日期 artifact，K4） | artifact 上传由 Actions 保证 | 已有 |
| 归档 B：发布追溯 | `reports/releases/` 版本化树 + release-manifest / release-rebuild-verify 动作 + tools/release_snapshot.py / release_manifest*.py 族 | release-rebuild-verify 即回读式验证 | 已有 |
| 归档 C：设计交接包 | tools/idml/delivery.py（handoff zip；ls-tree + grep "handoff" 命中族） | — | 已有 |
| 归档 D：对象存储（OSS）归档 | **不存在通用 OSS 归档**：`git grep -i "oss" origin/main -- tools/ scripts/ .github/` 仅命中 `tools/dingtalk/alidocs_session.py:320-397`（钉钉 AliDocs 上传通道的 oss2 用法，属交付非归档）；面 2：tools/ 无 archive/oss 模块名 | — | 缺口（若需要） |

Web Publish 回执链的顺序事实（feishu-web-publish-queue.yml）：process-build-queue 渲染（:114）→ publish 分支 worktree（:123-159）→ `tools/publish_branch_assembly.py` 装配 docs/publish（:164-166）→ scope 校验只许 docs/publish/**（:184-218）→ push + 开/更新 publish→main PR（:220-264）→ **HTML_link 回写（:266-277）**→ 失败 sentinel issue（:317-328）。即 **HTML_link 在 PR 合并之前、RTD 部署发生之前就已写回**（URL 为确定性拼串，write_web_publish_html_link.py:69-75），workflow 内无 verify_deployment 调用。

---

## 6. 真实缺口节（对照 M1/M2/M4/M5 与 REV-08）

M 定义出处：PR 分支 `code-as-doc/manual_production_revitalization_plan.md:167-172`；REV-08 验收：台账 :51。

### M1 持续核对（新差异告警）
- **可复用**：manual_operations_health.py（冻结产物健康）、manual_operations_online_health.py（HTTP 可达）、printed_url_inventory.py liveness、既有告警模式（review-branch-sync-check / backport-reminder 的 cron+sentinel 骨架，queue-sentinel-issue action）。
- **真空白**：不存在把「冻结发布记录 ↔ 线上部署 ↔ 目录/回执」做成对账差异告警的任何 tool 或 workflow（面 1：§2 全部 14 个 workflow 逐个读过，无对账类；面 2：tools/ ls-tree 无 reconcile/对账模块名，`git grep -i "reconcil" origin/main -- tools/` 零命中）。M0 差异表工具同样空白（REV-06 的前置）。

### M2 自动登记（幂等机器字段更新）
- **可复用**：write_web_publish_html_link.py 的确定性 URL + upsert（天然可重放不重登）；queue_bound_binding 的 preflight（write_web_publish_html_link.py:118-121）。
- **真缺口 1 — 登记时机**：HTML_link 回写发生在 PR 合并/部署之前（§5 顺序事实），与 M2「部署失败不可登记为线上可用」语义冲突。
- **真缺口 2 — 写后回读**：自动写链无 GET 回读（§5 表）；AGENTS.md 的写后回读纪律只约束 agent 手工操作面。
- **真缺口 3 — 登记失败独立重试**：workflow 失败只开 sentinel issue（yml:317-328），无「目录写入失败进入重试，不重发整本」的独立重试通道。

### M4 稳定入口管理
- **可复用**：rtd_alias_entry.py（根别名 = 可计数印刷/QR 入口，noindex+canonical）、printed_url_inventory.py（印刷 URL/QR 登记 + liveness）、cwa_report.py 的 classify() 入口归类（snapshot/tools_cwa_report.py:43+）。
- **真空白**：跨站历史链接映射与变更记录（旧入口→HT-Doc）无任何工具（面 1：tools/ 模块名过滤 `redirect|legacy|mapping|migrat` 仅 export_spec_master_row_key_mapping.py，语义无关；面 2：内容 grep "redirect" 在 tools/scripts/.github 仅命中同源跳转防护与 review 预览页跳转，无 legacy 映射件）。

### M5 统计口径版本
- **可复用**：cwa_report.py 已有窗口参数（--days）与路径归类规则（classify）。
- **真缺口**：无「每期保存窗口/来源/过滤/采样 + 目录快照」的落盘机制——cwa_report.py 仅 stdout（:111-114 无输出路径参数），reports/ 下无统计存档目录约定。

### REV-08（两路径站点一致性：RTD 项目 / main 分支 / 发布 URL）
- **可复用**：rtd_deployment_receipt.py 整套——构建期回执（:69-81）、verify_deployment 拉线上字节逐哈希对源指纹（:239-285）、同源强制（:143）、跨源跳转拒绝（:96-101）；manual_operations_online_health.py。
- **真缺口 1 — 「目标 RTD 项目」维度不校验（读码求证）**：`_without_rtd_proxy_injection`（rtd_deployment_receipt.py:219-236）把 RTD 注入的 `readthedocs-project-slug` meta 用通配 `[A-Za-z0-9_.-]+`（:229-230）剥除后才比哈希——**从不与期望的项目 slug 比较**。字节校验能证明「这些字节来自这份冻结源」，不能证明「发到了正确的 RTD 项目」；base_url 完全由调用方提供。
- **真缺口 2 — 校验器无自动调用者**：`git grep verify_deployment origin/main` 只命中定义、tests/、以及 `code-as-doc/dev/rtd_deployment_receipt.md:85-89` 的手工 snippet；没有任何 workflow/queue 步骤调用（§5 顺序事实同证）。
- **真缺口 3 — base_url 双源可漂移**：`write_web_publish_html_link.py:33` 硬编码默认 `https://ht-doc.readthedocs.io`，workflow 侧又有 `vars.AUTO_MANUAL_RTD_BASE_URL || 'https://ht-doc.readthedocs.io'`（yml:71），两处独立、无一致性检查——恰是 REV-08 要的「错误站点拒绝登记」反向用例落点。

---

## 附录：数据抓取记录（全部只读）

| UTC 时间 | 命令（对 /Users/hello-tech-team/Documents/GitHub/auto-manual 执行） | 取得 |
| --- | --- | --- |
| 03:10:08 | `git rev-parse origin/main`; `git log -1 origin/main` | 基线 SHA 与提交 |
| 03:10:08 | `git ls-tree origin/main .github/workflows/`; `git ls-tree origin/main tools/`（rtd/web/publish 过滤） | workflow/工具清单 |
| 03:10-03:11 | `git show origin/main:<path>` × 14 文件 + 14 workflows → `snapshot/` | 逐行证据副本 |
| 03:11-03:12 | `git grep`（BUILD_ACTIONS、四个撤回动作、web-publish 对照） | §1.1/§1.2 |
| 03:12-03:14 | `git grep`（verify_deployment、write_*_html_link 调用者、月报/monthly/launchd、oss/handoff、发布文档管理） | §4/§5/§6 |
| 03:14-03:16 | `git show origin/docs/manual-revitalization-plan:...`（台账 + 方案，只读旁证） | M 定义与 REV 验收语 |
| 03:16-03:17 | `git grep`（redirect/legacy 缺口两面、cwa_report 参数、upsert_record 读码） | §6 缺口求证 |

未做：任何飞书读写（本任务全部证据在 git 层即可闭合，未动用 lark-cli）；未验证仓库外调度（§4 已标待操作者确认）。
