"""Add review metadata and intervals without changing any frozen decision."""
from pathlib import Path
import json,hashlib,re,platform
import pandas as pd
ROOT=Path(r'D:\论文集\phaseD');OUT=ROOT/'D_dev'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
f=read(OUT/'FROZEN_METHOD.json')
history=read(ROOT/'SOURCE_REVISION_HISTORY.json')
f['reproducibility_recipe']={'duration_s':300,'sample_rate_hz':20,'phase_id':51,'record_ids':[1,60],'scenes':['S0','S2'],'snr_db':list(range(-20,-13)),'knot_rule':'0:Delta:T','evaluation_interval_s':'[5,T-5)','stage_block_rule_s':[20,60,'T-10'],'residual_band_hz':[-2,2],'fft_rule':'2^nextpow2(8*Ne)','bootstrap_generator':'numpy.default_rng PCG64','bootstrap_sampling':'Two scene-stratified seed-cluster draw arrays, 2000 x 60 each, generated sequentially with seed 20261051 and reused across paired metrics/variants; all 7 SNR records carried together.'}
f['provenance']={'nature_skills_commit':'84880815fb37317b3766bff2c2abba395b8993c3','figure_skill_version':'2.8.0','D1_manifest_sha256':history['D1_manifest_sha256'],'D2_manifest_sha256':history['D2_manifest_sha256'],'output_only_pre_D2_changes':['phaseD_d2_one.m: fixed-radius dwell diagnostics use their actual bounds; UNB not applicable','plot_phaseD_dev.py: equivalent explicit PDF/SVG/PNG export for static audit'],'decision_inputs_affected':False,'runtime_definition':'Six-worker loaded wall time of each BTA optimizer call. ADA sums reused F02 call time plus expansion call times; excludes frontend, family/SMR construction and dwell bookkeeping. This is not a serial benchmark.','python_version':platform.python_version(),'numpy_version':__import__('numpy').__version__,'pandas_version':pd.__version__,'run_configs':{p.stem:read(p) for p in OUT.glob('*_run_config.json')}}
f['provenance']['figure_export']={'source':'code/plot_phaseD_dev.py','final_layout_wrapper':'D_dev/qa/repair_figure_layout.py','wrapper_sha256':hashlib.sha256((OUT/'qa/repair_figure_layout.py').read_bytes()).hexdigest(),'display_only_correction':'Peak figure subplot top 0.84 -> 0.76; no data or decision changes; numerical source manifest unchanged.'}
f['provenance']['equivalent_reuse']={'authority':'Main protocol section 2.7 permits efficient implementations with identical per-record results','fixed':'F02 and UNB at selected Delta copied exactly from D1, with input-hash and SMR-start equality assertions','global_grid':'Compute tau=10 cap=0.08 chain once; retain the exact allowed prefix for each larger tau and cap','local_grid':'Compute separate cap=0.08 chain for each tau; cap=0.04 is its first-round prefix','timing':'Sum only the saved call times in the selected prefix, including the common F02 solve'}
f['provenance']['csv_flag_read_adapter']={'reason':'MATLAB wrote triggered as binary integer 0/1; original pandas Boolean-index statement failed before producing A/B comparison inputs','proof':read(OUT/'qa/csv_trigger_representation_check.json'),'source_files':{name:hashlib.sha256((OUT/'qa'/name).read_bytes()).hexdigest() for name in ['analyze_rerun_csv_adapter.py','run_remaining_development.ps1']},'decision_inputs_affected':False,'numerical_solver_retries':0,'original_numeric_source_and_manifests_unchanged':True}
(OUT/'FROZEN_METHOD.json').write_text(json.dumps(f,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
sha=hashlib.sha256((OUT/'FROZEN_METHOD.json').read_bytes()).hexdigest()
report=(OUT/'DEV_REPORT.md').read_text(encoding='utf8')
report=re.sub(r'FROZEN_METHOD\.json SHA-256：`[0-9a-f]{64}`',f'FROZEN_METHOD.json SHA-256：`{sha}`',report)
report=report.split('\n## 补充审计与复现信息')[0]
report=report.replace('未删记录、未追加预算、未重试。','未删记录、未追加预算、未重试数值求解。CSV 布尔表示适配后仅重新执行失败的 A/B 汇总，详见偏离记录。')
rerun=f['decisions']['rerun']
if rerun is not None:
    raw=json.dumps(rerun,ensure_ascii=False,indent=2)
    if '```json\n'+raw+'\n```' not in report:
        report=report.replace(raw,'```json\n'+raw+'\n```',1)
lines=['','## 补充审计与复现信息','',f'本机 MATLAB R2023a，Intel Core i5-1235U，6 个 process workers，10 条记录/分块。Python 只承担规则汇总、成簇重采样和绘图；实验模型及求解在 MATLAB 执行。Nature skills 更新至提交 `{f["provenance"]["nature_skills_commit"]}`，绘图技能 2.8.0。','',f'D1 源码清单 SHA-256：`{history["D1_manifest_sha256"]}`；D2/冻结清单 SHA-256：`{history["D2_manifest_sha256"]}`。D2 启动前的两项输出修正见 ../DEVIATIONS.md：固定半径驻留诊断参照实际边界、显式图件导出。它们不改变选择规则输入；原版本和原清单均留档。','',f'计时定义：{f["provenance"]["runtime_definition"]}。ADA 中继承的 B2 标签在第 0 轮表示原 SMR，在扩张轮表示上一轮候选。迭代/函数调用预算命中率、退出标志和 hard_fail 全部保留在逐记录表中。','', 'bootstrap 使用 NumPy PCG64，seed=20261051。场景内分别抽 60 个种子簇，携带全部 7 个 SNR；两场景等权合并；相同抽样数组跨变体和指标复用，保留配对。95% percentile 区间不进入方法冻结判定。3 dB 宽度在无法定义时保留 NaN，汇总均值仅含可定义记录；这项描述性指标不参与选择。','', '### 固定半径足够规则的完整区间','', '| 半径 | 场景 | G固定 [95% CI] | G ADA [95% CI] | H固定 [95% CI] | H ADA [95% CI] | 通过 |','|---|---|---|---|---|---|---|']
s=pd.read_csv(OUT/'D2_summary.csv')
def cell(r,m):return f'{r[m]:.9g} [{r[m+"_lo"]:.9g}, {r[m+"_hi"]:.9g}]'
tests=f['decisions']['fixed_radius_tests']; selection=f['decisions']['ADA_selection']
for test in tests:
    q=s[(s.scene==test['scene'])&(s.method==test['method'])].iloc[0]
    a=s[(s.scene==test['scene'])&(s.method==selection['selected_ADA'])].iloc[0]
    lines.append(f'| {test["method"]} | {test["scene"]} | {cell(q,"gain_eta_vs_F02")} | {cell(a,"gain_eta_vs_F02")} | {cell(q,"harm_vs_F02")} | {cell(a,"harm_vs_F02")} | {test["passes"]} |')
if not tests:lines+=['','A3 提前停止自适应开发，该规则不适用。']
lines+=['','### 交付内容','', '- DEV_REPORT.md 与 FROZEN_METHOD.json：开发选择及冻结配方。','- D1/D2 records、summary、cell_stats 和 selection_rules：完整数字与区间。','- 三组 PDF/SVG/PNG、FIGURE_CAPTIONS.md：开发图件及图注。','- qa/development_audit.json、qa/saved_outputs_audit.json、图件审计：完成后的只读检查。','- ../G_gates/GATES_REPORT.md：八个核验门。','', '状态保持停止点 1；确认阶段 C 未启动，等待用户核对规则后另行放行。']
lines+=['','图件排版修正：峰值图顶部留白由 qa/repair_figure_layout.py 调整，解决面板 b 与图例的文字边界盒碰撞；数值源码与源码清单未变。最终三张图均需通过 1.5 pt 面板对齐、5 pt 最小字号、渲染碰撞和目视检查，详见 qa 图件审计。修复前诊断叠加图明确标记为 before_repair，仅作为 QA 留档。']
lines+=['','等价复用按主方案 §2.7：global 先计算 τ=10、cap=0.08 的链，各 τ/cap 按前一轮驻留值取合法前缀；local 的每个 τ 独立计算 cap=0.08 链，cap=0.04 取第一轮前缀。不同 τ 的 local 链不互换。每个变体保留其实际前缀的解、界限、每轮 J 和累计求解时间；从不按 η 或峰值挑选重复结果。']
lines+=['','数字显示：Markdown 表格为便于阅读采用 9 位有效数字；逐条阈值核对应以 JSON/CSV 的完整双精度数字为准。UNB 的系数盒界为 ±Inf，CSV 的 final_bounds JSON 用 null 表示这一无限界；其固定半径边界驻留诊断不适用，保留 NaN。F01 原 SMR 起点不可行时 J_start 为 −Inf；选中终点 J 始终有限。以上描述性标记不进入任何冻结规则。']
lines+=['','D1 UNB 的 initial_dwell_s 是相对固定 0.02 参照包络 m=1 的连续超出诊断，不能解释为其自身无限盒界的驻留；D2 固定 UNB 的自身驻留输出 NaN。ADA 的实际触发来自 F02/各轮当前 m，与 D1 UNB 的该描述列无关；原数值不改。']
if rerun is not None:
    lines+=['','### A5 与 A/B 的逐项核对','',f'触发记录 {rerun["triggered_records"]}；A5 的比较门为 ≥30 条。']
    if 'mean_abs_eta_difference' in rerun:
        lines+=['','| 条件 | 实际值 | 严格阈值 | 通过 |','|---|---:|---|---|']
        for label,key,limit in [('平均绝对 η 差','mean_abs_eta_difference',.005),('平均绝对峰值差（dB）','mean_abs_peak_difference_db',.1),('B/A 时间比中位数','median_runtime_B_over_A',.6)]:
            value=rerun[key];lines.append(f'| {label} | {value:.9g} | < {limit} | {value<limit} |')
        lines+=['',f'三条件必须同时成立才选 B；实际冻结重跑方式为 {rerun["selected"]}。比较只含触发记录，差值先逐记录取绝对值再求平均。']
    else:lines+=['','不足 30 条，按 A5 直接取 A，不比较 B。']
lines+=['','### 已解决的 CSV 表示中断','', 'A/B 各 840 条数值求解已完成后，原汇总因整数 0/1 触发标记被 pandas 误作列索引而中断，未生成比较输入。先记录偏离并逐条证明：0/1 与布尔解释选择同样的 323 条记录，A/B 标记完全一致；原 CSV SHA 不变。独立读入适配脚本只转换标记类型，调用原判定函数，得到上表；没有改变记录、η、峰值、时间或公式。随后新驱动只首次运行 grid、冻结及绘图；D1/fixed/rerunA/rerunB 均未重跑。相关脚本 SHA 见冻结 JSON provenance，原失败日志以 EXECUTION_ERROR_resolved_CSV_type.txt 留档。','', '复核中将此归为不影响规则输入的表示适配；任何实际影响输入的异常仍按方案停止并交用户决定。']
(OUT/'DEV_REPORT.md').write_text(report+'\n'.join(lines)+'\n',encoding='utf8')
print(json.dumps({'frozen_method_sha256':sha,'method':f['method'],'branch':f['branch']}))
