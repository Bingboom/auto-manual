# JBP-3600A EU/en Web production-readiness evidence

Date: 2026-09-06

Target: `JBP-3600A / EU / en` (`HTP011`, Jackery Battery Pack 3600)

Engineering baseline: `9b356ecadfe355aae0eb474ef4c49bf168a01e4c`

Status: **engineering acceptance complete; live writes, review seed, Web Publish,
snapshot PR and formal URL are not yet authorized or executed.** The exact gated
increment is recorded in
[`reports/source_intake/JBP-3600A_EU/web_live_increment_plan_2026-09-06.json`](../../reports/source_intake/JBP-3600A_EU/web_live_increment_plan_2026-09-06.json).

## Source and identity

The current published booklet remains the content authority. The live DingTalk
page title reads `Jackery Battery Pack 3600 User Manual (JBP-3000A) EUUK
V2.0-2026-08-04.pdf`; the visible manual identity and the Illustrator source are
`JBP-3600A`. `JBP-3000A` is preserved only as external filename debt.

| Evidence | Identity | SHA-256 |
| --- | --- | --- |
| Current published PDF | [DingTalk PDF](https://alidocs.dingtalk.com/i/nodes/NZQYprEoWoeAawzwfBwMeb25J1waOeDk), V2.0-2026-08-04 | `084dd4517feddcd9b77da10415a2787ec4427f882a7b819160725fdff679ccfe` |
| DingTalk source-list row | `hgXiHot5Ow`, `BP3600加电包`, model `JBP-3600A` | source AI below |
| AI attachment | `16-0102-000334 说明书 HTP0113600A-EU-JAK RoHS REACH.ai`, 8,923,381 bytes, 10 pages | `e0ccc33427f89c77c30d32e073a3027123f4c8a9c9f5029d2378172a7f0a3761` |
| Approved recipe | `data/asset_recipes/manual_jbp3600a_eu_web.json` | `68fdf5c93fe9422e531234d264698709b2da81530690c6d8fbe6d972d34d63d1` |
| Web illustration binding | `docs/renderers/web/jbp3600a_eu_en_illustrations.json` | `b4e72a782d9acb6d88a133e53ef445695c375c346371fe0b2ae24e6ce0da47d4` |

The source artwork and all charging/connection copy bind to Jackery Explorer
3600 Plus. No JBP-2000B parameter or host artwork is used.

## Live business-plane preflight

The business Base `LD3lb4G1ua4GOVs1vxAc9W2enje` was queried with
`--profile cli_aaa0db0d4b39dcca --as bot`. Field shapes were read before target
queries. These are live reads from 2026-09-06; no row or field was written.

| Target set | Table | Live count / result |
| --- | --- | ---: |
| product `JBP-3600A` | `tbl9SuJR2W1P2Rsa` | 0 |
| project `HTP011` | `tblNW1zcgM75HcvL` | 0 |
| `JBP-3600A_EU` | Document_key `tbltnkDIdwiDOP7d` | 0 |
| build row by target/project | `tblbnRHjpJeCVTtj` | 0 |
| specifications | `tblPUFJqt2uGGvTT` | 0 |
| page placeholders | `tblEhqJVXiyKtnwq` | 0 |
| Manual_Copy_Source | `tblboUMUiLbWk9nF` | 0 |
| troubleshooting | `tblOmJoAfU35brkb` | 0 |
| source key or source SHA | `04_资产源文件` `tblsXlZx61Ff5pQC` | 0 |
| source-key definitions | `04_资产定义` `tblWilXeN5FXPraC` | 0 |
| source-key exports | `04_资产导出物` `tblavT0dcjZGK9DR` | 0 |
| published catalog (`JBP-3600A`, `HTP011`, `JBP-3000A`) | `tbldqnNBxFQsxpeN` | 0 for all three searches |

The Symbols and LCD `Model` filters returned `not_found`, and their live option
lists do not contain `JBP-3600A`. `secondary_li_ion_battery` is also absent from
the parameter Row_key table. Those three reference additions must follow the
engineering-plane-to-business-plane promote boundary; they are not direct live
schema edits for this target.

This is an additive intake. A repeated pre-write query is still mandatory at
execution time because the business state may change after this report.

## Exact reviewable increment

The approval plan is split into four batches so record-link IDs exist before
dependent rows and a build row cannot accidentally dispatch.

1. Promote the two `JBP-3600A` Model options and the
   `secondary_li_ion_battery` Row_key; create product, project and Document_key.
2. Create 38 structured-source rows: 21 specification/overview/storage values,
   8 Symbols, 2 LCD rows and 7 troubleshooting rows. Page placeholders and
   Manual_Copy_Source remain intentionally zero because the locked target fixture
   has no target-specific rows in those datasets.
3. Create one asset-source row, 15 asset definitions and 43 asset exports in the
   new three-table asset pipeline. Do not write `tblxFBWaDG4OYhqu`.
4. Create a dormant build record for version `2.0`; leave
   `是否触发文档构建` empty. The main task can later seed
   `review/JBP-3600A-EU` and transition the same record to `Web Publish` in the
   shared release order.

The structured rows are frozen by target-filtered canonical JSON digests:

| Dataset | Rows | Canonical JSON SHA-256 |
| --- | ---: | --- |
| `Spec_Master.csv` | 21 | `eb1a4d639b30ddb4d7f805bc9452b6029de73727d2a98e56de5a9a7c6e1ff664` |
| `symbols_blocks.csv` | 8 | `1f529d76cec9188461e76c74acdbad6cf9b8bcd4f63f1660baf04d7adb0f75b2` |
| `lcd_icons_blocks.csv` | 2 | `2583f8ea569ae0da8ebb7244e7a2055208591e8243da2764ae0ec4aa8fdbff11` |
| `troubleshooting_blocks.csv` | 7 | `8ffd35844579eee9c7567f5e8eab481d4808d4b5f06bcdbceae3de89e8449006` |

The live spec Version field currently allows `1.0/1.1`; LCD and
Troubleshooting allow `V1.0`. The plan uses those dataset revisions while
preserving the authoritative `V2.0-2026-08-04` in the source asset record and
notes, and uses `2.0` in the build record. This avoids inventing global select
options or losing the published-source revision.

## Asset-package regeneration

The cached source AI was read-only and its SHA-256 rechecked before running the
committed recipe with the Python 3.12 project environment. The run produced:

| Output | Count / bytes | SHA-256 |
| --- | ---: | --- |
| archive pages | 10 | included in package |
| archive previews | 10 | included in package |
| semantic exports | 23 | recipe hashes all matched |
| `manifest.json` | 44,646 bytes | `3348250c8c128e55c2a611342a7445843093c95b861ecf4b6afa9be9a91618e4` |
| `artifacts.csv` | 11,145 bytes | `e85f632bcc139b565b16401e3541f62eebe228bb2cd000cf4b2cb967a7d5bcf5` |
| `asset-package.zip` | 6,284,798 bytes | `1b621720e2f29e7f9a8b2035b70c4b3d22ed9402d1c640e5d437b3b5faefc42c` |

The current recipe has **43** artifacts, not the earlier report's 42. The
difference is a latest-main regeneration fact: 10 pages + 10 previews + 23
semantic outputs. No expected hash was relaxed.

After an approved live write, source, manifest and package attachments must all
read back with non-empty file tokens and be downloaded for byte-level SHA-256
comparison. The 23 build-eligible export attachments require the same check.

## Latest-main build and IR acceptance

Commands used the project Python 3.12 environment:

```text
AUTO_MANUAL_PRESENTATION_PROFILE=web python build.py md \
  --config configs/config.bp-eu-en-web.yaml \
  --model JBP-3600A --region EU --lang en \
  --data-root tests/fixtures/phase2 \
  --staging-root <fresh temp root>

python -m sphinx -W -b html <package>/md <fresh sphinx root>
python -m unittest tests.test_jbp3600a_eu_en_web
```

| Gate | Result |
| --- | --- |
| Target suite | 7/7 passed |
| Real Pandoc build | passed |
| Sphinx `-W` | passed |
| Public IR projection | `whole-document-components/v1` |
| Source fragments | 15 |
| Internal IR blocks | 78 |
| Packaged assets | 21 |
| Cold replay | 15 fragments; `.rst` and `.csv` reads denied |
| Tamper rejection | changed packaged asset rejected |
| Finished-panel gate | 5/5 (`overview` 1, `operation` 2, `charging` 2) |

Latest-main artifact hashes:

| Artifact | SHA-256 |
| --- | --- |
| Generated Markdown | `38940fef9baf637f625b0cbc58773b445e88c5e14de3965c5796cff0d79f467d` |
| Public Manual IR file | `a38375c2a5f698ec9ee59a1c73fa748ed53c2c6c5db3146e7e1351e9afad5250` |
| IR content hash | `6c7be734c08d4a9ed8d93ad97a9b879b7b4cdb24bcdb339b971ac2ded5d7ea19` |
| IR bundle hash | `78b144f79fcc60c38d1bbc111c8acdfbbfe5da97643d40f892381719f1abf0a3` |
| Final Sphinx HTML | `a5b56653e22f356f4f645f1b1f00c63b575ee7cde644adec635c126ce8b57681` |

## Final Sphinx image URLs

All 21 final `<img>` URLs resolved to files in the Sphinx output. Browser load
checks also reported `complete=true` and `naturalWidth>0` for every URL.

```text
assets/ir/1c117a76679b04836c2996afe39b3784c47b32dec71a8213735a97178ed42024/jbp3600a_expansion_cable.png
assets/ir/1c272a00fbd28d6562d4126040ba43e5747f6a6550878c4b13e05a5c28014577/10_warning_triangle_RkOwbJ9j1oUHJgxFEx3cqhVynjb.png
assets/ir/422379347e71e7827c3da380e421f2cb106da5d2f74781fc45782a2f86d493d2/20_no_open_flame_SAbnbxa6iohb2rxxk3PcEh8cnuf.png
assets/ir/5501e619ed381e57f62aa570cc65a99b0c69148663a1d0eaf778edcfc701e3a7/clearance.png
assets/ir/55c449da0da26e4224e3f3d2ab9964180618a6179d1eb9d8d9c37351569f892f/stacking_locking.png
assets/ir/5a72ce9c7bb2cafb17bfdd02e349601bc9cdc0d0840ae0ae7faf5c6ad39bc972/overview.png
assets/ir/66c3df77e4f84cccad4b9f162798b181c007e89d3f0e9dd4fdf52c392827cbab/10_do_not_dismantle_Ml7EbCjtYohuKAxWNDUc93UMnVc.png
assets/ir/7fb57972ebd1fb8bf82abc75d0d320ecaa9abc6544020f2374da2f1272a46171/70_weee2_VL7tbeJhHoy9wBxRZIdcygPBnmf.png
assets/ir/8680d65769528354c36adf993c24d53dbe96c484bdc55c4ef3e66d22f0e34716/jbp3600a_user_manual.png
assets/ir/8872b0b8392c52b4bd9c655be1883cb0fbbeea226a7642b0ea7e456aee5ede26/jbp3600a_inbox_unit.png
assets/ir/99ebd2c47426a2d2d8929643534e65774afc717474b371def0d80a36a8f5cf61/lcd.png
assets/ir/c9faba9de405cb0960918841b7aef59fe8cdd7746e4715a2b56c02b43bc64a2b/lcd_control.png
assets/ir/cac2944fb3d3189b1b5e400031343461fc0e3dc7c178d85a2383bc006fb30f1a/power.png
assets/ir/d14506fa5a9d449039887db61a259f1841f1826de2f190f54063f96195b955f5/20_read_manual_VK1Ab1MGIoOHdgx1rkUchOHRntb.png
assets/ir/d20b1c0b5c927514f698b41d41e37d4e675bbb78ac0846994b636f6b031748d8/ac_charging.png
assets/ir/e345b3278827691751b6beac9c8343c75ac7a98100618fbef1db73a27329b99d/30_keep_away_from_children_Nc5NbV2kyoMaTSxvismcAlzbnlh.png
assets/ir/e4eb11ad06f6b91f8ec03b9a000370bd3ba67076036fea89dee9b37a80d15768/solar_charging.png
assets/ir/e7f30b293864bc56b9eef638a3f75afbf28e05b7c923ff15edff58ef195b45ac/jbp3600a_charging_indicator.png
assets/ir/ea7766d417e962cf711bccf3de79d6f639602848ace780353cb329329d13cc91/40_li_ion_ZEcHbhY0Eo3XOExtXKCcbEVjnpe.png
assets/ir/eb094578bf165fa39399de1d957cc71a92191f2b0e7ed0a620885065ebedf8a3/50_weee_L9o3bcXq0oSsqdxSX86covnpnle.png
assets/ir/f82efe218bc0b63cb953aced0c85f7c9553935e68d5cf70a3577df9212f550ce/lcd_map.png
```

## Responsive browser acceptance

| Viewport | Images | Broken | Page overflow | Inbox cards | Grid |
| --- | ---: | ---: | ---: | ---: | --- |
| 1440 × 900 | 21 | 0 | 0 px | 3 | `271.344px 271.344px 271.344px` |
| 375 × 812 | 21 | 0 | 0 px | 3 | `103.469px 103.469px 103.469px` |

The 375 px browser viewport had a 360 px document client width after the
scrollbar; document scroll width was also 360 px.

## Hello-Docs release readiness

Read-only GitHub verification found:

- `Hello-Docs/main` = `f6df757e601ef505446828118b2d3aa272822be6`.
- The config, manifest, illustration binding, recipe and intake-report blobs on
  mirror main are byte-identical to auto-manual `origin/main`.
- `FEISHU_BUILD_QUEUE_PAUSED=false`.
- `review/JBP-3600A-EU` does not exist.
- `Hello-Docs/publish` = `0c7dc292d711d4ab5d971316ca2654d97f6a270d`
  and contains no JBP-3600A frozen Web snapshot.
- No open `publish -> main` PR exists for this target. The latest settled Web
  Publish run is unrelated to JBP-3600A.

Therefore the target is executable only after the four approved live batches
and a coordinated Start Review seed. The main task must then run
`feishu-web-publish-queue.yml` for this target's exact build record, verify the
run settles, inspect that the generated PR changes only `docs/publish/**`, merge
only with separate authorization, verify the formal page at
`https://ht-doc.readthedocs.io/manual_jbp3600a_eu.html`, and read the same URL
back from the build record. The expected URL is not yet a verified publication.

## Checklist

- [x] Latest engineering main and clean task branch verified.
- [x] Current PDF, source-list record, source AI size and hashes locked.
- [x] Live product/project/Document_key/source/asset/build queries repeated.
- [x] Exact additive source and asset increment prepared with readback gates.
- [x] Latest-main build, Sphinx, cold replay and tamper rejection passed.
- [x] All 21 final image URLs map to files and load in a browser.
- [x] 1440 px and 375 px broken-image/overflow checks passed.
- [x] Mirror code equivalence, queue pause state, review branch and publish tree checked.
- [ ] Approve and execute reference/master/source rows (batches 1-2), then read back.
- [ ] Approve and execute new-asset rows/attachments (batch 3), then read back tokens and hashes.
- [ ] Approve dormant build-record creation (batch 4), then read back with trigger empty.
- [ ] Main task coordinates Start Review and Web Publish order.
- [ ] Generated `docs/publish/**`-only PR reviewed and separately authorized for merge.
- [ ] Formal RTD page passes the same 21-image and responsive checks.
- [ ] Build-record `HTML_link`/`RTD_link` readback equals the verified formal URL.
