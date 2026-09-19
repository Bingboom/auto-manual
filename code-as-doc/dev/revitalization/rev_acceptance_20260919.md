# 0–30 天批次验收单（2026-09-19）

给验收人（夏冰）的一页纸：每行=一个 REV 任务的产物与验收动作。验收通过即在台账把该行
`verifying` 翻 `done` 并记验收人/日期；有异议的行退回说明即可。

| 任务 | 交付 | 证据 | 验收动作 |
|---|---|---|---|
| REV-01 两站快照 | 截图全部核实；旧站实为无 webhook 冻结项目 | [rev01_inventory.md](rev01_inventory.md) / [rev01_url_map.csv](rev01_url_map.csv) | 抽查清单任意行 |
| REV-02 旧链接核查 | 三登记面对旧站零暴露；HTML_link 形态不一致已修 | [rev02_link_audit.csv](rev02_link_audit.csv) / [rev02_conclusions.md](rev02_conclusions.md) | 认可"暴露面为 0"结论 |
| REV-03 入口整合 | 旧站已删、四探针 404、新站回归全绿、恢复路径在位 | [rev03_closing.md](rev03_closing.md) | 认可死亡探针与回归表 |
| REV-04 覆盖清单 | 24/47/52 三数闭环；现口径 52 目标/22 本 | [rev04_explain.md](rev04_explain.md) | 认可口径解释 |
| REV-05 能力矩阵 | 34 动作/14 workflow 在册；月报调度证实（本机定时任务，10-01 首跑） | [rev05_capability_matrix.md](rev05_capability_matrix.md) | 抽查矩阵任意行 |
| REV-06 M0 对账 | 12 条差异定性；2+1 项授权写已执行 | [rev06_m0_diff.md](rev06_m0_diff.md) / [writes_20260919.md](writes_20260919.md) | 认可差异表与写操作回读 |
| REV-08 目标校验 | #1190/#1192 已合；首跑抓出 429 缺陷，修复 #1193 待合 | PR 记录 + [kr 之外另见 #1193 正文] | 合 #1193，观察次日 cron 绿 |
| REV-10 M4/M5 | 入口映射表 v1 + 口径快照第一期 | [rev10_entry_map.md](rev10_entry_map.md) / [rev10_metrics_snapshot.md](rev10_metrics_snapshot.md) | 认可两份模板即可 |
| REV-11 翻译首批 | 74 补 Draft、59 转 Approved（7 带改值）、81 盖章、回灌 3 行、AC1 裁决落库 | [tm_writes_20260919.md](tm_writes_20260919.md) | 认可计数复核（1358 行 974/21/363） |
| REV-12 可达性与下一批 | 实测清单/IT 待办/下一批建议 | [rev12_reachability_and_next.md](rev12_reachability_and_next.md) | 大陆实测由大陆侧执行后回填 |
| （批次外）KR 回退轮 | HD#90 恢复+rediff=0+基线 20260919+F6 11 格修复+渲染证明 | [kr_backport_close_20260919.md](kr_backport_close_20260919.md) / [kr_error_codes_rootcause.md](kr_error_codes_rootcause.md) / [kr_f6_model_tags_20260919.md](kr_f6_model_tags_20260919.md) | 认可收尾报告 |

## 仍开着的口（不阻塞验收）

1. **#1193**（429 节流修复）待合；合后哨兵 Hello-Docs#91 于下次全量绿跑关闭。
2. **KR 未路由评审编辑 5 组**待路由拍板（序言两句 / 概览左侧面图小节 / USB 商标注 /
   标题层级——清单见 kr_backport_close §未决项 C）。
3. **F6「본 제품」通扫 ~4 组**（此前 MA-041/054 显式排除的存量，含 `바이패스 모드①①`
   双标记）——归下一个 F6 批次。
4. **37 条 TM 未解析候选**：评审句对不在现有 ko 语料，收编需"建新行"的新授权——建议随
   十月批次一并裁。
5. **3000C 反向候选 `1ef29f0b8796`**：已按"AC 按 2000E 的来"裁决压制，**不得再 approve**
   （防止把共享行翻回）。
6. REV-07/09（M1/M2 闭环、恢复演练）依赖本批验收后进入；JE-1000F US 补 fr/es 已列
   REV-21 便宜候选（rev12 §3）。
