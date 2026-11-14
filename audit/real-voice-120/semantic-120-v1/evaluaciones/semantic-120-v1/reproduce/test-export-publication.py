"""Synthetic exporter safety probes; no user credentials or source recordings."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

repo=Path('/home/gabriel/HOMEX/homex-nlp')
script=Path(__file__).with_name('export-publication.py')
scratch=Path(tempfile.mkdtemp(prefix='semantic-export-regression-'))
for name in ('safe','unsafe'):
    corpus=scratch/name
    data=corpus/'evaluaciones/semantic-120-v1'
    data.mkdir(parents=True)
    (corpus/'logs/semantic-120-v1').mkdir(parents=True)
    with ZipFile(data/'trace.zip','w') as archive:
        entry='../../../../outside-probe.trace' if name=='unsafe' else 'trace.trace'
        archive.writestr(entry,json.dumps({'password':'[REDACTED_AUTH]','name':'case.wav','mimeType':'audio/wav','buffer':'Synthetic-Inline-Audio-123'}))
    output=scratch/(name+'-out')
    result=subprocess.run([sys.executable,str(script),'--repo',str(repo),'--corpus',str(corpus),'--output',str(output)],capture_output=True,text=True)
    if name=='unsafe':
        assert result.returncode!=0 and 'Unsafe archive member' in result.stderr
        assert not output.exists() and not (scratch/'outside-probe.trace').exists()
    else:
        assert result.returncode==0, result.stderr
        content=(output/'evaluaciones/semantic-120-v1/trace.events/trace.trace').read_text()
        assert '[REDACTED_AUTH]' not in content
        assert 'Synthetic-Inline-Audio-123' not in content
        assert '[REDACTED_AUTH]' in content and '[SOURCE_AUDIO_OMITTED]' in content
        manifest=json.loads((output/'SEMANTIC-PUBLICATION-MANIFEST.json').read_text())
        assert manifest['historical_publication_unchanged']
print('PASS: unsafe archive rejected before output creation; credentials and inline audio removed.')
print('Parent cleanup scratch:',scratch)
