"""Write the JE-500A JP Japanese semantic document from the reviewed transcription.

Run from the repository root:
``python3 manual_sources/JE-500A/JP/ja/git-20261103-368d9934/source/intake.py``.
It writes ``source/ja/content.json`` and the declared plain-table row of
``source_manifest.json:shared_component_exceptions``. ``original.pdf`` is outlined
(no text layer), so every Japanese line below is transcribed from 300 dpi renders
(500-600 dpi clips for small or ambiguous glyphs) of the named physical page and
kept as printed, suspected source errors included (``source_concerns``). Every
printed block maps to a shared component or plain shared flow
(``source_manifest.json:component_map``); no package class or inline style. The
cover (p1) and table of contents (p2) are not Web content.
"""
from pathlib import Path
import json
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kit import OL, P, UL, Book, blocks, inbox_carrier, pair, spec_carrier  # noqa: E402
from kit import inline, node, root  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.manual_tables import (  # noqa: E402
    lcd_icon_component_spec, symbol_icon_component_spec, symbol_signal_component_spec,
    troubleshooting_component_spec,
)
from tools.component_specs.spec_table import spec_table_component_spec  # noqa: E402
from tools.component_specs.warranty import warranty_section_component_spec  # noqa: E402
from tools.web.frozen_ai_flow import table  # noqa: E402
from tools.web.prepared_style_audit import table_text_sha256  # noqa: E402

SOURCE = Path(__file__).resolve().parents[1]
DC = "⎓"  # the print's DC symbol
NAME = "Jackery ポータブル電源 500 New"


def cell(value: str, *, header: bool = False, **fields) -> dict:
    return node("table_cell", inline(value), header=header, **fields)


def panel(*children) -> dict:
    """The print's grey text panel as the shared theme's text panel (web_manual.css .hb-text-panel)."""
    return node("group", [P(c) if isinstance(c, str) else c for c in children], role="container",
                presentation={"html": {"attributes": {"class": "hb-text-panel"}}})


def make() -> list[str]:
    b = Book(SOURCE, "JE-500A", "JP", "ja", NAME + " · JE-500A")
    load = lambda name: json.loads((SOURCE / "source" / name).read_text())  # noqa: E731
    exceptions = []

    def plain_table(rows, reason):
        flow = table(rows)
        b.add(flow)
        exceptions.append({"kind": "table", "language": "ja", "page_id": b.current["id"],
                           "text_sha256": table_text_sha256(root(flow)), "reason": reason})

    def warn(title, *body, label="警告", variant="warning"):
        b.callout(label, P(f"**{title}**"), *body, variant=variant)

    # ---- p3-4 安全上のご注意 ------------------------------------------------------------
    b.chapter("safety", "安全上のご注意", [3, 4])
    b.add(P("**ご使用の前にこの「安全上のご注意」をよくお読みのうえ、正しくお使いください。**"))
    b.h("絵表示について")
    b.add(P("製品を安全に正しくお使いいただき、お客様や他の方々への危害や財産への損害を未然に防止するための表示です。\n"
            "内容をよく理解してから本文をお読みください。"))
    # The print's signal box has no header row; the shared table's 表示/意味 headers follow JE-1000D JP V2.
    b.comp(symbol_signal_component_spec, accessibility_label="絵表示について",
           headers=[pair("表示", "content"), pair("意味", "content")],
           rows=[{"label": label, "show_icon": True, **pair(meaning, "meaning")} for label, meaning in [
               ("警告", "この表示を無視して、誤った取り扱いをすると、人が死亡または重傷を負う可能性が想定される内容を示しています。"),
               ("注意", "この表示を無視して、誤った取り扱いをすると、人が傷害を負う可能性が想定される内容または物的損害の発生が"
                        "想定される内容を示しています。")]])
    b.h("絵表示の説明")
    symbols = [row for row in load("symbols.json") if row["physical_page"] == 3]
    panels = [[], []]
    for index, row in enumerate(symbols):
        meaning = pair(row["meaning"], "meaning")
        panels[0 if row["glyph_search_box"][0] < 100 else 1].append(
            {"asset_index": index, "icon_alt": meaning["meaning_text"], **meaning})
    b.comp(symbol_icon_component_spec, accessibility_label="絵表示の説明",
           headers=[pair(v, "content") for v in ("記号", "意味", "記号", "意味")],
           panels=panels, icon_refs=[r["local_path"] for r in symbols])
    # 警告 grid (p3): left column, then right column, each row one shared callout.
    warn("火のそばや炎天下の車内、熱器具の周辺など高温（45°C以上）になる場所で使用したり、放置しない",
         "発熱や発火、破裂する原因になります。")
    warn("強い衝撃を与えたり、投げつけたりしない", "発熱や発火、破裂する原因になります。")
    warn("水など、液体を入れたり、濡らしたりしない", "発熱や発火の原因になります。")
    warn("濡れた手で本体や接続するケーブルを触らない", "火災や感電の原因になります。")
    warn("端子部にケーブル以外の金属類を差し込まない", "発熱や発火の原因になります。")
    warn("雷が鳴りだしたら、電源プラグにふれない (充電をしない)", "感電の原因になります。")
    warn("各接続端子には確実に差し込む", "差し込みが不十分だと、発熱したりほこりが付着して火災や感電の原因になります。")
    warn("接地接続は必ず、電源プラグを電源につなぐ前に行って下さい",
         "また、接地接続を外す場合は、必ず電源プラグを切り離してから行って下さい。")
    # 警告 grid (p4).
    warn("万が一、次のような異常が発生したときはすぐに使用をやめる",
         UL("煙が出ている、異臭がする", "落としたり、破損したとき", "異音がする", "内部に水や異物が入ったとき",
            "電源コード (ACアダプター) が傷んだとき"),
         "このような異常が発生したまま使用していると、火災や感電の原因になります。\n"
         "すぐにACアダプターをコンセントから抜いてください。また、本製品に接続されている機器もすべて外してください。",
         "**万が一発煙や発火したら、大量の水で消火して煙が見えなくなるまで本製品を水浸しにしてください。**",
         "煙が出なくなることを確認してからカスタマーサポートにご連絡ください。\nお客様による修理は危険ですので絶対におやめください。")
    warn("分解、改造しない", "故障、発熱、火災·感電の原因になります。")
    warn("表示された電源電圧以外で使用しない", "故障、発熱、火災·感電の原因になります。また、本製品を使用できるのは日本国内のみです。")
    warn("付属品と本製品が破損した場合は、ご自身で修理をしない")
    caution = dict(label="注意", variant="caution")
    warn("本製品の上に物を載せたり、不安定な場所に置かない", "倒れたり、落ちたりしてけがの原因になります。", **caution)
    warn("データサーバや医療機器など、非常時に不具合が起こると人命 / 財産に重大な危険を及ぼしうる用途でのご使用はお控えください。"
         "次のようなような機器では、万が一使用中に給電ができなくなった場合、人命 / 財産にかかわる被害が想定されます。",
         UL("医療機器や使用上、生命に関わるような機器", "社会的、公共的に重要な機器など", "重要な事業用機器など"), **caution)
    warn("心臓にペースメーカーを装着している方は使用しない", "ペースメーカーが、本製品の影響を受ける恐れがあります。", **caution)
    warn(f"格納式ハンドルを使用して{NAME} を移動するときは、積み重ねたり、上に他の物を置いたりしないでください。"
         "落下して怪我をする場合があります。", **caution)

    # ---- p5-6 使用上のご注意 ------------------------------------------------------------
    b.chapter("usage_precautions", "使用上のご注意", [5, 6])
    b.add(panel(
        f"{NAME} は、定格出力 500W です。通常時で消費電力が 500W までの機器に給電ができるため、多くの電化製品や端末に"
        "対応可能です。ただし、電気モーターを搭載している製品については、例 ( 掃除機、ポンプ、冷蔵庫、電動丸ノコ、エアコン、"
        "洗濯機、電子レンジ、ドライヤーなど ) 起動時に「誘導負荷」が発生し、公称電力の 3〜7 倍の電力が必要となります。\n"
        "定格出力 500W は、一定の電力で動く機器への出力可能範囲を指しています。\n"
        "500W の出力を超えた場合は、電気回路が自動的に調整され、電力が低減、または保護機能が作動し自動で遮断することがあります。\n"
        "また AC 出力ポート 2 つ搭載されておりますが、2 つ同時にご利用頂く場合、合計して 500W 以内であることをご確認の上"
        "ご利用ください。"))
    b.callout("ご注意", "始動電力が出力上限値 ( 定格出力 ) を大幅に超える可能性のある製品のご利用や、定格出力を超え給電が"
              "ストップした製品を繰り返し利用することはポータブル電源のバッテリーが損傷するリスクがありますのでお控えください。",
              variant="caution")
    b.h("給電に関する注意事項")
    b.add(UL(
        "出力上限値を超える電化製品は使用しないでください。\n特に、始動電力が公称電力の 3〜7 倍になる誘導負荷（ポンプ、"
        "ヒーター、掃除機、冷蔵庫、エアコン、電気丸ノコなどの電動道具、洗濯機、電子レンジなど）の使用にはご注意ください。",
        "接続機器の消費電力が本製品の出力範囲内であることをご確認の上、出力ボタンを押してください。",
        "給電中、機器の制御や環境により、急速充電にならない・給電できない場合があります。",
        "充電または給電中、ラジオ・チューナー・テレビなどに雑音が入る場合があります。その際は、それらの機器から離してご使用ください。"))
    b.h("使用環境について")
    b.add(UL(
        "本製品は防塵・防水仕様ではありません。ほこり、水、海水などがかからないようご注意ください。",
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
    b.add(UL(
        "接続機器の入力が本製品の出力上限を超えている場合、自動で電源が遮断されます。",
        "本機は -20°C~45°C (-4°F~113°F) の温度範囲でお使いの機器に電力供給が可能となり、本機の蓄電は -20°C~45°C "
        "(-4°F~113°F) で行えます。\n動作温度が上記範囲外にある場合、本製品が温度異常マークが表示され、動作しない可能性があります。\n"
        "温度異常マークが表示された場合は、本製品を 2 時間以上、動作温度範囲内の環境に置いてください。",
        "容量表示は参考値であり、電圧により表示数値と実際の容量に差異が出る場合があります。"))

    # ---- p6 免責事項 -----------------------------------------------------------------------
    b.chapter("disclaimer", "免責事項", [6])
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

    # ---- p7 同梱品 -------------------------------------------------------------------------
    b.chapter("in_the_box", "同梱品", [7])
    slots = ("inbox-unit", "inbox-ac-cable", "inbox-user-manual")
    cards = [{"image_ref": b.figures[slot]["local_path"], "label": b.figures[slot]["caption"],
              "alt": b.figures[slot]["caption"]} for slot in slots]
    b.used_figures += list(slots)
    b.comp(inbox_component_spec, inbox_carrier, accessibility_label="同梱品", cards=cards,
           tip_label="", tip_body="", require_tip=False, variant="responsive-card-grid")
    b.add(P("※ 付属品を故障、紛失等してしまった場合はカスタマーサポートまでご連絡ください。"),
          P("※ シガーソケット充電ケーブルは別売りです。Jackery公式サイトよりご購入いただけます。\n"
            "サポートが必要な場合は、Jackeryカスタマーサポートまでお問い合わせください。"),
          P("**■本機の仕様および外観は、改善のため予告なく変更することがあります。**"))
    b.h("充電式電池のリサイクルについて")
    # The Li-ion 32 mark is this print's symbol row (source/symbols.json); it is shown from that row's asset.
    liion = next(row for row in load("symbols.json") if row["family"] == "li-ion/")
    b.figures["recycle-li-ion"] = {"slot": "recycle-li-ion", "physical_page": 7, "local_path": liion["local_path"],
                                   "caption": "Li-ion 32", "embedded_words": True}
    b.figure("recycle-li-ion")
    b.add(P("本機はリサイクル可能な充電池を内蔵しています。\nこの商品を廃棄する場合は、当社のカスタマーサポートにご連絡ください。\n"
            "充電池の取りはずしはお客様自身では行わないでください。"))

    # ---- p8 各部の名称 ----------------------------------------------------------------------
    b.chapter("product_overview", "各部の名称", [8])
    b.h("正面")
    b.figure("overview-front")
    b.h("右側面")
    b.figure("overview-right")

    # ---- p9-10 液晶画面 ----------------------------------------------------------------------
    b.chapter("lcd_display", "液晶画面", [9, 10])
    b.figure("lcd-display")
    glyphs = load("glyphs.json")
    names = [
        ("①", "UPS機能", "**点灯時：**製品が給電と充電を同時に行う「パススルー充電」状態にあります。停電時には家庭用電源から"
         "ポータブル電源の切り替え時間が10ミリ秒で行われます。\n**消灯時：**製品がパススルー充電状態ではありません。"),
        ("②", "交流電源による出力マーク（正弦波）", "AC出力（純正弦波）がオンになっています。"),
        ("③", "入力電力表示", "入力電力をワットで表示します。"),
        ("④", "消費電力パワー", "出力電力をワットで表示します。"),
        ("⑤", "AC入力電力表示", "本製品は、家庭用のコンセント（系統電力）を使用し、AC入力を通じて充電されます。"),
        ("⑥", "シガーソケット入力電力表示", "製品は、DC 12V（カーチャージ）を使用し、低PV入力（8020）を介して充電されています。"),
        ("⑦", "ソーラー(グリーンエネルギー)充電接続", "製品は、ソーラーパネルを使用し、8020入力ポートを介して充電されています。"),
        ("⑧", "バッテリーアイコン", "製品の充電中は、バッテリーのパーセンテージを囲むオレンジ色の円が順番に点灯します。他のデバイスの"
         "充電時には、オレンジ色の円は点灯したままになります。"),
        ("⑨", "バッテリーレベルパーセントタグ", "バッテリー残量を表示します。"),
        ("⑩", "エラーコード", "製品エラーが発生しました。詳細については、トラブルシューティングのセクションを参照してください。"),  # p10
        ("⑪", "高温インジケーター", "高温保護が作動しました。製品の温度が通常の動作範囲に戻るまで、製品の機能が停止する場合があります。"),
        ("⑪", "低温インジケーター", "低温保護が作動しました。製品の温度が通常の動作範囲に戻るまで、製品の機能が停止する場合があります。"),
        ("⑫", "省エネモード", "**アイコン表示：**省エネモードがオンになっています。\n**アイコン消える：**省エネモードがオフになっています。"),
    ]
    rows = [{**pair(number, "number"), **pair(name, "name"), **pair(description, "description"),
             "icon_alt": name, "asset_index": index}
            for index, (number, name, description) in enumerate(names)]
    b.comp(lcd_icon_component_spec, accessibility_label="液晶画面", rows=rows,
           icon_refs=[g["local_path"] for g in glyphs], icon_locale_policy="exact")

    # ---- p10 トラブルシューティング --------------------------------------------------------------
    b.chapter("troubleshooting", "トラブルシューティング", [10])
    rows = [
        ("F0 / F1\nF2 / F3", "製品の電源を切り、再起動してください。"),
        ("F4", "製品に負荷を接続してバッテリーを放電し、エラーが消えるまで続けてください。"),
        ("F5", "ソーラーパネルまたはAC電源コンセントを使用して、エラーが消えるまで製品を充電してください。"),
        ("F6", "1. AC 電源コンセントから充電する前に、電力グリッドが安定するのを待ってください。\n"
               "2. 吸気口および排気口が塞がれていないか確認し、製品の両側に 30cm のスペースを確保してください。\n"
               "3. 製品は日陰で通気の良い場所に設置し、周囲温度が 45°C未満であることを確認してください。\n"
               "4. 製品からすべての負荷を取り外し、アイドル状態にして、エラーが消えるまで待ってください。ご使用の機器の起動時"
               "消費電力が本製品の出力範囲を超えていないかをご確認ください。\n"
               "5. 製品を再起動してください。"),
        ("F7", "1. 製品からすべてのDC入力を取り外してください。\n"
               "2. ソーラーパネルで充電する場合は、接続されたソーラーパネルの開放電圧（Voc）を確認してください。本製品の最大DC"
               "入力電圧は60Vです。\n"
               "3. 製品を再起動し、アイドル状態を保ってください。エラーが消えるまで待ってください。"),
        ("F8", "販売店またはJackeryカスタマーサポートにお問い合わせください。"),
        ("F9", "製品のDC 12V出力ポート/USBポートに接続されている負荷を取り外してください。\n故障が消えるまで待機してください。"),
    ]
    b.comp(troubleshooting_component_spec, headers=[pair("エラーコード", "content"), pair("対処方法", "content")],
           rows=[{**pair(code, "code"), **pair(measures, "measures")} for code, measures in rows])

    # ---- p11-13 使い方 -------------------------------------------------------------------------
    b.chapter("operations", "使い方", [11, 12, 13])
    b.h("主電源ボタン/オフ")
    b.figure("power-on-off")
    b.h("USB/カーポート出力オン/オフ")
    b.figure("dc-usb-output")
    b.callout("ご注意", UL(
        "本製品は、Jackery 12Vカーバッテリー充電ケーブルを使用することで、車のバッテリーへの充電が可能です。12V車専用であり、"
        "24V車には対応しておりません。\n※充電ケーブルは別売りとなります。Jackery公式サイトにてお求めいただけます。",
        "本製品の12V DC出力（シガーソケット）から車のバッテリーへ充電中は、エンジンを始動しないでください。製品の故障に"
        "つながる恐れがあります。",
        "この機能はあくまで車のバッテリーの緊急補助用であり、深刻なバッテリー上がりや故障したバッテリーには対応しておりません。"),
        variant="caution")
    b.h("AC出力のオン/オフ")                                                             # p12
    b.add(P("* 主電源ボタンがオンになっていることを確認してください。"))
    b.figure("ac-output")
    b.h("LEDライト")
    b.add(panel("LEDライトには、照明モードとSOSモードの**2**つのモードがあります。\n"
                "LEDスイッチを短く押すとLEDライトが点灯し、再度短く押すとSOSモードに切り替わります。いずれのモードでも、"
                "LEDスイッチを長押しすることでLEDライトを消灯できます。"))
    b.figure("led-light")
    b.h("LCDディスプレイ")
    span = {"row_span": 3}
    plain_table([
        [cell("LCD画面", **span), cell("オンにする"), cell("主電源ボタンを押すか、充電入力がある場合。")],
        [cell("オフにする"), cell("主電源ボタンを押します。")],
        [cell("自動オフ"), cell("2分間操作がないとLCDは自動的に消灯し、\nスリープモードになります。")],
        [cell("常時点灯ディスプレイ\nモード\n（充電または放電状態）", **span), cell("オンにする"),
         cell("LCD画面がオンのときに主電源ボタンをダブルクリックします。")],
        [cell("オフにする"), cell("主電源ボタンを押します。")],
        [cell("自動オフ"), cell("常時点灯ディスプレイモードは、2時間操作がないと自動的に消灯します。")],
    ], "HB-TABLE-LCD-MODE requires its button artwork; this print sets the LCDディスプレイ on/off table without any "
       "drawing, so the printed three-column screen/action/description table is kept as a plain shared table "
       "(JE-500A US/en precedent).")
    b.h("省エネモード")                                                                  # p13
    b.add(panel(
        "【動作条件】",
        UL(("省エネモードON設定時：", UL("低出力状態継続6時間→全出力自動OFF",
                                        "ACまたはDC出力ボタがオンのままで、充放電なしで6時間→本体電源自動OFF")),
           ("省エネモードOFF設定時：", UL("自動OFF機能無効")),
           ("オンとオフの設定方法：", UL("手動設定は下記画像にてご参照"))),
        "【機能目的】\nバッテリーの無駄な消耗を防ぐ自動電源OFF機能\n※本機能をご利用になる場合は、省エネモードを手動でONに"
        "設定してください",
        "※ 低出力状態の定義：",
        UL("AC出力が25W以下", "DC出力（USB＋シガーソケット出力）が2W以下")))
    b.figure("energy-saving")
    b.callout("ご注意", UL(
        "はじめてお使いになるときは、本製品をフル充電してからご使用ください。",
        "低消費電力の機器をご使用の場合は、出力が途中で切れないよう、省エネモードを「オフ」にしてください。"),
        variant="caution")
    b.add(P("50Hz/60Hz周波数の切り替え:"),
          panel("※ 工場出荷時のデフォルト設定は60Hzに設定されています。\n"
                "自動識別: お客様のお住まいの地域に応じて周波数を自動的に識別し、対応する出力に自動調整されます。\n"
                "手動調整: AC出力ボタンを長押しすることで周波数を切り替えることができ、対応する周波数が画面に表示されます。"))
    b.figure("frequency-switch")

    # ---- p14 UPS 機能 ----------------------------------------------------------------------------
    b.chapter("ups", "UPS 機能", [14])
    b.figure("ups")
    b.add(panel(
        "本製品は、電気系統（家庭内の電源など）が突然停止した場合、自動的にバッテリー給電モードに切り替わる UPS（無停電電源装置）"
        "機能を備えています。切替時間は約 10 ミリ秒（0.010 秒）以内です。ただし、本機能は 0ms での完全な無停止給電には対応して"
        "おりません。そのため、以下のような高精度な連続電源供給を必要とする機器への接続はお控えください：",
        UL("データサーバー", "ワークステーション", "医療機器など"),
        "これらの機器でご使用を希望される場合は、事前に複数回の動作テストを実施し、機器との互換性をご確認の上でご使用ください。\n"
        "また、複数の高負荷機器を同時に接続した場合、過負荷保護が作動し電源が遮断される可能性があります。使用時はできるだけ一台の"
        "機器のみを接続することを推奨します。\n"
        "※記載の手順に従わずに機器が正常に動作しなかったり、データ消失などの損害が発生した場合、弊社では責任を負いかねます。"
        "あらかじめご了承ください。"))

    # ---- p14-16 充電方法 -------------------------------------------------------------------------
    b.chapter("charging", "充電方法", [14, 15, 16])
    b.add(P("**グリーンエネルギー優先モード:**\n本製品はグリーンエネルギー優先モードを搭載していますが、ソーラーパネルとAC充電"
            "ケーブルを使って同時に充電できます。同時に充電すると、ソーラーが優先されますが、バッテリーの最大許容電力で同時に"
            "充電されます。"))
    b.callout("ご注意", "1.製品の充電動作温度範囲は-20°C~45°C、放電動作温度範囲は-20°C~45°Cです。上限・下限温度を超えた場合、"
              "充放電が制限され、または充放電不可の可能性があります。\n2.温度によって、製品の充電効率と実際の容量は異なります。",
              variant="caution")
    b.callout("ご注意", UL(                                                                # p15
        "はじめてお使いになるときは、本製品をフル充電してからご使用ください。",
        "充電池は空の状態で長期保管(3カ月〜6カ月）すると、性能が劣化したり、充電できなくなる場合があります。",
        "長期保管中は、電池残量が0%にならないよう、3か月に一度の充電をおすすめします。"), variant="caution")
    b.h("AC充電ケーブル")
    b.add(P(f"付属のAC充電ケーブルをご使用ください。\nコンセントより{NAME} 本体に充電する場合、電流容量が大きいため、他機器と"
            "併用したり途中接続をすると、コンセントの電流上限値を超え充電停止したり、配線やコンセント・接続部が発熱し、火災の原因と"
            "なる恐れがあります。必ず電源タップなどを介して他の電気製品と併用しないでください。"))
    b.callout("ご注意", "AC充電ケーブルのプラグが製品のAC入力ポートにしっかりと、かつ完全に差し込まれていることを確認してください。"
              "差し込みが不完全な場合、電流の不安定、発熱、接触不良などが発生し、機器の正常な動作に支障をきたす恐れがあります。",
              variant="caution")
    b.figure("charging-ac")
    b.h("ソーラー充電")
    b.add(P(f"{NAME} は、DC8020 入力ポートを 1 つ搭載しており、DC 入力の最大電力は 200W です。Jackery ソーラーパネルと"
            "組み合わせて使用できます。"))
    b.callout("ご注意", "ソーラーパネルを接続する際は、パネルの開放電圧 (Voc) がポータブル電源の DC 入力電圧範囲（16〜60V）内で"
              "あることをご確認ください。過電圧による製品の損傷を防ぐためです。", variant="caution")
    b.add(P("ソーラーパネル1枚を接続する場合は、DC入力ポート（8020メス）にソーラーパネルの8020オスを直接接続してください。"
            "追加アクセサリーは不要です。"))
    b.figure("charging-solar-single")
    b.add(P("1 つの DC8020 ポートに 2 枚のソーラーパネルを同時に接続する場合は、別売りのJackery SolarSaga アダプター"   # p16
            "（Pro/Plus/New専用）を使用してください。接続イメージは以下をご参照ください。"))
    b.figure("charging-solar-pair")
    b.callout("充電に関する安全上のご注意",
              "※ 2  枚のソーラーパネルを同時にご使用になる場合は、必ず同一型番のパネルをご使用ください。本製品は最大 200W までの"
              "ソーラー入力に対応しています。",
              "※ Jackery ブランド以外の付属品を使用して充電しないでください。特に、ソーラーパネルで充電する際は、Jackery の"
              "ソーラーパネルを使用することをお勧めします。他社ソーラーパネルで充電することによる損失について、当社は一切の責任を"
              "負いません。", variant="caution")
    b.h("シガーソケット充電")
    b.add(P("**■本製品は、12V/10A 出力の車載シガーソケットからの充電に対応しています。**\nご使用の際は、以下にご注意ください："),
          UL("必ず車のエンジンを始動させてから接続してください。エンジン停止状態で使用すると、車両のバッテリーが上がる恐れがあります。",
             "車の充電ポートとシガーソケット充電ケーブルの接触状態をご確認ください。",
             "ケーブルが確実に奥まで差し込まれていることをご確認ください。",
             "悪路などで車両の振動が激しい場合は、接触不良や発熱・焼損の恐れがあるため、充電を中止してください。",
             "誤使用による故障・損傷については、弊社では責任を負いかねます。あらかじめご了承ください。"))
    b.figure("charging-car")
    b.callout("充電に関する安全上のご注意",
              "1) シガーソケット充電とソーラー充電を同時に使用しないでください。同時に使用すると、車のヒューズが損傷する可能性が"
              "あります。\n2) シガーソケット充電は 12V, 10A 車専用で、24V 車は充電できません。人身傷害や物的損害を避けるため、"
              "本製品の充電に 24V 車を使用しないでください。", variant="caution")

    # ---- p17 主な仕様 ------------------------------------------------------------------------------
    b.chapter("specifications", "主な仕様", [17])
    for title, rows in [
        ("基本情報", [("製品の名称", NAME), ("型番", "JE-500A"),
                      ("バッテリータイプ", "LiFePO₄ （リン酸鉄リチウムイオン電池）"),
                      ("定格容量", "20Ah/25.6V DC (512Wh)"), ("サイズ＆重量", "約311x205x157 mm (約5.7 kg）"),
                      ("サイクル寿命", "6,000回の充放電後も容量の70%以上を維持")]),
        ("入力ポート", [("AC入力", "100V-120V ~ 50Hz/60Hz, 最大15A, 最大550W±50W①"),
                        ("DC入力ポート", f"PV 16V-60V{DC}10.5A, 最大200W"),
                        ("ｼｶﾞｰｿｹｯﾄ", f"11V-16V{DC}電流制限8A")]),
        ("出力ポート", [("2×AC出力", "100V ~ 50Hz/60Hz, 2ポート合計500W (瞬間最大1000W)"),
                        ("パススルー充電AC出力", "100V-120V ~ 50Hz/60Hz, 最大500W"),
                        ("USB-A出力", f"5-6V{DC}3A, 6-9V{DC}2A, 9-12V{DC}1.5A, 最大18W"),
                        ("USB-C1出力", f"5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}5A, 最大100W"),
                        ("USB-C2出力", f"5V{DC}3A, 9V{DC}3A, 12V{DC}2.5A, 15V{DC}2A, 20V{DC}1.5A, 最大30W"),
                        ("シガーソケット出力", f"12V{DC}最大10A")]),
        ("温度範囲", [("充電温度", "-20°C~45°C (-4°F~113°F)"), ("動作温度", "-20°C~45°C (-4°F~113°F)"),
                      ("保存温度", "1ヶ月 -20°C~45°C (-4°F~113°F);"), ("", "3ヶ月 0°C~45°C (32°F~113°F);"),
                      ("", "1年 0°C~25°C (32°F~77°F)")]),
    ]:
        b.comp(spec_table_component_spec, spec_carrier, section_title=title, rows=rows)
    b.add(P("認証：UN38.3"),
          P("※USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."),
          P("① この数値は最大充電電力のみを示しています。実際の充電電力は、温度、バッテリー残量（SOC）、アプリの設定により変動する"
            "場合があります。"))

    # ---- p18-19 保証について, p19 contact, p20 back-cover QR ------------------------------------------
    b.chapter("warranty", "保証について", [18, 19, 20])
    b.add(panel("このたびは Jackery 製品をご購入いただき、誠にありがとうございます。\n"
                "本保証書は、Jackery ポータブル電源製品に関する保証内容を明確にご案内するものです。\n"
                "ご使用前に必ずご確認のうえ、大切に保管してください。"))
    sections = [
        ("保証期間", blocks(
            "1. 保証期間はご購入日から 3 年間です。",
            "2. また、延長保証にご登録いただくと、さらに 2 年間の保証が追加されます。詳しくは Jackery 公式サイトをご確認ください。",
            "※ Jackery 公式オンラインストアまたは正規代理店以外での購入品は保証対象外となります。")),
        ("保証の適用範囲", blocks(
            "1. 購入チャネルについて\n本保証は、Jackery公式オンラインストアまたは正規代理店で購入された製品に限り有効です。",
            "※ Jackery 公式オンラインストアまたは正規代理店以外での購入品は保証対象外となります。",
            "2. 保証提供地域\n保証は、日本国内に在住の方が、日本国内で使用する場合に限り有効です。")),
        ("保証の適用条件", blocks(
            "以下のすべての条件を満たす場合に、保証の適用対象となります：",
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
        ("購入証明について", blocks(
            "保証をご利用の際には、以下いずれかの購入証明書類をご提示いただく必要があります：",
            ["Jackery公式オンラインストアでの購入：注文番号（注文履歴画面または確認メール）",
             "正規代理店での購入：購入日・販売店名の記載された領収書または納品書"],
            "※  ご提示がない場合、保証対応いたしかねます。")),
        ("保証内容", blocks(                                                               # p19
            "**1. 初期不良による交換**（ご購入日から30日以内）",
            ["取扱説明書に従った正常な使用中に不具合が発生した場合、同一製品の新品と交換いたします。",
             "在庫切れや販売終了の場合は、同等品への交換または返金にて対応いたします。"],
            "**2. 無償修理**（ご購入日から30日以上〜保証期間内）",
            ["保証条件を満たす自然故障については、無料で修理対応いたします。",
             "修理が困難な場合は、同等品（同モデルまたは同等スペック品）への交換にて対応いたします。"],
            "**3. 有償修理**\n以下に該当する場合は、有償での修理対応となります：",
            ["保証期間を超えた製品", "保証対象外と判断された場合",
             "Jackery公式オンラインストアまたは正規代理店以外で購入された製品"],
            "有償修理後の保証期間は、修理完了日より90日間です。",
            "*無償修理の場合、残りの保証期間が90日未満であれば「90日間」、90日以上であれば「元の保証期間に準じます」。")),
    ]
    for index, (title, body) in enumerate(sections, start=1):
        b.h(title)
        b.comp(warranty_section_component_spec, title=title, section_index=index, blocks=body)
    # The panel's bold 免責事項 title is a heading so the panel is not drawn inside the 保証内容 card section.
    b.h("免責事項")
    b.add(panel(
        OL("弊社では、いかなる場合においても、間接的損害または付随的損害（データの損失・逸失利益など）に対して責任を負いません。",
           "本保証書は、お客様が法律上有する権利を制限するものではありません。",
           "保証内容は、予告なく変更される場合がございます。あらかじめご了承ください。"),
        "Jackery 製品を安心してご使用いただくために、本保証書の内容をご確認のうえ、ご活用くださいますようお願いいたします。",
        "ご不明点がございましたら、Jackery カスタマーサービスまでお問い合わせください。"))
    # p19 contact strip (web/mail/phone pictograms dropped) and the p20 back-cover QR code.
    b.add(P("公式サイト: http://www.jackery.jp\nカスタマーサポート: jackery.jp@jackery.com\nお問い合わせ電話番号: 050-3198-9007"))
    b.figure("contact-qr")

    problems = b.finish()
    manifest_path = SOURCE / "source_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["shared_component_exceptions"] = exceptions
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("chapters", len(b.chapters), "problems", problems)
    return problems


if __name__ == "__main__":
    if make():
        raise SystemExit("figure records and transcription disagree")
