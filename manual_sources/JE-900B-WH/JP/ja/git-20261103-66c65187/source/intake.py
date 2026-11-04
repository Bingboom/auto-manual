"""Write the JE-900B-WH JP Japanese semantic document from the reviewed transcription.

Run from the repository root:
``python3 manual_sources/JE-900B-WH/JP/ja/git-20261103-66c65187/source/intake.py``.
It writes ``source/ja/content.json``. ``original.pdf`` is outlined (no text
layer), so every Japanese line below is transcribed from 300-600 dpi renders of
the named physical pages (two passes) and kept as printed. Every printed block maps
to a shared component or plain shared flow (``source_manifest.json:component_map``);
the tables no shared component can carry are declared in
``source_manifest.json:shared_component_exceptions``. The cover (p1) and the contents
page (p2) are not Web content; the back cover (p27) carries the App download note,
store badges and QR code and closes the App chapter.
"""
from html import escape
from pathlib import Path
import json
import sys

REPO = next(p for p in Path(__file__).resolve().parents if (p / "build.py").is_file())
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from kit import P, UL, Book, blocks, inbox_carrier, inline, pair, spec_carrier  # noqa: E402
from tools.component_specs.app import app_download_component_spec, app_inline_control_component_spec  # noqa: E402
from tools.component_specs.inbox import inbox_component_spec  # noqa: E402
from tools.component_specs.key_combinations import key_combinations_component_spec  # noqa: E402
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
WARN, CAUT = "警告", "注意"


def cell(value: str, *, header: bool = False, **fields) -> dict:
    return node("table_cell", inline(value), header=header, **fields)


def plain_table(rows: list[list[dict]], head: list[list[dict]] | None = None) -> dict:
    """A declared plain table on the shared manual-table classes (shared_component_exceptions)."""
    parts = [node("table_head", [node("table_row", head)])] if head else []
    parts.append(node("table_body", [node("table_row", row) for row in rows]))
    return node("group", [node("table", parts, presentation={"html": {"attributes": {"class": "manual-table"}}})],
                role="container", presentation={"html": {"attributes": {"class": "table-wrapper docutils container"}}})


def panel(*values) -> dict:
    """The shared grey text panel (``hb-text-panel``) for a printed grey box, bubble or pill."""
    return node("group", [P(v) if isinstance(v, str) else v for v in values], role="container",
                presentation={"html": {"attributes": {"class": "hb-text-panel"}}})


def item(b: Book, variant: str, label: str, *body) -> None:
    """One printed 警告/注意 row: its title and body lines (str paragraph or a flow node)."""
    b.callout(label, *body, variant=variant)


def lcd_rows(b: Book, glyphs: dict, rows: list[tuple[str, str, str, str]]) -> None:
    """Numbered LCD icon catalog: (number, glyph slot, bold printed name, description)."""
    values = [{**pair(number, "number"), **pair(name, "name"), **pair(description, "description"),
               "icon_alt": name.replace("**", "").split("\n")[0], "asset_index": index}
              for index, (number, _, name, description) in enumerate(rows)]
    b.comp(lcd_icon_component_spec, accessibility_label="液晶画面", rows=values,
           icon_refs=[glyphs[slot]["local_path"] for _, slot, _, _ in rows], icon_locale_policy="exact", numbered=True)


def symbol_table(b: Book, label: str, rows: list[dict]) -> None:
    panels = [[], []]
    for index, row in enumerate(rows):
        meaning = pair(row["meaning"], "meaning")
        panels[0 if row["glyph_search_box"][0] < 100 else 1].append(
            {"asset_index": index, "icon_alt": meaning["meaning_text"], **meaning})
    b.comp(symbol_icon_component_spec, accessibility_label=label,
           headers=[pair(v, "content") for v in ("記号", "意味", "記号", "意味")],
           panels=panels, icon_refs=[r["local_path"] for r in rows])


def make() -> list[str]:
    b = Book(SOURCE, "JE-900B-WH", "JP", "ja", "Jackery ポータブル電源 900 取扱説明書")
    load = lambda name: json.loads((SOURCE / "source" / name).read_text())  # noqa: E731
    glyphs = {g["slot"]: g for g in load("glyphs.json")}
    symbols = load("symbols.json")
    icon = lambda slot, alt: node("image", source=glyphs[slot]["local_path"], alt=alt)  # noqa: E731

    # ---- p3-5 安全上のご注意 ------------------------------------------------------------
    b.chapter("safety", "安全上のご注意", [3, 4, 5])
    b.add(P("**ご使用の前にこの「安全上のご注意」をよくお読みのうえ、正しくお使いください。**"))
    b.h("絵表示について")
    b.add(P("製品を安全に正しくお使いいただき、お客様や他の方々への危害や財産への損害を未然に防止するための表示です。\n"
            "内容をよく理解してから本文をお読みください。"))
    b.comp(symbol_signal_component_spec, accessibility_label="絵表示について",
           headers=[pair("表示", "content"), pair("意味", "content")],
           rows=[{"label": label, "show_icon": shown, **pair(meaning, "meaning")} for label, shown, meaning in (
               (WARN, True, "この表示を無視して、誤った取り扱いをすると、人が死亡または重傷を負う可能性が想定される内容を"
                            "示しています。"),
               (CAUT, True, "この表示を無視して、誤った取り扱いをすると、人が傷害を負う可能性が想定される内容または物的"
                            "損害の発生が想定される内容を示しています。"),
               ("説明", False, "この表示を無視して誤った取り扱いをすると、機器の損傷、データの消失、性能の低下、または予期"
                              "しない動作が発生する可能性があることを示しています。"),
               ("ヒント", False, "文章内の重要な情報や操作のヒントを補足する内容を示しています。"))])
    b.h("絵表示の説明")
    symbol_table(b, "絵表示の説明", [r for r in symbols if r["physical_page"] == 3])
    symbol_table(b, "充電式電池のリサイクルについて", [r for r in symbols if r["physical_page"] == 4])   # p4
    for body in (
            "火のそばや炎天下の車内、熱器具の周辺など高温（45°C以上）になる場所で使用したり、放置しない\n"
            "発熱や発火、破裂する原因になります。",
            "強い衝撃を与えたり、投げつけたりしない\n発熱や発火、破裂する原因になります。",
            "水など、液体を入れたり、濡らしたりしない\n発熱や発火の原因になります。",
            "濡れた手で本体や接続するケーブルを触らない\n火災や感電の原因になります。",
            "端子部にケーブル以外の金属類を差し込まない\n発熱や発火の原因になります。",
            "雷が鳴りだしたら、電源プラグにふれない (充電をしない)\n感電の原因になります。",
            "各接続端子には確実に差し込む\n差し込みが不十分だと、発熱したりほこりが付着して火災や感電の原因になります。",
            "接地接続は必ず、電源プラグを電源につなぐ前に行って下さい\n"
            "また、接地接続を外す場合は、必ず電源プラグを切り離してから行って下さい。"):
        item(b, "warning", WARN, body)
    item(b, "warning", WARN, "万が一、次のような異常が発生したときはすぐに使用をやめる",                       # p5
         UL("煙が出ている、異臭がする", "落としたり、破損したとき", "異音がする", "内部に水や異物が入ったとき",
            "電源コード (AC充電ケーブル) が傷んだとき"),
         "このような異常が発生したまま使用していると、火災や感電の原因になります。\n"
         "すぐにAC充電ケーブルをコンセントから抜いてください。また、本製品に接続されている機器もすべて外してください。",
         "万が一発煙や発火したら、大量の水で消火して煙が見えなくなるまで本製品を水浸しにしてください。\n"
         "煙が出なくなることを確認してからカスタマーサポートにご連絡ください。\n"
         "お客様による修理は危険ですので絶対におやめください。")
    for body in ("分解、改造しない\n故障、発熱、火災·感電の原因になります。",
                 "表示された電源電圧以外で使用しない\n"
                 "故障、発熱、火災·感電の原因になります。また、本製品を使用できるのは日本国内のみです。",
                 "付属品と本製品が破損した場合は、ご自身で修理をしない"):
        item(b, "warning", WARN, body)
    item(b, "caution", CAUT, "本製品の上に物を載せたり、不安定な場所に置かない\n倒れたり、落ちたりしてけがの原因になります。")
    item(b, "caution", CAUT,
         "データサーバや医療機器など、非常時に不具合が起こると人命 / 財産に重大な危険を及ぼしうる用途でのご使用はお控え"
         "ください。次のような機器では、万が一使用中に給電ができなくなった場合、人命 / 財産にかかわる被害が想定されます。",
         UL("医療機器や使用上、生命に関わるような機器", "社会的、公共的に重要な機器など", "重要な事業用機器など"))
    item(b, "caution", CAUT, "心臓にペースメーカーを装着している方は使用しない\nペースメーカーが、本製品の影響を受ける恐れがあります。")
    item(b, "caution", CAUT,
         "ハンドルを使用してJackery ポータブル電源 900 を移動するときは、積み重ねたり、上に他の物を置いたりしないで"
         "ください。落下して怪我をする場合があります。")

    # ---- p6-7 使用上のご注意 --------------------------------------------------------------
    b.chapter("usage_precautions", "使用上のご注意", [6, 7])
    b.add(panel(
        "Jackery ポータブル電源 900は、定格出力1500Wです。通常時で消費電力が1500Wまでの機器に給電ができるため、多くの"
        "電化製品や端末に対応可能です。ただし、電気モーターを搭載している製品（掃除機、ポンプ、冷蔵庫、電動丸ノコ、"
        "エアコン、洗濯機、電子レンジ、ドライヤーなど）は、起動時に「誘導負荷」が発生し、公称電力の3〜7倍の電力が必要に"
        "なる場合があります。",
        "定格出力1500Wとは、一定の電力で動作する機器に対して安定して出力できる最大電力を指します。 接続する機器の消費"
        "電力が1500Wを超えた場合、保護機能が作動し、自動的に出力が停止することがあります。",
        "また、本製品にはAC出力ポートが3つ搭載されていますが、複数の機器を同時に使用する場合でも、合計消費電力が1500W"
        "以内になるようにご確認ください。"))
    b.callout("ご注意", "始動電力が出力上限値 ( 定格出力 ) を大幅に超える可能性のある製品のご利用や、定格出力を超え給電が"
              "ストップした製品を繰り返し利用することはポータブル電源のバッテリーが損傷するリスクがありますのでお控え"
              "ください。", variant="caution")
    b.add(P("**■ 給電に関する注意事項**"),
          P("出力上限値を超える電化製品は使用しないでください。"),
          UL("特に、始動電力が公称電力の 3~7 倍になる誘導負荷（ポンプ、ヒーター、掃除機、冷蔵庫、エアコン、電気丸ノコ"
             "などの電動道具、洗濯機、電子レンジなど）の使用にはご注意ください。",
             "接続機器の消費電力が本製品の出力範囲内であることをご確認の上、出力ボタンを押してください。",
             "給電中、機器の制御や環境により、急速充電にならない・給電できない場合があります。",
             "充電または給電中、ラジオ・チューナー・テレビなどに雑音が入る場合があります。その際は、それらの機器から離して"
             "ご使用ください。"),
          P("**■ 使用環境について**"),
          UL("本製品は防塵・防水仕様ではありません。ほこり、水、海水などがかからないようご注意ください。",
             "ほこりの多い場所や高温多湿の場所での充電・使用・放置は避けてください。",
             "平坦で安定した場所に設置し、不安定な場所に置かないでください。",
             "本製品の通風孔は、安全上絶対にふさがないでください。各面から 5cm 以上スペースを確保してください。",
             "充電・給電中は本体が温かくなります。周囲に物を置かないでください。"),
          P("**■ 接続時の注意事項**"),                                                       # p7
          UL("ケーブルを接続する際は、まっすぐに差し込んでください。",
             "抜く際は必ずプラグ部分を持って抜いてください。ケーブルを引っ張ったり折り曲げたりしないでください。",
             "この機器に同梱した指定の電源コードセットだけを使用する。"),
          P("**■ お手入れについて**"),
          UL("本体が汚れた場合は、電源プラグを抜いた状態で、柔らかい布で乾拭きしてください。",
             "汚れがひどい場合は、水または薄めた中性洗剤で拭き取ってください。",
             "シンナーやベンジンなどの使用は絶対に使わないでください。"),
          P("**■ 入出力・温度・表示に関するご注意**"),
          UL("接続機器の入力が本製品の出力上限を超えている場合、自動で電源が遮断されます。",
             ("本機は -10°C~45°C の温度範囲でお使いの機器に電力供給が可能となり、本機の蓄電は 0°C~45°C で行えます。",
              UL("動作温度が上記範囲外にある場合、本製品が温度異常マークが表示され、動作しない可能性があります。",
                 "温度異常マークが表示された場合は、本製品を 2 時間以上、動作温度範囲内の環境に置いてください。")),
             "容量表示は参考値であり、電圧により表示数値と実際の容量に差異が出る場合があります。"))

    # ---- p7 免責事項 -----------------------------------------------------------------------
    b.chapter("disclaimer", "免責事項", [7])
    b.add(panel(UL(
        "火災、地震、第三者による行為、その他の事故、お客様の故意または過失誤用・誤動作・その他の異常な条件下での使用に"
        "より生じた損害に関して、当社は一切責任を負いません。",
        "付属品と本製品が破損した場合は、ご自身で修理を行わないでください。ご自身で分解・修理したことにより生じた損害に"
        "関し、当社は一切責任を負いません。",
        "保証範囲は利用規約に適用され、記載されていない内容は当社の保証範囲外となります。",
        "取扱説明書の記載事項が遵守されないことにより生じた不適合について当社は責任を負いかねます。",
        "本製品の使用、または使用不能から発生する付随的な損害 ( 事業利益損失含む )、当社が関与しない接続機器との組み合わせ"
        "による誤動作などから生じた損害に関して、当社は一切の責任を負いません。",
        "本製品は病院仕様のシーパップ（CPAP）、エクモ（ECMO）、ペースメーカなど、身の安全に関わる医療救急機械の電源と"
        "しての使用、または、消費電力の大きいな設備、例えば核施設設備、スペースシャトル製造などの使用は推薦されません。"
        "上記設備の使用後、火災、機器故障など個人安全を脅かす事故の責任を取りません。")))

    # ---- p8 同梱品 ---------------------------------------------------------------------------
    b.chapter("in_the_box", "同梱品", [8])
    slots = ("inbox-main-unit", "inbox-ac-cable", "inbox-manual")
    cards = [{"image_ref": b.figures[s]["local_path"], "label": b.figures[s]["caption"],
              "alt": b.figures[s]["caption"]} for s in slots]
    b.used_figures += list(slots)
    b.comp(inbox_component_spec, inbox_carrier, accessibility_label="同梱品", cards=cards,
           tip_label="", tip_body="", require_tip=False, variant="responsive-card-grid")
    b.add(P("※ 付属品を故障、紛失等してしまった場合はカスタマーサポートまでご連絡ください。"),
          P("※ AC充電ケーブルは、同梱のAC充電ケーブルは、本製品以外の機器には使用しないでください。"),
          P("※ シガーソケット充電ケーブルは別売りです。Jackery公式サイトよりご購入いただけます。\n"
            "サポートが必要な場合は、Jackeryカスタマーサポートまでお問い合わせください。"),
          P("**■ 本機の仕様および外観は、改善のため予告なく変更することがあります。**"))

    # ---- p8-9 各部の名称 ---------------------------------------------------------------------
    b.chapter("product_overview", "各部の名称", [8, 9])
    b.h("正面")
    b.figure("parts-front")
    b.h("右側面")                                                                          # p9
    b.figure("parts-right-side")

    # ---- p9-11 液晶画面 ----------------------------------------------------------------------
    b.chapter("lcd_display", "液晶画面", [9, 10, 11])
    b.figure("lcd-overview")
    app_kept = "（Jackeryアプリで設定してください。電源オフ時も設定は保持されます。）"
    lcd_rows(b, glyphs, [                                                                  # p10
        ("①", "lcd-wifi", "**Wi-Fi**",
         "**オン：** Wi-Fi接続済。\n**点滅：** Wi-Fiに接続する準備ができました。\n**オフ：** Wi-Fi接続解除済。"),
        ("②", "lcd-bluetooth", "**Bluetooth**",
         "**オン：** Bluetooth接続済。\n**点滅：** Bluetoothに接続する準備ができました。\n**オフ：** Bluetooth接続解除済。"),
        ("③", "lcd-quiet-charging", "**静音充電モード**",
         "**オン：**充電中のノイズが大幅に低減され、充電電力が低下し、充電速度が低減します。\n"
         "**オフ：**静音充電モードが無効になっています。\n"
         "（Jackeryアプリで有効/無効にできます。電源オフ時も設定は保持されます。）"),
        ("④", "lcd-scheduled-charging", "**計画充電モード**",
         "Jackery ポータブル電源 900 の充電時間をカスタマイズすることで、電気料金のピーク時間とオフピーク時間に基づいた"
         "充電プランを選択。これにより月々の電気料金を削減することができます。\n" + app_kept),
        ("⑤", "lcd-self-consumption", "**自家発電モード**",
         "**点灯時：**自家発電モードがオンになっており、太陽光エネルギーの利用を最大化し、電力会社からの電力消費を削減"
         "して電気代を節約します。\n**消灯時：**自家発電モードがオフ、または未設定の状態です。\n" + app_kept),
        ("⑥", "lcd-tou", "**TOUモード**",
         "**オン：**TOUモードが有効です（デフォルトバックアップSOC：60%）。ピーク時間帯に、蓄積エネルギーがバックアップ"
         "SOCを上回ると、本製品はバッテリーの放電を優先し、ピーク時の電力コストを削減します。 オフピーク時間帯には、"
         "系統からバッテリーを充電し、ピークカットと谷埋めを実現します。\n"
         "**オフ：**TOUモードは無効になります。 本デバイスはTOU（時間帯別料金）戦略に従わず、デフォルトの電力供給および"
         "充電ロジックに基づいて動作します。\n" + app_kept),
        ("⑦", "lcd-ups", "**UPS機能**",
         "**点灯時：**製品はバイパスモードで動作しています。ACポートに接続された負荷は、ポータブル電源ではなく商用電源から"
         "給電されます。\n商用電源が突然停電した場合、製品は10ミリ秒以内に自動でバッテリー給電へ切り替わります。\n"
         "**消灯時：**製品はバイパスモードではありません。ACポートに接続された負荷は、ポータブル電源の内蔵バッテリー"
         "から給電されます。"),
        ("⑧", "lcd-ac-output", "**交流電源による出力マーク（正弦波）**", "AC出力（純正弦波）がオンになっています。"),
        ("⑨", "lcd-voltage-frequency", "**出力電圧と周波数**", "出力される電圧と周波数を表示します。"),
        ("⑩", "lcd-input-power", "**入力電力表示**", "入力電力をワットで表示します。"),
        ("⑪", "lcd-charge-time", "**充電残り時間**", "充電残り時間を表示します。"),
        ("⑫", "lcd-ac-input", "**AC入力電力表示**", "製品は、系統電力を使用し、AC入力を介して充電されます。"),
        ("⑬", "lcd-car-input", "**シガーソケット入力電力表示**",
         "製品は、DC 12V（カーチャージ）を使用し、8020入力ポートを介して充電されています。"),
    ])
    protect = "保護が作動しました。製品の温度が通常の動作範囲に戻るまで、製品の機能が停止する場合があります。"
    lcd_rows(b, glyphs, [                                                                  # p11
        ("⑭", "lcd-solar-input", "**ソーラー(グリーンエネルギー)充電接続**",
         "製品は、ソーラーパネルを使用し、8020入力ポートを介して充電されています。"),
        ("⑮", "lcd-battery-saving", "**バッテリー節約モード**\nJackeryアプリで有効/無効にできます",
         "バッテリー節約モードが有効になると、充電および放電の制限が適用され、バッテリーの寿命を延ばすことが可能です。\n"
         + app_kept + "\nこの機能が有効な場合、本製品はSOCを較正するために、時折フル充放電サイクルを実行します。"),
        ("⑯", "lcd-charge-speed-limit", "**充電速度制限**",
         "**点灯時：**アプリ側で充電速度制限が有効になっています。\n**消灯時：**アプリ側で充電速度制限が無効になっています。\n"
         + app_kept),
        ("⑰", "lcd-battery-ring", "**バッテリーアイコン**",
         "製品の充電中は、バッテリーのパーセンテージを囲むオレンジ色の円が順番に点灯します。他のデバイスの充電時には、"
         "オレンジ色の円は点灯したままになります。"),
        ("⑱", "lcd-low-battery", "**バッテリー残量警告灯**",
         "**オン：**バッテリー残量が20%未満です。\n**点滅：**バッテリー残量が5%未満です。\n**オフ：**製品は充電中です。"),
        ("⑲", "lcd-battery-percent", "**バッテリーレベルパーセントタグ**", "バッテリー残量を表示します。"),
        ("⑳", "lcd-discharge-timer", "**放電タイマー**",
         "**オン：**放電タイマーが設定されています。\n**オフ：**放電タイマーは設定されていません。\n"
         "Jackeryアプリで設定してください。本設定は、デバイスの電源を切ると保持されません。"),
        ("㉑", "lcd-energy-saving", "**省エネモード**",
         "ACまたはDC/USB出力ボタンを押して出力をオンにしたとき：\n**アイコン表示：**省エネモードがオンになっています。\n"
         "**アイコン無表示：**省エネモードがオフになっています。"),
        ("㉒", "lcd-high-temperature", "**高温インジケーター**", "高温" + protect),
        ("㉒", "lcd-low-temperature", "**低温インジケーター**", "低温" + protect),
        ("㉓", "lcd-fault-code", "**エラーコード**",
         "製品エラーが発生しました。詳細については、トラブルシューティングのセクションを参照してください。"),
        ("㉔", "lcd-output-power", "**消費電力**", "出力電力をワットで表示します。"),
        ("㉕", "lcd-runtime", "**バッテリー使用可能時間**", "接続した機器の使用可能な時間を表示します。"),
    ])

    # ---- p12-16 使い方 -------------------------------------------------------------------------
    b.chapter("usage", "使い方", [12, 13, 14, 15, 16])
    premise = "**前提：**主電源ボタンがオンになっていることを確認してください。"
    b.h("主電源ボタン/オフ")
    b.figure("use-power-button")
    b.add(panel("本製品のデフォルトの待機時間は2時間です（充電または放電がない場合、2時間後に自動的にシャットダウンします）。"
                "待機時間はJackeryアプリで設定できます。"),
          panel("省エネモードがオンのとき、AC出力またはDC/USB出力がオンでも、12時間連続して充放電が行われない場合は、"
                "自動的に電源がオフになります。"))
    b.h("AC出力のオン/オフ")
    b.add(panel(premise))
    b.figure("use-ac-output")
    b.h("50Hz/60Hz周波数の切り替え:")                                                        # p13
    b.add(panel("※ 工場出荷時のデフォルト設定は60Hzに設定されています。\n"
                "自動識別：お客様のお住まいの地域に応じて周波数を自動的に識別し、対応する出力に自動調整されます。\n"
                "手動調整：AC出力がオンの状態で、AC出力ボタンを5秒間長押しすることで周波数を切り替えることができ、対応する"
                "周波数が画面に表示されます。"))
    b.figure("use-frequency-switch")
    b.h("USB/カーポート出力オン/オフ")
    b.add(panel(premise))
    b.figure("use-dc-usb-output")
    b.callout("ご注意", UL(
        "USB-C 100W は、USB-PD Power Source 3（PS3）の高出力ポートです。接続されたユーザーデバイスまたはアクセサリーが"
        "安全基準を満たしていない場合、火災の危険性があります。これらのポートを使用する前に、接続するデバイスまたは"
        "アクセサリーに耐火安全保護が備わっていることを確認してください。",
        "Jackery ポータブル電源 900 は、IEC/EN/UL 62368-1（または同等の規格）の 6.3、6.4、6.5 条に準拠したデバイスまたは"
        "アクセサリーのみに接続してください。",
        "最大出力を得るためには、USB-C to USB-C 5A ケーブル（20V DC/5A、100W）を使用してください。"), variant="caution")
    b.add(P("本製品は、Jackery 12V 自動車用バッテリー充電ケーブル（別売り）を使用することで、車のバッテリーへの充電が"   # p14
            "可能です。\n"
            "※Jackery 12V 自動車用バッテリー充電ケーブルは付属しておりません。Jackery 公式サイトよりお求めいただけます。"))
    b.callout("ご注意", UL(
        "12V 車専用であり、24V 車には対応しておりません。",
        "本製品の 12V DC 出力（シガーソケット）から車のバッテリーへ充電中は、エンジンを始動しないでください。製品の故障に"
        "つながる恐れがあります。",
        "この機能はあくまで車のバッテリーの緊急補助用であり、深刻なバッテリー上がりや故障したバッテリーには対応して"
        "おりません。"), variant="caution")
    b.h("省エネモード")
    b.add(panel("省エネモードは、出力ボタンの消し忘れによる無駄なバッテリー消耗を防ぐための機能で、初期設定ではオンに"
                "なっています。AC出力が25W以下、またはDC/USB出力が2W以下の状態が12時間続くと、自動的に出力がオフに"
                "なります。ACまたはDC/USB出力がオンの状態では、画面に省エネアイコンが表示されます。アイコンの表示時間は、"
                "設定された省エネ時間に応じて変わります。省エネ時間は、Jackeryアプリで1H、2H、8H、12H、24Hに設定"
                "できます。「オフにしない」に設定すると、省エネモードは無効になります。"))
    # Three printed columns with one デフォルト設定 cell spanning both rows (declared plain table).
    default = "12時間経つとすべての出力は自動的にオフになります"
    b.add(plain_table([[cell("AC出力ポート"), cell("≤25W"), cell(default, row_span=2)],
                       [cell("DC/USB 出力ポート"), cell("≤2W")]],
                      head=[cell("出力ポートタイプ", header=True), cell("電力設定値", header=True),
                            cell("デフォルト設定", header=True)]))
    b.add(panel(
        node("paragraph", [text("※ 交流25Wおよび直流2W以下の低消費電力機器をご使用の場合、出力が途中で自動的にオフに"
                                "ならないように、省エネモードをオフにしてください。省エネモードをオフにすると、画面上の "),
                           icon("lcd-12h", "12H"), text(" アイコンは表示されなくなります。")]),
        "AC出力ボタンがオンの状態で、AC出力ボタンと主電源ボタンを同時に長押しし、省エネアイコンの表示（オン）／非表示"
        "（オフ）が切り替わるまで押し続けてください。"))
    b.figure("use-eco-mode-toggle")
    b.callout("説明", "省エネモードは電源投入後に前回の状態を維持します。モード変更には手動での切り替えが必要です。",
              variant="note")
    b.h("LEDライト")                                                                        # p15
    b.add(panel("LEDライトには、照明モードとSOSモードの2つのモードがあります。いずれのモードでも、LEDスイッチを長押しする"
                "ことでLEDライトを消灯できます。"))
    b.figure("use-led-light")
    # Numbered steps with their bulb / SOS pictograms (declared plain table).
    b.add(plain_table([[cell(number), node("table_cell", [icon(slot, alt)], header=False), cell(body)]
                       for number, slot, alt, body in (
                           ("①", "led-light-on", "点灯", "LEDスイッチを短く押すとLEDライトが点灯し"),
                           ("②", "led-sos", "SOS", "再度短く押すとSOSモードに切り替わります。"),
                           ("③", "led-light-off", "消灯", "再度短く押すとでライトが消灯します。"))]))
    b.h("LCDスクリーン")
    b.used_figures.append("use-lcd-screen")
    groups = [{**pair(state, "state"), "actions": [{**pair(a, "action"), **pair(d, "description")} for a, d in acts]}
              for state, acts in [
        ("短くオン", [("オンにする", "主電源ボタンを押すか、充電入力がある場合。"),
                     ("オフにする", "主電源ボタンを押します。"),
                     ("自動オフ", "2分後にLCDは自動的に消灯し、\nスリープモードになります。")]),
        ("常時オン", [("オンにする", "デバイスが起動している状態で主電源ボタンを2回押します。"),
                     ("オフにする", "主電源ボタンを押します。"),
                     ("自動オフ", "常時点灯ディスプレイモードは、2時間操作がないと自動的に消灯します。")]),
    ]]
    b.comp(lcd_mode_component_spec, accessibility_label="LCDスクリーン", groups=groups,
           artwork_ref=b.figures["use-lcd-screen"]["local_path"], artwork_locale_policy="exact")
    b.add(P("Jackeryアプリで画面表示モードを設定することもできます。"))
    b.h("ボタン操作")                                                                        # p16
    headers = ["ボタン", "操作", "機能"]
    keys = [("主電源ボタン", "AC出力ボタン", "3s", "両方を3秒間長押し", "省エネモードのオン / オフを切り替えます"),
            ("主電源ボタン", "DC/USB出力ボタン", "3s", "両方を3秒間長押し", "Wi-Fiのリセット"),
            ("AC出力ボタン", "DC/USB出力ボタン", "1s", "両方を1秒間長押し", "Wi-Fi&Bluetooth オン / オフ"),
            ("主電源ボタン", "ライトボタン", "1s", "両方を1秒間長押し", "緊急急速充電モードのオン／オフを切り替えます")]

    # Button names stand in for the printed button pictograms (plain cell; the ＋ is the printed plus).
    body = [node("table_row", [
        node("table_cell", [node("strong", [text(first)]), text(" ＋ "), node("strong", [text(second)])],
             header=False),
        node("table_cell", [node("paragraph", [text(duration)], presentation={"html": {"attributes": {
            "class": "hb-key-duration", "data-duration-icon": "clock"}}}), node("paragraph", [text(operation)])],
            header=False),
        node("table_cell", [text(function)], header=False)]) for first, second, duration, operation, function in keys]
    carrier = node("table", [node("table_head", [node("table_row", [
        node("table_cell", [text(h)], header=True) for h in headers])]), node("table_body", body)],
        presentation={"html": {"attributes": {"class": "hb-key-combination-table"}}})
    b.comp(key_combinations_component_spec, lambda spec: (carrier,), headers=headers,
           rows=[[f"{first} ＋ {second}", f"{duration} {operation}", function]
                 for first, second, duration, operation, function in keys])

    # ---- p16-17 UPS 機能 -------------------------------------------------------------------------
    b.chapter("ups", "UPS 機能", [16, 17])
    b.figure("ups-wiring")
    b.add(P("電気製品のコンセントをポータブル電源の AC 出力ポートに接続し、ポータブル電源の AC 入力ポートを家庭のコンセントに"
            "つなぐことで、停電時などにポータブル電源を予備電源として活用できます。"))
    b.add(panel(                                                                            # p17
        "本製品は、電気系統（家庭内の電源など）が突然停止した場合、自動的にバッテリー給電モードに切り替わる UPS（無停電"
        "電源装置）機能を備えています。切替時間は約 10 ミリ秒（0.010 秒）以内です。ただし、本機能は 0ms での完全な無停止"
        "給電には対応しておりません。そのため、以下のような高精度な連続電源供給を必要とする機器への接続はお控えください。",
        UL("データサーバー", "ワークステーション", "医療機器など",
           "その他、停電・瞬断の許容時間が 10ms 以下の精密機器 / 業務機器全般"),
        "これらの機器でご使用を希望される場合は、事前に複数回の動作テストを実施し、機器との互換性をご確認の上でご使用"
        "ください。",
        "※記載の手順に従わずに機器が正常に動作しなかったり、データ消失などの損害が発生した場合、弊社では責任を負いかね"
        "ます。あらかじめご了承ください。\n"
        "UPS  として使用している際はパススルー機能により充電と出力が同時に行われている状態のため、ポータブル電源の最大"
        "出力電流は 15A に制限され、停電時には定格出力に戻ります。複数の機器を UPS モードで同時に接続する場合は、合計負荷"
        "電流が 15A を超えないようにしてください。超えると、機器が過負荷保護により停止するおそれがあります。"))

    # ---- p17-21 充電方法 ---------------------------------------------------------------------------
    b.chapter("charging", "充電方法", [17, 18, 19, 20, 21])
    b.add(P("**グリーンエネルギー優先モード:**\n"
            "本製品はグリーンエネルギー優先モードを搭載していますが、ソーラーパネルとAC充電ケーブルを使って同時に充電"
            "できます。同時に充電すると、ソーラーが優先されますが、バッテリーの最大許容電力で同時に充電されます。"))
    b.callout("ご注意", UL(
        "製品の充電動作温度範囲は0°C~45°C、放電動作温度範囲は-10°C~45°Cです。上限・下限温度を超えた場合、充放電が"
        "制限され、または充放電不可の可能性があります。",
        "温度によって、製品の充電効率と実際の容量は異なります。"), variant="caution")
    b.callout("ご注意", UL(
        "はじめてお使いになるときは、本製品をフル充電してからご使用ください。",
        "充電池は空の状態で長期保管(3カ月~6カ月）すると、性能が劣化したり、充電できなくなる場合があります。",
        "長期保管中は、電池残量が0%にならないよう、3か月に一度の充電をおすすめします。"), variant="caution")
    b.h("AC充電ケーブル")                                                                      # p18
    b.add(P("コンセントからJackery ポータブル電源 900本体へ充電する際は、電流容量が大きいため、他の機器との併用や途中での"
            "抜き差しはお控えください。コンセントの定格を超えることで充電停止が発生したり、配線やコンセント・接続部の発熱、"
            "火災の原因となるおそれがあります。電源タップの使用や他の電気製品との併用は避けてご使用ください。"))
    b.figure("charge-ac-cable")
    b.add(P("付属のAC充電ケーブルをご使用ください。"))
    b.callout("ご注意", "AC充電ケーブルのプラグが製品のAC入力ポートにしっかりと、かつ完全に差し込まれていることを確認して"
              "ください。差し込みが不完全な場合、電流の不安定、発熱、接触不良などが発生し、機器の正常な動作に支障をきたす"
              "恐れがあります。", variant="caution")
    b.add(P("**緊急急速充電モード：**\n"
            "ACコンセントからの充電時、お急ぎの場合には緊急充電モードを使って充電することができます。使用するには"
            "「Jackery　App」でこの機能を「有効」または「無効」に設定してください。緊急充電モードでは、バッテリーの残量"
            "(SOC)を示す円形のライトの点滅速度が速くなります。\n"
            "※バッテリーは通常の速度で充電することでバッテリーを最大限に保護できるよう設計されているため、緊急充電は必要"
            "場合にのみ使用し、常時使用することはお勧めしません。"))
    b.h("ソーラー充電")
    b.add(P("ソーラーパネル接続用のDC入力ポート（8020メス）×2を搭載しており、合計最大入力電力は400Wです。そのため、"
            "ソーラーパネル100Wの場合は最大4枚まで接続可能です。"),
          panel("■ 必要なアクセサリー",
                UL("1枚または2枚接続時：アクセサリー不要、直接本体に接続可能です。",
                   "4枚接続時：別売りの「SolarSagaアダプター（Pro/Plus/New専用）」を2個ご用意いただく必要があります。"),
                "※Jackery SolarSagaアダプターを使って3枚接続はできません（電圧が許容範囲を超え、故障のリスクがあります）。"),
          P("■ 1枚または2枚接続時"),                                                         # p19
          UL("直接接続可能です。\n追加のアクセサリーは不要です。\n"
             "本製品のDC入力ポートは「8020メス」です。ソーラーパネル側の「8020オス」と接続してください。"))
    b.figure("charge-solar-2-panels")
    b.add(P("■ 4枚接続時"),
          UL(("別売りの「Jackery SolarSaga アダプター(Pro/Plus/New専用)」が必要です。",
              UL("「Jackery SolarSaga アダプター(Pro/Plus/New専用)」（オス・メス）とも8020端子です。",
                 "ソーラーパネルの8020オス端子を「Jackery  SolarSaga  アダプター(Pro/Plus/New専用)」の8020メス端子に"
                 "接続してください。"))))
    b.figure("charge-solar-4-panels")
    b.callout("ご注意", P("DC入力ポートの電圧を一致させてください\n"                                  # p20
                          "2つのDC入力ポートに接続する電源の電圧は必ず一致させてください。電圧が異なると、製品の異常動作や"
                          "故障の原因となる可能性があります。\n例："),
              UL("2つのDC8020入力ポートにソーラーパネルを接続する際は、同じ型番のJackery製ソーラーパネルを使用し、接続する"
                 "枚数も揃えてください。異なる型番や接続枚数で接続すると、電圧が不均一になり、製品が故障するおそれがあります。",
                 "車載充電器とソーラーパネルを同時に使用して製品を充電しないでください。車のヒューズが切れたり、充電が正常に"
                 "行われなかったりする可能性があります。",
                 "本製品は、日照が弱く、バッテリー残量が少ない状態でソーラーパネルを接続をした場合、バッテリーが過放電に"
                 "よって劣化する可能性があります。この場合はソーラーパネルの接続を外し、早めにACコンセント等を使って、充電"
                 "するようにしてください。"), variant="caution")
    b.add(P("Jackeryブランド以外の付属品を使用して充電しないでください。特に、ソーラーパネルで充電する際は、Jackeryの"
            "ソーラーパネルを使用することをお勧めします。ソーラーパネルの開放電圧（Voc）が、Jackery ポータブル電源 900の"
            "DC入力電圧範囲（16V〜60V）内に収まっていることを確認してください。他社ソーラーパネルで充電することによる損失に"
            "ついて、当社は一切の責任を負いません。"))
    b.h("シガーソケット充電")
    b.add(P("**■本製品は、車載シガーソケット（12V）からの充電に対応しています。\n（車載充電入力：11V〜16V、最大 8A）**"),
          P("ご使用の際は、以下にご注意ください。"),
          UL("必ず車のエンジンを始動させてから接続してください。エンジン停止状態で使用すると、車両のバッテリーが上がる恐れ"
             "があります。",
             "車の充電ポートとシガーソケット充電ケーブルの接触状態をご確認ください。",
             "ケーブルが確実に奥まで差し込まれていることをご確認ください。",
             "悪路などで車両の振動が激しい場合は、接触不良や発熱・焼損の恐れがあるため、充電を中止してください。",
             "誤使用による故障・損傷については、弊社では責任を負いかねます。あらかじめご了承ください。"))
    b.figure("charge-car-socket")
    b.callout("ご注意", UL(                                                                  # p21
        "シガーソケット充電とソーラー充電を同時に使用しないでください。同時に使用すると、車のヒューズが損傷する可能性が"
        "あります。",
        "シガーソケット充電は 12V, 10A 車専用で、24V 車は充電できません。人身傷害や物的損害を避けるため、本製品の充電に"
        " 24V 車を使用しないでください。"), variant="caution")

    # ---- p21 トラブルシューティング --------------------------------------------------------------
    b.chapter("troubleshooting", "トラブルシューティング", [21])
    b.add(P("次のいずれかのエラーコードが表示された場合は、記載されている対処方法に従って問題を解決してください。\n"
            "問題が解決しない場合は、Jackeryカスタマーサポートまでご連絡ください。"))
    faults = [
        ("F0 / F1\nF2 / F3", "製品を再起動してください。"),
        ("F4", "製品に負荷を接続してバッテリーを放電し、エラーが消えるまで続けてください。"),
        ("F5", "ソーラーパネルまたはAC電源コンセントを使用して、エラーが消えるまで製品を充電してください。"),
        ("F6", "1. AC 電源コンセントから充電する前に、電源供給が安定するのを待ってください。\n"
               "2. 吸気口および排気口が塞がれていないか確認し、製品の両側に 20cm のスペースを確保してください。\n"
               "3. 製品は日陰で通気の良い場所に設置し、周囲温度が 45°C未満であることを確認してください。\n"
               "4. 製品からすべての負荷を取り外し、アイドル状態にして、エラーが消えるまで待ってください。ご使用の機器の"
               "起動時消費電力が本製品の出力範囲を超えていないかをご確認ください。\n"
               "5. 製品を再起動してください。"),
        ("F7", "1. 製品からすべてのDC入力を取り外してください。\n"
               "2. ソーラーパネルで充電する場合は、接続されたソーラーパネルの開放電圧（V_{oc}）を確認してください。本製品の"
               "最大DC入力電圧は60Vです。\n"
               "3. 製品を再起動し、アイドル状態を保ってください。エラーが消えるまで待ってください。"),
        ("F8", "販売店またはJackeryカスタマーサポートにお問い合わせください。"),
        ("F9", "製品の DC/USB ポートに接続されている負荷を取り外してください。故障が消えるまで待機してください。"),
        ("FE", "販売店または Jackery カスタマーサポートにお問い合わせください。"),
    ]
    b.comp(troubleshooting_component_spec, headers=[pair("エラーコード", "content"), pair("対処方法", "content")],
           rows=[{**pair(code, "code"), **pair(measures, "measures")} for code, measures in faults])

    # ---- p22 主な仕様 ----------------------------------------------------------------------------
    b.chapter("specifications", "主な仕様", [22])
    for title, rows in [
        ("基本情報", [("製品の名称", "Jackery ポータブル電源 900"), ("型番", "JE-900B / JE-900B-WH"),
                      ("定格容量", "960Wh"), ("バッテリータイプ", "LiFePO₄（リン酸鉄リチウムイオン電池）"),
                      ("サイクル寿命", "4000回（4000回の充放電後も初期容量の70%以上を維持）"),
                      ("サイズ&重量", "約314 × 201 × 234 mm（約10.6 kg）")]),
        ("入力ポート", [("1×ACポート", "100V-120V~ 50Hz/60Hz, 最大15A"),
                        ("", "パススルー①：100V-120V~ 50Hz/60Hz, 最大15A"),
                        ("2×DC8020ポート", f"PV：16V-60V{DC}12A, 2ポート最大21A, 最大400W"),
                        ("", f"ｼｶﾞｰｿｹｯﾄ：11V-16V{DC}最大8A, 2ポート最大8A")]),
        ("出力ポート", [("3×ACポート", "100V~50Hz/60Hz, 最大15A, 定格1500W, 瞬間最大3000W"),
                        ("AC出力（パススルー）①", "100V-120V~ 50Hz/60Hz, 最大15A"),
                        ("USB-C 30Wポート", f"5V{DC}3A, 9V{DC}3A, 12V{DC}2.5A, 15V{DC}2A, 20V{DC}1.5A, 最大30W"),
                        ("USB-C 100Wポート", f"5V{DC}3A, 9V{DC}3A, 12V{DC}3A, 15V{DC}3A, 20V{DC}5A, 最大100W"),
                        ("1×USB-Aポート", f"5-6V{DC}3A, 6-9V{DC}2A, 9-12V{DC}1.5A, 最大18W"),
                        ("シガーソケット出力", f"12V{DC}最大10A")]),
        ("温度範囲", [("充電温度", "0°C~45°C"), ("動作温度", "-10°C ~ 45°C"),
                      ("保存温度", "1ヶ月 -20°C ~ 45°C"), ("", "3ヶ月 0°C ~ 45°C"), ("", "1年間 0°C ~ 25°C")]),
    ]:
        b.comp(spec_table_component_spec, spec_carrier, section_title=title, rows=rows)
    b.add(P("※ USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum."),
          P("① 本製品は、ACコンセントからバッテリーを充電しながら、AC出力ポートを通じて給電することができます。"))

    # ---- p23-24 保証について ---------------------------------------------------------------------
    b.chapter("warranty", "保証について", [23, 24])
    b.add(panel("このたびは Jackery 製品をご購入いただき、誠にありがとうございます。\n"
                "本保証書は、Jackery ポータブル電源製品に関する保証内容を明確にご案内するものです。\n"
                "ご使用前に必ずご確認のうえ、大切に保管してください。"))
    sections = [
        ("保証期間", blocks(
            "本製品の保証期間は以下の通りです。",
            ["電源本体：ご購入日より3年間", "付属品（AC充電ケーブルなど）：ご購入日より1年間"],
            "なお、延長保証にご登録いただいた場合、電源本体の保証期間はさらに2年間延長されます。",
            "※付属品（AC充電ケーブルなど）は延長保証の対象外です。",
            "詳細につきましては、公式サイトをご確認ください。")),
        ("保証の適用範囲", blocks(
            "1. 購入チャネルについて\n本保証は、Jackery公式オンラインストアまたは正規代理店で購入された製品に限り有効です。",
            "※ Jackery 公式オンラインストアまたは正規代理店以外での購入品は保証対象外となります。",
            "2. 保証提供地域\n保証は、日本国内に在住の方が、日本国内で使用する場合に限り有効です。")),
        ("保証の適用条件", blocks(
            "以下のすべての条件を満たす場合に、保証の適用対象となります。",
            ["Jackery公式オンラインストアまたは正規代理店にてご購入されたこと", "保証期間内であること",
             "下記の「保証対象外」に該当しないこと"])),
        ("保証対象外となる場合", blocks(
            "以下のいずれかに該当する場合、保証期間内であっても保証の対象外となります。",
            "1.故障・損傷が保証期間内に発生していても、保証期間終了後に申請された場合\n"
            "2.使用上の誤り（取扱説明書や本体ラベルに記載の注意事項に従わなかった使用）による故障・損傷\n"
            "3.他機器からの影響、不適切な修理または改造による故障・損傷\n"
            "4.移設・輸送・落下などに起因する故障・損傷\n"
            "5.火災・地震・風水害・落雷などの天災、または公害・塩害・異常電圧などによる故障・損傷\n"
            "6.消耗部品の劣化や摩耗、または外観の汚損など")),
        ("購入証明について", blocks(                                                         # p24
            "保証をご利用の際には、以下いずれかの購入証明書類をご提示いただく必要があります。",
            ["Jackery公式オンラインストアでの購入：注文番号（注文履歴画面または確認メール）",
             "正規代理店での購入：購入日・販売店名の記載された領収書または納品書"],
            "※ ご提示がない場合、保証対応いたしかねます。")),
        ("保証内容", blocks(
            "**1. 初期不良による交換**（ご購入日から30日以内）",
            ["取扱説明書に従った正常な使用中に不具合が発生した場合、同一製品の新品と交換いたします。",
             "在庫切れや販売終了の場合は、同等品への交換または返金にて対応いたします。"],
            "**2. 無償修理**（ご購入日から31日以上〜保証期間内）",
            ["保証条件を満たす自然故障については、無料で修理対応いたします。",
             "修理が困難な場合は、同等品（同モデルまたは同等スペック品）への交換にて対応いたします。"],
            "**3. 有償修理**\n以下に該当する場合は、有償での修理対応となります。",
            ["保証期間を超えた製品", "保証対象外と判断された場合",
             "Jackery公式オンラインストアまたは正規代理店以外で購入された製品"],
            "有償修理後の保証期間は、修理完了日より90日間です。",
            "*無償修理の場合、残りの保証期間が90日未満であれば「90日間」、90日以上であれば「元の保証期間に準じます」。")),
    ]
    for index, (title, body) in enumerate(sections, start=1):
        b.h(title)
        b.comp(warranty_section_component_spec, title=title, section_index=index, blocks=body)
    # The 免責事項 box title becomes its own subheading, so the box is not drawn inside the last warranty card.
    b.h("免責事項")
    b.add(panel("1. 弊社では、いかなる場合においても、間接的損害または付随的損害（データの損失・逸失利益など）に対して責任を"
                "負いません。",
                "2. 本保証書は、お客様が法律上有する権利を制限するものではありません。",
                "3. 保証内容は、予告なく変更される場合がございます。あらかじめご了承ください。",
                "Jackery 製品を安心してご使用いただくために、本保証書の内容をご確認のうえ、ご活用くださいますようお願い"
                "いたします。",
                "ご不明点がございましたら、Jackery カスタマーサービスまでお問い合わせください。"),
          panel("**公式サイト: https://www.jackery.jp**", "**カスタマーサポート: jackery.jp@jackery.com**",
                "**お問い合わせ電話番号: 050-3198-9007**"))

    # ---- p25-27 Jackeryアプリ ユーザーマニュアル ------------------------------------------------
    b.chapter("app_manual", "Jackeryアプリ ユーザーマニュアル", [25, 26, 27])
    b.h("1. アプリをダウンロードしてログインするには")
    columns = [{"role": "store", "text": "Google PlayまたはApp Storeで「Jackery」と検索し、アプリをインストールしてください。"
                                         "その後、登録とログインを行ってください。"},
               {"role": "qr", "text": "または、下の QR コードをスキャンしてアプリをダウンロードし、インストールしてください。"}]
    for column in columns:
        column["html"] = escape(column["text"])
    b.used_figures += ["app-store-badges", "app-qr-code"]
    store, qr = b.figures["app-store-badges"]["local_path"], b.figures["app-qr-code"]["local_path"]
    b.comp(app_download_component_spec,
           lambda spec: [node("image", source=qr, alt="Jackery App"), *(P(c["text"]) for c in columns)],
           accessibility_label="Jackery App", columns=columns, source_art_ref=qr, store_art_ref=store, qr_art_ref=qr)
    b.h("2. デバイスを追加するには")
    before, after = "2.1　APPの右上にあるデバイス追加ボタン", "をクリックします。"
    b.comp(app_inline_control_component_spec,
           lambda spec: [node("paragraph", [text(before + " "), node("strong", [text("+")]), text(" " + after)])],
           accessibility_label="+", paragraph_html=f"{escape(before)} <strong>+</strong> {escape(after)}",
           paragraph_text=f"{before} + {after}", metadata={"visual_recovery": "outlined-pdf-vector-plus-control"})
    b.add(P("2.2　デバイスの主電源ボタンを長押しして電源をいれると、ディスプレー画面にWi-FiとBluetoothのアイコンが点滅し、"
            "デバイスがネットワーク設定モードに入ったことを示します。アイコン点滅中ボタンをクリックし、アプリが近くの"
            "デバイスに接続し、Bluetoothのアクセス許可を開くことを許可します。"))
    b.figure("app-screen-2-1")
    b.figure("app-screen-2-2")
    b.figure("app-button-locator")
    b.add(P("**2.3 検出されたデバイスアイコンをクリックすると、アプリは自動的にBluetoothでデバイスを接続します。**"))
    b.callout("備考", "バインド処理中に「デバイスがバインドされました」と表示された場合は、以下の2つの方法で接続できます。",
              UL("デバイス所有者は、アプリを通じてこのデバイスを他のユーザーと共有します。",
                 "主電源ボタンとDC/USB出力ボタンを同時に3秒間押すと、Wi-FiとBluetoothが初期化されます。"),
              variant="note")
    b.add(P("**2.4  デバイスが正常に接続されると、デバイスが接続するWi-Fiの名前とパスワードを入力する必要があり、"   # p26
            "デバイスは自動的にWi-Fiネットワークに接続します。**"))
    b.callout("備考", "2.4GHz帯のWi-Fiネットワークを選択してください。デバイスは、5GHz帯のWi-Fiネットワークには対応して"
              "いません。", variant="note")
    b.add(P("**2.5  デバイスのホーム画面でデバイスが正常に追加されると、デバイスのWi-Fi  アイコンは常にオンになります。**"))
    b.figure("app-screen-2-3")
    b.figure("app-screen-2-4")
    b.figure("app-screen-2-5")
    b.add(P("上記のスクリーンショットはイメージです。"))
    b.callout("備考", "Jackeryアプリは、一度に1台のポータブル電源としかBluetooth接続できません。 デバイスリストに戻ると、"
              "自動的にBluetoothが切断されます。 リスト内のポータブル電源をもう一度タップすると、自動的に再接続されます。",
              variant="note")
    b.h("3. デバイスのバインドを解除するには")
    b.add(P("デバイスのメインインターフェースの右上隅にある「設定」ボタンをクリックして設定ページに入り、ページの下部にある"
            "「バインド解除」ボタンをクリックしてデバイスのバインドを解除します。"))
    b.h("4. Wi-Fi・Bluetoothの設定")
    b.add(P("**4.1 Wi-FiとBluetoothをオンにするには（ディスプレーにWi-FiとBluetoothのアイコンが点灯）：**"),
          UL("デバイスがオンになれば自動的にオンになり、ディスプレーにWi-FiとBluetoothのアイコンが点灯します。",
             "上記アイコンが点灯しない場合、ディスプレーにWi-FiとBluetoothのアイコンが点灯するまで、DC/USB出力ボタンと"
             "AC出力ボタンを同時長押しします。"),
          P("**4.2 Wi-FiとBluetoothをオフにするには（ディスプレーにWi-FiとBluetoothのアイコンが消える）：**"),
          UL("ディスプレーにWi-FiとBluetoothのアイコンが消えるまで、DC/USB出力ボタンとAC出力ボタンを同時長押しします。"),
          P("**4.3 Wi-FiとBluetoothをリセットするには：**"),
          UL("主電源ボタンとDC/USB出力ボタンを同時に3秒間押すと、Wi-FiとBluetoothが初期化され、接続されているポータブル"
             "電源はバインド解除されます。"))
    # p27 back cover: the App download note, store badges and QR code close the App chapter.
    b.add(P("本製品はJackeryアプリケーションによるスマートコントロールに対応しています。"),
          P("ご利用いただくには、下記のアプリストアより「Jackery」で検索して「Jackery アプリ」をダウンロードしてください。"))
    b.figure("back-store-badges")
    b.figure("back-qr-code")

    problems = b.finish()
    print("chapters", len(b.chapters), "problems", problems)
    return problems


if __name__ == "__main__":
    if make():
        raise SystemExit("figure records and transcription disagree")
