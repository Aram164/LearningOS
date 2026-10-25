import subprocess,os,json,hashlib,shutil
from pathlib import Path
base=Path('/Users/aramaljanadi/Desktop/semestercontext/LearningOS')
real=base/'repository'; raw=real/'workbench/campaigns-2026-10/raw/system/C2'
pair=Path('/private/tmp/los-campaign-verification-20261025/plan-pair');pair.mkdir(exist_ok=True)
clone=pair/'repository'
if not clone.exists(): subprocess.run(['git','clone','--quiet','--no-hardlinks',str(real),str(clone)],check=True)
if not (pair/'materials').exists(): (pair/'materials').symlink_to(base/'materials',target_is_directory=True)
checks=[
 ('m2-p1','module-hu-m2-statistik-analysis',raw/'module-hu-m2-statistik-analysis/packages/package-p1-ch03-07-binding.yaml','module-plan-import'),
 ('m2-p2','module-hu-m2-statistik-analysis',raw/'module-hu-m2-statistik-analysis/packages/package-p2-aml-l09-locator.yaml','module-plan-import'),
 ('m2-p3','module-hu-m2-statistik-analysis',raw/'module-hu-m2-statistik-analysis/packages/package-p3-ingmath2-pages.yaml','module-plan-import'),
 ('m2-p4','module-hu-m2-statistik-analysis',raw/'module-hu-m2-statistik-analysis/packages/package-p4-rehearsal-binding.yaml','module-plan-import'),
 ('aml-combined','module-hu-aml',raw/'module-hu-aml/packages/package-f1f2-combined.yaml','module-plan-import'),
 ('polars','module-job-polars',raw/'_job-modules-evidence/packages/package-polars-f1-notebook-attribution.yaml','module-plan-import'),
 ('git','unit-job-git-fluency',raw/'_job-modules-evidence/packages/package-git-f1-full-study-map.yaml','unit-map-import')]
import sys
sys.path.insert(0,str(real/'.venv/lib/python3.14/site-packages'))
import yaml
out=real/'workbench/campaigns-2026-10/evidence/plans';out.mkdir(exist_ok=True)
for name,target,pkg,verb in checks:
 data=yaml.safe_load(pkg.read_text());audit=data.get('plan_contract',{}).get('coverage_audit')
 if audit:
  dest=clone/audit;dest.parent.mkdir(parents=True,exist_ok=True)
  candidates=list(raw.rglob(Path(audit).name));assert len(candidates)==1,(audit,candidates)
  shutil.copyfile(candidates[0],dest)
 cmd=[str(real/'.venv/bin/python'),str(clone/'tools/los.py'),verb,target,'--file',str(pkg),'--file-sha256','sha256:'+hashlib.sha256(pkg.read_bytes()).hexdigest(),'--check','--json']
 if verb=='unit-map-import':cmd+=['--replace']
 p=subprocess.run(cmd,cwd=clone,capture_output=True,text=True,env={**os.environ,'PYTHONPATH':str(clone/'tools'),'PYTHONDONTWRITEBYTECODE':'1'})
 (out/(name+'.json')).write_text(p.stdout);(out/(name+'.err')).write_text(p.stderr)
 print(name,p.returncode,p.stderr[:300],flush=True)
