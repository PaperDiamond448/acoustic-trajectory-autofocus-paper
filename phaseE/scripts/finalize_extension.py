"""Export and verify completed B/C/D tables; leave MAT/H5 on the local machine."""
from pathlib import Path
import hashlib,json,os,shutil,sys,subprocess
for k in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):os.environ[k]='1'
ROOT=Path(__file__).resolve().parents[2];SCRIPTS=Path(__file__).parent
sys.path.insert(0,str(ROOT/'phaseE/_local_pydeps'))
import h5py
import numpy as np
import pandas as pd
from scipy.io import loadmat
import theory_metrics
REPO=ROOT/'GitHub整理_20261007/acoustic-trajectory-autofocus-paper'
NAMES={'B':'E2_frontend_ext','C':'E3_duration_ext','D':'E5_inject'}
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def export(out,stage,jobs,T):
    name=f'traj_export_E3_T{T}' if stage=='C' else ('traj_export_E2' if stage=='B' else 'traj_export_E5')
    stem=out/name;fronts={'B':['SUV_GRID','DHMM','ORACLE'],'C':['SUV','ORACLE'],'D':['VS','V0','MFT','SUV','SUV_GRID','DHMM']}[stage]
    nr=len(jobs);nt=len(fronts)*nr;ns=T*20;ix=[]
    tmp=stem.with_suffix('.incomplete.h5');final=stem.with_suffix('.h5')
    assert tmp.resolve().is_relative_to(out.resolve()) and final.resolve().is_relative_to(out.resolve())
    with h5py.File(tmp,'w') as h:
        h.attrs['fs_hz']=20.;h.attrs['duration_s']=T;h.attrs['row_index_origin']=0
        for key,n in [('truth',nr),('input',nt),('output',nt)]:h.create_dataset(key,(n,ns),dtype='f8',chunks=(1,ns),compression='gzip',compression_opts=1)
        n=0
        for j,r in enumerate(jobs.itertuples(index=False)):
            d=pd.read_csv(out/'records'/f'{r.tag}.csv')
            q=loadmat(out/'records'/f'{r.tag}.mat',simplify_cells=True)['S']
            details=q['details'];assert len(details)==len(fronts) and set(d.frontend)==set(fronts)
            truth=np.asarray(q['truth_g']).reshape(-1);assert len(truth)==ns
            h['truth'][j]=truth
            for k,fe in enumerate(fronts):
                detail=details[k];assert detail['frontend']==fe
                v=d[d.frontend==fe].iloc[0]
                assert v.input_hash==q['input_hash']
                gi=np.asarray(detail['input_g']).reshape(-1);go=np.asarray(detail['output_g']).reshape(-1)
                assert len(gi)==ns and len(go)==ns and np.isfinite(gi).all() and np.isfinite(go).all()
                h['input'][n]=gi;h['output'][n]=go
                row={'row':n,'truth_row':j,'scene':v.scene,'snr_db':v.snr_db,'record_id':v.record_id,
                    'seed':v.seed,'frontend':fe,'eta_in':v.eta_in,'eta_out':v.eta_out,'input_usable':v.input_usable,
                    'input_hash':v.input_hash,'duration_s':T}
                if stage=='D':row.update(band_id=v.band_id,window_id=v.window_id,target_kind=v.target_kind)
                ix.append(row);n+=1
            if (j+1)%100==0:print('EXPORT',stage,T,j+1,'/',nr,flush=True)
    tmp.replace(final)
    pd.DataFrame(ix).to_csv(str(stem)+'_index.csv',index=False)
    theory_metrics.main(str(stem))
    tm=pd.read_csv(str(stem)+'_theory_metrics.csv')
    di=float(tm.check_dev_in.max());do=float(tm.check_dev_out.max());assert di<1e-6 and do<1e-6
    status={'export_complete':True,'rows':nt,'truth_records':nr,'fs_hz':20,'duration_s':T,
            'max_eta_in_abs_diff':di,'max_eta_out_abs_diff':do,'passed':True,'h5_local_path':str(final),'h5_sha256':sha(final)}
    Path(str(stem)+'_python_check.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    return status
def bootstrap(data,stage,out):
    # Each cell is reduced to its paired eta-in/out mean before equal cell weighting.
    fronts=sorted(data.frontend.unique());durations=sorted(data.duration_s.unique())
    points=[];rng=np.random.default_rng(20261007);draw_records={};shared_draws={}
    for T in durations:
        dt=data[data.duration_s==T]
        groups=sorted(dt.band_id.unique()) if stage=='D' else sorted(dt.scene.unique())
        estimates=[];boots=[]
        for group in groups:
            x=dt[dt.band_id==group] if stage=='D' else dt[dt.scene==group]
            cluster='window_id' if stage=='D' else 'record_id'
            ids=sorted(x[cluster].unique());m=[]
            for key in ids:
                # D clusters carry both target kinds, all repeats/SNRs and all methods.
                y=x[x[cluster]==key];cells=['scene','snr_db','frontend']
                cell=y.groupby(cells)[['eta_in','eta_out']].mean()
                mean=cell.groupby('frontend').mean().reindex(fronts).to_numpy();assert np.isfinite(mean).all();m.append(mean)
            m=np.stack(m);draw_key=(str(group),tuple(ids))
            if draw_key not in shared_draws:shared_draws[draw_key]=rng.integers(0,len(ids),size=(2000,len(ids)))
            draw=shared_draws[draw_key]
            draw_records[f'T{T}_{group}']=draw
            estimates.append(m.mean(axis=0));boots.append(m[draw].mean(axis=1))
        point=np.stack(estimates).mean(axis=0);boot=np.stack(boots).mean(axis=0)
        for f,fe in enumerate(fronts):
            n=int((dt.frontend==fe).sum())
            for metric,p,v in [('eta_in',point[f,0],boot[:,f,0]),('eta_out',point[f,1],boot[:,f,1]),('gain',point[f,1]-point[f,0],boot[:,f,1]-boot[:,f,0])]:
                lo,hi=np.quantile(v,[.025,.975]);points.append({'duration_s':T,'frontend':fe,'metric':metric,'n':n,'estimate':p,'ci_lo':lo,'ci_hi':hi,
                  'bootstrap_replicates':2000,'bootstrap_seed':20261007,'cluster':'background window within band' if stage=='D' else 'record_id within scene','cell_weights':'equal scene/SNR; D also equal band/type'})
    np.savez_compressed(out/'BOOTSTRAP_DRAWS.npz',**draw_records)
    result=pd.DataFrame(points);result.to_csv(out/'PAIRED_SUMMARY.csv',index=False);return result
def main(stage):
    out=ROOT/'phaseE'/NAMES[stage];jobs=pd.read_csv(out/f'{stage}_jobs.csv');frames=[]
    for r in jobs.itertuples(index=False):
        p=out/'records'/f'{r.tag}.csv';assert p.exists(),f'Missing {p}'
        frames.append(pd.read_csv(p))
    data=pd.concat(frames,ignore_index=True);expected=len(jobs)*({'B':3,'C':2,'D':6}[stage]);assert len(data)==expected
    if stage in ('B','C'):
        old=pd.read_csv(ROOT/f'phaseD/{"X2_frontend/X2_records.csv" if stage=="B" else "X1_duration/X1_records.csv"}')
        keys=['scene','snr_db','record_id','duration_s'];original=old[keys+['input_hash']].drop_duplicates()
        got=data.merge(original,on=keys,validate='many_to_one',suffixes=('','_archived'));assert (got.input_hash==got.input_hash_archived).all()
    if stage=='B':
        reg=pd.concat([pd.read_csv(p) for p in (out/'regression').glob('B_reg*.csv')],ignore_index=True)
        assert len(reg)==140 and reg.passed.all();assert max(reg.eta_in_abs_diff.max(),reg.eta_out_abs_diff.max())<1e-9
        reg.to_csv(out/'REGRESSION_CHECKS.csv',index=False)
    data.to_csv(out/f'E{ {"B":2,"C":3,"D":5}[stage]}_records.csv',index=False)
    sums=bootstrap(data,stage,out)
    exports=[export(out,stage,jobs[jobs.duration_s==T],int(T)) for T in sorted(jobs.duration_s.unique())]
    pd.DataFrame(exports).to_csv(out/'LOCAL_H5_FILES_sha256.csv',index=False)
    protected=pd.read_csv(ROOT/'phaseE/E0_preflight/PROTECTED_FILES_before.csv')
    for r in protected.itertuples(index=False):assert sha(ROOT/r.path)==r.sha256,f'Frozen source changed: {r.path}'
    status={'task':stage,'complete':True,'input_records':len(jobs),'method_rows':expected,'eta_recomputation_passed':True,
        'protected_files_unchanged':len(protected),'hard_fail_rows':int(data.hard_fail.sum()),'budget_cap_rows':int(data.budget_cap.sum()),
        'input_hash_checks_passed':True if stage in ('B','C') else 'new injected inputs: paired hash checked within methods'}
    (out/'FINAL_STATUS.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    lines=[f'# {stage}：完成的新扩展结果','',f'状态：{len(jobs)} 个输入、{expected} 条方法输出全部完成。轨迹导出与独立 η 重算通过，154 个原冻结文件指纹未变。','',
      'B/C 是与既有 X2/X1 的同记录配对扩展；输入 MD5 逐条核对。ORACLE 为已知真值起点下的估计误差诊断，单列报告。D 使用18个筛选通过背景窗口，已知注入目标用于评价；背景筛选规则、门槛和测试窗口在注入前冻结。','',
      'η 为已知目标分量在 [5,T−5) s 的最大残余频率谱峰效率，搜索 ±2 Hz，FFT补零倍率8。观测 peak_in/out_db 为带内观测峰值，不等同于目标 η。input_usable 按去均值频率误差在 ±0.1 Hz 内的时间比例至少90%判断。','',
      '配对均值在场景/SNR组合等权汇总；B/C在场景内按record_id成簇重抽，D在频带内按背景窗口成簇，携带同簇全部SNR、目标类型、重复和前端。2000次，固定种子20261007，95%分位数区间。D先对窗内重复求均值，再对两频带/目标类型/SNR等权；同一航次背景的区间描述本批窗口的变动。','',
      f'硬失败 {status["hard_fail_rows"]} 行、最终轮预算触顶 {status["budget_cap_rows"]} 行，均保留；逐条退出码与预算使用在记录表。','',
      '| 时长/s | 前端 | 输入 η | 输出 η | 增量 [95%区间] |','|---:|---|---:|---:|---|']
    for (T,fe),x in sums.groupby(['duration_s','frontend']):
        v=x.set_index('metric');z=v.loc['gain'];lines.append(f'| {T} | {fe} | {v.loc["eta_in","estimate"]:.4f} | {v.loc["eta_out","estimate"]:.4f} | {z.estimate:.4f} [{z.ci_lo:.4f},{z.ci_hi:.4f}] |')
    lines+=['','逐条 CSV 列定义与原 X2 一致，D 增加 band_id、window_id、target_kind；行标识和种子可追溯到 jobs/config。轨迹 H5 从0开始编号，truth/input/output 为20Hz基带频率float64，评价窗口与理论脚本一致。MAT/H5留在本机，绝对路径与SHA-256见清单。CSV/MD/JSON/NPZ/脚本上传GitHub。',
      '', '汇总记录表包含每一个已运行的方法输出。逐输入的 records/*.csv、regression/*.csv 和 dhmm_dev/*.csv 是本机保存点，内容已汇入上述汇总表；这些小文件与 MAT/H5 一起留在本机，指纹仍列入清单。',
      '', 'D注入信号未经过真实传播信道，本实验量化真实背景下的表现。较弱未知运动线可能通过筛选，筛选灵敏度说明保留在屏蔽前的原README及筛选修订说明。']
    if (out/'README.md').exists():shutil.copy2(out/'README.md',out/'README_before_completion.md')
    (out/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    manifest=[]
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.suffix not in ('.log','.txt') and p.name!='SHA256_MANIFEST.csv':
            is_local_checkpoint=p.suffix=='.csv' and p.relative_to(out).parts[0] in ('records','regression','dhmm_dev')
            manifest.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'uploaded':p.suffix not in ('.mat','.h5') and not is_local_checkpoint})
    for name in ('phaseE_ext_one.m','phaseE_ext_batch.m','phaseE_inject_one.m','phaseE_inject_batch.m','estimate_dhmm.m','phaseE_dhmm_develop.m','finalize_extension.py'):
        p=SCRIPTS/name;manifest.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'uploaded':True})
    pd.DataFrame(manifest).to_csv(out/'SHA256_MANIFEST.csv',index=False)
    for m in manifest:
        if m['uploaded']:
            p=ROOT/m['path'];dest=REPO/m['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    shutil.copy2(out/'SHA256_MANIFEST.csv',REPO/out.relative_to(ROOT)/'SHA256_MANIFEST.csv')
    print(status,flush=True)
if __name__=='__main__':main(sys.argv[1])
