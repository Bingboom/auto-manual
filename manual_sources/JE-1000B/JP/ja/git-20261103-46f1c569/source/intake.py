"""Write the JE-1000B JP Japanese semantic document from the reviewed transcription.

Run from the repository root:
``python3 manual_sources/JE-1000B/JP/ja/git-20261103-46f1c569/source/intake.py``.
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

from kit import P, UL, Book, inbox_carrier, inline, pair, spec_carrier  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.manual_tables import symbol_icon_component_spec, symbol_signal_component_spec  # noqa: E402
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


def icon_para(glyph: dict, alt: str, before: str, after: str, body: str, *, bold: bool) -> dict:
    """A printed run-in whose LCD glyph sits inline inside its parentheses (p4, p6)."""
    lead = (lambda value: node("strong", [text(value)])) if bold else text
    tail = [node("line_break"), *inline(body)] if bold else inline(body)
    return node("paragraph", [lead(before), node("image", source=glyph["local_path"], alt=alt), lead(after), *tail])


def item(b: Book, variant: str, label: str, title: str, *body) -> None:
    """One printed 警告/注意 item: bold title, then its body lines (str paragraph or a flow node)."""
    b.callout(label, f"**{title}**", *body, variant=variant)


def make() -> list[str]:
    b = Book(SOURCE, "JE-1000B", "JP", "ja", "Jackery ポータブル電源 1000 Pro 取扱説明書")
    load = lambda name: json.loads((SOURCE / "source" / name).read_text())  # noqa: E731
    glyphs = {g["slot"]: g for g in load("glyphs.json")}

    # ---- p2 1.主な仕様 ---------------------------------------------------------------
    b.chapter("specifications", "1.主な仕様", [2])
    rows = [("製品の名称 :", "Jackery ポータブル電源 1000 Pro"), ("型番 :", "JE-1000B"),
            ("サイズ＆重量 :", "約340 x 262 x 255mm (約11.5kg)"),
            ("定格容量 :", "リチウムイオン電池 23.2Ah/43.2V DC(1002Wh)"),
            ("AC入力 :", "100V~ 50Hz/60Hz, 最大15A"),
            ("DC入力ポート:", f"12-17.5V{DC}8A, 2ポート電流制限16A;\n17.5-60V{DC}11A, 2ポート電流制限22A,合計800W"),
            ("3 x AC出力 :", "100V~ 50Hz/60Hz, 1ポート最大10A/1000W,\n3ポート合計1000W (瞬間最大2000W)"),
            ("2 x USB-A出力 :", f"Quick Charge 3.0, 5-6V{DC}3A, 6-9V{DC}2A, 9-12V{DC}1.5A,\n各ポート最大18W"),
            ("2 x USB-C出力 :", f"5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}5A,\n各ポート最大100W"),
            ("シガーソケット出力 :", f"12V{DC}10A"),
            ("充電温度 :", "0~40 °C (32~104 °F)"), ("動作温度 :", "-10~40 °C (14~104 °F)"),
            ("認証：", "UN38.3")]
    b.comp(spec_table_component_spec, spec_carrier, section_title="【Jackery ポータブル電源 1000 Pro】", rows=rows)
    # The Qualcomm Quick Charge 3.0 mark printed in the 認証 cell (HB-TABLE-SPEC cells carry text only).
    b.figure("cert-quick-charge")
    b.add(P("※USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum.\n"
            "※Qualcomm Quick Charge is a product of Qualcomm Technologies,Inc. and/or its subsidiaries.\n"
            "Qualcomm and Quick Charge are trademarks or registered trademarks of Qualcomm Incorporated."),
          P("**■本機の仕様および外観は、改善のため予告なく変更することがあります。**"))
    # The recycling notice beside its Li-ion 20 mark (declared plain table).
    b.add(plain_table([[node("table_cell", [node("image", source=glyphs["recycle-li-ion"]["local_path"],
                                                  alt="Li-ion 20")], header=False),
                        node("table_cell", [P("**充電式電池のリサイクルについて**"),
                                            P("本機はリサイクル可能な充電池を内蔵しています。\n"
                                              "この商品を廃棄する場合は、当社のカスタマーサポートにご連絡ください。\n"
                                              "充電池の取りはずしはお客様自身では行わないでください。")], header=False)]]))

    # ---- p3 2.各部の名称 ---------------------------------------------------------------
    b.chapter("product_overview", "2.各部の名称", [3])
    b.figure("parts-front")

    # ---- p3-4 3.液晶画面 -----------------------------------------------------------------
    b.chapter("lcd_display", "3.液晶画面", [3, 4])
    b.figure("lcd-screen")
    legend = ["入力電力表示", "充電残り時間", "ソーラー(グリーンエネルギー)充電接続", "AC入力電力表示",
              "シガーソケット入力電力表示", "バッテリー残量警告灯", "バッテリーレベルパーセントタグ", "消費電力パワー",
              "バッテリー使用可能時間", "エラーコード", "高温インジケーター", "低温インジケーター", "低電力モード",  # p4
              "交流電源による出力マーク", "バッテリーアイコン"]
    circled = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮"
    b.comp(reference_table_component_spec, variant="lcd-descriptions", label="3.液晶画面", headers=[],
           rows=[[{"html": circled[i], "text": circled[i]}, {"html": escape(v), "text": v}]
                 for i, v in enumerate(legend)])
    b.add(icon_para(glyphs["lcd-battery-ring"], "バッテリーアイコン", "バッテリーアイコン（", "）：",
                    "本製品の充電時、アイコンは時計回りに回転します。本製品の放電時、アイコンは現在の電力を表示します。",
                    bold=True),
          icon_para(glyphs["lcd-low-battery"], "バッテリー残量警告灯", "バッテリー残量警告灯（", "）:",
                    "バッテリー残量が20%未満の場合は、ローバッテリーランプが表示されます。バッテリー残量が5%未満の場合は、"
                    "ローバッテリーランプが点滅します。バッテリー充電中は、ランプは表示されません。", bold=True),
          icon_para(glyphs["lcd-low-power-mode"], "12H", "低電力モード（", "）:",
                    "使用中に、出力をOFFにするのを忘れてバッテリーがなくなるのを防ぐために、本製品は出荷時、低電力モードを"
                    "OFFに設定しています。接続品がない、または接続されているものが特定の値以下の場合（詳細は下の表を参照）、"
                    "本製品は12時間後に自動的にシャットダウンします。", bold=True))
    shutdown = "12時間後に自動的にシャットダウンします"
    b.add(plain_table(
        [[cell(port), cell(limit), cell(shutdown)]
         for port, limit in (("AC出力ポート", "⩽25W"), ("USB出力ポート", "⩽2W"), ("シガーソケット出力ポート", "⩽2W"))],
        head=[cell("出力ポートタイプ", header=True), cell("電力設定値", header=True), cell("デフォルト設定", header=True)]))
    b.add(P("**低電力モードをONにする手順は次のとおりです:**画面に低電力モードのアイコンが表示されるまで、「AC出力ボタン"
            "+DISPLAY」を長押しします。低電力モードでは、出力を切るのを忘れて電力が不足しないように、本製品を使用しない"
            "ときは電源を切ってください。\n"
            "**低電力モードをOFFにする手順は次のとおりです:**画面に低電力モードのアイコンが消えるまで、「AC出力ボタン"
            "+DISPLAY」を長押しします。"),
          P("**50Hz/60Hz周波数の切り替え:**\n"
            "2つの方法があります。一つは自動識別です。初めてACで充電する時、本体はお客様のお住まいの地域に応じて周波数を"
            "自動的に識別し、対応する出力に自動調整されます。もう一つは手動による調整です。AC出力ボタンを長押しすることで"
            "周波数を切り替えることができ、対応する周波数が画面に表示されます。なお、工場出荷時のデフォルト設定は60Hzに"
            "設定されています。"),
          icon_para(glyphs["lcd-fault-code"], "F8", "故障コード（", "）:",
                    "ユーザーのフィードバックを迅速に解決するために、システムに一般的な故障コードF0-F9を設定しました。"
                    "ディスプレイにF0、F1、F2、F3、F4、F7のいずれかの故障コードが表示されたら、カスタマーサポートに連絡して"
                    "ください。F6コードが発生した場合は、接続機器を外すか、充電プラグを抜けば、製品は自動的に回復します。"
                    "もしできない場合は、カスタマーサポートに連絡してください。F9障害コードが発生した場合は、接続機器を"
                    "外せば、製品は自動的に回復します。もしも回復しない場合は、カスタマーサポートに連絡してください。",
                    bold=True))

    # ---- p5 4.使用について ---------------------------------------------------------------
    b.chapter("usage", "4.使用について", [5])
    b.h("電源ON/OFF")
    b.add(P("**AC出力のON/OFF:**\n"
            "AC出力ボタンを短く押すと、AC出力インジケーターが点灯し、AC電源が必要な機器に給電ができます。AC出力電源"
            "ボタンをもう一度短く押すと、AC出力がOFFになります。"),
          P("**USB出力のON/OFF:**\n"
            "USB出力ボタンを短く押すと、USB出力インジケーターが点灯し、USB Type-AおよびUSB Type-C出力ポートで外部機器"
            "に給電ができます。USB出力ボタンをもう一度短く押すと、出力がOFFになります。"),
          P("**シガーソケット出力のON/OFF:**\n"
            "シガーソケット出力ボタンを短く押すと、シガーソケット出力インジケーターが点灯し、シガーソケット出力ポートが"
            "外部機器に給電ができます。シガーソケット出力ボタンをもう一度短く押すと、出力がOFFになります。"))
    b.h("LCDディスプレイのON/OFF")
    b.add(P("デジタルディスプレイは、任意の出力ボタンまたはLCDスイッチを短く押すことで、画面が点灯します。また充電時も"
            "画面は点灯します。もう一度ボタンを押すと画面は消灯します。また30秒間操作をしない状態が続くと、スリープ状態"
            "となり、表示は自動的に消灯します。充電状態または放電状態で画面を常にONにする必要がある場合の操作手順は次の"
            "とおりです:ディスプレイがONになったら、デジタルディスプレイボタンをダブルクリックすると、画面がコンスタント"
            "ライトモードになります。コンスタントライトモードをオフにする操作手順は次のとおりです: デジタルディスプレイ"
            "ボタンを短く押すと、30秒後に画面が自動的にオフになります。"),
          P("※コンスタントライトモードで充電または給電しない場合、2時間後にディスプレイは自動的に消灯します。"))
    b.h("LEDライトのON/OFF")
    b.add(P("LEDライトには、ローライトモード、ハイライトモード、SOSモードの三つのモードがあります。操作手順は次のとおり"
            "です: LEDライトスイッチを短く押すと、LEDライトがオンになります。デフォルトはローライトモードに設定されて"
            "おり、画面には1Wの出力電力が表示され、もう一度押すとハイライトモードになり、画面には3Wの出力電力が表示され"
            "ます。もう一度押すと、SOSモードになり、画面に出力電力3Wが表示され、もう一度押すと、LEDライトがオフに"
            "なります。いずれかのモードで、LEDライトスイッチを長押しすればLEDライトをオフにすることができます。"))

    # ---- p5-8 5.充電方法 ------------------------------------------------------------------
    b.chapter("charging", "5.充電方法", [5, 6, 7, 8])
    b.add(P("グリーンエネルギー優先モード:本製品はグリーンエネルギー優先モードを搭載していますが、ソーラーACアダプターを"
            "使って同時に充電できます。同時に充電すると、ソーラーが優先されますが、バッテリーの最大許容電力で同時に"
            "充電されます。"))
    high = icon_para(glyphs["lcd-high-temperature"], "高温インジケーター", "高温警告（ ", " ）：",   # p6
                     "環境温度が高温時に表示されます。直射日光などが当たっている場合は移動してください。電池が冷めたら、"
                     "自動的に表示がオフになります。", bold=False)
    low = icon_para(glyphs["lcd-low-temperature"], "低温インジケーター", "低温警告（ ", " ）：",
                    "環境温度が低い場合に表示されます。温度が通常になれば自動的に回復します。", bold=False)
    b.add(node("paragraph", [*high["children"], node("line_break"), *low["children"]]))
    b.callout("ご注意", UL(
        "はじめてお使いになるときは、本製品をフル充電してからご使用ください。",
        "充電池が空の状態で長期保管（3ヶ月-6ヶ月）すると、性能が劣化したり、充電ができなくなる場合があります。"
        "本製品を長期保管する場合には、定期的に60% ~ 80%程度の充電をしてください。"),
        variant="caution")
    b.h("AC充電ケーブル")
    b.add(P("付属のAC充電ケーブルをご使用ください。"))
    b.figure("ac-charging")
    b.h("ソーラー充電")
    b.h("Jackery SolarSaga 60、100、200 の接続操作説明", level=4)
    b.add(P("1枚または2枚のソーラーパネルを接続する場合は、ソーラーパネルDC 8020ポートをJackeryポータブル電源 1000 Pro "
            "のDC 8020ポートに接続して充電することができます。\n"
            "3枚または4枚のソーラーパネルを接続する場合は、下の図のようにソーラーパネル直列アダプターを使って充電して"
            "ください（注意：ソーラーパネル直列アダプターは標準付属品ではなく、別途購入する必要があります。使用前に"
            "ソーラーパネル直列アダプターの詳細な操作説明を参照してください）"))
    b.figure("solar-3-panels")
    b.figure("solar-4-panels")
    b.add(P("**注意：** Jackeryポータブル電源 1000 Proに3枚のソーラーパネルで直列入力をしないでください。接続した場合、"
            "過電圧保護が作動し、充電ができなくなります。"))
    b.h("Jackery SolarSaga 80 接続説明", level=4)                                            # p7
    b.add(P("Jackery SolarSaga 80を購入したユーザーは、下の図のような接続方法を参照して本製品を充電することができます。"
            "Jackery SolarSaga 80は並列に接続、または並列に接続後に直列に接続することによって本製品を充電することが"
            "できます。Jackery ポータブル電源1000 Pro は1つの入力ポートで最大6枚のJackery SolarSaga 80 の入力をサポート"
            "します。６枚で接続する時は2組に分け、1組3枚のJackery SolarSaga 80を並列に接続してからソーラーパネル直列"
            "アダプター（別売り）を通じてポータブル電源を充電してください。\n"
            "Jackery SolarSaga 80の並列接続の詳細な操作説明は、ソーラーパネルの説明書を参照してください。"))
    b.figure("solarsaga80-parallel")
    b.h("DC7909-DC8020トランスジャックの取扱説明", level=4)
    b.add(P("現在販売中のJackery ソーラーパネルにはDC7909-DC8020トランスジャックを付属していますが、お買い上げした"
            "Jackery ソーラーパネルにDC7909-DC8020トランスジャックが付属されていなければ、恐れ入りますが、下記の接続"
            "方法にてJackeryポータブル電源1000 Proに接続して充電してください。"))
    b.figure("transjack-connection")
    b.add(P("**注意：**Jackeryポータブル電源1000 Pro でアダプターを使わずに、3枚の100Wまたは200Wのソーラーパネルの"
            "直列入力をしないでください。過電圧保護が作動し、充電ができなくなります。"))
    b.h("シガーソケット充電")
    b.add(P("本製品は12Vの車のシガーソケットに対応し、充電ができます。車のバッテリーが上がってしまわないように、"
            "エンジンを始動してから、シガーソケットを使用してください。使用の際は車の充電ポートと入力ケーブルのシガー"
            "ライターの接触に問題がないことを確認し、シガーソケットの所定の場所に差し込めることを確認してください。道路"
            "状況が悪くて、車の振動が多い場合は、充電が接触不良になりますので、接触部分が焼損するのを防ぐために、シガー"
            "ソケット充電を中止してください。本製品の誤った取り扱いによる損害が発生しましても当社は一切の責任を負いかね"
            "ます。"))
    b.figure("car-charging")
    b.h("充電に関する安全上のご注意")                                                       # p8
    b.add(P("1) シガーソケット充電は12Vの車専用であり、24Vの車では充電できません。人身傷害や物的損害を避けるため、"
            "本製品の充電に24Vを使用しないでください。\n"
            "2) Jackeryブランド以外の付属品を使用して充電しないでください。特に、ソーラーパネルで充電する際は、Jackery"
            "のソーラーパネルを使用することをお勧めします。他社ソーラーパネルで充電することによる損失について、当社は"
            "一切の責任を負いません。"))

    # ---- p8-9 6.安全上のご注意 ------------------------------------------------------------
    b.chapter("safety", "6.安全上のご注意", [8, 9])
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
            ("火のそばや炎天下の車内、熱器具の周辺など高温（40°C以上）になる場所で使用したり、放置しない",
             "発熱や発火、破裂する原因になります。"),
            ("強い衝撃を与えたり、投げつけたりしない", "発熱や発火、破裂する原因になります。"),
            ("水など、液体を入れたり、濡らしたりしない", "発熱や発火の原因になります。"),
            ("濡れた手で本体や接続するケーブルを触らない", "火災や感電の原因になります。"),
            ("端子部にケーブル以外の金属類を差し込まない", "発熱や発火の原因になります。"),
            ("雷が鳴りだしたら、電源プラグにふれない (充電をしない)", "感電の原因になります。"),
            ("各接続端子には確実に差し込む", "差し込みが不十分だと、発熱したりほこりが付着して火災や感電の原因になります。")):
        item(b, "warning", WARN, title, body)
    item(b, "caution", CAUT, "本製品の上に物を載せたり、不安定な場所に置かない", "倒れたり、落ちたりしてけがの原因になります。")
    item(b, "caution", CAUT,
         "次のような機器では、絶対に使用しないでください。万が一使用中に給電ができなくなった場合、命にかかわる被害が"
         "想定されます。",
         UL("医療機器や使用上、生命に関わるような機器", "社会的、公共的に重要な機器など", "重要な事業用機器など"))
    item(b, "caution", CAUT, "心臓にペースメーカーを装着している方は使用しない", "ペースメーカーが、本製品の影響を受ける恐れがあります。")

    # ---- p10 7.使用上のご注意 -------------------------------------------------------------
    b.chapter("usage_precautions", "7.使用上のご注意", [10])
    b.add(UL(
        "本製品は防塵·防水仕様ではありませんので、ほこりや水、海水などがかからないように注意してください。",
        "ほこりが多い場所や高温多湿の場所での充電および使用、放置をしないでください。",
        "本製品を不安定な場所に置かないでください。必ず、平坦で安定した場所に置いて使用してください。",
        "本製品の通風孔は、安全上絶対にふさがないでください。また、本製品の各面から5cm以上スペースを空けてください。",
        "充電または給電中は本製品が温かくなります(故障ではありません)、周囲には物を置かないでください。",
        "本製品接続機器のケーブルを差すときは、真っすぐな向きに差してください。",
        "接続機器のケーブルを抜くときは、必ずプラグ部分を持って抜いてください。ケーブルを引っ張ったり折り曲げると、"
        "断線などの原因となります。",
        "給電する機器の充電制御や充電状況、環境などにより給電できない、または急速充電にならない場合があります。",
        "充電または給電中はラジオやチューナー、テレビなどに雑音が入る場合があります。\n"
        "雑音が入る場合には、それらの製品から離れた場所でお使いください。",
        "本体が汚れたらコンセントから電源プラグを抜き、柔らかい布で乾拭きしてください。\n"
        "汚れがひどいときは、水または薄めた中性洗剤でふきとってください。シンナーやベンジンなどは絶対に使わないで"
        "ください。",
        "付属のACアダプターは、電源コードの抜き差しで電源が入ったり切れたりするため、異常時に電源コードを容易に抜き"
        "差しできるスペースを空けておいてください。",
        "入出力の電力(W)\n"
        "接続機器の入力仕様が本製品の出力値の上限を超えている場合、電源を自動的に遮断します。消費電力が仕様以下である"
        "ことを確認してから出力ボタンを押してください。",
        "低/高温警報\n"
        "本製品は、-10 ~ 40°C (14 ~104°F)の温度範囲でお使いの機器に電力を供給できます。\n"
        "動作温度が上記範囲外にある場合、本製品が動作しないことがあります。",
        "容量表示に関しては、あくまで参考値となり、電圧により電力が算出され、表示数値にズレが発生することがあります。",
    ))

    # ---- p11 8.同梱品 -----------------------------------------------------------------------
    b.chapter("in_the_box", "8.同梱品", [11])
    slots = ("inbox-main-unit", "inbox-car-adapter", "inbox-ac-cable", "inbox-pouch", "inbox-transjack",
             "inbox-manual", "inbox-warranty")
    cards = [{"image_ref": b.figures[s]["local_path"], "label": b.figures[s]["caption"],
              "alt": b.figures[s]["caption"]} for s in slots]
    b.used_figures += list(slots)
    b.comp(inbox_component_spec, inbox_carrier, accessibility_label="8.同梱品", cards=cards,
           tip_label="", tip_body="", require_tip=False, variant="responsive-card-grid")
    b.add(P("※付属品を故障、紛失等してしまった場合はカスタマーサポートまでご連絡ください。"))

    # ---- p12 9.免責事項 ---------------------------------------------------------------------
    b.chapter("disclaimer", "9.免責事項", [12])
    b.add(UL(
        "火災、地震、第三者による行為、その他の事故、お客様の故意または過失\n"
        "誤用・誤動作・その他の異常な条件下での使用により生じた損害に関して、当社は一切責任を負いません。",
        "付属品と本製品が破損した場合は、ご自身で修理を行わないでください。\n"
        "ご自身で分解・修理したことにより生じた損害に関し、当社は一切責任を負いません。",
        "保証範囲は利用規約に適用され、記載されていない内容は当社の保証範囲外となります。",
        "取扱説明書の記載事項が遵守されないことにより生じた不適合について当社は責任を負いかねます。",
        "本製品の使用、または使用不能から発生する付随的な損害(事業利益損失含む)、当社が関与しない接続機器との組み合わせ"
        "による誤動作などから生じた損害に関して、当社は一切の責任を負いません。",
        "本製品は個人の安全に関係する製品、消費電力の大きな設備に給電できません。例えば、医療機器、核施設設備、CPAP"
        "（シーパップ）、スペースシャトルの製造などです。\n"
        "上記の設備、用途で使用した結果、火災、機器故障など個人の安全を脅かす事故が生じた場合、当社は一切責任を負い"
        "ません。",
    ))

    problems = b.finish()
    print("chapters", len(b.chapters), "problems", problems)
    return problems


if __name__ == "__main__":
    if make():
        raise SystemExit("figure records and transcription disagree")
