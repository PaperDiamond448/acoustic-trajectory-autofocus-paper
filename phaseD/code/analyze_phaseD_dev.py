"""Pre-registered Phase D decisions; only phase-51 development data accepted."""
from pathlib import Path
import json, sys, hashlib, csv, platform, re
import numpy as np
import pandas as pd

ROOT=Path(r'D:\论文集\phaseD'); OUT=ROOT/'D_dev'; OUT.mkdir(exist_ok=True)
KEY=['scene','snr_db','record_id','seed','input_hash']
DELTAS=[60,30,20,15,10,7.5,6]; FREEZE=[30,15,10,7.5,6]
SEED=20261051; rng=np.random.default_rng(SEED)
DRAWS={s:rng.integers(0,60,(2000,60)) for s in ['S0','S2']}

def write(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')

def read(name):
    t=pd.read_csv(OUT/name)
    assert t['seed'].eq(20260915+51000000+t.scene.map({'S0':10000,'S2':30000})+t.record_id).all()
    return t

def paired_base(t):
    base=t[(t.method=='F02')&(t.arm=='scaled')][KEY+['Delta_s','eta','peak_db']].rename(columns={'eta':'eta_F02','peak_db':'peak_F02'})
    assert not base.duplicated(KEY+['Delta_s']).any()
    t=t.merge(base,on=KEY+['Delta_s'],how='left',validate='many_to_one')
    assert t.eta_F02.notna().all()
    t['gain_eta_vs_F02']=t.eta-t.eta_F02
    t['harm_vs_F02']=(t.eta<t.eta_F02-0.01).astype(float)
    return t

def matrix(t,metric,scene):
    q=t[t.scene==scene]
    a=q.pivot(index='record_id',columns='snr_db',values=metric).reindex(index=range(1,61),columns=range(-20,-13)).to_numpy(float)
    assert a.shape==(60,7) and np.isfinite(a).all(),f'Missing/nonfinite {metric} in {scene}'
    return a

def interval(t,metric,scene='pooled'):
    scenes=['S0','S2'] if scene=='pooled' else [scene]
    arrays=[matrix(t,metric,s).mean(axis=1) for s in scenes]
    value=float(np.mean([a.mean() for a in arrays]))
    boots=np.mean([a[DRAWS[s]].mean(axis=1) for s,a in zip(scenes,arrays)],axis=0)
    lo,hi=np.percentile(boots,[2.5,97.5])
    return {'value':value,'lower':float(lo),'upper':float(hi)}

def summarize(t,prefix):
    rows=[];cells=[]
    metrics=['eta','gain_eta_vs_VIT','gain_eta_vs_SMR','gain_eta_vs_F02','harm_vs_F02','harm_vs_SMR','peak_db','prominence_db','track_rmse_hz','max_error_hz','longest_out_0p02_s','budget_cap']
    for (delta,arm,method),q in t.groupby(['Delta_s','arm','method'],sort=False):
        assert len(q)==840 and not q.duplicated(KEY).any()
        for scene in ['S0','S2','pooled']:
            r={'Delta_s':delta,'P':int(300/delta+1),'arm':arm,'method':method,'scene':scene,'n_records':840 if scene=='pooled' else 420,'n_seeds':120 if scene=='pooled' else 60}
            for metric in metrics:
                iv=interval(q,metric,scene);r[metric]=iv['value'];r[metric+'_lo']=iv['lower'];r[metric+'_hi']=iv['upper']
            v=q if scene=='pooled' else q[q.scene==scene]
            r['runtime_median_s']=float(v.runtime_s.median());r['runtime_p90_s']=float(v.runtime_s.quantile(.9));r['width_3db_hz']=float(v.width_3db_hz.mean());r['hard_fail_count']=int(v.hard_fail.sum())
            rows.append(r)
        for (scene,snr),v in q.groupby(['scene','snr_db']):
            v=v.sort_values('record_id');assert len(v)==60
            r={'Delta_s':delta,'P':int(300/delta+1),'arm':arm,'method':method,'scene':scene,'snr_db':snr,'n':60}
            for metric in metrics:
                a=v[metric].to_numpy(float);b=a[DRAWS[scene]].mean(axis=1);lo,hi=np.percentile(b,[2.5,97.5]);r[metric]=float(a.mean());r[metric+'_lo']=float(lo);r[metric+'_hi']=float(hi)
            cells.append(r)
    s=pd.DataFrame(rows);s.to_csv(OUT/(prefix+'_summary.csv'),index=False);pd.DataFrame(cells).to_csv(OUT/(prefix+'_cell_stats.csv'),index=False)
    return s

def d1():
    t=paired_base(read('D1_records.csv'));assert len(t)==840*20
    s=summarize(t,'D1');gr=[]
    for scene in ['S0','S2']:
        for method in ['F02','UNB']:
            q=s[(s.scene==scene)&(s.method==method)&(s.arm=='scaled')]
            maximum=float(q.gain_eta_vs_VIT.max());threshold=.95*maximum if maximum>0 else maximum-.005
            for row in q.itertuples():
                gr.append({'scene':scene,'method':method,'Delta_s':row.Delta_s,'P':row.P,'G':row.gain_eta_vs_VIT,'G_lo':row.gain_eta_vs_VIT_lo,'G_hi':row.gain_eta_vs_VIT_hi,'Gmax_all_seven':maximum,'threshold':threshold,'qualifies':row.gain_eta_vs_VIT>=threshold,'freeze_allowed':row.Delta_s in FREEZE,'gap':maximum-row.gain_eta_vs_VIT})
    gt=pd.DataFrame(gr);gt.to_csv(OUT/'D1_selection_rules.csv',index=False)
    options=[d for d in FREEZE if gt[gt.Delta_s==d].qualifies.all()]
    if options:delta=max(options);reason='All four 95%/nonpositive-gain conditions met; largest eligible spacing.'
    else:
        worst={d:float(gt[gt.Delta_s==d].gap.max()) for d in FREEZE};minimum=min(worst.values());delta=max(d for d in FREEZE if worst[d]<=minimum+1e-4)
        reason='95% 规则无解，按最坏差距选取；W 相差不超过 1e-4 时取较大的 Δ。'
    write('D1_DECISION.json',{'Delta_s':delta,'P':int(300/delta+1),'reason':reason,'eligible_intersection':options,'rules':gr,'worst_gaps':{str(d):float(gt[gt.Delta_s==d].gap.max()) for d in FREEZE},'selection_uses':'eta gain vs common VIT, point estimates; peak not used','bootstrap_seed':SEED,'bootstrap_replicates':2000})
    print(json.dumps({'Delta_s':delta,'reason':reason},ensure_ascii=True))

def fixed():
    t=paired_base(read('fixed_records.csv'));assert len(t)==840*5;s=summarize(t,'D2_fixed')
    rows=s[(s.scene!='pooled')&s.method.isin(['F04','F08','UNB'])]
    no_benefit=bool((rows.gain_eta_vs_F02<.005).all())
    p=s[s.scene=='pooled'].set_index('method');best=min(['F04','F08'],key=lambda m:(-p.loc[m,'gain_eta_vs_F02'],m))
    write('D2_FIXED_DECISION.json',{'C0':no_benefit,'Gref':float(p.loc[['F04','F08','UNB'],'gain_eta_vs_F02'].max()),'F_star':best,'A3_inputs':rows[['scene','method','gain_eta_vs_F02','gain_eta_vs_F02_lo','gain_eta_vs_F02_hi']].to_dict('records'),'strict_threshold':.005})
    print(json.dumps({'C0':no_benefit,'F_star':best}))

def triggers():
    t=read('rerunA_records.csv');assert len(t)==840
    n=int(t.triggered.sum());write('D2_TRIGGER_DECISION.json',{'triggered_records':n,'run_B':n>=30,'rerun_if_sparse':'A','threshold':30})
    print('Triggered records:',n)

def rerun():
    decision=json.loads((OUT/'D2_TRIGGER_DECISION.json').read_text(encoding='utf8'));n=decision['triggered_records']
    if n<30:result={'selected':'A','triggered_records':n,'reason':'A5: fewer than 30 triggered records; no A/B comparison.'}
    else:
        a=read('rerunA_records.csv');b=read('rerunB_records.csv');q=a.merge(b,on=KEY,suffixes=('_A','_B'),validate='one_to_one');assert (q.triggered_A==q.triggered_B).all();q=q[q.triggered_A]
        eta=float(np.abs(q.eta_B-q.eta_A).mean());peak=float(np.abs(q.peak_db_B-q.peak_db_A).mean());ratio=float(np.median(q.runtime_s_B/q.runtime_s_A))
        choose=eta<.005 and peak<.1 and ratio<.6
        result={'selected':'B' if choose else 'A','triggered_records':n,'mean_abs_eta_difference':eta,'mean_abs_peak_difference_db':peak,'median_runtime_B_over_A':ratio,'thresholds':[.005,.1,.6],'all_strict_conditions_met':choose}
        q.to_csv(OUT/'D2a_triggered_pairs.csv',index=False)
    write('D2_RERUN_DECISION.json',result);print(json.dumps(result))

def freeze():
    delta=json.loads((OUT/'D1_DECISION.json').read_text(encoding='utf8'));fixed_d=json.loads((OUT/'D2_FIXED_DECISION.json').read_text(encoding='utf8'))
    t=paired_base(read('fixed_records.csv'));params=None;selection=None;fixedtests=[]
    if fixed_d['C0']:branch='C0';chosen='F02';rerun_d=None
    else:
        rerun_d=json.loads((OUT/'D2_RERUN_DECISION.json').read_text(encoding='utf8'));grid=read('grid_records.csv');assert len(grid)==840*20
        t=pd.concat([read('fixed_records.csv'),grid],ignore_index=True);t=paired_base(t);s=summarize(t,'D2');ada=s[(s.scene=='pooled')&s.method.str.startswith('ADA_')].copy();threshold=.9*fixed_d['Gref'];ada['qualifies']=ada.gain_eta_vs_F02>=threshold
        good=ada[ada.qualifies].copy()
        if len(good):
            hmin=float(good.harm_vs_F02.min());eligible=good[good.harm_vs_F02<=hmin+.005].copy();rule='G >= 0.9 Gref; H <= Hmin+0.005; global, smaller cap, larger tau.'
        else:
            eligible=ada[ada.gain_eta_vs_F02==ada.gain_eta_vs_F02.max()].copy();hmin=None;rule='未保留去盒界 90% 的增益：无合格变体，取 G 最大者。'
        def priority(name):
            m=re.fullmatch(r'ADA_(global|local)_c(04|08)_t(\d+)_(A|B)',name);return (m[1]!='global',int(m[2]),-int(m[3]))
        selected=min(eligible.method,key=priority);m=re.fullmatch(r'ADA_(global|local)_c(04|08)_t(\d+)_(A|B)',selected)
        params={'mode':m[1],'cap_hz':int(m[2])/100,'tau_s':int(m[3]),'rerun':m[4]}
        ada['H_min_qualified']=hmin;ada['gain_threshold']=threshold;ada.to_csv(OUT/'D2b_selection_rules.csv',index=False)
        sufficient=[]
        for fm in ['F04','F08']:
            both=True
            for scene in ['S0','S2']:
                a=s[(s.scene==scene)&(s.method==selected)].iloc[0];f=s[(s.scene==scene)&(s.method==fm)].iloc[0];ok=f.gain_eta_vs_F02>=a.gain_eta_vs_F02-.002 and f.harm_vs_F02<=a.harm_vs_F02+.01;both=both and ok
                fixedtests.append({'method':fm,'scene':scene,'G_fixed':float(f.gain_eta_vs_F02),'G_fixed_ci':[float(f.gain_eta_vs_F02_lo),float(f.gain_eta_vs_F02_hi)],'G_ADA':float(a.gain_eta_vs_F02),'G_ADA_ci':[float(a.gain_eta_vs_F02_lo),float(a.gain_eta_vs_F02_hi)],'H_fixed':float(f.harm_vs_F02),'H_ADA':float(a.harm_vs_F02),'gain_threshold':float(a.gain_eta_vs_F02-.002),'harm_threshold':float(a.harm_vs_F02+.01),'passes':bool(ok)})
            if both:sufficient.append(fm)
        chosen=sufficient[0] if sufficient else selected;branch='C-F' if sufficient else 'C-A';selection={'selected_ADA':selected,'parameters':params,'Gref':fixed_d['Gref'],'gain_threshold':threshold,'H_min':hmin,'qualified_count':int(ada.qualifies.sum()),'rule':rule,'all_20_inputs':ada[['method','gain_eta_vs_F02','gain_eta_vs_F02_lo','gain_eta_vs_F02_hi','harm_vs_F02','harm_vs_F02_lo','harm_vs_F02_hi','qualifies']].to_dict('records')}
    s=summarize(t,'D2');t.to_csv(OUT/'D2_records.csv',index=False)
    p=delta['P'];scale=(p-2)/19*(15/delta['Delta_s'])**3
    if delta['Delta_s']==15:scale=1.
    main=ROOT/'PREREGISTRATION_PhaseD_20261003.md';add=ROOT/'PREREGISTRATION_PhaseD_ADDENDUM_20261003.md'
    manifest=pd.read_csv(ROOT/'code/SOURCE_MANIFEST_sha256.csv')
    frozen={'protocol':'ASL-D-20261003','status':'development_frozen_awaiting_user_rule_audit','branch':branch,'method':chosen,'Delta_s':delta['Delta_s'],'P':p,'r_hz':.02,'regularization':{'formula':'lambda0*(P-2)/19*(300/T)*(15/Delta)^3','lambda_C':.001*scale,'lambda_F':.1*scale,'lambda_C0':.001,'lambda_F0':.1},'fixed_radius_hz':{'F02':.02,'F04':.04,'F08':.08}.get(chosen),'ADA':params if branch=='C-A' else None,'developed_ADA':params,'F_star':fixed_d['F_star'],'bounds_rule':'u in +/-rho/0.02; unbounded +/-Inf; global frequency constraints preserved','SMR_start_rule':'fixed radius 0.02 and |u|<=1 for all radii','stage_blocks_s':[20,60,290],'budget_formula':{'max_iter_per_stage':'round(240*max(1,P/21))','max_fevals_per_stage':'round(1000*max(1,P/21))','selected_iterations':int(np.floor(240*max(1,p/21)+.5)),'selected_fevals':int(np.floor(1000*max(1,p/21)+.5))},'tolerances':{'step':1e-6,'optimality':1e-6},'trigger_definition':'At 20 Hz on [5,T-5), |B(t)u|>=0.95 B(t)m; longest maximal contiguous run, samples/20 seconds','candidate_selection':'Explicit previous solution and feasible stage endpoints; maximum final full-length objective J only; no eta or observed peak','bootstrap':{'replicates':2000,'seed':SEED,'unit':'seed cluster within scene; all seven SNR records carried together'},'plan_sha256':hashlib.sha256(main.read_bytes()).hexdigest(),'addendum_sha256':hashlib.sha256(add.read_bytes()).hexdigest(),'code_sha256_manifest':manifest.to_dict('records'),'decisions':{'D1':delta,'A3':fixed_d,'rerun':rerun_d,'ADA_selection':selection,'fixed_radius_tests':fixedtests},'confirmation_started':False}
    write('FROZEN_METHOD.json',frozen);h=hashlib.sha256((OUT/'FROZEN_METHOD.json').read_bytes()).hexdigest()
    lines=['# Phase D 开发报告','',f'状态：停止点 1。仅使用 phase 51、S0/S2 × −20…−14 dB × 60 条，共 840 条、120 个种子。确认阶段 C 未启动。',f'冻结方法：{chosen}；分支 {branch}；Δ*={delta["Delta_s"]} s，P={p}。','',f'主方案 SHA-256：`{frozen["plan_sha256"]}`',f'补充方案 SHA-256：`{frozen["addendum_sha256"]}`',f'FROZEN_METHOD.json SHA-256：`{h}`','','## 统计与核验','', 'G1–G8 全部通过，详见 ../G_gates/GATES_REPORT.md。合并统计为单元等权均值；按场景内种子成簇 bootstrap，携带全部 7 个 SNR，2000 次，seed=20261051；单元内为配对记录 bootstrap。下列判定全部使用预注册点估计，95% 区间用于报告，不替代阈值。计时是 6 workers 并发负载下单次调用墙钟；批量墙钟见各阶段 run_config。','','## D1：规则 → 输入数字 → 区间 → 判定','', '| 场景 | 模式 | Δ | G | 95% 区间 | Gmax（七个） | 阈值 | 合格 | 可冻结 |','|---|---|---:|---:|---|---:|---:|---|---|']
    for r in delta['rules']:lines.append(f'| {r["scene"]} | {r["method"]} | {r["Delta_s"]} | {r["G"]:.9g} | [{r["G_lo"]:.9g}, {r["G_hi"]:.9g}] | {r["Gmax_all_seven"]:.9g} | {r["threshold"]:.9g} | {r["qualifies"]} | {r["freeze_allowed"]} |')
    lines+=['',f'判定：{delta["reason"]}；交集={delta["eligible_intersection"]}；Δ*={delta["Delta_s"]} s。',f'若交集无解，五个 W 值：{delta["worst_gaps"]}。','对照臂只预注册未缩放 F02，没有未缩放 UNB；报告完整对照曲线及 F02 差异，不虚构四模式的对照 Δ*。','','## D2 A3：扩张无收益规则','', '| 场景 | 变体 | G（相对 F02） | 95% 区间 | <0.005 |','|---|---|---:|---|---|']
    for r in fixed_d['A3_inputs']:lines.append(f'| {r["scene"]} | {r["method"]} | {r["gain_eta_vs_F02"]:.9g} | [{r["gain_eta_vs_F02_lo"]:.9g}, {r["gain_eta_vs_F02_hi"]:.9g}] | {r["gain_eta_vs_F02"]<.005} |')
    lines+=['',f'A3 判定：六个条件同时满足={fixed_d["C0"]}；Gref={fixed_d["Gref"]:.9g}。']
    if rerun_d is not None:
        lines+=['','## D2a：A5 与重跑方式','',json.dumps(rerun_d,ensure_ascii=False,indent=2),'','区间：本规则使用触发计数、平均绝对差及时间比中位数的点估计，预注册未规定这些量的区间；不把它们写作显著性。','', '## D2b：自适应网格冻结','',f'参照 Gref={selection["Gref"]:.9g}；合格阈值={selection["gain_threshold"]:.9g}；合格数={selection["qualified_count"]}/20；H_min={selection["H_min"]}。',f'规则：{selection["rule"]}；选出的 ADA={selection["selected_ADA"]}。','','| 变体 | G | 95% 区间 | H | 95% 区间 | 合格 |','|---|---:|---|---:|---|---|']
        for r in selection['all_20_inputs']:lines.append(f'| {r["method"]} | {r["gain_eta_vs_F02"]:.9g} | [{r["gain_eta_vs_F02_lo"]:.9g}, {r["gain_eta_vs_F02_hi"]:.9g}] | {r["harm_vs_F02"]:.9g} | [{r["harm_vs_F02_lo"]:.9g}, {r["harm_vs_F02_hi"]:.9g}] | {r["qualifies"]} |')
        lines+=['','## D2：固定半径是否足够','', '| 半径 | 场景 | G固定 | G ADA | G阈值 | H固定 | H ADA | H阈值 | 通过 |','|---|---|---:|---:|---:|---:|---:|---:|---|']
        for r in fixedtests:lines.append(f'| {r["method"]} | {r["scene"]} | {r["G_fixed"]:.9g} | {r["G_ADA"]:.9g} | {r["gain_threshold"]:.9g} | {r["H_fixed"]:.9g} | {r["H_ADA"]:.9g} | {r["harm_threshold"]:.9g} | {r["passes"]} |')
    lines+=['',f'最终判定：冻结 {chosen}，分支 {branch}。F*={fixed_d["F_star"]}。所有逐单元、分场景及合并区间见 D1/D2 summary 和 cell_stats。','','## 实现与边界','', '不同半径只改 u 上下界，r=0.02；SMR 始终原 0.02 起点。F01 的 SMR 起点若超出其盒界，不把该不可行起点列为可选终点；求解仍从同一 SMR 输入开始，fmincon 原生处理初值。D2 复用 D1 所选 Δ 的 F02/UNB 原始结果；不重新求解，不挑选更好的重复结果。ADA 不触发时直接复用 F02，扩张时显式保留上一轮解，按全长 J 选取。所有系数、阶段状态、ADA 每轮输出保存在带键的 v7.3 分块 MAT 中。', '未运行串行计时，也不将并行记录时间称为串行时间。负结果全部保留；未删记录、未追加预算、未重试。', '', '停止点 1：等待用户逐条核对规则后才允许 C；本代码没有确认或外部验证入口。']
    (OUT/'DEV_REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf8');print(json.dumps({'method':chosen,'branch':branch,'Delta_s':delta['Delta_s'],'frozen_sha256':h}))

if __name__=='__main__':
    {'d1':d1,'fixed':fixed,'triggers':triggers,'rerun':rerun,'freeze':freeze}[sys.argv[1]]()
