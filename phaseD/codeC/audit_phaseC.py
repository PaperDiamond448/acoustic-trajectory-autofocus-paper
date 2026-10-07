"""Independent checks of primary arithmetic, bootstrap, immutable inputs and completeness."""
from pathlib import Path
import csv, hashlib, json
import numpy as np
import pandas as pd

ROOT=Path(r'D:\论文集\phaseD');OUT=ROOT/'C_confirm'
FM='ADA_local_c04_t30_A'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def audit():
    hashcounts={}
    for name in ['BASELINE_MANIFEST_sha256.csv','code/SOURCE_MANIFEST_sha256.csv','codeC/SOURCE_MANIFEST_C_sha256.csv','codeC/POSTPROCESS_MANIFEST_sha256.csv','C_confirm/PROTECTED_STOP1_sha256.csv']:
        rows=list(csv.DictReader((ROOT/name).open(encoding='utf-8-sig')))
        for r in rows:
            p=Path(r.get('source_file',r.get('path','')))
            assert sha(p)==r['sha256'],str(p)
        hashcounts[name]=len(rows)
    data=pd.read_csv(OUT/'C_records.csv')
    assert len(data)==14000 and not data.duplicated(['scene','snr_db','record_id','method']).any()
    eta=data.pivot(index=['scene','snr_db','record_id'],columns='method',values='eta')
    assert len(eta)==2800 and not eta.isna().any().any()
    assert len(data[['scene','record_id','seed']].drop_duplicates())==400
    assert len(data[['scene','snr_db','record_id','input_hash']].drop_duplicates())==2800
    old=pd.read_csv(ROOT/'D_dev/fixed_records.csv')
    assert not set(data.seed).intersection(set(old.seed))
    e4a=pd.read_csv(ROOT.parent/'phaseC/E4a_track_only_pilot_20260925/track_only_metrics.csv',usecols=['seed'])
    assert not set(data.seed).intersection(set(e4a.seed))
    # Independently form paired harm indicators from raw eta, never from precomputed flags.
    contrasts=[eta[FM]-eta.F02, eta[FM]-eta.UNB,
        (eta[FM]<eta.F02-.01).astype(int)-(eta.UNB<eta.F02-.01).astype(int)]
    rng=np.random.default_rng(20261052)
    cluster=[rng.integers(0,200,size=(2000,200)) for _ in range(2)]
    cell_draws=[rng.integers(0,200,size=(2000,200)) for _ in range(14)]
    draws=np.load(OUT/'bootstrap_draws.npz')
    assert np.array_equal(draws['cluster'],cluster) and np.array_equal(draws['cells'],cell_draws)
    decision=json.loads((OUT/'CONFIRM_DECISION.json').read_text(encoding='utf8'))
    checks=0
    for key,x in zip(['P1','P2','P3'],contrasts):
        values=[];boot=np.zeros(2000)
        for si,scene in enumerate(['S0','S2']):
            # Compute each seed's equally weighted SNR contrast independently.
            matrix=x.loc[scene].unstack('snr_db').sort_index().to_numpy()
            seedmeans=matrix.mean(axis=1)
            values.extend(seedmeans)
            for b in range(2000):boot[b]+=seedmeans[cluster[si][b]].mean()/2
        lo,hi=np.quantile(boot,[.025,.975]);actual=decision['endpoints'][key]
        np.testing.assert_allclose([np.mean(values),lo,hi],[actual['mean'],actual['lo'],actual['hi']],rtol=0,atol=2e-15)
        expected=lo>0 if key=='P1' else lo>-.005 if key=='P2' else hi<0
        assert actual['passed']==bool(expected);checks+=4
    celltable=pd.read_csv(OUT/'C_cell_statistics.csv');bad=[]
    for i,(scene,snr) in enumerate(pd.MultiIndex.from_product([['S0','S2'],range(-20,-13)])):
        x=(eta[FM]-eta.F02).loc[(scene,snr)].to_numpy()
        boot=np.array([x[draw].mean() for draw in cell_draws[i]])
        lo,hi=np.quantile(boot,[.025,.975])
        row=celltable[celltable.scene.eq(scene)&celltable.snr_db.eq(snr)&celltable.method.eq(FM)&celltable.metric.eq('gain_eta_vs_F02')].iloc[0]
        np.testing.assert_allclose([x.mean(),lo,hi],[row['mean'],row.lo,row.hi],rtol=0,atol=2e-15)
        if hi<-.005:bad.append((scene,int(snr)))
        checks+=3
    assert decision['endpoints']['S1']['passed']==(len(bad)==0)
    p1,p2,p3,s1=[decision['endpoints'][k]['passed'] for k in ['P1','P2','P3','S1']]
    branch='C-A3' if not p1 else 'C-A4' if not s1 else 'C-A1' if p2 and p3 else 'C-A2' if p3 else '介于两者之间'
    assert branch==decision['branch']
    saved=json.loads((OUT/'SAVED_OUTPUTS_AUDIT.json').read_text(encoding='utf8'));assert saved['status']=='PASS' and saved['records']==2800
    checks+=3
    report=dict(status='PASS',records=2800,method_rows=14000,unique_seed_clusters=400,primary_arithmetic_checks=checks,protected_hashes=hashcounts,development_seed_overlap=0,E4a_seed_overlap=0,branch=branch,scope='Independent raw-record primary contrasts, seed cluster bootstrap and cell S1 calculation; all historical protected files unchanged; native output audit also passed')
    (OUT/'INDEPENDENT_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':audit()
