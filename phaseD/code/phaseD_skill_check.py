from pathlib import Path
import hashlib, json, urllib.request, zipfile, io

ROOT = Path(r'D:\论文集\phaseD')
AUDIT = ROOT / 'skill_audit'
AUDIT.mkdir(parents=True, exist_ok=True)
api = 'https://api.github.com/repos/Yuan1z0825/nature-skills/commits/main'
req = urllib.request.Request(api, headers={'User-Agent':'PhaseD-skill-audit'})
meta = json.load(urllib.request.urlopen(req, timeout=30))
sha = meta['sha']
url = f'https://codeload.github.com/Yuan1z0825/nature-skills/zip/{sha}'
data = urllib.request.urlopen(url, timeout=60).read()
(AUDIT/'upstream.zip').write_bytes(data)
z = zipfile.ZipFile(io.BytesIO(data))
prefix = z.namelist()[0]
installed = Path(r'C:\Users\Lenovo\.codex\skills')
changes=[]
for entry in z.infolist():
    rel = entry.filename[len(prefix):]
    if not rel.startswith('skills/nature-') or entry.is_dir():
        continue
    skill_rel=rel[len('skills/'):]
    dest=installed/skill_rel
    if not (installed/skill_rel.split('/')[0]).exists():
        continue
    upstream=z.read(entry)
    old=dest.read_bytes() if dest.exists() else None
    # Ignore platform-only newline conversion in text sources.
    same=old is not None and old.replace(b'\r\n',b'\n')==upstream.replace(b'\r\n',b'\n')
    stage=AUDIT/'upstream'/skill_rel
    stage.parent.mkdir(parents=True,exist_ok=True)
    stage.write_bytes(upstream)
    if not same:
        changes.append({'file':skill_rel,'old_sha256':hashlib.sha256(old).hexdigest() if old else None,'new_sha256':hashlib.sha256(upstream).hexdigest()})
report={'upstream':'https://github.com/Yuan1z0825/nature-skills','commit':sha,'commit_date':meta['commit']['committer']['date'],'changes':changes}
(AUDIT/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=True,indent=2))
