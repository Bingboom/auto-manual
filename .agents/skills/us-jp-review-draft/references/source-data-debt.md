# Source-data debt found while drafting

Problems in the live source data (Feishu Bases) that a JP review draft had to
work around. The draft fixes its own copy only; the source stays unchanged
until the operator approves a write through
[`lark-cli-bitable-ops`](../../lark-cli-bitable-ops/SKILL.md) (write, then
read back record_id + field). Rebuild the affected manuals after a fix.

| ID | Found | Where | Problem | Proposed fix | Status |
| --- | --- | --- | --- | --- | --- |
| JPD-01 | 2026-10-14, JHP-3600C JP draft v0.37 | 文档构建 Base `LD3lb4G1ua4GOVs1vxAc9W2enje` → 内容源_LCD icons `tblW5fCuJ6YdAcND`, field `icon_desc_jp` | LCD state wording is mixed. Six records use 「オン／点滅／オフ」: No.1 Wi-Fi `recvhBxMIMvx5r`, No.2 Bluetooth `recvhBxMIMwY4F`, No.3 静音充電モード `recvhBxMIMsWoY`, No.6 TOUモード `recvhBxNA2BbYd`, No.19 バッテリー残量警告灯 `recvhBxNA2eFdi`, No.20 放電タイマー `recvhBxNA2ZYWB`. Three use 「点灯時／消灯時」: No.5 自家発電モード `recvhBxNA2P5xy`, No.7 UPS機能 `recvhBxNA2PTb2`, No.16 充電速度制限 `recvhBxNA2h5G2`. The rows are shared by up to nine models (JE-1000F, JE-2000E/F, JE-1500D, JE-1800B, JE-900B, JE-1000J/H, JE-3000C), so the published JE-1000F JP manual shows the same mix. | Operator-gated write: in the six records change 「オン：」→「点灯時：」, 「点滅：」→「点滅時：」, 「オフ：」→「消灯時：」; leave the sentence bodies as they are. | open |
| JPD-02 | 2026-10-14, same check | Translation_Memory Base `Ji1hb5ub1aUbewsTljGccvx5nhc` → 句对表 `tblqtvNbgjDwR4ya`, field `jp` | Not the cause of JPD-01, but a gap: all 41 LCD state pairs (`On: Wi-Fi connected.` … `On: A discharge timer is set.`, e.g. TM-00914 … TM-00942, TM-01298, TM-SRC-*) have an empty `jp`, so TM lookup cannot supply or check this wording. | After JPD-01 is fixed, backfill `jp` from the corrected `icon_desc_jp` through `bilingual-tm-maintenance`. | open |
