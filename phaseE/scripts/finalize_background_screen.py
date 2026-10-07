"""Read back saved background screening; no injection or rule changes."""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
import pandas as pd
from scipy.io import loadmat
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'phaseE/E5_inject';REPO=ROOT/'GitHub整理_20261007/acoustic-trajectory-autofocus-paper'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def main():
    d=pd.read_csv(OUT/'BACKGROUND_SCREEN.csv');assert len(d)==20
    checks=[]
    for r in d.itertuples(index=False):
        q=loadmat(OUT/'background'/f'b{r.band_id}_w{r.window_id}.mat',simplify_cells=True)
        f=q['freq'];power=q['power'];db=10*np.log10(np.maximum(power,np.finfo(float).tiny))
        score=float(db[abs(f)<=2.5].max()-np.median(db[(abs(f)>=3)&(abs(f)<=8)]))
        assert abs(score-r.screen_score_db)<1e-9 and bool(r.retained)==(score<8)
        z=q['normalized'];p=abs(np.fft.fft(z))**2/len(z);nu=np.fft.fftfreq(len(z),1/20)
        bandmean=float(p[abs(nu)<=2].mean());assert abs(bandmean-1)<1e-10
        checks.append({'band_id':r.band_id,'window_id':r.window_id,'score_db_recomputed':score,
            'score_abs_diff':abs(score-r.screen_score_db),'normalized_band_mean':bandmean,'passed':True})
    pd.DataFrame(checks).to_csv(OUT/'BACKGROUND_SCREEN_READBACK.csv',index=False)
    lock=json.loads((ROOT/'phaseE/PREREGISTRATION_PhaseE_20261007.sha256.json').read_text())
    status={'task':'D','screen_complete':True,'screened_windows':20,'retained_windows':int(d.retained.sum()),
        'injection_started':False,'complete':False,'status':'stopped_no_eligible_background' if not d.retained.any() else 'screen_frozen',
        'preregistration_sha256':lock['sha256'],'readback_passed':True,
        'implementation_note':'All 20 MAT/CSV outputs saved; MATLAB final status-writing cell-indexing error fixed in new driver. Freeze metadata reconstructed from independently checked saved outputs; no extraction rerun.'}
    (OUT/'BACKGROUND_SCREEN_FREEZE.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    config={'task':'D','stage':'background_screen','centers_hz':[263.5,315],'windows':20,'duration_s':300,
        'channel':9,'lofar_window_s':10,'lofar_hop_s':1,'lofar_fft_points':200,'center_band_hz':[-2.5,2.5],
        'annulus_abs_hz':[3,8],'score':'maximum dB across all center-band frames/bins minus median dB across all annulus frames/bins',
        'retain_if':'score < 8 dB','preregistration_sha256':lock['sha256']}
    (OUT/'run_config.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    (OUT/'README.md').write_text('\n'.join(['# D：真实背景注入的运行前筛选','',
        '状态：完成 20 个背景窗口的提取和筛选；按写定规则 0/20 通过。尚未注入任何目标，也没有运行注入方法。',
        '',f'中心 263.5/315 Hz，通道 9，每带 10 个不重叠 300 s 窗。筛选量范围 {d.screen_score_db.min():.4f}–{d.screen_score_db.max():.4f} dB，均超过严格 <8 dB 的保留条件。',
        '', '筛选量按任务书的 LOFAR 最大值直接实现：200 点对称 Hann（10 s）、20 点帧移（1 s），中心 ±2.5 Hz 的所有时频点取最大 dB，环带 3≤|f|≤8 Hz 的所有时频点取 dB 中位数。此操作包含单帧随机峰值，不能把拒绝窗口直接解释为存在持续线谱。规则没有改动；需要核定筛选量的时间汇总方式或给出新规则后，任务 D 才能继续。',
        '', 'CSV 与保存 MAT 的独立谱计算逐条一致（<1e−9）。所有归一化背景在 |f|≤2 Hz 的 |FFT|²/N 均值为 1（误差 <1e−10）。FFT 提取时使用 320 s 总段长，首窗保护 (0,20) s，末窗 (20,0) s，内部各 10 s，裁回原 300 s 窗。',
        '', 'MATLAB 在全部 20 组结果保存后，写最终状态文件时出现新驱动对 cell 数组点索引的错误。已修正新驱动；本次从保存的 MAT/CSV 重算筛选量并生成状态文件，不重提取背景、不修改任何保存的功率、输入或判定。',
        '', '`BACKGROUND_SCREEN.csv` 每行一个频带/窗口，包含筛选量、中心峰/环带中位数、峰位与帧起点、通过标志、保护时长、归一化系数和 MD5。`BACKGROUND_SCREEN_READBACK.csv` 给出独立读回核对；`BACKGROUND_SCREEN_FREEZE.json` 冻结 0 个通过窗口的事实；大文件在本机 `D:\\论文集\\phaseE\\E5_inject\\background\\`，指纹见清单。',
        '', '任务 D 停在筛选，原 Phase D 仿真与导出不受影响。'])+'\n',encoding='utf-8')
    manifest=[]
    for p in sorted(OUT.rglob('*')):
        if p.is_file() and p.suffix!='.log' and p.name!='SHA256_MANIFEST.csv':manifest.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'uploaded':p.suffix!='.mat'})
    for name in ('phaseE_screen_background.m','finalize_background_screen.py'):
        p=ROOT/'phaseE/scripts'/name;manifest.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p),'uploaded':True})
    pd.DataFrame(manifest).to_csv(OUT/'SHA256_MANIFEST.csv',index=False)
    for m in manifest:
        if m['uploaded']:
            p=ROOT/m['path'];dest=REPO/m['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    shutil.copy2(OUT/'SHA256_MANIFEST.csv',REPO/'phaseE/E5_inject/SHA256_MANIFEST.csv')
    print(status,flush=True)
if __name__=='__main__':main()
