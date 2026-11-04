"""Write the JE-300C JP Japanese semantic document from the reviewed transcription.

Run from the repository root:
``python3 manual_sources/JE-300C/JP/ja/git-20261103-890abb4a/source/intake.py``.
It writes ``source/ja/content.json``. ``original.pdf`` is outlined (no text
layer), so every Japanese line below is transcribed from 300 dpi renders of the
named physical page (500-600 dpi clips for small or ambiguous glyphs) and kept as
printed, including full/half-width punctuation. Every printed block maps to a
shared component or plain shared flow (``source_manifest.json:component_map``);
no package class, inline style or plain table. The cover (p1) and the table of
contents (p2) are not Web content.
"""
from pathlib import Path
import json
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kit import OL, P, UL, Book, blocks, inline, inbox_carrier, pair, spec_carrier  # noqa: E402,F401
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.lcd_mode import lcd_mode_component_spec  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
    troubleshooting_component_spec,
)
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import warranty_section_component_spec  # noqa: E402
from tools.web.frozen_ai_flow import node, text  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
DC = "⎓"  # the print's DC symbol


def panel(*children) -> dict:
    """Shared grey text panel (web_manual.css ``.hb-text-panel``) for the print's grey text boxes."""
    flow = [P(c) if isinstance(c, str) else c for c in children]
    return node("group", flow, role="container",
                presentation={"html": {"attributes": {"class": "hb-text-panel"}}})


def strong(value: str) -> dict:
    return P("**" + value + "**")


def icon_line(ref: str, alt: str, after: str) -> dict:
    """A printed line that starts with an LCD glyph drawn inline (the 6H mark)."""
    return node("paragraph", [node("image", source=ref, alt=alt), text(after)])


def item(title: str, *body, lists=()) -> list[dict]:
    """One pictogram-grid row: the bold printed title, then its body lines."""
    flow = [strong(title)]
    flow += [UL(*items) for items in lists]
    flow += [P(b) for b in body]
    return flow


def make() -> list[str]:
    b = Book(SOURCE, "JE-300C", "JP", "ja", "Jackery ポータブル電源 300 New · JE-300C")
    load = lambda name: json.loads((SOURCE / "source" / name).read_text())  # noqa: E731

    # ---- p3-5 安全上のご注意 (printed 01-03) ---------------------------------------------
    b.chapter("safety", "安全上のご注意", [3, 4, 5])
    b.add(strong("ご使用の前にこの「安全上のご注意」をよくお読みのうえ、正しくお使いください。"))
    b.h("絵表示について")
    b.add(P("製品を安全に正しくお使いいただき、お客様や他の方々への危害や財産への損害を未然に防止するための表示です。\n"
            "内容をよく理解してから本文をお読みください。"))
    rows = [{"label": label, "show_icon": icon, **pair(meaning, "meaning")} for label, icon, meaning in [
        ("警告", True, "この表示を無視して、誤った取り扱いをすると、人が死亡または重傷を負う可能性が想定される内容を示しています。"),
        ("注意", True, "この表示を無視して、誤った取り扱いをすると、人が傷害を負う可能性が想定される内容または物的損害の発生が"
                       "想定される内容を示しています。"),
        ("説明", False, "この表示を無視して誤った取り扱いをすると、機器の損傷、データの消失、性能の低下、または予期しない動作が"
                        "発生する可能性があることを示しています。"),
        ("ヒント", False, "文章内の重要な情報や操作のヒントを補足する内容を示しています。"),
    ]]
    # Component chrome: the shared signal table requires two column headers (JE-1000D/JE-1500D JP V2 wording).
    b.comp(symbol_signal_component_spec, accessibility_label="絵表示について",
           headers=[pair("表示", "content"), pair("意味", "content")], rows=rows)
    b.h("絵表示の説明")
    symbols = load("symbols.json")
    table_rows = [r for r in symbols if r["physical_page"] == 3]
    panels = [[], []]
    for index, row in enumerate(table_rows):
        meaning = pair(row["meaning"], "meaning")
        panels[0 if row["glyph_search_box"][0] < 100 else 1].append(
            {"asset_index": index, "icon_alt": meaning["meaning_text"], **meaning})
    headers = [pair(v, "content") for v in ("記号", "意味", "記号", "意味")]
    b.comp(symbol_icon_component_spec, accessibility_label="絵表示の説明", headers=headers,
           panels=panels, icon_refs=[r["local_path"] for r in table_rows])
    # p4: the recycling and WEEE rows (a separate two-row symbol table in the print).
    recycle = [r for r in symbols if r["physical_page"] == 4]
    li_ion, weee = recycle
    li_meaning = pair("**充電式電池のリサイクルについて**\n" + li_ion["meaning"].split("\n", 1)[1], "meaning")
    weee_meaning = pair(weee["meaning"], "meaning")
    b.comp(symbol_icon_component_spec, accessibility_label="充電式電池のリサイクルについて", headers=headers,
           panels=[[{"asset_index": 0, "icon_alt": "Li-ion 32", **li_meaning}],
                   [{"asset_index": 1, "icon_alt": weee_meaning["meaning_text"], **weee_meaning}]],
           icon_refs=[r["local_path"] for r in recycle])

    # p4 警告 pictogram grid: left table, then right table; one shared callout per row.
    warn = [
        item("火のそばや炎天下の車内、熱器具の周辺など高温（45°C以上）になる場所で使用したり、放置しない",
             "発熱や発火、破裂する原因になります。"),
        item("強い衝撃を与えたり、投げつけたりしない", "発熱や発火、破裂する原因になります。"),
        item("水など、液体を入れたり、濡らしたりしない", "発熱や発火の原因になります。"),
        item("濡れた手で本体や接続するケーブルを触らない", "火災や感電の原因になります。"),
        item("端子部にケーブル以外の金属類を差し込まない", "発熱や発火の原因になります。"),
        item("雷が鳴りだしたら、電源プラグにふれない (充電をしない)", "感電の原因になります。"),
        item("各接続端子には確実に差し込む", "差し込みが不十分だと、発熱したりほこりが付着して火災や感電の原因になります。"),
        item("接地接続は必ず、電源プラグを電源につなぐ前に行って下さい",
             "また、接地接続を外す場合は、必ず電源プラグを切り離してから行って下さい。"),
    ]
    for body in warn:
        b.callout("警告", *body, variant="warning")
    # p5 警告 table
    b.callout("警告", *item("万が一、次のような異常が発生したときはすぐに使用をやめる",
                            lists=[("煙が出ている、異臭がする", "落としたり、破損したとき", "異音がする",
                                    "内部に水や異物が入ったとき", "電源コード (AC充電ケーブル) が傷んだとき")]),
              P("このような異常が発生したまま使用していると、火災や感電の原因になります。\n"
                "すぐにAC充電ケーブルをコンセントから抜いてください。また、本製品に接続されている機器もすべて外してください。"),
              strong("万が一発煙や発火したら、大量の水で消火して煙が見えなくなるまで本製品を水浸しにしてください。"),
              P("煙が出なくなることを確認してからカスタマーサポートにご連絡ください。\n"
                "お客様による修理は危険ですので絶対におやめください。"), variant="warning")
    for body in [
        item("分解、改造しない", "故障、発熱、火災·感電の原因になります。"),
        item("表示された電源電圧以外で使用しない",
             "故障、発熱、火災·感電の原因になります。また、本製品を使用できるのは日本国内のみです。"),
        item("付属品と本製品が破損した場合は、ご自身で修理をしない"),
    ]:
        b.callout("警告", *body, variant="warning")
    # p5 注意 table
    for body in [
        item("本製品の上に物を載せたり、不安定な場所に置かない", "倒れたり、落ちたりしてけがの原因になります。"),
        item("データサーバや医療機器など、非常時に不具合が起こると人命 / 財産に重大な危険を及ぼしうる用途でのご使用は"
             "お控えください。次のようなような機器では、万が一使用中に給電ができなくなった場合、人命 / 財産にかかわる"
             "被害が想定されます。",
             lists=[("医療機器や使用上、生命に関わるような機器", "社会的、公共的に重要な機器など", "重要な事業用機器など")]),
        item("心臓にペースメーカーを装着している方は使用しない", "ペースメーカーが、本製品の影響を受ける恐れがあります。"),
        item("本製品を積み重ねたり、上に他の物を置いたりしないでください。落下して怪我をする場合があります。"),
    ]:
        b.callout("注意", *body, variant="caution")

    # ---- p6-7 使用上のご注意 (printed 04-05) ------------------------------------------------
    b.chapter("usage_precautions", "使用上のご注意", [6, 7])
    b.add(panel(
        "Jackery ポータブル電源 300 Newは、定格出力300Wです。通常時で消費電力が300Wまでの機器に給電ができるため、"
        "多くの電化製品や端末に対応可能です。ただし、電気モーターを搭載している製品（掃除機、ポンプ、冷蔵庫、電動丸ノコ、"
        "エアコン、洗濯機、電子レンジ、ドライヤーなど)は、起動時に「誘導負荷」が発生し、公称電力の3~7倍の電力が必要となります。",
        "定格出力300Wは、一定の電力で動く機器への出力可能範囲を指しています。",
        "300Wの出力を超えた場合は、電気回路が自動的に調整され、電力が低減、または保護機能が作動し自動で遮断することがあります。",
        "またAC出力ポート2つ搭載されておりますが、2つ同時にご利用頂く場合、合計して300W以内であることをご確認の上"
        "ご利用ください。"))
    b.callout("ご注意", "始動電力が出力上限値 ( 定格出力 ) を大幅に超える可能性のある製品のご利用や、定格出力を超え給電が"
              "ストップした製品を繰り返し利用することはポータブル電源のバッテリーが損傷するリスクがありますのでお控えください。",
              variant="caution")
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
    b.h("接続時の注意事項")                                                              # p7
    b.add(UL("ケーブルを接続する際は、まっすぐに差し込んでください。",
             "抜く際は必ずプラグ部分を持って抜いてください。ケーブルを引っ張ったり折り曲げたりしないでください。"))
    b.h("お手入れについて")
    b.add(UL("本体が汚れた場合は、電源プラグを抜いた状態で、柔らかい布で乾拭きしてください。",
             "汚れがひどい場合は、水または薄めた中性洗剤で拭き取ってください。",
             "シンナーやベンジンなどの使用は絶対に使わないでください。"))
    b.h("入出力・温度・表示に関するご注意")
    b.add(UL("接続機器の入力が本製品の出力上限を超えている場合、自動で電源が遮断されます。",
             ("本機は -15°C~45°C の温度範囲でお使いの機器に電力供給が可能となり、本機の蓄電は 0°C~45°C で行えます。",
              UL("動作温度が上記範囲外にある場合、本製品が温度異常マークが表示され、動作しない可能性があります。",
                 "温度異常マークが表示された場合は、本製品を 2 時間以上、動作温度範囲内の環境に置いてください。")),
             "容量表示は参考値であり、電圧により表示数値と実際の容量に差異が出る場合があります。"))

    # ---- p7 免責事項 (printed 05) -------------------------------------------------------------
    b.chapter("disclaimer", "免責事項", [7])
    b.add(panel(UL(
        "火災、地震、第三者による行為、その他の事故、お客様の故意または過失誤用・誤動作・その他の異常な条件下での使用により"
        "生じた損害に関して、当社は一切責任を負いません。",
        "付属品と本製品が破損した場合は、ご自身で修理を行わないでください。ご自身で分解・修理したことにより生じた損害に関し、"
        "当社は一切責任を負いません。",
        "保証範囲は利用規約に適用され、記載されていない内容は当社の保証範囲外となります。",
        "取扱説明書の記載事項が遵守されないことにより生じた不適合について当社は責任を負いかねます。",
        "本製品の使用、または使用不能から発生する付随的な損害 ( 事業利益損失含む )、当社が関与しない接続機器との組み合わせ"
        "による誤動作などから生じた損害に関して、当社は一切の責任を負いません。",
        "本製品は病院仕様のシーパップ（CPAP）、エクモ（ECMO）、ペースメーカなど、身の安全に関わる医療救急機械の電源としての"
        "使用、または、消費電力の大きいな設備、例えば核施設設備、スペースシャトル製造などの使用は推薦されません。上記設備の"
        "使用後、火災、機器故障など個人安全を脅かす事故の責任を取りません。")))

    # ---- p8 同梱品 (printed 06) -------------------------------------------------------------
    b.chapter("in_the_box", "同梱品", [8])
    slots = ("inbox-unit", "inbox-ac-cable", "inbox-user-manual")
    cards = [{"image_ref": b.figures[slot]["local_path"], "label": b.figures[slot]["caption"],
              "alt": b.figures[slot]["caption"]} for slot in slots]
    b.used_figures += list(slots)
    b.comp(inbox_component_spec, inbox_carrier, accessibility_label="同梱品", cards=cards,
           tip_label="", tip_body="", require_tip=False)
    b.add(P("※ 付属品を故障、紛失等してしまった場合はカスタマーサポートまでご連絡ください。"),
          P("※ AC充電ケーブルは、同梱されている本体以外には使用しないでください。"),
          P("※ シガーソケット充電ケーブルは別売りです。Jackery公式サイトよりご購入いただけます。サポートが必要な場合は、"
            "Jackeryカスタマーサポートまでお問い合わせください。"),
          strong("■本機の仕様および外観は、改善のため予告なく変更することがあります。"))

    # ---- p9 各部の名称 (printed 07) -------------------------------------------------------------
    b.chapter("product_overview", "各部の名称", [9])
    b.h("正面")
    b.figure("overview-front")
    b.h("右側面")
    b.figure("overview-right")

    # ---- p10-11 液晶画面 (printed 08-09) -------------------------------------------------------
    b.chapter("lcd_display", "液晶画面", [10, 11])
    b.figure("lcd-display")
    glyphs = {g["slot"]: g["local_path"] for g in load("glyphs.json")}
    names = [
        ("①", "UPS機能", "点灯時：製品が給電と充電を同時に行う「パススルー充電」状態にあります。停電時には家庭用電源から"
         "ポータブル電源の切り替え時間が10ミリ秒で行われます。\n消灯時：製品がパススルー充電状態ではありません。", "lcd-ups"),
        ("②", "交流電源による出力マーク\n(正弦波)", "AC出力（純正弦波）がオンになっています。", "lcd-ac-power"),
        ("③", "出力電圧と周波数", "出力される電圧と周波数を表示します。", "lcd-output-voltage"),
        ("④", "入力電力表示", "入力電力をワットで表示します。", "lcd-input-power"),
        ("⑤", "消費電力", "出力電力をワットで表示します。", "lcd-output-power"),
        ("⑥", "AC入力電力表示", "製品は、系統電力を使用し、AC入力を介して充電されます。", "lcd-ac-wall-charging"),
        ("⑦", "シガーソケット入力電力表示", "製品は、DC 12V（カーチャージ）を使用し、8020入力ポートを介して充電されています。",
         "lcd-car-charging"),
        ("⑧", "ソーラー(グリーンエネルギー)\n充電接続", "製品は、ソーラーパネルを使用し、8020入力ポートを介して充電されています。",
         "lcd-solar-charging"),
        ("⑨", "バッテリーレベルパーセントタグ", "製品の充電中は、バッテリーのパーセンテージを囲むオレンジ色の円が順番に点灯します。"
         "他のデバイスの充電時には、オレンジ色の円は点灯したままになります。", "lcd-battery-power"),
        ("⑩", "バッテリーレベルパーセントタグ", "バッテリー残量を表示します。", "lcd-battery-percentage"),           # p11
        ("⑪", "エラーコード", "製品エラーが発生しました。詳細については、トラブルシューティングのセクションを参照してください。",
         "lcd-fault-code"),
        ("⑫", "高温インジケーター", "高温保護が作動しました。製品の温度が通常の動作範囲に戻るまで、製品の機能が停止する場合が"
         "あります。", "lcd-temperature"),
        ("⑫", "低温インジケーター", "低温保護が作動しました。製品の温度が通常の動作範囲に戻るまで、製品の機能が停止する場合が"
         "あります。", "lcd-temperature"),
        ("⑬", "省エネモード", "**アイコン表示：**省エネモードがオンになっています。\n**アイコン消える：**省エネモードがオフに"
         "なっています。", "lcd-energy-saving"),
    ]
    rows = [{**pair(number, "number"), **pair(name, "name"), **pair(description, "description"),
             "icon_alt": " ".join(name.split()), "asset_index": index}
            for index, (number, name, description, _) in enumerate(names)]
    # ⑫ prints one thermometer icon and one number cell for both temperature rows.
    b.comp(lcd_icon_component_spec, accessibility_label="液晶画面", rows=rows,
           icon_refs=[glyphs[slot] for *_, slot in names], icon_locale_policy="exact",
           metadata={"number_cell_layout": "span-adjacent-equal"})

    # ---- p11-14 使い方 (printed 09-12) ----------------------------------------------------------
    b.chapter("operations", "使い方", [11, 12, 13, 14])
    b.h("主電源ボタン/オフ")
    b.figure("power-on-off")
    b.add(panel("本製品のデフォルトの待機時間は2時間です(充電または放電がない場合、2時間後に自動的にシャットダウンします）。\n"
                "省エネモードがオンのとき、AC出力またはUSB出力がオンでも、6時間連続して充放電が行われない場合は、自動的に"
                "電源がオフになります。"))
    b.h("USB/カーポート出力オン/オフ")                                                   # p12
    b.add(P("**前提：**主電源ボタンがオンになっていることを確認してください。"))
    b.figure("dc-usb-output")
    b.callout("ご注意", P("USB-C 100Wは、USB-PD Power Source 3 (PS3) の高出力ポートです。接続されたユーザーデバイスまたは"
                          "アクセサリーが安全基準を満たしていない場合、火災の危険性があります。これらのポートを使用する前に、"
                          "接続するデバイスまたはアクセサリーに耐火安全保護が備わっていることを確認してください。"),
              UL("Jackery ポータブル電源 300 Newは、IEC/EN/UL 62368-1（または同等の規格）の6.3、6.4、6.5条に準拠した"
                 "デバイスまたはアクセサリーのみに接続してください。",
                 "最大出力を得るためには、公式のJackery USB-C to USB-C 5Aケーブル（20V DC/5A、100W）を使用してください。"),
              variant="caution")
    b.add(P("本製品は、別売のJackery 12V 自動車用バッテリー充電ケーブルを使用することで、車のバッテリーへの充電が可能です。\n"
            "※Jackery 12V 自動車用バッテリー充電ケーブルは付属しておりません。Jackery公式サイトよりお求めいただけます。"))
    b.callout("ご注意", UL("12V車専用であり、24V車には対応しておりません。",
                           "本製品の12V DC出力（シガーソケット）から車のバッテリーへ充電中は、エンジンを始動しないでください。"
                           "製品の故障につながる恐れがあります。",
                           "この機能はあくまで車のバッテリーの緊急補助用であり、深刻なバッテリー上がりや故障したバッテリーには"
                           "対応しておりません。"), variant="caution")
    b.h("AC出力のオン/オフ")                                                              # p13
    b.add(P("**前提：**主電源ボタンがオンになっていることを確認してください。"))
    b.figure("ac-output")
    b.h("LEDライト")
    b.add(P("LEDライトには、照明モードとSOSモードの2つのモードがあります。いずれのモードでも、LEDスイッチを長押しすることで"
            "LEDライトを消灯できます。"))
    b.figure("led-light")
    b.h("LCDディスプレイ")
    b.used_figures.append("lcd-screen")
    groups = [{**pair(state, "state"), "actions": [{**pair(a, "action"), **pair(d, "description")} for a, d in acts]}
              for state, acts in [
        ("画面は2分間点灯し続けます", [("オンにする", "主電源ボタンを押すか、充電入力がある場合。"),
                                      ("オフにする", "主電源ボタンを押します。"),
                                      ("自動オフ", "2分間操作がないとLCDは自動的に消灯し、スリープモードになります。")]),
        ("常時点灯表示モード\n（充電または放電状態）",
         [("オンにする", "LCD画面がオンのときに主電源ボタンを2回押します。"),
          ("オフにする", "主電源ボタンを押します。"),
          ("自動オフ", "常時点灯ディスプレイモードは、2時間操作がないと自動的に消灯します。")]),
    ]]
    b.comp(lcd_mode_component_spec, accessibility_label="LCDディスプレイ", groups=groups,
           artwork_ref=b.figures["lcd-screen"]["local_path"], artwork_locale_policy="exact")
    b.h("省エネモード")                                                                   # p14
    on, off = glyphs["eco-icon-on"], glyphs["eco-icon-off"]
    b.add(panel(strong("【動作条件】"), strong("●省エネモードON設定時："), UL("低出力状態継続6時間→全出力自動OFF"),
                icon_line(on, "6H", " アイコン表示"),
                strong("●省エネモードOFF設定時："), UL("自動OFF機能無効"),
                icon_line(off, "6H", " アイコン消える"),
                P("アイコンの表示時間は、設定された省エネ時間に応じて変わります。"),
                strong("●オンとオフの設定方法："), UL("手動設定は下記画像にてご参照"),
                strong("【機能目的】"),
                P("バッテリーの無駄な消耗を防ぐ自動電源OFF機能\n"
                  "※本機能をご利用になる場合は、省エネモードを手動でONに設定してください"),
                strong("※ 低出力状態の定義："),
                UL("AC出力が25W以下", "DC出力（USB＋シガーソケット出力）が2W以下")))
    b.figure("energy-saving")
    b.callout("ご注意", UL("はじめてお使いになるときは、本製品をフル充電してからご使用ください。",
                           "低消費電力の機器をご使用の場合は、出力が途中で切れないよう、省エネモードを「オフ」にしてください。"),
              variant="caution")
    b.h("50Hz/60Hz周波数の切り替え", level=4)
    b.add(panel("※ 工場出荷時のデフォルト設定は60Hzに設定されています。\n"
                "自動識別: お客様のお住まいの地域に応じて周波数を自動的に識別し、対応する出力に自動調整されます。\n"
                "手動調整: AC出力ボタンを長押しすることで周波数を切り替えることができ、対応する周波数が画面に表示されます。"))
    b.figure("frequency-switch")

    # ---- p15 UPS 機能 (printed 13) -------------------------------------------------------------
    b.chapter("ups", "UPS 機能", [15])
    b.figure("ups")
    b.add(panel(
        "本製品は、電気系統（家庭内の電源など）が突然停止した場合、自動的にバッテリー給電モードに切り替わる UPS（無停電電源"
        "装置）機能を備えています。切替時間は約 10 ミリ秒（0.010 秒）以内です。",
        "ただし、本機能は 0ms での完全な無停止給電には対応しておりません。そのため、以下のような高精度な連続電源供給を必要と"
        "する機器への接続はお控えください：",
        UL("データサーバー", "ワークステーション", "医療機器など",
           "その他、停電・瞬断の許容時間が 10ms 以下の精密機器／業務機器全般"),
        "これらの機器でご使用を希望される場合は、事前に複数回の動作テストを実施し、機器との互換性をご確認の上でご使用ください。",
        "※記載の手順に従わずに機器が正常に動作しなかったり、データ消失などの損害が発生した場合、弊社では責任を負いかねます。"
        "あらかじめご了承ください。",
        "UPS として使用している際はパススルー機能により充電と出力が同時に行われている状態のため、ポータブル電源の最大出力は "
        "300W に制限され、停電時には定格出力に戻ります。複数の機器を UPS モードで同時に接続する場合は、合計負荷電力が"
        "バイパス時の最大出力（300W）を超えないようにしてください。超えると、機器が過負荷保護により停止するおそれがあります。"))

    # ---- p16-18 充電方法 (printed 14-16) --------------------------------------------------------
    b.chapter("charging", "充電方法", [16, 17, 18])
    b.add(strong("グリーンエネルギー優先モード:"),
          P("本製品はグリーンエネルギー優先モードを搭載していますが、ソーラーパネルとAC充電ケーブルを使って同時に充電できます。"
            "同時に充電すると、ソーラーが優先されますが、バッテリーの最大許容電力で同時に充電されます。"))
    b.callout("ご注意", UL("製品の充電動作温度範囲は 0°C~45°C、放電動作温度範囲は -15°C~45°Cです。上限・下限温度を超えた場合、"
                           "充放電が制限され、または充放電不可の可能性があります。",
                           "温度によって、製品の充電効率と実際の容量は異なります。"), variant="caution")
    b.callout("ご注意", UL("はじめてお使いになるときは、本製品をフル充電してからご使用ください。",
                           "充電池は空の状態で長期保管 (3 カ月 ~6 カ月）すると、性能が劣化したり、充電できなくなる場合があります。",
                           "長期保管中は、電池残量が 0%にならないよう、3 か月に一度の充電をおすすめします。"),
              variant="caution")
    b.h("AC充電ケーブル")
    b.add(P("コンセントよりJackery ポータブル電源 300 New 本体に充電する場合、電流容量が大きいため、他機器と併用したり途中接続を"
            "すると、コンセントの電流上限値を超え充電停止したり、配線やコンセント・接続部が発熱し、火災の原因となる恐れが"
            "あります。必ず電源タップなどを介して他の電気製品と併用しないでください。"))
    b.figure("charging-ac")
    b.callout("ご注意", "AC 充電ケーブルのプラグが製品の AC 入力ポートにしっかりと、かつ完全に差し込まれていることを確認して"
              "ください。差し込みが不完全な場合、電流の不安定、発熱、接触不良などが発生し、機器の正常な動作に支障をきたす恐れが"
              "あります。", variant="caution")
    b.h("USB-C充電ケーブル")                                                              # p17
    b.add(P("壁用充電器を準備してください。"))
    b.callout("ご注意", "USB-C ポートから充電する場合、本製品は最大 100W に対応しています。そのためには、100W に対応した PD "
              "充電器とケーブルの両方が必要です。", variant="caution")
    b.figure("charging-usbc")
    b.h("ソーラー充電")
    b.add(P("ソーラーパネル接続用のDC入力ポート（8020メス）を搭載しており、最大入力電力は100Wです。"),
          strong("直接接続可能です。"),
          P("追加のアクセサリーは不要です。\n"
            "本製品のDC入力ポートは「8020メス」です。ソーラーパネル側の「8020オス」と接続してください。"))
    b.figure("charging-solar")
    b.add(P("Jackery ブランド以外の付属品を使用して充電しないでください。特に、ソーラーパネルで充電する際は、Jackery の"   # p18
            "ソーラーパネルを使用することをお勧めします。ソーラーパネルの開放電圧（Voc）が、Jackery ポータブル電源 300 New の"
            " DC 入力電圧範囲（16V～28V）内に収まっていることを確認してください。他社ソーラーパネルで充電することによる損失に"
            "ついて、当社は一切の責任を負いません。"))
    b.h("シガーソケット充電")
    b.add(strong("本製品は、12V/10A 出力の車載シガーソケットからの充電に対応しています。"),
          P("ご使用の際は、以下にご注意ください："),
          UL("必ず車のエンジンを始動させてから接続してください。エンジン停止状態で使用すると、車両のバッテリーが上がる恐れが"
             "あります。",
             "車の充電ポートとシガーソケット充電ケーブルの接触状態をご確認ください。",
             "ケーブルが確実に奥まで差し込まれていることをご確認ください。",
             "悪路などで車両の振動が激しい場合は、接触不良や発熱・焼損の恐れがあるため、充電を中止してください。",
             "誤使用による故障・損傷については、弊社では責任を負いかねます。あらかじめご了承ください。"))
    b.figure("charging-car")
    b.callout("ご注意", UL("シガーソケット充電とソーラー充電を同時に使用しないでください。同時に使用すると、車のヒューズが損傷"
                           "する可能性があります。",
                           "シガーソケット充電は 12V, 10A 車専用で、24V 車は充電できません。人身傷害や物的損害を避けるため、"
                           "本製品の充電に 24V 車を使用しないでください。"), variant="caution")

    # ---- p19 トラブルシューティング (printed 17) -----------------------------------------------
    b.chapter("troubleshooting", "トラブルシューティング", [19])
    b.add(P("次のいずれかのエラーコードが表示された場合は、記載されている対処方法に従って問題を解決してください。問題が解決しない"
            "場合は、Jackery カスタマーサポートまでご連絡ください。"))
    lines = lambda *items: pair("\n".join(items), "measures")  # noqa: E731

    def icon_code(slot: str, alt: str) -> dict:
        return {"code_html": f'<img src="{glyphs[slot]}" alt="{alt}"/>', "code_text": alt}
    rows = [
        {**pair("F0 / F1\nF2 / F3", "code"), **pair("製品を再起動してください。", "measures")},
        {**pair("F4", "code"), **pair("製品に負荷を接続してバッテリーを放電し、エラーが消えるまで続けてください。", "measures")},
        {**pair("F5", "code"), **pair("ソーラーパネルまたはAC電源コンセントを使用して、エラーが消えるまで製品を充電してください。",
                                      "measures")},
        {**pair("F6", "code"), **lines(
            "1. AC 電源コンセントから充電する前に、電力グリッドが安定するのを待ってください。",
            "2. 吸気口および排気口が塞がれていないか確認し、製品の両側に 30cm のスペースを確保してください。",
            "3. 製品は日陰で通気の良い場所に設置し、周囲温度が 45°C未満であることを確認してください。",
            "4. 製品からすべての負荷を取り外し、アイドル状態にして、エラーが消えるまで待ってください。ご使用の機器の起動時消費"
            "電力が本製品の出力範囲を超えていないかをご確認ください。",
            "5. 製品を再起動してください。")},
        {**pair("F7", "code"), **lines(
            "1. 製品からすべてのDC入力を取り外してください。",
            "2. ソーラーパネルで充電する場合は、接続されたソーラーパネルの開放電圧（Voc）を確認してください。本製品の最大DC"
            "入力電圧は28Vです。",
            "3. 製品を再起動し、アイドル状態を保ってください。エラーが消えるまで待ってください。")},
        {**pair("F8", "code"), **pair("販売店またはJackeryカスタマーサポートにお問い合わせください。", "measures")},
        {**pair("F9", "code"), **pair("製品のDC 12V出力ポート/USBポートに接続されている負荷を取り外してください。故障が消えるまで"
                                      "待機してください。", "measures")},
        {**icon_code("ts-high-temperature", "高温インジケーター"), **lines(
            "1.製品へのすべての充電·放電ケーブル（壁用充電器、ソーラーパネル、車載充電器、負荷機器を含む）を切り離してください。",
            "2.製品を日陰で風通しの良い場所に設置し、周囲温度が45°C以下であることを確認してください。",
            "3.吸気口および排気口が塞がれていないか確認し、製品の両側に30cmの空間を確保してください。",
            "4. 製品をアイドル状態にし、故障が消えるまで待ってください。")},
        {**icon_code("ts-low-temperature", "低温インジケーター"), **lines(
            "1.製品を0°C以上の暖かい環境へ移動させてください。",
            "2.極端に寒い屋外での使用や充電は行わないでください。必要に応じて、室内で予熱してください。",
            "3.製品を寒い環境から室内に移動させた場合は、使用前にしばらく放置してください。",
            "4. 低温インジケーターが表示された場合は、製品をアイドル状態にして、システムが自動的に回復するのを待ってください。")},
    ]
    b.comp(troubleshooting_component_spec, headers=[pair("エラーコード", "content"), pair("対処方法", "content")],
           rows=rows)

    # ---- p20 主な仕様 (printed 18) -------------------------------------------------------------
    b.chapter("specifications", "主な仕様", [20])
    usb100 = f"100W: 5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}5A, 最大100W"
    for title, rows in [
        ("基本情報", [("製品の名称", "Jackery ポータブル電源 300 New"), ("型番", "JE-300C"),
                     ("バッテリータイプ", "LiFePO₄（リン酸鉄リチウムイオン電池）"),
                     ("定格容量", "288Wh (15Ah/19.2V DC)"), ("サイズ＆重量", "約231×153×167.7 mm (約3.7 kg)"),
                     ("サイクル寿命", "4,000回の充放電後も容量の70%以上を維持")]),
        ("入力ポート", [("AC入力ポート", "100V-120V~ 50Hz/60Hz, 最大15A, 最大300W①"),
                       ("DC8020入力ポート", f"PV：16V-28V{DC}最大6A, 最大100W"),
                       ("", f"シガーソケット：11V-16V{DC}最大6A，最大96W"),
                       ("USB-C入力ポート", usb100)]),
        ("出力ポート", [("2×AC出力", "100V~ 50/60Hz, 3A, 300W"),
                       ("AC出力（パススルー)②", "100V-120V~ 50Hz/60Hz, 最大300W"),
                       ("USB-A出力", f"5V{DC}3A, 最大15W"),
                       ("2×USB-C出力", usb100), ("", f"15W: 5V{DC}3A, 最大15W"),
                       ("シガーソケット出力", f"12V{DC}最大10A")]),
        ("使用環境", [("充電温度", "0°C~45°C"), ("動作温度", "-15°C~45°C"),
                     ("保存温度", "1ヶ月 -20°C~45°C　3ヶ月 0°C~45°C　1年 0°C~25°C"), ("使用高度", "3000 m 以下")]),
    ]:
        b.comp(spec_table_component_spec, spec_carrier, section_title=title, rows=rows)
    b.add(P("認証： UN38.3"),
          P("①この数値は最大充電電力のみを示しています。実際の充電電力は、温度、バッテリー残量（SOC）、アプリの設定により変動する"
            "場合があります。"),
          P("②本製品は、ACコンセントからバッテリーを充電しながら、AC出力ポートを通じて給電することができます。"),
          P("※USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."))

    # ---- p21-22 保証について (printed 19-20), p23 QR ------------------------------------------
    b.chapter("warranty", "保証について", [21, 22, 23])
    b.add(panel("このたびは Jackery 製品をご購入いただき、誠にありがとうございます。",
                "本保証書は、Jackery ポータブル電源製品に関する保証内容を明確にご案内するものです。",
                "ご使用前に必ずご確認のうえ、大切に保管してください。"))
    note = "※ Jackery 公式オンラインストアまたは正規代理店以外での購入品は保証対象外となります。"
    sections = [
        ("保証期間", blocks("1. 保証期間はご購入日から 3 年間です。",
                           "2. また、延長保証にご登録いただくと、さらに 2 年間の保証が追加されます。詳しくは Jackery "
                           "公式サイトをご確認ください。", note)),
        ("保証の適用範囲", blocks("1. 購入チャネルについて\n本保証は、Jackery公式オンラインストアまたは正規代理店で購入された"
                                 "製品に限り有効です。", note,
                                 "2. 保証提供地域\n保証は、日本国内に在住の方が、日本国内で使用する場合に限り有効です。")),
        ("保証の適用条件", blocks("以下のすべての条件を満たす場合に、保証の適用対象となります：",
                                 ["Jackery公式オンラインストアまたは正規代理店にてご購入されたこと", "保証期間内であること",
                                  "下記の「保証対象外」に該当しないこと"])),
        ("保証対象外となる場合", blocks(
            "以下のいずれかに該当する場合、保証期間内であっても保証の対象外となります：\n"
            "1.故障・損傷が保証期間内に発生していても、保証期間終了後に申請された場合\n"
            "2.使用上の誤り（取扱説明書や本体ラベルに記載の注意事項に従わなかった使用）による故障・損傷\n"
            "3.他機器からの影響、不適切な修理または改造による故障・損傷\n"
            "4.移設・輸送・落下などに起因する故障・損傷\n"
            "5.火災・地震・風水害・落雷などの天災、または公害・塩害・異常電圧などによる故障・損傷\n"
            "6.消耗部品の劣化や摩耗、または外観の汚損など")),
        ("購入証明について", blocks("保証をご利用の際には、以下いずれかの購入証明書類をご提示いただく必要があります：",
                                   ["Jackery公式オンラインストアでの購入：注文番号（注文履歴画面または確認メール）",
                                    "正規代理店での購入：購入日・販売店名の記載された領収書または納品書"],
                                   "※  ご提示がない場合、保証対応いたしかねます。")),
        ("保証内容", blocks(                                                                     # p22
            "**1. 初期不良による交換**（ご購入日から30日以内）",
            ["取扱説明書に従った正常な使用中に不具合が発生した場合、同一製品の新品と交換いたします。",
             "在庫切れや販売終了の場合は、同等品への交換または返金にて対応いたします。"],
            "**2. 無償修理**（ご購入日から30日以上～保証期間内）",
            ["保証条件を満たす自然故障については、無料で修理対応いたします。",
             "修理が困難な場合は、同等品（同モデルまたは同等スペック品）への交換にて対応いたします。"],
            "**3. 有償修理**\n以下に該当する場合は、有償での修理対応となります：",
            ["保証期間を超えた製品", "保証対象外と判断された場合",
             "Jackery公式オンラインストアまたは正規代理店以外で購入された製品"],
            "有償修理後の保証期間は、修理完了日より90日間です。",
            "※ 無償修理の場合、残りの保証期間が90日未満であれば「90日間」、90日以上であれば「元の保証期間に準じます」。")),
    ]
    for index, (title, body) in enumerate(sections, start=1):
        b.h(title)
        b.comp(warranty_section_component_spec, title=title, section_index=index, blocks=body)
    # The panel's bold title is a heading so the last warranty card's section ends before it.
    b.h("免責事項")
    b.add(panel(
                "1. 弊社では、いかなる場合においても、間接的損害または付随的損害（データの損失・逸失利益など）に対して責任を負い"
                "ません。",
                "2. 本保証書は、お客様が法律上有する権利を制限するものではありません。",
                "3. 保証内容は、予告なく変更される場合がございます。あらかじめご了承ください。",
                "Jackery 製品を安心してご使用いただくために、本保証書の内容をご確認のうえ、ご活用くださいますようお願いいたします。",
                "ご不明点がございましたら、Jackery カスタマーサービスまでお問い合わせください。"))
    b.add(P("**公式サイト: http://www.jackery.jp**"),
          P("**カスタマーサポート: jackery.jp@jackery.com**"),
          P("**お問い合わせ電話番号: 050-3198-9007**"))
    b.figure("contact-qr")                                                                   # p23

    problems = b.finish()
    print("chapters", len(b.chapters), "problems", problems)
    return problems


if __name__ == "__main__":
    if make():
        raise SystemExit("figure records and transcription disagree")
