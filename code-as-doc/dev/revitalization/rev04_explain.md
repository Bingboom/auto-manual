# REV-04 — 型号×区域×语言 覆盖清单（同一时点）与 24 / 47 / 52 差异解释

- 调查窗口（UTC）：2026-09-19T03:10:04Z – 2026-09-19T03:17:02Z（全部数据抓取在此窗口内，逐条时间戳见 §5）
- 全程只读：无飞书写操作、无 git push、无仓库文件修改。
- 产出文件：`rev04_coverage.csv`（54 行 = 当前 52 目标 + 2 已撤 sideload），本文件，及原始证据（§5）。

## 1. 同一时点口径（canonical snapshot）

数据源 = Hello-Docs `main` tip **b8c09fd9a953f2dd386e912507c5e478fbdb2b6f**（commit 时间 2026-09-17T10:51:09Z，clone 于 2026-09-19T03:10:14Z–03:11:18Z），`docs/publish/publish_manifest.json`（manifest 内 `built_at` = 2026-09-17T07:23:17Z）。

- **发布目标（型号×区域×语言）= 52**
- **本数（型号×区域）= 22**：欧规 21 + 美规 1（JE-1000F US）
- 语言展开：多语本 = JBP-2000B EU（5：de/en/es/fr/it）、JE-1000F EU（5：de/en/es/fr/it）、JE-1000H EU（6：+uk）、JE-2000E EU（6）、JE-2000F EU（6）、JE-3000C EU（6）、JE-3600A EU（3：en/es/fr）；其余 15 本均为单语 en。
- 完整清单见 `rev04_coverage.csv`。

## 2. 24 / 47 / 52 三个数字的裁决

三个数字**互不矛盾**——它们是同一条产线在三个不同时点/口径上的读数：

| 数字 | 口径 | 时点 | 对账结果 |
| --- | --- | --- | --- |
| **47** | 型号×区域×语言（发布目标数） | 运营表快照 = manifest 在 HD#82（a38abd77，2026-09-16T03:51:13Z）的状态；表最后编辑 2026-09-16T06:47:50Z（revision 26） | **集合级精确相等**：运营表 47 行与 manifest@HD#82 的 47 targets 逐元素相同（diff 双向为空，§5 步骤 E） |
| **52** | 型号×区域×语言（发布目标数） | 当前 main（HD#89 之后） | 52 = 47 + 5（HD#85 于 2026-09-16T10:08:47Z 新增 JE-1000H EU de/es/fr/it/uk，晚于运营表编辑 3h21m）+ 2（HD#86–88 sideload）− 2（HD#89 撤下） |
| **24** | 本（型号×区域） | 撤下 sideload 之前的峰值 = HD#88（f83606cb，manifest built_at 2026-09-17T07:23:17Z，54 targets） | 24 本 = 欧规 21 + 美规 2（JE-1000F US、JHP-3600A US）+ 日规 1（JE-5000A JP）；HD#89（2026-09-17T10:43:12Z）撤下 JE-5000A_JP(ja) 与 JHP-3600A_US(en) 两本 sideload 后 → **22 本 / 52 targets（现状）** |

关键换算关系：

```
47 targets (运营表快照, 2026-09-16 06:47Z)
  + 5  JE-1000H EU de/es/fr/it/uk   (HD#85, 2026-09-16 10:08Z)
  + 2  JE-5000A_JP(ja), JHP-3600A_US(en) sideload (HD#86–#88)
  = 54 targets / 24 本               (HD#88 峰值, built_at 2026-09-17 07:23Z)
  − 2  两本 sideload 撤下            (HD#89 revert, 2026-09-17 10:43Z)
  = 52 targets / 22 本               (当前 main b8c09fd9)
```

任务说明中的猜测「52 可能与两本 sideload 书撤下同源」**证实**：撤下的正是 JE-5000A_JP(ja) 与 JHP-3600A_US(en)（pre/post manifest 差集，§5 步骤 C）。

### 与操作者「欧规21+美规3」子拆分的出入

24 的总数与 HD#88 峰值精确吻合，欧规 21 也精确吻合；但 manifest 里的 3 本非欧规书是 **美规 2 + 日规 1**（JE-1000F US、JHP-3600A US、JE-5000A JP），不是「美规 3」。可能是把日规 sideload 一并计入了「美规」，或口头子拆分不精确——总数与欧规数均对得上，仅子标签有 1 本出入。未能进一步核实操作者原话的时点，故不下「操作者错」的结论，仅记录出入。

### 运营表与 manifest 的差集（当前）

- 运营表 − manifest：**空**（运营表无一行超出 manifest）。
- manifest − 运营表：恰好 5 条 = JE-1000H EU de/es/fr/it/uk（HD#85 晚于表编辑）。
- 两本已撤 sideload 从未进入运营表（表内无 JE-5000A / JHP-3600A 行）。
- 结论：运营表不是独立口径，而是 manifest 在 2026-09-16 06:47Z 的忠实快照；**唯一需要的维护动作是把 HD#85 的 5 行补进去（47→52）**。运营表其余子表：每日访问明细 / 运营行动清单 / 口径与维护 / 采集记录。

## 3. 阻塞项现状

### JE-1000H EU —— **已解**（web 线六语全上线）

证据（均为 origin/main = 58767931，2026-09-17T10:50:34Z）：

1. **publish_manifest（现状）**：JE-1000H EU 共 6 个 targets（de/en/es/fr/it/uk），HD#85「add the EU fr/es/de/it/uk routes at 3x artwork」2026-09-16T10:08:47Z 合入（前一版 #83 因 12x 资产超发布树被 #84 revert，#85 以 3x 重上——与「发布树512MB闸门」记忆一致）。
2. **configs（auto-manual origin/main）**：六个欧规单语 config（config.eu-en/-fr/-es/-de/-it/-uk.yaml）全部声明 `model: JE-1000H, region: EU`，并各自带 `web_illustration_manifests: JE-1000H_EU: docs/renderers/web/je1000h_eu_{lang}_illustrations.json`。
3. 支撑提交已在 origin/main：#1162（译文入冻结源）、#1167（本地化成品图）、#1170（非英语路由真实本地化页）、#1172（web 面板 12x→3x）。
4. 备注：config.eu.yaml（整本多语线）未声明 JE-1000H——web 上线走的是单语线，整本 IDML 线是否需要它不属本项范围。
5. 唯一残余：运营表还没有它的 5 个非英语行（见 §2 差集）。

### JE-3000C KR —— **部分解**（声明链已补齐，但仍为 candidate、无 web 目标，构建可行性本轮未验证）

记忆口径（2026-09-04）：manifest 缺封面/封底声明、页面只存在于 _review、构建不出来。现状逐项（均 origin/main）：

| 项 | 现状 | 证据 |
| --- | --- | --- |
| family config 声明 | **已解**：config.kr.yaml `targets` 含 JE-3000C/KR（PR#954），并 wired `idml_assembly_plans` + `idml_layout_params_overlays_by_target` | `git show origin/main:configs/config.kr.yaml` |
| 封面/封底声明 | **部分**：IDML 装配计划 `je3000c_kr_v1_candidate.json` 已声明 front_cover（page/cover_je3000c-ko.rst，第1页）与 back_cover（qr_only）；**但共享页 manifest `docs/manifests/manual_kr.yaml`（75行）仍无任何 cover/封面/封底条目**（正交核实×2：全文逐行读 + `grep -inE 'cover|back|封面|封底'` exit 1） | 装配计划 §5 步骤 G；manual_kr.yaml §5 步骤 F |
| 页面只在 _review | **仍然**：cover_je3000c-ko.rst / 99_back_cover.rst 只在 `docs/_review/JE-3000C/KR/ko/page/`；docs/templates/page_eu-kr 无 cover 模板（`grep -iE 'cover|3000'` exit 1） | §5 步骤 H |
| 生产资格 | **仍阻塞**：装配计划 `status: candidate`、`production_eligible: false`（#964 建线、#966 收紧词表后未再动） | §5 步骤 G/H |
| web 发布 | **无**：publish_manifest 无任何 KR region target（正交核实×2：python 按 region 聚合 = ['EU','US']；JE-3000C 的 targets 全为 EU 六语）；运营表亦无 KR 行 | §5 步骤 D/E |
| 「默认参数构建不出来」 | **未能核实**——本轮铁规矩禁止构建；上述结构事实（cover 页不在共享模板/manifest、计划仍 candidate）与该口径相容，但没有跑 build 不能断言现在必失败 | — |

## 4. 需要操作者/后续 PR 处理的事项

1. 运营表补 5 行（JE-1000H EU de/es/fr/it/uk）——本轮只读，未写表。
2. 「美规3」子拆分与 manifest 的 1 本出入（日规 JE-5000A），如需精确口径请操作者确认原话时点。
3. JE-3000C KR 若要盘活：cover/back 页从 _review 升入共享模板/manifest（或维持 per-target 装配计划路线并将 candidate 转正），再验证构建。

## 5. 数据抓取台账（UTC / 命令 / 结果摘要）

| # | UTC | 命令 | 结果 |
| --- | --- | --- | --- |
| A | 03:10:14–03:11:18 | `git clone --filter=blob:none --depth 1 https://github.com/Bingboom/Hello-Docs` | main tip b8c09fd9…（2026-09-17T10:51:09Z） |
| B | 03:11:56–03:12:01 | `gh api repos/Bingboom/Hello-Docs/commits?path=docs/publish/publish_manifest.json` | 20 条历史；HD#89=de4f1ff3 撤 sideload |
| C | 03:12:37 | `gh api -H "Accept: application/vnd.github.raw" …?ref=f83606cb` → `manifest_pre_withdraw_f83606cb.json` | 54 targets / 24 本（EU21+US2+JP1）；撤下差集 = JE-5000A_JP(ja)、JHP-3600A_US(en) |
| D | 03:11:41（首读）+ 03:16:09（region 聚合复核） | python 解析 `Hello-Docs/docs/publish/publish_manifest.json` | 52 targets / 22 本（EU21+US1）；regions=['EU','US']，KR targets=[] |
| E | 03:13:09–03:13:59 | `lark-cli --profile cli_aaa0db0d4b39dcca wiki +node-get` / `sheets +workbook-info` / `sheets +csv-get --sheet-id 15c75c` | 说明书运营表（obj=K13JsXoUjhd75sth7eec1sKpnKd，sheet）revision 26、最后编辑 2026-09-16T06:47:50Z；「说明书目录」47 数据行 → `ops_sheet_catalog_raw.txt`；03:17:02 复核：47 行集合 == manifest@HD#82（a38abd77）双向 diff 为空 |
| F | 03:14:5x | `git show origin/main:configs/config.*.yaml`（JE-1000H grep）、`git show origin/main:configs/config.kr.yaml`、`git show origin/main:docs/manifests/manual_kr.yaml`（全文+grep） | 六单语 EU config 均声明 JE-1000H；KR config 声明 JE-3000C；manual_kr.yaml 无 cover/back（grep exit 1） |
| G | 03:16:09 | python 解析 `origin/main:docs/renderers/contracts/target_assembly/je3000c_kr_v1_candidate.json` | status=candidate、production_eligible=false；editable_components 含 back_cover；页序列声明 front_cover→page/cover_je3000c-ko.rst |
| H | 03:16:3x | `git ls-tree -r origin/main docs/_review/JE-3000C/KR`、`docs/templates/page_eu-kr` grep、`git log --follow`（装配计划） | cover/99_back_cover 仅在 _review；模板目录无 cover；计划历史=#964/#966 |

lark-cli 备注：`~/.openclaw/.env` 本身只有表坐标键（无 APP_ID/SECRET）；实际认证走 lark-cli 本地 profile `cli_aaa0db0d4b39dcca`（bot 身份），SKILL 里的 `--profile prod` 已不存在（可用 profile 由 CLI 报错提示获得）。租户 xcn57j1urbe6 可读，未遇权限墙。CLI 1.0.69。

原始证据文件（同目录）：
- `Hello-Docs/`（浅 clone，勿改）
- `manifest_pre_withdraw_f83606cb.json`（HD#88 版 manifest，54 targets）
- `manifest_at_hd82_a38abd77.json`（HD#82 版 manifest，47 targets）
- `ops_sheet_catalog_raw.txt`（运营表「说明书目录」lark-cli 原始 JSON 输出）
- `rev04_coverage.csv`（54 行：52 现役 + 2 已撤，含来源/版本/链接/备注）
