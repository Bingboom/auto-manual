# 骨架库产线拓展执行方案（Skeleton Library Expansion Plan）

Status: 执行方案草案 — 待操作者批准 · Owner: 夏冰 · 2026-08-21

这份是**骨架模板拓展的执行方案**：从今天「17 份 manifest 实为一个章节骨架、
语料 58 本只能生成 15 本」拓展到「二维骨架库五格全通、58 本全部可重构、
新线上线 = 加数据行」。机制设计在
[`../architecture/Product_Skeleton_Library_Design.md`](../architecture/Product_Skeleton_Library_Design.md)（英文，供评审），
证据在 [`../architecture/manual_ia_audit_2026-08.md`](../architecture/manual_ia_audit_2026-08.md)。
本文件只讲：**分几波、每波改什么、解锁多少本、怎么验收**。

## 0. 一条前提认知（操作者 2026-08-21 校正后写死在方案里）

**出货书 = 管线产物 + InDesign 手工层。**

语料与模板的差集因此分两类，处置完全不同：

| 差集类型 | 现状 | 方案处置 |
| --- | --- | --- |
| 管线缺口（骨架/模板/数据缺位，InDesign 也无从下手） | 例：日规 manifest 缺 safety 页、加电包无家族 | 本方案主体，按波修 |
| **手工层承担项**（模板零命中，但操作者在 InDesign 手放） | 例：巴西规 ANATEL 封底块 | **fragment 化**：把反复手放的块收进模板资产，InDesign 只做微调。收益 = 免每次手放、进版本控制、随姊妹线传播、仓库检查可见 |

后一类不是故障，是债——本方案把它排进 B8，不当急件。

## 1. 目标与验收

| 指标 | 现状 | 目标 |
| --- | --- | --- |
| 语料可重构 | 46/58 纯删除（79.3%）/ 55/58 ≤1 overlay | 58/58（含 3 本 outlier 的显式 legacy 登记） |
| 产线可生成 | 15/58（25.9%） | 结构层全通（数据入库另计，走既有 spec-intake） |
| SKU 覆盖 | 5/22 | 22/22 结构可承载 |
| 加电包品类 | 0% | 7/7 |
| 新区规上线 | 克隆姊妹 + 手改 manifest | **加数据行**（语言集 + region_profile + fragment 挂载行） |
| 新品类上线 | 从零手写 | **新家族格 = 1 份锚点 manifest + 词汇表实例** |

**终验收（两条，都是实证不是推演）**：
1. **HTE153 回归基准对账**：`JE-1000F_AU/KR/pt-BR` 三目标产线构建产物 vs 真实出货书逐页对齐
   （全库唯一语料↔产线双向可对账的 SKU）。
2. **Workstream W 欠的实测**：下一条真实新线以 instantiate-and-fill 方式上线，操作者日 ≤2。

## 2. 三波拓展

依赖主链：**B0 → 一切**；B3/B4/B5 → B6；T-K4（源表备份）→ B6/B8；B2 → B7 → B8。
与在途工作：T Tier-1 全程可并行（零共享文件）；Q（template-sync）须与 B3 同期或在前；
V 受益于 B0（页名稳定后 bump PR 才能按文件名分类）。

### Wave 0 · 护栏（1 个 PR，解锁 0 本，是后面一切的前提）

**B0 序数解耦**：`tools/config_pages.py` 五个 page dataclass 加显式 `ordinal`；
页名锁 + 契约 source_ref 门。
已实测的根因：`tools/gen_index_bundle_plan.py` 里 capability 过滤（117 行）跑在序数循环
（130 行）**之前**——能力位掉页会整段位移 `pNN_` 名，而唯一会拦的门只在 IDML 生产构建里跑，
正是版式 pin 漂移事故（PR#720）的盲区。**B0 之前不动任何 manifest。**
验证：`python -m unittest` + US/JP check + golden 守恒（全部字节不变，纯加字段）。

### Wave 1 · 现有格子修真 + 语言轴（4 个 PR，日规/中规两条最大队列落地）

| 期 | 改什么 | 解锁 |
| --- | --- | --- |
| **B1 语言块参数化** | 新增 `tools/manifest_lang_groups.py` 展开器（`{lang}` token + `ordinal_base`），`manual_eu.yaml` 429 行手抄 6 遍 → 1 个 group + 覆写；家族索引升 v2（二维格子注册表） | 0 本直接；页数方差 82% 的那根轴第一次有载体；改语言集从改 manifest 降为改 `data/model_languages.csv` 一行 |
| **B2 App 能力门** | `data/capability_page_rules.csv` 加一行 `App/联网`（列由规则表派生，零代码）；`model_capabilities.csv` 补列，未取证目标留空走 fail-open | 拦住 13 本印不存在的 App 章（能力门旧账同型复发的修法） |
| **B3 MAIN@JP 修真** | `manual_jp.yaml`：接零引用的 `safety_ja.rst`、新增 usage_precautions/disclaimer 两页、独立符号页降为安全章子节。**同时缺章又多章的唯一修法**（17 本日规实测 100% 三段式） | 日规 12 本结构齐活（数据侧另走入库）；注意 v2 日规**零合规载体**是实测常态，不要按 v1 的認証行自动补 |
| **B4 MAIN@CN 修真** | `manual_zh.yaml`：接 `safety_zh.rst`（前言+保修吸收进安全页）、新增合格证兼封底尾槽模板 | 中规 7 本（A3 已实测 0 overlay） |

### Wave 2 · 新格子与契约（2 个 PR，加电包品类清零）

| 期 | 改什么 | 解锁 |
| --- | --- | --- |
| **B5 BP 家族锚点** | **先修硬阻断**：`tools/target_defaults.py` 加显式 `build.family_default: true` 标记——否则新建 `config.bp-jp.yaml` 会与 `config.ja.yaml` 同分，模块级 `_DEFAULTS`（148 行）直接让整个 build.py CLI 起不来。然后：BP manifest（−ups/−app/−extra_battery/−UMI，+connections/+installation）、加电包 product_overview contract、`model_capabilities.csv` 加 category 维度 | **加电包 0 → 7 本**；A5 撤锚落地（HTP007→BP@JP@v1、HTE119→MAIN@JP@v1） |
| **B7 contract 分档** | `03_product_overview.yaml` 必需占位行按 `capability/category/region` 分档 + `requires_capability` 组开关；**回收 JE-300E fork**（1 contract + 5 份 RST） | 解除 9 本排队要付的 fork 债（HTE150 日规、HTE162、7 本加电包）——仓库里唯一机制性强迫模板分叉的地方 |

### Wave 3 · 数据权威化 + fragment 库（3 个 PR，新线边际成本降到数据行）

| 期 | 改什么 | 解锁 |
| --- | --- | --- |
| **B6 page_registry 权威化** | 加 `region_scope`/`category_scope`/`presentation_level` 三列 + 归一词表落库（30 id）。**必须在 B3/B4/B5 之后**——否则会把今天错误的日规/中规组成冻进数据表 | Workstream M 的 exit criteria 第一次真实成立；新区规=加数据行 |
| **B8 合规 fragment 库** | `snippets/compliance/` 建 fragment 载体：FCC 寄生块 / EU-DoC 封底 / **ANATEL 封底（首批，见 §0）** / 中规合格证 / JP-v1 認証行；挂载表 `(region, host_page, repeat_per_language)`，AU/KR 记显式空行+法务签字标记。**只建载体不改形态**——FCC 独立页 vs 寄生块的形态归操作者裁决。同期 Row_key/Variant_key 拆分（扩 22 SKU 前置） | 手工层承担项收编进管线；巴西规 ANATEL 免每次手放 |
| **B9 收尾** | `config.ph.yaml`（用 B5 的 family_default 标记）、`data/corpus_registry.csv` 落库、两处建档缺陷按操作者裁决填 `alias_of`、能力位逐列全 bundle 取证后补齐 | 菲律宾规 1 本；9 个反向差集目标显式登记 |

## 3. 新线上线的目标形态（拓展完成后）

- **新区规（同品类）**：语言集一行（`model_languages.csv`）+ region_profile 参数
  （TOC 开关/封底形态/联系方式/单位制）+ 合规 fragment 挂载行（法务签字）+ 规格入库。
  **零 manifest 手写、零模板克隆。**
- **新型号（同区规）**：能力矩阵一行 + 规格入库。既有机制，B2/B9 补全能力列后闭环。
- **新品类**：新家族格 = 1 份锚点 manifest + 品类词汇表实例（Row_key 集 + 能力词表 + contract 档）。
  加电包（B5）就是这条路径的首个实例，照它复制。
- **研发期建骨架**（需求文档 Phase C-P4）：结构先立、值标 ⚠️需确认、diff 制演进——
  依赖 `document_key` 增加"仅型号"粒度，是飞书 schema 变更，**单独走操作者审批**，不混进上面各期。

## 4. 操作者的门（每个都会拦住对应期）

1. **B6/B8 前**：T-K4 源表备份到位（`data/phase2/**` schema 变更的恢复路径）。
2. **B8 内**：合规裁决表逐区规签字（AU/KR 空载、HTE162 DoC、FCC 形态）——签字前 fragment 只建载体不出页。
3. **B9 内**：墨西哥规 alias 与 HTE152 日规错档的处置，查实时 Base 后裁决。
4. **每波合并**：照 §8.6 惯例 PR + 人审；golden 变更只允许显式重基线。

## 5. 不做什么

TOC 自动生成（presentation_level 落数据前生成必错）、页预算求解（版式引擎地界，Workstream X）、
DITA XML（D1 决策）、散文正文迁移（Workstream N 地界）、review 派生物重构（Workstream V 地界）。

## 6. 修订记录

- 2026-08-21：按操作者要求从设计文档抽出独立执行方案；写入「出货书 = 管线 + InDesign 手工层」
  前提认知并更正 ANATEL 措辞（管线债务，非印刷阻断）。
