from pathlib import Path
import xml.etree.ElementTree as ET,re,hashlib,json
p=Path('/Users/hello-tech-team/.codex/worktrees/manual-warning-alignment/auto-manual-codex/manual_sources/JHP-5000C/US/en/git-20261103-3381c816-source-alignment-release');S='{http://www.w3.org/2000/svg}';proof=json.loads((p/'source/structural-art-provenance.json').read_text())
for r in proof:
 f=p/'assets'/r['asset'];root=ET.parse(f).getroot();defs=[x for x in root.iter(S+'defs')];lookup={n.get('id'):n for d in defs for n in d if n.get('id')};keep=set()
 def refs(n):
  for v in n.attrib.values():
   keep.update(re.findall(r'url\(#([^)]*)\)',v))
   if v.startswith('#'):keep.add(v[1:])
  for c in n:
   if c.tag!=S+'defs':refs(c)
 refs(root);last=set()
 while last!=keep:
  last=set(keep)
  for id in last:
   if id in lookup:refs(lookup[id])
 for d in defs:
  for n in list(d):
   if n.get('id') not in keep:d.remove(n)
 ET.register_namespace('','http://www.w3.org/2000/svg');f.write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True));r['sha256']=hashlib.sha256(f.read_bytes()).hexdigest();print(f.name,f.stat().st_size)
(p/'source/structural-art-provenance.json').write_text(json.dumps(proof,indent=2)+'\n')
