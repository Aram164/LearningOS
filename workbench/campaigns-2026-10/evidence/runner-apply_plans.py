from pathlib import Path
import subprocess,json,hashlib,os,sys,yaml
core=Path('/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository')
drafts=core.parent/'workbench/campaign-integration-2026-10-25/drafts'
logs=core/'workbench/campaigns-2026-10/evidence/live-plans';logs.mkdir(exist_ok=True)
py=str(core/'.venv/bin/python')
# Preserve every map/stage's recorded learner state independently of preflight.
state_fields={'status','current_stage','working_note','attachments','source_feedback','runtime_review','completed','completed_at','skipped','result','notes'}
def learner_state():
 out={}
 for p in (core/'curriculum/modules').glob('*/units/*/study-map.yaml'):
  d=yaml.safe_load(p.read_text());out[str(p.relative_to(core))]={'map':{k:v for k,v in d.items() if k in state_fields},'stages':{s['id']:{k:v for k,v in s.items() if k in state_fields} for s in d.get('stages',[])}}
 return out
before=learner_state();(logs/'learner-state-before.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n')
for name,target in [('m2-combined','module-hu-m2-statistik-analysis'),('aml-combined','module-hu-aml'),('polars','module-job-polars'),('git','unit-job-git-fluency')]:
 pkg=drafts/(name+'.yaml');sha='sha256:'+hashlib.sha256(pkg.read_bytes()).hexdigest()
 verb='unit-map-import' if name=='git' else 'module-plan-import'
 command=[py,'tools/los.py',verb,target,'--file',str(pkg),'--file-sha256',sha,'--check','--json']
 if name=='git':command+=['--replace']
 p=subprocess.run(command,cwd=core,capture_output=True,text=True)
 report=logs/(name+'-check.json');report.write_text(p.stdout);(logs/(name+'-check.err')).write_text(p.stderr)
 if p.returncode: print(name,'CHECK FAILED',p.stderr[-800:],flush=True);sys.exit(1)
 r=json.loads(p.stdout);assert r['ok'] and r['canonical_files_written']==0
 if name!='git':
  assert not r['semantic_ack_required'],r['semantic_ack_required']
  for u in r['units'].values():
   for key in ['learner_state_changes','resource_learner_changes','map_state_changes','destructive_learner_changes']:assert not u[key],(name,key,u[key])
  command=[py,'tools/los.py',verb,target,'--file',str(pkg),'--apply-reviewed-sha256',sha,'--review-report',str(report),'--json']
 else:
  d=r['diff']
  for k in ['stages_added','stages_retired','learner_state_changes','map_changes']:
   if k in d:assert not d[k],(k,d[k])
  assert not d['relative_order_changed']
  assert len(d['content_changes'])==1,d['content_changes']
  payload={'unit_id':target,'file':str(pkg),'file_sha256':sha,'replace':True}
  payload_path=logs/(name+'-payload.json');payload_path.write_text(json.dumps(payload)+'\n')
  command=[py,'tools/seal_envelope.py','--capability','unit.map.import','--payload','@'+str(payload_path),'--key','campaign-20261025-git-locator','--session-id','campaign-verification-20261025','--channel','codex','--guards','auto','--out','/private/tmp/los-campaign-verification-20261025/git-envelope.json','--submit']
 p=subprocess.run(command,cwd=core,capture_output=True,text=True)
 (logs/(name+'-apply.json')).write_text(p.stdout);(logs/(name+'-apply.err')).write_text(p.stderr)
 if p.returncode: print(name,'APPLY FAILED',p.stderr[-1200:],flush=True);sys.exit(1)
 r=json.loads(p.stdout);assert r['ok'],r
 print(name,'APPLIED',r.get('receipt_path',r.get('result',{}).get('receipt_path')),flush=True)
 after=learner_state();assert after==before,'recorded learner state changed'
 (logs/'learner-state-after.json').write_text(json.dumps(after,ensure_ascii=False,indent=2)+'\n')
 # Preserve the exact successfully applied package inside the Git archive.
 dest=logs/(name+'-applied.yaml');dest.write_bytes(pkg.read_bytes())
print('ALL FOUR APPLIED; recorded learner state unchanged across all maps',flush=True)
