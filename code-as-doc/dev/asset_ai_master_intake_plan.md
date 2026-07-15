# AI 母版资产入库实施计划

Updated: 2026-07-15

## 1. 目标

把 PDF-compatible Illustrator 母版作为不可变源文件，确定性地产出页面归档、
预览、获批资产、清单和归档包，并把获批资产通过仓库快照纳入构建解析与发布血缘：

```text
AI 母版 -> 拆分/归档 -> 04_资产* Base 表 -> 资产快照 -> 构建解析
        -> HTML/Word/PDF/IDML -> 发布血缘
```

业务 Base 中只新建并使用 `04_资产源文件`、`04_资产定义`、`04_资产导出物`。
旧插图表 `tblxFBWaDG4OYhqu` 永久不作为读取、写入或失败回退目标。

## 2. 已复核事实

源文件：`16-0102-000404 说明书 HTE1531000A-US-JAK RoHS REACH.ai`

- 完整 SHA-256：`ee1fd9367021c99b3a16e14dc8aa702929c71ac4c98c7132816da05d90ce06ed`
- 字节数：`26,899,760`
- 格式：PDF 1.6 / PDF/X-4-compatible AI，Illustrator 30.6 (Windows)
- 页数：59；第 1 页是工程拼版总览，第 2–59 页是成品尺寸页
- 语言段：第 5–22 页英语、第 23–40 页法语、第 41–58 页西语
- 第 21/22、39/40、57/58 页含 App UI、QR 或机型相关截图，必须隔离
- 当前 recipe 定义 59 条页面目录和 10 个已核对的语义资产
- 10 个语义资产中 9 个获批，`page/back_cover` 因 QR/法务范围未核对而隔离

`data/asset_recipes/manual_je1000f_us_master.json` 使用严格 1 基页码。
所有页面初始 `build_eligible=false`；只有独立导出且通过 gate 的语义资产可以进入构建。
文字策略区分零文字、纯数字、固定产品丝印和本地化整页；POWER/AC/DC/USB 等设备
实物标记属于 `fixed-product-markings`，不得误报为 `textless`。

## 3. 非目标与安全边界

- 不保存、关闭或覆盖 Illustrator 当前文档。
- 不修改源 `.ai`，运行前后都校验完整 SHA-256。
- 不把 `.ai`、页面归档或 ZIP 大文件提交 Git。
- 不用 `qpdf`/`pdfseparate` 拆 AI；它们会复制 Illustrator 私有数据并造成异常膨胀。
- 不把 package 输出直接覆盖到 `docs/`；先在独立输出根生成并验证。
- 不自动放行 App/QR/截图页，不把工程拼版页变成构建页。
- 本阶段不引入 Illustrator/ExtendScript 桌面依赖。
- 不修改旧资产表，不在 Base 权限失败时切换到旧表或伪造附件指针。

## 4. 分阶段实施

### Phase A：确定性 intake

修改面：

- `data/asset_recipes/`
- `tools/asset_intake.py`
- `tools/asset_commands.py`
- `tools/build_cli.py`、`tools/build_dispatch.py`、`build.py`
- `tests/test_asset_intake.py` 及 CLI 回归测试
- 当前工作流文档

产物全部写到显式 `--asset-output-root`：

- 59 个清理后的单页 PDF
- 59 个页面预览 PNG（第 1 页低倍率）
- recipe 中的获批语义资产 PDF/PNG
- `manifest.json`
- `artifacts.csv`
- 固定时间戳、固定顺序的确定性 ZIP

安全网：先校验 source key、源 SHA、页数、页目录连续性、bbox、输出相对路径和
recipe schema；任何失败都不产生可发布结果。PDF 保存参数固定为
`garbage=4, clean=True, deflate=True, no_new_id=True`。运行时先创建私有源快照，
后续拆分只读这个已验证快照；外部源在 package 发布前再次校验。私有标记门同时扫描
物理字节、解码后的 PDF 对象和 stream，压缩不能隐藏禁用标记。

### Phase B：Base 归档与快照

在业务 `文档构建` Base（`LD3lb4G1ua4GOVs1vxAc9W2enje`）创建三张新表，
回读真实 table/field ID 后才写配置或文档。源 `.ai`、确定性 ZIP 和 manifest 作为
附件上传；回下载后逐字节校验 SHA，成功后才填写
`data/asset_sources.csv.source_pointer`。Base 暂时不可写时，Git 指针保持空值。

### Phase C：构建消费

模板或 bundle 使用稳定的 `asset:<asset_key>` 引用。构建先冻结本次使用的资产快照，
解析器只接受状态和哈希都通过的本地导出物，并输出 used-assets manifest。HTML、Word、
PDF 和 IDML 从同一解析结果消费，不允许各渲染器自行猜路径。

### Phase D：发布血缘

发布门只检查本次实际使用的资产；临时、缺失、隔离或哈希不匹配资产阻断发布。
release manifest 记录 asset key、格式、内容 SHA、源修订、快照和 intake run ID。

## 5. 验证梯子

按由便宜到昂贵执行：

```bash
python -m json.tool data/asset_recipes/asset-extraction-recipe-v1.schema.json
python -m json.tool data/asset_recipes/manual_je1000f_us_master.json
python -m ruff check build.py integrations tools tests scripts
python -m unittest tests.test_asset_intake
python -m unittest
python tools/check_maintainability_guardrails.py
python tools/check_doc_link_integrity.py
python build.py asset-check --json
python build.py check --config configs/config.us-en.yaml --model JE-1000F --region US
```

真实母版再执行两次 intake，逐字节比较两次的 manifest、CSV、ZIP、页面 PDF/PNG 和
语义资产；扫描输出不得残留 `AIPrivateData`、`PieceInfo` 或 `AIMetaData`；渲染页面与
语义资产做视觉抽检。只有本地验证和 PR CI 全绿后才合并该阶段。

## 6. 当前外部阻塞

2026-07-15 使用当前 user 身份创建 `04_资产源文件` 时，飞书返回资源级
`91403 you don't have permission`。创建未发生，旧表也未被访问。恢复条件是把当前
用户或已授权应用设为该 Base 的可编辑协作者；恢复后从“三表创建并回读”续跑。
