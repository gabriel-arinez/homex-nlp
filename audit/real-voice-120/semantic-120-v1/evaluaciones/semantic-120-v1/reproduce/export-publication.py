"""Export only this run's auditable text, console logs and final screenshots.

Original local evidence is never edited. Replay clips and full screencast archives
stay private; trace event streams are credential-sanitized and retained separately.
"""
import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path, PurePosixPath
from zipfile import ZipFile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def safe_member(name):
    member = PurePosixPath(name)
    if not member.parts or member.is_absolute() or ".." in member.parts or "\\" in name or "\x00" in name or member.parts[0].endswith(":"):
        raise ValueError(f"Unsafe archive member: {name!r}")
    return member


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    helper = args.repo / 'audit/real-voice-120/evaluaciones/audit-120/export_publication.py'
    spec = importlib.util.spec_from_file_location('previous_publication_sanitizer', helper)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sanitizer = module.Sanitizer()
    run = 'semantic-120-v1'
    sources = []
    for name in ('evaluaciones', 'logs'):
        root = args.corpus / name / run
        sources.extend((p, Path(name) / run / p.relative_to(root))
                       for p in sorted(root.rglob('*')) if p.is_file())
    for source, _ in sources:
        if source.is_symlink():
            raise ValueError(f'Symlink refused: {source}')
        if source.suffix == '.zip':
            with ZipFile(source) as archive:
                for entry in archive.infolist():
                    safe_member(entry.filename)
            module.gather_zip(sanitizer, source)
        elif source.suffix.lower() in {'.json', '.jsonl', '.py', '.sh', '.mjs', '.log', '.txt'}:
            sanitizer.collect_bytes(source.read_bytes())
    args.output.mkdir(parents=True, exist_ok=False)
    rows = []
    allowed = {'.json', '.jsonl', '.csv', '.tsv', '.md', '.txt', '.html', '.log', '.py', '.sh', '.mjs', '.png'}
    for source, relative in sources:
        raw = source.read_bytes()
        row = dict(source=str(source.relative_to(args.corpus)), source_sha256=digest(raw),
                   source_bytes=len(raw))
        target = args.output / relative
        portable = {'README.md','bootstrap-v3.sh','runner-v3.sh','setup-v3.py','snapshot-v3.py','worker-v3.py','verify-v3.py','probe-v3.mjs'}
        if any(part.startswith('integration-v') for part in relative.parts) and 'reproduce' in relative.parts and source.name not in portable:
            row['status'] = 'PRIVATE_HISTORICAL_RUNTIME_HELPER_RETAINED_LOCAL'
            rows.append(row)
            continue
        if source.suffix == '.zip':
            # Preserve full local trace identity, not thousands of redundant frames.
            row['status'] = 'FULL_TRACE_RETAINED_LOCAL_TEXT_EVENTS_EXPORTED'
            row['trace_entries'] = []
            with ZipFile(source) as archive:
                excluded = module.zip_audio_members(archive)
                for entry in archive.infolist():
                    if entry.is_dir():
                        continue
                    data = archive.read(entry)
                    item = dict(entry=entry.filename, source_sha256=digest(data), bytes=len(data))
                    if entry.filename.endswith(('.trace', '.network', '.stacks')) and entry.filename not in excluded:
                        clean = sanitizer.clean_bytes(data, excluded)
                        member = safe_member(entry.filename)
                        boundary = target.with_suffix('.events').resolve()
                        out = (boundary / str(member)).resolve()
                        if not out.is_relative_to(boundary):
                            raise ValueError('Archive output escaped destination')
                        out.parent.mkdir(parents=True, exist_ok=True)
                        out.write_bytes(clean)
                        item.update(export=str(out.relative_to(args.output)), export_sha256=digest(clean),
                                    status='SANITIZED_EVENT_STREAM')
                    else:
                        item['status'] = 'AUXILIARY_TRACE_RESOURCE_RETAINED_LOCAL'
                    row['trace_entries'].append(item)
            rows.append(row)
            continue
        if source.suffix.lower() not in allowed or '__pycache__' in source.parts:
            row['status'] = 'LOCAL_AUDIO_ARTIFACT_OR_CACHE_NOT_PUBLISHED'
            rows.append(row)
            continue
        if source.name == '.env' or source.name.startswith('.env.') or module.audio_bytes(raw):
            raise ValueError(f'Unexpected private payload: {source}')
        clean = sanitizer.clean_bytes(raw)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(clean)
        row.update(export=str(relative), export_sha256=digest(clean), export_bytes=len(clean),
                   status='IDENTICAL' if raw == clean else 'SANITIZED_COPY')
        rows.append(row)
    result = dict(schema_version='semantic-publication/1', records=rows,
                  status_counts=dict(Counter(r['status'] for r in rows)),
                  redaction_counts=dict(sanitizer.counts),
                  policy='Private originals intact. No audio, wheel smoke artifacts, model weights, database or environment. Full local traces preserved; sanitized text event streams and final screenshots published, not redundant screencast frames.',
                  historical_publication_unchanged=True)
    (args.output / 'SEMANTIC-PUBLICATION-MANIFEST.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: v for k,v in result.items() if k != 'records'}, indent=2))


if __name__ == '__main__':
    main()
