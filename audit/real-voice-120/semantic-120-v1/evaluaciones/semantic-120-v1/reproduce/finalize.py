"""Finalize a complete, source-bound development audit; never claim acoustic gold."""
import argparse
import hashlib
import json
import statistics
import subprocess
from collections import Counter
from pathlib import Path


def load(path):
    return json.loads(path.read_text())


def write(path, value):
    assert not path.exists(), f'Preserve historical artifact: {path}'
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--corpus', type=Path, required=True)
    args = parser.parse_args()
    root = args.corpus / 'evaluaciones/semantic-120-v1'
    comparison = root / 'comparison-v5'
    summary = load(comparison / 'summary.json')
    experiments = load(root / 'asr-experiments/summary.json')
    configs = ['temperature_zero','no_previous','vad_no_previous','wider_beam','context_no_previous']
    assert set(experiments) == set(configs) and not summary['pending_asr_configurations']
    assert len(summary['cells']) == 14 and all(c['complete'] and c['cases']==120 for c in summary['cells'].values())
    references = {r['id']:r for r in map(json.loads, (root/'references-v2/cases.jsonl').read_text().splitlines())}
    assert len(references)==120
    assert Counter(r['category'] for r in references.values()) == Counter(MUEBLE_MEDIDA=73,SILLA=27,PISO_FLOTANTE=7,OTRO=13)
    identity = load(comparison/'identity.json')
    for name, digest in identity['current_source_hashes'].items():
        assert hashlib.sha256((args.repo/name).read_bytes()).hexdigest()==digest
    rows = {(cell,p.stem):load(p) for cell in summary['cells'] for p in (comparison/'cases'/cell).glob('*.json')}
    invariants = Counter()
    for row in rows.values():
        raw=row['nlp_raw']; text=row['text_original']
        assert 'execution_error' not in raw
        evidence=raw.get('candidates',raw.get('evidence',[]))
        assert len({e['candidate_id'] for e in evidence})==len(evidence)
        for e in evidence:
            assert text[e['start']:e['end']]==e['text'], (row['id'],e)
            invariants['exact_candidate_spans']+=1
        for channel in ('reference','asr'):
            original=row['script_text'] if channel=='reference' else text
            for t in row['normalization'][channel+'_transforms']:
                assert original[t['start']:t['end']]==t['raw']
                invariants['exact_normalization_spans']+=1
    matrix=[]; causes=[]
    no_proposal=[]
    for identifier, ref in sorted(references.items()):
        old=rows['original__baseline_nlp',identifier]; new=rows['original__current_nlp',identifier]
        control=rows['script_control__current_nlp',identifier]
        ctrl={tuple(f['key']):f['matched'] for f in control['score']['field_results']}
        old_matches={tuple(f['key']) for f in old['score']['field_results'] if f['matched']}
        unsupported=set(new['supported_score']['unsupported_verified_reference_indices'])
        for f in new['score']['field_results']:
            key=tuple(f['key']); refs=[ref['script_fields'][i] for i in f['reference_indices']]
            unresolved_price = (key[0]=='price' and all(r.get('modality')=='UNSPECIFIED' for r in refs)
                                and (new['nlp_raw'].get('item_proposal') or {}).get('price') is None)
            cause=('FUNCTIONALITY_UNSUPPORTED_BY_CATEGORY_CONTRACT' if set(f['reference_indices']) <= unsupported
                   else 'LEGITIMATE_UNSPECIFIED_PRICE_MODALITY_ABSTENTION' if unresolved_price
                   else 'NLP_RULE_SCALAR_RECOVERY' if f['matched'] and key not in old_matches
                   else 'SCALAR_MATCH_ONLY_ASSOCIATION_UNVERIFIED' if f['matched']
                   else 'TEXT_CHANNEL_DISCREPANCY_PENDING_ACOUSTIC_REVIEW' if ctrl.get(key)
                   else 'NLP_SUPPORT_ASSOCIATION_OR_REFERENCE_REVIEW_REQUIRED')
            causes.append(dict(id=identifier,category=ref['category'],field_key=f['key'],classification=cause,
                               script_control_matched=ctrl.get(key),original_asr_matched=f['matched'],
                               source_reference_indices=f['reference_indices'],acoustic_status='PENDING_HUMAN_LISTENING',
                               confirmed_acoustic_error=False,association_status='UNVERIFIED'))
        if new['no_proposal']:
            no_proposal.append(dict(id=identifier,category=ref['category'],warnings=new['nlp_raw'].get('warnings',[]),
                                    artifact=f'comparison-v5/cases/original__current_nlp/{identifier}.json'))
        matrix.append(dict(id=identifier,category=ref['category'],family=ref['family'],leakage_group=ref['leakage_group'],
                           reference=f'references-v2/cases/{identifier}.json',
                           reference_status='SCRIPT_LITERAL_SCALARS_ONLY_ACOUSTIC_AND_ASSOCIATION_PENDING',
                           audio=new['audio'],cells=[dict(cell=cell,artifact=f'comparison-v5/cases/{cell}/{identifier}.json',
                                supported_score=rows[cell,identifier]['supported_score'],
                                no_proposal=rows[cell,identifier]['no_proposal']) for cell in sorted(summary['cells'])]))
    (root/'case-matrix.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in matrix))
    write(root/'root-cause-matrix.json',dict(scope='Current NLP on frozen original ASR; per-field script diagnostic, not acoustic adjudication',
                                          counts=dict(Counter(r['classification'] for r in causes)),rows=causes))
    write(root/'cases-needing-review.json',dict(human_listening_pending=sorted(references),no_proposal=no_proposal,
        unverified_association_cases=sorted(references),confirmed_false_positives=None,commercial_precision=None,
        reason='No complete human acoustic/association gold; no precision or independent generalization claim.'))
    resource_rows=[]
    for config in configs:
        cases=[load(p) for p in (root/'asr-experiments'/config/'cases').glob('*.json')]
        assert len(cases)==120 and not any('error' in c for c in cases)
        resource_rows.append(dict(configuration=config,summary=experiments[config],
            case_metrics_artifact=f'asr-experiments/{config}/cases',
            timing_scope='Concurrent local workload diagnostics, not controlled isolated benchmarks'))
    write(root/'experiment-register.json',dict(configurations=resource_rows,identity='asr-experiments/identity.json',
        original_asr='Historical baseline-routing-v2; model and production configuration unchanged',
        model_alternative_promoted=False,selection='Retain original ASR until verified commercial outcomes justify change'))
    changes=[r for r in load(comparison/'recoveries-regressions.json') if r['asr_configuration']=='original']
    base=summary['cells']['original__baseline_nlp']; current=summary['cells']['original__current_nlp']
    final=dict(status='VERIFIED_ENGINEERING_IMPROVEMENT_NOT_COMPLETE_ACOUSTIC_OR_COMMERCIAL_PRECISION_VALIDATION',
        cases=120,categories=dict(Counter(r['category'] for r in references.values())),
        baseline_commit='b851b5aa15a04e5ab1046271f124cc05c3135da8',source_release_commit='02d4299',
        nlp_delivery_branch='feat/real-voice-120-results',backend_local_branch='feat/real-voice-120-semantic',
        backend_local_commit='7040564',backend_publication='PENDING_EXPLICIT_DESTINATION_AND_CREDENTIAL_AUTHORIZATION',
        frontend_commit='feece0a99689c9a73c601f249ea1af3bf11e1b6e',
        wheel=load(args.repo/'docs/catalog-release.json'),
        original_asr_supported_scalar_fields=dict(before=base['supported_numerator'],after=current['supported_numerator'],denominator=current['supported_denominator']),
        recovery_cases=sum(bool(r['recoveries']) for r in changes),regression_cases=sum(bool(r['regressions']) for r in changes),
        no_proposal=dict(before=base['no_proposal'],after=current['no_proposal'],ids=[r['id'] for r in no_proposal]),
        all_asr_runs=600,nlp_comparison_rows=len(rows),invariants=dict(invariants),
        acoustic_denominator=0,association_denominator=0,confirmed_false_positives=None,independent_audio_generalization=None,
        integration='integration-v3;8/8 actual browser/audio scenarios,19 authority snapshots unchanged,240 audio hashes unchanged',
        checks=dict(nlp_tests=891,backend_relevant_tests=99,frontend_tests=306,independent_installed_guards=9),
        source_ci='ci-source-584e90b.json; all4jobs successful; evidence-only delivery commit checked separately on GitHub',
        superseded_runs={'references':'Superseded by references-v2; coordinated-measure proposals were corrected without changing original sources',
                         'comparison-v1':'Intermediate source and incomplete diagnostic', 'comparison-v2':'Intermediate source; adapters superseded',
                         'comparison-v3':'Corrected adapters; pre-final semantic source', 'comparison-v4':'Pre-final conservative code/gauge/count guards'})
    write(root/'latest-evaluation.json',final)
    lines=['# Real-voice semantic intervention — verified scope and remaining limits','',
           'The engineering intervention improves supported script-scalar coverage on unchanged original ASR, with no lost previously matched scalar tuple in that comparison. This is **not** a completed human-acoustic or full commercial precision evaluation. All120 cases are development data.','',
           f"Original ASR + baseline NLP: **{base['supported_numerator']}/{base['supported_denominator']}** supported scalar tuples; corrected NLP: **{current['supported_numerator']}/{current['supported_denominator']}**. Recoveries in {final['recovery_cases']} cases; scalar-loss cases: {final['regression_cases']}. No-proposal cases: {base['no_proposal']}→{current['no_proposal']}.",'',
           'The denominator deduplicates verified script literals/scalars within each case and excludes unsupported category field families. It does not validate associations, modality, acoustic truth, every feature subtype or precision. OTRO configurator omissions are not NLP defects. Full-coverage and supported denominators are both retained.','',
           '## Per-category NLP on unchanged original ASR','',
           '| Category | Cases | Before supported matches | After supported matches | Denominator | No proposal before→after |','| --- | ---: | ---: | ---: | ---: | --- |']
    for cat,b in base['categories'].items():
        n=current['categories'][cat]
        lines.append(f"| {cat} | {n['cases']} | {b['supported_numerator']} | {n['supported_numerator']} | {n['supported_denominator']} | {b['no_proposal']}→{n['no_proposal']} |")
    lines+=['','## ASR experiment register','',
            'Raw WER/CER are script-relative, not verified spoken accuracy. Strict numeric-commercial WER is reported separately in comparison-v5; metric-only changes are not recognition gains. Exact parameters/model hashes/segments/tokens/timing/CPU/peak-process-RSS are retained in asr-experiments. Latencies overlap other test workloads.','',
            '| Setting | Category | WER errors / words | CER errors / characters |','| --- | --- | ---: | ---: |']
    for config in configs:
        for cat,m in experiments[config]['categories'].items():
            lines.append(f"| {config} | {cat} | {m['wer']['errors']}/{m['wer']['denominator']} | {m['cer']['errors']}/{m['cer']['denominator']} |")
    lines+=['','No production ASR model/configuration was changed. Candidate selection cannot rely on WER or one favorable case; all five settings have full two-version NLP comparisons.','',
            '## Corrections and checks','',
            '- Conservative furniture/coreference/component boundaries; preserve real independent-order abstention.',
            '- Axis-adjective disambiguation, unitless spoken scalar evidence without invented units, component-local material/thickness evidence.',
            '- USB/HDMI/interface connector counts, strict compound integers and alternative-count abstention.',
            '- Explicit presiunitario alias, bounded catalog names, reason-bearing spelling equivalence, ambiguous initial de/a abstention, explicit HDF8mm gauge.',
            '- Every defect had observed RED and GREEN regression logs; failed iterations are retained. Final891NLP tests,99backend tests and306frontend tests passed, alongside schemas/lint/format/type/build.',
            '- Actual final wheel consumed from backend site-packages;26modules match the wheel.8/8 actual audio browser cases cover four forms;19 authoritative-model snapshots unchanged;240 original audio hashes unchanged.',
            '- Reproducible0.1.22 wheel identity fixed without overwriting historical0.1.21 artifacts. Exactly two verified historical tokenizer-hash fingerprints exempted; all four source-commit CI jobs green.',
            '', '## Remaining limits and difficult cases','',
            f"No proposal on original ASR: {', '.join(final['no_proposal']['ids'])}. See cases-needing-review.json for warnings, all120 pending acoustic/association cases and every full raw result.",
            'MP-0036 keeps its unitless depth and unspecified price pending; MP-0045 does not force composite side geometry into unrelated global axes. Repeated original-ASR passages are not silently erased or treated as genuine duplicate orders. SIL-0016 de43 remains unresolved instead of fabricating D43. New unmatched predictions are review candidates, not confirmed false positives.',
            'Full human field association validation, listening adjudication and independent recordings are unavailable.69 connected commercial/source groups prevent claiming these development examples as a holdout. The independent-audio protocol is in references-v2; no generalization percentage is invented.',
            'Backend consumer commit7040564 is local on its controlled branch; remote publication awaits explicit destination/credential authorization. No frontend source change, main merge or deployment was made.',
            '', '## Evidence navigation','',
            '- latest-evaluation.json: source versions, hashes, denominators, scope and superseded-run index.',
            '- case-matrix.jsonl: all120 IDs with14 comparison cells each; comparison-v5 contains1680 complete raw case results and field expectations/predictions.',
            '- root-cause-matrix.json and comparison-v5/root-cause-isolation.json: contract-supported classifications versus uncertain text-channel/association causes.',
            '- references-v2: all field proposals, document/script/ASR provenance and private timestamped playback index. No automatic transcript is human gold.',
            '- integration-v3 and logs/semantic-120-v1: exact commands, screenshots, raw responses, immutable authority snapshots and complete console output.',
            '- Raw recordings,462 replay clips and full large screencast archives remain local. Public copies sanitize credentials and export text trace events plus final screenshots with an omission/hash ledger.',
            '', 'Risk: items3(shared parsing/evidence consumers) and5(package distribution and consumer version binding). Independent source/installed-wheel and end-to-end checks passed in their documented scope.']
    (root/'final-report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(final,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
