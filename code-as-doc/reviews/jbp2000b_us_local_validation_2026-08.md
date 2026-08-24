# JBP-2000B_US 本地生产线验证与修复计划

日期：2026-08-22
目标：`JBP-2000B_US`（HTP017 美加规，EN/FR/ES，Battery Pack）
源文档：`Jackery Battery Pack 2000 User Manual V2.0-2026-04-27.pdf`（28 页）

## 1. 发现结论

当前 `main@efa4822b` 已包含 `BP@INTL` 骨架、`config.bp-us.yaml`、BP 专用
产品概览/操作配方、三语页面、JBP 结构化 fixture 和四张已审核插图。

结构门禁已通过：

- `skeleton_resolve.py verify`：resolved manifest 与三层输入逐字节一致；
- 54 个 BP/contract/config/asset 定向测试：通过；
- `build.py check --config configs/config.bp-us.yaml --model JBP-2000B --region US
  --data-root tests/fixtures/phase2`：通过。

完整构建没有通过生产验收：

- PDF 为 31 页，机械预算和出货书均为 28 页；
- 三语各多 1 页，根因是复用了主机安全页（两页），而出货书的安全信息与符号共一页；
- `WHAT'S IN THE BOX` 误用主机图和 AC 充电线，正确内容应为 Battery Pack、Expansion Cable、Documents；
- 产品概览未消费已登记的 JBP 正面/左侧图；
- LCD 页误用主机 25 项显示屏图，JBP 只有 Power Percentage/Fault Code 与 Charging Indicator；
- connections/charging 模板尚未消费已登记的 JBP 专用插图；
- warranty 共享模板在当前装配中产生 21 个 `Unexpected section title` 警告；
- 线上 Start Review 运行使用了 `config.us.yaml / family=legacy`。JBP 队列行必须显式携带
  `Build_family=bp-us`，否则即使 BP 生产线本地正常，也会回到主机骨架。

## 2. 本轮边界

### 需要完成

1. BP 专用安全/前言/装箱/LCD/保修载体，不修改 MAIN 主机模板；
2. 接入已审核的四张 JBP 插图；
3. 从出货书单独提取 Battery Pack 装箱图、Expansion Cable 和 JBP LCD 屏幕图，先像素确认，
   再登记与接入；
4. 新增回归测试，禁止主机 AC/USB/接地文案和主机资产进入 BP；
5. 本地四渲染栈验收，PDF 必须为 28 页，并逐页抽查 PDF/HTML/Word。

### 本轮不做

- 不写飞书暂存表、正式源表、资产表或队列表；
- 不触发 Start Review/Draft/Publish；
- 不创建或覆盖 `docs/_review/**`；
- 不为 BP 建立 approved-reference IDML 版式计划；IDML 保持已记录的 fallback 降级；
- 不修改现有 MAIN 目标的共享内容或布局参数。

## 3. 可逆实施阶段

### A. 安全网

- 固定 BP resolved manifest 与 `Build_family=bp-us` 路由；
- 固定 BP 禁用主机资产/端口/接地文案；
- 固定 PDF 28 页和 Sphinx warning ratchet。

### B. 资产供应（独立于模板接入）

- 新资产 recipe 只覆盖出货书 PDF 第 5/6 页；
- crop-only，保留固定产品标识，不执行破坏性图元删除；
- package-only 生成 PDF/PNG 与 12x 对照图；
- 操作者确认后才更新 registry 和哈希。

### C. BP 载体接入

- `page_bp/{en,fr,es}` 新增/修订 BP 专用页面；
- blueprint 的 slot 顺序不变，仅调整 slot carrier；
- 所有产品事实继续由 BP recipe/CSV 数据提供。

## 4. 验证梯度

1. `python3 -m ruff check build.py integrations tools tests scripts`
2. BP 定向单测与资产测试
3. `python3 -m unittest`
4. `python3 tools/check_maintainability_guardrails.py`
5. `python3 tools/check_doc_link_integrity.py`
6. `python3 build.py check --config configs/config.bp-us.yaml --model JBP-2000B --region US --data-root tests/fixtures/phase2`
7. 隔离 worktree 中运行 `build.py all` 与 `renderer_acceptance.py --block-pages 8`
8. 渲染 PDF 页面，与出货书 28 页逐页抽查；确认 MAIN 目标没有变化。

## 5. 最终本地修复

### 资产边界

- `jbp2000b_in_box_main_unit` 使用操作者确认的左侧源图，保留整机上的
  `Jackery`、`POWER` 与 `Battery Pack 2000`；
- `jbp2000b_expansion_cable` 只去除线缆两端的 `Jackery`、`A`、`B`；
- `jbp2000b_lcd_screen` 保留数字、百分号与充电图标；
- 本轮只更新本地 recipe、registry 镜像、资产文件和消费模板，没有写飞书插图资产表。

### 语言分页

- `hb_latex_warranty.py` 的固定保修页识别扩展为
  `WARRANTY / GARANTIE / GARANTÍA`，三语均生成成对的
  `HBWarrantyPageStart / HBWarrantyPageEnd`；
- 西语安全页仅在 BP 专用 carrier 内采用与法语相同的局部符号表紧凑参数，
  不修改共享 MAIN 符号组件；
- 最终页序为：封面 1 页、前言 1 页、目录 1 页、EN 8 页、FR 8 页、
  ES 8 页、封底 1 页，共 28 页。

## 6. 最终验收结果

- `python3 -m ruff check build.py integrations tools tests scripts
  docs/renderers/latex/hb_latex_warranty.py`：通过；
- `python3 -m unittest`：3019 项通过，5 项跳过；
- `python3 tools/check_maintainability_guardrails.py`：通过；
- `python3 tools/check_doc_link_integrity.py`：132 个 Markdown、1580 个链接，
  0 个断链；
- `python3 build.py check --config configs/config.bp-us.yaml --model JBP-2000B
  --region US --data-root tests/fixtures/phase2`：通过；
- `python3 build.py all --config configs/config.bp-us.yaml --model JBP-2000B
  --region US --data-root tests/fixtures/phase2`：HTML、Word、PDF、Markdown
  全部生成；
- `python3 tools/renderer_acceptance.py --config configs/config.bp-us.yaml
  --model JBP-2000B --region US --block-pages 8 --json`：PDF 28/28 页、
  页面尺寸统一、LaTeX 日志干净、HTML/Word 存在；
- HTML 与 LaTeX 的 `sphinx-warnings.log` 均为 0 行；
- 28 页联系表逐页检查通过：p11/p19/p27 分别为 EN/FR/ES 保修，
  p20 从西语安全开始，p21 为 FCC + 装箱 + 产品概览，p22 从 LCD 开始，
  p28 为封底；未见语言串页、孤立标题、重叠或裁切。

## 7. 线上状态

本轮未写飞书暂存表、正式源表、插图资产表或构建队列，未触发
Start Review / Draft / Publish。只有在操作者再次明确确认“入库/上线上表”后，
才进入带逐条 read-back 的线上写入阶段。

## 8. IDML 发现报告与执行计划

### 发现

- JBP-2000B/US 当前没有已批准的 reference-layout plan；registry 只绑定
  JE-1000F/US。当前生产 IDML 会走由构建时 LaTeX PDF 测量得到的
  `latex-auto` page plan，不应把它描述为已获人工批准的像素级版式；
- 本机已安装 Adobe InDesign 2026，版本 `21.0.1.6` 与仓库 pin 完全匹配；
- 原说明书为 28 页，页面尺寸 `368.754 x 524.659 pt`；本地 LaTeX
  参考 PDF 为 28 页、同规格，可作为 IDML 首轮页数、尺寸和视觉对比基线；
- 支持入口为 `build.py idml --idml-mode both`，随后用
  `tools/indesign_finalize.py` 生成 INDD、InDesign PDF 和 native preflight；
- 可交付物必须是自包含 ZIP：生产 IDML、`Links/`、flow IDML/Markdown、
  source trace、reports、fonts manifest 与 reference PDF，不能只交裸 IDML。

### 执行计划

1. 在隔离 worktree 通过真实 `build.py idml` 入口生成 production + flow；
2. 对生成的 IDML 运行结构自检，再由本机 InDesign 转换为 INDD/PDF；
3. 要求 native preflight 的 overset、missing fonts、bad links 均为 0；
4. 对原 28 页 PDF、LaTeX 28 页参考 PDF和 InDesign PDF做页数、页面尺寸、
   页面占用率与逐页联系表对比；
5. 用 delivery packager 重写链接为 `file:Links/<name>` 并生成自包含 ZIP，
   再检查 ZIP 内 IDML、链接和报告完整性；
6. 若 fallback 结果不足以满足首轮视觉验收，记录明确差异和后续
   reference-layout scaffold 需求，不在本轮伪造“approved”状态。

### 非目标

- 本轮不注册或批准 JBP reference-layout contract；
- 不写飞书/线上表，不触发 Start Review、Draft 或 Publish；
- 不把构建产物加入 Git 提交范围。

## 9. 组件化插图接入后的第二轮分页修复

### 当前基线

- 复杂插图改为消费从冻结原稿裁切的 composite 资产后，真实
  `build.py all` 仍可成功，但 PDF 从此前 28 页漂移为 34 页；生产 IDML
  也成功生成，但为 34 个 spread，故二者都不满足交付条件；
- 34 页由封面、前言、目录、三种语言各 10 页和封底构成。原稿每种语言
  只有 8 页；三语均发生相同的两处分页漂移；
- 第一处是 LCD 插图按 `420px` 放大，导致 Operations 只有 H1 留在 LCD 页，
  操作图流到下一页。LaTeX page plan 虽把两个标题都锚定到同一物理页，
  视觉内容并未真正共页；
- 第二处是 locking composite 单占一页，而 7 行 Troubleshooting 被固定
  `102mm` 的 section guard 推到下一页。原稿应为 locking 图在上、
  Troubleshooting 标题和表格在下；
- 原稿与当前 EN 联系表已逐页对照：p4/p5 和 Warranty 结构一致；需要恢复
  原稿 p6 的 LCD + Operations、p8 的 locking + Troubleshooting，后续
  Charging 与 Storage + Specifications 会随连续流重新归位；
- prepared bundle 的 43 个 source page 现已全部获得显式语义角色，
  `unclassified_prose=0`。精确 stable alias 不会吞掉 `*_notes.rst` 等未知页。

### 可逆实施阶段

1. 先固定 stable-slot role 的正例与伪前缀反例，保证专用组件路由可达；
2. 只调整 LCD 资产载体尺寸并复用现有 `add_lcd_operations_page`，不改 H1、
   LCD 表或 Operations 图本身的视觉组件；
3. 为短 Troubleshooting 表新增按真实行数选择的紧凑 section guard，
   7 行表使用短预算，JE-1000F 的 11 行表继续使用现有 `102mm` 预算；
4. IDML 复用现有图像、H1 和 rounded troubleshooting table 组件，新增
   locking + Troubleshooting 同页的几何 compositor；
5. 依次重跑聚焦测试、`build.py all`、`build.py idml --idml-mode both`、
   两份 IDML 自检、InDesign native finalize 和 28 页逐页视觉对比；
6. 只有页数 28、overset/missing fonts/bad links 均为 0、PDF/X-4 通过且
   自包含 ZIP 重开无缺链时，才允许标记本地交付完成。

### 安全边界

- 不缩减正文内容，不删除固定产品文字，不重新执行过度无字化；
- 不注册伪造的 approved reference-layout；
- 不写线上表、不触发云端流程、不提交或推送；
- 不清理 `_build/`、`tmp/` 或其他窗口留下的未提交产物。

## 10. 2026-08-23 IDML 装配架构纠偏

### 决策

第 2、8、9 节中“本轮不建立 JBP reference-layout / 保持 fallback”的旧边界，
已被操作者在 2026-08-23 的明确决定替代：

- 不能复制 JE-1000F 的 58 页目标装配；
- 必须复用 JE 已有的语义组件、页面角色和 composition 类型；
- JBP-2000B/US 只新增目标装配数据，不新增按型号、文件名、相邻页面或标题
  判断的页面逻辑；
- JBP 的目标装配在完成本地 InDesign/PDF 视觉验收前保持 candidate，不写入
  approved reference-layout registry，也不伪造操作者的版面批准。

### 冻结基线

- 原稿：`Jackery Battery Pack 2000 User Manual V2.0-2026-04-27.pdf`；
  SHA-256 `c29a14daf6053a45920cd8d1523f6faf054425a2f04d01576e00ce8794270740`；
  28 页；`368.754 x 524.659 pt`；
- 已知最近的 28 页 native 基线：
  `output/indesign/JBP-2000B_US_local_validation_20260822_v14/`；PDF SHA-256
  `11d0d6cd599deffbbc88f065ed3d6e55e634490db39526fa120a30bd4bc2d216`；
  InDesign 2026 `21.0.1.6` 与 pin 匹配，missing fonts / bad links 为 0，
  PDF/X-4、`Japan Color 2001 Coated`、`JC200103` 均通过；
- 当前未完成工作树的 LaTeX PDF 与 production IDML 都为 34 页/spreads。
  28→34 是待修复的行为漂移；重构期间不覆盖上述 28 页 native 基线。

### 目标架构

1. `ComponentSpec`：保留 `tools/idml/components/REGISTRY` 和现有专用
   renderer，继续负责 callout、inbox、LCD、表格、图像等原生可编辑对象；
2. `CompositionSpec`：新增目标无关的共享 composition registry，按显式
   `composition_type` 装配一个或多个 `PageRole`，页面几何只存在于共享
   compositor 与 `layout_params.csv`；
3. `TargetAssemblyPlan`：JBP 只声明 43 个 source binding 到 28 个物理页的
   `composition_id / composition_type / start_page / page_count / flow_split`；
4. `ApprovedReferenceLayout`：JE 的 approved contract 与 JBP candidate 都投影
   到相同的 renderer-neutral `PagePlan`/composition dispatcher；只有通过人工
   视觉批准的 target contract 才进入 approved registry；
5. `export_idml.py` 只负责 IR、plan、dispatcher 和输出生命周期，不保留
   JBP fallback 的 `next_page`、`shares_latex_page` 或型号分支。

### 分阶段实施与文件边界

1. **模型和安全网**：新增共享 composition model/registry/loader 及定向测试；
   JE 现有 approved plan 必须继续解析为 58 页、52 bindings、40 compositions；
2. **兼容投影**：JE v2 contract 保持可读，不改 approved 目标、参考 PDF、内容
   或页面范围；旧 contract 通过 PageRole 组合投影到共享 composition 类型；
3. **导出收敛**：把 `export_idml.py` 中组合页的判断迁入共享 dispatcher，删除
   JBP 的 measured-LaTeX 页面特判；普通连续 flow 保持兼容 facade；
4. **JBP 数据**：新增 JBP-2000B/US candidate target assembly JSON，并由
   `config.bp-us.yaml` 显式选择；不注册为 approved reference-layout；
5. **验证**：Ruff → 定向单测 → 全量单测 → guardrails/doc links → JE 58 页构建
   → JBP 28 页 build/check/IDML → native finalize → 逐页视觉对比 → delivery ZIP。

### 非目标

- 不改变 `build.py idml` 的公开参数；
- 不把 JBP 页面几何写入模板文件名、标题字符串或 `if model == ...` 分支；
- 不修改 `data/phase2/**` schema、依赖版本、线上表或云端队列；
- 不清理或提交 `_build/`、`tmp/`、`output/` 产物；
- 不在本轮重排 JE-1000F 的 58 页 approved composition map。

## 11. 2026-08-23 candidate 视觉收敛阶段

### 发现

- candidate plan 已稳定生成 28 个 spread、43/43 source bindings，且
  `skipped_raw=0`；native preflight 的 overset、missing fonts、bad links
  均为 0，因此当前问题是视觉尺寸，不是内容缺失或 InDesign 包结构失败；
- 普通 RST 图片在 `prose_image` 中未命中既有语义后缀时固定回落为
  `120pt`。JBP 的 Operations、Connections、connection tail 与 Charging
  插图因此过小；继续扩充文件名 allowlist 会把目标知识重新散落进 renderer；
- LCD/Operations、Connections、Troubleshooting、Charging/Storage 的物理
  组合已由共享 `composition_type` 确定。插图尺寸应由这些 compositor 选择
  共享 semantic image role，并由 layout token 决定几何；candidate JSON
  继续只声明目标装配数据；

- 本地真实 `build.py idml` 可显式使用 `tests/fixtures/phase2`。该 snapshot
  已通过 JBP Spec_Master 校验且与当前 `manual.ir.json` 的 snapshot SHA
  一致，无需联网同步或写线上表。

### 本阶段计划与安全网

1. 为 prose image 增加目标无关的 semantic role（默认、宽图、整栏图、紧凑图），
   保留既有 JE 文件名兼容路径；
2. 只由共享 composition compositor 分配 role，不读取型号、图片文件名、标题或
   相邻页；新增/调整的几何全部来自 `layout_params.csv`；
3. 先跑 Ruff 与 image/shared-page 定向测试，再用 `tests/fixtures/phase2` 通过
   真实 `build.py idml --no-clean --skip-root-index` 重建；
4. 运行 native InDesign finalize，要求 28 页、0 overset、0 missing fonts、
   0 bad links，并重新渲染 28 页 PNG 与原稿逐页比较；
5. 最后运行全量测试、guardrails、doc links 和 JE-1000F approved 58 页回归；
   不通过 JE contract gate 时隔离新增 JBP token，不修改或重绑 approved contract；
6. 视觉批准前保持 `status=candidate`、`production_eligible=false`，不生成
   approved registry 条目，不写线上表，不清理生成物。

## 12. 2026-08-23 approved style identity 隔离

### 发现

- JE-1000F/US 的 approved v2 contract 对全局 `data/layout_params.csv` 的完整
  有效 token 序列做 hard gate；即使 JE 页面不消费新增 token，只要把 BP
  紧凑 composition token 追加到该文件，JE 的 style identity 也会失配；
- `build.py` 已能按 config 解析基础 layout CSV，但 IDML dispatch 未透传，
  `export_idml.py`、production Manual IR 和 flow writer/sidecar 仍各自读取全局
  默认文件，存在“几何使用一套 token、IR hash 记录另一套”的风险；
- 不允许更新 JE approved hash、弱化 style hard gate，或用视觉无变化代替
  contract 验证。

### 实施 contract

1. 恢复 `data/layout_params.csv` 与生成镜像 `params.tex` 到 JE approved 基线；
2. 新增可复用的紧凑 composition token overlay，由 `config.bp-us.yaml` 显式选择；
3. overlay 只能新增 key，禁止重定义基线 key；有效 hash 为 base + ordered overlay；
4. `build_dispatch` 同时透传 base 和 overlay，production/flow writer 与 Manual IR
   必须消费同一有效 token 集；
5. JBP contract 继续保持 `status=candidate`、`production_eligible=false`，且不
   修改 JE reference-layout registry、approved contract 或 `build.py` 公共参数；
6. 通过 JE 58 页 approved production build 和 JBP 28 页 native finalize 双向
   验证隔离成立，再生成新的 candidate delivery ZIP；旧 ZIP 不可复用。

## 13. 2026-08-23 v23 candidate 本地验收结果

### 组件与目标装配

- Overview 与 Operations 已停止消费三语整页 composite 截图。三语模板只保留
  H1/H2、表格/NOTE/On-Off/正文等活字语义，并分别引用四张经操作者确认的
  `front_controls / left_side_ports / power_control / lcd_control` 固定丝印资产；
- `lcd_operations` 共享 compositor 先执行既有 `oppanel.transform()`，POWER 图
  与 On/Off 行继续生成通用 `oppanel`，第二张 LCD 操作图才作为普通语义图片；
  此修复不读取型号、语言、标题或文件名；
- `HB-SPECIAL-OVERVIEW` instance contract 新增可选的每视图
  `heading_text_rect`。JE 未提供该字段，继续走原默认几何；JBP 仅在
  `jbp2000b-us-v1` 目标数据中声明横向双视图、callout 与 leader 几何；
- JBP target assembly 保持 `status=candidate`、
  `production_eligible=false`，没有进入 approved registry。

### 正式资产闭环

- 新增独立 corrective recipe
  `data/asset_recipes/manual_jbp2000b_us_fixed_markings.json`，没有改写两个原
  approved recipe；正式 package 与工作树中的 8 个 PDF/PNG 逐字节一致；
- 四张 PDF SHA-256 分别为 `26b6ac82fb421fc6...`、
  `9c4bd27261e9a568...`、`66a0306a88f6a0e...`、
  `e977dbc5bea5876e...`；对应 PNG 为 `c405e6a1fdd35bb5...`、
  `6ac9bc60991ebd6d...`、`c8332fadce5987fe...`、
  `4d5f74e927261d7c...`；
- 本轮只更新本地 recipe、资产文件和 `data/asset_registry.csv` 镜像；没有写
  飞书插图资产表或其他线上表。

### 构建、原生预检与视觉验收

- `build.py check` 通过；真实 `build.py idml --source runtime
  --idml-mode both` 生成 28 spreads、43/43 bindings、261 blocks，
  `skipped_raw=0`；IDML 中旧 `jbp2000b_product_overview_*` 与
  `jbp2000b_operations_*` 链接均为 0；
- InDesign 2026 `21.0.1.6`（pin match）finalize v23：28 页、0 overset、
  0 missing fonts、0 bad links；PDF/X-4、`Japan Color 2001 Coated`、
  `JC200103` 全部通过；
- 已并排检查原稿与 v23 的 p5/p6、p13/p14、p21/p22。Overview 已恢复为原稿的
  横向双视图，三语长标签完整且不再压住装箱卡片；Operation 图中不含章节标题、
  On/Off、NOTE 或正文，固定产品/UI 丝印与操作图形按确认保留；
- delivery ZIP 包含 41/41 链接、missing=0，root IDML 的绝对链接为 0。从 ZIP
  解压后再次 finalize 仍为 28 页、0 overset/字体/链接；两次 PDF 的 28 页
  72 dpi 渲染逐页完全一致。

### 回归结论与已知门禁

- Ruff、3067 项全量 unittest（5 skipped）、maintainability guardrails、
  132 个 Markdown / 1580 个链接完整性检查全部通过；JE approved contract pin、
  58 页 composition map 和 Overview 默认几何的 57 项定向回归通过；
- 用当前 runtime fixture 做 JE 同源 production build 时，approved gate 因冻结
  source identity 与当前内容快照已有漂移而拒绝激活（多页 digest 与 App 控件
  标签不一致）。该门禁没有被弱化或重绑；本轮的可选 heading 几何未改变 JE
  instance，但当前快照不能被描述为一次成功的 JE 58 页同源实构建；
- 最终本地产物位于 `docs/_build/JBP-2000B/US/idml/native-v23/`；handoff ZIP
  SHA-256 为 `3108cdd67abe99acda233d4028a399a8cbfe1571f04261c82fa4219dcafd2677`。

### 线上状态

未提交、未推送、未创建 PR、未写飞书/线上表、未触发 Start Review、Draft
或 Publish。candidate 视觉验收不等于批准生产；线上入库仍需操作者另行明确授权。

## 14. 2026-08-23 v28 Mac/自包含包修复

### 共享组件修复

- 普通 H2 的黑色圆点改为内联 InDesign 原生矢量圆与独立 gap，不再写入
  `●`，也不依赖 Segoe UI Symbol 或 Yu Gothic；Windows/macOS 共用同一组件；
- LCD 紧凑两列表复用 `comp_lcd_label_col_width`，并按三语实时文案计算行高；
- Troubleshooting 短表不再套用 JE 完整表的 ordinal 高度，错误码列按表头和
  全部代码动态测宽，右表头保持白底、首列使用灰底，紧凑圆角为 4.8pt；该圆角
  token 只属于 compact overlay，不进入 JE 冻结完整表的 strict identity；
- line-block 的 `|` 只作为源结构换行，F6-F9 / FA, FC 不再出现可见管道符；
  故障标题、引言和单元格关闭断词；
- connection tail 使用共享 `reference_measure` 图片角色；目标图宽、split 与
  `heading_space_after` 继续只写在 JBP candidate assembly JSON，不增加型号或
  页面标题判断。

### v28 本地与打包验收

- 使用冻结 `tests/fixtures/phase2` 经真实 `build.py idml --idml-mode both`
  重建：28 页、43/43 bindings、261 blocks、241 stories、`skipped_raw=0`；
- InDesign 2026 `21.0.1.6` finalize：0 overset、0 missing fonts、0 bad links，
  PDF/X-4、Japan Color 2001 Coated、JC200103 均通过；
- 印刷页 05 的 connection locking 图和 Troubleshooting 表头、灰底、圆角、
  行样式均存在；原始 Stories 中无 `Segoe UI Symbol`、`Yu Gothic`、文本 `●`、
  可见 `| FA`。InDesign 普通编辑视图中，圆点锚定对象会显示图层色框架边缘；
  这是非打印辅助线，预览模式和导出 PDF 中均为完整黑色圆点；
- delivery ZIP 收集 41 个链接、missing=0。由全新临时目录解包后再次 finalize
  仍为 28 页且 preflight 全绿；解包前后 28 页 72 dpi 全部逐像素一致，印刷页
  05/06 的 144 dpi PNG 也逐像素一致；
- 与 2026-04-27 源说明书逐页对照后，印刷页 05 的连接图、故障表结构和版面已
  高度对齐；印刷页 06 的圆点和 Mac 字符问题已关闭，但仍缺 `SOLD SEPARATELY`
  徽标，warning/intro 顺序、两张充电图图幅以及 STORAGE 分页仍与源稿不同。这些
  是 candidate composition/目标装配数据的后续差异，不得用 JBP 页面特判修补；
- v28 handoff ZIP SHA-256 为
  `e39cc115008e810a730debe969cdb3bef791e2d6d45611b512c212b2d61648d6`；
- `data/phase2` 当前 runtime 快照仍缺 JBP Product Name，本轮未修补该历史漂移、
  未写线上表；可复现本地验证继续显式使用仓库冻结 fixture。
