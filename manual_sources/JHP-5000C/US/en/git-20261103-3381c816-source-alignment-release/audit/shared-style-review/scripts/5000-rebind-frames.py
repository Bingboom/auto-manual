from pathlib import Path
s=Path('/private/tmp/manual-web-audit-20261102/5000-apply-source-art.py').read_text();exec(s[:s.index('os.chdir(P)')]);os.chdir(P)
frames={'power':'source-power-frame','ac-output':'source-ac-frame','usb-output':'source-usb-frame','dc-output':'source-dc-frame','ac-charge':'source-ac-charge-frame','sts-charge':'source-sts-charge-frame','ess':'source-ess-frame','package-host':'source-package-host-frame','package-battery':'source-package-battery-frame','package-sts':'source-package-sts-frame'}
newfull={'ups':'current-ups-art','battery-packs':'current-battery-art','sts-connect':'current-sts-art'}
def walk(n):
 if not isinstance(n,dict):return
 if n.get('kind')=='image' and n.get('source')=='assets/contact-qr.svg':n['source']='assets/source-contact-qr.svg'
 if n.get('kind')=='component' and n['component_spec']['component_id']=='HB-SPECIAL-REFERENCE-FIGURE':
  sp=n['component_spec'];rid=next(x['content'] for x in sp['slots'] if x['role']=='reference_id')
  if rid in frames:
   asset=composite('assets/'+rid+'.svg','assets/'+frames[rid]+'.svg','assets/'+rid+'-source-framed.svg')
   if rid=='package-battery':sp['metadata']['base_art_layout']['labels'][1].update(rect=[87,38,12,24],color='#ffffff');sp['metadata']['base_art_layout']['labels'][1].pop('fill',None)
   if rid=='package-sts':sp['metadata']['base_art_layout']['labels'][42].update(rect=[87,73.5,12,15],color='#ffffff');sp['metadata']['base_art_layout']['labels'][42].pop('fill',None)
   bind(n,asset,remove_fill=rid=='power')
  elif rid in newfull:bind(n,'assets/'+newfull[rid]+'.svg',remove_fill=True)
  return
 for x in n.get('children',[]):walk(x)
for c in d['chapters']:
 for n in c['nodes']:walk(n)
(P/'source/en/content.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');mf=P/'source_manifest.json';m=json.loads(mf.read_text());paths={x['path'] for x in m['inputs']}
for path in [*(str(x.relative_to(P)) for x in (P/'assets').glob('source-*.svg')),*(str(x.relative_to(P)) for x in (P/'assets').glob('current-*.svg')),*newassets,'source/structural-art-provenance.json']:
 if path not in paths:b=(P/path).read_bytes();m['inputs'].append({'path':path,'size':len(b),'sha256':hashlib.sha256(b).hexdigest()});paths.add(path)
mf.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print('rebound',len(newassets))
