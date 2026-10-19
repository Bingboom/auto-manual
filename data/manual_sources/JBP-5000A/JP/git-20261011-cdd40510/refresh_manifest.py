from pathlib import Path
import hashlib,json
S=Path(__file__).resolve().parent
R=next(p for p in S.parents if (p/'build.py').is_file())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d={'schema_version':'auto-manual-frozen-web-source/v1','target':{'model':'JBP-5000A','region':'JP','technical_version':S.name,'languages':['ja']},'original_source':{'filename':next(S.glob('*.pdf')).name,'sha256':sha(next(S.glob('*.pdf'))),'page_count':10,'printed_version':'unknown'},'physical_page_map':{'ja':[2,10],'archived_print_cover':1},'web_roots':{'ja':'web/ja'},'publication_eligible':False,'review_status':'candidate','live_bitable_dependency':False,'phase2_enrolled':False,'build_py_check_scope':'Shared JP family regression only; native JBP-5000A body validated against source/ja/coverage.json and pinned source PDF.','normalizations':['Printed cover archived outside Web body; native physical pages 2–10 retained.','Japanese print wraps joined without added spaces; source wording preserved.','Native independent caption boxes removed from art and reconstructed in CSS.','Shared transparent glyphs copied byte-identically; only concrete JP differences extracted.']}
deps={R/'tools/markdown_bundle.py',R/'tools/build_paths.py',R/'docs/renderers/web/assets/shared/symbols/manifest.json',R/'docs/renderers/web/assets/shared/buttons/manifest.json'}
for rel in ['tools/manual_ir','tools/component_specs','tools/web','tools/asset_pipeline','tools/utils','docs/renderers/contracts']:
 deps.update(p for p in (R/rel).rglob('*') if p.is_file() and p.suffix in ['.py','.css','.json','.yaml','.yml'])
for a in json.loads((S/'source/asset_decisions.json').read_text()):
 if a.get('candidate'):deps.add(R/a['candidate'])
d['repo_inputs']=[{'path':p.relative_to(R).as_posix(),'sha256':sha(p),'size':p.stat().st_size} for p in sorted(deps)]
d['inputs']=[{'path':p.relative_to(S).as_posix(),'sha256':sha(p),'size':p.stat().st_size} for p in sorted(S.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='source_manifest.json']
(S/'source_manifest.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');print(len(d['inputs']),len(d['repo_inputs']))
