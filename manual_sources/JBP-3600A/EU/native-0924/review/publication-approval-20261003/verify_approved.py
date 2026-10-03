import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys
sys.path.insert(0,str(Path.cwd()))
from tools.frozen_ai_web import replay_package
from tools.manual_ir.hashing import file_sha256
from tools.web.component_admission import require_fresh_component_admission

base=Path('manual_sources/JBP-3600A/EU/native-0924')
source=Path('manual_sources/JBP-3600A/EU/git-20261003-44b6ce61-reviewed')
scratch=Path('.tmp/jbp3600a-publish-20261003')
results=[]
for entry in json.loads((source/'approval-parity.json').read_text()):
    lang, revision=entry['language'],entry['revision']
    package=source/'web'/lang
    filename=f'manual_jbp3600a_eu{"" if lang=="en" else "_"+lang}.md'
    html=scratch/'approved-html'/lang
    cold=scratch/'cold'/lang
    shutil.copytree(package,cold)
    if lang!='en': replay_package(cold)
    assert (cold/filename).read_bytes()==(package/filename).read_bytes()
    for label,src,dst in [('strict',package,html),('cold',cold,scratch/'cold-html'/lang)]:
        with (scratch/f'{lang}-{label}.log').open('w') as log:
            subprocess.run([sys.executable,'-m','sphinx','-W','--keep-going','-b','html',str(src),str(dst)],check=True,stdout=log,stderr=subprocess.STDOUT)
    actual=(html/filename).with_suffix('.html')
    accepted=gzip.decompress((base/'review/transparent-final-independent'/f'{revision}.html.gz').read_bytes())
    assert actual.read_bytes()==accepted, (lang,'accepted HTML mismatch')
    assert actual.read_bytes()==(scratch/'cold-html'/lang/actual.name).read_bytes()
    report=require_fresh_component_admission(package,model='JBP-3600A',region='EU',language=lang)
    # Gate remains fail-closed on the original candidate, even after enrollment.
    try: require_fresh_component_admission(base/'web'/revision,model='JBP-3600A',region='EU',language=lang)
    except RuntimeError as exc: assert str(exc)=='manual IR has pending source review'
    else: raise AssertionError('Old candidate unexpectedly admitted')
    results.append({**entry,'strict_sphinx':'pass','cold_replay':'pass','accepted_html_byte_identical':True,'html_sha256':file_sha256(actual),'original_candidate_rejected':True,'admission_issues':report['issues']})
    print(lang,'strict + cold + exact accepted HTML + fresh admission passed',flush=True)
producer=base/'review/transparent-symbol-r1'
for name,digest in json.loads((producer/'evidence-manifest.json').read_text())['files'].items():assert file_sha256(producer/name)==digest
for name,digest in json.loads((producer/'historical-seals.json').read_text()).items():assert file_sha256(Path(name))==digest
ind=base/'review/transparent-final-independent'
for name,digest in json.loads((ind/'receipt.json').read_text())['files'].items():assert file_sha256(ind/name)==digest
(scratch/'approved-verification.json').write_text(json.dumps({'languages':results,'historical_seals':'unchanged'},ensure_ascii=False,indent=2)+'\n')
