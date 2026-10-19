"""Create an isolated interpreter prefix without changing shared dependencies."""
from __future__ import annotations
import json
import os
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
CORE=HERE/'candidate/repository'
ORIGINAL=HERE.parents[2]/'repository'
original_python=ORIGINAL/'.venv/bin/python'
info=json.loads(subprocess.check_output([str(original_python),'-c',
    'import json,sys,sysconfig; print(json.dumps({"prefix":sys.prefix,"purelib":sysconfig.get_path("purelib"),"version":sys.version}))'],text=True))
before=HERE/'runtime-before-private-prefix'
if before.exists():raise RuntimeError('preserve the earlier runtime evidence; do not overwrite')
source=CORE/'.venv'
metadata={'original':info,'candidate_before':{'pyvenv_cfg':(source/'pyvenv.cfg').read_text(),
    'links':{p.name:os.readlink(p) for p in source.iterdir() if p.is_symlink()}}}
source.rename(before)
subprocess.run([str(original_python),'-m','venv','--without-pip',str(source)],check=True)
private_lib=Path(subprocess.check_output([str(source/'bin/python'),'-c',
    'import sysconfig; print(sysconfig.get_path("purelib"))'],text=True).strip())
# Plain paths reuse installed dependencies, but do not execute the original
# editable-install .pth hooks that select the wrong source checkout.
(private_lib/'learningos-candidate.pth').write_text(str(CORE/'tools')+'\n'+info['purelib']+'\n')
for name in ['scrut','ruff']:
    path=ORIGINAL/'.venv/bin'/name
    if path.exists():(source/'bin'/name).symlink_to(path)
for name in ['lint-imports','pytest','mypy']:
    path=ORIGINAL/'.venv/bin'/name
    if path.is_file():
        raw=path.read_text();_,separator,body=raw.partition('\n')
        if not separator:raise RuntimeError('unrecognized runtime entrypoint '+name)
        target=source/'bin'/name
        target.write_text('#!'+str(source/'bin/python')+'\n'+body)
        target.chmod(0o755)
metadata['candidate_after']=json.loads(subprocess.check_output([str(source/'bin/python'),'-c',
 'import json,sys,learning_os,importlinter,yaml,pypdf; print(json.dumps({"prefix":sys.prefix,"executable":sys.executable,"source":learning_os.__file__,"version":sys.version}))'],text=True))
assert Path(metadata['candidate_after']['prefix']).resolve()==source.resolve()
assert Path(metadata['candidate_after']['source']).resolve()==(CORE/'tools/learning_os/__init__.py').resolve()
(HERE/'runtime-private-prefix.json').write_text(json.dumps(metadata,indent=2,sort_keys=True)+'\n')
print(json.dumps(metadata['candidate_after'],indent=2))
