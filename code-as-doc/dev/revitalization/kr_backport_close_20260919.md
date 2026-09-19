# JE-2000E-KR 回写轮收尾报告（Hello-Docs#90 合入后）

- generated_utc: 2026-09-19T09:16:25Z
- 对象：`review/JE-2000E-KR` @ tip `d53ccf331dd13ffd2c7d2279ab7111b5091d6a05`（= Hello-Docs#90 squash `d53ccf33`，仅存在于 hello-docs 远端；origin 无此分支）
- 工具：`tools/cloud_doc_backport.py run-review-branch`（dry-run，`--remote hello-docs --lang ko`，F2 值索引 147 值 / data/phase2 快照 2026-08-22，F3 家族模板 11 个）
- worktree：`/Users/hello-tech-team/Documents/GitHub/auto-manual-worktrees/review-review-JE-2000E-KR`（工具自动 fetch+reset 到远端 tip；始终干净，收尾时 status=0、HEAD=d53ccf33）
- 评审文档行：文档构建表 `LD3lb4G1ua4GOVs1vxAc9W2enje`:`tblbnRHjpJeCVTtj`，record `recvsI5B5GSKvu`（Document_ID `JE-2000E_KR_0.2`，Review_status InReview，飞书云文档 wiki `Jwp8wWi5LirRUskXP7gcUQd4nNg`）
- 主 checkout 未动（保持 `feat/sweep-terminology-crosscheck`）；两次 run 均为 dry-run，分支零写入。

## 1. rediff 结果

| 轮次 | run_id | 基线 | deltas | 结果 |
| --- | --- | --- | --- | --- |
| r1（快照前） | backport-review-JE-2000E-KR-20260919-close-r1 | 旧基线① `IvoSweoyfiuGEtkQNtLcK0Rwnlg`（基线20260819） | **93** | DIFF（routes: R=37, D=54*, image=1, human=1；*工具口径含删除类） |
| r2（快照后） | backport-review-JE-2000E-KR-20260919-close-r2 | 新基线① `I5sNwpFvFiRF1bkIBfccWjMenFd`（基线20260919） | **0** | **NO_DIFF** ✅ |

r1 的 93 delta 与 PR#67 轮（2026-09-05）报告的 93 逐批同源 = 冻结基线陈旧导致的幂等重报（PR#60 曾有意不推进基线：「否则未落地 delta 会从下轮 diff 消失」）。逐条判定见 §4：无一条是本次恢复（PR#90）造成的缺失；真残差全部是前两轮已登账的分流/延后项。

报告文件：`rediff1/`、`rediff2/`、`delta_judgment_r1.json`、`cloud_doc_current.md`（判定用云文档快照）。

## 2. 基线重快照（授权内 SOP 动作）

两层基线，按 runbook §6 只推进第①层（行上冻结副本）：

| 项 | 值 |
| --- | --- |
| 旧指针（写前读） | ``https://xcn57j1urbe6.feishu.cn/wiki/IvoSweoyfiuGEtkQNtLcK0Rwnlg``，节点 title `manual_je2000e_kr_ko_0.2_基线20260819`（保留在 wiki 供追溯，未删除） |
| node-copy | `wiki +node-copy --as bot` 源 `Jwp8wWi5LirRUskXP7gcUQd4nNg` → 过程文档管理 `AvBhwdpNxivgXfkPm1VcCG01nPh`（space 7649591386208717774） |
| 新冻结副本 | 节点 `I5sNwpFvFiRF1bkIBfccWjMenFd`，obj `L0R1dmweYovQMRxmFb6c4a0ZnIc`，title `manual_je2000e_kr_ko_0.2_基线20260919` |
| 副本内容校验 | fetch 副本 vs 当前云文档，normalize 后 **完全相等**（原始字节差异仅为飞书按文档重生成的图片 token/alt 噪音） |
| 行指针写入 | `+record-upsert --record-id recvsI5B5GSKvu`，字段 `基线文档` = 新副本 URL（保持 url-style 字段形制） |
| 写后回读 | sleep 6s 后 `+record-get`：`基线文档` = `https://xcn57j1urbe6.feishu.cn/wiki/I5sNwpFvFiRF1bkIBfccWjMenFd`（url-style 渲染形） ✅（record_id `recvsI5B5GSKvu`，Git_ref/飞书云文档/Review_status 未变） |
| 生效证明 | §1 的 r2 rediff = 0（fetch 优先走行上基线①） |

**分支 seed 基线②**：合并 tip 上不存在 `docs/_review/JE-2000E/KR/**/.backport/*.baseline.md`（`git ls-tree -r d53ccf33` 全量列举 + KR 目录只含 `ko/`，两个正交面核验）。基线①存在时②不参与 diff（工具取用优先级①>②），且创建②需向 review 分支直接落 commit——本轮判定**不新建**，属显式决策而非遗漏。若后续操作者要同步②，走 `run-review-branch --seed --reseed --push`（工具会在 worktree 提交 seed 文件）。

未触碰的同分支旧行：`recvsC2hJVuUY9`（JE-2000E_KR_0.1，自带 0.1 云文档/0.1 基线，已被 0.2 轮取代）、`recvukpZmgHa1G`（Start Review 行，无云文档字段）——均在授权外，保持原样。

## 3. 删除专项复查（post-apply checklist §1）

对当前云文档导出全文（`cloud_doc_current.md`，33,268 字符）逐项核验「源里有、文档里没有」：

| 删除类 delta | 判定 | 证据 |
| --- | --- | --- |
| #47–#59（故障排除表 13 条管道行，F0–F9/FC/FE + 分隔行） | **diff 错位，非真删除**（与 PR#67 判定一致） | 云文档故障排除表以 HTML 形态完整含 **全部 12 个错误码**（F0–F9、FC、FE，`<td>` 逐一命中）；tip 两份 troubleshooting 页 12/12 在位（§4） |
| #20（AC1/AC2 콘센트 쌍 句） | **replace 配对，非删除** | 云文档 L123 = tip `05_operation_guide_placeholder.rst:39` **逐字相同**（AC 콘센트 1구/2구 新句）；被"删"的是基线旧句 |
| #39/#40（太阳能段图+句） | **段落/图位合并，非删除**（与 PR#60 判定一致） | 「두 개의 태양광 패널…」在云文档出现 2 次（已并入引言段）；tip 08 页含完整尾从句 |

弃权/结构删除项：r2 报告为空（deltas=0），无未处置弃权。**删除专项 = PASS，无真实删除逃逸。**

## 4. 恢复清单复查矩阵（合并 tip，`restore_recheck.json`，大小写不敏感）

**在位 40/40（范围内全通过）**，含反向探针：

| 组 | 探针 | 结果 |
| --- | --- | --- |
| 故障排除 F0–F9、FC、FE | `page/troubleshooting_ko.rst` 12/12 + `generated/JE-2000E/troubleshooting_ko.rst` 12/12（`* - <code>` 行形） | ✅ 24/24 |
| 12_app 7 处 | 2.1 韩文「버튼을 눌러 장치를 추가」/ 2.2 「장치의 POWER 버튼」/ 按钮清单 `\| POWER 버튼`+`\| AC1 전원 버튼`+`\| AC2 전원 버튼` / 참고块 POWER+DC/USB 3초 / 4.1+4.2 `DC/USB 전원 버튼 + AC1 전원 버튼`（count=2）/ 4.3 동시에 3초 | ✅ 9/9 |
| 06_ups 2 处 | 合并单行句（`10A에 도달합니다. 바이패스 모드에서는…복귀합니다.`）；`0ms` 紧排 ==2（排除 10ms） | ✅ 2/2 |
| 08_charging 尾从句 | 「태양광 패널 커넥터(별도 판매, 기본 구성품 아님)를 통해 충전하십시오」 | ✅ 1/1 |
| 反向探针 | 英文 `Click the`、裸 `\| 전원 버튼` 行、裸 `AC 전원 버튼`、`0 ms` 带空格 —— 均不出现 | ✅ 4/4 |

范围外备注：`generated/JE-2000E/draft/12_app_setup_ko.rst` 不含 POWER 버튼/AC1（与恢复来源树 `6e564eac` 一致为 0 处——draft 生成副本历轮就未携带该编辑，属下次构建刷新件，非恢复残漏）。

## 5. r1 93 delta 逐类处置账（scope closure）

| 处置 | 数量 | 明细 |
| --- | --- | --- |
| 已在 tip（基线过期重报） | 53 判定器直证 + 9 纯标记/表形噪音 + 1（#30，line-block `\|` 匹配假阴性，人工核实在位） | 含 12_app/06_ups/08/11_warranty/02_box 各轮已落编辑、F6 已落源表新值（점멸、AC1 콘센트、규격 千分位等） |
| 删除类 = diff 错位/配对 | 16 | §3 |
| 分支比文档新（有意超前，非残差） | 3 处 | #86/#92 `APP→App`（PR#67+模板#984 已统一，文档旧拼写未回改）；#64 `2 × DC8020 포트`（F6 批准形，评审原笔 `입력`） |
| **真残差 A：上游已修、待传播** | 3 | #21（62368-1 句 본 제품은）、#38（08 引言主语）、#41（Voc 句 본 제품의）—— auto-manual **PR#1044**（09-05T14:41 合入，晚于 07:57 重播种）已改 `page_eu-kr/05` + `page_shared/ko/08` 模板；本在评审分支未拾取，下次 re-seed/Start Review 自动带入，或按 runbook Class T 同轮补改评审页 |
| **真残差 B：F6/源表 본 제품 通扫未做**（MA-041/054 显式排除项） | ~4 组 | #17 LCD 표（충전 계획 행 产品名 → 본 제품의；文档还含 `충전 전력 제한` 行文案）、#46/#59 故障排除 FC/F9 行产品名与 `DC 12V/USB→DC/USB` 简写、#42 车充주의 句（본 제품을+시동을 거십시오 措辞）、#64 尾注 `바이패스 모드①①` 双标记（= PR#90 body follow-up #2，F6 路径已登账） |
| **真残差 C：未路由的评审编辑** | 5 组 | #00 序言 `(이하 "본 제품")` 定义句、#01 序言 `해석권은 회사에→Jackery에`、#10+#11+#13 概览新增「왼쪽 측면도」小节（핸들/DC 확장 포트 행，需资产+占位行）、#75 규격 `※ USB Type-C®…USB Implementers Forum` 商标注（KR 无此行，EU-EN 模板有先例）、#37 `비상 충전 모드` 标题层级（Class T，自 PR#60 起挂账，main 模板仍为粗体段）+ #32 07_extra 주의 第一条措辞（评审原笔 vs 更新模板文案，语义等价、PR#67 已延后） |

真残差 A/B/C 均为 PR#60/#67 轮**当时已明示分流或延后**的项（两轮 PR body 均有记录），无一条由 09-05 re-seed 或本次恢复新造。基线①已推进，这些项**不再出现在下轮 diff**——本表即其防丢失台账；后续处置路线：A=等 re-seed（或评审页传播），B=按 F6 审批流对源表（TROUBLESHOOTING `tblOmJoAfU35brkb`、LCD icons `tblW5fCuJ6YdAcND`、规格脚注 `tblVusBZ8Fi56AWN` 等），C=需操作者逐条拍板（序言两句可走评审页 Class R；왼쪽 측면도/商标注/标题层级涉及资产·数据·模板机制）。

## 6. 遗留（沿承 PR#90 body follow-up，未在本轮处置）

1. 错误码源行适用型号核查（防再次 re-seed 冲掉恢复行）——PR#90 follow-up #1，未动活表。
2. `바이패스 모드①①` 双脚注标记 F6 修复——follow-up #2（§5 残差 B 项之一）。
3. §5 真残差 A/B/C 的路由执行。
