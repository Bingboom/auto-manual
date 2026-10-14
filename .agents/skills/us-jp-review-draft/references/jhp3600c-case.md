# Case: JHP-3600C (HomePower 3600 Pro Max) JP review draft, 2026-10

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

The example scripts take the previous version's directory and are tied to that
draft's markup; reuse their patterns (helpers, replacement assertions, Chinese
gloss patching), not their hard-coded strings.
