"""Record local chain identities and draft PR content, without remote access."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

OUT=Path('/home/gabriel/Descargas/HOMEX_Guiones_Evaluacion_Voz/evaluaciones/audit-120')
backup=OUT/'before-local-chain';backup.mkdir(exist_ok=False)
for name in ['progress-report.md','latest-evaluation.json']:shutil.copy2(OUT/name,backup/name)

def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def identity(branch):return git('rev-parse',branch)
def changed(base,head):
    rows=git('diff','--numstat',f'{base}...{head}').splitlines()
    return sum(int(a)+int(d) for a,d,_ in (line.split('\t',2) for line in rows))

branches=[
 {'position':0,'head':'feat/real-voice-120','base':'main','base_commit':'c94e7a89995a7157bd113a03bb8304321d30b0b1','title':'docs(audit): track real voice evaluation and remaining work','type_label':'type:docs','scope':'Audit specification, original request, decisions and retained evidence; draft integration tracker only.','tests':'Passive document structural readback and git diff --check passed. No new executable behavior in this branch.','risk':'none (passive specification/evidence)','file':'00-tracker.md'},
 {'position':1,'head':'chore/real-voice-120-01-evaluation','base':'feat/real-voice-120','title':'feat(evaluation): preserve auditable real voice baseline results','type_label':'type:feature','scope':'Safe exclusive/resumable corpus runner, deterministic metric tests and usage guide. Extractor rules are unchanged in this slice.','tests':'Clean detached commit:769 tests passed; schemas, Ruff lint/format,4 curated corpus validators and inventory audit passed. CLI help verified. Original120-case run evidence retained outside Git.','risk':'none for production behavior; audio preservation verified on240 original hashes','file':'01-evaluation.md'},
 {'position':2,'head':'fix/real-voice-120-02-extraction','base':'chore/real-voice-120-01-evaluation','title':'fix(nlp): preserve commercial fields in natural dictation','type_label':'type:bug','scope':'Six bounded extraction fixes with30 public-interface regression cases and grammar docs; no public schema, model or dependency change.','tests':'Clean detached code commitf139bd2:799 tests; schemas/Ruff/corpus/inventory passed.24 source hashes match after-nlp-v5 and independently verified candidate. Previously observed99 backend/306 frontend checks and real4-form plus latest3-poltrona uploads retained; these are selected-field application proofs, not full corpus semantic accuracy. Offline wheel/sdist smoke/privacy/reproducible rebuild passed; temporary artifacts are NOT a release.','risk':'item3(shared extraction/parser behavior); independent verification performed','file':'02-extraction.md'},
]
pr_dir=OUT/'pr-drafts';pr_dir.mkdir(exist_ok=False)
for branch in branches:
    branch['head_commit']=identity(branch['head'])
    base=branch.get('base_commit',branch['base'])
    branch['authored_lines']=changed(base,branch['head'])
    assert branch['authored_lines']<=400
    diagram='main\n └── feat/real-voice-120 [draft/no merge]\n      └── chore/real-voice-120-01-evaluation\n           └── fix/real-voice-120-02-extraction'
    diagram=diagram.replace(branch['head']+' ', '📍 '+branch['head']+' ',1) if branch['position']==0 else diagram.replace(branch['head']+'\n','📍 '+branch['head']+'\n',1) if branch['position']==1 else diagram.replace(branch['head'],'📍 '+branch['head'],1)
    body=f'''# {branch['title']}

## Publication state

LOCAL DRAFT ONLY. No remote lookup, push, issue mutation, PR creation or CI query
has been performed. Do not submit until the remote destination and credential
session are authorized and applicable repository issue/label policies are checked.
No issue number or approved status has been invented.

## Summary

{branch['scope']}

## Chain Context

| Field | Value |
|---|---|
| Strategy | Feature Branch Chain |
| Tracker | feat/real-voice-120; remote PR identity pending |
| Position | {branch['position']} (tracker0; children1–2) |
| Base | `{branch['base']}` |
| Head | `{branch['head']}` |
| Head commit | `{branch['head_commit']}` |
| Review budget | {branch['authored_lines']} /400 authored lines |
| Includes | {branch['scope']} |
| Excludes | Production changes, corpus/audio publication, versioned release, backend vendoring, unresolved audit work |

### Chain Overview

```text
{diagram}
```

## Checks actually observed

{branch['tests']}

Remote CI: **not queried or run by this local preparation**. RDD is globally OFF
(disabled/unmanaged); no receipt or review approval is claimed. No merge or
ready-for-review transition is authorized by this draft.

## Audit limitations

Current confirmed categories73 custom furniture/27chairs/7floors/13OTRO=120.
Original240 audio hashes unchanged; immutable ASR baseline and corrected original-
code routing retained. Full field annotation/audio adjudication and independent
real-audio generalization are still open.85 explicit unit-price labels give
ASR62→65 matches and reference67→70; this is a PARTIAL oracle, not NLP accuracy.
The three additional original-code baseline matches after poltrona routing are a
CORPUS correction, not a code improvement. No raw commercial corpus/audio/model
is included in these branches. Installed backend remains on its previous0.1.21
wheel; source integration tests used candidate source explicitly.

## Rollback and delivery

Revert only this child range to its listed parent; preserve other slices and all
original corpus files. Tracker stays draft/no-merge until remaining feature work
and human review are complete. Do not force-push, merge, deploy, rewrite history,
relabel an existing issue, or publish same-version build-smoke artifacts.

Risk: {branch['risk']}.
'''
    (pr_dir/branch['file']).write_text(body)
manifest={'repository':'gabriel-arinez/homex-nlp','strategy':'feature-branch-chain','user_authorization':'si, procede (accepts chain strategy; does not identify a remote credential)',
          'draft_no_merge':True,'remote_contacted':False,'remote_auth_inspected':False,'pushed':False,'pull_requests_created':False,'remote_ci':'UNKNOWN_NOT_QUERIED',
          'branches':branches,'commits':[{'sha':line.split(' ',1)[0],'subject':line.split(' ',1)[1]} for line in git('log','--reverse','c94e7a8..HEAD','--format=%H %s').splitlines()]}
(OUT/'local-chain.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
latest=json.loads((OUT/'latest-evaluation.json').read_text());latest['local_chain']='local-chain.json';latest['committed_candidate']=identity('fix/real-voice-120-02-extraction');latest['extraction_behavior_commit']='f139bd224f54f0c643b023c121c2ccba79e68054';latest['publication']='LOCAL_COMMITS_ONLY_REMOTE_AUTH_PENDING'
(OUT/'latest-evaluation.json').write_text(json.dumps(latest,indent=2)+'\n')
p=OUT/'progress-report.md';report=p.read_text();report=report.replace('No remote\n   operation performed; no CI status invented. Installed backend wheel still0.1.21;', 'Local chain ff4df92→c02c6df→f139bd2→40e4665 now committed; remote\n   authorization/push/PR/CI remain pending. Installed backend wheel still0.1.21;')
report+='''
## Local feature-chain checkpoint

User approved Feature Branch Chain. Local tracker`feat/real-voice-120` is based on
c94e7a8; evaluation child targets tracker; extraction child targets evaluation.
Actual child review budgets397/339/205 authored lines. Commits:ff4df92 specification,
c02c6df evaluator,f139bd2 fixes,40e4665 verification evidence. No merge, push or
remote lookup performed. See local-chain.json and pr-drafts/ for exact refs/bodies.

Each code slice was verified in a clean detached worktree: evaluator769 tests,
extraction799 tests; schemas/lint/format/curated corpus/inventory passed. Fully
offline wheel and sdist installation/privacy/required-files/rebuild checks passed.
Temporary same-version0.1.21 test artifacts are in packaging-smoke-only/; they are
NOT a versioned release and were never installed into the backend or published.
Original workspace published distributions remain unchanged.

Next publication prerequisite: explicit authorization for remote repository and
credential/session, followed by repository policy/issue lookup. No approval or
issue identity has been inferred. The full audit remains incomplete.
'''
p.write_text(report)
print(json.dumps({'heads':[(b['head'],b['head_commit'],b['authored_lines']) for b in branches],'publication':'local only','remote_contacted':False},indent=2))
