# Scaling Execution Plan（Workstream W）— 模版+数据 → InDesign 的规模化改造

登记日期：2026-07-30 · 状态：**已批准**（2026-07-30 操作者拍板「按方案来 落PR 让codex开跑」；范围=全六阶段，gated 项按 §5 逐个放行）· PR 级登记：[`../next_optimization_checklist.md`](../next_optimization_checklist.md) Milestone L（本文件 §4 为权威 PR 清单）
依据：9-agent 全仓深读（main @ e3fc9e4e，136 万 token 读码量，file:line 级取证）+ 可执行性批判环修订
与既有路线图的关系：本计划**是** roadmap §5 的业务触发事件——扩产品线点燃了 K13 的显式触发器；Codex 连夜窗口即 Tier 3 要求的「专门窗口」。计划复用 K2/K8/K13/K14/E1/I2 原编号与 Done-when，不与 triage 体系冲突。

---

## 1. 现状：新增一条产线的边际成本账（实测）

| 成本类 | 今天 | 证据 |
| --- | --- | --- |
| 新 region（已有语言） | ~5 个 repo 文件克隆 + target_defaults/CI 两 workflow 登记（不登=零 CI 覆盖）+ 飞书 ~70-110 行 | KR 上线实证；manual-validation.yml:193-239 仅覆盖 JE-1000F US/JP 两目标，**17 个 config 里 15 个裸奔** |
| 新输出语言 | **≥15 处 Python 枚举** + ~10 份各自为政的别名表 + 2 个测试文件 + 3 张飞书表建列;漏一处=静默英文回退 | sync_data_models.py:84-320 六表列快照、manual_copy_source.py 五常量等;**漂移已实锤**:ko 缺席 4 处注册点,KR 线脚注今天就无法本地化 |
| IDML 语言（超出 en/fr/es） | ≥13 处 `{"en","fr","es"}` 字面量 + SYMBOL_COPY 词表代码 PR + layout_params ~127 token/语言;CJK 被 Gilroy 硬编码+0.52 拉丁估宽双杀挡死 | loaders.py:15-34; styles.py:183 |
| IDML 批准复刻档 | 手写 ~52 页契约 JSON+手算哈希+一场 parity 马拉松;此后**每次数据刷新逐线人工重绑一次** | JE-1000F US 横跨 #639-#724 数十 PR;rebind 单 --plan 接口 |
| 发布运行 | 全局串行并发组+每 run 4-8 分钟装 TeX;web 版只服务全局最新 target（后发布覆盖先发布）;批量派发第 3 行起静默丢单;finalize 逐份人工 osascript | feishu-build-queue.yml:25-27,119-133; build_publish_latest_site.py:59-64; queue_execute.py:455-470 |
| 验证 | 新线 fixture 手摘 6+ CSV+手改哈希;warning 基线烧死 target 路径（strict 翻不了）;capability 缺行=章节门**静默跳过** | check_docs_capability.py:76 fail-open |

**结论**：边际成本不在数据录入（已有 intake 工具），而在①散点代码注册②手工克隆产物③每线运行仪式。目标态：新语言=注册表一行+飞书建列（零 Python）；新 region=一条 new-line 命令+≤10 行差分；运行=批量命令+一次审批。

## 2. 度量（放进 H3 dashboard，逐夜可查）

- 新输出语言 Python 编辑数 = 0（fake-lang 'xx' 端到端测试机器证明 = K13 出口判据原文）
- CI check 覆盖率 = **PASS/(PASS+SKIP+FAIL)**（SKIP≠覆盖；SKIP 数做只降不升棘轮，new-line 强制串接 fixture-refresh）
- 共享 layout_params 一次修改 → 契约恢复 = 1 条 `--all-registered` 命令 + 1 次审批（此前 N 次人工仪式）
- 静默失效传感器读数全零或全登记：missing_columns / skipped_raw / CAPABILITY_ROW_MISSING / manifest-regen-diff / ratchet-new
- 手写产物残量棘轮只降不升：manifest 手写行（1621→差分）、手算哈希行（→0）、`is_<model>_` 特判函数（→0）、语言/能力字面量表
- 单线接入成本 ≤ 2 操作者日（roadmap Phase 4 阈值；超了=回头加做 Stage 2/3，不硬推）

## 3. Codex 执行规则（每夜每 PR 均适用）

1. 遵守 AGENTS.md 全部纪律：一 PR 一分支（worktree，起于 origin/main）、Conventional Commits、PR 模板全填、**不自合**（合并统一走 gate-on-green 登记表，操作者授权后由授权持有方执行）。
2. 验证阶梯（每 PR）：`ruff` → 目标单测 → `python -m unittest` 全量 → `check_maintainability_guardrails` → `check_doc_link_integrity`（动 docs 时）→ 两条基线 check 命令（fixtures 数据根）→ 涉及 golden 的跑 golden 套件。**done_when 全部是机器断言**；标注〔操作者验收〕的项不属于 Codex 的完成判据，列在 PR body 供操作者事后执行。
3. golden `--regenerate` 是显式例外：fixture diff 必须像代码一样进 PR 评审，PR body 说明逐字节差异来源。
4. 遇到〔GATE〕停：该 PR 之后的依赖链挂起，转做同 Stage 无依赖项；夜终报告列出等待中的 gate。
5. 遇到实际规模 ≈3× 预估、或任何 done_when 需要放宽比较才能过：停，报告，不得「洗绿」。
6. 禁区=本文档 §6 non-goals + AGENTS.md §8.4 保护面 + Deferred 1-5 + 一切 fail-closed 审批语义（数据化载体可以动，审批人/审批点不许动）。
7. 每夜收工报告：完成 PR 清单（含验证输出摘要）/ 阻塞与原因 / 次夜计划。

## 4. 阶段与 PR 清单

> 尺寸：S≈半夜内、M≈一夜内。建议节奏：夜1-2=Stage 0+1，夜3-4=Stage 2，夜5-6=Stage 3，夜7-8=Stage 4a；4b/5 里 gated 项按拍板逐步放行。每阶段结束仓库处于可发布状态。

### Stage 0 — 安全网与静默失效传感器（8 PR，全部零行为变化）
卸掉：大改造无回归锁的风险 + 静默英文回退/静默跳过无传感器的排查成本。
〔GATE〕capability 豁免清单是业务判断（diff 即清单，操作者 review 拍板）；fr golden `--regenerate` 的 fixture diff 需人审。

1. [S] `test(idml): drop orphan data_only fixtures + fr golden variant` — 删无引用的 data_only fixtures（32 文件，grep 证据入 body）；golden VARIANTS 增 composed_fr。Done：golden 套件绿；`git grep data_only tools tests` 为空；fr 变体双跑 byte 相等。
2. [S] `test(configs): auto-enumerate config shape coverage` — glob 全部 config，逐个 subTest 断言可加载/目标可解析。Done：subTest 数==config 文件数；坏 config 注入用例红。
3. [M] `feat(lang): language registry + core parity locks` — 新增 `tools/lang_registry.py`（code/列后缀候选含历史别名/各列名/TM 列/显示名/模板目录/分隔符）；parity 测试锁核心消费面（sync_data_models 六表、manual_copy_source 五常量、localized_copy、signal_words）。零行为。Done：unittest 全绿；parity 显式清单覆盖。
4. [S] `feat(lang): long-tail parity locks + drift ledger` — parity 扩展到 content_lint 四映射/idml loaders 后缀表/variable_resolver/check_docs/显示层；已知 ko/de/it/uk 漂移以 expectedFailure 机器化记录。Done：漂移清单=测试产物。
5. [S] `test(sync): four parallel table registries consistency lock` — TABLE_SCHEMAS ↔ PHASE2_REQUIRED_* ↔ REQUIRED_CSV_HEADERS ↔ phase2_source_tables.json 闭合锁，缝隙显式豁免注明成因。
6. [M] `feat(sync): missing_columns sensor` — sync-data 用已获取的 field-list 对 schema 求差，缺列写入 snapshot_manifest + WARNING（pt-BR 别名豁免）。Done：删 Text_ko 字段的 fake-source 用例。
7. [S] `feat(check): capability fail-open visible + known-missing ledger` — 缺能力行从静默跳过改 WARN 级 CAPABILITY_ROW_MISSING + 豁免表。
8. [S] `feat(idml): skipped_raw report field (no gate)` — 丢块计数进导出报告 sidecar；strict 门留 Stage 5（先取证后收紧）。

### Stage 1 — CI/门禁随产线自动扩展（7 PR）
卸掉：新产线默认零 CI 覆盖 + 共享文件变更后的 N 次人工发现成本。
〔GATE〕workflow 变更逐项批准（check-all job、review-preview 通配、artifacts 项在 Stage 4）；`export_idml --model` 改必填是公开 CLI 行为变更；strict 翻转时点仍归操作者（本阶段只做归一化前置）。

1. [M] `feat(ci): ci_check_targets driver + check-all job` — 从 configs 派生目标清单循环 check（fixtures 数据根，缺 key 明确 SKIP），聚合 PASS/SKIP/FAIL；与现有两 job 并存观察。Done：configs 增一 yaml 清单自动+1；覆盖率按 §2 修正定义输出；SKIP 棘轮文件落盘。
2. [M] `feat(ratchet): warning baselines target-prefix normalization` — sanitize_line 把 target 路径前缀换 `{target}` 令牌，重生成两份基线（diff 随 PR 评审）。strict(I2) 的硬前置。Done：US/JP 同模板 warning → known=1 new=0；基线无 JE-1000F 字面。
3. [M] `feat(fixtures): data_snapshot fixture-refresh by document_key` — 一条命令把某 key 的行从本地镜像合并进 fixtures 并重算 manifest 哈希。Done：幂等/隔离/哈希复算三断言。
4. [S] `chore(ci): review-preview paths glob` — 六个枚举改通配。Done：yaml 解析；〔操作者验收〕合并后测试 PR 验证触发。
5. [S] `refactor(ci): derive review-preview/nightly fallback targets from configs scan` — 消灭 :79-86 的写死 fallback（补批判环挂空承诺）。Done：parity 单测（派生==现值）。
6. [M] `feat(idml): rebind --all-registered + pins fix-command output` — 批量 dry-run 汇总表；--write 仍逐 plan 显式；pins check 失败附可复制修复命令。Done：双 fixture plan 用例。
7. [S] `fix(idml): export_idml --model required` — 删 :118 的 JE-1000F 默认值（AGENTS.md 违例）。失败方向安全。

### Stage 2 — 语言接入零代码化：K13 落地（13 PR）
卸掉：新语言 ≈15 文件散点编辑的最大边际尖峰；顺带消灭 ko/de/it/uk 实锤漂移与 content_lint 对 ja/ko/zh 的 QC 盲区。全程 golden/parity 锁行为。
〔GATE〕①正式认定 K13 触发器已击发（本计划即触发事件）②飞书内容表建列清单（Text_ko 等）批准后人工/lark-cli 执行——代码先行，missing_columns 传感器如实报告缺口③content_lint 扩 ja/ko/zh 仅报告不阻断，口径确认。

1. [M] `fix(lang): close ko/de/it/uk registration drift` — 修四处实锤缺口；**含四处联动同步**：fixtures 表头、snapshot_manifest 哈希、phase2_source_tables.json、REQUIRED_CSV_HEADERS（Stage 0 一致性锁会打红的正是这些）。Done：expectedFailure 转正；全量 unittest 绿。
2. [S] `refactor(lang): signal_words + localized_copy consume registry`
3. [M] `refactor(lang): manual_copy_source five constants from registry` — 派生列序 golden 锁逐项相等。
4. [M] `refactor(lang): sync_data_models TABLE_SCHEMAS language columns from registry` — Done：fixtures 各 CSV 表头 sha256 不变；sync dry-run manifest sha 不变。
5. [S] `refactor(sync): derive PHASE2_REQUIRED_*/REQUIRED_CSV_HEADERS from TABLE_SCHEMAS` — 平行清单消减（不止传感器化）。
6. [M] `refactor(lang): csv_pages/builder/variable_resolver alias consolidation` — page_jp/page_zh 目录特例入注册表字段。Done：RST bundle 逐字节 diff 为空。
7. [S] `refactor(lang): content_lint maps from registry`（ja/ko/zh 进 QC 报告面）
8. [M] `refactor(lang): display/query layer consolidation`（含 HTML 切换器补全语言标签）
9. [M] `refactor(idml): SYMBOL_COPY/page_toc language packs + governed_languages() single point` — ≥13 处 `{"en","fr","es"}` 字面量归一；loaders.py 拉链回落。Done：en+fr golden 零字节差。
10. [S] `feat(latex): HBApplyLang notice labels for all registered langs` — components_safety.tex:320-335 仅 fr/es 的硬编码宏标签数据化（批判环漏配项：拉丁新线印刷件会静默出英文告示标签）。Done：现有语言输出逐字节不变；新语言标签用例。
11. [S] `feat(guardrail): language-literal grep ratchet`
12. [S] `refactor(capability): CAPABILITY_FIELDS from rules CSV`（能力新增从三处降两处零代码）
13. [S] `test(lang): fake-language 'xx' end-to-end zero-Python proof` — **K13 出口判据机器证明**；setup-map「代码注册」段同 PR 改写。

### Stage 3 — 克隆产物生成化：新 region 一条命令（13 PR）
卸掉：手工克隆 config/manifest/模板/资产行/登记点的克隆边际成本。
〔GATE〕①new_line_seed 的 --write 触碰 phase2 源表（F6 面）：dry-run 计划批准后另 PR 放行②promotion 契约载体（Python 常量→JSON）变更确认③target_defaults 元组序无消费方依赖确认。

1. [S] `feat(manifest): manifest-lint drift sentinel (report only)`
2. [M] `feat(manifest): family-manifest diff format + 2-line pilot roundtrip` — 差分格式设计 + 2 条试点线 byte-identical 往返（批判环拆分：原单 PR 过大）。
3. [M] `feat(manifest): fold remaining 15 manifests` — 全部 17 份 byte-identical golden。
4. [S] `chore(ci): manifest regenerate-and-diff guardrail`（手改生成物即红）
5. [M] `feat(scaffold): build.py new-line dry-run` — 对 KR/AU 两线重放校准，白名单外 diff 为空。
6. [M] `feat(scaffold): new-line --write + auto check` — 强制串接 fixture-refresh（关联覆盖率棘轮）。
7. [M] `feat(assets): asset_registry refresh + scaffold-override` — 哈希机器重算（终结手算 sha256）；v2- 垫片与 EXPORT_PREFIXES 收口备注入 body。
8. [M] `refactor(assets): datafy reviewed-promotion contract (dual-read)` — fail-closed 语义不变，载体到 JSON。
9. [S] `refactor(spec): _KNOWN_VALUE_REPAIRS to tracked CSV`（数据补丁出代码，防绕 F6）
10. [M] `feat(doctor): new-line data-plane preflight` — 一条命令代替「靠 build 失败反推缺行」。
11. [M] `feat(intake): new_line_seed dry-run plan` — doc-key 行/占位克隆/field-create 助手三件事的零写计划。
12. [S] `refactor(targets): target_defaults from configs scan + parity lock`
13. [S] `test(backport): source_record_index registries lock + abstain sensor` — 回写闭环 6 张代码内字典的一致性锁（批判环漏配项）。

### Stage 4a — 运行吞吐（无并发语义变化,18 PR）
卸掉：每 run 4-8 分钟 TeX、web 版互踩、批量丢单、逐线契约仪式、finalize 逐份触发、型号特判复制；补冻结快照（E1）与 Feishu 传输单点（K8 全四件）。
〔GATE〕①TeX/nightly 的 workflow 变更逐项批准②finalize JSX 需操作者设计机 2-doc 实测③E1 归档位置/保留策略确认④HTML_link 是生产别名还是唯一部署 URL 先实测确认（定 web 多 target 化紧迫度）。

1. [S] `feat(ci): TeX apt package cache` — Done（机器）：yaml 解析+缓存逻辑单测；〔操作者验收〕冷暖时长对比与 pdf sha 对拍（XeLaTeX 时间戳未固定前不承诺字节等价——批判环修正,K2 原文是目标态）。
2. [M] `feat(site): multi-target latest site + per-target HTML link writeback` — dist/<model>/<region>/<lang>/ 子路径+根索引；旧行为兼容开关。
3. [S] `fix(queue): batch dispatch dedupe` — >1 行时改派发一次批量 run（消除 pending 槽静默丢单；比现状**更**串行，安全）。
4. [S] `feat(queue): asset lineage pre-check at dispatch`（15-30 分钟构建后才被门拦 → 派发时预警;正式门不动）
5. [S] `feat(queue): run-level phase2 sync memo`（批量 run 内同 config 只同步一次）
6. [M] `refactor(feishu): K8 slice-1 converge queue runners into feishu_record_transport`
7. [S] `refactor(feishu): K8 slice-2 converge listen/spec_master_rebuild/bitable_schema`
8. [S] `feat(feishu): K8 slice-3 429 retry/backoff + pagination single point`
9. [S] `feat(sync): phase2 snapshot write file-lock` — K8 原 Done-when 第 4 件（批判环补漏：并发 sync 竞态 10x 下无覆盖）。
10. [M] `feat(idml): reference_layout_scaffold contract draft generator` — 52 页手抄哈希 → 只审 composition/approval；不接激活路径，fail-closed 兜底。
11. [M] `feat(finalize): --jobs manifest Python side` — 清单校验/逐 job 报告聚合/单 job 失败隔离；**jobs 清单强制显式 preset 字段**（修 [PDF/X-4 Japan]/Japan Color 默认 ICC 坑——批判环漏配项）；附 `indesign_package.complete=FALSE` 扫描自动组批盘点。
12. [S] `feat(finalize): JSX batch loop` — 外层循环+try/catch 隔离；〔操作者验收〕设计机 2-doc 实测。
13. [M] `refactor(idml): contract-driven app page ownership` — 退役 `is_je1000f_us_*` 模式;guardrail 正则防再生。
14. [M] `refactor(idml): explicit page-role table + assembly coverage WARNING`
15. [S] `feat(release): layout signals in release manifest`（overset 数/页数入 manifest——发布链版式信号从零到有）
16. [M] `feat(release): E1-PR1 freeze publish snapshot + manifest binding`
17. [M] `feat(release): E1-PR2 rebuild equivalence end-to-end`
18. [M] `feat(ci): nightly-render workflow` — doctor 循环+试点 IDML smoke（#720 类事故发现延迟上界→1 天）；〔操作者验收〕手触一轮。

### Stage 4b — 并发子阶段（操作者拍板后执行,3 PR）
批判环最高级修正：**并发组分键必须晚于最小原子认领**，否则 record-run 与 batch-run 可双跑同一行（RUNNING 是软认领）。
〔GATE〕队列语义变更整体拍板；合并前两条测试行实测（pending 槽/限流/Vercel）。

1. [M] `feat(queue): K12-min atomic claim token`（queue_transitions 层,claim+TTL,fixture 双派发用例;全量 K12 仍留 Tier3）
2. [S] `feat(queue): per-record concurrency group + Vercel mutex`（deps: K12-min + multi-target site）
3. [S] `chore(ci): artifacts retention + selective upload`（manifests/<ts> 无界增长与全量上传——额度卡死有前科）

### Stage 5 — 行为收口与扩张前置门（14 PR;唯一集中出现行为变化的阶段,每项独立开关、先取证后收紧）
〔GATE〕①strict 翻转清单逐项拍板（ratchet/skipped_raw/未知语言/capability 族级注解——先全 bundle 取证,TOU 三反转教训）②占位化的生产源表 seed 走 F6（模板+fixtures 先行,机器可验;生产 seed=操作者步骤）③copy-key 迁移的 Localized_Copy 覆盖取证④JP/KR/CN 是否走 IDML 生产线（决定 CJK 三件套执行与否）⑤K15 设计批准=Workstream O(many-target 扩张)解锁条件。

1. [S] `feat(idml): skipped_raw strict gate`（approved-reference 线超基线即败）
2. [S] `feat(idml): unknown-language fail-closed in strict`
3. [M] `feat(manifest): family-level capability annotations` — JP/KR/EU 吃到装配期选页;全 bundle 取证入 body。
4. [M] `feat(templates): PV input range placeholder-ize (a:模板+fixtures)` — '16V-60V' 烧死在 8 语言拷贝里,安全电气参数;机器验收=fixtures 数据根构建逐字节不变;〔操作者步骤〕生产表 seed(F6)后 diff-report 取证。
5. [M] `feat(templates): DC8020/UPS-10ms placeholder-ize (a)` — 同模式。
6. [M] `refactor(copy): copy-key pilot 03_product_overview family`（us-es/fr/pt-br;eu 系 raw-LaTeX 页不动）
7. [M] `feat(review): structured propagation ledger --json` — 只读台账:每在途分支×每受影响文件,标 merge_params-safe/需人工;**不做自动应用**（`--from-ledger` 半自动消费移出本计划,列为 K15 设计交付后的操作者单独拍板项——批判环:预设计锁定风险）。
8. [S] `feat(idml): font family token`（styles.py:183 + style_resources + **delivery._FONT_ROWS 一并收编**;默认=现值零变化）
9. [S] `test(idml): ja/ko golden variants`（CJK 三件套的字节级前置安全网——批判环补漏）
10. [M] `feat(idml): CJK fallback runs`（token idml_font_family_cjk;gated on ④）
11. [M] `feat(idml): east_asian_width line estimates`（0.52 拉丁估宽改字符宽度类别;gated）
12. [S] `test(idml): JP smoke export + check_idml record`（gated）
13. [M] `feat(release): K14 release tag + rollback runbook`（deps: E1;演练计时归操作者）
14. [M] `docs(arch): K15/V review-propagation design doc` — 纯文档,覆盖 checklist L1459-1462 五项;**批准即解锁 many-target 扩张**。

## 5. 操作者拍板点汇总（按时间序）

1. **本计划整体批准**（范围可砍：例如只跑 Stage 0-2）
2. Stage 1/4 的 `.github/workflows` 变更逐项（check-all、review-preview 通配、TeX 缓存、nightly、artifacts 保留）
3. `export_idml --model` 必填（公开 CLI 行为）
4. Stage 2 飞书建列清单（Text_ko 等,schema 面）
5. Stage 3 promotion 契约载体变更;new_line_seed `--write`（F6）
6. Stage 4b 队列并发语义（K12-min+分键,两测试行实测）
7. Stage 5 strict 翻转逐项;生产表占位 seed(F6);**CJK/IDML 产线决策**;K15 设计批准
8. 呈报项（附证据,只呈报不执行）：K3 新二进制 LFS 路由（pack 已 147.7MiB,10x 扩张前最划算——批判环建议呈报而非默默排除）;bus-factor 组织呈报（roadmap:81 交付物）;HTML_link 别名语义实测

## 6. Non-goals（显式不做,含触发器）

- **K9/K10**（tools/ 打包、build_docs 门面拆解）：Tier 3 铁律,半搬完的子系统比平铺更糟;若操作者另给连续多夜专门窗口可单独立项
- **K11 结构化日志**：触发器（诊断队列失败靠 print 而受伤）未火,火了再做
- **K12 全量**（stale-claim 过期/跨 workflow 并发契约文档化）：只做 4b 的最小认领;并行构建矩阵在其后另行登记
- **K15/V 实现**：设计批准前只做只读台账;`sync-review --from-ledger` 为批准后候选
- InDesign Server/多机 finalize 采购;版本 pin 精确语义不放宽
- prose_table 逐型号校准矩阵（read2 已识别的「魔法矩阵」债）：显式登记为设计债,触发器=下一个需要该矩阵的新型号;届时按 read2 降级方案（可缺省 token+设计师回填）单独立项
- C4-PR2 表级并行拉取：依赖 K8 限流层先行,K8 三切片合入后作为后续小 PR 登记
- recipes 逐 (region,lang) 目录去重:触发器=下次新增占位符字段再痛一次
- Workstream M（page registry 唯一装配权威）：family-manifest 生成器是本计划选定的同题杠杆,Workstream M 保持既有登记不动、不在本计划内启动
- 泰/阿/越等新文字系统字体工程;长文 CMS 化(Workstream N 自己的门);git history rewrite;Deferred 1-5 与一切刻意冻结项

## 7. 交付与验收

- 每夜:Codex 收工报告(完成/阻塞/gate 等待);操作者只审 gate 项与 PR
- 阶段出口:Stage 0-1=传感器读数与覆盖率基线建立;Stage 2=fake-lang 零 Python 证明绿;Stage 3=KR/AU 重放 diff 干净+new-line 端到端;Stage 4=单 target 环境费<30s+批量派发零丢单+N target N 链接;Stage 5=strict 清单按拍板逐项翻转+K15 设计稿交付
- 总验收=§2 度量全部落 dashboard,下一条真实新产线按 new-line 流程走完并计时(目标 ≤2 操作者日)
