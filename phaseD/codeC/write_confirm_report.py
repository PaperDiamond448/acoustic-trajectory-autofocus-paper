from pathlib import Path
import json, hashlib
import numpy as np
import pandas as pd

ROOT=Path(r'D:\论文集\phaseD');OUT=ROOT/'C_confirm';FM='ADA_local_c04_t30_A'

def f(x):
    return '未定义' if x is None or pd.isna(x) else f'{x:.6f}'

def table(frame, columns):
    lines=['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']
    for _,r in frame.iterrows():lines.append('| '+' | '.join(str(r[c]) for c in columns)+' |')
    return '\n'.join(lines)

def write():
    decision=json.loads((OUT/'CONFIRM_DECISION.json').read_text(encoding='utf8'))
    audit=json.loads((OUT/'INDEPENDENT_AUDIT.json').read_text(encoding='utf8'))
    native=json.loads((OUT/'SAVED_OUTPUTS_AUDIT.json').read_text(encoding='utf8'))
    figqa=json.loads((OUT/'qa/FIGURE_QA.json').read_text(encoding='utf8'))
    assert audit['status']==native['status']==figqa['status']=='PASS'
    assert figqa['visual_review']=='PASS'
    run=json.loads((OUT/'C_run_config.json').read_text(encoding='utf8'))
    machine=json.loads((OUT/'MACHINE.json').read_text(encoding='utf-8-sig'))
    d=pd.read_csv(OUT/'C_records.csv');cells=pd.read_csv(OUT/'C_cell_statistics.csv');s=pd.read_csv(OUT/'C_summary.csv')
    rounds=pd.read_csv(OUT/'C_ADA_rounds.csv')
    rules={'P1':'FM−F02 合并 Δη 的 95% CI 下界 > 0','P2':'FM−UNB 合并 Δη 的 95% CI 下界 > −0.005','P3':'H_FM−H_UNB 的 95% CI 上界 < 0','S1':'不存在 FM−F02 单元 Δη 的 95% CI 上界 < −0.005 的单元'}
    primary=[]
    for name in ['P1','P2','P3','S1']:
        r=decision['endpoints'][name]
        primary.append({'终点':name,'预登记规则':rules[name],'估计值':f(r.get('mean')) if name!='S1' else f"退化单元 {len(r['deteriorated_cells'])}/14",'95% CI':f"[{f(r['lo'])}, {f(r['hi'])}]" if name!='S1' else '见完整单元表','判定':'通过' if r['passed'] else '未通过'})
    branch=decision['branch'];method=decision['primary_method']
    interpretations={
        'C-A1':'P1、P2、P3、S1 全部满足，按 §6.4 自适应作为主方法。',
        'C-A2':'P1、P3、S1 满足，但 P2 未通过。按 §6.4 自适应作为主方法；必须同时交代相对 UNB 的平均 η 代价和实质退化率降低。',
        'C-A3':'P1 未通过，按 §6.4 固定 0.02 Hz 作为主方法；半径放宽与去盒界仅作敏感性分析。',
        'C-A4':'P1 通过，但 S1 未通过，按 §6.4 固定 0.02 Hz 作为主方法；自适应作为变体并列出退化单元。',
        '介于两者之间':'所得终点组合不属于 §6.4 已列分支，依方案如实报告“介于两者之间”，不强行归入最近分支、不修改冻结方法。'}
    sections=[f'# Phase D 确认报告：{branch}\n\n协议 ASL-D-20261003；phase 52；2026-10-04 用户放行后执行。状态：**停止点 2，等待用户核对；X1–X3 未开始。**',
        '## 1. 预登记终点与分支\n\nFM 为开发冻结的 `ADA_local_c04_t30_A`。判定严格采用主方案 §6.3、§6.4 与优先适用的补充文件；无确认后改参数。\n\n'+table(pd.DataFrame(primary),['终点','预登记规则','估计值','95% CI','判定'])+f'\n\n**正式分支：{branch}。** {interpretations[branch]}\n\n后续主方法：'+(f'`{method}`。' if method else '尚不能由预登记分支唯一确定。')+' 后续实验仍需停止点 2 放行。',
        '## 2. 完整性与冻结配置\n\nS0/S2 × SNR −20:−14 dB × record_id 1–200：2,800 条新记录、400 个场景内种子簇、五种方法各 2,800 条，共 14,000 行。T=300 s；评价区间 [5,295) s；20 Hz。SMR、F02、F04、UNB 和 FM 均在同记录上配对。没有删除记录、追加预算或重试求解。\n\nΔ=10 s，31 个节点，r=0.02 Hz；λ_C=0.005151315789473684，λ_F=0.5151315789473684；各阶段预算为 354 次迭代 / 1,476 次目标调用；三阶段块长 20/60/290 s；步长与最优性容差均为 10⁻⁶。SMR 始终固定 ±0.02 Hz；F04 的系数界为 ±2；UNB 只去掉系数盒界，保留全局频带约束。\n\nFM 以同记录 F02 为第 0 轮；最长 0.95 倍边界驻留 ≥30 s 时，只将受影响帽函数支撑节点及其相邻节点从 ±1 升至 ±2；从上一轮解重跑完整三阶段，上一解显式进入候选，候选只按全长目标 J 选择。最多一次扩张。未触发记录与 F02 逐位相同；所有记录 FM 的全长 J 均未下降。\n\n种子为 `20260915 + 52×10^6 + scene_code×10^4 + record_id`（S0=1，S2=3），与开发 phase 51 无交集，亦不使用 E4a 记录。',
        '## 3. 统计实现\n\n2,000 次配对 bootstrap；2.5/97.5 百分位。随机种子 20261052，NumPy PCG64。先依 S0、S2 顺序生成两个 2000×200 的场景内种子重采样数组，同种子携带七个 SNR；合并值为 14 个单元均值等权平均。分场景值为七个单元等权平均。随后按 scene、SNR 顺序生成 14 个 2000×200 单元内配对重采样数组。各配对指标共用对应抽样数组，保存在 `bootstrap_draws.npz`。\n\nP3 直接重采样同记录的二元伤害指标之差，H_method 定义为 η_method < η_F02−0.01；没有把两个独立 CI 相减。S1 只检查单元 CI 上界 <−0.005，未要求每个单元正向显著。不作联合多重比较校正，也不将单元数量作为显著性结论。\n\n全部 η 和主终点均要求有限；若次要 3 dB 宽度数学上未定义，保留该记录，并单独报告有效数，仅该次要均值按有效值计算。软件版本：Python '+decision['bootstrap']['python']+'，NumPy '+decision['bootstrap']['numpy']+'，pandas '+decision['bootstrap']['pandas']+'。']
    scene_rows=[]
    for scene,stats in decision['by_scene'].items():
        for metric,r in stats.items():scene_rows.append({'场景':scene,'对比':metric,'均值':f(r['mean']),'95% CI':f"[{f(r['lo'])}, {f(r['hi'])}]"})
    sections.append('## 4. 分场景主对比\n\n'+table(pd.DataFrame(scene_rows),['场景','对比','均值','95% CI']))
    s1=pd.read_csv(OUT/'S1_cells.csv');z=s1[['scene','snr_db','mean','lo','hi','systematic_deterioration']].copy()
    z['95% CI']=z.apply(lambda r:f"[{f(r.lo)}, {f(r.hi)}]",axis=1);z['均值']=z['mean'].map(f);z['系统性退化']=z.systematic_deterioration.map({True:'是',False:'否'})
    sections.append('## 5. S1 完整单元核对\n\n'+table(z,['scene','snr_db','均值','95% CI','系统性退化']))
    z=cells[cells.method.eq(FM)&cells.metric.isin(['gain_eta_vs_SMR','gain_peak_vs_SMR_db'])].copy()
    for col in ['mean','median','q25','q75','positive_fraction']:z[col]=z[col].map(f)
    z['95% CI']=z.apply(lambda r:f"[{f(r.lo)}, {f(r.hi)}]",axis=1)
    sections.append('## 6. 论文逐单元表：FM 相对 SMR\n\n均值的 CI 为单元内配对 bootstrap；IQR 以 Q25、Q75 给出；正值比例按逐记录配对增量计算。\n\n'+table(z,['scene','snr_db','metric','mean','median','q25','q75','95% CI','positive_fraction']))
    z=s[s.metric.isin(['eta','gain_eta_vs_F02','gain_eta_vs_SMR','harm_vs_F02','harm_vs_SMR'])].copy()
    z['均值']=z['mean'].map(f);z['95% CI']=z.apply(lambda r:f"[{f(r.lo)}, {f(r.hi)}]",axis=1)
    sections.append('## 7. 所有方法增益与实质退化\n\n包含固定 F04 对照与去盒界 UNB，保留全部负向结果。\n\n'+table(z,['scope','method','metric','均值','95% CI']))
    sections.append('## 8. 次要指标与绘图\n\n观测谱峰、突出度、3 dB 宽度、轨迹 RMSE、最大偏差、超出 0.02 Hz 的最长时长和相对 VIT 的 η 增量见 `C_summary.csv`；逐条值见 `C_records.csv`。这些指标均未用于候选选择或确认分支。完整单元配对统计见 `C_cell_statistics.csv`。\n\n![确认逐单元增量](fig_C_paired_eta.png)\n\n![确认增益与退化](fig_C_gain_harm.png)\n\n绘图采用 Nature Figure 2.8.0 / Python，读取结果前已有固定绘图约定。两图均导出 600 dpi PNG、PDF、SVG，严格面板对齐 1.5 pt、字体检查、碰撞检查与逐图目视核验全部通过；完整图注见 `FIGURE_CAPTIONS.md`。')
    rt=[]
    q=d[d.method.eq(FM)]
    for scope in ['ALL','S0','S2']:
        z=q if scope=='ALL' else q[q.scene.eq(scope)]
        for col in ['t_frontend_s','t_vit_s','t_family_s','t_smr_s','runtime_s']:
            rt.append({'场景':scope,'时间项':col,'中位秒':f(z[col].median()),'90% 分位秒':f(z[col].quantile(.9)),'记录数':len(z)})
        rr=rounds if scope=='ALL' else rounds[rounds.scene.eq(scope)]
        for rn in [0,1]:
            a=rr[rr['round'].eq(rn)]
            rt.append({'场景':scope,'时间项':f'BTA_round_{rn}','中位秒':f(a.runtime_s.median()),'90% 分位秒':f(a.runtime_s.quantile(.9)),'记录数':len(a)})
    sections.append('## 9. 计算量与求解诊断\n\n'+table(pd.DataFrame(rt),['场景','时间项','中位秒','90% 分位秒','记录数'])+f'\n\nFM 触发 {int(q.triggered.sum())}/2800（{q.triggered.mean():.2%}）；每次触发恰为一次扩张。FM 相对 SMR 的额外 BTA 时间/300 s：中位 {q.runtime_s.median()/300:.2%}，90% 分位 {q.runtime_s.quantile(.9)/300:.2%}。\n\n计时为六 worker 负载下每次调用的墙钟时间；ADA 总时间为复用 F02 时间加扩张调用时间，排除共享前端、VIT、族、SMR 与驻留核算。没有进行串行基准测量。整个 C 数值批处理墙钟 '+f(run['elapsed_wall_seconds'])+' 秒。机器：'+str(machine['cpu'])+f"，{machine['cores']} 核 / {machine['logical_processors']} 逻辑处理器；MATLAB {run['matlab_version']}；6 个 Processes worker。\n\n各方法 hard_fail 数：`"+json.dumps(decision['diagnostics']['hard_fail_counts'],ensure_ascii=False)+'`。各方法最终求解输出预算触顶数：`'+json.dumps(decision['diagnostics']['budget_cap_counts'],ensure_ascii=False)+'`。原始各阶段退出标志、迭代与调用次数保留于 CSV/MAT；完整 ADA 轮次时间与 J 见 `C_ADA_rounds.csv`。未因失败或触顶追加预算、重试或删除记录。')
    sections.append('## 10. 独立核验、来源与停止点\n\nMATLAB 只读核验重新生成全部 2,800 条 phase-52 输入并复算五种方法的指标，核对候选全长 J、全局约束、预算、本地扩张支撑、上一解显式保留和未触发逐位等价；全部通过。独立 Python 脚本从原始 η 重算三个合并终点和 14 个 S1 单元，bootstrap 与分支全部一致。所有登记的历史源文件、原始结果、开发及停止点 1 核对文件指纹均保持不变。\n\n- 主方案 SHA-256：`af3ab68bbdfd8ecefbd042e9faaac001a16c28a8f73a2fc071b3e315a6090df5`。\n- 补充文件 SHA-256：`fa6ccd779cb2ecfdff250778571963cdc77a170c187a95f85978a15638400344`。\n- 开发冻结文件 SHA-256：`ff63f32c38fc17e99620faa074025c337df247bf823be4fa4b40e74860c0a89f`。\n- C 源码 manifest SHA-256：`'+run['source_signature']+'`。\n- C 逐条 CSV SHA-256：`'+decision['confirmation_csv_sha256']+'`。\n\n核验结果：`PREFLIGHT.json`、`SAVED_OUTPUTS_AUDIT.json`、`INDEPENDENT_AUDIT.json` 和 `qa/FIGURE_QA.json`；用户放行记录见 `AUTHORIZATION.md`。实验数值没有偏离冻结方案；运行环境启动时 MATLAB 报告自身统计工具箱 settingsInfo.json 警告，未修改该系统文件，接口独立核验及全部原始输出核验均通过。\n\n**已到停止点 2。确认后未调整方法，也未执行 X1–X3。请用户核对本报告与逐条记录后决定是否放行后续阶段。**')
    (OUT/'CONFIRM_REPORT.md').write_text('\n\n'.join(sections)+'\n',encoding='utf8')
    decision['status']='stop2_complete_awaiting_user_audit';decision['X_started']=False
    (OUT/'CONFIRM_DECISION.json').write_text(json.dumps(decision,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    (OUT/'FINAL_STATUS.json').write_text(json.dumps(dict(status='stop2_complete_awaiting_user_audit',branch=branch,primary_method=method,records=2800,methods=5,X_started=False,report_sha256=hashlib.sha256((OUT/'CONFIRM_REPORT.md').read_bytes()).hexdigest()),ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print('CONFIRM_REPORT.md written; stop 2 reached.')

if __name__=='__main__':write()
