# RTD 自有域名绑定 runbook

状态：**待执行**。依据：运营规划第 0 步决策 D3（绑定，2026-09-15），见
`code-as-doc/manual_operations_growth_plan.md`（#1150 分支，合入后为正式坐标）。
Owner：夏冰。绑定动作全部发生在 RTD 后台与 DNS 面板，不改仓库代码；本 runbook
只固化步骤、不变量与验收。

## 0. 待补输入（操作者提供后再执行）

- [ ] 最终域名：＿＿＿＿（例如 `manuals.<品牌域>.com`；建议子域，不建议裸 apex）
- [ ] DNS 面板权限归属（谁能加 CNAME 记录）：＿＿＿＿

## 1. 不变量（执行前后都必须成立）

1. **已印刷的 QR 码与既有 `*.readthedocs.io` 链接必须继续可达**。RTD 把自有域名
   设为 canonical 后，旧域名请求会 301/302 跳转到新域名同路径；绑定失败或证书
   未签发期间旧域名不受影响。
2. **不改冻结出版物内容**：域名绑定是托管层配置，`docs/publish/**`、别名与
   嵌套路由零变更。
3. **线上表的 `HTML_link` 记录暂不改写**：旧链接经跳转仍有效；是否批量改写为
   新域名是独立的、审批门内的源表写入决策，不随本 runbook 执行。

## 2. 执行步骤（RTD 后台 + DNS）

1. RTD 项目 → Admin → Domains → 添加自有域名，勾选 canonical。
2. 按 RTD 给出的目标值在 DNS 面板加 CNAME 记录（子域 → `readthedocs.io` 指向值）。
   若 DNS 托管在 Cloudflare：**先用 DNS-only（灰云）**等 RTD 完成域名验证与
   Let's Encrypt 证书签发；确需开代理（橙云）时 SSL 模式设 Full，并复验证书续期。
3. 等待 RTD 显示证书就绪（通常分钟级到小时级，取决于 DNS 生效）。

## 3. 验收清单

- [ ] `curl -I https://<新域名>/` 返回 200，证书为新域名有效证书。
- [ ] `curl -I https://<旧 readthedocs.io 域名>/<任一手册路径>` 返回 301/302，
  Location 指向新域名同路径。
- [ ] 抽查一个印刷 QR 别名路径：扫码/直开旧链接最终落在新域名的正确页面。
- [ ] 按线上 HTTP 健康 runbook（`manual_operations_online_health.md`）以新域名
  为基准重跑一轮，全路由通过。
- [ ] 抽查一个多语切换页与站内搜索页，确认相对链接在新域名下正常。

## 4. 与其他决策的联动

- **D1 访问统计**：Cloudflare Web Analytics 站点按最终域名创建；域名绑定完成后
  再建站点、取 token，然后走 settings 激活切片（`analytics_beacon_token`）。
  先绑域名、后开统计，避免统计站点换域名重建。
- **D2 反馈邮箱**：与域名无关，不受本 runbook 影响。

## 5. 回滚

RTD 后台删除自有域名（或取消 canonical），DNS 删除 CNAME。旧
`*.readthedocs.io` 域名全程未停用，回滚即恢复原状；无内容或数据需要恢复。

## 修订记录

| 日期 | 变更 | 经手 |
| --- | --- | --- |
| 2026-09-15 | 初版：D3 决策后的绑定步骤、不变量与验收清单 | Claude（操作者：夏冰） |
