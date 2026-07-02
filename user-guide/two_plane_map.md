# 双平面地图：仓库、飞书 base、谁在哪跑

Updated: 2026-07-02

这套系统有 **2 个 git 仓库 + 2 组飞书 base**，四个东西都常被叫"库"，
不看地图必混。本文是唯一的权威地图：改了拓扑（合并仓库、迁移 base、
换租户）必须同步更新这里。

## 0. 一句话总纲

**代码和表结构在工程面（auto-manual + 旧 base）演进，业务在业务面
（Hello-Docs + 新 base）运行；代码自动流过去，表结构人工 promote 过去；
翻译语料库（TM-B）是两面共享的唯一真身。**

## 1. 四个实体

| 实体 | 类型 | 角色 | 状态 |
| --- | --- | --- | --- |
| **auto-manual**（Bingboom/auto-manual） | git 仓库 | **工程面**：所有代码修改、PR、CI 验证、表结构演进都发生在这里 | 活跃 |
| **Hello-Docs**（Bingboom/Hello-Docs） | git 仓库 | **业务面**：业务运行时。单向镜像接收方——**永远不要在这里改代码** | 活跃（队列 2026-06-12 已解除暂停） |
| **旧 base**（「文档构建」space） | 飞书多维表 | 工程面数据沙盒 + legacy 数据。phase2 `DOp8bczA8aGLhJsc5iMcOqOvnpg`、TM-A `LUIcbxeKdaCY2rsEHwCcnVQSnUe`（只读归档） | legacy（本机身份已只读） |
| **新 base**（「便携资料开发工作台」space，业务租户 xcn57j1urbe6） | 飞书多维表 | **业务数据的家**。phase2「文档构建」`LD3lb4G1ua4GOVs1vxAc9W2enje`、**TM-B `Ji1hb5ub1aUbewsTljGccvx5nhc`（语料唯一规范写库）**、发布文档管理 `WGVwb2HctauRi7sEiKqcIzTRn1c` | 活跃 |

新旧 base 的完整 table_id 映射见
[`../code-as-doc/dev/bitable_schema_sync.md`](../code-as-doc/dev/bitable_schema_sync.md)
与 parity 检查；飞书复制 base 时 view_id 不变、table_id 变。

## 1.1 业务面 base 清单（操作者 2026-07-02 live 逐表枚举确认）

三个 base 都绑定在 Hello-Docs 对应的业务飞书主体（xcn57j1urbe6）上。

**① 文档构建（phase2 构建源）** — base `LD3lb4G1ua4GOVs1vxAc9W2enje`，wiki 节点 `BLYEwfMMFiS7wsk9MuvcOvdVnje`，20 张表：

| 分组 | 表名 | table_id |
| --- | --- | --- |
| 主表 | 文档构建表 | `tblbnRHjpJeCVTtj` |
| 02_主数据 | 产品信息表 | `tbl9SuJR2W1P2Rsa` |
| 02_主数据 | 项目信息 | `tblNW1zcgM75HcvL` |
| 02_主数据 | Slot | `tblS7qyV1DTZkoNq` |
| 02_主数据 | Document_key | `tbltnkDIdwiDOP7d` |
| 02_主数据 | 参数名 | `tbl8yQfXYe3KKyAM` |
| 02_主数据 | 语言 | `tblVNk16VXXVo5oj` |
| 02_主数据 | 区域法规 | `tblvBsr8qGPjXWdA` |
| 03_内容源 | 规格参数明细 | `tblPUFJqt2uGGvTT` |
| 03_内容源 | 页面占位参数 | `tblEhqJVXiyKtnwq` |
| 03_内容源 | Manual_Copy_Source | `tblboUMUiLbWk9nF` |
| 03_内容源 | Symbols | `tblSZX8hBzpJLqAe` |
| 03_内容源 | LCD icons | `tblW5fCuJ6YdAcND` |
| 03_内容源 | TROUBLESHOOTING | `tblOmJoAfU35brkb` |
| 03_内容源 | Variable_Defaults | `tblS7vc8LqR0GGNv` |
| 03_内容源 | 规格页Footnotes | `tblVusBZ8Fi56AWN` |
| 03_内容源 | 规格页notes | `tblgJCepw4JvbMbH` |
| 03_内容源 | Variable_Lang_Overrides | `tblZvjTiBypTAtdi` |
| 入库 staging | 数据入库表 | `tblIi0BEufjvGLIU` |
| 入库 staging | 规格书字段映射规则 | `tblHrelfzylJIRT2` |

**② 多维表CAT（翻译记忆，TM-B = 语料唯一规范写库）** — base
`Ji1hb5ub1aUbewsTljGccvx5nhc`，wiki 节点 `FRUywcjrPiMoPrkxnadcQhhenmb`：

| 表名 | table_id | 视图 |
| --- | --- | --- |
| Translation_Memory | `tblqtvNbgjDwR4ya` | 总表 `veweqW2fQv` |
| Terms | `tblzerRpOEuDIkKA` | `vewChPXyP9` |

**③ 发布文档管理（成品说明书目录，`product-manual-catalog` 技能读这里）** — base
`WGVwb2HctauRi7sEiKqcIzTRn1c`，wiki 节点 `QKNGwHFwPiY7J7kZ0bzcximKnyb`：

| 表名 | table_id |
| --- | --- |
| 交付资料管理 | `tbldqnNBxFQsxpeN` |
| 包材附件 | `tblmfCf3Pdk3YsdU` |

## 2. 三条同步通道

| 通道 | 方向 | 机制 | 频率 |
| --- | --- | --- | --- |
| **代码** | auto-manual → Hello-Docs | [`sync-hello-docs.yml`](../.github/workflows/sync-hello-docs.yml) | 每次合入 main 自动，秒级 |
| **表结构 + 引用数据** | 旧 base → 新 base | `python tools/bitable_schema.py promote`（只增不删、dry-run 默认）；每日 01:00 parity 哨兵盯滞后并开 `[schema-drift]` issue | 人工，有告警兜底 |
| **翻译语料** | 不同步——**只有一份** | TM-B 是唯一写库（G4 收敛）；TM-A 只读归档，工具层已拆除对它的静默回退 | — |

## 3. 谁在哪跑

| 东西 | 跑在哪 | 对着哪组 base |
| --- | --- | --- |
| CI 验证（unittest/check/门禁） | auto-manual | fixtures（不碰活库） |
| 队列 worker（构建/初稿/评审启动） | 两个仓库各自有 | 各自的 base（auto-manual→旧=legacy；Hello-Docs→新=业务） |
| schema-parity 哨兵 | 仅 auto-manual（工程面比对，锁源仓库是对的） | 读新旧两组 |
| backport-reminder 哨兵 | 两个仓库都跑（各用各的 secrets；PR #525 修复守卫后生效） | 各自的 base |
| OpenClaw / BlockClaw agent | 本机 `~/Documents/GitHub/Hello-Docs` checkout | 新 base（`~/.openclaw/.env`） |
| **业务的本机账本**（revision_ledger / tm_hit_rate） | **Hello-Docs checkout 的 `reports/`** | 闭环运营手册的日常命令在那个 checkout 里跑 |
| 工程面实验/验证产物 | auto-manual checkout 的 `reports/` | 不代表业务数据 |

## 4. 用语约定（防止再混）

- 说 **"仓库"** = git（auto-manual / Hello-Docs）；说 **"base"** = 飞书多维表。
  不要单说"库"。
- **A/B 只用来指 TM 的两个 base**（A=旧归档，B=规范写库），不要用 A/B 指仓库。
- "dev→prod"（parity/promote 的旧叫法）实际含义 = **工程面旧 base → 业务面新 base**。

## 5. 纪律（违反必出事故）

1. **代码只改 auto-manual**。Hello-Docs 是镜像，改了会被下一次同步覆盖或产生分叉。
2. **表结构只在旧 base 迭代，成熟后 promote**。直接改新 base 结构 = 绕过沙盒，
   parity 哨兵会把它当漂移报出来。
3. **语料只写 TM-B**。`tm-apply --tm-binding` 只能指向 B。
4. 业务评审、业务账本、业务回收都在 **Hello-Docs checkout** 操作。
5. **模板更新要进在飞评审**时，先 backport 收干净、再合模板 PR、再重触发
   Start Review（force reseed）——完整决策见
   [`closed_loop_ops_guide.md`](closed_loop_ops_guide.md) §4.5。

## 6. 收口清单（2026-07-02 遗留，做完删本节）

- [ ] 合并 [PR #525](https://github.com/Bingboom/auto-manual/pull/525)（回收哨兵在业务面生效）
- [ ] 飞书 UI：旧 base 文档构建表筛 `Review_status=InReview`（10 条）→ 全部改 `NotStarted`
      （本机 bot/user 身份对旧 base 只读，需操作者手动）；改完后 auto-manual 侧
      [issue #524](https://github.com/Bingboom/auto-manual/issues/524) 会被哨兵自动关闭
- [ ] 飞书 UI：旧 base 标题加 **【归档】** 前缀，权限保持只读
- [ ] 核对 auto-manual 仓库 secret `FEISHU_TRANSLATION_MEMORY_BASE_TOKEN` 是否 =
      `Ji1hb5ub1aUbewsTljGccvx5nhc`（B）；不是则更新（TABLE_ID 应为
      `tblqtvNbgjDwR4ya`，VIEW_ID `veweqW2fQv`）

## 7. 架构演进备忘

"要不要收敛成一个仓库"在 2026-07-02 评估过：**现在不合**。双仓库运营成本低
（同步全自动），双 base 的沙盒价值在表结构活跃演进期是真实的（6 月的源表拆分
就是先在旧 base 迭代再 promote 的）。再评估条件：**promote / parity 连续约三个
月无事可做**（结构稳定）时，考虑"单仓库 + GitHub Environments 双 secrets"方案
合并仓库——而不是简单删掉镜像。
