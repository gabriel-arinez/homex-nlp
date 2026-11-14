"""Read-only original-audio and installed-wheel identity verification."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import zipfile
import homex_nlp

s = Path(os.environ['HOMEX_REPRO_SCRATCH']).resolve()
c = Path(os.environ['HOMEX_REPRO_CORPUS']).resolve()
assert Path(sys.prefix).resolve() == s / 'venv'
package = Path(homex_nlp.__file__).resolve()
assert package.is_relative_to(s / 'venv'), package
assert importlib.metadata.version('homex-nlp') == '0.1.22'
wheel = s / 'backend/vendor/homex_nlp-0.1.22-py3-none-any.whl'
sha = hashlib.sha256(wheel.read_bytes()).hexdigest()
assert sha == 'c1a085f899a9f2f0797f332304fcf8eeea91f4837d5d06a9a2ca5a6c07815a80'
modules = []
with zipfile.ZipFile(wheel) as archive:
    for name in archive.namelist():
        if name.startswith('homex_nlp/') and name.endswith('.py'):
            assert archive.read(name) == (package.parent.parent / name).read_bytes(), name
            modules.append(name)
ledger = json.loads((c / 'evaluaciones/audit-120/audio-ledger.json').read_text())
checked = []
for row in ledger:
    for entry in row['audio'].values():
        if isinstance(entry, dict) and 'sha256' in entry:
            target = c / entry['path']
            assert hashlib.sha256(target.read_bytes()).hexdigest() == entry['sha256'], target
            checked.append(entry['path'])
assert len(checked) == 240
result = dict(wheel_sha256=sha, package_path=str(package), python_modules=modules,
              original_audio_unchanged=checked, stage=sys.argv[1])
with (s / 'evidence' / ('identity-' + sys.argv[1] + '.json')).open('x') as f:
    json.dump(result, f, indent=2)
print('Verified 240 original audio hashes and installed final wheel bytes.')
