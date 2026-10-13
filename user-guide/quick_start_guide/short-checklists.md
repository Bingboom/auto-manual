# 快速开始：最短操作清单（§8）

属于[快速开始指南](../quick_start_guide.md)，其索引列出全部分页。章节编号与原文一致。
示例或流程变化时更新本页，不要把新内容追加到总文件。

## 8. 最短操作清单

### 如果你要第一次进入 Review

1. 在 `Review Init` 表新增一行
2. 勾 `是否进入Review`
3. 等系统回写 `Git_ref` 和 `PR_url`

### 如果你要继续出 Build Draft Package

1. 在 Feishu 改 phase2 数据
2. 在 PR 分支改 `_review`
3. 在 `Document_link` 里设：
   - `Workflow_action = Build Draft Package`
   - `是否触发文档构建 = Y`
   - `是否立即构建 = 勾选`
   - `是否强制刷新数据 = 只有这次确实要拉最新 phase2 时才勾`

### 如果你要正式 Publish

1. 确认当前 review / PR 分支内容已准备好
2. 确认 `Document_link.Git_ref` 仍指向这条 review / PR 分支
3. 在 `Document_link` 里设：
   - `Workflow_action = Publish`
   - `是否触发文档构建 = Y`
   - `是否立即构建 = 勾选`
   - `是否强制刷新数据 = 只有这次确实要拉最新 phase2 时才勾`
4. 等队列回写 `Document directory`（DOCX 留档路径）和 `idml_file`（设计交付 ZIP 的知识库链接）

### 如果你要正式 Web Publish

1. 确认当前 review / PR 分支和 `Git_ref` 已准备好
2. 在 `04_资产导出物` 上传完整图文插图，选择 `web_locale`，填写两个 SHA-256，并完成 `approved + build_eligible` 审核门
3. 在 `Document_link` 里设：
   - `Workflow_action = Web Publish`
   - `是否触发文档构建 = Y`
   - `是否立即构建 = 勾选`
4. 运行 `Feishu Web Publish Queue`；它会强制同步资产，所以不依赖 `是否强制刷新数据`
5. 验收生成的 `publish -> main` PR 只含 `docs/publish/**`，审核合入后再确认 `Hello-Docs/main:docs/publish/publish_manifest.json`、RTD 页面、`Web Publish Receipt` run 绿和它回写的 `HTML_link`（合入并核验部署之后才写）

### 如果你要按方案 2 复刻获批 PDF 为原生 InDesign

1. 冻结当前 review 和 phase2 snapshot，并确认参考文件确实是
   `Jackery Explorer 1000 User Manual V2.0-2026-06-05.pdf`：58 页、
   `368.787 × 524.692 pt`，SHA-256 为
   `e72b1ba01882062e261b17d5ba54a2f7c3099e5ba531a6428be13888641083f2`。
   本目标必须命中
   [`reference_layout_registry.json`](../../docs/renderers/contracts/reference_layout_registry.json)
   里的
   [`je1000f_us_v2_20260605.json`](../../docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json)；
   plan 缺失、hash 漂移或页数漂移都要停，不能退回 fuzzy 匹配。
2. 从冻结来源构建 production IDML：

   ```bash
   python3 build.py idml \
     --config configs/config.us.yaml \
     --model JE-1000F \
     --region US \
     --source review-asis \
     --idml-mode production \
     --data-root <phase2-snapshot>
   ```

   已在 reference-layout registry 注册的目标会直接使用批准的物理页合同，
   `--source auto` 也会自动选择与上面相同的冻结 `review-asis` 装配；显式
   source 参数不会被改写。入口只准备 RST，不再额外构建一份 LaTeX PDF；
   未注册目标才默认 runtime 并保留历史的 LaTeX 分页匹配回退。

3. 打开 `docs/_build/JE-1000F/US/idml/manual_je1000f_us.idml`。
   `manual.ir.json` 是内容身份，`latex_page_plan.json` 只是同源 LaTeX
   分页 trace，不是这次的视觉验收母版。文字、标题、表格、callout、
   Product Overview 和封底必须是原生对象；插图必须是获批、scope/hash
   正确的 linked asset。正文或封底不得靠整页 PDF 充当可见内容，参考
   PDF 只能放在非打印比较层。内容、法务、规格或资产身份有问题时回源
   修改后重建，不在 INDD 里另养一份内容。
4. 在装有 InDesign 的设计 Mac 上关闭旧 INDD，再运行：

   ```bash
   python3 -m tools.indesign_finalize \
     --idml docs/_build/JE-1000F/US/idml/manual_je1000f_us.idml \
     --indd output/indesign/JE-1000F_US_same_source.indd \
     --pdf output/pdf/JE-1000F_US_indesign.pdf \
     --report output/indesign/JE-1000F_US_preflight.json \
     --pdf-preset '[PDF/X-4:2008 (Japan)]' \
     --output-intent 'Japan Color 2001 Coated' \
     --output-condition JC200103 \
     --pdfx PDF/X-4
   ```

5. 用获批 PDF 做逐页硬门禁。这里 `--latex-pdf` 是历史参数名，传入的
   必须是获批参考 PDF，不是本次新生成的 LaTeX PDF：

   ```bash
   python3 -m tools.idml_pdf_parity \
     --latex-pdf <approved-reference.pdf> \
     --indesign-pdf output/pdf/JE-1000F_US_indesign.pdf \
     --preflight output/indesign/JE-1000F_US_preflight.json \
     --manual-ir docs/_build/JE-1000F/US/idml/manual.ir.json \
     --reference-layout-plan docs/renderers/contracts/reference_layout/je1000f_us_v2_20260605.json \
     --idml docs/_build/JE-1000F/US/idml/manual_je1000f_us.idml \
     --indd output/indesign/JE-1000F_US_same_source.indd \
     --pages all \
     --out output/comparison/JE-1000F_US_same_source_parity.json
   ```

6. 只有以下条件全部满足才交付：58 页及 geometry 通过、overset / missing
   fonts / missing glyphs / bad links 全为 0、PDF/X-4 与 `Japan Color 2001 Coated` /
   `JC200103` 正确、52/52 source identity 匹配、所有实际使用资产获批且
   hash 正确、没有可见正文/封底整页 PDF shortcut、58 页逐页 RGB MAD
   `≤ 0.008` 且 changed-pixel ratio `≤ 0.040`，最终 parity JSON 的
   `accepted=true`。写完文档、生成 IDML 或肉眼看起来接近，都不等于已经
   验收通过。

   `tools/indesign_finalize.py` 会在最终 PDF 上扫描可见 `U+FFFD` 与
   `.notdef` 字形，因此正文和置入 PDF 中保留的文本都会进入机器闸门；已
   转曲或纯位图素材仍必须依靠逐页视觉验收。

### 构建尚未晋升的 BP@INTL EU candidate

EU 六语加电包继续复用 `BP@INTL`，不需要复制一套页面 renderer：

```bash
python3 build.py idml \
  --config configs/config.bp-eu.yaml \
  --model JBP-2000B \
  --region EU \
  --data-root tests/fixtures/phase2
```

该目标的 `uk` 是乌克兰语，不代表 UK 市场；配套主机显示名必须是
`Jackery Explorer 2000 Plus`。命令应得到 54 个物理页、76/76 source binding
和 `skipped_raw=0`。随后仍须在设计 Mac 上运行 `tools/indesign_finalize.py`，
要求 overset / missing fonts / missing glyphs / bad links 全为 0，并检查
PDF/X-4。这里的 assembly 仍是 `candidate` / `production_eligible=false`；
构建成功不等于已经完成 approved reference-layout 晋升。

### 构建尚未晋升的 BP@JP JP candidate

日规加电包使用独立 `BP@JP` 骨架，但继续复用共享组件和 composition 类型：

```bash
python3 build.py check \
  --config configs/config.bp-jp.yaml \
  --model JBP-2000B \
  --region JP

python3 build.py idml \
  --config configs/config.bp-jp.yaml \
  --model JBP-2000B \
  --region JP \
  --no-clean
```

配套主机显示名必须是 `Jackery ポータブル電源 2000 Plus`。目标应输出
12 个物理页、13/13 source binding、`skipped_raw=0`；`Connections` 为两页，
Troubleshooting 与 Specifications 共页。随后在设计 Mac 上运行
`tools/indesign_finalize.py`，要求保存/重开后 overset、missing fonts、
missing glyphs、bad links 均为 0，PDF/X-4 通过，并逐页对照冻结参考 PDF。
该计划仍是 `candidate`，首次出包通过不等于 approved reference-layout
晋升。
