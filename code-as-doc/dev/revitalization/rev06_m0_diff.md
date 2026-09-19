# REV-06 / M0 存量对账 — 已知历史差异清单（差异表）

- 任务：PR #1188 0-30 天批次 REV-06（M0 存量对账）。前置 REV-01/02/04/05 证据全部复用；本轮新抓取 2 项（构建表全量复读 + 撤下目标 URL 探测），均只读。
- 本轮新抓取窗口（UTC）：**2026-09-19T03:40:47Z – 2026-09-19T03:46:11Z**；前置证据窗口 2026-09-19T03:10Z–03:37Z（同日，视为同一时点面）。
- 全程只读：lark-cli 仅 `+record-list`（bot，profile `cli_aaa0db0d4b39dcca`，CLI 1.0.69）；仓库仅 `git show/ls-tree/log origin/main`；公网仅 HTTPS GET。未写任何飞书表、未动 RTD、未合并 PR、未在主 checkout 切分支。
- 本目录新证据：`raw/build_table_fresh_20260919.json`（构建表 33 行全量，rev=1173，03:44:51Z）、`raw/withdrawn_probe_log.csv`（4 条 404 探测，03:46:09-11Z）。

---

## 1. 五个面的集合规模与口径

### A 面 — 冻结发布记录

**A1（Hello-Docs main 的 publish_manifest）：52 targets / 22 本**（EU 21 本 + JE-1000F US 1 本）。时点 = Hello-Docs main tip `b8c09fd9`（commit 2026-09-17T10:51:09Z，manifest built_at 2026-09-17T07:23:17Z），抓取 2026-09-19T03:10-11Z。来源：`../rev04/rev04_explain.md` §1、`../rev04/rev04_coverage.csv`（54 行 = 52 现役 + 2 已撤）。

**A2（auto-manual reports/releases 版本树，origin/main 口径）：空集——设计如此。** 三个正交面（本轮 03:42:07Z，origin/main = `58767931`）：① `git ls-tree -r origin/main reports/releases` 零输出；② `git log origin/main -- reports/releases` 零提交；③ `.gitignore` 第 15 行 `/reports/releases/`，紧邻注释原文 *"Runtime release output is delivered through Feishu / GitHub Actions, not Git."* 即发布产物树是本地/CI 运行时产物，从不进 git（本地工作区可能有未跟踪产物，按任务口径不计）。origin/main 下唯一被跟踪的 reports 版本类目录是 `reports/version_tracking/`（36 个文件，全部是 JE-1000F US/JP 的 HEAD 差异报表，属遗留单型号报表，不构成发布台账）。**推论：git 层的冻结发布记录只有一处 = Hello-Docs publish_manifest。**

### B 面 — 线上部署

新站 ht-doc：门户 52 个手册链接**逐一 GET 全 200**（rev01，03:14-16Z，`../rev01/raw/new_site_status_sweep.csv`）。旧站 ht-manuals：仅 JE-1000F US en 1.7 一本 + index，冻结于 2026-08-02 构建（commit `e24ab7bc`），两条 URL 实测仍 200。来源：`../rev01/rev01_inventory.md`、`../rev01/rev01_url_map.csv`（53 行）。

### C 面 — 成品目录（两张，口径不同）

- **发布文档管理（历史交付/印刷面）**：45 行，每行=型号×区域×文档类型×版本，`说明书链接` 45/45 全部 alidocs.dingtalk.com（0 RTD、0 空）。抓取 03:30:46Z。来源：`../rev02_10/raw/catalog_extract.csv`。
- **运营表·说明书目录（web 快照面）**：47 数据行，revision 26，表最后编辑 2026-09-16T06:47:50Z。已证明为 manifest 在 HD#82 时点的忠实快照（双向 diff 为空）。来源：`../rev04/rev04_explain.md` §2、`../rev04/ops_sheet_catalog_raw.txt`。

### D 面 — 队列回执（文档构建表）

33 行全量（base `LD3lb4G1ua4GOVs1vxAc9W2enje` / 表 `tblbnRHjpJeCVTtj`）。本轮 03:44:51Z 复读与 rev02 03:27Z 首读完全一致（rev=1173 未变，record_scope=all_records，has_more=false）。构成：**Build Draft Package 25 行 + Web Publish 3 行 + Publish（印刷）1 行 + Start Review 2 行 + 无动作（Git-only 回执）2 行**。HTML_link 非空 3 行（全 ht-doc 域名）、RTD_link 33 行全空。来源：`../rev02_10/raw/build_table_extract.csv`、本目录 `raw/build_table_fresh_20260919.json`。

### E 面 — 印刷/别名面

52 个根别名（= 52 target stem 一一对应，无自定义别名）+ 22 个 legacy_route 兼容跳转页（= 22 个 legacy_default 目标，别名全部等于 manual stem）+ 已登记印刷 QR 3 个（**全部解码为物料号 16-0102-\*，非 URL**）；可印源全树 grep readthedocs 零命中（带阳性对照）。→ **没有任何已登记印刷物指向任一 RTD 域名。** 时点 03:29-34Z。来源：`../rev02_10/rev02_conclusions.md` §2、`../rev02_10/rev02_link_audit.csv`（154 行：33+52+22+2+45）。

---

## 2. 差异表

| 编号 | 涉及面 | 差异描述 | 成因解释 | 建议处理 | 责任人建议 |
| --- | --- | --- | --- | --- | --- |
| M0-01 | A↔C | 运营表 47 行，缺 manifest 52 中的 5 行 = **JE-1000H EU de/es/fr/it/uk** | HD#85（2026-09-16T10:08Z）新增 5 目标晚于运营表最后编辑（06:47Z）3h21m；且目录同步是人工快照、无写入器（REV-05 §5 缺口） | **补登记**（唯一需要的表写操作，操作者授权后 +5 行；rev04 §4 同口径） | 操作者（夏冰）授权，agent 代写+回读 |
| M0-02 | D | 构建表 30 行 HTML_link 为空，其中 **28 行按契约本就不写**：Build Draft Package 25 行（草稿包产物走飞书/CI 交付）+ Publish（印刷 lane）1 行（JE-1000F_US_1.2）+ Start Review 2 行（JE-3000C_KR、JE-2000E_KR，非构建行） | HTML_link 写入器只挂在 web-publish 队列 workflow（feishu-web-publish-queue.yml:270）；其余 lane 无此字段语义 | **记为已解释，不动** | — |
| M0-03 | D | 剩余 2 行空 HTML_link 之一：**JE-1000F_US_2.2**（Web Publish）无任何时间戳/构建结果，且 `是否触发文档构建` 仍 = **'Y'（待跑）**、`是否立即构建`=True | 被同日 2.3 行取代后从未消费、也从未标记作废；'Y' 行是队列 worker 的取行条件（本机复跑手法正是"已构建行翻Y重跑"），存在**被未来队列扫描误消费重跑 2.2 的活隐患** | **待操作者决策**：翻掉触发标志或补 Remarks 注记作废（写表需授权） | 操作者拍板，agent 代写+回读 |
| M0-04 | D↔A/B | 剩余之二：**JE-2000F_EU_2.0**（Web Publish）构建结果 = **FAILED**（2026-09-14；原文：*Git_ref main does not contain review content for JE-2000F/EU; queue builds must render the active target from the review branch*），Remarks 明写「暂缓…改走 Git-only 单语发布」；而 manifest 里 JE-2000F EU **6 语已全部在线**（en=2.0-20260913） | 队列 Web Publish 强制从 review 分支渲染，但六语成品图在 main、欧规内容在 7 月的 review 分支——路线冲突，实际发布走了 Git-only；失败行不写 HTML_link 是**正确行为**（部署失败不得登记为在线） | 失败行本身**记为已解释，不动**；其后继 Git-only 发布的登记缺口并入 M0-05 | — |
| M0-05 | A↔D | **49/52 web targets 无任何 HTML_link 登记**：19 本书/40 targets 在构建表零行（JA-* 6、JS-* 4、JBP-2000B EU、JBP-3600A、JE-1000H EU、JE-100C、JE-2000E EU、JE-3000C EU、JE-300D、JE-3600A、JE-500A）；JE-1000F EU 仅 en/fr 有 Git-only 回执行（Hello-Docs #72），**de/es/it 3 目标无**；JE-2000F EU 6 目标全无回执（只有 M0-04 的 FAILED 行）。33 vs 52 的覆盖差同源：构建表是**全区域队列台账**（JP/KR/AU/CN 印刷草稿线占 25 行），web 52 目标绝大多数走 Git-only 路线、按现行契约队列行只是可选的事后回执 | Web 上线是 Git-only 路线（队列行=事后回执，且回执纪律只在 HD#72 执行过一次共 2 行）；没有任何机制要求每个 web target 落一行 | **记为已解释历史差异**；按台账原则**不为对齐补造队列历史**。49 个未登记 target 名单进 REV-07/M1 持续核对基线；是否在 M2 自动登记上线时一次性补录存量（及登记到哪张表）由操作者决策 | M2 工作线；操作者定补录策略 |
| M0-06 | D | HTML_link **登记形态不一致**：US 2.3 = 平铺根别名（`/manual_je1000f_us.html`，自动写入器 `write_web_publish_html_link.py:69-75` 拼的形态）；EU en/fr 回执 = 嵌套正式路由（`/JE-1000F/EU/en/md/...`，手工写入）。两种当前都 200 | 自动器与手工回执各写各的，无形态契约 | **待 M2/M4 拍板统一**（rev02 建议统一为根别名=稳定入口层）；拍板前新回执沿用即将确定的形态 | 操作者拍板，M2 落契约 |
| M0-07 | C↔A/B | 发布文档管理 45 行与 web 52 targets **零交集**（45/45 alidocs，0 RTD；反向 52/52 无 alidocs） | 口径不同：该表登记**印刷/租户内交付**（含 JP/KR/CN/US/AU/菲/巴西等 web 未覆盖区域），web 面从未以它为台账 | **记为已解释，不动**；REV-07/M1 对账时两表按各自口径分开核对，不做跨面求等 | — |
| M0-08 | B | 旧站 ht-manuals 冻结快照（JE-1000F US en **1.7**，2026-08-02 构建）仍 200，与新站同书 **2.3** 并存双在线；旧站内容落后 publish 线约 300 提交 | 旧 RTD 项目无 webhook、无后续构建，冻结在建站导入那一次；未下线也未 301 | **待 REV-03 处置**（下线 vs custom redirect vs 保留，先看 RTD 后台旧项目流量）；三个受管登记面对下线的暴露面已证为 0（rev02 §4） | 操作者（RTD 后台） |
| M0-09 | A–E 全面 | **JE-5000A JP / JHP-3600A US 撤下后各面残留 = 零**：A 面 manifest 已随 HD#89 移除；B 面 4 条 URL（嵌套×2+平铺别名×2）本轮实测全 **404**（03:46:09-11Z，`raw/withdrawn_probe_log.csv`）；C 面运营表从未有其行，发布文档管理有 Doc-078/Doc-102 两行=其**印刷源交付**（alidocs，属印刷面正常记录，非残留）；D 面构建表 **0 行**（两次全表 dump：03:27Z 与 03:44Z，rev 均 =1173，record_scope=all_records，grep JE-5000A/JHP 零命中）；E 面 52 根别名/22 兼容页不含它们 | sideload 走的是传送带四 PR 栈（HD#86-88），撤回（HD#89 + auto-manual #1186）把 manifest/产物一并回滚；传送带 receipt 步骤未在构建表留行（是否曾写入后被删，只读 dump 无法回溯，现状=0） | **记为已解释，无需动作** | — |
| M0-10 | A | **冻结发布记录的 auto-manual 半边在 git 上是空集**：reports/releases 被 `.gitignore:15` 忽略（"Runtime release output is delivered through Feishu / GitHub Actions, not Git"），origin/main 零跟踪、零历史提交；被跟踪的 reports/version_tracking 只是 JE-1000F 单型号遗留报表 | 设计决策：运行时发布产物经飞书/Actions 交付，不入 git | **记为已解释（by-design）**；但 REV-07/M1 的对账基线应明确 **A 面唯一权威 = Hello-Docs publish_manifest**，不要再把 reports/releases 当第二本账 | M1 基线定义 |
| M0-11 | A↔C↔D | **版本词汇六种形态并存**（52 targets census）：semver 36、semver-dated（`2.0-20260913`）6、git-hash（`git-20260906-0252cb5d` 等）4、bare-date 4、`candidate` 1、`candidate-2025-10-24` 1。跨面版本对齐（catalog `V2.0` ↔ manifest `2.0-20260913` ↔ 构建表 `2.0`）无法机器化 | 各上线批次（正式版 / Git-only 批量 / 附件类小书 / 候选）各自起的版本名，无版本口径契约 | **记为已解释历史差异**；版本口径进 M2（登记）/M5（统计口径版本）拍板；M1 对账先按 (model,region,lang) 三元组对齐、版本仅作展示字段 | M2/M5 工作线 |
| M0-12 | D | 数据质量小项：JE-1000F_US_**2.3** 行的 `Document directory` 仍写 2.2 的产物路径（`.../versions/2.2/manual_je1000f_us_publish_2.2.docx`，与 2.2 行同值） | 建行时从 2.2 复制未更新；该字段在 web lane 无消费方 | **记录即可**（如顺手可与 M0-03 同批修正） | 可选，随 M0-03 一并 |

---

## 3. 结论

### 3.1 已解释历史差异（记录即可，不动）

**M0-02**（28 行按契约无 HTML_link）、**M0-04**（FAILED 行不登记=正确行为）、**M0-05**（49 target 无登记=Git-only 路线契约现状）、**M0-07**（两目录口径不同）、**M0-09**（撤下零残留）、**M0-10**（reports/releases 不入 git 是设计）、**M0-11**（版本词汇分叉）、**M0-12**（字段复制残值）。共 **8 条**。这些差异全部有闭合成因，台账验收目标「无未解释差异」在本清单内达成——**不需要也不应该**为抹平它们补造队列历史行。

### 3.2 待办写操作（需操作者授权，均为飞书表写）

1. **M0-01**：运营表补 5 行（JE-1000H EU de/es/fr/it/uk）——唯一的必要维护写。
2. **M0-03**：JE-1000F_US_2.2 行去武装（翻触发标志或注记作废）——消除误重跑隐患。
3. （可选）**M0-12** 顺手修正。

### 3.3 待操作者决策（不写不动，等拍板）

- **M0-06**：HTML_link 形态统一（平铺别名 vs 嵌套正式）→ M2/M4。
- **M0-08**：旧站 ht-manuals 处置（REV-03：下线/301/保留，先看流量）。
- **M0-05 附属**：M2 上线后是否一次性补录 49 个存量 target 的登记（以及登记面选构建表还是新表）。

### 3.4 进 REV-07 / M1 持续核对基线

- **A 面唯一权威 = Hello-Docs main 的 publish_manifest**（M0-10）；对账键 = (model, region, lang) 三元组（M0-11：版本仅展示）。
- 基线数字（2026-09-19 时点）：manifest **52** = 线上 200 **52**；运营表 **47**（差集=固定 5 行，M0-01 修完应为 0）；构建表 web 登记 **3/52**（M0-05 名单为已知未登记基线，新增 target 若既不进登记也不进名单才算新差异）；印刷面 RTD 暴露 **0**；旧站在线 **1 本**（1.7，直到 REV-03 处置）。
- 告警语义：M1 只对「新出现且不在本清单成因内」的差异告警；本表 12 条编号即首版白名单。

### 数据抓取台账（本轮新增）

| UTC | 操作 | 结果 |
| --- | --- | --- |
| 03:42:07 | `git ls-tree/log origin/main reports/releases` + `.gitignore` 三面核实（origin/main=58767931） | A2 空集，gitignore:15 |
| 03:42-43 | 解析 rev02 raw 构建表 JSON（positional-array 形）5 关键行全字段 | M0-03/04 的 Remarks/构建结果/触发标志原文 |
| 03:44:51 | `lark-cli base +record-list`（只读，全表）→ `raw/build_table_fresh_20260919.json` | 33 行，rev=1173，JE-5000A/JHP 零命中（绝对面 2/2） |
| 03:46:09-11 | curl 撤下目标 4 URL → `raw/withdrawn_probe_log.csv` | 4/4 = 404 |
