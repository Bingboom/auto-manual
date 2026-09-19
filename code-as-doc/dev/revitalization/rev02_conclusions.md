# REV-02 结论 — HTML_link / 印刷二维码 / 历史交付链接只读核查

- 调查窗口（UTC）：**2026-09-19T03:27:06Z – 2026-09-19T03:37:06Z**；逐条抓取时间见 `raw/http_probe_log.csv` 与本文台账（§6）。
- 全程只读：lark-cli 仅 `+field-list` / `+record-list`（bot 身份，profile `cli_aaa0db0d4b39dcca`，CLI 1.0.69）；仓库仅 `git show origin/main:<path>` / `git grep origin/main`；未 checkout 主仓、未写任何飞书表。
- 明细表：`rev02_link_audit.csv`（154 行 = 构建表 33 + 根别名 52 + legacy_route 兼容页 22 + 旧站入口 2 + 发布目录 45；其中 27 行带本轮实测 HTTP 状态，另有 6 条负对照/正式路由探测只入 `raw/http_probe_log.csv`，合计 33 次实测）。

## 1. 构建表 HTML_link（文档构建 base `LD3lb4G1ua4GOVs1vxAc9W2enje` / 表 `tblbnRHjpJeCVTtj`，33 行全量）

| 分类 | 行数 | 明细 |
| --- | --- | --- |
| 指向 ht-doc 域名 | **3** | `JE-1000F_US_2.3`（根别名平铺形态 `/manual_je1000f_us.html`）、`JE-1000F_EU_en_2.0`、`JE-1000F_EU_fr_2.0`（嵌套正式路由形态） |
| 指向旧域名 ht-manuals | **0** | 全表无任何 `ht-manuals` 值（`RTD_link` 字段亦 33 行全空） |
| 空 | **30** | 其余全部行（JP/KR/AU/CN/US 各历史构建行与 InReview 行） |
| 其它形态 | 0 | — |

写入时间口径：HTML_link **无字段级时间戳**（CLI record-list 不暴露记录修改时间）。可用代理：
- `JE-1000F_US_2.3`（rec`vsgDIt6HwEI`）：Web Publish 队列真实运行写入，`构建结果` built_at=**2026-08-14T11:05:39Z**，`开始构建时间`=2026-08-14T19:02:39+08:00，PR=Hello-Docs#51。
- `JE-1000F_EU_en_2.0` / `JE-1000F_EU_fr_2.0`（rec`vv9cTEvtUF4` / rec`vv9cTEvtX8l`）：**Git-only 事后回执**（Remarks 原文：*Git-only Web publication receipt; source content V2.0; Hello-Docs #72; no build dispatch*），无构建时间字段值；按 Hello-Docs #72 时段约 2026-09-13/14。

**形态不一致（真发现）**：自动写入器 `tools/write_web_publish_html_link.py::target_rtd_url` 确定性拼的是**根别名平铺 URL**（`{base}/{md stem}.html`，:69-75），而两条 Git-only 手工回执写的是**嵌套正式路由**。两种形态当前都 200，但 M2/M4 落地时应统一登记形态（建议统一为根别名=稳定入口层）。

## 2. 印刷二维码与根别名（repo 侧，origin/main = 58767931）

别名注册处不是独立注册文件，而是两层生成机制：

1. **根别名（52 个，全量）**：`tools/readthedocs_source.py::_write_short_aliases` 按每个发布目标的 manual 文件名 stem 自动派生 `docs/publish/web/<stem>.md` 平铺页；运行时 `tools/rtd_alias_entry.py::alias_targets`（数据源=门户 catalog，即 `index.md` 链接列表→publications）给根级页面加 noindex+canonical 并延迟跳转（beacon 可计数）。52 根别名 = 52 发布目标 stem，一一对应，无额外自定义别名（`docs/publish/web/*.md` 与 stems 差集双向为空，§6-D）。
2. **legacy 兼容别名（22 个目标）**：数据源 = Hello-Docs `docs/publish/sources/web/**/publish_meta.json` 的 `legacy_default:true` + `legacy_aliases` + `legacy_route` 字段（由 auto-manual `tools/publish_locale_identity.py::migrate_legacy_targets` 一次性设为 `[manual stem]`，此后 `stage_web_target` 逐轮继承）；`tools/publish_branch_assembly.py::_write_legacy_compatibility_routes` 据此写 `<MODEL>/<REGION>/md/` 兼容跳转页。当前 22 个 `legacy_aliases` 全部等于各自 manual stem，**无一个别名带额外自定义名字**。

**是否已印刷**：印刷登记面 = `data/printed_url_inventory.csv` + `data/printed_url_manual_entries.csv`（工具 `tools/printed_url_inventory.py`，I4）。核实结果（两个正交面）：

- 面1（印刷清单）：已登记的 3 个印刷 QR（JBP-2000B US p28、JE-3000C KR 封底、AI 母版 p59）**全部解码为文档物料号（16-0102-*），不是 URL**；清单中的 URL/email 全部是 jackery 域名与字体许可链接，**无任何 readthedocs 域名条目**。
- 面2（可印源全树 grep）：`git grep -l readthedocs origin/main -- docs/templates/ docs/renderers/ docs/manifests/ configs/ data/` **exit 1（零命中）**；阳性对照 `tools/write_web_publish_html_link.py` 命中，方法有效（03:30:21Z）。

→ 结论：**当前没有任何已登记印刷物指向任一 RTD 域名**。每个根别名在审计表中标「未登记印刷（推定未印刷）」；旧站 URL（ht-manuals 形态）是否曾在其它渠道对外分发标**未知**（仓库与两张飞书表均无登记）。

## 3. 历史交付链接（发布文档管理 base `WGVwb2HctauRi7sEiKqcIzTRn1c` / 表 `tbldqnNBxFQsxpeN`，45 行全量）

- **45/45 行 `说明书链接` 全部指向 `alidocs.dingtalk.com`**（钉钉文档），0 行空、0 行 readthedocs、0 行其它域名。
- 语义：行级版本交付（每行=型号×区域×文档类型×版本，`Is_latest` 44 TRUE / 1 False）→ 归类**历史版本绑定**。
- 抽样 5 条实测：HTTP 200，但最终落在 `login.dingtalk.com` 登录墙（链接活着、内容需登录，属预期的租户内交付形态）。

## 4. HT-Manuals 下线影响面（用数据证实）

**理论影响面极小——数据证实成立**：

1. 构建表 33 行：0 行引用 ht-manuals（§1）。
2. 别名/印刷层：0 个已登记印刷物指向任何 RTD 域名，自然也没有指向旧站的（§2）。
3. 发布目录 45 行：全部 alidocs，0 行 RTD（§3）。
4. 旧站内容面（rev01 已证）：旧站全量只有 JE-1000F US en 1.7 一本 + index；其旧路径形态在新站已有 200 兼容跳转页（`/JE-1000F/US/md/manual_je1000f_us.html` → JS redirect），本轮复测 200（03:31:55Z）。
5. 残余风险仅一类：**未经登记的外部流传链接**（如早期聊天/邮件里发出的 `ht-manuals.readthedocs.io/...`）。旧站两条 URL 本轮实测仍 200（冻结快照在线）。若直接下线项目，这类链接会 404；换域名重贴即可到达新站。此类流量量级只能靠旧站 CWA/RTD 流量数据判断——仓库内无此数据，**留待操作者在 RTD 后台看旧项目流量后再定下线 vs 301**（rev01 §7 同口径）。

→ 除「仓库外未登记流传链接」外，**三个受管登记面（构建表 / 印刷层 / 发布目录）对 HT-Manuals 下线的暴露面为 0**。

## 5. 未决 / 需操作者

1. 旧站 ht-manuals 下线动作（删项目 / RTD custom redirect / 保持冻结）需操作者决策；建议先看 RTD 后台旧项目流量。
2. HTML_link 登记形态统一（平铺别名 vs 嵌套正式）待 M2/M4 拍板。
3. 发布目录 alidocs 链接的登录墙后内容有效性（是否指向正确版本文件）本轮无法核验（需钉钉登录身份），标未验证。

## 6. 抓取台账（UTC）

| # | UTC | 操作 | 结果 |
| --- | --- | --- | --- |
| A | 03:27:15 | `base +field-list`（构建表 tblbnRHjpJeCVTtj） | 44 字段，含 HTML_link/RTD_link → `raw/build_table_fields.json` |
| B | 03:27:39 | `base +record-list` offset 0/200/400 | 33 行全量（200 上限未触顶）→ `raw/build_table_records_off*.json` |
| C | 03:28:06 | 解析构建表 | `raw/build_table_extract.csv`；HTML_link 分布 30空/3 ht-doc |
| D | 03:29:27 | Hello-Docs@b8c09fd（rev04 浅clone）枚举 `docs/publish/web/*.md` + 52 份 publish_meta.json | 52 根别名 = 52 stem；22 legacy_default；`raw/entry_map_tables.md` |
| E | 03:30:21 | 印刷清单 `git show origin/main:data/printed_url_*.csv` + 可印源 grep（负对照+阳性对照） | §2 结论 |
| F | 03:30:46 | `base +field-list` + `+record-list`（发布目录 tbldqnNBxFQsxpeN） | 45 行全量 → `raw/catalog_*.json` / `raw/catalog_extract.csv` |
| G | 03:31:49–03:32:05 + 03:34 | curl 实测 33 条（25 主样本 + 8 补充根别名） | `raw/http_probe_log.csv`；ht-doc 全 200，负对照 404，alidocs 200→登录墙 |
| H | 03:32–03:33 | `git show origin/main:tools/{rtd_alias_entry,rtd_portal,publish_branch_assembly,readthedocs_source,publish_locale_identity,write_web_publish_html_link,printed_url_inventory}.py` | 别名机制与 URL 拼写逻辑读码证据 |
