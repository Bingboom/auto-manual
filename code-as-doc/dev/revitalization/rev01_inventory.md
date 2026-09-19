# REV-01：HT-Manuals / HT-Doc 两个 RTD 项目同一时点快照

- 抓取窗口（UTC）：**2026-09-19T03:10:01Z ～ 2026-09-19T03:16:43Z**（约 7 分钟，视为同一时点）
- 全程只读：仅 RTD 公共 API v3（无登录）、公网 HTTPS GET、`gh api` 只读端点。原始响应存于 `raw/`；逐条抓取时间见 `raw/fetch_log.txt` 与 `raw/probe_log.csv`。
- 本轮未触碰：飞书表、RTD 后台、git 写操作、仓库工作区。

## 1. RTD 项目快照（来源：`https://readthedocs.org/api/v3/projects/<slug>/` 及 `.../builds/?limit=5`、`.../versions/`）

| 项目 | HT-Manuals（旧站） | HT-Doc（新站） |
| --- | --- | --- |
| slug / id | `ht-manuals` / 1188810 | `ht-doc` / 1187935 |
| API 抓取时间 | 2026-09-19T03:10:09Z（project）/ 03:10:23Z（builds+versions） | 2026-09-19T03:10:08Z（project）/ 03:10:21Z（builds+versions） |
| 项目创建 | 2026-08-02T12:13:15Z | 2026-07-17T16:01:11Z |
| 关联仓库 | https://github.com/Bingboom/Hello-Docs | https://github.com/Bingboom/Hello-Docs |
| default_branch | **publish** | **main** |
| default_version | latest | latest |
| 活跃版本 | 仅 `latest`（identifier=**publish**，type=branch，built=True） | `latest`（identifier=**main**）+ `publish`（identifier=publish）两个活跃版本 |
| 文档 URL 形态 | `https://ht-manuals.readthedocs.io/en/latest/`（多版本路径） | `https://ht-doc.readthedocs.io/`（单版本、根路径直出；`/en/latest/` 与 `/publish/`、`/en/publish/` 实测均 404，见 probe_log 03:16:41-43Z） |
| 构建总数 | **1** | **323** |
| 最近构建 | id **33875158**，version=latest，commit `e24ab7bc0352c3bea64b7c3d374ab4f0c328724b`，created 2026-08-02T12:13:15Z，success=True | id **34611273**，version=latest，commit `b8c09fd9a953f2dd386e912507c5e478fbdb2b6f`，created 2026-09-17T10:51:11Z，success=True。（其前一条 34611119 为 cancelled；34607301 是 publish 版本构建，commit `902adab8`，success）|
| 原始 JSON | `raw/rtd_project_ht-manuals.json`、`raw/rtd_builds_ht-manuals.json`、`raw/rtd_versions_ht-manuals.json` | `raw/rtd_project_ht-doc.json`、`raw/rtd_builds_ht-doc.json`、`raw/rtd_versions_ht-doc.json` |

对操作者 2026-09-17 截图的核实结论：
- 「HT-Manuals 关联 publish 分支、最后构建 33875158（2026-08-02）」——**核实成立**（default_branch=publish，latest→identifier publish，唯一构建 33875158）。
- 「HT-Doc 关联 main、构建 34611273（2026-09-17）」——**核实成立**（default_branch=main，latest→identifier main，最新成功构建即 34611273）。
- 旧站 slug 无需另找：`ht-manuals` 首试即 HTTP 200（03:10:09Z）。

## 2. 分支绑定的旁证（不进后台的三条独立证据）

1. **RTD API**（上表）：两项目 default_branch / 版本 identifier 直接给出绑定。
2. **GitHub webhook**（`gh api repos/Bingboom/Hello-Docs/hooks`，03:13Z，`raw/gh_hooks.json`）：仓库只有一个 RTD webhook —— id 660295351 → `https://app.readthedocs.org/api/v2/webhook/ht-doc/330788/`，active=true，events=[create,delete,pull_request,push]。**没有指向 ht-manuals 的 webhook**（断言依据①：hooks 列表全量只此一条；依据②：ht-manuals 构建总数=1 且其唯一构建 created 与项目 created 同秒 2026-08-02T12:13:15Z，即“建项目时的导入构建”，此后 publish 分支又有约 300 个提交却零构建——推不出 webhook 存在）。
3. **`.readthedocs.yaml`**（main tip `b8c09fd` 与 e24ab7bc 各一份，`raw/hd_readthedocs_yaml_main.yaml` / `raw/hd_readthedocs_yaml_e24ab7bc.yaml`）：两版都是「有 `docs/publish/web/conf.py` 就直接 sphinx 渲染冻结快照」；新版注释明确 *main carries reviewed, frozen Web source merged from the publish candidate branch*，且加了 `tools.rtd_portal` 扩展（门户页来源）。

**需操作者后台确认**（公共 API 看不到）：ht-doc 上活跃的 `publish` 版本在单版本模式下从哪个 URL 提供（实测常见路径 404）；两项目的 automation rules / PR-build 开关；ht-manuals 是否曾配置过 webhook 后被删。

## 3. Hello-Docs 两分支状态（`gh api`，03:12Z，`raw/gh_branch_*.json`、`raw/gh_compare_*.json`）

| 分支 | tip SHA | 提交时间 (UTC) | 首行 message |
| --- | --- | --- | --- |
| main | `b8c09fd9a953f2dd386e912507c5e478fbdb2b6f` | 2026-09-17T10:51:09Z | chore(mirror): sync auto-manual main |
| publish | `902adab805a1f50b924126206616478b861f820d` | 2026-09-17T07:33:56Z | chore(publish): refresh web documentation |

- `compare main...publish`：**diverged**，publish 比 main 多 5 个提交（ahead_by=5）、缺 main 上 4 个提交（behind_by=4）。
- `compare e24ab7bc...publish`（旧站唯一构建的 commit vs 当前 publish tip）：**diverged**，publish 领先 **300** 个提交，e24ab7bc 上另有 2 个不在 publish 线上的提交。即旧站内容落后当前 publish 线约 300 个提交（约 46 天）。
- main tip 与 ht-doc 最新构建 commit 一致（`b8c09fd`）；publish tip 与 ht-doc 的 publish 版本构建 commit 一致（`902adab8`）。

## 4. 站点在线抽样（HTTP 状态逐条见 `raw/probe_log.csv`，页面存 `raw/pages/`）

### 旧站 ht-manuals（03:11:51-54Z + 03:16:26-27Z）
| URL | 状态 | 说明 |
| --- | --- | --- |
| `/`（根） | 301→`/en/latest/` 200 | furo 主题 index，标题『Auto Manual Library』 |
| `/en/latest/JE-1000F/US/md/manual_je1000f_us.html` | 200 | 唯一手册页（315KB 级完整正文页的旧版） |
| `/en/latest/manual_je1000f_us.html`（平铺形态） | **404** | 旧站不存在平铺路径 |
| `/en/latest/genindex.html`、`searchindex.js`、`/sitemap.xml` | 200 | — |
| `/en/latest/JE-1000F/EU/en/md/...`、`/en/latest/JBP-2000B/EU/de/md/...`（新站才有的目标） | **404** | 负对照 |

**旧站全量清单 =「JE-1000F US en 一本 + index」**。两个正交核实：① index 页 href 全列表只有这一条手册链接（`raw/htmanuals_root.html`）；② `searchindex.js` docnames 全量 = `["JE-1000F/US/md/index","JE-1000F/US/md/manual_je1000f_us","index"]`（03:11:53Z）。

### 新站 ht-doc（03:11:55-03:12:01Z；全量扫 03:14-16Z）
- 根 `/` 200：自定义门户『Manual Center』（`tools.rtd_portal`），列 **52 个手册链接**（`raw/htdoc_root.html`、`raw/new_portal_links.txt`）。
- searchindex docnames 共 **201** 条（52 目标 × (index+manual) + 平铺别名 + 旧形态路径）。
- **52 个门户链接逐一 GET：全部 200**（`raw/new_site_status_sweep.csv`，03:14-16Z）。
- 抽样细看 6 页均 200：JE-1000F US en、JE-1000F EU en、JE-2000E EU uk、JBP-2000B EU de、JE-1000H EU it、JA-CA05B EU en。
- **旧路径兼容**：旧站形态 `JE-1000F/US/md/manual_je1000f_us.html` 在新站返回 200 的跳转页（13.5KB，`window.location.replace("../en/md/manual_je1000f_us.html")` + “Continue to the manual” 链接，`raw/pages/new_oldform_je1000f_us.html`）。即**旧 URL 换域名即可到达新站并被 JS 跳转到带语言段的新路径**。

## 5. 版本标识的取证口径

渲染页正文/页脚**不含**手册版本号（两站页面 grep `V[0-9]+.[0-9]+`、meta、footer 均无 1.7/2.3 字样；只有 `readthedocs-version-slug=latest`）。版本身份用构建 commit 上的 `docs/publish/publish_manifest.json` 取证：

- 旧站（commit `e24ab7bc`，`raw/hd_publish_manifest_e24ab7bc.json`，schema v1，built_at 2026-08-02T11:13:18Z）：**唯一 target = JE-1000F US en，version "1.7"**，route `JE-1000F/US/md`。
- 新站（commit `b8c09fd`，`raw/hd_publish_manifest_b8c09fd.json`，schema v2，built_at 2026-09-17T07:23:17Z）：**52 个 target**，其中 **JE-1000F US en version "2.3"**（built_at 2026-08-14T11:05:39Z，git_ref review/JE-1000F-US）。其余：EU 主力线多为 2.0 / 2.0-20260913，另有 git-hash / candidate / 日期形态版本号（JA-AD01A、JA-CA05B、JA-CA3SA、JA-CC30A、JAAC-WHE-100-EUA1、JE-300D、JE-3600A、JS-40C）。
- 服务页 ↔ manifest 的对应关系旁证：旧站在线页的资产文件名 token `BiBvbNteAoNsHqxoMICc11cjnHc` 在旧 manifest 命中 3 处；新站在线页 token `LOAZbnxfqoHFwIxx2Myc532jnzb` 在新 manifest 命中 57 处（同名资产多尺寸/多条目）。
- 在线页 SHA256（`raw/page_hashes.txt`）：旧 `5a9c98fc…a69dbe`，新 `0b2c3603…9549c`。

## 6. URL 对应表

见 `rev01_url_map.csv`（53 行 = 门户 1 行 + 52 个文档目标；重叠目标只有 JE-1000F-US-en 一条，旧版本 1.7 → 新版本 2.3；其余 51 个为新站独有，old_url 留空并注明依据）。

## 7. 未决/需操作者

1. RTD 后台设置（automation rules、ht-doc 单版本开关、publish 版本的对外可达性、是否给 ht-manuals 配 301/停用）——公共 API 无此字段，标**需操作者后台确认**。
2. ht-manuals 是否保留：它现在是 2026-08-02 的冻结快照（仅 JE-1000F US 1.7），无 webhook、无后续构建；对外若还有旧链接流量，迁移动作（RTD custom redirect / 项目下线）需操作者决策。
3. e24ab7bc 上那 2 个不在 publish 线上的提交（diverged 的另一侧）未逐个考证来源（推测为当时 publish 线被重写/重建，未核实）。
