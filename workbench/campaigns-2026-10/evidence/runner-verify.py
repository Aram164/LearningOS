import os,subprocess,json,time
from pathlib import Path
root=Path('/Users/aramaljanadi/Desktop/semestercontext/LearningOS')
logs=root/'repository/workbench/campaigns-2026-10/evidence'
rows=[]
env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
def run(name,cmd,cwd,expected=0):
 start=time.monotonic()
 with (logs/(name+'.log')).open('w') as f:
  result=subprocess.run(cmd,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT)
 row={'name':name,'command':cmd,'cwd':str(cwd),'exit_code':result.returncode,'expected_exit':expected,'seconds':round(time.monotonic()-start,2)}
 rows.append(row);(logs/'verification-results.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(name, result.returncode, 'OK' if result.returncode==expected else 'UNEXPECTED', flush=True)
for batch,glob in [('V3','test_v3_*.py'),('V4','test_v4_ai_gateway.py')]:
 clone=Path('/Users/aramaljanadi')/f'los-glm-{batch}-2026-10/repository'
 for p in sorted((clone/'tests').glob(glob)):
  run(p.stem,[str(clone/'.venv/bin/python'),'-m','pytest','-p','no:cacheprovider',str(p),'-q'],clone)
core=root/'repository'
run('landed-system-regressions',[str(core/'.venv/bin/python'),'-m','pytest','-q',*[str(p) for p in sorted((core/'tests').glob('test_c1*.py'))]],core)
run('documentation-and-contracts',[str(core/'.venv/bin/python'),'-m','pytest','-q','tests/test_system_map.py','tests/test_normative_corpus.py','tests/test_manifest_contract.py','tests/test_schema_contract.py','tests/test_arch_doc_commands.py'],core)
run('ui-complete-check',['npm','run','check'],root/'obsidian-ui')
# Run current UI, retaining unmodified original probe copies in raw/.
probe_dir=Path('/private/tmp/los-campaign-verification-20261025/v2');probe_dir.mkdir(exist_ok=True)
for p in (logs.parent/'raw/verification/V2/probes').glob('*.js'):
 text=p.read_text().replace('/Users/aramaljanadi/los-glm-V2-2026-10/obsidian-ui',str(root/'obsidian-ui'))
 (probe_dir/p.name).write_text(text)
for p in sorted(probe_dir.glob('probe*.js')):
 run(p.stem,['node',str(p)],root/'obsidian-ui')
run('stage-plugin-reproduction',['npm','run','stage-plugin'],root/'obsidian-ui',1)
print('FINISHED',flush=True)
