# REV-10 · M5 统计口径快照 v1（第一期：模板 + 实例）

- 口径版本：**metrics-caliber v1**；本文件是「每期一份」序列的第一期，同时定义模板结构。
- 生成（UTC）：2026-09-19T03:36Z；生成方式：只读（git show / lark-cli 只读 / 公网 GET），未运行 CWA 查询（凭据在环境外，本轮不触碰）。
- M5 定义（方案原文，`code-as-doc/manual_production_revitalization_plan.md:172`）：「**每期保存窗口、来源、过滤和路径归类规则、采样情况及目录快照**」。

## 每期模板（结构约定）

每期快照必须填齐以下 8 栏；缺数据的栏写 `no_data` 并保留上一期（方案 WP3 失败语义：「采集失败标记 no_data，保留上一期」）。

| 栏 | 本期值（第 1 期） |
| --- | --- |
| 1. 统计窗口 | 首版参考窗口 = **2026-09-09 至 09-15 UTC**（方案记载的首版查询窗口；本期未重跑查询，无新窗口数据 → 本栏对新窗口为 `no_data`） |
| 2. 数据源 | **Cloudflare Web Analytics (CWA)**，经 `tools/cwa_report.py` 的 GraphQL 只读查询（`rumPageloadEventsAdaptiveGroups`，按 `requestPath` 分组，输出 pageviews + visits）。凭据：`CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` + site-tag（环境变量，非 beacon token）。采集端 = `tools/rtd_analytics.py` 无 cookie beacon 注入 |
| 3. 过滤规则 | **现状：未排除机器人及内部流量**。方案原文（plan:36）：「首版查询窗口为 2026-09-09 至 09-15 UTC；**未排除机器人及内部流量**」，风险栏注明「需与仪表盘口径统一，不能直接代表客户使用情况」。v1 口径如实沿用此现状，不假装已过滤；过滤规则升级时口径版本号必须递增 |
| 4. 路径归类规则 | `tools/cwa_report.py::classify()`（origin/main=58767931 读码）：`/` 或 `/index.html` → **门户首页**；`/search.html` 或 `/_*` → **站内功能页**；根级单段路径（无二级 `/`）→ **扫码/印刷入口（根别名）**；其余 → **站内手册页** |
| 5. 采样说明 | CWA adaptive groups 为 Cloudflare 自适应采样聚合（工具原样透传，不做本地再采样）；本期无新查询运行 → 无采样数据 |
| 6. 当期目录快照指针 | `../rev04/rev04_coverage.csv`（52 现役目标 + 2 已撤 sideload，54 行）＠ Hello-Docs `main` tip **b8c09fd9a953f2dd386e912507c5e478fbdb2b6f**（publish_manifest built_at 2026-09-17T07:23:17Z）；入口层快照 = `rev10_entry_map.md`（同 tip） |
| 7. 命名规则版本 | **v1**：路径身份 = `<MODEL>/<REGION>/<lang>/md/<manual_stem>.html`（嵌套正式）；根别名 = `/<manual_stem>.html`；manual_stem 命名 = `manual_<model小写去横线><区域/语言后缀>`（既有例外：JBP-2000B/JBP-3600A 的 en 用 `_eu` 不带 `_en`；JE-1000F US 用 `_us`）——命名例外随目标清单冻结在目录快照里，不在本表逐一维护 |
| 8. 落盘/存档位置 | **真缺口（REV-05 §6-M5 已证）**：`cwa_report.py` 仅 stdout（无输出路径参数），`reports/` 无统计存档目录约定。本期快照落在 REV 证据目录；正式「每期一份」的仓库归档路径待 M5 实施 PR 拍板 |

## 与仪表盘/运营表的关系

- 运营表（说明书运营表，wiki obj `K13JsXoUjhd75sth7eec1sKpnKd`）的「每日访问明细」子表是人工/半自动快照，与 CWA 查询口径尚未统一（方案 plan:36 风险栏原话）。本快照不覆盖旧统计（REV-10 验收语：「不覆盖旧统计」）。
- 别名入口计数依赖 `rtd_alias_entry.py` 的延迟跳转设计（beacon 有发送窗口）——根别名 pageview ≈ 印刷/QR/短链入口信号；嵌套路径 pageview ≈ 站内/搜索/门户流量。此语义是 classify() 归类的依据。

## 下一期触发条件（建议）

1. 首次真实 CWA 查询运行（月报首跑，方案记载 10-01，调度现状在仓库外未核实 —— REV-05 §4）→ 第 2 期填窗口/采样/数据。
2. 过滤规则任何变化（排除机器人/内部）→ 口径版本 v2 并在本节记录差异。
3. 目录快照 tip 变化（新目标上线/撤下）→ 更新第 6 栏指针；不回改旧期。
