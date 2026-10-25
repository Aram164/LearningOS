from pathlib import Path
import subprocess,os,json,tarfile,hashlib,shutil
core=Path('/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository');raw=core/'workbench/campaigns-2026-10/raw/knowledge';logs=core/'workbench/campaigns-2026-10/evidence'
tmp=Path('/private/tmp/los-campaign-verification-20261025/plan-pair');clone=tmp/'repository';ui=tmp/'obsidian-ui'
if not ui.exists():subprocess.run(['git','clone','--quiet','--no-hardlinks',str(core.parent/'obsidian-ui'),str(ui)],check=True)
if not (ui/'node_modules').exists():(ui/'node_modules').symlink_to(core.parent/'obsidian-ui/node_modules',target_is_directory=True)
# Recover the six missing K3 probe sources from the checkout-preservation tar.
tarpath=Path('/Users/aramaljanadi/LearningOS-archive-2026-10-25/home/los-glm-K3-2026-10/obsidian-ui/.checkout/untracked.tar')
index=core/'workbench/campaigns-2026-10/archive-index.json';idx=json.loads(index.read_text())
with tarfile.open(tarpath) as tar:
 for member in tar.getmembers():
  if member.isfile() and member.name.startswith('tests/k3-') and member.name.endswith('.js'):
   data=tar.extractfile(member).read();dest=raw/'K3/probes'/Path(member.name).name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(data)
   (ui/member.name).write_bytes(data)
   idx['files'].append({'path':str(dest.relative_to(index.parent)),'source':str(tarpath)+'!'+member.name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
index.write_text(json.dumps(idx,indent=2)+'\n')
files=[]
for batch in ['K1','K4']:
 for p in sorted((raw/batch/'probes').glob('test_*.py')):
  shutil.copyfile(p,clone/'tests'/p.name);files.append(p.name)
mapfile=clone/'tests/group_map.py'
with mapfile.open('a') as f:
 f.write('\n# Temporary campaign verification registration.\nGROUPS["gateway"].extend('+repr(files)+')\nFILE_TO_GROUP.update({name: "gateway" for name in '+repr(files)+'})\n')
manifest=clone/'.github/shard-manifest.json';m=json.loads(manifest.read_text());print('manifest layout',list(m),flush=True)
# Targeted run only; no production test registration is changed.
env={**os.environ,'PYTHONPATH':str(clone/'tools'),'PYTHONDONTWRITEBYTECODE':'1'}
results=[]
for name in files:
 with (logs/(name+'.log')).open('w') as f:r=subprocess.run([str(core/'.venv/bin/python'),'-m','pytest','-q','-p','no:cacheprovider','tests/'+name],cwd=clone,env=env,stdout=f,stderr=subprocess.STDOUT)
 results.append({'file':name,'exit_code':r.returncode});print(name,r.returncode,flush=True)
for p in sorted((ui/'tests').glob('k3-*.js')):
 with (logs/(p.name+'.log')).open('w') as f:r=subprocess.run(['node',str(p)],cwd=ui,env=env,stdout=f,stderr=subprocess.STDOUT)
 results.append({'file':p.name,'exit_code':r.returncode});print(p.name,r.returncode,flush=True)
(logs/'knowledge-verification-results.json').write_text(json.dumps(results,indent=2)+'\n')
assert all(r['exit_code']==0 for r in results)
