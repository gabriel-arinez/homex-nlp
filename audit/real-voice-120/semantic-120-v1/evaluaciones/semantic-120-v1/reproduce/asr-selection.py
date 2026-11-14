"""Summarize ASR tradeoffs without selecting the best result per case."""
import json
import statistics
from collections import defaultdict
from pathlib import Path
root=Path('/home/gabriel/Descargas/HOMEX_Guiones_Evaluacion_Voz/evaluaciones/semantic-120-v1')
summary=json.loads((root/'comparison-v5/summary.json').read_text())
deltas=json.loads((root/'comparison-v5/asr-recoveries-regressions.json').read_text())
baseline=[json.loads(p.read_text()) for p in (root.parent/'audit-120/baseline-routing-v2/cases').glob('*.json')]
groups=defaultdict(list)
for row in baseline:groups[row['category']].append(row)
original={cat:{kind:{'errors':sum(r['metrics'][kind]['errors'] for r in rows),
                        'denominator':sum(r['metrics'][kind]['reference_length'] for r in rows)}
               for kind in ('wer','cer')} for cat,rows in groups.items()}
configs=[]
for name, cell in sorted(summary['cells'].items()):
    if not name.endswith('__current_nlp') or name.startswith('script_control'):continue
    config=name.split('__')[0]
    change=[d for d in deltas if d['nlp_configuration']=='current_nlp' and d['candidate_asr']==config]
    data=dict(configuration=config,supported_fields=cell['supported_numerator'],denominator=cell['supported_denominator'],
              no_proposal=cell['no_proposal'],raw_wer=cell['wer']['original'],strict_wer=cell['wer']['strict_normalized'],
              recovered_scalar_tuples=sum(len(d['recoveries']) for d in change),
              lost_scalar_tuples=sum(len(d['regressions']) for d in change),
              recovery_cases=sum(bool(d['recoveries']) for d in change),regression_cases=sum(bool(d['regressions']) for d in change))
    if config!='original':
        rows=[json.loads(p.read_text()) for p in (root/'asr-experiments'/config/'cases').glob('*.json')]
        data['resources']=dict(wall_seconds=sum(r['wall_seconds'] for r in rows),cpu_seconds=sum(r['cpu_seconds'] for r in rows),
            median_seconds=statistics.median(r['wall_seconds'] for r in rows),max_seconds=max(r['wall_seconds'] for r in rows),
            process_peak_rss_kib=max(r['process_peak_rss_kib'] for r in rows),
            note='Concurrent workload diagnostic; peak RSS belongs to entire process, not incremental per-case memory')
    configs.append(data)
result=dict(original_categories=original,configurations=configs,
    decision='KEEP_ORIGINAL_PRODUCTION_ASR',
    rationale='Context/VAD recover additional script-scalar tuples but also lose previous matches. Incomplete acoustic/association gold and unverified extra predictions do not justify a global production change. No per-case cherry-picking or complete reference prompts were used.',
    alternative_model='Not promoted or downloaded; all experiments use the original hashed local Whisper Small CPU/int8 model',
    runtime_completion='600 successful case artifacts and final240audio hash proof; original session handle expired across turn interruptions, so its shell exit code is not asserted')
(root/'asr-selection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
lines=['','## ASR baseline and promotion decision','',
       '| Original category | WER errors / words | CER errors / characters |','| --- | ---: | ---: |']
for cat,row in original.items():lines.append(f"| {cat} | {row['wer']['errors']}/{row['wer']['denominator']} | {row['cer']['errors']}/{row['cer']['denominator']} |")
lines+=['','| ASR setting + corrected NLP | Supported script tuples | Recoveries versus original | Lost previous scalar matches | No proposal |','| --- | ---: | ---: | ---: | ---: |']
for row in configs:lines.append(f"| {row['configuration']} | {row['supported_fields']}/{row['denominator']} | {row['recovered_scalar_tuples']} | {row['lost_scalar_tuples']} | {row['no_proposal']} |")
lines+=['',result['rationale'],'',
        'Candidate-only literal material evidence and structured applied fields are not interchangeable with full commercial association accuracy. In particular, candidate colors not applied as primary/secondary are not silently counted as usable form colors. Missing fixture catalog values and unspecified price modalities need separate review, not fabricated completion.',
        'See asr-selection.json for CPU/wall/median/max/peak-process-memory and exact decision scope. The original ASR process handle expired after turn interruptions; completion is established by all600 successful case artifacts, final aggregates and240 unchanged audio hashes, not an invented shell exit status.']
with (root/'final-report.md').open('a') as stream:stream.write('\n'.join(lines)+'\n')
print(json.dumps({r['configuration']:[r['supported_fields'],r['recovered_scalar_tuples'],r['lost_scalar_tuples']] for r in configs}))
