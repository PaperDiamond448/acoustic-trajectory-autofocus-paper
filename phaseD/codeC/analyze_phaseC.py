from pathlib import Path
import json, hashlib, platform
import numpy as np
import pandas as pd

ROOT = Path(r'D:\论文集\phaseD')
OUT = ROOT / 'C_confirm'
FM = 'ADA_local_c04_t30_A'
METHODS = ['SMR', 'F02', 'F04', 'UNB', FM]
KEYS = ['scene', 'snr_db', 'record_id']
SEED = 20261052
B = 2000

def describe(x, draws):
    x = np.asarray(x, dtype=float)
    finite = np.isfinite(x)
    if not finite.any():
        return dict(mean=None, lo=None, hi=None, median=None, q25=None, q75=None, positive_fraction=None, valid_n=0)
    # Only mathematically undefined secondary metrics (e.g. 3-dB width) may be NaN.
    samples = x[draws]
    counts = np.isfinite(samples).sum(axis=1)
    boot = np.divide(np.nansum(samples, axis=1), counts, out=np.full(len(draws), np.nan), where=counts > 0)
    lo, hi = np.nanquantile(boot, [.025, .975])
    q25, median, q75 = np.quantile(x[finite], [.25, .5, .75])
    return dict(mean=float(x[finite].mean()), lo=float(lo), hi=float(hi), median=float(median), q25=float(q25), q75=float(q75), positive_fraction=float((x[finite] > 0).mean()), valid_n=int(finite.sum()))

def analyze():
    d = pd.read_csv(OUT / 'C_records.csv')
    assert len(d) == 14000 and set(d.method) == set(METHODS)
    assert not d.duplicated(KEYS + ['method']).any()
    expected = pd.MultiIndex.from_product([['S0', 'S2'], range(-20, -13), range(1, 201)], names=KEYS)
    frames = {}
    for m in METHODS:
        q = d[d.method.eq(m)].set_index(KEYS).sort_index()
        assert q.index.equals(expected)
        assert np.isfinite(q.eta).all() and q.eta.between(0, 1).all()
        frames[m] = q
    f02, smr, unb, fm = (frames[m] for m in ['F02', 'SMR', 'UNB', FM])
    for m, q in frames.items():
        assert q.seed.equals(f02.seed) and q.input_hash.equals(f02.input_hash)
        assert (q.seed.to_numpy() == 20260915 + 52_000_000 + np.where(q.index.get_level_values('scene') == 'S0', 10000, 30000) + q.index.get_level_values('record_id').to_numpy()).all()
        assert (q.Delta_s == 10).all() and (q.P == 31).all()
    for col in ['triggered', 'hard_fail', 'fallback', 'budget_cap']:
        assert set(d[col].unique()).issubset({0, 1})
    assert np.array_equal(fm.loc[fm.triggered.eq(0), 'eta'], f02.loc[fm.triggered.eq(0), 'eta'])
    assert (fm.J >= f02.J - 1e-12).all()
    rng = np.random.default_rng(SEED)
    cluster = np.stack([rng.integers(0, 200, size=(B, 200)) for _ in range(2)])
    cell_draws = np.stack([rng.integers(0, 200, size=(B, 200)) for _ in range(14)])
    np.savez_compressed(OUT / 'bootstrap_draws.npz', cluster=cluster, cells=cell_draws)

    def pooled(values, scope='ALL'):
        # Sorted row order is scene, SNR, record_id. Each sampled seed carries all SNRs.
        a = np.asarray(values, dtype=float).reshape(2, 7, 200)
        scenes = [0, 1] if scope == 'ALL' else [0 if scope == 'S0' else 1]
        mean = np.nanmean(a[scenes], axis=2).mean()
        boot = np.stack([np.nanmean(a[s][:, cluster[s]], axis=2).mean(axis=0) for s in scenes]).mean(axis=0)
        lo, hi = np.quantile(boot, [.025, .975])
        return dict(mean=float(mean), lo=float(lo), hi=float(hi))

    harms = {m: q.eta.lt(f02.eta - .01).astype(float).to_numpy() for m, q in frames.items()}
    p1 = pooled(fm.eta - f02.eta)
    p2 = pooled(fm.eta - unb.eta)
    p3 = pooled(harms[FM] - harms['UNB'])
    p1.update(rule='lower > 0', passed=p1['lo'] > 0)
    p2.update(rule='lower > -0.005', passed=p2['lo'] > -.005)
    p3.update(rule='upper < 0', passed=p3['hi'] < 0)
    cellrows = []
    for i, (scene, snr) in enumerate(pd.MultiIndex.from_product([['S0', 'S2'], range(-20, -13)])):
        for m in METHODS:
            q = frames[m].loc[(scene, snr)]
            a = f02.loc[(scene, snr)]; s = smr.loc[(scene, snr)]; u = unb.loc[(scene, snr)]
            for metric, x in [
                ('eta', q.eta), ('gain_eta_vs_F02', q.eta-a.eta),
                ('gain_eta_vs_SMR', q.eta-s.eta), ('gain_eta_vs_UNB', q.eta-u.eta),
                ('gain_peak_vs_SMR_db', q.peak_db-s.peak_db), ('gain_peak_vs_F02_db', q.peak_db-a.peak_db),
                ('harm_vs_F02', q.eta.lt(a.eta-.01).astype(float)),
                ('harm_vs_SMR', q.eta.lt(s.eta-.01).astype(float)),
            ]:
                cellrows.append(dict(scene=scene, snr_db=snr, method=m, metric=metric, **describe(x, cell_draws[i])))
    cells = pd.DataFrame(cellrows)
    cells.to_csv(OUT / 'C_cell_statistics.csv', index=False)
    s1cells = cells[cells.method.eq(FM) & cells.metric.eq('gain_eta_vs_F02')].copy()
    s1cells['systematic_deterioration'] = s1cells.hi.lt(-.005)
    s1cells.to_csv(OUT / 'S1_cells.csv', index=False)
    s1 = dict(rule='No cell with upper < -0.005', passed=not bool(s1cells.systematic_deterioration.any()), deteriorated_cells=s1cells[s1cells.systematic_deterioration][['scene', 'snr_db', 'mean', 'lo', 'hi']].to_dict('records'))
    if not p1['passed']:
        branch, primary = 'C-A3', 'F02'
    elif not s1['passed']:
        branch, primary = 'C-A4', 'F02'
    elif p3['passed'] and p2['passed']:
        branch, primary = 'C-A1', FM
    elif p3['passed'] and not p2['passed']:
        branch, primary = 'C-A2', FM
    else:
        branch, primary = '介于两者之间', None
    summary = []
    for m, q in frames.items():
        vals = {
            'eta': q.eta, 'gain_eta_vs_F02': q.eta-f02.eta,
            'gain_eta_vs_SMR': q.eta-smr.eta, 'gain_eta_vs_VIT': q.eta-q.eta_VIT,
            'gain_eta_vs_UNB': q.eta-unb.eta, 'harm_vs_F02': harms[m],
            'harm_vs_SMR': q.eta.lt(smr.eta-.01).astype(float),
            'peak_db': q.peak_db, 'gain_peak_vs_SMR_db': q.peak_db-smr.peak_db,
            'gain_peak_vs_F02_db': q.peak_db-f02.peak_db,
            'prominence_db': q.prominence_db, 'width_3db_hz': q.width_3db_hz,
            'track_rmse_hz': q.track_rmse_hz, 'max_error_hz': q.max_error_hz,
            'longest_out_0p02_s': q.longest_out_0p02_s,
            'trigger_fraction': q.triggered, 'expansion_rounds': q.expansion_rounds,
        }
        for scope in ['ALL', 'S0', 'S2']:
            sel = np.ones(2800, dtype=bool) if scope=='ALL' else q.index.get_level_values('scene')==scope
            for metric, x in vals.items():
                raw = np.asarray(x, dtype=float)[sel]
                finite = raw[np.isfinite(raw)]
                qq = np.quantile(finite, [.25, .5, .75]) if len(finite) else [np.nan]*3
                summary.append(dict(scope=scope, method=m, metric=metric, **pooled(x, scope), median=float(qq[1]), q25=float(qq[0]), q75=float(qq[2]), positive_fraction=float((finite>0).mean()) if len(finite) else np.nan, valid_n=len(finite)))
    pd.DataFrame(summary).to_csv(OUT / 'C_summary.csv', index=False)
    paired = fm[['eta', 'peak_db', 'triggered', 'expansion_rounds']].copy()
    paired['delta_eta_vs_F02'] = fm.eta-f02.eta
    paired['delta_eta_vs_UNB'] = fm.eta-unb.eta
    paired['delta_eta_vs_SMR'] = fm.eta-smr.eta
    paired['harm_FM'] = harms[FM]; paired['harm_UNB'] = harms['UNB']
    paired['paired_harm_difference'] = harms[FM]-harms['UNB']
    paired.to_csv(OUT / 'C_paired_endpoints.csv')
    timing = []
    for scope in ['ALL', 'S0', 'S2']:
        for m, q in frames.items():
            z = q if scope == 'ALL' else q.loc[scope]
            for metric in ['runtime_s', 't_frontend_s', 't_vit_s', 't_family_s', 't_smr_s']:
                timing.append(dict(scope=scope, method=m, component=metric, median=float(z[metric].median()), p90=float(z[metric].quantile(.9)), n=len(z)))
    pd.DataFrame(timing).to_csv(OUT / 'C_runtime.csv', index=False)
    decision = dict(protocol='ASL-D-20261003', phase_id=52, records=2800, rows=14000, frozen_method=FM, endpoints=dict(P1=p1,P2=p2,P3=p3,S1=s1), branch=branch, primary_method=primary, by_scene={s:{'FM_minus_F02':pooled(fm.eta-f02.eta,s),'FM_minus_UNB':pooled(fm.eta-unb.eta,s),'H_FM_minus_H_UNB':pooled(harms[FM]-harms['UNB'],s)} for s in ['S0','S2']}, bootstrap=dict(seed=SEED, replicates=B, generator='numpy.default_rng PCG64', sampling='Two scene-stratified 2000x200 seed draw arrays generated sequentially, carrying all seven SNRs. Then 14 cell 2000x200 paired record draw arrays, scene then SNR order. Arrays reused for all paired metrics.', numpy=np.__version__, pandas=pd.__version__, python=platform.python_version()), diagnostics=dict(hard_fail_counts=d.groupby('method').hard_fail.sum().astype(int).to_dict(), budget_cap_counts=d.groupby('method').budget_cap.sum().astype(int).to_dict(), expansion_count=int(fm.triggered.sum()), negative_eta_gain_vs_F02_count=int(fm.eta.lt(f02.eta).sum())), status='statistics_complete_pending_QA_stop2', confirmation_csv_sha256=hashlib.sha256((OUT/'C_records.csv').read_bytes()).hexdigest(), X_started=False)
    (OUT/'CONFIRM_DECISION.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(branch=branch,endpoints=decision['endpoints']),ensure_ascii=False,indent=2))

if __name__ == '__main__':
    analyze()
