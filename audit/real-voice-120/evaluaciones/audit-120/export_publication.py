"""Export audit copies for public Git publication without credentials or source audio.

Raw local evidence is never modified. Source/export hashes and trace redactions
are recorded. This helper does not push, open PRs, or change product behavior.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
from collections import Counter
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

MARKER = '[REDACTED_AUTH]'
AUDIO_SUFFIXES = {'.aac', '.wav', '.mp3', '.m4a', '.ogg', '.webm', '.flac'}
SENSITIVE = {'password','passwd','pwd','token','access','refresh','access_token','refresh_token',
             'authorization','cookie','set-cookie','secret','secret_key','django_secret_key',
             'client_secret','csrfmiddlewaretoken','csrftoken','sessionid','x-csrftoken','x-xsrf-token'}
TOKEN = re.compile(r'\b(?:eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b')
LITERAL = re.compile(r'''(?i)((?:["'])?(?:[a-z0-9_]*password|[a-z0-9_]*secret_key)(?:["'])?\s*[:=]\s*)(["'])([^"'\r\n]+)\2''')
PASSWORD_SELECTOR = re.compile(r'password|contrase(?:ñ|n)a', re.I)


def digest(data):return hashlib.sha256(data).hexdigest()
def sensitive(name):
    name=str(name).casefold().replace('-','_')
    return name in {n.replace('-','_') for n in SENSITIVE} or name.endswith(('_password','_secret_key'))

def audio_bytes(data):
    start=0
    while (index:=data.find(b'RIFF',start))>=0:
        if data[index+8:index+12]==b'WAVE' and len(data)>=index+12:
            size=struct.unpack('<I',data[index+4:index+8])[0]
            if 36<=size<=len(data)-index-8:return True
        start=index+4
    return data.startswith(b'fLaC') or (len(data)>2 and data[0]==255 and data[1]&0xF6==0xF0)


class Sanitizer:
    def __init__(self):self.secrets=set();self.counts=Counter()

    def remember(self,value):
        if isinstance(value,str) and len(value)>=12 and not any(x in value for x in ('REDACTED','REPLACE_','${','$( ')):
            self.secrets.add(value)

    def collect(self,obj):
        if isinstance(obj,list):
            for item in obj:self.collect(item)
        if not isinstance(obj,dict):return
        params=obj.get('params')
        if isinstance(params,dict) and PASSWORD_SELECTOR.search(str(params.get('selector',''))):self.remember(params.get('value'))
        if sensitive(obj.get('name','')):self.remember(obj.get('value'))
        for key,value in obj.items():
            if sensitive(key) and isinstance(value,str):self.remember(value)
            self.collect(value)

    def collect_bytes(self,data):
        try:text=data.decode('utf-8')
        except UnicodeDecodeError:return
        for match in LITERAL.finditer(text):self.remember(match[3])
        for line in text.splitlines():
            try:self.collect(json.loads(line))
            except (ValueError,TypeError):pass
        try:self.collect(json.loads(text))
        except (ValueError,TypeError):pass

    def clean_text(self,text):
        for secret in sorted(self.secrets,key=len,reverse=True):
            if secret in text:
                self.counts['known_sensitive_value']+=text.count(secret);text=text.replace(secret,MARKER)
            escaped=json.dumps(secret,ensure_ascii=False)[1:-1]
            if escaped!=secret and escaped in text:
                self.counts['escaped_sensitive_value']+=text.count(escaped);text=text.replace(escaped,MARKER)
        text,n=TOKEN.subn(MARKER,text);self.counts['credential_token_pattern']+=n
        def literal(match):
            if match[3]==MARKER:return match[0]
            self.counts['literal_credential_assignment']+=1
            return match[1]+match[2]+MARKER+match[2]
        return LITERAL.sub(literal,text)

    def clean_obj(self,obj,excluded=frozenset()):
        if isinstance(obj,list):return [self.clean_obj(v,excluded) for v in obj]
        if isinstance(obj,str):return self.clean_text(obj)
        if not isinstance(obj,dict):return obj
        result={};is_header=sensitive(obj.get('name',''))
        params=obj.get('params');password_fill=isinstance(params,dict) and PASSWORD_SELECTOR.search(str(params.get('selector','')))
        uploaded_audio=str(obj.get('mimeType','')).startswith('audio/') or Path(str(obj.get('fileName',obj.get('name','')))).suffix.casefold() in AUDIO_SUFFIXES
        for key,value in obj.items():
            if key in {'_file','_sha1','sha1'} and isinstance(value,str) and (value in excluded or 'resources/'+value in excluded):
                self.counts['audio_reference_removed']+=1;result['_publication_note']='Source audio resource omitted; original hash retained in publication ledger.';continue
            if uploaded_audio and key in {'buffer','base64'}:
                self.counts['inline_audio_removed']+=1;result[key]='[SOURCE_AUDIO_OMITTED]';continue
            if isinstance(value,str) and (sensitive(key) or (is_header and key=='value')):
                if value and value!=MARKER:self.counts['credential_field']+=1
                result[key]=MARKER if value else value;continue
            result[key]=self.clean_obj(value,excluded)
        if password_fill and isinstance(result.get('params'),dict) and result['params'].get('value'):
            result['params']['value']=MARKER;self.counts['password_fill_value']+=1
        return result

    def clean_bytes(self,data,excluded=frozenset()):
        try:text=data.decode('utf-8')
        except UnicodeDecodeError:return data
        try:
            obj=json.loads(text);clean=self.clean_obj(obj,excluded)
            if obj==clean:return data
            return (json.dumps(clean,ensure_ascii=False,indent=2)+'\n').encode()
        except ValueError:pass
        lines=text.splitlines(keepends=True);output=[]
        for line in lines:
            try:
                obj=json.loads(line);clean=self.clean_obj(obj,excluded)
                output.append(line if obj==clean else json.dumps(clean,ensure_ascii=False)+'\n')
            except ValueError:output.append(self.clean_text(line))
        return ''.join(output).encode()


def gather_zip(sanitizer,path):
    with ZipFile(path) as archive:
        for info in archive.infolist():
            if not info.is_dir():sanitizer.collect_bytes(archive.read(info))


def zip_audio_members(archive):
    excluded=set()
    for info in archive.infolist():
        if info.is_dir():continue
        data=archive.read(info)
        if Path(info.filename).suffix.casefold() in AUDIO_SUFFIXES or audio_bytes(data):excluded.add(info.filename)
        if info.filename.endswith('.network'):
            for line in data.splitlines():
                try:obj=json.loads(line)
                except ValueError:continue
                snapshot=obj.get('snapshot',{})
                for content in [snapshot.get('request',{}).get('postData',{}),snapshot.get('response',{}).get('content',{})]:
                    if not isinstance(content,dict):continue
                    is_audio=str(content.get('mimeType','')).startswith('audio/')
                    params=content.get('params') or []
                    is_audio=is_audio or any(isinstance(p,dict) and Path(str(p.get('fileName',''))).suffix.casefold() in AUDIO_SUFFIXES for p in params)
                    if is_audio:
                        ref=content.get('_file',content.get('_sha1'))
                        if ref:excluded.add(ref if ref in archive.namelist() else 'resources/'+ref)
    return excluded


def sanitize_zip(sanitizer,source,destination):
    records=[]
    with ZipFile(source) as original,ZipFile(destination,'w',compression=ZIP_DEFLATED,compresslevel=6) as target:
        excluded=zip_audio_members(original)
        for info in original.infolist():
            if info.is_dir():continue
            raw=original.read(info)
            if info.filename in excluded:
                records.append({'entry':info.filename,'source_sha256':digest(raw),'status':'OMITTED_EMBEDDED_SOURCE_AUDIO'});continue
            clean=sanitizer.clean_bytes(raw,excluded)
            zi=ZipInfo(info.filename,date_time=(1980,1,1,0,0,0));zi.compress_type=ZIP_DEFLATED
            target.writestr(zi,clean)
            if clean!=raw:records.append({'entry':info.filename,'source_sha256':digest(raw),'export_sha256':digest(clean),'status':'AUTH_REDACTED_OR_AUDIO_REFERENCE_REMOVED'})
        zi=ZipInfo('PUBLICATION-REDACTIONS.json',date_time=(1980,1,1,0,0,0));zi.compress_type=ZIP_DEFLATED
        target.writestr(zi,json.dumps(records,indent=2)+'\n')
    return records


def export(corpus,destination):
    sources=[]
    for folder in ['evaluaciones','logs']:
        sources += [(p,Path(folder)/p.relative_to(corpus/folder)) for p in sorted((corpus/folder).rglob('*')) if p.is_file()]
    for name in ['manifiesto.csv','README.md','referencias/guiones_referencia_pregrabacion.jsonl','referencias/trazabilidad_fuentes.jsonl']:
        sources.append((corpus/name,Path('corpus')/name))
    for p in sorted((corpus/'control').iterdir()):
        if p.is_file():sources.append((p,Path('corpus/control')/p.name))
    destination.mkdir(parents=True,exist_ok=False)
    sanitizer=Sanitizer()
    for source,_ in sources:
        if source.suffix=='.zip':gather_zip(sanitizer,source)
        else:sanitizer.collect_bytes(source.read_bytes())
    records=[]
    for source,relative in sources:
        assert not source.is_symlink(),source
        raw=source.read_bytes();row={'source':str(source.relative_to(corpus)),'export':str(relative),'source_bytes':len(raw),'source_sha256':digest(raw)}
        if '__pycache__' in source.parts or source.suffix=='.pyc':
            row['status']='OMITTED_GENERATED_CACHE';records.append(row);continue
        if source.name=='.env' or source.name.startswith('.env.') and source.name!='.env.example':
            row['status']='OMITTED_ENVIRONMENT_FILE';records.append(row);continue
        if source.suffix.casefold() in AUDIO_SUFFIXES or audio_bytes(raw):
            row['status']='OMITTED_SOURCE_AUDIO';records.append(row);continue
        target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True)
        if source.suffix=='.zip':
            changes=sanitize_zip(sanitizer,source,target);row['trace_entries_changed_or_omitted']=len(changes)
        else:target.write_bytes(sanitizer.clean_bytes(raw))
        clean=target.read_bytes();row.update(export_bytes=len(clean),export_sha256=digest(clean),status='IDENTICAL' if clean==raw else 'SANITIZED_COPY')
        records.append(row)
    manifest={'source_snapshot_policy':'Complete evaluaciones/ and logs/ snapshot plus current metadata/references/control; raw local originals unchanged.',
              'redaction_policy':'Credentials/session tokens/cookies/password fill values removed from COPIES; embedded original audio omitted from trace copies; screenshots, event timings, ASR/NLP results retained.',
              'records':records,'redaction_counts':dict(sanitizer.counts),'known_sensitive_values_count':len(sanitizer.secrets),
              'scope_note':'No original AAC/WAV corpus recordings, ASR weights, host .env/keyring, cache, or database added. Smoke0.1.21 artifacts are explicitly NOT a release.'}
    (destination/'PUBLICATION-MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'source_files':len(records),'status_counts':dict(Counter(r['status'] for r in records)),
                      'redaction_counts':dict(sanitizer.counts),'export_bytes':sum(r.get('export_bytes',0) for r in records)},indent=2))
    return sanitizer


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--corpus',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();export(args.corpus.resolve(),args.output.resolve())
