"""Validate all guided cases and publish the complete descriptive result."""
from pathlib import Path
import hashlib,json,shutil,sys
import numpy as np
import pandas as pd
from scipy.io import loadmat
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'phaseE/E4_guided_real'
REPO=ROOT/'GitHub整理_20261007/acoustic-trajectory-autofocus-paper'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    cases=[(52,600),(52,900),(52,2400),(61,2100),(100,600),(100,900),(100,1200),(100,1500),(100,1800),(103,900),(103,1200),(118,1500),(121,0),(133,1200),(136,900)]
    old=pd.read_csv(ROOT/'phaseD/X3_real/X3_cases.csv')
    frames=[];checks=[]
    for tone,start in cases:
        tag=f'f{tone}_s{start}_T300'
        d=pd.read_csv(OUT/'records'/f'{tag}.csv');assert len(d)==3 and set(d.method)=={'G_ADA','G_UNB','G94_ADA'}
        original=old[(old.tone_hz==tone)&(old.segment_start_s==start)&(old.method=='SMR')].iloc[0]
        assert (d.input_hash==original.input_hash).all()
        s=pd.read_csv(OUT/'spectra'/f'{tag}.csv');tr=pd.read_csv(OUT/'tracks'/f'{tag}.csv')
        assert len(tr)==6000 and np.isfinite(tr.to_numpy()).all()
        assert np.allclose(np.diff(tr.time_s),.05,atol=1e-9)
        z=(s.frequency_Hz-tone).abs()<=.01
        period=s.Periodogram.max();lp=s.LPS.max();ap=s.VS_FM.max()
        err=0
        for r in d.itertuples(index=False):
            v=s[r.method];peak=v.max();zpeak=v[z].max()
            for actual,want in [(r.peak_power,peak),(r.zero_peak_power,zpeak),
                (r.peak_relative_periodogram_db,10*np.log10(peak/period)),
                (r.gain_peak_vs_LPS_db,10*np.log10(peak/lp)),
                (r.gain_peak_vs_VS_FM_db,10*np.log10(peak/ap)),
                (r.gain_zero_peak_vs_LPS_db,10*np.log10(zpeak/s.LPS[z].max())),
                (r.gain_zero_peak_vs_VS_FM_db,10*np.log10(zpeak/s.VS_FM[z].max()))]:
                err=max(err,abs(actual-want))
        assert err<1e-9
        q=loadmat(OUT/'records'/f'{tag}.mat',simplify_cells=True)['S']
        assert q['baseline_metric_abs_diff']<1e-9
        checks.append({'tone_hz':tone,'segment_start_s':start,'methods':3,'input_hash_match':True,
            'max_spectrum_readback_difference':err,'baseline_metric_abs_diff':q['baseline_metric_abs_diff']})
        frames.append(d)
    data=pd.concat(frames,ignore_index=True);data.to_csv(OUT/'E4_records.csv',index=False)
    pd.DataFrame(checks).to_csv(OUT/'E4_READBACK_CHECKS.csv',index=False)
    summaries=[]
    for method,x in data.groupby('method'):
        for metric in ['gain_peak_vs_LPS_db','gain_peak_vs_VS_FM_db','gain_zero_peak_vs_LPS_db','gain_zero_peak_vs_VS_FM_db']:
            v=x[metric];summaries.append({'method':method,'metric':metric,'n':len(v),'mean_db':v.mean(),
                'median_db':v.median(),'min_db':v.min(),'max_db':v.max(),
                'positive':int((v>1e-9).sum()),'negative':int((v<-1e-9).sum()),'unchanged':int((abs(v)<=1e-9).sum())})
    summ=pd.DataFrame(summaries);summ.to_csv(OUT/'E4_summary.csv',index=False)
    before=pd.read_csv(ROOT/'phaseE/E0_preflight/PROTECTED_FILES_before.csv')
    for r in before.itertuples(index=False):assert sha(ROOT/r.path)==r.sha256
    status={'task':'E','complete':True,'cases':15,'method_rows':45,'input_hashes_match':True,
        'all_readback_checks_passed':True,'protected_files_unchanged':len(before),
        'hard_fail_rows':int(data.hard_fail.sum()),'budget_cap_rows':int(data.budget_cap.sum()),
        'interpretation':'Descriptive cases from one voyage; all prespecified cases retained.'}
    (OUT/'FINAL_STATUS.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    lines=['# E：实测强线引导锚定','', '状态：15 个弱线案例、3 种方法共 45 行全部完成。输入 MD5 与已有 X3 相同，谱表独立读回核对通过，冻结文件指纹不变。',
        '', '引导中位数来自同一时段的六根强线输出频率除以其名义频率，再乘弱线名义频率；94 Hz 引导单列。全部从零系数起步。G_ADA/G94_ADA 调用冻结局部扩张模块；G_UNB 取消系数幅度界，保留检查点频带约束。',
        '', '优化 [5,295) s，所有谱使用完整 300 s。完整带为残余 ±1.5 Hz，零频附近指标为 ±0.01 Hz 内最大值；这两个指标比较的频率范围不同。dB 的共同基准为同案例未补偿周期图在完整带内的最大值。全部案例保留，没有按引导收益筛选。',
        '', '## 描述性汇总','', '| 方法 | 指标 | n | 中位/dB | 范围/dB | 提高/降低/不变 |','|---|---|---:|---:|---|---|']
    for r in summ.itertuples(index=False):lines.append(f'| {r.method} | {r.metric} | {r.n} | {r.median_db:.4f} | [{r.min_db:.4f}, {r.max_db:.4f}] | {r.positive}/{r.negative}/{r.unchanged} |')
    lines+=['', '案例来自同一航次；以上描述各案例的结果，不作独立海试重复的显著性推断。完整带最大峰可能位于目标预测位置之外，需与零频附近峰值、逐案谱和轨迹一起阅读。',
        '', f'求解硬失败 {status["hard_fail_rows"]} 行，最终轮预算触顶 {status["budget_cap_rows"]} 行，均保留并逐条报告；每行迭代数、目标调用数和退出码在记录表。',
        '', '## 文件与列','', '`E4_records.csv`：tone/segment/duration 标识案例；input_hash 为原始复基带 MD5；method 标识三种引导操作；peak_* 为完整带最大峰；zero_peak_* 为 ±0.01 Hz 最大峰；gain_* 为同案例与 LPS/原模块输出的配对 dB 差；prominence/width 与冻结 X3 定义相同；runtime/trigger/J/exitflags 为求解记录。',
        '', '`anchors/` 为两种绝对频率引导；`tracks/` 为绝对频率输出；`spectra/` 为频率及功率，含同一输入的 Periodogram、LPS、原 VS_FM 和三种新方法，可独立核算。`records/*.mat` 留在本机，含完整求解记录，路径为 `D:\\论文集\\phaseE\\E4_guided_real\\records\\`，其 SHA-256 在清单中。',
        '', '新驱动没有调用会覆盖 X3 输出目录的 `phaseX3_one`；只读取其输入/轨迹，并调用冻结估计与评价函数。旧的 100 Hz 发射线归属问题不因本任务更换标签或判定；新结果提供引导参照下的谱和轨迹供进一步分析。']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    manifests=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.suffix!='.log' and p.name!='SHA256_MANIFEST.csv':
            manifests.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'uploaded':p.suffix!='.mat'})
    for name in ('phaseE_guided_one.m','phaseE_guided_batch.m','finalize_guided_E.py'):
        p=ROOT/'phaseE/scripts'/name;manifests.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'uploaded':True})
    pd.DataFrame(manifests).to_csv(OUT/'SHA256_MANIFEST.csv',index=False)
    for m in manifests:
        if not m['uploaded']:continue
        p=ROOT/m['path'];dest=REPO/m['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    shutil.copy2(OUT/'SHA256_MANIFEST.csv',REPO/'phaseE/E4_guided_real/SHA256_MANIFEST.csv')
    print(summ.to_string(index=False));print(status,flush=True)

if __name__=='__main__':main()
