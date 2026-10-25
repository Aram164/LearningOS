from pathlib import Path
import yaml,copy,json,hashlib,shutil
core=Path('/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository')
raw=core/'workbench/campaigns-2026-10/raw/system/C2'
drafts=core.parent/'workbench/campaign-integration-2026-10-25/drafts';drafts.mkdir(parents=True,exist_ok=True)
auditdir=core/'work/active/workspace-campaign-verification-2026-10-25/outputs';auditdir.mkdir(parents=True,exist_ok=True)
for folder in ['module-hu-m2-statistik-analysis','module-hu-aml','_job-modules-evidence']:
 for p in (raw/folder/'packages').rglob('*.md'):
  if p.name.startswith(('audit','coverage-audit')):shutil.copyfile(p,auditdir/p.name)
base=yaml.safe_load((core/'curriculum/modules/module-hu-m2-statistik-analysis/source-map.yaml').read_text())
combined={};patches=[]
def diff(a,b,path=()):
 if type(a)!=type(b):return [(path,a,b)]
 if isinstance(a,dict):
  assert a.keys()==b.keys(),path
  return [d for k in a for d in diff(a[k],b[k],path+(k,))]
 if isinstance(a,list):
  assert len(a)==len(b),path
  return [d for i,(aa,bb) in enumerate(zip(a,b)) for d in diff(aa,bb,path+(i,))]
 return [] if a==b else [(path,a,b)]
for n in [1,2,3,4]:
 p=next((raw/'module-hu-m2-statistik-analysis/packages').glob(f'package-p{n}-*.yaml'))
 d=yaml.safe_load(p.read_text())
 if n==1:combined=copy.deepcopy(d)
 elif 'units' in d:combined['units']+=d['units']
 if 'source_map' in d:
  for path,before,after in diff(base,d['source_map']):
   assert path[-1]=='locator',path
   assert not any(x['path']==list(path) for x in patches),path
   patches.append({'path':list(path),'before':before,'after':after})
 if d.get('claim_evidence'):combined.setdefault('claim_evidence',[]).extend(d['claim_evidence'])
assert len(patches)==4,patches
combined['source_map']=copy.deepcopy(base)
for patch in patches:
 node=combined['source_map']
 for k in patch['path'][:-1]:node=node[k]
 node[patch['path'][-1]]=patch['after']
contract_path='work/active/workspace-campaign-verification-2026-10-25/outputs/m2-combined-audit.md'
combined['plan_contract']['coverage_audit']=contract_path
(core/contract_path).write_text('''# Reviewed campaign corrections — combined Math2 package, 2026-10-25

This combines the four independently preflighted C2 packages. The current task
explicitly requests verification and integration of the campaign fixes.

## Local

Fresh preflights of all four source packages pass against Core fb73b0f9 and
current learner data in an isolated copy. Every learner-state change list is
empty. P1 binds the 472 existing chapter 3–7 resource rows without moving or
rewriting them. P4 binds nine existing rehearsal rows to their unique declared
source route, preserving the row wording and placement. Its historical judgment
and coarse-covers limitation remain recorded in audit-p4-rehearsal-2026-10-25.md.

## Linked

The source-map combination was compared structurally with today's owning file.
There are exactly four leaf changes, all locator fields: one two-deck filename
correction, plus three IngMath2 PDF/printed-page corrections. No route identity,
source, covers, angle, selection, stage or ordering changes. The four original
claim-evidence bundles are retained. Their quotes were revalidated by the
current preflight. No route or source is added or removed.

## Completeness

P1/P4 units are disjoint. P2/P3 source maps were merged by their disjoint leaf
changes, so neither can overwrite the other's correction. All original material
menus, sources, placements and learner state remain. Original coverage audits
sit beside this file; the campaign packages, probes and fresh preflights are
saved under workbench/campaigns-2026-10/. The eight never-placed Math2 routes,
additional chapter-3 page issue, and other deferred critique debt are recorded
in the original package report and are outside this bounded integration.
''')
(drafts/'m2-combined.yaml').write_text(yaml.safe_dump(combined,allow_unicode=True,sort_keys=False,width=100))
for name,source in [('aml-combined',raw/'module-hu-aml/packages/package-f1f2-combined.yaml'),('polars',raw/'_job-modules-evidence/packages/package-polars-f1-notebook-attribution.yaml'),('git',raw/'_job-modules-evidence/packages/package-git-f1-full-study-map.yaml')]:
 d=yaml.safe_load(source.read_text())
 if 'plan_contract' in d:
  d['plan_contract']['coverage_audit']='work/active/workspace-campaign-verification-2026-10-25/outputs/'+Path(d['plan_contract']['coverage_audit']).name
 (drafts/(name+'.yaml')).write_text(yaml.safe_dump(d,allow_unicode=True,sort_keys=False,width=100))
(core/'workbench/campaigns-2026-10/evidence/m2-source-map-delta.json').write_text(json.dumps(patches,ensure_ascii=False,indent=2)+'\n')
print('Four live drafts prepared, Math2 route changes:',len(patches))
