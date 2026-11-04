"""Write the JE-300B JP Japanese semantic document from the reviewed transcription.

Run from the repository root:
``python3 manual_sources/JE-300B/JP/ja/git-20261103-456bb360/source/intake.py``.
It writes ``source/ja/content.json``. ``original.pdf`` is outlined (no text
layer), so every Japanese line below is transcribed from 300 dpi renders (450-700
dpi clips for dense or small text) of the named physical page and kept as printed.
Every printed block maps to a shared component or plain shared flow
(``source_manifest.json:component_map``); the two 省エネモード tables are the only
declared plain tables. The cover (p1) is not Web content; the print has no paper
table of contents and no back-cover contact page.
"""
from html import escape
from pathlib import Path
import json
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kit import OL, P, UL, Book, inbox_carrier, pair, spec_carrier  # noqa: E402,F401
from tools.component_specs.app import app_inline_control_component_spec, app_qr_download_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
)
from tools.component_specs.reference_table import reference_table_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.web.frozen_ai_flow import node, scroll_table, text  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
DC = "⎓"  # the print's DC symbol
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰"


def cell(value: str, header: bool = False) -> dict:
    return node("table_cell", [text(value)], header=header)


def make() -> list[str]:
    b = Book(SOURCE, "JE-300B", "JP", "ja", "Jackery ポータブル電源 300 Plus · JE-300B")
    load = lambda name: json.loads((SOURCE / "source" / name).read_text())  # noqa: E731
    glyph = {g["slot"]: g["local_path"] for g in load("glyphs.json")}

    # ---- p2 (printed 1) 1.主な仕様 -------------------------------------------------------
    b.chapter("specifications", "1.主な仕様", [2])
    b.comp(spec_table_component_spec, spec_carrier, section_title="【Jackery ポータブル電源 300 Plus】", rows=[
        ("製品の名称 :", "Jackery ポータブル電源 300 Plus"),
        ("型番 :", "JE-300B"),
        ("バッテリータイプ :", "LiFePO4（リン酸鉄リチウム）"),
        ("サイズ＆重量 :", "約230x155x167mm (約3.75kg)"),
        ("定格容量 :", "リチウムイオン電池22.5Ah/12.8V DC (288Wh)"),
        ("AC入力 :", "100V-120V~ 50Hz/60Hz, 最大10A"),
        ("DC入力ポート(USB-C):", f"12-27V{DC}5A Max, 100W Max"),
        ("総出力 :", "300W"),
        ("AC出力 :", "100V~ 50Hz/60Hz, 3A, 300W (瞬間最大600W)"),
        ("USB-A出力 :", f"5V{DC}3A, 最大15W"),
        ("USB-C(OUT)出力 :", f"5V{DC}3A, 最大15W"),
        ("USB-C(IN/OUT)出力 :", f"5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}5A, 最大100W"),
        ("USB総出力 :", "USB-C(IN/OUT): 100W Max, USB-C(OUT)+USB-A: 24W Max"),
        ("シガーソケット出力 :", f"12V{DC}10A"),
        ("充電温度 :", "0~45 °C (32~113 °F)"),
        ("動作温度 :", "-10~45 °C (14~113 °F)"),
        ("保存温度 :", "3ヶ月の場合: -20~45°C (4~113°F)"),
        ("", "6ヶ月の場合: -10~25°C (14~77°F)"),
        ("認証：", "UN38.3"),
    ])
    b.add(P("※USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."),
          P("**■本機の仕様および外観は、改善のため予告なく変更することがあります。**"))
    # Framed recycling notice beside its Li-ion 32 mark (the mark's meaning is the notice title).
    recycle = next(r for r in load("symbols.json") if r["family"] == "li-ion/")
    # The mark sits in its own paragraph: a bare section image would be stretched to the reading width.
    b.add(node("paragraph", [node("image", source=recycle["local_path"], alt="Li-ion 32")]),
          P("**充電式電池のリサイクルについて**"),
          P("本機はリサイクル可能な充電池を内蔵しています。"),
          P("この商品を廃棄する場合は、当社のカスタマーサポートにご連絡ください。"),
          P("充電池の取りはずしはお客様自身では行わないでください。"))

    # ---- p3 (printed 2) 2.各部の名称 ------------------------------------------------------
    b.chapter("product_overview", "2.各部の名称", [3])
    b.figure("overview")

    # ---- p3-4 (printed 2-3) 3.使用について ---------------------------------------------------
    b.chapter("usage", "3.使用について", [3, 4])
    b.h("出力オン/オフ")
    b.add(P("**主電源オン/オフ:**「主電源ボタン」を押すと、作動インジケータが点灯し、LCD ディスプレイの明かりがつきます。 "
            "本製品は 2 分間操作しない場合、休止状態に入り、ディスプレイが自動的にオフになります。主電源を切る必要がある場合は、"
            "作動インジケータが消灯するまで「主電源ボタン」を長押ししてください。この製品の初期設定の待機時間は2時間です。"
            "他の出力スイッチがオンになっておらず、製品に負荷入力がない場合、本製品は 2 時間後に自動的にシャットダウンします。 "
            "自動シャットダウン時間の長さは、Jackery アプリで設定できます。"),
          P("**AC出力のON/OFF:**"),
          P("AC出力ボタンを短く押すと、AC出力インジケーターが点灯し、AC電源が必要な機器に給電ができます。"
            "AC出力電源ボタンをもう一度短く押すと、AC出力がOFFになります。"),
          P("**USB/カーポート出力オン/オフ:**"),
          P("主電源がオンになっていることを確認します。DCボタンを押すと、DC出力作動インジケータが点灯します。この後、"
            "USB/カーポート出力ポートを外部負荷デバイスに接続できます。再度DC ボタンを押すと、USB/カーポート出力がオフになります。"),
          P("**LEDライトのON/OFF**"),                                                       # p4
          P("LEDライトには、照明モード、SOSモードの二つのモードがあります。操作手順は次のとおりです: LEDライトボタンを短く"
            "押すと、LEDライトがオンになります。画面には1Wの出力電力が表示されます。もう一度押すと、SOSモードになり、画面に"
            "出力電力1Wが表示され、もう一度押すと、LEDライトがオフになります。"),
          P("**アプリの接続:**"),
          P("本製品は、Jackeryアプリの接続に対応し、アプリを使用した制御と操作を実現します。ユーザーは、App Storeまたは "
            "Google play からJackeryアプリをダウンロードできます。接続手順の詳細については、Jackery アプリのユーザー "
            "マニュアルをご参照ください。"))

    # ---- p4-6 (printed 3-5) 4.液晶画面 ---------------------------------------------------------
    b.chapter("lcd_display", "4.液晶画面", [4, 5, 6])
    b.figure("lcd-map")
    legend = ["入力電力表示", "充電残り時間", "AC入力電力表示", "シガーソケット入力電力表示",
              "ソーラー(グリーンエネルギー)充電接続", "バッテリー残量警告灯", "バッテリーレベルパーセントタグ",
              "エラーコード", "高温インジケーター", "低温インジケーター", "バッテリー使用可能時間", "消費電力パワー",
              "省エネモード", "交流電源による出力マーク", "バッテリーアイコン", "Wi-Fi", "Bluetooth"]
    b.comp(reference_table_component_spec, variant="lcd-descriptions", label="4.液晶画面", headers=[],
           rows=[[{"html": CIRCLED[i], "text": CIRCLED[i]}, {"html": escape(v), "text": v}]
                 for i, v in enumerate(legend)])
    b.add(P("**EPS：**電気製品のコンセントをポータブル電源のAC出力ポートに接続し、ポータブル電源のAC入力ポートを家庭の"
            "コンセントにつなぐことで、停電時などにポータブル電源を予備電源として活用できます。電気系統の電気が突然切れた場合、"
            "本製品は20ms以内に自動的にバッテリー給電モードに切り替わります。この機能は非専門レベルのUPS機能であり、0msで"
            "切り替えることができないため、データサーバーまたはワークステーションのような無停止充電が必要な要求の高い設備に"
            "接続しないようにしてください。あるいは、複数回のテストを実施し、コンパチビリティを確認してから使用してください。"  # p5
            "ただし、複数の設備への同時接続によって過負荷保護になる可能性があるため、使用時に一台だけの設備に接続することを"
            "お勧めします。指示通りに操作しなかったことにより、設備が正常に作動できなかったり、データが消失した場合も当社は"
            "責任を負いかねます。"))

    def lcd_rows(rows):
        values = [{"name_html": escape(name), "name_text": name, "description_html": escape(body),
                   "description_text": body, "icon_alt": name, "asset_index": index}
                  for index, (name, body, _) in enumerate(rows)]
        b.comp(lcd_icon_component_spec, accessibility_label=rows[0][0], rows=values,
               icon_refs=[glyph[slot] for _, _, slot in rows], icon_locale_policy="exact", numbered=False)

    lcd_rows([
        ("バッテリーアイコン", "本製品の充電時、アイコンは時計回りに回転します。本製品の放電時、アイコンは現在の電力を"
         "表示します。", "lcd-battery-icon"),
        ("バッテリー残量警告灯", "バッテリー残量が20%未満の場合は、ローバッテリーランプが表示されます。バッテリー残量が5%"
         "未満の場合は、ローバッテリーランプが点滅します。バッテリー充電中は、ランプは表示されません。", "lcd-low-battery"),
        ("省エネモード", "電池の消耗につながる出力の切り忘れを防ぐため、省エネモードを搭載しております。省エネモードONに"
         "することで、出力のワット数が電力設定値以下の場合、12時間経つと本電源は自動的に出力をオフにします。",
         "lcd-energy-saving"),
    ])
    rule = "12時間経つとすべての出力は自動的にオフになります"
    b.add(scroll_table([[cell(v, True) for v in ("出力ポートタイプ", "電力設定値", "デフォルト設定")],
                        [cell("AC出力ポート"), cell("≤25W"), cell(rule)],
                        [cell("USB出力ポート"), cell("≤2W"), cell(rule)],
                        [cell("シガーソケット出力ポート"), cell("≤2W"), cell(rule)]]),
          scroll_table([[cell(v, True) for v in ("省エネモード機能", "省エネモードのアイコン",
                                                  "出力のワット数が電力設定値以下の場合", "利用想定シーン")],
                        [cell("OFF"), cell("アイコン無表示"), cell("12時間経っても出力変更なし"),
                         cell("消費電力が電力設定値以下のデバイスを利用する場合")],
                        [cell("ON"), cell("アイコン表示"), cell("12時間経つと出力自動OFF"), cell("上の欄以外の場合")]]),
          P("**省エネモードONとOFFを切り替える方法：**"),
          P("**◆ON：**任意出力ボタンONの状態で、省エネモードアイコンが点灯するまで、【AC出力ボタン+主電源ボタン】を"
            "長押しすれば、ONになります。"),
          P("**◆OFF：**任意出力ボタンONの状態で、省エネモードアイコンが消えるまで、【AC出力ボタン+主電源ボタン】を"
            "長押しすれば、OFFになります。"),
          P("**50Hz/60Hz周波数の切り替え:**"),
          P("**自動識別：**お客様のお住まいの地域に応じて周波数を自動的に識別し、対応する出力に自動調整されます。"),
          P("**手動調整：**AC出力ボタンを長押しすることで周波数を切り替えることができ、対応する周波数が画面に表示されます。"
            "なお、工場出荷時のデフォルト設定は60Hzに設定されています。"))
    lcd_rows([                                                                              # p6
        ("故障コード", "フィードバックに迅速に対応するため、システムに一般的な障害コード F0-FE を設定しています。"
         "F8コードが表示された場合は、給電を停止するか、充電プラグを抜いてください。本製品は自動的に回復します。"
         "回復しない場合は、アフターサービスにご連絡ください。F9障害コードが表示された場合は、給電を停止してください。"
         "製品は自然に回復します。そうならない場合は、カスタマーサービスにご連絡ください。その他のコードが表示された場合は、"
         "カスタマーサービスにご連絡ください。", "lcd-fault-code"),
        ("高温警告", "環境温度が高温時に表示されます。直射日光などが当たっている場合は移動してください。電池が冷めたら、"
         "自動的に表示がオフになります。", "lcd-high-temperature"),
        ("低温警告", "環境温度が低い場合に表示されます。温度が通常になれば自動的に回復します。", "lcd-low-temperature"),
    ])

    # ---- p6-7 (printed 5-6) 5.充電方法 ---------------------------------------------------------
    b.chapter("charging", "5.充電方法", [6, 7])
    b.add(P("グリーンエネルギー優先モード:本製品はグリーンエネルギー優先モードを搭載していますが、ソーラーパネルとAC"
            "アダプターを使って同時に充電できます。同時に充電すると、ソーラーが優先されますが、バッテリーの最大許容電力で"
            "同時に充電されます。"))
    b.callout("ご注意", UL(
        "はじめてお使いになるときは、本製品をフル充電してからご使用ください。",
        "充電池は空の状態で長期保管(3カ月～6カ月）すると、性能が劣化したり、充電できなくなる場合があります。",
        "本機を長期保管する場合には、３ヵ月に１度を目安に本体にACアダプターやソーラーパネルを通して蓄電が可能か、"
        "他製品に給電可能か、などの動作確認をお願い致します。",
        "保管時の電池残量は60%～80%ほどを目安に保管することを推奨します。"), variant="caution")
    b.h("AC充電ケーブル")
    b.add(P("付属のAC充電ケーブルをご使用ください。"))
    b.figure("charging-ac")
    b.h("ソーラー充電")                                                                      # p7
    b.h("Jackery SolarSaga 40 Mini 接続説明", level=4)
    b.add(P("ソーラーパネル40Wの接続ケーブルのDC8020⇒ケーブル\n(DC8020-USB-C)⇒ポータブル電源 300 PlusのUSB-Cポートの"
            "順で接続ください。"))
    b.figure("charging-solar")
    b.h("シガーソケット充電")
    b.add(P("本製品は12Vの車のシガーソケットに対応し、充電ができます。車のバッテリーが上がってしまわないように、エンジンを"
            "始動してから、シガーソケットを使用してください。使用の際は車の充電ポートと入力ケーブルのシガーライターの接触に"
            "問題がないことを確認し、シガーソケットの所定の場所に差し込めることを確認してください。道路状況が悪くて、車の振動が"
            "多い場合は、充電が接触不良になりますので、接触部分が焼損するのを防ぐために、シガーソケット充電を中止してください。"
            "本製品の誤った取り扱いによる損害が発生しましても当社は一切の責任を負いかねます。"))
    b.figure("charging-car")
    b.h("充電に関する安全上のご注意", level=4)
    b.add(P("1) シガーソケット充電は12Vの車専用であり、24Vの車では充電できません。人身傷害や物的損害を避けるため、本製品の"
            "充電に24Vを使用しないでください。"),
          P("2) Jackery 製品以外の付属品を使用して充電しないでください。特に、ソーラーパネルで充電する際は、Jackeryの"
            "ソーラーパネルを使用することをお勧めします。他社ソーラーパネルで充電することによる損失について、当社は一切の"
            "責任を負いません。"))

    # ---- p8-9 (printed 7-8) 6.安全上のご注意 -----------------------------------------------------
    b.chapter("safety", "6.安全上のご注意", [8, 9])
    b.add(P("**ご使用の前にこの「安全上のご注意」をよくお読みのうえ、正しくお使いください。**"))
    b.h("絵表示について")
    b.add(P("製品を安全に正しくお使いいただき、お客様や他の方々への危害や財産への損害を未然に防止するための表示です。"),
          P("内容をよく理解してから本機をご使用ください。"))
    b.comp(symbol_signal_component_spec, accessibility_label="絵表示について",
           headers=[pair("表示", "content"), pair("意味", "content")],
           rows=[{"label": "警告", "show_icon": True, **pair(
                      "この表示を無視して、誤った取り扱いをすると、人が死亡または重傷を負う可能性が想定される内容を"
                      "示しています。", "meaning")},
                 {"label": "注意", "show_icon": True, **pair(
                      "この表示を無視して、誤った取り扱いをすると、人が傷害を負う可能性が想定される内容または物的損害の"
                      "発生が想定される内容を示しています。", "meaning")}])
    b.h("絵表示の説明")
    symbols = [r for r in load("symbols.json") if r["physical_page"] == 8]
    panels = [[], []]
    for index, row in enumerate(symbols):
        meaning = pair(row["meaning"], "meaning")
        panels[0 if row["glyph_search_box"][0] < 100 else 1].append(
            {"asset_index": index, "icon_alt": meaning["meaning_text"], **meaning})
    b.comp(symbol_icon_component_spec, accessibility_label="絵表示の説明",
           headers=[pair(v, "content") for v in ("記号", "意味", "記号", "意味")],
           panels=panels, icon_refs=[r["local_path"] for r in symbols], icon_locale_policy="exact")

    def item(variant, label, title, *body):
        b.callout(label, P(f"**{title}**"), *[P(v) if isinstance(v, str) else v for v in body], variant=variant)

    w, c = "warning", "caution"
    item(w, "警告", "万が一、次のような異常が発生したときはすぐに使用をやめる",
         UL("煙が出ている、異臭がする", "落としたり、破損したとき", "異音がする", "内部に水や異物が入ったとき",
            "電源コード (ACアダプター) が傷んだとき"),
         "このような異常が発生したまま使用していると、火災や感電の原因になります。",
         "すぐにACアダプターをコンセントから抜いてください。また、本製品に接続されている機器もすべて外してください。",
         P("**万が一発煙や発火したら、大量の水で消火して煙が見えなくなるまで本製品を水浸しにしてください。**"),
         "煙が出なくなることを確認してからカスタマーサポートにご連絡ください。",
         "お客様による修理は危険ですので絶対におやめください。")
    item(w, "警告", "分解、改造しない", "故障、発熱、火災･感電の原因になります。")
    item(w, "警告", "表示された電源電圧以外で使用しない",
         "故障、発熱、火災･感電の原因になります。また、本製品を使用できるのは日本国内のみです。")
    item(w, "警告", "付属品と本製品が破損した場合は、ご自身で修理をしない")
    item(w, "警告", "火のそばや炎天下の車内、熱器具の周辺など高温（40°C以上）になる場所で使用したり、放置しない",  # p9
         "発熱や発火、破裂する原因になります。")
    item(w, "警告", "強い衝撃を与えたり、投げつけたりしない", "発熱や発火、破裂する原因になります。")
    item(w, "警告", "水など、液体を入れたり、濡らしたりしない", "発熱や発火の原因になります。")
    item(w, "警告", "濡れた手で本体や接続するケーブルを触らない", "火災や感電の原因になります。")
    item(w, "警告", "端子部にケーブル以外の金属類を差し込まない", "発熱や発火の原因になります。")
    item(w, "警告", "雷が鳴りだしたら、電源プラグにふれない (充電をしない)", "感電の原因になります。")
    item(w, "警告", "各接続端子には確実に差し込む", "差し込みが不十分だと、発熱したりほこりが付着して火災や感電の原因になります。")
    item(c, "注意", "本製品の上に物を載せたり、不安定な場所に置かない", "倒れたり、落ちたりしてけがの原因になります。")
    item(c, "注意", "次のような機器では、絶対に使用しないでください。万が一使用中に給電ができなくなった場合、命にかかわる"
         "被害が想定されます。",
         UL("医療機器や使用上、生命に関わるような機器", "社会的、公共的に重要な機器など", "重要な事業用機器など"))
    item(c, "注意", "心臓にペースメーカーを装着している方は使用しない", "ペースメーカーが、本製品の影響を受ける恐れがあります。")

    # ---- p10-11 (printed 9-10) 7.使用上のご注意 ---------------------------------------------------
    b.chapter("usage_precautions", "7.使用上のご注意", [10, 11])
    b.add(P("Jackeryポータブル電源 300 Plusは、最大電力300Wまでの機器に給電可能です。最大出力300Wは、一定の電力で動く機器"
            "への出力可能範囲を指しています。300Wの出力を超えた場合は、電気回路が自動的に調整され、電力が低減、または保護"
            "機能が作動し自動で遮断することがあります。始動電力が300Wの出力上限値を超える場合、ご利用できませんのでご了承"
            "ください。"),
          P("ご注意："),
          UL("電気モーターを搭載している製品については、例(掃除機、ポンプ、冷蔵庫、電動丸ノコ、エアコン、洗濯機、電子レンジ、"
             "ドライヤーなど)起動時に「誘導負荷」が発生し、公称電力の3～7倍の電力が必要となります。",
             "始動電力が出力上限値(定格出力)を大幅に超える可能性のある製品のご利用や、定格出力を超え給電がストップした製品を"
             "繰り返し利用することはポータブル電源が損傷するリスクがありますのでお控えください。",
             "本製品は防塵･防水仕様ではありませんので、ほこりや水、海水などがかからないように注意してください。",
             "ほこりが多い場所や高温多湿の場所での充電および使用、放置をしないでください。",
             "本製品を不安定な場所に置かないでください。必ず、平坦で安定した場所に置いて使用してください。",
             "本製品の通風孔は、安全上絶対にふさがないでください。また、本製品の各面から5cm以上スペースを空けてください。",
             "充電または給電中は本製品が温かくなります(故障ではありません)、周囲には物を置かないでください。",
             "本製品接続機器のケーブルを差すときは、真っすぐな向きに差してください。",
             "接続機器のケーブルを抜くときは、必ずプラグ部分を持って抜いてください。ケーブルを引っ張ったり折り曲げると、"
             "断線などの原因となります。",
             "給電する機器の充電制御や充電状況、環境などにより給電できない、または急速充電にならない場合があります。",
             "充電または給電中はラジオやチューナー、テレビなどに雑音が入る場合があります。雑音が入る場合には、それらの"
             "製品から離れた場所でお使いください。",
             "本体が汚れたらコンセントから電源プラグを抜き、柔らかい布で乾拭きしてください。汚れがひどいときは、水または"
             "薄めた中性洗剤でふきとってください。シンナーやベンジンなどは絶対に使わないでください。",
             "付属のACアダプターは、電源コードの抜き差しで電源が入ったり切れたりするため、異常時に電源コードを容易に"
             "抜き差しできるスペースを空けておいてください。",
             "入出力の電力(W)\n接続機器の入力仕様が本製品の出力値の上限を超えている場合、電源を自動的に遮断します。"   # p11
             "消費電力が仕様以下であることを確認してから出力ボタンを押してください。",
             "低/高温警報\n本製品は、-10 ~ 45°C (14 ~ 113°F)の温度範囲でお使いの機器に電力を供給できます。\n"
             "動作温度が上記範囲外にある場合、本製品が動作しないことがあります。\n"
             "この製品は、0 ~ 45°C (32 ~113°F) の温度範囲内で充電してください。\n"
             "充電温度が上記範囲を超えると、正常に充電できない場合があります。\n"
             "過低温および過高温の表示があれば保護装置が動作し充電又は出力が停止します。\n"
             "復旧は本機が規定温度になれば自然復旧します。",
             "容量表示に関しては、あくまで参考値となり、電圧により電力が算出され、表示数値にズレが発生することがあります。",
             "保存温度：-10~25°C (14~77°F)で6ヶ月；-20~45°C (-4~113°F)で3ヶ月\n"
             "ご確認：-10~25°C (14~77°F)で長期保管する場合、6ヶ月に１度を目安に、\n"
             "-20~45°C (-4~113°F) で長期保管をする場合、3ヵ月に１度を目安に、本体にACアダプターやソーラーパネルを通して"
             "蓄電が可能か、他製品に給電可能かなど動作確認をお願い致します。また長期保管の場合、電池残量は60-80%程度で"
             "保管を行ってください。"))

    # ---- p11 (printed 10) 8.同梱品 ---------------------------------------------------------------
    b.chapter("in_the_box", "8.同梱品", [11])
    slots = ("inbox-unit", "inbox-ac-cable", "inbox-user-manual", "inbox-warranty")
    cards = [{"image_ref": b.figures[s]["local_path"], "label": f"{CIRCLED[i]} {b.figures[s]['caption']}",
              "alt": b.figures[s]["caption"]} for i, s in enumerate(slots)]
    b.used_figures += list(slots)
    b.comp(inbox_component_spec, inbox_carrier, accessibility_label="8.同梱品", cards=cards,
           tip_label="", tip_body="", require_tip=False)
    b.add(P("※付属品を故障、紛失等してしまった場合はカスタマーサポートまでご連絡ください。"))

    # ---- p12 (printed 11) 9.免責事項 ---------------------------------------------------------------
    b.chapter("disclaimer", "9.免責事項", [12])
    b.add(UL(
        "火災、地震、第三者による行為、その他の事故、お客様の故意または過失\n誤用・誤動作・その他の異常な条件下での使用に"
        "より生じた損害に関して、当社は一切責任を負いません。",
        "付属品と本製品が破損した場合は、ご自身で修理を行わないでください。\nご自身で分解・修理したことにより生じた損害に"
        "関し、当社は一切責任を負いません。",
        "保証範囲は利用規約に適用され、記載されていない内容は当社の保証範囲外となります。",
        "取扱説明書の記載事項が遵守されないことにより生じた不適合について当社は責任を負いかねます。",
        "本製品の使用、または使用不能から発生する付随的な損害(事業利益損失含む)、当社が関与しない接続機器との組み合わせに"
        "よる誤動作などから生じた損害に関して、当社は一切の責任を負いません。",
        "本製品は個人の安全に関係する製品、消費電力の大きな設備に給電できません。例えば、医療機器、核施設設備、CPAP"
        "（シーパップ） 、スペースシャトルの製造などです。\n上記の設備、用途で使用した結果、火災、機器故障など個人の安全を"
        "脅かす事故が生じた場合、当社は一切責任を負いません。"))

    # ---- p12-14 (printed 11-13) Jackeryアプリ ユーザーマニュアル -----------------------------------------
    # The unheaded app notice at the foot of p12 (with its store badges) opens the App chapter.
    b.chapter("app_setup", "Jackeryアプリ ユーザーマニュアル", [12, 13, 14])
    notice = ("本製品はJackeryアプリケーションによるスマートコントロールに対応しています。ご利用いただくには、"
              "下記のアプリストアより「Jackery」で検索して「Jackery APP」をダウンロードしてください。")
    badges = b.figures["app-store-badges"]["local_path"]
    b.used_figures.append("app-store-badges")
    b.comp(app_qr_download_component_spec,
           lambda spec: [node("image", source=badges, alt="App Store / Google Play"), P(notice)],
           label="App Store / Google Play", paragraph={"text": notice, "html": escape(notice)}, image_ref=badges)
    b.h("1. アプリをダウンロードしてログインするには")                                     # p13
    b.add(P("Google  PlayまたはApp  Storeで「Jackery」と検索し、アプリをインストールしてください。その後、登録とログインを"
            "行ってください。"))
    b.h("2. デバイスを追加するには")
    before, after = "2.1  APPの右上にあるデバイス追加ボタン", "をクリックします。"
    b.comp(app_inline_control_component_spec,
           lambda spec: [node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])],
           accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
           paragraph_text=f"{before} + {after}", metadata={"visual_recovery": "outlined-pdf-vector-plus-control"})
    b.add(P("2.2　デバイスの主電源ボタンを長押しして電源をいれると、ディスプレー画面にWi-FiとBluetoothのアイコンが点滅し、"
            "デバイスがネットワーク設定モードに入ったことを示します。アイコン点滅中ボタンをクリックし、アプリが近くの"
            "デバイスに接続し、Bluetoothのアクセス許可を開くことを許可します。"))
    b.figure("app-add")
    b.callout("備考", "電源を入れた後、アプリが5分以内接続されていないと、デバイスは自動的にWi-FiとBluetoothをオフにします。"
              "再度Wi-FiとBluetoothをオンにするには、「DC/USBボタン」と「ACボタン」を同時長押しする必要があります。",
              variant="note")
    b.figure("app-control")
    b.add(P("2.3 検出されたデバイスアイコンをクリックすると、アプリは自動的にBluetoothでデバイスを接続します。"))
    b.callout("備考", P("バインド処理中に「デバイスがバインドされました」と表示された場合は、以下の2つの方法で接続できます："),
              UL("デバイス所有者は、アプリを通じてこのデバイスを他のユーザーと共有します。詳細は、「機器共有」をご参照ください。",
                 "「POWERボタン」と「DC/USBボタン」を3秒間長押ししてデバイスをリセットし、再度バインドしてくだい。"),  # p14
              variant="note")
    b.add(P("2.4  デバイスが正常に接続されると、デバイスが接続するWi-Fiの名前とパスワードを入力する必要があり、デバイスは"
            "自動的にWi-Fiネットワークに接続します。"))
    b.callout("備考", "2.4GHz帯のWi-Fiネットワークを選択してください。デバイスは、5GHz帯のWi-Fiネットワークには対応して"
              "いません。", variant="note")
    b.add(P("2.5 デバイスのホーム画面でデバイスが正常に追加されると、デバイスのWi-Fi アイコンは常にオンになります。"))
    b.figure("app-results")
    b.add(P("上記のスクリーンショットはご参考まで。"))
    b.h("3. デバイスのバインドを解除するには")
    b.add(P("デバイスのメインインターフェースの右上隅にある「設定」ボタンをクリックして設定ページに入り、ページの下部にある"
            "「バインド解除」ボタンをクリックしてデバイスのバインドを解除します。"))
    b.h("4. ご確認")
    b.add(P("4.1 Wi-FiとBluetoothをオンにするには（ディスプレーにWi-FiとBluetoothのアイコンが点灯）："),
          UL("デバイスがオンになれば自動的にオンになり、ディスプレーにWi-FiとBluetoothのアイコンが点灯します。",
             "上記アイコンが点灯しない場合、ディスプレーにWi-FiとBluetoothのアイコンが点灯するまで、DC/USB出力ボタンと"
             "AC出力ボタンを同時長押しします。"),
          P("4.2 Wi-FiとBluetoothをオフにするには（ディスプレーにWi-FiとBluetoothのアイコンが消える）："),
          UL("ディスプレーにWi-FiとBluetoothのアイコンが消えるまで、DC/USB出力ボタンとAC出力ボタンを同時長押しします。",
             "5分以内にデバイスが接続されない場合、Wi-FiとBluetooth は自動的にオフになります。"),
          P("4.3 Wi-FiとBluetoothをリセットするには："),
          UL("主電源ボタンとDC/USBボタンを同時に3秒間押すと、Wi-FiとBluetoothが初期化され、システムが再起動します。"
             "接続されているアプリアカウントはバインド解除されます。"))

    problems = b.finish()
    print("chapters", len(b.chapters), "problems", problems)
    return problems


if __name__ == "__main__":
    if make():
        raise SystemExit("figure records and transcription disagree")
