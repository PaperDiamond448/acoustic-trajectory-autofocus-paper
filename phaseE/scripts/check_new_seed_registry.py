"""Compare Phase E's new seed ranges with archived seed-bearing CSV files."""
from pathlib import Path
import json
import hashlib
import pandas as pd

root=Path(__file__).resolve().parents[2]
existing=set();sources=[]
for directory in ('phaseA','phaseC','phaseD'):
    for path in sorted((root/directory).rglob('*.csv')):
        header=pd.read_csv(path,nrows=0)
        if 'seed' not in header.columns:
            continue
        values=pd.to_numeric(pd.read_csv(path,usecols=['seed'])['seed'],errors='coerce').dropna()
        assert (values%1==0).all(),str(path)
        numbers=set(values.astype('int64').tolist());existing.update(numbers)
        sources.append({'path':path.relative_to(root).as_posix(),'unique_seeds':len(numbers),
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
development=pd.read_csv(root/'phaseE/E2_frontend_ext/DHMM_development_records.csv')
dev=set(development.seed.astype('int64'))
injection=pd.read_csv(root/'phaseE/E5_inject/D_jobs.csv')
inj=set(injection.seed.astype('int64'))
assert not (dev & existing),sorted(dev & existing)
assert not (inj & existing),sorted(inj & existing)
assert not (inj & dev),sorted(inj & dev)
assert len(dev)==40 and len(inj)==720
assert injection.groupby('seed').size().eq(7).all()
out=root/'phaseE/E0_preflight'
pd.DataFrame(sources).to_csv(out/'SEED_REGISTRY_SOURCES.csv',index=False)
status={'archived_seed_csv_files':len(sources),'archived_unique_seeds':len(existing),
        'dhmm_development_unique_seeds':len(dev),'dhmm_development_inputs':120,
        'injection_unique_seeds':len(inj),'injection_inputs':5040,
        'development_archive_overlap':0,'injection_archive_overlap':0,
        'development_injection_overlap':0,'injection_snr_pairing':7,'passed':True,
        'scope':'All seed-bearing CSVs under phaseA, phaseC and phaseD; original files read only.'}
(out/'NEW_SEED_REGISTRY_CHECK.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
print(json.dumps(status),flush=True)
