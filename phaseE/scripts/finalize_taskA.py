"""Package checked task-A tables; keep H5, logs and dependencies local."""
from pathlib import Path
import csv
import hashlib
import json
import shutil
import sys

LOCAL=Path(__file__).resolve().parents[1]
ROOT=LOCAL.parent
REPO=ROOT/'GitHub整理_20261007/acoustic-trajectory-autofocus-paper'
OUT=LOCAL/'E1_trajexport'

import numpy as np
import pandas as pd


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def main():
    stems=['traj_export_X2']+[f'traj_export_X1_T{T}' for T in [150,300,450,600]]
    summaries=[];checks=[];fit=[];hfiles=[]
    for stem in stems:
        config=json.loads((OUT/(stem+'_run_config.json')).read_text(encoding='utf-8'))
        exported=json.loads((OUT/(stem+'_export_status.json')).read_text(encoding='utf-8'))
        check=json.loads((OUT/(stem+'_python_check.json')).read_text(encoding='utf-8'))
        assert exported['export_complete'] and exported['all_input_hashes_match'] and check['passed']
        data=pd.read_csv(OUT/(stem+'_theory_metrics.csv'))
        assert len(data)==config['trajectory_rows']==check['checked_rows']
        paired=pd.read_csv(OUT/(stem+'_paired_summary.csv'))
        for frontend,x in data.groupby('frontend'):
            ci=paired[(paired.frontend==frontend)&(paired.metric=='gain')].iloc[0]
            summaries.append({'dataset':stem,'duration_s':config['duration_s'],'frontend':frontend,'n':len(x),
                              'eta_in':float(x.eta_in.mean()),'eta_out':float(x.eta_out.mean()),
                              'gain':float(x.gain.mean()),'gain_ci_lo':float(ci.ci_lo),'gain_ci_hi':float(ci.ci_hi),
                              'in_sigma2_median':float(x.in_sigma2.median()),
                              'in_low_share_median':float(x.in_low_share.median()),
                              'corr_pred_vs_gain':float(x.pred_recoverable.corr(x.gain,method='spearman'))})
            for side in ['in','out']:
                for limit in [.5,1.,np.inf]:
                    small=x[x[side+'_sigma2']<limit]
                    fit.append({'dataset':stem,'duration_s':config['duration_s'],'frontend':frontend,'trajectory':side,
                                'sigma2_upper_exclusive':limit,'n':len(small),
                                'eta_prediction_mae':float((small[side+'_eta_pred']-small['eta_'+side]).abs().mean()),
                                'definition':'mean absolute difference: exp(-sigma2) versus saved eta'})
        h=OUT/(stem+'.h5'); assert sha(h)==exported['h5_sha256']
        hfiles.append({'file':h.name,'local_path':str(h),'bytes':h.stat().st_size,'sha256':exported['h5_sha256']})
        checks.append({'dataset':stem,'trajectory_rows':check['checked_rows'],
                       'truth_records':config['truth_records'],'duration_s':config['duration_s'],
                       'max_eta_in_abs_diff':check['max_eta_in_abs_diff'],
                       'max_eta_out_abs_diff':check['max_eta_out_abs_diff'],'passed':True})
        source=pd.read_csv(OUT/(stem+'_source_chunks_sha256.csv'))
        assert (source.sha256_before==source.sha256_after).all()
    pd.DataFrame(summaries).to_csv(OUT/'THEORY_OVERVIEW.csv',index=False)
    pd.DataFrame(fit).to_csv(OUT/'THEORY_APPROXIMATION_CHECKS.csv',index=False)
    pd.DataFrame(checks).to_csv(OUT/'ETA_RECOMPUTATION_CHECKS.csv',index=False)
    pd.DataFrame(hfiles).to_csv(OUT/'LOCAL_H5_FILES_sha256.csv',index=False)
    before=pd.read_csv(LOCAL/'E0_preflight/PROTECTED_FILES_before.csv')
    for r in before.itertuples(index=False):
        p=ROOT/r.path
        assert p.stat().st_size==r.bytes and sha(p)==r.sha256, f'Frozen file changed: {p}'
    script=LOCAL/'scripts/theory_metrics.py'
    received=ROOT/'当前主线精选_20261003/13_第一批补充分析_20261007/theory_metrics.py'
    assert script.read_bytes()==received.read_bytes()
    assert {json.loads((OUT/(s+'_python_check.json')).read_text(encoding='utf-8'))['supplied_script_sha256'] for s in stems}=={sha(script)}
    status={'task':'A','complete':True,'trajectory_rows':sum(c['trajectory_rows'] for c in checks),
            'x2_rows':5600,'x2_records':1400,'x1_rows':2400,'x1_durations_s':[150,300,450,600],
            'all_input_hashes_match':True,'all_eta_checks_passed':True,
            'max_eta_in_abs_diff':max(c['max_eta_in_abs_diff'] for c in checks),
            'max_eta_out_abs_diff':max(c['max_eta_out_abs_diff'] for c in checks),
            'eta_tolerance':1e-6,'protected_files_unchanged':len(before),
            'supplied_theory_script_unchanged':True,'h5_storage':'local_only',
            'tasks_B_to_F_started':False}
    (OUT/'FINAL_STATUS.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    run={'task':'A','data_sets':stems,'source_phases':{'X2':54,'X1':53},
         'records':'Existing archived records; no frontend or correction solver rerun in task A.',
         'evaluation':'20 Hz; [5,T-5) s; target-only max FFT power in residual band +/-2 Hz; FFT padding factor 8.',
         'theory_script_sha256':sha(script),'eta_check_tolerance':1e-6,
         'bootstrap':{'seed':20261007,'replicates':2000,'cluster':'record_id within scene, carrying all SNRs and frontends',
                      'cell_weights':'equal scene/SNR','interval':'95% percentile'},
         'h5_local_files':hfiles,'protected_files_unchanged':len(before)}
    (OUT/'run_config.json').write_text(json.dumps(run,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# 任务 A：已有轨迹导出与理论指标','',
           f'状态：完成。X2 的 1400 条记录、4 种前端共 5600 行；X1 的 4 种时长各 600 行，共计 {status["trajectory_rows"]} 行。',
           '',f'全部输入 MD5 与原结果表一致。MATLAB 原指标核对、Python 独立重算及冻结文件指纹核对已通过；Python 最大输入差 {status["max_eta_in_abs_diff"]:.3g}、最大输出差 {status["max_eta_out_abs_diff"]:.3g}，均小于 1e-6。',
           '', '## 汇总','',
           '| 数据 | 时长/s | 前端 | 行数 | 修正前 η | 修正后 η | 增量 [95%区间] | 近似可回收量与实际增量的秩相关 |',
           '|---|---:|---|---:|---:|---:|---|---:|']
    for r in summaries:
        lines.append(f'| {r["dataset"]} | {r["duration_s"]} | {r["frontend"]} | {r["n"]} | {r["eta_in"]:.4f} | {r["eta_out"]:.4f} | {r["gain"]:.4f} [{r["gain_ci_lo"]:.4f}, {r["gain_ci_hi"]:.4f}] | {r["corr_pred_vs_gain"]:.4f} |')
    x2=[r for r in summaries if r['dataset']=='traj_export_X2']
    small=[r for r in fit if r['dataset']=='traj_export_X2' and r['trajectory']=='in' and r['sigma2_upper_exclusive']==.5]
    lines+=['', 'X2 的 σ²<0.5 输入子集，各前端预测 η 的平均绝对误差为 '+
            '、'.join(f'{r["frontend"]} {r["eta_prediction_mae"]:.4f}（{r["n"]} 行）' for r in small)+'。这是小相位近似的定量检查。',
            '', '对全部 X2 记录，脚本计算的近似可回收量与实际增量的秩相关因前端而异：'+
            '、'.join(f'{r["frontend"]} {r["corr_pred_vs_gain"]:+.4f}' for r in x2)+'。MFT 的相关为负，说明该近似量在这组全量记录上与实际增量排序相反。',
            '', '周期长于 20 s 的相位方差贡献份额中位数为 '+
            '、'.join(f'{r["frontend"]} {r["in_low_share_median"]:.4f}' for r in x2)+'。VS、V0、SUV 的份额很接近；按这项指标，当前数据未显示相位连续 TBD 留下的慢分量份额明显更小。此处衡量的是频带积分后的相位贡献，与第一批报告的频率误差方差份额分别定义。']
    lines+=['','增量区间采用同记录配对、场景×信噪比等权、场景内种子成簇重抽样 2000 次。原附带脚本的汇总是均值、中位数与相关；由于本次各组合样本数相等，原均值与组合等权均值一致。各数据集的 `_paired_summary.csv` 另给配对区间，`_bootstrap_draws.npz` 保存实际抽样数组。',
            '', '## 理论量的含义','',
            '收到的 `theory_metrics.py` 保持原字节。`sigma2` 是残余相位去掉最小二乘常数和线性项后的均方值（rad²）；`eta_pred=exp(-sigma2)` 是小相位误差近似。`THEORY_APPROXIMATION_CHECKS.csv` 分别列出 σ²<0.5、σ²<1 和全部轨迹的预测误差与样本数，输入、输出分开。σ² 条件与实际 η 条件分别保留。',
            '', '`p_gt60s`、`p_20to60s`、`p_10to20s`、`p_lt10s` 是对应频带单独积分、去趋势后的相位方差（rad²），名称沿用收到的脚本。它们不等同于频率误差自身的方差；各带重新积分后存在交叉项，份额按脚本采用各带贡献之和作分母。',
            '', '`eta_ceiling_nodes10s` 是将周期短于 20 s 的贡献代入小误差近似得到的量。实际的 10 s 节点、幅度界、正则与求解器均未参与这个量的计算。`pred_recoverable` 在此近似量上减去修正前 η；其与实际增量的相关完整列在表中。小误差近似的预测误差与实际模块增量的预测能力是两项不同检查，汇总分别报告。',
            '', '## 文件与各列','',
            '- `*_index.csv`：一行对应一条记录和一个前端；`row`、`truth_row` 从 0 开始，分别指向 H5 的输入/输出行和真值行。`scene`、`snr_db`、`record_id`、`seed` 与原表相同；`frontend` 的 VS、V0、MFT、SUV 分别表示 VIT–LPS、VIT、MFT 和相位连续 TBD。`eta_in/out` 取原表，`input_usable` 沿用 X2 的入口判据（X1 按同一判据计算）；新增指纹和数值核对列用于查对来源。',
            '- `*_theory_metrics.csv`：原脚本产生的逐行指标；`in_` 与 `out_` 对应模块输入和输出。`rmse_hz` 和 `rmse_demeaned_hz` 单位 Hz；`sigma2` 及 `p_*` 单位 rad²；`low_share`、`eta_pred`、`eta_ceiling_nodes10s` 无量纲。`check_dev_in/out` 是重算 η 与原 η 的绝对差；`gain=eta_out-eta_in`。',
            '- `*_theory_summary.csv`：原脚本的逐前端汇总，未添加或替换原统计量。',
            '- `*_paired_summary.csv`：输入 η、输出 η 和配对增量的等权估计与 95% 区间。',
            '- `THEORY_OVERVIEW.csv`、`THEORY_APPROXIMATION_CHECKS.csv`、`ETA_RECOMPUTATION_CHECKS.csv`：跨数据集导航、近似误差和数值校核。',
            '- `*_source_chunks_sha256.csv`：被读取分块的读取前后 SHA-256。原分块仅被读取。',
            '- `LOCAL_H5_FILES_sha256.csv`：5 个完整 H5 的本机路径、大小和指纹。X2 为 `/truth` 1400×6000、`/input` 和 `/output` 5600×6000；X1 各为 600×(20T)。全部 float64，基带 Hz，完整时间网格 t=n/20。H5 未提交到 GitHub。',
            '', '## 执行与环境','',
            '0.1 预检保存后的三个 MAT 文件已逐行回读，与 12 行 CSV 一致。任务 A 没有重新运行前端或修正求解器；重新生成同一种子的观测记录仅用于重建真值与核对指纹。',
            '', 'X1 由新写的 MATLAB 导出程序读取原分块完成。X2 的 MATLAB 全分块导出两次中断：第一次 HDF5 打开/写入失败，临时读取与写入重叠；第二次在没有并发读取的情况下出现 0xc0000374 堆损坏。中断文件和日志留在本机。最终 X2 导出采用 MATLAB 原生成器一次产生真值、核对 1400 个指纹，Python 串行读取原 MAT-v7 并写 H5；适配过程仅处理存储格式，冻结代码、参数及数值结果保持原样。事件见两个 `ENVIRONMENT_*.json`。',
            '', 'Python 的 h5py 3.16.0 仅安装在本机 `D:\\论文集\\phaseE\\_local_pydeps\\`，用于收到脚本的 HDF5 读取；其余依赖使用原有 D 盘 Python。实际版本见各 `_python_check.json`。新驱动和封装脚本在 `phaseE/scripts/`，新增要求见 `phaseE/requirements.txt`。',
            '', '当前交付截至任务 A。任务 B–F 尚未开始，第 5 节正文及第一批报告原文均保持原样。']
    (OUT/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    preflight_readback={'saved_mat_csv_readback_passed':True,'checked_rows':12,
                        'source':'Every successful phaseE_exportA run reread the three saved preflight MAT structures.'}
    for base in (LOCAL,REPO/'phaseE'):
        (base/'E0_preflight/SAVED_OUTPUT_READBACK.json').write_text(json.dumps(preflight_readback,indent=2)+'\n',encoding='utf-8')
    preflight=LOCAL/'E0_preflight'
    with (preflight/'OUTPUT_MANIFEST_sha256.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['file','bytes','sha256','storage']);w.writeheader()
        for p in sorted(preflight.iterdir()):
            if p.is_file() and p.name!='OUTPUT_MANIFEST_sha256.csv':
                w.writerow({'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p),
                            'storage':'local_only' if p.suffix in ('.mat','.log') else 'repository_and_local'})
    shutil.copy2(preflight/'OUTPUT_MANIFEST_sha256.csv',REPO/'phaseE/E0_preflight/OUTPUT_MANIFEST_sha256.csv')
    excluded=lambda p: p.suffix in ('.h5','.mat','.log') or '.partial.' in p.name
    files=[p for p in OUT.iterdir() if p.is_file() and p.name!='OUTPUT_MANIFEST_sha256.csv']
    with (OUT/'OUTPUT_MANIFEST_sha256.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['file','bytes','sha256','storage']);w.writeheader()
        for p in sorted(files):w.writerow({'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p),
                                           'storage':'local_only' if excluded(p) else 'repository_and_local'})
    for p in OUT.iterdir():
        if p.is_file() and not excluded(p):shutil.copy2(p,REPO/'phaseE/E1_trajexport'/p.name)
    for p in (LOCAL/'scripts').iterdir():
        if p.is_file():shutil.copy2(p,REPO/'phaseE/scripts'/p.name)
    for base in (LOCAL,REPO/'phaseE'):
        (base/'requirements.txt').write_text('numpy==2.2.5\npandas==2.3.3\nscipy==1.15.3\nh5py==3.16.0\n',encoding='utf-8')
        (base/'README.md').write_text('''# Phase E 补充分析

已完成当前指定的 0.1 复现预检与任务 A，任务 B–F 尚未开始。

- [任务书](TASKS_PhaseE_20261007.md)：收到的原文。
- [0.1 预检结果](E0_preflight/README.md)：3 条记录、4 种前端，12 行通过。
- [任务 A 结果与定义](E1_trajexport/README.md)：X2 的 5600 行及 X1 的 2400 行轨迹，理论指标、配对区间和数值核对。
- [逐数据集与前端汇总](E1_trajexport/THEORY_OVERVIEW.csv)
- [理论近似误差检查](E1_trajexport/THEORY_APPROXIMATION_CHECKS.csv)
- [第一批报告和工作清单](../当前主线精选_20261003/13_第一批补充分析_20261007/README.md)

本机大文件：`D:\\论文集\\phaseE\\E1_trajexport\\`，路径和 SHA-256 在任务 A 的 `LOCAL_H5_FILES_sha256.csv`。H5、MAT、日志和独立依赖目录留在本机；脚本、CSV、MD、配置、抽样数组和指纹清单已整理供推送。冻结代码、参数、原实验结果及正文未改动。
''',encoding='utf-8')
    print(json.dumps(status),flush=True)


if __name__=='__main__':main()
