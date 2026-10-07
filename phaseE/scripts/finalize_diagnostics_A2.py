"""Describe A2 quantities and independently check the phase area of candidate bursts."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'phaseE/_local_pydeps'))
import h5py
OUT=ROOT/'phaseE/E1_trajexport'
REPO=ROOT/'GitHub整理_20261007/acoustic-trajectory-autofocus-paper'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    config=json.loads((OUT/'run_config_A2.json').read_text(encoding='utf-8'))
    sums=[];subset=[];regions=[];checks=[]
    for stem in config['datasets']:
        checks.append(json.loads((OUT/(stem+'_diagA2_check.json')).read_text()))
        d=pd.read_csv(OUT/(stem+'_diagA2.csv'))
        tm=pd.read_csv(OUT/(stem+'_theory_metrics.csv'))
        d=d.merge(tm[['row','in_sigma2','in_low_share','in_p_gt60s','in_rmse_hz','in_rmse_demeaned_hz','pred_recoverable']],on='row',validate='one_to_one')
        d['regime']=np.select([d.in_sigma2<.5,d.in_sigma2<5,d.input_usable.astype(bool)],['A','B','C'],default='D')
        for fe,x in d.groupby('frontend'):
            s=pd.read_csv(OUT/(stem+'_diagA2_summary.csv')).set_index('frontend').loc[fe].to_dict()
            s.update(dataset=stem,frontend=fe);sums.append(s)
            for label,part in [('all',x),('sigma2_lt5',x[x.in_sigma2<5]),('S0_sigma2_lt0p5',x[(x.scene=='S0')&(x.in_sigma2<.5)])]:
                subset.append({'dataset':stem,'frontend':fe,'subset':label,'n':len(part),
                    'eta_in_mean':part.eta_in.mean(),'gain_mean':part.gain.mean(),
                    'rmse_demean_hz_median':part.in_rmse_demeaned_hz.median(),
                    'slow_phase_variance_median':part.in_p_gt60s.median(),
                    'rho_old_vs_gain':part.pred_recoverable.corr(part.gain,method='spearman'),
                    'rho_clean_vs_gain':part.ceiling_gain_m1.corr(part.gain,method='spearman')})
            for reg,p in x.groupby('regime'):
                regions.append({'dataset':stem,'frontend':fe,'regime':reg,'n':len(p),'eta_in':p.eta_in.mean(),
                    'eta_out':p.eta_out.mean(),'gain':p.gain.mean(),'eta_clean_m1':p.eta_clean_m1.mean(),
                    'eta_clean_m2':p.eta_clean_m2.mean(),'candidate_slip_rows':int((p.n_slip_runs>0).sum()),
                    'candidate_slip_runs_total':int(p.n_slip_runs.sum())})
    pd.DataFrame(sums).to_csv(OUT/'DIAGNOSTICS_A2_OVERVIEW.csv',index=False)
    pd.DataFrame(subset).to_csv(OUT/'DIAGNOSTICS_A2_SUBSETS.csv',index=False)
    pd.DataFrame(regions).to_csv(OUT/'DIAGNOSTICS_A2_REGIMES.csv',index=False)
    # A candidate run does not by itself establish an integer-cycle readout error.
    # Report its signed area, without promoting a numerical threshold to a mechanism test.
    ix=pd.read_csv(OUT/'traj_export_X2_index.csv');tm=pd.read_csv(OUT/'traj_export_X2_theory_metrics.csv')
    x=ix[ix.frontend=='SUV'].merge(tm[['row','in_sigma2']],on='row',validate='one_to_one')
    events=[]
    with h5py.File(OUT/'traj_export_X2.h5','r') as h:
        for r in x.itertuples(index=False):
            gt=h['truth'][r.truth_row];gi=h['input'][r.row]
            t=np.arange(len(gt))/20;use=(t>=5)&(t<295)
            e=(gt-gi)[use];e-=np.median(e);te=t[use]
            mask=np.abs(e)>.0625
            transitions=np.diff(np.r_[False,mask,False].astype(int));starts=np.flatnonzero(transitions==1);ends=np.flatnonzero(transitions==-1)
            count=0
            for a,b in zip(starts,ends):
                duration=(b-a)/20
                if not 4<=duration<=12:continue
                count+=1
                # Rectangle area follows the discrete sample-count run duration; also report trapezoids.
                cycles=float(e[a:b].sum()/20)
                a_ext=max(0,a-80);b_ext=min(len(e),b+80)
                cycles_ext=float(e[a_ext:b_ext].sum()/20)
                events.append({'row':r.row,'scene':r.scene,'snr_db':r.snr_db,'record_id':r.record_id,
                    'seed':r.seed,'in_sigma2':r.in_sigma2,'event_index':count,'start_s':te[a],
                    'end_s_exclusive':te[b-1]+.05,'duration_s':duration,'signed_phase_cycles_rectangle':cycles,
                    'signed_phase_cycles_trapezoid':float(np.trapezoid(e[a:b],dx=.05)),
                    'nearest_integer_cycle':int(np.rint(cycles)),
                    'distance_to_nearest_integer_cycles':float(abs(cycles-np.rint(cycles))),
                    'extended_start_s':te[a_ext],'extended_end_s_exclusive':te[b_ext-1]+.05,
                    'extended_signed_phase_cycles':cycles_ext,
                    'extended_nearest_integer_cycle':int(np.rint(cycles_ext)),
                    'extended_distance_to_integer_cycles':float(abs(cycles_ext-np.rint(cycles_ext))),
                    'peak_abs_error_hz':float(abs(e[a:b]).max())})
    cols=['row','scene','snr_db','record_id','seed','in_sigma2','event_index','start_s','end_s_exclusive','duration_s',
          'signed_phase_cycles_rectangle','signed_phase_cycles_trapezoid','nearest_integer_cycle',
          'distance_to_nearest_integer_cycles','extended_start_s','extended_end_s_exclusive',
          'extended_signed_phase_cycles','extended_nearest_integer_cycle','extended_distance_to_integer_cycles','peak_abs_error_hz']
    ev=pd.DataFrame(events,columns=cols);ev.to_csv(OUT/'PC_TBD_CANDIDATE_EVENT_PHASE_AREAS.csv',index=False)
    diag=pd.read_csv(OUT/'traj_export_X2_diagA2.csv').set_index('row')
    got=ev.groupby('row').size().to_dict() if len(ev) else {}
    for r in x.itertuples(index=False):assert got.get(r.row,0)==int(diag.loc[r.row,'n_slip_runs'])
    protected=pd.read_csv(ROOT/'phaseE/E0_preflight/PROTECTED_FILES_before.csv')
    for r in protected.itertuples(index=False):assert sha(ROOT/r.path)==r.sha256
    lines=['# A2：已有轨迹的直接 η 诊断','',
        '状态：X2 5600 行及 X1 四种时长共 2400 行全部完成。没有重跑仿真，收到的诊断脚本保持原字节。',
        f'重算输入 η 的最大绝对差为 {max(c["eta_in_max_abs_diff"] for c in checks):.10g}，全部小于 1e−6。154 个已登记冻结文件的指纹保持一致。',
        '', '## 实际计算的量','',
        '`eta_clean_m1/m2`：在已知无噪声目标上，按分块相干能量减平滑罚项运行三个阶段，再按全长罚项目标选择候选，最后计算残余频率搜索下的 η。m1 为全局 ±0.02 Hz，m2 为全局 ±0.04 Hz；使用 L-BFGS-B、不设原频率检查点约束。它是该数值流程找到的可达 η，不是经过全局最优性证明的上界，也不是冻结局部扩张方法的无噪声输出。',
        '', '`ceiling_gain_m1` 是上述可达值减去保存的输入 η。`noise_loss_m1` 是上述可达值减去保存的实际输出 η；两项之差在代数上等于实际增量。后一差值同时受噪声、求解器、约束以及起点重建影响，不能独立归因于噪声。',
        '', 'X2 的 VS 使用同记录 V0 作为锚，并用带界最小二乘重建输入系数；`start_fit_rms_hz` 报告重建误差。其余前端以自己的输入作锚。X1 没有 V0 导出，VS 也以自身输入作锚、从零起步。原脚本 `anchor_is_input` 实际标记的是 VS 缺少 V0 时的回退（X1=1）；X2 的非 VS 行虽然标记为 0，仍是自身输入作锚。',
        '', '`n_slip_runs` 为去中位数后误差绝对值超过 0.0625 Hz、持续 4–12 s 的段数；它筛出候选误差段。独立表 `PC_TBD_CANDIDATE_EVENT_PHASE_AREAS.csv` 给出每段的有符号相位面积及距最近整数周的距离，另给两端各延长 4 s 的面积，以包含线性插值造成的阈值以下尾部；这些量尚不能确定误差来源是读出整周判错。原脚本说明中的单独 wrapped-phase 输出没有实际生成；脚本实际通过复指数计算 η。',
        '', '## 汇总','', '| 数据 | 前端 | n | 输入 η | 输出 η | 无噪声 m1 | 无噪声 m2 | m1 增量与实际增量秩相关 |',
        '|---|---|---:|---:|---:|---:|---:|---:|']
    for r in sums:lines.append(f'| {r["dataset"]} | {r["frontend"]} | {int(r["n"])} | {r["eta_in"]:.4f} | {r["eta_out"]:.4f} | {r["eta_clean_m1"]:.4f} | {r["eta_clean_m2"]:.4f} | {r["rho_ceiling_gain_vs_gain"]:.4f} |')
    lines+=['','数值流程的可达值低于输入 η、扩大幅度界后低于较小幅度界，以及低于实际输出的行数，逐数据集列在 `DIAGNOSTICS_A2_CHECKS.csv`。这也是区分数值可达值和严格上界的直接检查。',
        '', '误差分区按 σ² 与已有入口判据划分，是对已有结果的条件汇总。σ²≥5 且入口可用的区间本身不等同于已经证实发生突发误差；机制需要结合逐条轨迹检查。收到的 Claude 分析和分区表保留原文，独立复算见 `DIAGNOSTICS_A2_REGIMES.csv`、`DIAGNOSTICS_A2_SUBSETS.csv`。这些诊断没有改变最终方法参数。',
        '', '完整 H5 的本机路径及 SHA-256 仍见 `LOCAL_H5_FILES_sha256.csv`；新诊断的输入、六进程设置、脚本指纹见 `run_config_A2.json`。CSV 列来自原 index 加上述诊断列；`*_diagA2_summary.csv` 为各前端行均值及全体行秩相关。相关系数的子集和 n 在独立复算表中逐项写明。']
    (OUT/'README_A2.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    manifest=[]
    for p in sorted(OUT.glob('*')):
        if p.is_file() and ('diagA2' in p.name or p.name.startswith(('DIAGNOSTICS_A2','PC_TBD_')) or p.name in ('README_A2.md','run_config_A2.json','任务A结果分析_Claude_20261007.md','任务A_误差分区表.csv')) and p.suffix!='.log':
            manifest.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
    for p in (Path(__file__),Path(__file__).with_name('run_diagnostics_A2_checked.py'),Path(__file__).with_name('diagnostics_A2.py')):
        manifest.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
    pd.DataFrame(manifest).to_csv(OUT/'A2_SHA256_MANIFEST.csv',index=False)
    for m in manifest:
        p=ROOT/m['path'];dest=REPO/m['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    shutil.copy2(OUT/'A2_SHA256_MANIFEST.csv',REPO/'phaseE/E1_trajexport/A2_SHA256_MANIFEST.csv')
    print(pd.DataFrame(sums).to_string(index=False));print('Candidate PC-TBD episodes',len(ev),flush=True)

if __name__=='__main__':main()
