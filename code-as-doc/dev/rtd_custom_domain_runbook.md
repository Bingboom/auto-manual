# RTD 自有域名绑定 runbook

状态：**暂缓执行（2026-09-15）**。域名已定 `manuals.jackery.com`，但 `jackery.com`
的 DNS 权限不在操作者手里，绑定需要跨团队交接；操作者裁决先按 RTD 默认域名
跑 D1 统计，本 runbook 挂起，待 DNS 交接可行时再执行。依据：运营规划第 0 步决策 D3（绑定，2026-09-15），见
`code-as-doc/manual_operations_growth_plan.md`（#1150 分支，合入后为正式坐标）。
Owner：夏冰。绑定动作全部发生在 RTD 后台与 DNS 面板，不改仓库代码；本 runbook
只固化步骤、不变量与验收。

## 0. 待补输入（操作者提供后再执行）

- [x] 最终域名：**`manuals.jackery.com`**（操作者拍板，2026-09-15；子域，符合建议）
- [ ] DNS 面板权限归属：**不在操作者手里**（jackery.com DNS 由其他团队掌握，
  2026-09-15 确认）。执行前需确认对接团队并完成 CNAME 申请交接；申请件只有
  一条记录：`manuals` 子域 CNAME → RTD 后台 Admin → Domains 添加域名后给出的
  指向值。

## 1. 不变量（执行前后都必须成立）

1. **已印刷的 QR 码与既有 `*.readthedocs.io` 链接必须继续可达**。RTD 把自有域名
   设为 canonical 后，旧域名请求会 301/302 跳转到新域名同路径；绑定失败或证书
   未签发期间旧域名不受影响。
2. **不改冻结出版物内容**：域名绑定是托管层配置，`docs/publish/**`、别名与
   嵌套路由零变更。
3. **线上表的 `HTML_link` 记录暂不改写**：旧链接经跳转仍有效；是否批量改写为
   新域名是独立的、审批门内的源表写入决策，不随本 runbook 执行。

## 2. 执行步骤（RTD 后台 + DNS）

1. RTD 项目 → Admin → Domains → 添加 `manuals.jackery.com`，勾选 canonical。
2. 在 `jackery.com` 的 DNS 面板给 `manuals` 子域加 CNAME 记录（→ RTD 给出的
   `readthedocs.io` 指向值）。
   若 DNS 托管在 Cloudflare：**先用 DNS-only（灰云）**等 RTD 完成域名验证与
   Let's Encrypt 证书签发；确需开代理（橙云）时 SSL 模式设 Full，并复验证书续期。
3. 等待 RTD 显示证书就绪（通常分钟级到小时级，取决于 DNS 生效）。

## 3. 验收清单

- [ ] `curl -I https://manuals.jackery.com/` 返回 200，证书为该域名有效证书。
- [ ] `curl -I https://<旧 readthedocs.io 域名>/<任一手册路径>` 返回 301/302，
  Location 指向 `manuals.jackery.com` 同路径。
- [ ] 抽查一个印刷 QR 别名路径：扫码/直开旧链接最终落在 `manuals.jackery.com` 的正确页面。
- [ ] 按线上 HTTP 健康 runbook（`manual_operations_online_health.md`）以
  `manuals.jackery.com` 为基准重跑一轮，全路由通过。
- [ ] 抽查一个多语切换页与站内搜索页，确认相对链接在新域名下正常。

## 4. 与其他决策的联动

- **D1 访问统计**：因本 runbook 暂缓，操作者裁决（2026-09-15）**先按 RTD 默认
  域名创建 CWA 站点**、取 token 走 settings 激活切片（`analytics_beacon_token`），
  统计先跑起来。已知代价：将来绑定 `manuals.jackery.com` 后 CWA 站点需按新域名
  重建，统计数据不连续——此代价已被明确接受。
- **D2 反馈邮箱**：与域名无关，不受本 runbook 影响。

## 5. 回滚

RTD 后台删除自有域名（或取消 canonical），DNS 删除 CNAME。旧
`*.readthedocs.io` 域名全程未停用，回滚即恢复原状；无内容或数据需要恢复。

## 修订记录

| 日期 | 变更 | 经手 |
| --- | --- | --- |
| 2026-09-15 | 初版：D3 决策后的绑定步骤、不变量与验收清单 | Claude（操作者：夏冰） |
| 2026-09-15 | 补入操作者拍板的最终域名 `manuals.jackery.com`，步骤/验收具体化 | Claude（操作者：夏冰） |
| 2026-09-15 | 确认操作者无 jackery.com DNS 权限：runbook 暂缓，D1 改为先按 RTD 默认域名建站跑统计 | Claude（操作者：夏冰） |
