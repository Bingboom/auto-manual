"""Write the JE-300D JP Japanese semantic document from the reviewed transcription.

Run from the repository root:
``python3 manual_sources/JE-300D/JP/ja/git-20261103-6ab11ee9/source/intake.py``.
It writes ``source/ja/content.json``. ``original.pdf`` is outlined (no text
layer), so every Japanese line below is transcribed from 300 dpi renders (450-1200
dpi clips for small or ambiguous glyphs) of the named physical page and kept as
printed. Every printed block maps to a shared component or plain shared flow
(``source_manifest.json:component_map``); no package class, inline style or plain
table. The cover (p1), the paper table of contents (p2) and the QR-only back
cover (p21) are not Web content.
"""
from pathlib import Path
import json
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kit import P, UL, Book, blocks, cell_pair, inbox_carrier, pair, spec_carrier  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.lcd_mode import lcd_mode_component_spec  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
    troubleshooting_component_spec,
)
from tools.component_specs.reference_table import reference_table_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import warranty_section_component_spec  # noqa: E402
from tools.web.frozen_ai_flow import node  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
DC = "⎓"  # the print's DC symbol
PANEL = {"html": {"attributes": {"class": "hb-text-panel"}}}  # shared grey text panel (web_manual.css)


def panel(*children) -> dict:
    """A printed grey text panel: shared ``hb-text-panel`` group (JE-1000D JP V2 precedent)."""
    return node("group", list(children), role="container", presentation=PANEL)


def make() -> list[str]:
    b = Book(SOURCE, "JE-300D", "JP", "ja", "Jackery ポータブル電源 300D · JE-300D")
    load = lambda name: json.loads((SOURCE / "source" / name).read_text())  # noqa: E731
    W, C = "warning", "caution"

    # ---- p3-5 安全上のご注意 --------------------------------------------------------
    b.chapter("safety", "安全上のご注意", [3, 4, 5])
    b.add(P("**ご使用の前にこの「安全上のご注意」をよくお読みのうえ、正しくお使いください。**"))
    b.h("絵表示について")
    b.add(P("製品を安全に正しくお使いいただき、お客様や他の方々への危害や財産への損害を未然に防止するための表示です。\n"
            "内容をよく理解してから本文をお読みください。"))
    b.comp(symbol_signal_component_spec, accessibility_label="絵表示について",
           headers=[pair("表示", "content"), pair("意味", "content")],
           rows=[{"label": label, "show_icon": True, **pair(meaning, "meaning")} for label, meaning in [
               ("警告", "この表示を無視して、誤った取り扱いをすると、人が死亡または重傷を負う可能性が想定される内容を示し"
                        "ています。"),
               ("ご注意", "この表示を無視して、誤った取り扱いをすると、人が傷害を負う可能性が想定される内容または物的損害の"
                          "発生が想定される内容を示しています。"),
               ("説明", "この表示を無視して誤った取り扱いをすると、機器の損傷、データの消失、性能の低下、または予期しない動作"
                        "が発生する可能性があることを示しています。"),
               ("ヒント", "文章内の重要な情報や操作のヒントを補足する内容を示しています。"),
           ]])
    b.h("絵表示の説明")
    symbols = load("symbols.json")
    panels = [[], []]
    for index, row in enumerate(symbols):
        meaning = pair(row["meaning"], "meaning")
        panels[0 if row["glyph_search_box"][0] < 100 else 1].append(
            {"asset_index": index, "icon_alt": meaning["meaning_text"], **meaning})
    b.comp(symbol_icon_component_spec, accessibility_label="絵表示の説明",
           headers=[pair(v, "content") for v in ("記号", "意味", "記号", "意味")],
           panels=panels, icon_refs=[r["local_path"] for r in symbols])
    # p4 first 警告 grid (left column, then right column)
    for title, body in [
        ("火のそばや炎天下の車内、熱器具の周辺など高温（45°C以上）になる場所で使用したり、放置しない",
         "発熱や発火、破裂する原因になります。"),
        ("強い衝撃を与えたり、投げつけたりしない", "発熱や発火、破裂する原因になります。"),
        ("各接続端子には確実に差し込む", "差し込みが不十分だと、発熱したりほこりが付着して火災や感電の原因になります。"),
        ("端子部にケーブル以外の金属類を差し込まない", "発熱や発火の原因になります。"),
        ("雷が鳴りだしたら、電源プラグにふれない (充電をしない)", "感電の原因になります。"),
        ("水など、液体を入れたり、濡らしたりしない", "発熱や発火の原因になります。"),
        ("濡れた手で本体や接続するケーブルを触らない", "火災や感電の原因になります。"),
    ]:
        b.callout("警告", f"**{title}**", body, variant=W)
    # p4 second 警告 grid
    b.callout("警告", "万が一、次のような異常が発生したときはすぐに使用をやめる",
              UL("煙が出ている、異臭がする", "落としたり、破損したとき", "異音がする",
                 "内部に水や異物が入ったとき", "電源コードが傷んだとき"),
              "このような異常が発生したまま使用していると、火災や感電の原因になります。\n"
              "すぐにアダプターをコンセントから抜いてください。また、本製品に接続されている機器もすべて外してください。",
              "**万が一発煙や発火したら、大量の水で消火して煙が見えなくなるまで本製品を水浸しにしてください。**",
              "煙が出なくなることを確認してからカスタマーサポートにご連絡ください。\n"
              "お客様による修理は危険ですので絶対におやめください。", variant=W)
    b.callout("警告", "**分解、改造しない**", "故障、発熱、火災·感電の原因になります。", variant=W)
    b.callout("警告", "**表示された電源電圧以外で使用しない**",
              "故障、発熱、火災·感電の原因になります。また、本製品を使用できるのは日本国内のみです。", variant=W)
    b.callout("警告", "**付属品と本製品が破損した場合は、ご自身で修理をしない**", variant=W)
    # p5 注意 grid
    b.callout("注意", "**本製品の上に物を載せたり、不安定な場所に置かない**", "倒れたり、落ちたりしてけがの原因になります。",
              variant=C)
    b.callout("注意", "**データサーバや医療機器など、非常時に不具合が起こると人命 / 財産に重大な危険を及ぼしうる用途での"
                     "ご使用はお控えください。次のようなような機器では、万が一使用中に給電ができなくなった場合、人命 / 財産に"
                     "かかわる被害が想定されます。**",
              UL("医療機器や使用上、生命に関わるような機器", "社会的、公共的に重要な機器など", "重要な事業用機器など"),
              variant=C)
    b.callout("注意", "**心臓にペースメーカーを装着している方は使用しない**", "ペースメーカーが、本製品の影響を受ける恐れがあります。",
              variant=C)

    # ---- p5-6 使用上のご注意 --------------------------------------------------------
    b.chapter("usage_precautions", "使用上のご注意", [5, 6])
    b.h("給電に関する注意事項")
    b.add(P("出力上限値を超える電化製品は使用しないでください。"),
          UL("特に、始動電力が公称電力の 3~7 倍になる誘導負荷（ポンプ、ヒーター、掃除機、冷蔵庫、エアコン、電気丸ノコなどの"
             "電動道具、洗濯機、電子レンジなど）の使用にはご注意ください。",
             "接続機器の消費電力が本製品の出力範囲内であることをご確認の上、出力ボタンを押してください。",
             "給電中、機器の制御や環境により、急速充電にならない・給電できない場合があります。",
             "充電または給電中、ラジオ・チューナー・テレビなどに雑音が入る場合があります。その際は、それらの機器から離して"
             "ご使用ください。"))
    b.h("使用環境について")
    b.add(UL("本製品は防塵・防水仕様ではありません。ほこり、水、海水などがかからないようご注意ください。",
             "ほこりの多い場所や高温多湿の場所での充電・使用・放置は避けてください。",
             "平坦で安定した場所に設置し、不安定な場所に置かないでください。",
             "本製品の通風孔は、安全上絶対にふさがないでください。各面から 5cm 以上スペースを確保してください。",
             "充電・給電中は本体が温かくなります。周囲に物を置かないでください。"))
    b.h("接続時の注意事項")                                                              # p6
    b.add(UL("ケーブルを接続する際は、まっすぐに差し込んでください。",
             "抜く際は必ずプラグ部分を持って抜いてください。ケーブルを引っ張ったり折り曲げたりしないでください。"))
    b.h("お手入れについて")
    b.add(UL("本体が汚れた場合は、電源プラグを抜いた状態で、柔らかい布で乾拭きしてください。",
             "汚れがひどい場合は、水または薄めた中性洗剤で拭き取ってください。",
             "シンナーやベンジンなどの使用は絶対に使わないでください。"))
    b.h("入出力・温度・表示に関するご注意")
    b.add(node("list", [
        node("list_item", [P("接続機器の入力が本製品の出力上限を超えている場合、自動で電源が遮断されます。")]),
        node("list_item", [P("本機は -15°C~45°C の温度範囲でお使いの機器に電力供給が可能となり、本機の蓄電は 0°C~45°C で行えます。"),
                           P("動作温度が上記範囲外にある場合、本製品が温度異常マークが表示され、動作しない可能性があります。"),
                           P("温度異常マークが表示された場合は、本製品を 2 時間以上、動作温度範囲内の環境に置いてください。")]),
        node("list_item", [P("容量表示は参考値であり、電圧により表示数値と実際の容量に差異が出る場合があります。")]),
    ], ordered=False))

    # ---- p6 免責事項 ---------------------------------------------------------------
    b.chapter("disclaimer", "免責事項", [6])
    b.add(panel(UL(
        "火災、地震、第三者による行為、その他の事故、お客様の故意または過失誤用・誤動作・その他の異常な条件下での使用により"
        "生じた損害に関して、当社は一切責任を負いません。",
        "付属品と本製品が破損した場合は、ご自身で修理を行わないでください。ご自身で分解・修理したことにより生じた損害に関し、"
        "当社は一切責任を負いません。",
        "保証範囲は利用規約に適用され、記載されていない内容は当社の保証範囲外となります。",
        "取扱説明書の記載事項が遵守されないことにより生じた不適合について当社は責任を負いかねます。",
        "本製品の使用、または使用不能から発生する付随的な損害 ( 事業利益損失含む )、当社が関与しない接続機器との組み合わせに"
        "よる誤動作などから生じた損害に関して、当社は一切の責任を負いません。")))

    # ---- p7 同梱品 -----------------------------------------------------------------
    b.chapter("in_the_box", "同梱品", [7])
    slots = ("inbox-unit", "inbox-shoulder-belt", "inbox-user-manual")
    cards = [{"image_ref": b.figures[slot]["local_path"], "label": b.figures[slot]["caption"],
              "alt": b.figures[slot]["caption"]} for slot in slots]
    b.used_figures += list(slots)
    b.comp(inbox_component_spec, inbox_carrier, accessibility_label="同梱品", cards=cards,
           tip_label="", tip_body="", require_tip=False)
    b.add(panel(P("※ 付属品を故障、紛失等してしまった場合はカスタマーサポートまでご連絡ください。\n"
                  "※ 本充電ケーブルユニットは、同梱されている電気機器以外には使用しないでください。\n"
                  "※ シガーソケット充電ケーブルは別売りです。Jackery公式サイトよりご購入いただけます。\n"
                  "サポートが必要な場合は、Jackeryカスタマーサポートまでお問い合わせください。")),
          P("**■本機の仕様および外観は、改善のため予告なく変更することがあります。**"))

    # ---- p8 各部の名称 -------------------------------------------------------------
    b.chapter("product_overview", "各部の名称", [8])
    b.h("製品の外観")
    b.figure("overview-front")
    b.add(P("※本製品にはACポートは搭載されていません。"),
          P("*リングはショルダーストラップにも使用できます。"))
    b.figure("shoulder-strap")

    # ---- p9 液晶画面 ---------------------------------------------------------------
    b.chapter("lcd_display", "液晶画面", [9])
    b.figure("lcd-display")
    glyphs = load("glyphs.json")
    names = [
        ("①", "入力電力表示", "入力電力をワットで表示します。"),
        ("②", "USB-C充電インジケーター", "本製品はUSB-C1ポート経由で充電されます。"),
        ("③", "シガーソケット入力電力表示", "製品は、DC 12V（カーチャージ）を使用し、8020入力ポートを介して充電されています。"),
        ("④", "ソーラー(グリーンエネルギー)充電接続", "製品は、ソーラーパネルを使用し、8020入力ポートを介して充電されています。"),
        ("⑤", "バッテリーレベルパーセントタグ", "製品の充電中は、バッテリーのパーセンテージを囲むオレンジ色の円が順番に点灯し"
         "ます。他のデバイスの充電時には、オレンジ色の円は点灯したままになります。"),
        ("⑥", "バッテリーレベルパーセントタグ", "バッテリー残量を表示します。"),
        ("⑦", "省エネモード", "オン：省エネモードが有効になります。\nオフ：省エネモードが無効になります"),
        ("⑧", "高温インジケーター", "高温保護が作動しました。製品の温度が通常の動作範囲に戻るまで、製品の機能が停止する場合が"
         "あります。"),
        ("⑧", "低温インジケーター", "低温保護が作動しました。製品の温度が通常の動作範囲に戻るまで、製品の機能が停止する場合が"
         "あります。"),
        ("⑨", "エラーコード", "製品エラーが発生しました。詳細については、トラブルシューティングのセクションを参照してください。"),
        ("⑩", "消費電力", "出力電力をワットで表示します。"),
    ]
    rows = [{**pair(number, "number"), **pair(name, "name"), **pair(description, "description"),
             "icon_alt": name, "asset_index": index}
            for index, (number, name, description) in enumerate(names)]
    b.comp(lcd_icon_component_spec, accessibility_label="液晶画面", rows=rows,
           icon_refs=[g["local_path"] for g in glyphs], icon_locale_policy="exact")

    # ---- p10-13 使い方 -------------------------------------------------------------
    b.chapter("operations", "使い方", [10, 11, 12, 13])
    b.h("主電源ボタン/オフ")
    b.figure("power-on-off")
    b.add(P("本製品は、バッテリーが完全に消耗した場合、自動的に電源が切れる仕様となっております。"))
    b.h("USB出力オン/オフ")
    b.add(P("本製品の電源を入れると、USBポートが自動的に有効となり、接続した機器の充電が可能になります。"))
    b.figure("usb-output")
    b.callout("ご注意", UL(
        "USB-C1およびUSB-C2は、USB-PD Power Source 3 (PS3) の高出力ポートです。接続されたユーザーデバイスまたはアクセサリーが"
        "安全基準を満たしていない場合、火災の危険性があります。これらのポートを使用する前に、接続するデバイスまたはアクセサリーに"
        "耐火安全保護が備わっていることを確認してください。",
        "Jackery ポータブル電源 300Dは、IEC/EN/UL 62368-1（または同等の規格）の6.3、6.4、6.5条に準拠したデバイスまたは"
        "アクセサリーのみに接続してください。",
        "最大出力を得るためには、公式のJackery USB-C to USB-C 5Aケーブル（20V DC/5A、100W；28V DC/5A、140W）を使用して"
        "ください。"), variant=C)
    b.h("カーポート出力オン/オフ")                                                      # p11
    b.add(P("**前提：**主電源ボタンがオンになっていることを確認してください。"))
    b.figure("dc-output")
    b.add(P("本製品は、別売のJackery 12V 自動車用バッテリー充電ケーブルを使用することで、車のバッテリーへの充電が可能です。"),
          P("※Jackery 12V 自動車用バッテリー充電ケーブルは付属しておりません。Jackery公式サイトよりお求めいただけます。"))
    b.callout("ご注意", UL(
        "12V車専用であり、24V車には対応しておりません。",
        "本製品の12V DC出力（シガーソケット）から車のバッテリーへ充電中は、エンジンを始動しないでください。製品の故障につながる"
        "恐れがあります。",
        "この機能はあくまで車のバッテリーの緊急補助用であり、深刻なバッテリー上がりや故障したバッテリーには対応しておりません。"),
        variant=C)
    b.h("省エネモード")                                                                  # p12
    b.add(P("省エネモードは、出力ボタンの消し忘れによる無駄なバッテリー消耗を防ぐための機能で、初期設定ではオン（画面に省エネアイコン"
            "「6H」表示）になっています。\n"
            "この状態では、DC 12V/USB 出力が2W以下のまま6時間経過すると、本製品はすべての出力を自動でオフにした後、電源もオフに"
            "なります。"),
          P("※低消費電力機器（DC/USB接続時は2W以下）をご使用の場合、途中で出力が自動オフにならないよう、省エネモードをオフにして"
            "ください。\n"
            "省エネモードをオフにすると、画面上の「6H」アイコンは表示されなくなります。"))
    b.figure("energy-saving")
    b.callout("説明", "省エネモードは電源投入後に前回の状態を維持します。モード変更には手動での切り替えが必要です。", variant="note")
    b.h("LEDライトオン/オフ")
    b.add(P("LEDライトには、照明モードとSOSモードの2つのモードがあります。いずれのモードでも、LEDスイッチを長押しすることで"
            "LEDライトを消灯できます。"))
    b.figure("led-light")
    b.h("LCDスクリーン オン/オフ")                                                      # p13
    b.used_figures.append("lcd-screen")
    groups = [{**pair(state, "state"), "actions": [{**pair(a, "action"), **pair(d, "description")} for a, d in acts]}
              for state, acts in [
        ("画面は2分間点灯し続けます", [("オンにする", "主電源ボタンを押すか、充電入力がある場合。"),
                                       ("オフにする", "主電源ボタンを押します。"),
                                       ("自動オフ", "2分後にLCDは自動的に消灯し、スリープモードになります。")]),
        ("常時点灯表示モード", [("オンにする", "LCD画面がオンのときに主電源ボタンを2回押します。"),
                                ("オフにする", "主電源ボタンを押します。"),
                                ("自動オフ", "常時点灯ディスプレイモードは、2時間操作がないと自動的に消灯します。")]),
    ]]
    b.comp(lcd_mode_component_spec, accessibility_label="LCDスクリーン オン/オフ", groups=groups,
           artwork_ref=b.figures["lcd-screen"]["local_path"], artwork_locale_policy="exact")

    # ---- p13-15 充電方法 -----------------------------------------------------------
    b.chapter("charging", "充電方法", [13, 14, 15])
    b.add(P("**グリーンエネルギー優先モード**\n"
            "本製品はグリーンエネルギー優先モードを搭載していますが、ソーラーパネルとUSB-C充電ケーブルを使って同時に充電できます。"
            "同時に充電すると、ソーラーが優先されますが、バッテリーの最大許容電力で同時に充電されます。"))
    b.callout("ご注意", UL(
        "製品の充電動作温度範囲は-0°C~45°C、放電動作温度範囲は-15°C~45°Cです。上限・下限温度を超えた場合、充放電が制限され、"
        "または充放電不可の可能性があります。",
        "温度によって、製品の充電効率と実際の容量は異なります。"), variant=C)
    b.callout("ご注意", UL(
        "はじめてお使いになるときは、本製品をフル充電してからご使用ください。",
        "充電池は空の状態で長期保管(3カ月~6カ月）すると、性能が劣化したり、充電できなくなる場合があります。",
        "長期保管中は、電池残量が0%にならないよう、3か月に一度の充電をおすすめします。"), variant=C)
    b.h("USB-C充電ケーブル（最大140W）")                                                # p14
    b.add(P("USB-Cケーブルとしても使える2-in-1キャリーハンドルを取り外してください。製品のUSB-C1ポートと電源コンセントに接続して"
            "ください。"))
    b.figure("charging-usbc")
    b.callout("ご注意", "USB-Cポートから充電する場合、本製品は最大140Wに対応しています。そのためには、140Wに対応したPD充電器と"
              "ケーブルの両方が必要です。", variant=C)
    b.h("ソーラー充電（最大100W）")
    b.add(P("ソーラーパネル接続用のDC入力ポート（8020メス）×1を備え、最大1枚のパネル（最大入力電力100W）まで接続可能です。\n"
            "※ Jackery SolarSaga アダプターを使って2枚接続はできません（電圧が許容範囲を超え、故障のリスクがあります）。"),
          P("直接接続可能です。追加のアクセサリーは不要です。\n"
            "本製品のDC入力ポートは「8020メス」です。ソーラーパネル側の「8020オス」と接続してください。"))
    b.figure("charging-solar")
    b.add(P("Jackeryブランド以外の付属品を使用して充電しないでください。特に、ソーラーパネルで充電する際は、Jackeryのソーラー"
            "パネルを使用することをお勧めします。ソーラーパネルの開放電圧（V_{oc}）が、Jackery ポータブル電源 300DのDC入力電圧"
            "範囲（16V〜28V）内に収まっていることを確認してください。他社ソーラーパネルで充電することによる損失について、当社は"
            "一切の責任を負いません。"))
    b.h("シガーソケット充電（最大96W）")                                                # p15
    b.add(P("■本製品は、12V/10A出力の車載シガーソケットからの充電に対応しています。"),
          P("ご使用の際は、以下にご注意ください："),
          UL("必ず車のエンジンを始動させてから接続してください。エンジン停止状態で使用すると、車両のバッテリーが上がる恐れが"
             "あります。",
             "車の充電ポートとシガーソケット充電ケーブルの接触状態をご確認ください。",
             "ケーブルが確実に奥まで差し込まれていることをご確認ください。"))
    b.figure("charging-car")
    b.add(P("※ シガーソケット充電ケーブルは別売りです。"))
    b.callout("ご注意", UL(
        "悪路などで車両の振動が激しい場合は、接触不良や発熱·焼損の恐れがあるため、充電を中止してください。",
        "誤使用による故障·損傷については、弊社では責任を負いかねます。あらかじめご了承ください。",
        "シガーソケット充電は 12V, 10A 車専用で、24V 車は充電できません。人身傷害や物的損害を避けるため、本製品の充電に 24V 車を"
        "使用しないでください。"), variant=C)

    # ---- p16 トラブルシューティング ------------------------------------------------
    b.chapter("troubleshooting", "トラブルシューティング", [16])
    b.add(P("次のいずれかのエラーコードが表示された場合は、記載されている対処方法に従って問題を解決してください。問題が解決しない"
            "場合は、Jackeryカスタマーサポートまでご連絡ください。"))
    restart = "製品を再起動してください。"
    dealer = "販売店またはJackeryカスタマーサポートにお問い合わせください。"
    rows = [{**pair(code, "code"), **pair(measures, "measures")} for code, measures in [
        ("F0", restart), ("F1", dealer), ("F2", dealer), ("F3", restart),
        ("F4", "製品に負荷を接続してバッテリーを放電し、エラーが消えるまで続けてください。"),
        ("F5", "ソーラーパネルまたはUSB-C電源コンセントを使用して、エラーが消えるまで製品を充電してください。"),
        ("F6", dealer),
        ("F7", "1. 製品からすべてのDC入力を取り外してください。\n"
               "2. ソーラーパネルで充電する場合は、接続されたソーラーパネルの開放電圧（V_{oc}）を確認してください。本製品の最大DC入力"
               "電圧は28Vです。\n"
               "3. 製品を再起動し、アイドル状態を保ってください。エラーが消えるまで待ってください。"),
        ("F8", dealer),
        ("F9", "製品のDC 12V/USBポートに接続されている負荷を取り外してください。故障が消えるまで待機してください。"),
    ]]
    b.comp(troubleshooting_component_spec, headers=[pair("エラーコード", "content"), pair("対処方法", "content")], rows=rows)

    # ---- p17-18 主な仕様 -----------------------------------------------------------
    b.chapter("specifications", "主な仕様", [17, 18])
    c12 = f"最大140W, 5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}5A, 28V{DC}5A"
    for title, rows in [
        ("基本情報", [("製品の名称", "Jackery ポータブル電源 300D"), ("型番", "JE-300D"),
                      ("バッテリータイプ", "LiFePO₄ （リン酸鉄リチウムイオン電池）"),
                      ("定格容量", "15Ah / 19.2V DC (288 Wh)"),
                      ("サイクル寿命", "4,000回の充放電後も容量の70%以上を維持"),
                      ("サイズ＆重量", "約118.6×120.2×183 mm(約2.5 kg）")]),
        ("入力ポート", [("1×USB-C入力ポート", f"C1: 5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}5A, 28V{DC}5A, 最大140W"),
                        ("1×DC8020入力ポート", f"PV: 16V-28V{DC}6A，最大100W"),
                        ("", f"ｼｶﾞｰｿｹｯﾄ: 11V-16V{DC}6A，最大96W")]),
        ("出力ポート", [("3×USB-C出力", "C1: " + c12), ("", "C2: " + c12),
                        ("", f"C3: 最大65W, 5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}3.25A"),
                        ("1×USB-A出力", f"最大15W, 5V{DC}3A"), ("シガーソケット出力", f"12V{DC}電流制限10A")]),
        ("温度範囲", [("充電温度", "0°C~45°C"), ("動作温度", "-15°C~45°C"),
                      ("保存温度", "1ヶ月 -20°C~45°C; 3ヶ月 0°C~45°C; 1年 0°C~25°C")]),
    ]:
        b.comp(spec_table_component_spec, spec_carrier, section_title=title, rows=rows)
    b.h("マルチポート出力の組み合わせ")
    cig = "シガーソケット出力ポート"
    for title, first, rows in [
        ("1ポート出力", "使用ポート", [("USB-C1", "140W"), ("USB-C2", "140W"), ("USB-C3", "65W"), ("USB-A", "15W"),
                                        (cig, "120W")]),
        ("2ポート出力", "組み合わせ", [
            ("USB-C1 + USB-C2", "140W + 140W"), ("USB-C1 + USB-C3", "140W + 65W"), ("USB-C1 + USB-A", "140W + 15W"),
            (f"USB-C1 + {cig}", "140W + 120W"), ("USB-C2 + USB-C3", "140W + 65W"), ("USB-C2 + USB-A", "140W + 15W"),
            (f"USB-C2 + {cig}", "140W + 120W"), ("USB-C3 + USB-A", "65W + 15W"), (f"USB-C3 + {cig}", "65W + 120W"),
            (f"USB-A + {cig}", "15W + 120W")]),
        ("3ポート出力", "組み合わせ", [
            ("USB-C1 + USB-C2 + USB-C3", "140W + 140W + 65W"), ("USB-C1 + USB-C2 + USB-A", "140W + 140W + 15W"),
            (f"USB-C1 + USB-C2 + {cig}", "100W + 100W + 120W"), ("USB-C1 + USB-C3 + USB-A", "140W + 65W + 15W"),
            (f"USB-C1 + USB-C3 + {cig}", "140W + 65W + 120W"), (f"USB-C1 + USB-A + {cig}", "140W + 15W + 120W"),
            ("USB-C2 + USB-C3 + USB-A", "140W + 65W + 15W"), (f"USB-C2 + USB-C3 + {cig}", "140W + 65W + 120W"),
            (f"USB-C2 + USB-A + {cig}", "140W + 15W + 120W"), (f"USB-C3 + USB-A + {cig}", "65W + 15W + 120W")]),
        ("4ポート出力", "組み合わせ", [
            ("USB-C1 + USB-C2 + USB-C3 + USB-A", "140W + 65W + 65W + 15W"),
            (f"USB-C1 + USB-C2 + USB-C3 + {cig}", "100W + 65W + 30W + 120W"),
            (f"USB-C1 + USB-C2 + USB-A + {cig}", "100W + 65W + 15W + 120W"),
            (f"USB-C1 + USB-C3 + USB-A + {cig}", "100W + 65W + 15W + 120W"),
            (f"USB-C2 + USB-C3 + USB-A + {cig}", "100W + 65W + 15W + 120W")]),
        ("5ポート出力", "全てのポートがアクティブ", [
            (f"USB-C1 + USB-C2 + USB-C3 + USB-A + {cig}", "65W + 65W + 30W + 15W + 120W")]),
    ]:
        b.h(title, level=4)
        b.comp(reference_table_component_spec, variant="lcd-actions-compact", label=title,
               headers=[cell_pair(first), cell_pair("最大出力")],
               rows=[[cell_pair(a), cell_pair(v)] for a, v in rows])
        if title == "1ポート出力":
            b.add(P("* 組み合わせによっては、メインポートの優先順位によりUSB-C1/2/3の出力が制限される場合があります。"))
    b.add(P("※USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."),       # p18
          P("デバイスが高出力ポートに接続されると、製品の温度保護機構により出力電力が自動調整される場合があります。 これは正常動作で"
            "あり、故障を示すものではありません。 心配には及びません。"))

    # ---- p19-20 保証について -------------------------------------------------------
    b.chapter("warranty", "保証について", [19, 20])
    b.add(panel(P("このたびは Jackery 製品をご購入いただき、誠にありがとうございます。\n"
                  "本保証書は、Jackery ポータブル電源製品に関する保証内容を明確にご案内するものです。\n"
                  "ご使用前に必ずご確認のうえ、大切に保管してください。")))
    sections = [
        ("保証期間", blocks(
            "1. 保証期間はご購入日から 3 年間です。\n"
            "2. また、延長保証にご登録いただくと、さらに 2 年間の保証が追加されます。詳しくは Jackery 公式サイトをご確認ください。",
            "※ Jackery 公式オンラインストアまたは正規代理店以外での購入品は保証対象外となります。")),
        ("保証の適用範囲", blocks(
            "1. 購入チャネルについて\n本保証は、Jackery公式オンラインストアまたは正規代理店で購入された製品に限り有効です。",
            "2. 保証提供地域\n保証は、日本国内に在住の方が、日本国内で使用する場合に限り有効です。")),
        ("保証の適用条件", blocks(
            "以下のすべての条件を満たす場合に、保証の適用対象となります：\n"
            "・Jackery公式オンラインストアまたは正規代理店にてご購入されたこと\n"
            "・保証期間内であること\n"
            "・下記の「保証対象外」に該当しないこと")),
        ("保証対象外となる場合", blocks(
            "以下のいずれかに該当する場合、保証期間内であっても保証の対象外となります：\n"
            "1.故障・損傷が保証期間内に発生していても、保証期間終了後に申請された場合\n"
            "2.使用上の誤り（取扱説明書や本体ラベルに記載の注意事項に従わなかった使用）による故障・損傷\n"
            "3.他機器からの影響、不適切な修理または改造による故障・損傷\n"
            "4.移設・輸送・落下などに起因する故障・損傷\n"
            "5.火災・地震・風水害・落雷などの天災、または公害・塩害・異常電圧などによる故障・損傷\n"
            "6.消耗部品の劣化や摩耗、または外観の汚損など")),
        ("購入証明について", blocks(
            "保証をご利用の際には、以下いずれかの購入証明書類をご提示いただく必要があります：\n"
            "・Jackery公式オンラインストアでの購入：注文番号（注文履歴画面または確認メール）\n"
            "・正規代理店での購入：購入日・販売店名の記載された領収書または納品書",
            "※ ご提示がない場合、保証対応いたしかねます。")),
        ("保証内容", blocks(                                                             # p20
            "**1. 初期不良による交換**（ご購入日から30日以内）\n"
            "・取扱説明書に従った正常な使用中に不具合が発生した場合、同一製品の新品と交換いたします。\n"
            "・在庫切れや販売終了の場合は、同等品への交換または返金にて対応いたします。",
            "**2. 無償修理**（ご購入日から30日以上〜保証期間内）\n"
            "・保証条件を満たす自然故障については、無料で修理対応いたします。\n"
            "・修理が困難な場合は、同等品（同モデルまたは同等スペック品）への交換にて対応いたします。",
            "**3. 有償修理**\n"
            "以下に該当する場合は、有償での修理対応となります：\n"
            "・保証期間を超えた製品\n"
            "・保証対象外と判断された場合\n"
            "・Jackery公式オンラインストアまたは正規代理店以外で購入された製品\n"
            "有償修理後の保証期間は、修理完了日より90日間です。",
            "*無償修理の場合、残りの保証期間が90日未満であれば「90日間」、90日以上であれば「元の保証期間に準じます」。")),
    ]
    for index, (title, body) in enumerate(sections, start=1):
        b.h(title)
        b.comp(warranty_section_component_spec, title=title, section_index=index, blocks=body)
    b.h("免責事項")                                                                     # printed bold panel title
    b.add(panel(P("1. 弊社では、いかなる場合においても、間接的損害または付随的損害（データの損失・逸失利益など）に対して責任を"
                  "負いません。"),
                P("2. 本保証書は、お客様が法律上有する権利を制限するものではありません。"),
                P("3. 保証内容は、予告なく変更される場合がございます。あらかじめご了承ください。"),
                P("Jackery 製品を安心してご使用いただくために、本保証書の内容をご確認のうえ、ご活用くださいますようお願いいたします。"),
                P("ご不明点がございましたら、Jackery カスタマーサービスまでお問い合わせください。")),
          P("公式サイト: http://www.jackery.jp\n"
            "カスタマーサポート: jackery.jp@jackery.com\n"
            "お問い合わせ電話番号: 050-3198-9007"))

    problems = b.finish()
    print("chapters", len(b.chapters), "problems", problems)
    return problems


if __name__ == "__main__":
    if make():
        raise SystemExit("figure records and transcription disagree")
