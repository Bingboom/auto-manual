# JBP-2000B_JP live staging readback (2026-08-30 PT)

- Business-plane identity: `prod` / `bot`
- Base: `LD3lb4G1ua4GOVs1vxAc9W2enje`
- Staging table: `tblIi0BEufjvGLIU`
- Target: `JBP-2000B_JP`
- Readback: 17/17 rows; 11 specifications + 6 placeholders
- Every row: `Source_lang=ja`, `状態=✅直通`, `確認=FALSE`, `入庫結果` empty
- Formal source tables at this gate: specifications 0 rows; placeholders 0 rows

| record_id | Page | Row_key | Slot_key | Value |
| --- | --- | --- | --- | --- |
| `recvtR9ZPP52wa` | Product overview | main_power_button | label | 主電源ボタン |
| `recvtR9ZPPW3Rh` | Product overview | dc_expansion_port | side.a.label | DC 拡張ポート A |
| `recvtR9ZPPs6Au` | Product overview | dc_expansion_port | side.a.spec | 接続拡張ケーブルのプラグAに接続 |
| `recvtR9ZPPNGgr` | Product overview | dc_expansion_port | side.b.label | DC 拡張ポート B |
| `recvtR9ZPPTU3E` | Product overview | dc_expansion_port | side.b.spec | 接続拡張ケーブルのプラグBに接続 |
| `recvtR9ZPP27RS` | operation_guide | default_standby_duration | value | 2時間 |
| `recvtR9ZPP4Ljc` | specifications | charging_temperature | main | -10℃~45℃ |
| `recvtR9ZPPWR17` | specifications | discharging_temperature | main | -10℃~45℃ |
| `recvtR9ZPPLf7P` | specifications | storage_temperature | main | 1年間 0~25℃ / 3ヶ月 0~45℃ / 1ヶ月 -20~45℃ |
| `recvtR9ZPP12aC` | specifications | capacity | main | 2048 Wh (40Ah/51.2V DC) |
| `recvtR9ZPPGpPf` | specifications | cell_chemistry | main | LiFePO₄ (リン酸鉄リチウムイオン電池) |
| `recvtR9ZPPI5q9` | specifications | cycle_life | main | 6,000回の充放電後も容量の70%以上を維持 |
| `recvtR9ZPPTzzq` | specifications | model_no | main | JBP-2000B |
| `recvtR9ZPPhJPU` | specifications | product_name | main | Jackery Battery Pack 2000 |
| `recvtR9ZPPERnB` | specifications | weight | main | 約365 × 255 × 191 mm (約14.8kg) |
| `recvtR9ZPPCh9L` | specifications | dc_expansion_port | main | 36.8V-57.6V⎓最大75A |
| `recvtR9ZPPnYQk` | specifications | dc_expansion_port | main | 36.8V-57.6V⎓最大75A |

No formal-source, asset-registry, build-table, or schema write was performed.
