"""Source-bound CN DX2 Web transcription; only the two operator-approved page15 copy edits."""
from pathlib import Path
import json,sys,re,html,hashlib
import fitz
REPO=next(p for p in Path(__file__).resolve().parents if (p/'build.py').is_file())
sys.path.insert(0,str(REPO));sys.path.insert(0,str(Path(__file__).resolve().parent))
from kit import P,UL,OL,Book,pair,cell_pair,inbox_carrier,spec_carrier,reference_flow
from tools.web.frozen_ai_flow import node,text,table
from tools.component_specs.reference_figure import reference_figure_component_spec
from tools.component_specs.reference_figure_adapters import web_reference_figure_projection
from tools.component_specs.model import ComponentSpec
from tools.manual_ir.components import component_flow_node
from tools.manual_ir.flow import flow_nodes_to_html
from tools.web.reference_figure_component import _component_contract, _validate_carrier
from tools.web.presentation import _transform_reference_figure
from tools.web.composite_presentation import WebCompositeContext
from bs4 import BeautifulSoup
from tools.component_specs.inbox import inbox_component_spec
from tools.component_specs.manual_tables import lcd_icon_component_spec,symbol_icon_component_spec,troubleshooting_component_spec
from tools.component_specs.spec_table import spec_table_component_spec
from tools.component_specs.lcd_mode import lcd_mode_component_spec
from tools.component_specs.auto_resume import auto_resume_component_spec
from tools.component_specs.key_combinations import key_combinations_component_spec
from tools.component_specs.app import app_qr_download_component_spec

SOURCE=Path(__file__).resolve().parents[1]
AS=json.loads((SOURCE/'source/reused-assets.json').read_text())
DOC=fitz.open(SOURCE/'original.pdf')

def clean(s):
    lines=[v.strip() for v in s.splitlines() if v.strip()]
    out=''
    for line in lines:
        if out and re.search(r'[A-Za-z0-9]$',out) and re.match(r'[A-Za-z0-9]',line):out+=' '
        out+=line
    return out

def source_clip(p,box):
    return clean(DOC[p-1].get_text(clip=fitz.Rect(box),sort=True))

def source_bullets(p,box):
    s=DOC[p-1].get_text(clip=fitz.Rect(box),sort=True)
    return [clean(v) for v in s.split('•') if v.strip()]

def add_paras(b,*ss):b.add(*[P(x) for x in ss if x])

def inbox_with_tip(spec):
    return [*inbox_carrier(spec),table([[node('table_cell',[text(str(spec.slot('tip_label').content))],header=False),node('table_cell',[text(str(spec.slot('tip_body').content))],header=False)]])]


def shared_group(css,*children):
    return node('group',list(children),role='container',presentation={'html':{'attributes':{'class':css}}})

def app_phones_with_captions(b):
    g=b.figures['app-phones'];b.used_figures.append('app-phones')
    spec=reference_figure_component_spec(reference_id='app-phones',accessibility_label=g['caption'],caption_mode='live',captions=[cell_pair('2.1'),cell_pair('2.2')],adjacent_copy=None,source_art_ref=g['local_path'],source_art_locale_policy='exact',source_fragment_sha256=hashlib.sha256((SOURCE/g['local_path']).read_bytes()).hexdigest(),source_ref='transcribed-pdf/page-17/app-phones',language='zh',image_key='app-phones')
    flow=[node('image',source=g['local_path'],alt=g['caption'])]
    payload=web_reference_figure_projection(spec);payload.update(capture_following_lines=0,captions_origin='configured',composite_locale='')
    soup=BeautifulSoup(flow_nodes_to_html([{'schema_version':'manual-flow/v2',**v} for v in flow]),'html.parser')
    image=_validate_carrier(payload,soup)
    _transform_reference_figure(soup,image=image,spec=_component_contract(payload),source_path=Path(spec.source_ref),composites=WebCompositeContext(None,b.model,b.region,'zh',ValueError))
    data=spec.to_dict();data['metadata'].update(capture_following_lines=0,captions_origin='configured',source_fragment_sha256=soup.figure['data-source-fragment-sha256'],caption_centers_pct=[19.3,80.7])
    b.add(component_flow_node(ComponentSpec.from_dict(data),carrier_flow=flow,root=True))

def make():
    b=Book(SOURCE,'JE-1000F','CN','zh','电小二户外电源 1000 Pro 3 · JE-1000F 用户指南')
    b.chapter('introduction','前言',[3])
    # The source opens with prose, without an added chapter title or warranty frame.
    b.current['nodes'].clear()
    b.serial += 1  # Preserve following source references after removing the former warranty component.
    add_paras(b,'感谢您选择购买电小二产品。在使用之前请您务必仔细阅读本用户指南，按照指引正确使用并妥善保管。',
      '在遵从法律法规的情况下，本公司享有对本文档及本产品所有相关文档的最终解释权。如有更新改版或终止请以官方发布最新通知为准。',
      '您现在可以通过微信注册您的产品，激活质保服务。注册过程轻松快速，注册后您将享有：')
    def registration_group(css,*children):
      return node('group',list(children),role='container',presentation={'html':{'attributes':{'class':css}}})
    benefits=['自购买日起享质保3年+注册延保2年','电小二售后专家技术支持','真伪查询服务','售后维修进度实时查看']
    qr=node('image',source=b.figures['registration-qr']['local_path'],alt='电小二产品注册二维码',presentation={'html':{'attributes':{'class':'hb-registration-qr'}}})
    b.used_figures.append('registration-qr')
    b.add(registration_group('hb-registration-panel',
      registration_group('hb-registration-benefits',registration_group('line-block',*[registration_group('line',text(v)) for v in benefits])),
      registration_group('hb-registration-steps',qr,OL('打开微信，点击“发现”中的“扫一扫”','扫描右方的二维码','按照提示完成注册激活'))))
    add_paras(b,'如您未能成功注册，您可以联系电小二官方服务热线400-668-9293或联系在线客服进行注册，产品具体保修条款和注册细则，请登录电小二户外电源服务小程序查看。',
      '以下情况不在保修范围内：产品使用后外观损坏；自行拆机或维修；因人为原因造成产品性能故障；由于自然灾害、雷电、事故等不可抗拒的因素造成的损害。')

    b.chapter('safety','使用注意安全事项',[3])
    b.add(P('使用本产品时，应始终遵循基本注意事项，包括：'))
    bullets=source_bullets(3,[22,248,346,501]);assert len(bullets)==15,len(bullets)
    b.add(UL(*bullets))

    b.chapter('symbols','符号含义',[4])
    meanings=[
      '警告／注意：请阅读并遵守安全说明，以避免潜在的危险。',
      '使用本产品之前，请阅读所有说明。',
      '废弃电池（产品）不可作为生活垃圾丢弃，请交由专门的回收机构处理。',
      '本产品内置锂离子电池，废弃时请妥善回收处理。',
      '本产品的环保使用期限为10年。在此期限内，产品中含有的有害物质不会发生外泄或突变，用户正常使用本产品不会对环境造成严重污染，也不会对人身、财产造成严重损害。']
    panels=[[],[]]
    for i,m in enumerate(meanings):panels[0 if i<3 else 1].append({'asset_index':i,'icon_alt':['警告／注意','阅读说明','废弃电池回收','Li-ion回收','环保使用期限10年'][i],**pair(m,'meaning')})
    b.comp(symbol_icon_component_spec,accessibility_label='符号含义',headers=[pair(x,'content') for x in ['符号','含义','符号','含义']],panels=panels,icon_refs=AS['symbols'])
    b.h('用户维护说明')
    b.add(P('储能产品使用生命周期过程中，会有一定的容量和能量衰减，随着使用次数增长和存储时间延长衰减增加，这是符合电芯衰减趋势的正常现象。'))

    b.chapter('in_the_box','包装清单',[4])
    slots=['inbox-unit','inbox-ac','inbox-manual']
    cards=[{'image_ref':b.figures[x]['local_path'],'label':b.figures[x]['caption'],'alt':b.figures[x]['caption']} for x in slots]
    b.used_figures+=slots
    b.comp(inbox_component_spec,inbox_with_tip,accessibility_label='包装清单',cards=cards,tip_label='说明',tip_body='车载充电线需单独购买，请前往电小二官网选购或联系电小二售后客服寻求帮助。',require_tip=True)
    b.chapter('product_overview','产品介绍',[5])
    b.figure('overview-front');b.figure('overview-input')

    b.chapter('lcd_display','显示屏界面',[6,7]);b.figure('lcd-display')
    names=['Wi-Fi','蓝牙','静音充电模式','充电计划','自发自用模式','TOU模式','UPS','交流输出符号','输出电压和频率','充电功率显示','剩余充电时间','市电充电接入','车充充电接入','太阳能（绿色能源）充电接入','节省电池模式','充电速度限制','电池电量图标','低电量提醒','电池电量百分比','放电倒计时','节能模式','高温警告','低温警告','故障代码','放电功率显示','剩余放电时间']
    # Exact source row boundaries; the printed row22 spans its high/low subrows.
    bounds6=[222.46,253.47,283.44,322.97,354.2,394.0,463.3,497.32]
    # Page6's last four borders are read from the native table geometry at intake, stored below.
    import importlib.util
    raw=json.loads((SOURCE/'source/lcd-rows.json').read_text())
    rows=[]
    numbers=list(range(1,23))+[22,23,24,25]
    assert len(numbers)==len(names)==len(raw)==len(AS['lcd'])==26
    for i,(name,r,n) in enumerate(zip(names,raw,numbers)):
      desc=r['description']
      entry={**pair(str(n),'number'),**pair(name,'name'),**pair(desc,'description'),'icon_alt':name,'asset_index':i}
      if i in (21,22):
        # The print repeats the thermometer inline; preserve that pictogram with
        # the exact same shared asset rather than dropping it during text extraction.
        icon=f'<img src="{AS["lcd"][i]}" alt="{name}" width="18" height="24">'
        entry['description_html']=entry['description_html'].replace('出现 ，','出现 '+icon+'，')
        entry['description_text']=entry['description_text'].replace('出现 ，','出现'+name+'图标，')
      rows.append(entry)
    b.comp(lcd_icon_component_spec,accessibility_label='显示屏图标说明',rows=rows,icon_refs=AS['lcd'],icon_locale_policy='shared')

    b.chapter('operations','产品使用',[8,9,10,11])
    b.h('电源开机／关机');b.figure('main-power')
    b.serial += 1  # The complete SVG now owns its inset standby note and bottom copy.
    b.h('AC输出开／关');b.figure('ac-power');b.serial += 1
    b.h('DC/USB输出开／关');b.figure('dc-usb-power');b.serial += 1
    b.callout('注意',UL('仅将便携式电源连接到符合GB4943.1第6.3、6.4和6.5条款（或其它等效标准）的设备或配件。','为了实现USB-C端口的最大输出功率，请使用USB-C to USB-C 5A数据线（20V DC/5A，100W）。'),variant='caution')
    b.add(P('本产品可通过电小二12V汽车电池补电线为汽车电池充电。该补电线需单独购买，可前往电小二官网选购。'))
    b.callout('注意',UL('该功能仅适用于12V车型，不适用于24V车型。','产品通过12V DC输出（车充口）为汽车电池补电时，请勿启动汽车，否则可能导致产品损坏。','仅适用于汽车电池应急补电，不适用于汽车电池深度亏电或已损坏的情况。'),variant='caution')
    b.h('节能模式')
    b.add(P('为防止因忘记关闭输出而造成电池电量的额外消耗，产品默认开启节能模式。当AC或DC/USB输出开启时，屏幕将显示节能图标“12H”。在此模式下，当未连接设备，或已连接设备的功率低于设定值（AC输出25W或DC/USB输出2W）时，对应输出将在设定时间后自动关闭。默认设置为12小时。节能模式时长可在Jackery App中设置为1H、2H、8H、12H或24H。若设置为“Never Off”，则节能模式将被关闭。'))
    b.serial += 1  # The original prerequisite strip stays inside the framed SVG.
    b.figure('energy-buttons')
    b.add(P('※ 使用交流25W及直流2W以下低功耗设备时，请关闭节能模式以避免输出中途自动关闭。关闭节能模式后，屏幕将不再显示“12H”图标。此时，输出不会自动关闭。'))
    b.callout('说明','设备重新上电后，节能模式将保持上次断电前的状态。',variant='note')
    b.h('LED灯开／关')
    b.figure('led-light');b.serial += 1  # The complete panel retains its inset note and all three numbered actions.
    b.h('屏幕显示');b.used_figures.append('lcd-button')
    groups=[{**pair(state,'state'),'actions':[{**pair(a,'action'),**pair(v,'description')} for a,v in actions]} for state,actions in [
      ('屏幕短亮',[('打开','短按总电源开关键或有充电输入。'),('关闭','短按总电源开关键。'),('自动关闭','2分钟后显示屏将自动熄灭，进入休眠模式。')]),
      ('屏幕常亮',[('打开','开机状态下，双击总电源开关键。'),('关闭','短按总电源开关键。'),('自动关闭','在常亮模式下，无充放电情况，屏幕将在2小时后自动熄灭。')])]]
    b.comp(lcd_mode_component_spec,accessibility_label='屏幕显示',groups=groups,artwork_ref=b.figures['lcd-button']['local_path'],artwork_locale_policy='exact')
    lcd=b.current['nodes'].pop();b.add(shared_group('hb-source-operation',lcd))
    b.h('输出记忆功能');b.add(P('产品可以记忆输出状态，功能是否触发的条件如下：'))
    b.comp(auto_resume_component_spec,headers=['自动恢复输出','不能自动恢复输出'],conditions=[['重启或关机后开机','充电至 电量 ≥（放电下限 + 10%）','OTA升级完成时'],['通过按键或App手动关闭输出','低功率模式关闭输出','故障保护关闭输出','放电倒计时结束后关闭输出']])
    b.h('组合按键')
    keys=[('总电源开关键','AC输出按键','button/power','button/ac','3s','长按3秒','切换节能模式'),('DC/USB输出按键','AC输出按键','button/dc_usb','button/ac','1s','长按1秒','Wi-Fi&蓝牙开关'),('总电源开关键','DC/USB输出按键','button/power','button/dc_usb','3s','长按3秒','Wi-Fi&蓝牙重置'),('总电源开关键','LED灯按键','button/power','button/led','1s','长按1秒','切换应急闪充模式')]
    def attrs(css):return {'html':{'attributes':{'class':css}}}
    body=[]
    for first,second,k1,k2,duration,op,fn in keys:
      buttons=node('group',[node('inline_group',[node('image',source=AS['buttons'][k1],alt=first),node('strong',[text(first)])],presentation=attrs('hb-key-button')),node('inline_group',[text('＋')],presentation=attrs('hb-key-button-plus')),node('inline_group',[node('image',source=AS['buttons'][k2],alt=second),node('strong',[text(second)])],presentation=attrs('hb-key-button'))],role='container',presentation=attrs('hb-key-button-pair'))
      body.append(node('table_row',[node('table_cell',[buttons],header=False),node('table_cell',[node('paragraph',[text(duration)],presentation={'html':{'attributes':{'class':'hb-key-duration','data-duration-icon':'clock'}}}),P(op)],header=False),node('table_cell',[text(fn)],header=False)]))
    headers=['按键','操作','功能']
    carrier=node('table',[node('table_head',[node('table_row',[node('table_cell',[text(x)],header=True) for x in headers])]),node('table_body',body)],presentation=attrs('hb-key-combination-table'))
    b.comp(key_combinations_component_spec,lambda _: [carrier],headers=headers,rows=[[f'{a} ＋ {c}',f'{du} {op}',fn] for a,c,_,_,du,op,fn in keys])

    b.chapter('ups','不间断电源（UPS）',[12])
    b.add(P('本产品通过AC电源线连接电网，电器可以使用本产品的交流输出端口工作（此时交流电来自电网，而不是电池），当电网突然断电后，本产品可以在10ms内自动切换为本产品电池供电模式。'))
    b.figure('ups')
    b.callout('警告',P('请勿将本产品用于数据服务器、医疗设备等一旦发生故障可能危及生命或造成重大财产损失的用途。'),P('对于以下设备，若在使用过程中发生无法供电的情况，可能会对生命安全或财产造成重大损害：'),UL('医疗设备及其他与生命安全密切相关的设备；','社会基础设施、公共服务等重要设备；','企业关键业务设备等。'),P('佩戴心脏起搏器（心脏起搏器植入者）者请勿使用本产品。'),variant='warning')
    b.callout('注意',UL('本产品不支持0ms切换，请勿接到要求0ms切换供电的设备上，例如数据服务器或工作站，请充分测试确认兼容性后使用。','使用UPS功能连接负载时，请勿超出设备最大输出功率，以防触发过载保护。','因未按说明操作导致设备异常或数据丢失，本公司不承担相关责任。','UPS功能仅支持单台户外电源接入市电时使用。请勿将多台户外电源级联（串联）使用，否则UPS不间断供电功能可能失效，市电断开时无法正常切换供电，导致连接设备停止工作。'),variant='caution')

    b.chapter('charging','充电方式',[12,13,14])
    b.add(P('绿色能源优先模式：本产品倡导优先使用绿色能源，本产品支持太阳能充电与市电充电同时使用。当同时开启市电充电与太阳能充电时，产品会优先太阳能充电且太阳能充电与市电充电同时以电池最大允许功率充电。'))
    b.callout('提示','首次使用前请先将本设备充满电！',variant='tip')
    b.callout('提示',UL('产品充放电环境温度为-10℃～45℃，超出此温度范围会限制产品充放电，甚至无法充放电。','产品的充电功率和电池能量会因温度的变化有所差异。'),variant='tip')
    b.h('市电充电');b.add(P('请使用官方标配的AC电源线。'));b.figure('ac-charge')
    b.callout('注意','请确保AC充电线插头牢固且完全插入产品的AC输入接口，避免因插入不完全引发电流不稳、发热或接触不良等问题，影响设备正常运行。','若使用电源适配器供电，则应购买配套使用获得CCC认证并满足PD协议标准要求的电源适配器。',variant='caution')
    b.h('应急闪充模式')
    b.add(P('储能可以通过AC充电方式实现超速充电，请在电小二App上激活或关闭此功能。应急闪充模式下，显示剩余电量的环形灯闪烁速度加快。'),P('※ 以正常充电速度充电能最大程度保护电池。我们建议仅在必要时使用应急充电，不建议长期使用此功能。'))
    note=b.current['nodes'].pop();copy=b.current['nodes'].pop();title=b.current['nodes'].pop();b.add(shared_group('hb-source-operation',title,copy,note))
    b.h('太阳能充电');b.add(P('本产品有两个DC8020直流输入端口，最大支持400W输入，可搭配电小二SolarSaga系列太阳能板使用。'));b.figure('solar-direct')
    b.add(P('如果单个DC8020直流输入端口需要同时连接两个太阳能板，请参考下图，需要使用太阳能串联转接盒（单独售卖）。'));b.figure('solar-four')
    b.callout('注意','单个DC8020输入端口请勿连接两个以上光伏板。',variant='caution')
    b.callout('注意',P('同时连接到两个DC输入端口的电源，其电压必须保持一致，否则可能导致产品异常或损坏。例如：'),UL('连接太阳能板至两个DC8020输入端口时，请使用相同型号的Jackery太阳能板，并确保连接的数量一致。','给产品充电时，请勿同时使用车载充电与光伏充电，否则可能烧坏车内保险丝或无法充电。'),variant='caution')
    b.add(P('建议使用电小二的太阳能板为本产品充电。请确保所用太阳能板的开路电压（V_{oc}）在1000 Pro 3的直流输入电压范围内（16V-60V）。因使用第三方太阳能板或配件而导致的任何损坏或损失，电小二概不负责。'))
    b.h('车充充电');b.add(P('本产品适用12V车型车充口对本产品进行充电，请确保汽车车充口和车充线的点烟器接触良好，确保点烟器完全插入到位。'));b.figure('car-charge')
    b.callout('注意',UL('请在汽车点火启动后使用车充充电，以免造成汽车电瓶亏电无法启动。','汽车在行驶过程中，路况颠簸，禁止使用车充充电，防止车充接触不良，引起接触点烧坏。若因不按规范操作而造成损失，本公司不予承担相应责任。','车充充电只支持12V车型，不支持24V车型，请勿使用24V车型的车给本产品充电以免造成人身伤害及财产损失。'),variant='caution')

    b.chapter('troubleshooting','故障处理',[15])
    b.add(P('如果出现以下任一故障代码，请按照所列的处理方法进行处理。如故障仍然存在，请联系Jackery客户支持。'))
    measures=['重启产品。']*4+['将产品连接负载，放电直至故障消失。','通过太阳能板或AC墙充为产品充电，直至故障消失。','1. 待电网恢复正常后再通过交流墙插为产品充电。\n2. 检查进风口和出风口是否堵塞；确保产品两侧有20厘米的间隙。\n3. 将产品放置在避免阳光直射、环境温度低于45℃的地方。\n4. 断开产品连接的所有负载，保持产品空闲待机，等待故障消失。检查负载的启动功率是否超出本产品的输出范围。\n5. 重启产品。','1. 移除连接到产品的所有太阳能板。\n2. 检查连接到产品的太阳能板的开路电压（V_{oc}）。产品允许的最大直流输入电压为60V。\n3. 重启产品，保持产品空闲待机，等待故障消失。','请联系经销商或电小二客户支持。','移除连接到产品DC 12V/USB端口的负载，等待故障消失。']
    b.comp(troubleshooting_component_spec,headers=[pair(x,'content') for x in ['故障代码','处理方法']],rows=[{**pair('F'+str(i),'code'),**pair(m,'measures')} for i,m in enumerate(measures)])
    b.chapter('storage','存储',[15])
    b.add(P('请将产品存放在干燥、清洁、通风良好的环境中。存储温度和湿度要求如下：'),UL('1个月：-20°C～45°C（0-60%RH）','3个月：0°C～45°C（0-60%RH）','12个月：0°C～25°C（0-60%RH）'),P('若产品在电量耗尽的情况下长时间（3～6个月）存放，可能会导致无法再次充电。为避免此情况并保持电池健康，建议每隔三个月检查并为产品充电一次，并在6～12个月内至少进行一次完整的充放电循环。'))

    b.chapter('specifications','技术参数',[16])
    specs=[('基本规格',[['产品名称','便携式储能电源'],['型号','JE-1000F'],['电芯类型','磷酸铁锂电芯'],['额定能量','1024Wh'],['重量','约10.6kg'],['尺寸','约314×201×233.5mm'],['循环寿命','6000次循环，≥70%SOH']]),
      ('输入',[['IN1（AC输入）','220V-240V~50Hz，最大10A'],['AC旁路输入①','220V-240V~50Hz，最大1500W'],['IN2/IN3（DC8020输入）','光伏：16V-60V⎓最大12A，双路最大21A/最大400W\n车充：11V-16V⎓最大8A，双路最大8A']]),
      ('输出',[['OUT1（车充输出端口）','12V⎓最大10A'],['OUT2（USB-C1输出端口）','最大30W，5V⎓3A，9V⎓3A，12V⎓2.5A，15V⎓2A，20V⎓1.5A'],['OUT3（USB-C2输出端口）','最大100W，5V⎓3A，9V⎓3A，12V⎓3A，15V⎓3A，20V⎓5A'],['OUT4（USB-A输出端口）','最大18W，5-6V⎓3A，6-9V⎓2A，9-12V⎓1.5A'],['OUT5/OUT6（AC输出）','220V~50Hz，6.8A，额定1500W'],['AC总输出','额定1500W，瞬时最大3000W'],['AC旁路输出①','220V-240V~50Hz，最大1500W']]),
      ('工作环境温度',[['充电温度','-10°C～45°C'],['放电温度','-10°C～45°C'],['存储环境温度','1个月：-20°C～45°C\n3个月：0°C～45°C\n1年：0°C～25°C']])]
    for title,rows in specs:b.comp(spec_table_component_spec,spec_carrier,section_title=title,rows=rows)
    b.add(P('如需查看本产品的有害物质含有信息，请访问：https://www.dx2.cn/hazardoussubstance。'),P('①：产品支持边充边放。'),P('※ USB Type-C和USB-C是USB Implementers Forum的注册商标。'),P('※ 常温条件下，车充输出端口（OUT1）、USB-C输出端口（OUT2、OUT3）、USB-A输出端口（OUT4）及AC输出端口（OUT5、OUT6）支持同时为设备供电，各端口不会因同时使用而降低输出功率。使用时，各端口的负载不得超过“技术参数”中标示的输出限值。其中，两个AC输出端口（OUT5、OUT6）的合计额定输出功率为1500W。'))

    b.chapter('app_setup','APP操作说明书',[17,1])
    b.h('1. 下载并登录App')
    download='在App Store或者国内各大应用市场搜索“电小二”App安装并注册登录。或扫描右边二维码下载电小二App。'
    b.used_figures.append('app-download')
    b.comp(app_qr_download_component_spec,lambda _: [P(download),node('image',source=b.figures['app-download']['local_path'],alt='电小二App下载二维码')],label='下载电小二App',paragraph=cell_pair(download),image_ref=b.figures['app-download']['local_path'])
    b.h('2. 添加设备')
    add_paras(b,'2.1 在App内点击 ＋ 添加设备。','2.2 短按设备上的“总电源开关键”开机，设备上的Wi-Fi和蓝牙图标闪烁后表示设备已进入配网模式，在App内点击“图标已快闪”按钮并允许应用连接附近的设备和打开蓝牙权限。')
    app_phones_with_captions(b)
    b.callout('备注','打开设备，如果两小时内未连接到APP，设备会自动关闭Wi-Fi和蓝牙。',variant='note');b.figure('app-controls')
    b.add(P('2.3 点击搜索到的设备图标后App通过蓝牙自动连接设备。'))
    b.callout('备注',P('如果在绑定过程中提示“设备已被绑定”，可通过以下两种方式连接：'),UL('设备拥有者通过App将此设备分享给其他用户；','同时长按“总电源开关按键”和“DC/USB输出按键”重置设备Wi-Fi后可重新绑定设备。'),variant='note')
    b.add(P('2.4 设备连接成功后输入设备将要连接的Wi-Fi名称和密码，设备自动连接到Wi-Fi网络。'))
    b.callout('备注','请选择2.4GHz频段的Wi-Fi网络，设备不支持5GHz频段的Wi-Fi网络。',variant='note')
    b.add(P('2.5 设备添加成功后进入设备主页面，设备上的Wi-Fi图标会常亮。'));b.figure('app-results');b.add(P('图片仅供参考'))
    b.callout('注意','App通过蓝牙与储能设备连接，每次仅支持一台设备。连接后返回设备列表时，蓝牙连接将自动断开。再次点击储能设备图标时，App会自动重新连接。',variant='caution')
    b.h('3. 解绑设备');b.add(P('点击设备主界面右上角的设置按钮进入设置页面，点击页面最下方的解除绑定按钮解绑设备。'))
    b.h('4. 其他说明')
    b.h('4.1 打开Wi-Fi&蓝牙',level=4)
    add_paras(b,'开机后自动打开Wi-Fi&蓝牙，屏幕上的Wi-Fi&蓝牙图标点亮表示Wi-Fi&蓝牙已被打开。','同时长按“AC输出按键”和“DC/USB输出按键”1秒手动打开Wi-Fi和蓝牙。')
    b.h('4.2 关闭Wi-Fi&蓝牙',level=4)
    add_paras(b,'两小时内未连接WiFi或蓝牙，设备上的Wi-Fi&蓝牙会自动关闭。','同时长按“AC输出按键”和“DC/USB输出按键”1秒手动关闭Wi-Fi和蓝牙。')
    b.h('4.3 重置Wi-Fi&蓝牙',level=4)
    b.add(P('同时长按“总电源开关按键”和“DC/USB输出按键”将重置Wi-Fi和蓝牙，同时清除App中的自定义设置。'))
    b.chapter('contact','制造商与服务信息',[18])
    b.used_figures.append('service-qr')
    service_code=node('figure',[
      node('image',source=b.figures['service-qr']['local_path'],alt='电小二官方品牌公众号二维码'),
      node('caption',[node('small_text',[text('关注官方品牌公众号，'),node('line_break'),text('获取更多资讯服务。')])])
    ],anchor='native-contact-code')
    manufacturer=P('制造商：深圳市华宝新能源股份有限公司\n地址：深圳市龙华区大浪街道同胜社区华繁路东侧嘉安达科技工业园厂房七栋第二、三、四层')
    factory=P('生产厂：深圳市华宝新能源股份有限公司\n地址：深圳市龙华区大浪街道同胜社区华繁路东侧嘉安达科技工业园厂房七栋第二、三、四、五层，四栋，二栋第一、二、三层')
    b.add(node('group',[service_code,node('group',[manufacturer,factory],role='container',anchor='native-contact-details')],role='container',anchor='native-contact-layout'))
    issues=b.finish(extra={'transcription':'native-pdf-source-bound-cn','approved_errata':[{'printed_page':15,'before':'长按设备上的','after':'短按设备上的','operator_quote':'第15页写“短按”。'},{'printed_page':15,'before':'“USB输出按键”','after':'“DC/USB输出按键”','operator_quote':'第15页写“DC/USB输出按键”'}]})
    if issues:raise ValueError(issues)
    return {'chapters':len(b.chapters),'figure_slots':len(b.figures),'used_figures':len(b.used_figures)}
if __name__=='__main__':print(json.dumps(make(),ensure_ascii=False))
