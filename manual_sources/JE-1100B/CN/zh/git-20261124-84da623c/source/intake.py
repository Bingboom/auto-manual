"""Verbatim source-bound transcription of the operator's outlined 000071 CN PDF.

Native shared components own prose, tables, callouts and App captions. Source-only
finished connection panels retain their complete borders and printed labels.
"""
from pathlib import Path
import hashlib
import html
import json
import sys

SOURCE = Path(__file__).resolve().parents[1]
REPO = next(p for p in SOURCE.parents if (p / 'build.py').is_file())
sys.path[:0] = [str(REPO), str(SOURCE / 'source')]
from kit import (Book, P, UL, OL, pair, cell_pair, inbox_carrier, spec_carrier)
from tools.web.frozen_ai_flow import node, text, table
from tools.component_specs.inbox import inbox_component_spec
from tools.component_specs.reference_table import reference_table_component_spec
from tools.component_specs.spec_table import spec_table_component_spec
from tools.component_specs.app import app_qr_download_component_spec
from tools.component_specs.reference_figure import reference_figure_component_spec
from tools.component_specs.reference_figure_adapters import web_reference_figure_projection
from tools.component_specs.model import ComponentSpec
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import flow_nodes_to_html
from tools.web.reference_figure_component import _component_contract, _validate_carrier
from tools.web.presentation import _transform_reference_figure
from tools.web.composite_presentation import WebCompositeContext
from bs4 import BeautifulSoup

AS = json.loads((SOURCE / 'source/reused-assets.json').read_text())

def group(css, *children):
    return node('group', list(children), role='container', presentation={'html': {'attributes': {'class': css}}})

def inbox_with_tip(spec):
    return [*inbox_carrier(spec), table([[node('table_cell', [text(str(spec.slot('tip_label').content))], header=False), node('table_cell', [text(str(spec.slot('tip_body').content))], header=False)]])]

def phones(b, slot, captions, centers):
    g = b.figures[slot]
    b.used_figures.append(slot)
    spec = reference_figure_component_spec(reference_id=slot, accessibility_label=g['caption'], caption_mode='live', captions=[cell_pair(v) for v in captions], adjacent_copy=None, source_art_ref=g['local_path'], source_art_locale_policy='exact', source_fragment_sha256=hashlib.sha256((SOURCE/g['local_path']).read_bytes()).hexdigest(), source_ref=f"transcribed-pdf/page-{g['physical_page']}/{slot}", language='zh', image_key=slot)
    flow = [node('image', source=g['local_path'], alt=g['caption'])]
    payload = web_reference_figure_projection(spec)
    payload.update(capture_following_lines=0, captions_origin='configured', composite_locale='')
    soup = BeautifulSoup(flow_nodes_to_html([{'schema_version': 'manual-flow/v2', **v} for v in flow]), 'html.parser')
    image = _validate_carrier(payload, soup)
    _transform_reference_figure(soup, image=image, spec=_component_contract(payload), source_path=Path(spec.source_ref), composites=WebCompositeContext(None, b.model, b.region, 'zh', ValueError))
    data = spec.to_dict()
    data['metadata'].update(capture_following_lines=0, captions_origin='configured', source_fragment_sha256=soup.figure['data-source-fragment-sha256'], caption_centers_pct=centers)
    b.add(component_flow_node(ComponentSpec.from_dict(data), carrier_flow=flow, root=True))

def make():
    b = Book(SOURCE, 'JE-1100B', 'CN', 'zh', '电小二户外电源 1100 Pro 2 · JE-1100B 用户指南')
    b.chapter('introduction', '前言', [2])
    b.current['nodes'].clear()
    b.add(P('感谢您选择购买电小二产品。在使用之前请您务必仔细阅读本用户指南，按照指引正确使用并妥善保管。'), P('在遵从法律法规的情况下，本公司享有对本文档及本产品所有相关文档的最终解释权。如有更新改版或终止请以官方发布最新通知为准。'), P('您现在可以通过微信注册您的产品，激活质保服务。注册过程轻松快速，注册后您将享有：'))
    qr = node('image', source=b.figures['registration-qr']['local_path'], alt='电小二产品注册二维码', presentation={'html': {'attributes': {'class': 'hb-registration-qr'}}})
    b.used_figures.append('registration-qr')
    b.add(group('hb-registration-panel', group('hb-registration-benefits', group('line-block', *[group('line', text(v)) for v in ['自购买日起享质保3年+注册延保2年', '电小二售后专家技术支持', '真伪查询服务', '售后维修进度实时查看']])), group('hb-registration-steps', qr, OL('打开微信，点击“发现”中的“扫一扫”', '扫描右方的二维码', '按照提示完成注册激活'))))
    b.add(P('如您未能成功注册，您可以联系电小二官方服务热线 **400-668-9293** 或联系在线客服进行注册，产品具体保修条款和注册细则，请登录 **电小二户外电源服务小程序** 查看。'), P('以下情况不在保修范围内：产品使用后外观损坏；自行拆机或维修；因人为原因造成产品性能故障；由于自然灾害、雷电、事故等不可抗拒的因素造成的损害。'))

    b.chapter('specifications', '1.技术参数', [2])
    rows = [['名称', '户外电源1100 Pro 2'], ['型号', 'JE-1100B'], ['电芯类型', '磷酸铁锂电芯'], ['电池组能量', '30.4Ah / 35.2V DC (1070Wh)'], ['AC 额定输出能量', '835Wh（220V~，6.81A）'], ['尺寸&重量', '约32.7 × 22.4 × 24.7 cm（约10.8kg）'], ['循环寿命', '4000次循环（70%+）'], ['AC 输入', '220V–240V~ 50Hz，10A Max'], ['DC 输入(8020端口)', '光伏 16V–60V/10.5A，双路21A/400W Max\n车充12V–16V/8A Max，双路8A Max'], ['2 × AC 输出', '220V~ 50Hz'], ['AC 总输出', '额定1500W，峰值3000W\n并机模式下，单口额定2200W，两个口合计额定3000W，峰值6000W'], ['USB-C1 输出', '30W Max，5V⎓3A，9V⎓3A，12V⎓2.5A，15V⎓2A，20V⎓1.5A'], ['USB-C2 输出', '100W Max，5V⎓3A，9V⎓3A，12V⎓3A，15V⎓3A，20V⎓5A'], ['USB-A 输出', '18W Max，5–6V⎓3A，6–9V⎓2A，9–12V⎓1.5A'], ['车充输出', '12V⎓10A'], ['充电温度', '0°C – 45°C'], ['放电温度', '−10°C – 45°C'], ['认证', 'UN38.3']]
    b.comp(spec_table_component_spec, spec_carrier, section_title='技术参数', rows=rows)
    b.add(P('※USB Type-C® and USB-C® are registered trademarks of USB Implementers Forum.'))

    b.chapter('product_overview', '2.产品介绍', [3, 4, 5, 6])
    b.h('2.1产品外观介绍'); b.figure('overview')
    b.h('2.2显示屏界面介绍'); b.figure('lcd-display')
    names = ['Wi-Fi', '蓝牙', '静音充电模式', '浅充浅放模式', '充电功率显示', '剩余充电时间', '市电充电接入', '车充充电接入', '太阳能（绿色能源）充电接入', '电池电量图标', '低电量提醒', '电池电量百分比', '故障代码', '高温警告', '低温警告', '节能模式', '交流输出符号', '放电功率显示', '剩余放电时间']
    descriptions = {3: '静音充电模式开启后，充电功率降低，充电速度减缓，同时显著降低充电时的噪音（请在APP中开启/关闭该功能）。', 4: '浅充浅放模式开启后，产品的可用电量减少，电芯使用寿命延长（请在APP中开启/关闭该功能）。', 10: '当本产品处于充电状态时，该图标顺时针转动；当产品处于放电状态时，该图标显示当前电量。', 11: '当电池容量低于20%时，低电量图标显示；当电池容量低于5%时，低电量图标闪烁；充电状态时，该图标不显示。', 13: '为了快速解决用户反馈，我们在系统中设置故障代码F0–FE：如果出现F8代码，请移除负载或者拔掉充电插头，产品可以自行恢复，如果不能，请联系售后处理；如果出现F9故障代码，请移除负载，产品可以自行恢复，如果不能，请联系售后处理。如果出现其他故障代码，请联系我们售后处理。', 14: '如果屏幕上出现高温警告图标，请勿担心，电池降温后可自行恢复。', 15: '如果屏幕上出现低温警告图标，请勿担心，环境温度恢复后自动恢复。', 16: '为避免使用过程中忘记关闭输出，导致电池电量耗完，产品默认是开启节能模式，即不连接任何设备或者连接的设备小于等于某个值时（详情参考下表），12H后系统自动关闭输出。'}
    from tools.web.prepared_style_audit import table_text_sha256
    catalog_rows = [[node('table_cell', [text(v)], header=True) for v in ['序号', '图标', '名称']]]
    for i, name in enumerate(names, 1):
        catalog_rows.append([node('table_cell', [text(str(i))], header=False), node('table_cell', [node('image', source=AS['lcd'][i-1], alt=name, presentation={'html': {'attributes': {'width': '40', 'height': '40'}}})], header=False), node('table_cell', [text(name)], header=False)])
    catalog = table(catalog_rows)
    b.add(catalog)
    exceptions = [{'language': 'zh', 'page_id': 'product_overview', 'kind': 'table', 'text_sha256': table_text_sha256(catalog), 'reason': 'The printed LCD catalog has only number, icon and name, with no separate description column. HB-TABLE-LCD-ICON requires a description; HB-TABLE-REFERENCE/lcd-legend rejects images. Preserve this exact label-only catalog as a native table using the shared theme and byte-identical shared icons; retain the printed explanation paragraphs separately without fabricating or repeating descriptions.'}]
    b.add(P('**电池电量图标：** ' + descriptions[10]), P('**低电量提醒：** ' + descriptions[11]), P('**节能模式：** ' + descriptions[16]))
    b.comp(reference_table_component_spec, variant='lcd-actions', label='节能模式默认关闭阈值', headers=[cell_pair(v) for v in ['放电方式', '功率设定值', '默认设置']], rows=[[cell_pair(v) for v in row] for row in [['AC输出', '≤25W', '12H后自动关闭输出'], ['USB输出', '≤2W', '12H后自动关闭输出'], ['车充输出', '≤2W', '12H后自动关闭输出']]])
    b.add(P('**关闭“节能模式”：** 任意输出打开时，长按“AC输出电源键+总电源开关键”直至节能模式图标消失。在非节能模式状态下，不使用本产品时请注意关闭电源，避免因为忘记关闭输出导致电量耗尽。'), P('**开启“节能模式”：** 任意输出打开时，长按“AC输出电源键+总电源开关键”直至节能模式图标在屏幕出现。'))
    b.add(P('**故障代码：** ' + descriptions[13]), P('**高温警告：** ' + descriptions[14]), P('**低温警告：** ' + descriptions[15]), P('**静音充电：** ' + descriptions[3]), P('**浅充浅放：** ' + descriptions[4]))
    b.h('2.3产品使用介绍')
    b.h('2.3.1电源开机/关机', level=4)
    b.add(P('**总电源开机/关机：** 短按“总电源开关键”同时工作指示灯亮起，LCD显示屏被点亮。当本产品持续2分钟没有任何操作时，产品进入休眠状态，显示屏自动熄灭。如需关闭总电源，请长按“总电源开关键”直至工作指示灯熄灭。本产品的默认待机时间为2小时，若产品无任何充电输入或放电输出，2小时后将自动关机，自动关机时间可以在APP上设置。'), P('*节能模式下，开启DC输出或AC输出，若产品无任何充电输入或放电输出，12小时后将自动关机，请在APP中设置节能模式的自动关闭时间。'), P('**AC输出开/关：** 确保总电源开启后，短按AC输出电源键，AC输出工作指示灯亮起，此时可连接需要交流电的设备使用。再次短按AC输出电源键可关闭AC输出。'), P('**DC输出开/关：** 短按DC/USB输出电源键打开直流电源，此时USB-A、USB-C和车充输出端口可以连接负载设备使用。再次短按DC/USB输出电源键关闭输出。'))
    b.callout('注意', '本产品可通过电小二12V汽车电池充电线为汽车电池充电。该充电线需单独购买，可前往电小二官网选购。设备通过12V DC输出（车充口）为汽车电池补电时，请勿启动汽车，否则可能造成产品损坏。', variant='caution')
    b.h('UPS', level=4)
    b.add(P('本产品通过AC电源线连接电网，电器可以使用本产品的交流输出端口工作（此时交流电来自电网，而不是电池），当电网突然断电后，产品可以在20ms内自动切换为本产品电池供电模式。由于本产品不支持0ms的切换，请勿接到需要不间断供电要求高的设备上，例如数据服务器和工作站，或者请多次测试后确认是否兼容后再使用，且使用过程中建议只使用一台设备，不要同时使用多台设备以免引发本产品过载保护，如果没有按照指示操作造成设备不能正常运行或者数据丢失，本公司不承担相应的责任。'), P('停电前，储能的最高输出功率是1500W，因为这边应用下采用的是旁路功率，虽然额定功率是1500W，但在这种特定模式下，实际输出功率会低于额定功率；停电时，储能的输出功率为额定功率1500W。'))
    b.h('2.3.2显示屏亮起/熄灭', level=4)
    b.add(P('短按总电源开关键或者有充电输入时，屏幕都会亮起，再按一下，屏幕会熄灭，或者持续2分钟无任何操作后，产品进入休眠状态，显示屏也会自动熄灭。在充电或者放电状态下如需要屏幕常亮，操作步骤如下：在显示屏亮起后，双击“总电源开关键”，屏幕进入常亮模式。如需关闭屏幕的常亮模式，操作步骤如下：短按“总电源开关键”，屏幕将自动熄灭。'))
    b.callout('注意', '在屏幕常亮模式下，不进行任何充电输入或连接负载的放电操作，持续2H后屏幕自动熄灭。', variant='caution')
    b.h('2.3.3 LED照明灯开启及关闭', level=4)
    b.add(P('**LED照明灯共有三种模式：** 低亮模式、高亮模式和SOS模式。'), P('短按LED开关键同时LED灯亮起，默认为低亮模式，再次短按LED开关键依次切换为高亮、SOS模式及关闭LED灯。在其中任何一种模式开启期间，长按LED开关键都可以关闭LED灯。'))

    b.chapter('parallel', '3.并机操作说明', [6, 7])
    b.callout('警告', UL('并机模式下无法进行AC充电，可进行DC充电。', '请勿在AC输出开启时（AC按键指示灯亮起时）用手触摸并机线插入口，此处为220V高压，存在触电风险！'), variant='warning')
    b.h('3.1 并机'); b.figure('parallel')
    b.h('3.2 退出并机'); b.add(P('退出并机前，先移除所有负载设备，关闭两台户外电源的AC输出，然后依次拔出并机线。'))
    b.h('3.3 注意事项')
    b.add(UL('**并机线需单独购买，** 请访问电小二官方网站购买，或联系电小二官方客服获取帮助。', '连接并机线前，请确保两台设备的AC输出已关闭（AC按键指示灯熄灭），否则可能损坏设备。并机成功后，如未关闭AC输出就拔掉并机线，可能会触发过载保护。', '插入并机线后，两台设备会默认进入并机准备模式。此时，需两台设备的AC输出均打开后，才能进行并机输出；仅打开其中一台设备的AC输出无法进行并机输出。', '若插上并机线且并机失败，显示屏将显示故障代码FA。', '并机过程中，如任意一台设备的AC输出被关闭或出现故障，系统将自动退出并机模式，另一台设备也会自动关闭AC输出，并显示故障代码FA。此过程不会影响DC输出。如需重新并机，请再次按下两台设备的AC按键。', '关闭AC输出后，如需重新开启，必须等待5秒，以确保正常输出电压。若未按此操作，AC输出可能无法正常工作。'))

    b.chapter('charging', '4.充电方式', [7, 8, 9])
    b.add(P('**绿色能源优先模式：** 本产品倡导优先使用绿色能源，本产品支持太阳能充电与市电充电同时使用。当同时开启市电充电与太阳能充电时，产品会优先太阳能充电且太阳能充电与市电充电同时以电池最大允许功率充电。'))
    b.add(P('**温馨提示：**'), OL('产品充电环境温度为0°C–45°C，放电环境温度为−10°C–45°C，超出此温度范围会限制产品充放电，甚至无法充放电。', '产品的充电功率和电池能量会因温度的变化有所差异。'))
    b.callout('提示', '**首次使用前请先将本设备充满电！**', variant='tip')
    b.h('4.1市电充电'); b.add(P('请使用官方标配的AC电源线。'))
    b.h('应急闪充模式', level=4)
    b.add(P('储能可以通过AC充电方式实现超速充电，**请在电小二App上激活或关闭此功能。** 应急闪充模式下，显示剩余电量的环形灯闪烁速度加快。'), P('*以正常充电速度充电能最大程度保护电池。我们建议仅在必要时使用应急充电，不建议长期使用此功能。')); b.figure('ac-charge')
    b.h('4.2太阳能充电')
    b.add(P('本产品有两个DC8020直流输入端口，每个DC8020直流输入口支持一块100W或一块200W太阳能板直接接入使用，当一个DC8020输入口需要同时接入两块100W太阳能板时，需要搭配太阳能串联转接盒（单独售卖）使用。')); b.figure('solar-direct'); b.figure('solar-four')
    b.callout('注意', '请确保DC输入端口的电压一致，连接到两个DC输入端口的电源，其电压必须保持一致，否则可能导致产品异常或损坏。', P('例如：'), OL('连接太阳能板至两个DC8020输入端口时，必须使用相同型号的Jackery太阳能板，并确保连接的数量一致。否则，不同型号或数量不匹配可能导致电压不一致，从而损坏产品。', '给产品充电时，请勿同时使用车充充电与光伏充电，否则可能烧坏车内保险丝或导致充电失败。'), variant='caution')
    b.figure('solar-mismatch'); b.figure('solar-car-mixed')
    b.h('4.3车充充电')
    b.add(P('本产品适用12V车型车充口对本产品进行充电，请在汽车点火启动后使用车充充电，以免造成汽车电瓶亏电无法启动。同时请确保汽车车充口和车充线的点烟器接触良好，确保点烟器完全插入到位，如汽车在行驶过程中，路况颠簸，禁止使用车充充电，防止车充接触不良，引起接触点烧坏。若因不按规范操作而造成损失，本公司不予承担相应责任。')); b.figure('car-charge')
    b.h('4.4充电注意安全事项')
    b.add(OL('请勿同时使用车充与太阳能充电，否则，会损坏车内保险丝。', '车充充电只支持12V车型，不支持24V车型，请勿用24V车型的车给本产品充电以免造成人身伤害及财产损失。', '请勿使用非电小二品牌的配件进行充电，尤其在使用太阳能板充电时，建议使用电小二品牌的太阳能板进行充电，对于使用其他品牌的太阳能板充电造成的损失，本司概不负责。'))

    b.chapter('safety', '5.使用注意安全事项', [9])
    b.add(P('**使用本产品时，应始终遵循基本注意事项，包括：**'), OL('使用本产品之前，请阅读所有说明。', '为了降低风险，当在儿童附近使用本产品时，需要进行密切监督。', '使用非专业产品制造商推荐或销售的配件可能会导致触电的风险。', '产品在未使用时，请将电源插头拔出产品插座。', '禁止对产品进行拆机，产品拆机后可能会导致火灾、爆炸或触电等不可预测的风险。', '禁止使用损坏的电线或插头，或损坏的输出电缆来使用产品，有触电的危险。', '请在通风良好的地方对产品进行充电，请勿以任何方式限制产品的通风。', '请将产品放置在干燥的地方，不得淋雨，不得使产品进水，这会有触电风险（非预定仅在室外安装使用）。', '禁止将产品撞击或投入火中，这可能导致产品发生起火，爆炸等安全事故。', '禁止在高温下（直热的阳光下或很热的汽车车内）使用或放置产品，否则可能会引起内部电池过热、起火或功能失效，寿命减短等风险。', '首次使用时，请在使用前将设备充满电。如果本产品在电量耗尽的情况下长时间（3个月–6个月）存放，其性能会下降，甚至无法充电。'))

    b.chapter('in_the_box', '6.包装清单', [9])
    slots = ['inbox-unit', 'inbox-ac', 'inbox-manual']; b.used_figures += slots
    b.comp(inbox_component_spec, inbox_with_tip, accessibility_label='包装清单', cards=[{'image_ref': b.figures[s]['local_path'], 'label': b.figures[s]['caption'], 'alt': b.figures[s]['caption']} for s in slots], tip_label='说明', tip_body='车载充电线需单独购买，请前往电小二官网购买或联系电小二售后客服寻求帮助。', require_tip=True)

    b.chapter('app', 'APP操作说明书', [10, 11])
    b.h('1. 下载并登录App')
    b.used_figures.append('app-download')
    b.comp(app_qr_download_component_spec, lambda _: [P('在App Store或者国内各大应用市场搜索“电小二”App安装并注册登录。或扫描下图二维码下载安装。'), node('image', source=b.figures['app-download']['local_path'], alt='电小二App下载二维码')], label='下载电小二App', paragraph=cell_pair('在App Store或者国内各大应用市场搜索“电小二”App安装并注册登录。或扫描下图二维码下载安装。'), image_ref=b.figures['app-download']['local_path'])
    b.h('2. 添加设备')
    b.add(P('**2.1 在App内点击 ＋ 添加设备。**'), P('**2.2 短按设备上的“POWER”键开机，设备上的WiFi和蓝牙图标闪烁后表示设备已进入配网模式，在App内点击“图标已快闪”按钮并允许应用连接附近的设备和打开蓝牙权限。**'))
    phones(b, 'app-phones', ['2.1', '2.2'], [19.3, 80.7])
    b.callout('备注', '打开设备，如果两小时内未连接到APP，设备会自动关闭Wi-Fi和蓝牙，长按“DC/USB输出电源键”和“AC输出电源键”重新打开Wi-Fi和蓝牙。', variant='note')
    b.figure('app-controls')
    b.add(P('**2.3 点击搜索到的设备图标后App通过蓝牙自动连接设备。**'))
    b.callout('备注', P('如果在绑定过程中提示“设备已被绑定”，可通过以下两种方式连接：'), UL('设备拥有者通过App将此设备分享给其他用户；', '长按“POWER开关键”和“DC/USB输出电源键”3秒重置设备后可重新绑定设备。'), variant='note')
    b.add(P('**2.4 设备连接成功后输入设备将要连接的WiFi名称和密码，设备自动连接到WiFi网络。**'))
    b.callout('备注', '请选择2.4GHz频段的Wi-Fi网络，设备不支持5GHz频段的Wi-Fi网络。', variant='note')
    b.add(P('**2.5 设备添加成功后进入设备主页面，设备上的Wi-Fi图标会常亮。**'))
    phones(b, 'app-results', ['2.3', '2.4', '2.5'], [14.9, 49.9, 85.1]); b.add(P('图片仅供参考'))
    b.h('3. 解绑设备')
    b.add(P('点击设备主界面右上角的设置按钮进入设置页面，点击页面最下方的解除绑定按钮解绑设备。'))
    b.h('4. 其他说明')
    b.h('4.1 打开WiFi&蓝牙：', level=4)
    b.add(UL('开机后自动打开WiFi&蓝牙，屏幕上的WiFi&蓝牙图标点亮表示WiFi&蓝牙已被打开。', '同时按DC/USB输出电源按键和AC输出电源按键，直到屏幕上的WiFi&蓝牙图标点亮表示WiFi&蓝牙已被打开。'))
    b.h('4.2 关闭WiFi&蓝牙：', level=4)
    b.add(UL('同时按DC/USB输出电源按键和AC输出电源按键，直到屏幕上的WiFi&蓝牙图标熄灭表示WiFi&蓝牙已被关闭。', '两小时内未连接WiFi或蓝牙，设备上的WiFi&蓝牙图标会自动关闭。'))
    b.h('4.3 重置WiFi&蓝牙：', level=4)
    b.add(UL('同时按下“POWER开关键”和“DC/USB输出电源按键”3秒，已连接的APP账号会被解绑，系统会重置Wi-Fi和蓝牙，同时清除所有数据。'))

    b.chapter('contact', '制造商与服务信息', [12])
    b.figure('certificate')
    b.used_figures.append('service-qr')
    code = node('figure', [node('image', source=b.figures['service-qr']['local_path'], alt='电小二官方品牌公众号二维码'), node('caption', [node('small_text', [text('关注官方品牌公众号，'), node('line_break'), text('获取更多资讯服务。')])])], anchor='native-contact-code')
    details = P('制造商/生产厂：深圳市华宝新能源股份有限公司\n地址：深圳市龙华区大浪街道同胜社区华繁路东侧嘉安达科技工业园')
    b.add(node('group', [code, node('group', [details], role='container', anchor='native-contact-details')], role='container', anchor='native-contact-layout'))
    manifest = json.loads((SOURCE/'source_manifest.json').read_text())
    manifest['shared_component_exceptions'] = exceptions
    (SOURCE/'source_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    b.add(P('www.dx2.cn'))
    issues = b.finish(extra={'transcription': 'outlined-pdf-manual-transcription', 'approved_errata': [{'physical_page':10,'section':'App 2.2','before':'长按设备上的“POWER”键开机','after':'短按设备上的“POWER”键开机','operator_quote':'统一为“短按”（推荐）','operator_date':'2026-11-24'}], 'source_copy_note': 'App step2.2 corrected to short press by explicit operator confirmation; remaining source wording preserved.'})
    if issues: raise ValueError(issues)
    return {'chapters': len(b.chapters), 'figure_slots': len(b.figures), 'used_figures': len(b.used_figures)}

if __name__ == '__main__':
    print(json.dumps(make(), ensure_ascii=False))
