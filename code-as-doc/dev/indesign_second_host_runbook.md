# InDesign 第二主机 Runbook（Milestone K7）

Registered: 2026-07-17

## 0. 为什么有这份文件

IDML→成品 PDF 的终饰(finalize)是全流水线**唯一不在 CI 里**的交付环节,
历来只跑在操作者的 Mac 上——生产就绪评审把它列为最高交付 SPOF。这份
runbook 的目标:任何一台满足前提的 Mac,照着本文从零到跑通一次 finalize,
使"操作者的 Mac 不可用"从事故降级为不便。

配套机制(随本 PR 落地):

- **版本锁**:[`tools/idml/indesign_version_pin.json`](../../tools/idml/indesign_version_pin.json)
  是唯一权威版本(当前 `Adobe InDesign 2026 21.0.1.6`,2026-07-17 从操作者
  Mac 采集)。`tools/indesign_finalize.py` 启动时比对本机版本:**不匹配直接
  拒跑**(`--allow-version-mismatch` 可强行越过,但 mismatch 会记进
  finalize report 的 `toolchain` 块)。精确到补丁号——漂移版本的排版输出
  不可跨机比对,所以升级的正确动作是"两台机一起升 + `--write-pin` 重锁",
  不是放宽比对。

## 1. 前提

| 项 | 要求 |
| --- | --- |
| 硬件/系统 | macOS(finalize 走 osascript + InDesign ExtendScript,Windows 不适用) |
| InDesign | 与版本锁完全一致(见上;安装后先跑 §2 第 3 步核对) |
| 仓库 | clone auto-manual + `.venv`(`ONBOARDING.md` §5 环境步骤) |
| 字体 | 手册用字体本机已安装——从最近一次 release 的 handoff zip 里的字体清单核对(交付包含 Links 相对化与字体清单,见 `reports/releases/` 的 handoff 产物);缺字体会在 finalize report 的 `missing_fonts` 里暴露 |
| pdfinfo | `brew install poppler`(PDF/X 合规校验用) |

## 2. 从零验证步骤(每步都可独立失败、独立修)

```bash
# 1. 环境自检(python/pandoc 等;InDesign 不在 doctor 里,下一步单独核)
python build.py doctor

# 2. 版本核对——必须输出 match,否则先对齐 InDesign 版本再继续
python tools/indesign_finalize.py --check-host

# 3. 取一个已知良品 IDML(最近一次 release 的 handoff zip,或让操作者
#    指定 docs/_build/<model>/<region>/ 下的现成 IDML)

# 4. 跑一次 finalize(输出放临时目录,不碰仓库)
python tools/indesign_finalize.py \
  --idml <known-good>.idml \
  --indd /tmp/k7-verify/out.indd \
  --pdf  /tmp/k7-verify/out.pdf \
  --report /tmp/k7-verify/report.json

# 5. 验收 = 与主力机基线报告**逐项一致**(2026-07-21 修正:不是 overset 清零):
#    - missing_fonts/bad_links 全空、pdf_export_validation.pass=true、
#      toolchain.version_pin_status="match"
#    - page_count/story_count 与基线相同
#    - overset_stories 的 story id 集合与基线**完全一致**
#    说明:红 ⊞ 溢流是设计内的 designer 工作项(内容都在 story 里,拖框
#    即现,见交付包内 designer_checklist.md);历史上从无 overset=0 的包,
#    因此"已知良品"的真义是"已知基线"。基线报告随包携带(主力机同输入
#    finalize 的 report.json);两份报告除本机路径字段外 diff 应为零。
#    退出码:基线含 overset 时命令退出 1,属预期,以报告一致性为准。
```

## 3. 验证登记

主机预检只证明版本锁可用，**不等于**跑通 finalize。预检可先登记，完整首验仍须
填写后面的端到端表格。

| 日期 | 主机 | InDesign 版本 | 预检结果 | 尚欠 |
| --- | --- | --- | --- | --- |
| 2026-07-20 | `ArriettyMac-mini.local` | Adobe InDesign 2026 21.0.1.6 | `python tools/indesign_finalize.py --check-host` → `match` | 下载的 main 目录没有已知良品 IDML；§2 步骤 3-5 未执行，K7 仍为 `in_progress` |

跑通一次后,把记录追加到下表**并同步更新 `ONBOARDING.md` §3 登记表**
(这一行从"待第二主机验证"改为"已验证 + 日期")。

| 日期 | 主机 | InDesign 版本 | IDML 来源 | 结果 |
| --- | --- | --- | --- | --- |
| 2026-07-21 | `ArriettyMac-mini.local` | Adobe InDesign 2026 21.0.1.6(`pin=match`) | `manual_je1000f_us_publish_1.6_handoff.zip`(11 跑 publish 长征产物,Document fonts 随包) | **通过(基线一致性)**:pages=63、story_count=546、fonts=0、links=0、PDF/X-4+Japan Color 2001 Coated+JC200103 全过;11 条 overset 的 story id/顺序/页框定位与主力机基线完全一致,排除三条本机路径字段后两份 JSON diff 为零。⇒ 两主机等价,K7 关闭。11 条 overset 为 #692 组成在回退计划下的已知内容/版面项,归 replica 线契约重基线处理 |

## 4. 日常纪律

- **版本升级**:两台(所有)finalize 主机一起升 → 任一台跑
  `python tools/indesign_finalize.py --write-pin` → 提交 pin 的 diff →
  另一台跑 `--check-host` 确认 match。禁止只升一台。
- **节奏**:季度冷启动演练(ONBOARDING §7)时在第二主机重跑 §2,
  保持"可恢复"是被验证过的事实而不是文档愿望。
- **文字改动永远不在 InDesign 层做**(ONBOARDING §8 既有红线),
  第二主机同样适用。
