# Case: JHP-3600C (US: HomePower 3600 Pro Max; JP: Jackery HomePower 3600 Plus Max) JP review draft, 2026-10

Source: `https://ht-docs-ht-manuals.readthedocs-hosted.com/en/latest/JHP-3600C/US/en/md/manual_jhp3600c_us_en.html`.
Draft in Feishu wiki space 便携资料开发工作台 (`7649591386208717774`): original
`JHP-3600C-JP-English-Draft.zip` (v0.14), v0.19 uploaded alongside.

| Version | Operator instruction | What changed | Script |
| --- | --- | --- | --- |
| v0.15 | JP spec sheet screenshots, product positioning | spec table regrouped and filled; ports from JE-5000A JP wording; EPO removed; box confirmed; USB-C 100W, UPS bypass 1500W, 5 battery packs, DC8020×2/1200W | `examples/jhp3600c/make_v015.py` |
| v0.16 | 加，写成英语的 (add connections, in English); RTD JP manuals have no 并机口 term → English | English CONNECTIONS chapter (cascade, ATS, MTS + 3.6kW caution); English port labels | `make_v016.py` |
| v0.17 | 有日文的要替换成日文; 日文黑色、缺语料英文绿色、中文蓝色小字; 现有日规 web 手册也可以作为语料 | corpus replacements in the chapter; color contract; LCD new-icon descriptions; translation count 56 units / 601 words | `make_v017.py` |
| v0.18 | 样式按现有日规说明书风格 | JE-1000F JP styling; 絵表示の説明 moved into safety; 認証 label reused; alignment audit (571 applicable US units) | `make_v018.py` |
| v0.19 | 200V 充电和 UPS 小节加上，附录先不加 | UPS "WITH 200V AC INPUT", "CHARGING VIA 200V AC INPUT" (outlet + ATS); 77 units / 879 words; coverage 62.2% full, 79.9% incl. partial | `make_v019.py` |

Open items handed to the operator at v0.19: JP product name and nameplate model,
200V input cable (20A fast-charge vs 30A parallel/fast-charge), 200V charging
power, per-port bypass limits, whether ATS is sold in Japan, weight 32 vs 33.5 kg,
inverter 3.6 kW vs 4000 W rating, US annexes (AC ESS, BP3600 spec, ATS spec)
deferred.

## v0.20 → v0.69 (2026-10-13 … 10-21)

| Versions | Operator instruction / input | What changed |
| --- | --- | --- |
| v0.20–v0.27 | A0 spec sheet (HTE1573600A-JP-JAK, 2026-10-10); 安全章照搬 JE-1000F; product name | every spec-sheet value purple with source (`jp-spec-updated`/`jp-spec-filled`); safety chapter copied from JE-1000F JP with this model's values; full name + 「（以下「本製品」）」, elsewhere 「本製品」 (amber); NEMA …R names |
| v0.28–v0.36 | 美规为准 | operations, UPS, connections and charging reordered and restyled to the US manual (pills, prerequisite boxes); template sentences that contradict the US removed; STORAGE removed |
| v0.37 | LCD wording | 点灯時／点滅時／消灯時 throughout (JPD-01) |
| v0.38–v0.50 | layout and names | LCD panel, US footnotes ①–④, App layout, right-side view redrawn from the A0 line art, EPO removed (struck in A0), port names 「AC出力ポート (NEMA …)」 |
| v0.51 | 把稿内英文全部译为日文并保持原颜色 | all 107 green units translated into a first-pass Japanese draft, still green; US English kept in `data-previous-english`; list gains a Japanese column |
| v0.52–v0.53 | spec table in US structure | rows the US and other JP manuals lack removed; input/output groups follow the US table |
| v0.54–v0.57 | screenshots from the operator | LCD ㉗ 点灯時／消灯時; App sentence position; 省エネモード panel and 50Hz/60Hz section restored from JE-1000F |
| v0.58–v0.62 | R&D answers (研发答复 2026-10-20) | bypass limits per port and input voltage, cascade total 6000W, switching 10ms single / 20ms parallel; all magenta 【要確認】 resolved; an inferred "MTS 最大4000W" removed again |
| v0.63–v0.66 | corpus reuse and MTS wording | JE-5000A L14-30R sentence restored; UPS sentences split into new + corpus halves; 「手動切替スイッチ（MTS）」 heading; 「市販の」 (Jackery does not sell MTS); 電気工事士 caution |
| v0.67–v0.69 | sibling JP wording | AC input row 「パススルー①」 without 「充電モード」; DC8020 labels 「シガーソケット: 」「PV: 」; first product-name reference moved to 「使用上のご注意」 |

State at v0.69: 108 units / 1507 words (unique 1498) / 8978 chars, no pending
parameters. Open: 50Hz/60Hz figure to redraw from this unit's LCD, native
review of all green Japanese, the remaining R&D questions in the appendix.

## Example scripts

| Script | Pattern |
| --- | --- |
| `make_v015.py` … `make_v019.py` | spec fill, connections chapter, color/count, restyle, 200V sections (English-green era) |
| `make_v061.py` | R&D answer into a sentence as purple values (`PU()` helper) and the matching review note |
| `make_v064.py` | split a unit into new + corpus halves; heading insert; recount with `--previous`; appendix tables regenerated |
| `make_v066.py` | JP-only caution as a callout table with a `jp-draft-insert` sentence (not counted) |
| `make_v067.py` | spec row rewritten to the sibling JP wording; two term units leave the list; recount |
| `make_v069.py` | move the product-name reference and update every reference tooltip |

The example scripts take the previous version's directory and are tied to that
draft's markup; reuse their patterns (helpers, exact-count replacement
assertions, version-string bump, Chinese gloss patching), not their hard-coded
strings. `make_v064.py` and `make_v067.py` rebuild the shipped v0.64 and v0.67
byte for byte from v0.63 / v0.66 with `scripts/count_translation.py --previous`.
