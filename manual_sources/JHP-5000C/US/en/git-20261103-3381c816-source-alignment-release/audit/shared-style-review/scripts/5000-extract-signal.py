from pathlib import Path
p=Path('/private/tmp/manual-web-audit-20261102/5000-extract-structural.py');src=p.read_text();first=src.split('# Source notes/structural frames only:')[0];later=src[src.index('for idx,nodes in enumerate(mapped):'):src.index('full_figures=')];tail=src[src.index('allids='):];tail=tail.replace("proof=[]","proof=json.loads((P/'source/structural-art-provenance.json').read_text())")
code=first+"\norigins[5]=(origins[4][0]-377.42570000000023,origins[4][1])\nrecords=[('source-signal-white',5,[38.9,121.7,49.01,129.22],[103935])]\n"+later+tail
exec(compile(code,str(p),'exec'))
