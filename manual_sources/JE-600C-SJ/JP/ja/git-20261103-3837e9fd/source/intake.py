"""Write the JE-600C-SJ JP Japanese semantic document from the reviewed transcription.

Run from the repository root:
``python3 manual_sources/JE-600C-SJ/JP/ja/git-20261103-3837e9fd/source/intake.py``.
It writes ``source/ja/content.json``. ``original.pdf`` is outlined (no text
layer), so every Japanese line below is transcribed from 300-1000 dpi renders of
the named physical pages (two passes) and kept as printed. Every printed block maps
to a shared component or plain shared flow (``source_manifest.json:component_map``);
the two tables no shared component can carry are declared in
``source_manifest.json:shared_component_exceptions``. The cover (p1) is not Web
content; this print has no contents page and no back cover.
"""
from html import escape
from pathlib import Path
import json
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kit import OL, P, UL, Book, inbox_carrier, inline, pair, spec_carrier  # noqa: E402,F401
from tools.component_specs.app import app_inline_control_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
)
from tools.component_specs.reference_table import reference_table_component_spec  # noqa: E402
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.web.frozen_ai_flow import node, text  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
DC = "⎓"  # the print's DC symbol
WARN, CAUT = "警告", "注意"


def cell(value: str, *, header: bool = False, **fields) -> dict:
    return node("table_cell", inline(value), header=header, **fields)


def plain_table(rows: list[list[dict]], head: list[list[dict]] | None = None) -> dict:
    """A declared plain table on the shared manual-table classes (shared_component_exceptions)."""
    parts = [node("table_head", [node("table_row", head)])] if head else []
    parts.append(node("table_body", [node("table_row", row) for row in rows]))
    return node("group", [node("table", parts, presentation={"html": {"attributes": {"class": "manual-table"}}})],
                role="container", presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}})


def lcd_rows(b: Book, glyphs: dict, rows: list[tuple[str, str, str]]) -> None:
    """Unnumbered LCD icon catalog: (glyph slot, bold printed title, description)."""
    values = [{**pair(name, "name"), **pair(description, "description"), "icon_alt": name, "asset_index": index}
              for index, (_, name, description) in enumerate(rows)]
    b.comp(lcd_icon_component_spec, accessibility_label=rows[0][1], rows=values,
           icon_refs=[glyphs[slot]["local_path"] for slot, _, _ in rows], icon_locale_policy="exact", numbered=False)


def item(b: Book, variant: str, label: str, title: str, *body) -> None:
    """One printed 警告/注意 item: bold title, then its body lines (str paragraph or a flow node)."""
    b.callout(label, f"**{title}**", *body, variant=variant)


def make() -> list[str]:
    b = Book(SOURCE, "JE-600C-SJ", "JP", "ja", "Jackery ポータブル電源 600 Plus 取扱説明書")
    load = lambda name: json.loads((SOURCE / "source" / name).read_text())  # noqa: E731
    glyphs = {g["slot"]: g for g in load("glyphs.json")}

    # ---- p2 1.主な仕様 ---------------------------------------------------------------
    b.chapter("specifications", "1.主な仕様", [2])
    rows = [("製品の名称 :", "Jackery ポータブル電源 600 Plus"), ("型番 :", "JE-600C-SJ"),
            ("バッテリータイプ :", "LiFePO4（リン酸鉄リチウムイオン電池）"),
            ("定格容量 :", "15.2Ah/41.6V DC(632.3Wh)"), ("サイズ＆重量 :", "約300 x 219 x 197 mm (約7.3kg）"),
            ("AC入力 :", "100V-120V~ 50Hz/60Hz, 最大15A"),
            ("DC入力ポート:", f"11V-16V{DC}8A Max; 16V-60V{DC}10.5A/200W Max"),
            ("2×AC出力 :", "100V~ 50Hz/60Hz, 最大8A, 2ポート合計800W (瞬間最大1600W)"),
            ("USB-A出力 :", f"5-6V{DC}3A, 6-9V{DC}2A, 9-12V{DC}1.5A, 最大18W"),
            ("USB-C1出力 :", f"5V{DC}3A, 9V{DC}3A, 12V{DC}2.5A, 15V{DC}2A, 20V{DC}1.5A, 最大30W"),
            ("USB-C2出力 :", f"5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}5A, 最大100W"),
            ("シガーソケット出力 :", f"12V{DC}10A, 最大10A"),
            ("充電温度 :", "0~45 °C (32~113 °F)"), ("動作温度 :", "-10~45 °C (14~113 °F)"),
            ("保存温度 :", "1ヶ月 -20~45°C (-4~113°F); 3ヶ月 0~45°C (32~113°F);\n12ヶ月 0~25°C (32~77°F)"),
            ("認証 :", "UN38.3")]
    b.comp(spec_table_component_spec, spec_carrier, section_title="【Jackery ポータブル電源 600 Plus】", rows=rows)
    b.add(P("※USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."),
          P("**■本機の仕様および外観は、改善のため予告なく変更することがあります。**"))
    # The recycling notice beside its Li-ion 32 mark (declared plain table).
    b.add(plain_table([[node("table_cell", [node("image", source=glyphs["recycle-li-ion"]["local_path"],
                                                  alt="Li-ion 32")], header=False),
                        node("table_cell", [P("**充電式電池のリサイクルについて**"),
                                            P("本機はリサイクル可能な充電池を内蔵しています。\n"
                                              "この商品を廃棄する場合は、当社のカスタマーサポートにご連絡ください。\n"
                                              "充電池の取りはずしはお客様自身では行わないでください。")], header=False)]]))

    # ---- p3 2.各部の名称 ---------------------------------------------------------------
    b.chapter("product_overview", "2.各部の名称", [3])
    b.figure("overview")

    # ---- p3-5 3.液晶画面 -----------------------------------------------------------------
    b.chapter("lcd_display", "3.液晶画面", [3, 4, 5])
    b.figure("lcd-map")
    legend = ["Wi-Fi", "Bluetooth", "静かな充電モード", "バッテリ節約モード", "入力電力表示", "充電残り時間",
              "AC入力電力表示", "シガーソケット入力電力表示", "ソーラー(グリーンエネルギー)充電接続",
              "バッテリーアイコン", "バッテリー残量警告灯", "バッテリーレベルパーセントタグ", "エラーコード",
              "高温インジケーター", "低温インジケーター", "省エネモード", "交流電源による出力マーク",
              "消費電力パワー", "バッテリー使用可能時間"]
    circled = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲"
    b.comp(reference_table_component_spec, variant="lcd-descriptions", label="3.液晶画面", headers=[],
           rows=[[{"html": circled[i], "text": circled[i]}, {"html": escape(v), "text": v}]
                 for i, v in enumerate(legend)])
    lcd_rows(b, glyphs, [                                                                  # p4
        ("lcd-battery-ring", "バッテリーアイコン",
         "本製品の充電時、アイコンは時計回りに回転します。本製品の放電時、アイコンは現在の電力を表示します。"),
        ("lcd-low-battery", "バッテリー残量警告灯",
         "バッテリー残量が20%未満の場合は、ローバッテリーランプが表示されます。バッテリー残量が5%未満の場合は、"
         "ローバッテリーランプが点滅します。バッテリー充電中は、ランプは表示されません。"),
        ("lcd-energy-saving", "省エネモード",
         "電池の消費につながる出力の切り忘れを防ぐため、本製品は、初期設定で省エネモードをオンにします。これは接続して"
         "いるデバイスがない場合、または接続しているデバイスがある値以下の場合に起動します。（詳しくは以下の表をご参照"
         "ください）、12時間たつと本デバイスは自動的にすべての出力をオフにします。"),
    ])
    # Four printed columns with the inline 88H mark (declared plain table).
    eco_icon = node("image", source=glyphs["lcd-energy-saving"]["local_path"], alt="88H")
    on = lambda: node("table_cell", [text("ON（dispalyに"), dict(eco_icon), text("がある）")], header=False)  # noqa: E731
    shutdown = "12時間後に自動的にシャットダウンします"
    b.add(plain_table(
        [[cell(port), cell(limit), cell(shutdown), on()]
         for port, limit in (("AC出力ポート", "≤25W"), ("USB出力ポート", "≤2W"), ("シガーソケット出力ポート", "≤2W"))],
        head=[cell("**出力ポートタイプ**", header=True), cell("**電力設定値**", header=True),
              cell("**デフォルト設定**", header=True),
              node("table_cell", [node("strong", [text("省エネモード")]), dict(eco_icon)], header=True)]))
    b.add(P("**省エネモードをOFFにするため:** ACまたはDCいずれかのの出力ボタンがオンになっている状態で、画面に省エネ"
            "モードのアイコンが消えるまで、「AC出力ボタン+主電源ボタン」を長押しします。」省エネモードがOFFの場合、出力の"
            "切り忘れによる電力不足を防ぐため、製品を使用しない時は電源を切るよう注意してください。"),
          P("**省エネモードをONにするため:** ACまたはDCいずれかのの出力ボタンをオンの状態で、画面に省エネモードの"
            "アイコンが表示されるまで、「AC出力ボタン+主電源ボタン」を長押ししてください。"),
          P("**50Hz/60Hz周波数の切り替え:**"),
          P("**自動識別:** お客様のお住まいの地域に応じて周波数を自動的に識別し、対応する出力に自動調整されます。"),
          P("**手動調整:** AC出力ボタンを長押しすることで周波数を切り替えることができ、対応する周波数が画面に表示されます。"
            "なお、工場出荷時のデフォルト設定は60Hzに設定されています。"))
    lcd_rows(b, glyphs, [
        ("lcd-fault-code", "故障コード",
         "フィードバックに迅速に対応するため、システムに一般的な障害コード F0-FE を設定しています。\n"
         "F8コード: 給電を停止するか、充電プラグを抜いてください。本製品は自動的に回復します。\n"
         "F9コード: 給電を停止してください。製品は自動的に回復します。\n"
         "F8とF9コードにつき、上記の処理で回復しない場合、またはその他のコードが表示された場合は、カスタマー"
         "サポートにご連絡ください。"),
        ("lcd-high-temperature", "高温警告",                                                  # p5
         "環境温度が高温時に表示されます。直射日光などが当たっている場合は移動してください。\n"
         "電池が冷めたら、自動的に表示がオフになります。"),
        ("lcd-low-temperature", "低温警告", "環境温度が低い場合に表示されます。温度が通常になれば自動的に回復します。"),
        ("lcd-quiet-charging", "静かな充電モード",
         "静かな充電モード下、inputワット数が低下し、充電所要時間が長くなる一方、稼動音は著しく静かになります。"
         "（アプリで設置可能）"),
        ("lcd-battery-saving", "バッテリ節約モード",
         "バッテリ節約モード下、バッテリー残量が既定値に設定されるため、バッテリーの寿命を延ばすことが可能です。"
         "（アプリで設置可能）"),
    ])

    # ---- p5-6 4.使用について -------------------------------------------------------------
    b.chapter("usage", "4.使用について", [5, 6])
    b.h("出力オン/オフ")
    b.add(P("**主電源ボタン/オフ:** 「主電源ボタン」を押すと、作動インジケータが点灯し、LCD ディスプレイの明かりがつき"
            "ます。 本製品は 2 分間操作しない場合、休止状態に入り、ディスプレイが自動的にオフになります。主電源を切る必要"
            "がある場合は、作動インジケータが消灯するまで「主電源ボタン」を長押ししてください。この製品の初期設定の待機時間"
            "は2時間です。他の出力スイッチがオンになっていない、または製品に充電入力がない場合、本製品は 2 時間後に自動的に"
            "シャットダウンします。 自動シャットダウン時間は、Jackery アプリで設定できます。\n"
            "省エネモード設置後、DC/AC出力ボタンがオンの状態であるとしても、以下の場合12時間後電源が自動オフになります。\n"
            "1.電源本体が無充電、無放電\n"
            "2.充放電の出力が既定値以下(詳細は省エネモードの説明をご参照)"),
          P("**AC出力のオン/オフ:** 主電源ボタンがオンになっていることを確認します。 AC ボタンを押すと、AC 出力作動"
            "インジケータが点灯します。この後、AC充電が必要な機器を接続できます。再度ACボタンを押すと、AC 出力がオフに"
            "なります。"),
          P("**USB/カーポート出力オン/オフ:**\n"
            "主電源がオンになっていることを確認します。DC/USBボタンを押すと、DC出力作動インジケータが点灯します。この後、"
            "USB/カーポート出力ポートを外部負荷デバイスに接続できます。再度DC/USBボタンを押すと、USB/カーポート出力が"
            "オフになります。\n"
            "電源ボタンまたは任意出力ボタンを押す、あるいは充電が入力されれば、ディスプレイが点灯します。再び押せば、"
            "ディスプレイが消灯します。2分間操作しないと、製品はスリープ状態に入り、ディスプレイも自動的に消灯します。"
            "充電時及び放電時に、ディスプレイの常時点灯が必要な場合の操作手順は以下の通り: ディスプレイが点灯した後、"
            "「主電源ボタン」を2回押せば常時点灯になります。ディスプレイの常時点灯をOFFにする操作手順は以下の通り：「主電源"
            "ボタン」を押せば、ディスプレイが消灯します。\n"
            "**注意:** ディスプレイの常時点灯モードにおいて、充電または設備への接続をしない場合、2時間後にディスプレイが"
            "自動的に消灯します。"),
          P("**UPS機能:** 電気製品のコンセントをポータブル電源のAC出力ポートに接続し、ポータブル電源のAC入力ポートを"   # p6
            "家庭のコンセントにつなぐことで、停電時などにポータブル電源を予備電源として活用できます。電気系統の電気が突然"
            "切れた場合、本製品は20ms(0.020秒)以内に自動的にバッテリー給電モードに切り替わります。この機能は非専門レベル"
            "のUPS機能のため、0msで切り替えることができません。そのため、データサーバーまたはワークステーションのような"
            "無停止充電が必要な要求の高い設備に接続しないようにしてください。あるいは、複数回のテストを実施し、"
            "コンパチビリティを確認してから使用してください。ただし、複数の設備への同時接続によって過負荷保護になる可能性"
            "があるため、使用時には一台だけの設備に接続することをお勧めします。指示通りに操作しなかったことにより、設備が"
            "正常に作動できなかったり、データが消失した場合、当社は責任を負いかねます。"),
          P("**LEDライト:** LEDライトには、微光モード、強光モード、SOSモードの3つのモードがあります。\n"
            "LEDスイッチを短く押すと、LEDライトが点灯し、デフォルトの微光モードになります。もう一度LEDスイッチを短く押すと、"
            "強光モード→SOSモード→LED消灯の順に切り替わります。また、いずれのモードでも、LEDスイッチを長押しすることで、"
            "LEDライトを消灯できます。"))

    # ---- p6 5.アプリの接続 ---------------------------------------------------------------
    b.chapter("app_connection", "5.アプリの接続", [6])
    b.add(P("本製品は、Jackeryアプリのリモート接続に対応します。ユーザーは、App Storeまたはgoogle playからJackery"
            "アプリをダウンロードできます。接続手順の詳細については、Jackery アプリのユーザー マニュアルをご参照ください。"))

    # ---- p6-8 6.充電方法 ------------------------------------------------------------------
    b.chapter("charging", "6.充電方法", [6, 7, 8])
    b.add(P("**グリーンエネルギー優先モード:**\n"
            "本製品はグリーンエネルギー優先モードを搭載していますが、ソーラーパネルとAC充電ケーブルを使って同時に充電"
            "できます。同時に充電すると、ソーラーが優先されますが、バッテリーの最大許容電力で同時に充電されます。"),
          P("**ご注意**\n"
            "1.製品の充電動作温度範囲は0°C〜45°C、放電動作温度範囲は-10°C〜45°Cです。上限・下限温度を超えた場合、"
            "充放電が制限され、または充放電不可の可能性があります。\n"
            "2.温度によって、製品の充電効率と実際の容量は異なります。"))
    b.callout("ご注意", UL(
        "はじめてお使いになるときは、本製品をフル充電してからご使用ください。",
        "充電池は空の状態で長期保管(3カ月〜6カ月）すると、性能が劣化したり、充電できなくなる場合があります。",
        "本機を長期保管する場合には、3ヵ月に１度を目安に本体にACアダプターやソーラーパネルを通して蓄電が可能か、"
        "他製品に給電可能かなど動作確認をお願い致します。\n"
        "保管の際は、満充電状態でも保管可能ですが、バッテリー残量を60%〜80%程度で保管する事を推奨します。"),
        variant="caution")
    b.h("AC充電ケーブル")
    b.add(P("付属のAC充電ケーブルをご使用ください。"))
    b.figure("ac-charging")
    b.add(P("**緊急充電モード:** ACコンセントからの充電時、お急ぎの場合には緊急充電モードを使って充電することができ"   # p7
            "ます。使用するには「Jackery App」でこの機能を「有効」または「無効」に設定してください。緊急充電モードでは、"
            "バッテリーの残量(SOC)を示す円形のライトの点滅速度が速くなります。\n"
            "※バッテリーは通常の速度で充電することでバッテリーを最大限に保護できるよう設計されているため、緊急充電は"
            "必要な場合にのみ使用し、常時使用することはお勧めしません。"),
          P("コンセントよりJackery ポータブル電源 600 Plus本体に充電する場合、電流容量が大きいため、他機器と併用したり"
            "途中接続をすると、コンセントの電流上限値を超え充電停止したり、配線やコンセント・接続部が発熱し、火災の原因と"
            "なる恐れがあります。必ず電源タップなどを介して他の電気製品と併用しないでください。"))
    b.h("ソーラー充電")
    b.add(P("ポータブル電源600 Plusは、最大で200Wのソーラーパネル1枚、あるいは100Wのソーラーパネル2枚の直列入力に"
            "対応しており、ソーラーパネルの接続ケーブル端子は8020なので直接ポータブル電源600 PlusのDC8020ポートに接続"
            "して充電することが可能です。ソーラーパネルを2枚接続する場合は、下記の図を参照し、ソーラーパネルの直列用中継"
            "ボックスを介して充電してください（ご注意：ソーラーパネルの中継ボックスは標準装備ではありませんので、別途"
            "購入する必要があります）。"))
    b.figure("solar-single")
    b.figure("solar-dual")
    b.h("シガーソケット充電")
    b.add(P("本製品は12Vの車のシガーソケットに対応し、充電ができます。車のバッテリーが上がってしまわないように、"
            "エンジンを始動してから、シガーソケットを使用してください。使用の際は車の充電ポートと入力ケーブルのシガー"
            "ライターの接触に問題がないことを確認し、シガーソケットの所定の場所に差し込めることを確認してください。道路"
            "状況が悪くて、車の振動が多い場合は、充電が接触不良になりますので、接触部分が焼損するのを防ぐために、シガー"
            "ソケット充電を中止してください。本製品の誤った取り扱いによる損害が発生した場合も当社は一切の責任を負いかね"
            "ます。"))
    b.figure("car-charging")
    b.h("充電に関する安全上のご注意")                                                       # p8
    b.add(P("1)シガーソケット充電とソーラー充電を同時に使用しないでください。同時に使用すると、車のヒューズが損傷する"
            "可能性があります。\n"
            "2)シガーソケット充電は12V車専用で、24V車は充電できません。人身傷害や物的損害を避けるため、本製品の充電に"
            "24V車を使用しないでください。\n"
            "3)Jackeryブランド以外の付属品を使用して充電しないでください。特に、ソーラーパネルで充電する際は、Jackery"
            "のソーラーパネルを使用することをお勧めします。他社ソーラーパネルで充電することによる損失について、当社は"
            "一切の責任を負いません。"))

    # ---- p8-9 7.安全上のご注意 ------------------------------------------------------------
    b.chapter("safety", "7.安全上のご注意", [8, 9])
    b.add(P("**ご使用の前にこの「安全上のご注意」をよくお読みのうえ、正しくお使いください。**"))
    b.h("絵表示について")
    b.add(P("製品を安全に正しくお使いいただき、お客様や他の方々への危害や財産への損害を未然に防止するための表示です。\n"
            "内容をよく理解してから本文をお読みください。"))
    b.comp(symbol_signal_component_spec, accessibility_label="絵表示について",
           headers=[pair("表示", "content"), pair("意味", "content")],
           rows=[{"label": label, "show_icon": True, **pair(meaning, "meaning")} for label, meaning in (
               (WARN, "この表示を無視して、誤った取り扱いをすると、人が死亡または重傷を負う可能性が想定される内容を示して"
                      "います。"),
               (CAUT, "この表示を無視して、誤った取り扱いをすると、人が傷害を負う可能性が想定される内容または物的損害の"
                      "発生が想定される内容を示しています。"))])
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
    item(b, "warning", WARN, "万が一、次のような異常が発生したときはすぐに使用をやめる",
         UL("煙が出ている、異臭がする", "落としたり、破損したとき", "異音がする", "内部に水や異物が入ったとき",
            "電源コード (ACアダプター) が傷んだとき"),
         "このような異常が発生したまま使用していると、火災や感電の原因になります。\n"
         "すぐにACアダプターをコンセントから抜いてください。また、本製品に接続されている機器もすべて外してください。",
         "**万が一発煙や発火したら、大量の水で消火して煙が見えなくなるまで本製品を水浸しにしてください。**",
         "煙が出なくなることを確認してからカスタマーサポートにご連絡ください。\n"
         "お客様による修理は危険ですので絶対におやめください。")
    for title, body in (                                                                    # p9
            ("分解、改造しない", "故障、発熱、火災·感電の原因になります。"),
            ("表示された電源電圧以外で使用しない",
             "故障、発熱、火災·感電の原因になります。また、本製品を使用できるのは日本国内のみです。"),
            ("付属品と本製品が破損した場合は、ご自身で修理をしない", None)):
        item(b, "warning", WARN, title, *([body] if body else []))
    for title, body in (
            ("火のそばや炎天下の車内、熱器具の周辺など高温（45°C以上）になる場所で使用したり、放置しない",
             "発熱や発火、破裂する原因になります。"),
            ("強い衝撃を与えたり、投げつけたりしない", "発熱や発火、破裂する原因になります。"),
            ("水など、液体を入れたり、濡らしたりしない", "発熱や発火の原因になります。"),
            ("濡れた手で本体や接続するケーブルを触らない", "火災や感電の原因になります。"),
            ("端子部にケーブル以外の金属類を差し込まない", "発熱や発火の原因になります。"),
            ("雷が鳴りだしたら、電源プラグにふれない (充電をしない)", "感電の原因になります。"),
            ("各接続端子には確実に差し込む", "差し込みが不十分だと、発熱したりほこりが付着して火災や感電の原因になります。"),
            ("接地接続は必ず、電源プラグを電源につなぐ前に行って下さい",
             "また、接地接続を外す場合は、必ず電源プラグを切り離してから行って下さい。")):
        item(b, "warning", WARN, title, body)
    item(b, "caution", CAUT, "本製品の上に物を載せたり、不安定な場所に置かない", "倒れたり、落ちたりしてけがの原因になります。")
    item(b, "caution", CAUT,
         "データサーバや医療機器など、非常時に不具合が起こると人命 / 財産に重大な危険を及ぼしうる用途でのご使用はお控え"
         "ください。次のようなような機器では、万が一使用中に給電ができなくなった場合、人命 / 財産にかかわる被害が想定され"
         "ます。",
         UL("医療機器や使用上、生命に関わるような機器", "社会的、公共的に重要な機器など", "重要な事業用機器など"))
    item(b, "caution", CAUT, "心臓にペースメーカーを装着している方は使用しない", "ペースメーカーが、本製品の影響を受ける恐れがあります。")
    item(b, "caution", CAUT,
         "格納式ハンドルを使用してJackery ポータブル電源 600 Plus を移動するときは、積み重ねたり、上に他の物を置いたり"
         "しないでください。落下して怪我をする場合があります。")

    # ---- p10-11 8.使用上のご注意 ----------------------------------------------------------
    b.chapter("usage_precautions", "8.使用上のご注意", [10, 11])
    b.add(UL(
        "Jackery ポータブル電源 600 Plusは、定格出力800Wです。通常時で消費電力が800Wまでの機器に給電ができるため、"
        "多くの電化製品や端末に対応可能です。ただし、電気モーターを搭載している製品については、例(掃除機、ポンプ、冷蔵庫、"
        "電動丸ノコ、エアコン、洗濯機、電子レンジ、ドライヤーなど)起動時に「誘導負荷」が発生し、公称電力の3〜7倍の電力が"
        "必要となります。定格出力800Wは、一定の電力で動く機器への出力可能範囲を指しています。\n"
        "800Wの出力を超えた場合は、電気回路が自動的に調整され、電力が低減、または保護機能が作動し自動で遮断すること"
        "があります。\n"
        "またAC出力ポート2つ搭載されておりますが、2つ同時にご利用頂く場合、合計して800W以内であることをご確認の上"
        "ご利用ください。\n"
        "ご注意：始動電力が出力上限値(定格出力)を大幅に超える可能性のある製品のご利用や、定格出力を超え給電がストップ"
        "した製品を繰り返し利用することはポータブル電源のバッテリーが損傷するリスクがありますのでお控えください。",
        "出力上限値を超えた電化製品を利用しない(始動電力が公称電力3倍〜7倍の誘導負荷の掃除機、冷蔵庫、エアコン、"
        "電子レンジ、洗濯機、電動丸、ポンプなどは特にご注意下さい) 。",
        "本製品は防塵·防水仕様ではありませんので、ほこりや水、海水などがかからないように注意してください。",
        "ほこりが多い場所や高温多湿の場所での充電および使用、放置をしないでください。",
        "本製品を不安定な場所に置かないでください。必ず、平坦で安定した場所に置いて使用してください。",
        "本製品の通風孔は、安全上絶対にふさがないでください。また、本製品の各面から5cm以上スペースを空けてください。",
        "充電または給電中は本製品が温かくなります(故障ではありません)、周囲には物を置かないでください。",
        "本製品接続機器のケーブルを差すときは、真っすぐな向きに差してください。",
        "接続機器のケーブルを抜くときは、必ずプラグ部分を持って抜いてください。ケーブルを引っ張ったり折り曲げると、"
        "断線などの原因となります。",
        "給電する機器の充電制御や充電状況、環境などにより給電できない、または急速充電にならない場合があります。",
        "充電または給電中はラジオやチューナー、テレビなどに雑音が入る場合があります。\n"                      # p11
        "雑音が入る場合には、それらの製品から離れた場所でお使いください。",
        "本体が汚れたらコンセントから電源プラグを抜き、柔らかい布で乾拭きしてください。\n"
        "汚れがひどいときは、水または薄めた中性洗剤でふきとってください。シンナーやベンジンなどは絶対に使わないで"
        "ください。",
        "入出力の電力(W)\n"
        "接続機器の消費電力が本製品の出力上限値を超えている場合、電源を自動的に遮断します。消費電力が仕様以下である"
        "ことを確認してから出力ボタンを押してください。",
        "低/高温警報\n"
        "本機は-10°C〜45°C(14〜113°F)の温度範囲でお使いの機器に電力供給が可能となり、本機への蓄電は0°C〜45°C°C"
        "(32〜113°F)で行えます。\n"
        "動作温度が上記範囲外にある場合、本製品が温度異常マークが表示され動作しない可能性がございます。\n"
        "温度異常マークを解除するには、動作温度範囲内の環境に2時間以上置くようにお願い致します。",
        "容量表示に関しては、あくまで参考値となり、電圧により電力が算出され、表示数値にズレが発生することがあります。",
    ))

    # ---- p11 9.同梱品 -----------------------------------------------------------------------
    b.chapter("in_the_box", "9.同梱品", [11])
    slots = ("inbox-unit", "inbox-ac-cable", "inbox-user-manual", "inbox-warranty")
    cards = [{"image_ref": b.figures[s]["local_path"], "label": b.figures[s]["caption"],
              "alt": b.figures[s]["caption"]} for s in slots]
    b.used_figures += list(slots)
    b.comp(inbox_component_spec, inbox_carrier, accessibility_label="9.同梱品", cards=cards,
           tip_label="", tip_body="", require_tip=False, variant="responsive-card-grid")
    b.add(P("**※付属品を故障、紛失等してしまった場合はカスタマーサポートまでご連絡ください。**"))

    # ---- p12 10.免責事項 ---------------------------------------------------------------------
    b.chapter("disclaimer", "10.免責事項", [12])
    b.add(UL(
        "火災、地震、第三者による行為、その他の事故、お客様の故意または過失誤用・誤動作・その他の異常な条件下での使用に"
        "より生じた損害に関して、当社は一切責任を負いません。",
        "付属品と本製品が破損した場合は、ご自身で修理を行わないでください。\n"
        "ご自身で分解・修理したことにより生じた損害に関し、当社は一切責任を負いません。",
        "保証範囲は利用規約に適用され、記載されていない内容は当社の保証範囲外となります。",
        "取扱説明書の記載事項が遵守されないことにより生じた不適合について当社は責任を負いかねます。",
        "本製品の使用、または使用不能から発生する付随的な損害(事業利益損失含む)、当社が関与しない接続機器との組み合わせ"
        "による誤動作などから生じた損害に関して、当社は一切の責任を負いません。",
        "本製品は病院仕様のCPAP（シーバップ）、ECMO（エクモ）、ペースメーカなど、身の安全に関わる医療救急機械の電源と"
        "しての使用、または、消費電力の大きいな設備、例えば核施設設備、スペースシャトル製造などの使用は推薦されません。"
        "上記設備の使用後、火災、機器故障など個人安全を脅かす事故の責任を取りません。",
    ))
    b.add(P("本製品はJackeryアプリケーションによるスマートコントロールに対応しています。\n"
            "ご利用いただくには、下記のアプリストアより「Jackery」で検索して「Jackery アプリ」をダウンロードしてください。"))
    b.figure("app-store-badges")

    # ---- p13-14 Jackeryアプリ ユーザーマニュアル -------------------------------------------
    b.chapter("app_manual", "Jackeryアプリ ユーザーマニュアル", [13, 14])
    b.h("1. アプリをダウンロードしてログインするには")
    b.add(P("Google　PlayまたはApp　Storeで「Jackery」と検索し、アプリをインストールしてください。その後、登録とログインを"
            "行ってください。"))
    b.h("2. デバイスを追加するには")
    before, after = "2.1 APPの右上にあるデバイス追加ボタン", "をクリックします；"
    b.serial += 1
    plus = app_inline_control_component_spec(
        accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
        paragraph_text=f"{before} + {after}", source_ref=f"transcribed-pdf/app_manual/{b.serial}", language="ja",
        metadata={"visual_recovery": "outlined-pdf-vector-plus-control"})
    from tools.manual_ir.components import component_flow_node
    b.add(component_flow_node(plus, carrier_flow=(node("paragraph", [text(before + " "), node("strong", [text("+")]),
                                                                      text(" " + after)]),), root=True))
    b.add(P("2.2 デバイスの主電源ボタンを長押しして電源をいれると、ディスプレー画面にWi-FiとBluetoothのアイコンが点滅し、"
            "デバイスがネットワーク設定モードに入ったことを示します。アイコン点滅中ボタンをクリックし、アプリが近くの"
            "デバイスに接続し、Bluetoothのアクセス許可を開くことを許可します；"))
    b.figure("app-2-1")
    b.figure("app-2-2")
    b.callout("備考", "電源を入れた後、アプリが5分以内接続されていないと、デバイスは自動的にWi-FiとBluetoothをオフにします。"
              "再度Wi-FiとBluetoothをオンにするには、「DC/USBボタン」と「ACボタン」を同時長押しする必要があります。",
              variant="note")
    b.figure("app-buttons")
    b.add(P("2.3 検出されたデバイスアイコンをクリックすると、アプリは自動的にBluetoothでデバイスを接続します。"))
    b.callout("備考", "バインド処理中に「デバイスがバインドされました」と表示された場合は、以下の2つの方法で接続できます：",
              UL("デバイス所有者は、アプリを通じてこのデバイスを他のユーザーと共有します。",
                 "「POWERボタン」と「DC/USBボタン」を3秒間長押ししてデバイスをリセットし、再度バインドしてください。"),  # p14
              variant="note")
    b.add(P("2.4 デバイスが正常に接続されると、デバイスが接続するWi-Fiの名前とパスワードを入力する必要があり、デバイスは"
            "自動的にWi-Fiネットワークに接続します。"))
    b.callout("備考", "2.4GHz帯のWi-Fiネットワークを選択してください。デバイスは、5GHz帯のWi-Fiネットワークには対応して"
              "いません。", variant="note")
    b.add(P("2.5 デバイスのホーム画面でデバイスが正常に追加されると、デバイスのWi-Fi アイコンは常にオンになります。"))
    b.figure("app-2-3")
    b.figure("app-2-4")
    b.figure("app-2-5")
    b.add(P("上記のスクリーンショットはご参考まで。"))
    b.h("3. デバイスのバインドを解除するには")
    b.add(P("デバイスのメインインターフェースの右上隅にある「Setting」（設定）ボタンをクリックして設定ページに入り、ページの"
            "下部にある「Unbind」（バインド解除）ボタンをクリックしてデバイスのバインドを解除します。"))
    b.h("4. ご確認")
    b.add(P("4.1 Wi-FiとBluetoothをオンにするには（ディスプレーにWi-FiとBluetoothのアイコンが点灯）："),
          UL("デバイスがオンになれば自動的にオンになり、ディスプレーにWi-FiとBluetoothのアイコンが点灯します；",
             "上記アイコンが点灯しない場合、ディスプレーにWi-FiとBluetoothのアイコンが点灯するまで、DC/USB出力ボタンと"
             "AC出力ボタンを同時長押しします。"),
          P("4.2 Wi-FiとBluetoothをオフにするには（ディスプレーにWi-FiとBluetoothのアイコンが消える）："),
          UL("ディスプレーにWi-FiとBluetoothのアイコンが消えるまで、DC/USB出力ボタンとAC出力ボタンを同時長押しします；",
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
