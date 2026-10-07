from pathlib import Path
from collections import Counter, defaultdict
import csv
import hashlib
import json
import math
import statistics
import zipfile
import xml.etree.ElementTree as ET
import numpy as np

ROOT = Path(r'D:/论文集')
REV = ROOT / '当前主线精选_20261003/11_正文稿/修订稿_20261005'
OUT = Path(__file__).resolve().parent
ATTR = REV / '补充分析_实测峰归属'
read = lambda p: list(csv.DictReader(p.open(encoding='utf-8-sig')))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
tracked = [REV/'论文修订稿_中文_20261005.docx',
           REV/'回复审稿/修订稿Word正文段落.txt',
           REV/'回复审稿/修改说明与逐条回复_20261005.md',
           ATTR/'归属检查规则.md', ATTR/'peak_attribution.py',
           ATTR/'实测峰归属_15例.csv', ATTR/'积累时长窗口归属.csv',
           ROOT/'phaseD/X2_frontend/X2_records.csv',
           ROOT/'phaseD/C_confirm/C_records.csv',
           ROOT/'当前主线精选_20261003/11_正文稿/论文初稿_中文_20261005_排版修订.docx']
tracked += [ROOT/f'审稿评估_20261005/Reviewer{i}_独立审阅.md' for i in (1,2,3)]
before = {str(p): sha(p) for p in tracked}
checks = []
def add(aid, status, location, check, result):
    checks.append(dict(audit_id=aid, status=status, location=location,
                       check=check, result=result))

ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
      'm':'http://schemas.openxmlformats.org/officeDocument/2006/math'}
with zipfile.ZipFile(tracked[0]) as z:
    tree = ET.fromstring(z.read('word/document.xml'))
lines = []
for i,p in enumerate(tree.findall('.//w:body/w:p',ns),1):
    val = ''.join(t.text or '' for t in p.iter()
                  if t.tag in [f"{{{ns['w']}}}t",f"{{{ns['m']}}}t"])
    if val.strip(): lines.append(f'[P{i:04d}] {val}')
expected = '\n\n'.join(lines)
assert expected == tracked[1].read_text(encoding='utf-8')
add('REV-AUD-01','passed','全文 P 编号','重新只读提取 DOCX 主体段落，与提交文本逐字比较',
    {'nonempty_paragraphs':len(lines),'paragraph_text_matches_docx':True,
     'tables':len(tree.findall('.//w:body/w:tbl',ns)),
     'paragraph_numbering_excludes_table_cells':True})

a = read(ATTR/'实测峰归属_15例.csv')
assert len(a)==15
summary={}
for method,gain in [('VS_FM','gain_max_peak_db'),('MFT_FM','gain_mft_max_peak_db'),
                    ('SUV_FM','gain_suv_max_peak_db')]:
    sub=[r for r in a if r[method+'_class']=='对应']
    summary[method]={'classes':dict(Counter(r[method+'_class'] for r in a)),
                     'accepted_gain_min':min(float(r[gain]) for r in sub),
                     'accepted_gain_max':max(float(r[gain]) for r in sub),
                     'accepted_gain_median':statistics.median(float(r[gain]) for r in sub)}
weak=[float(r['gain_max_peak_db']) for r in a]
sub100=[r for r in a if int(r['tone_hz'])==100]
add('REV-AUD-02','passed','P0003、P0186、P0192、P0197、表6',
    '由逐例 CSV 复算完整分母、归属数和增量',
    {'n':len(a),'all_positive':all(v>0 for v in weak),
     'all_median_db':statistics.median(weak),'summary':summary,
     'both_LPS_and_corrected_accepted':sum(r['SMR_class']==r['VS_FM_class']=='对应' for r in a),
     'tone100_n':len(sub100),'tone100_min_db':min(float(r['gain_max_peak_db']) for r in sub100),
     'tone100_max_db':max(float(r['gain_max_peak_db']) for r in sub100),
     'tone100_median_db':statistics.median(float(r['gain_max_peak_db']) for r in sub100)})

diff_excess=max(abs(float(r['screen_excess_db'])-float(r['screen_excess_repro_db'])) for r in a)
diff_cont=max(abs(float(r['screen_cont'])-float(r['screen_cont_repro'])) for r in a)
diff_gain=max(abs(float(r['gain_max_peak_db'])-float(r['gain_case_table_db'])) for r in a)
assert diff_excess<1e-10 and diff_cont<1e-10 and diff_gain<1e-10
add('REV-AUD-03','passed','P0296、作者归属检查自检',
    '核对保存的原值与重算值；本次没有从基带重算连续 LOFAR',
    {'max_excess_difference_db':diff_excess,'max_continuity_difference':diff_cont,
     'max_gain_difference_db':diff_gain,
     'ridge_fit_rms_median_hz':statistics.median(float(r['ridge_fit_rms_hz']) for r in a)})

sens=[]
for threshold in [.025,.03,.04,.05,.06,.075,.10]:
    sub=[r for r in a if float(r['VS_FM_median_dev_hz'])<=threshold]
    sens.append({'threshold_hz':threshold,'n':len(sub),
                 'gain_median_db':statistics.median(float(r['gain_max_peak_db']) for r in sub),
                 'tone100_n':sum(int(r['tone_hz'])==100 for r in sub)})
geometry=[]
for r in a:
    tone,start=int(r['tone_hz']),int(r['start_s'])
    p=REV/f'_build/figs/source_data/tf_f{tone}_s{start}.npz'
    with np.load(p) as d:
        e=np.abs(d['map_ada']-d['fsc'])
        assert abs(float(np.median(e))-float(r['VS_FM_median_dev_hz']))<1e-10
        geometry.append({'tone_hz':tone,'start_s':start,'median_dev_hz':float(np.median(e)),
                         'q90_dev_hz':float(np.quantile(e,.9)),
                         'fraction_within_0p05':float(np.mean(e<=.05)),
                         'fraction_within_0p10':float(np.mean(e<=.10))})
add('REV-AUD-04','aggregation_ambiguity','P0189、P0192、P0232、P0296',
    '探索性阈值敏感性与逐帧映射一致性；没有改变原归属标签',
    {'threshold_sensitivity':sens,'frame_geometry':geometry,
     'limits':'只检验几何一致性，不证明物理声源身份；原判据在分析前写定的时点未独立认证'})
window=[]
for r in a:
    if r['VS_FM_class']=='对应':
        window.append({'tone_hz':int(r['tone_hz']),'start_s':int(r['start_s']),
                       'window_0p10_gain_db':float(r['gain_ridge_peak_db']),
                       'window_0p05_gain_db':float(r['gain_ridge_peak_w05_db'])})
add('REV-AUD-05','aggregation_ambiguity','P0198、P0230、作者回复第四节',
    '复核已有两种脊线中心比较窗口；窗口缩窄会排除原最大峰，不等于证明目标退化',
    {'accepted_cases_window_comparison':window,
     'key_case':'61 Hz 2100 s：2.5784 dB 转为 -0.7134 dB；应披露定位与窗口敏感性'})

common=[r for r in a if r['SMR_class']==r['VS_FM_class']==r['SUV_class']==r['SUV_FM_class']=='对应']
common100=[r for r in common if int(r['tone_hz'])==100]
add('REV-AUD-12','aggregation_ambiguity','P0197、P0224',
    '不同前端按各自修正后归属筛选的子集不相同；追加增量也不等于最终链路性能',
    {'both_chains_same_ridge_n':len(common),
     'VIT_LPS_common_median_db':statistics.median(float(r['gain_max_peak_db']) for r in common),
     'SUV_common_median_db':statistics.median(float(r['gain_suv_max_peak_db']) for r in common),
     'same100_n':len(common100),
     'VIT_LPS_same100_median_db':statistics.median(float(r['gain_max_peak_db']) for r in common100),
     'SUV_same100_median_db':statistics.median(float(r['gain_suv_max_peak_db']) for r in common100),
     'interpretation':'可用同一 100 Hz 五个时段做配对描述，不能用不同事后子集宣布普遍排序'})

x=read(ROOT/'phaseD/X2_frontend/X2_records.csv')
groups=defaultdict(list)
for r in x: groups[r['frontend']].append(r)
frontend={}
for fe,rs in groups.items():
    assert len(rs)==1400
    assert max(abs(float(r['eta_out'])-float(r['eta_in'])-float(r['gain_eta'])) for r in rs)<1e-10
    frontend[fe]={'n':len(rs),'eta_in':statistics.mean(float(r['eta_in']) for r in rs),
                  'eta_out':statistics.mean(float(r['eta_out']) for r in rs),
                  'gain':statistics.mean(float(r['gain_eta']) for r in rs),
                  'loss_gt_0p01_n':sum(float(r['gain_eta'])<-.01 for r in rs),
                  'loss_gt_0p01_fraction':sum(float(r['gain_eta'])<-.01 for r in rs)/len(rs),
                  'negative_gain_n':sum(float(r['gain_eta'])<0 for r in rs),
                  'negative_gain_fraction':sum(float(r['gain_eta'])<0 for r in rs)/len(rs),
                  'correction_runtime_median_s':statistics.median(float(r['runtime_s']) for r in rs),
                  'scene_seed_clusters':len(set((r['scene'],r['seed']) for r in rs))}
add('REV-AUD-06','passed','表4、P0159、P0226','复算跨前端绝对效率、增量和逐条退化',frontend)

c=read(ROOT/'phaseD/C_confirm/C_records.csv')
c=[r for r in c if r['method']=='ADA_local_c04_t30_A' and r['arm']=='scaled']
assert len(c)==2800
cs={}
for scene in ['ALL','S0','S2']:
    rs=c if scene=='ALL' else [r for r in c if r['scene']==scene]
    cs[scene]={'n':len(rs),'positive_fraction':sum(float(r['gain_eta_vs_SMR'])>0 for r in rs)/len(rs),
               'loss_gt_0p01_n':sum(float(r['gain_eta_vs_SMR'])<-.01 for r in rs),
               'loss_gt_0p01_fraction':sum(float(r['gain_eta_vs_SMR'])<-.01 for r in rs)/len(rs),
               'scene_seed_clusters':len(set((r['scene'],r['seed']) for r in rs))}
add('REV-AUD-07','passed','P0129、P0133','复算确认组逐条收益比例与种子簇数',cs)

du=read(ATTR/'积累时长窗口归属.csv')
assert len(du)==16
amb=[r for r in du if r['VS_FM_class']=='不确定']
assert len(amb)==1 and amb[0]['tone_hz']=='103' and amb[0]['duration_s']=='450'
add('REV-AUD-08','confirmed_internal_error','图13(d)、P0210、P0214',
    '核对 CSV、绘图逻辑及实际图例',
    {'uncertain_case':amb[0],
     'display':'103 Hz 900 s 起、450 s 为归属不确定，却用空心标记且图例写为最大峰不在筛选脊线',
     'fix':'增加不确定标记，或把空心图例改为未通过在脊线上的判据（含不确定）'})

N,fs=200,20
w=np.hanning(N)
freq=2*fs/(N-1)
response=abs(np.dot(w,np.exp(-2j*np.pi*freq*np.arange(N)/fs)))/w.sum()
add('REV-AUD-09','confirmed_internal_error','P0297、归属检查规则的阈值依据',
    '由实际 200 点对称 Hann 窗计算第一零点，明确全宽与半宽',
    {'first_null_hz':freq,'response_at_first_null':float(response),
     'null_to_null_width_hz':2*freq,
     'issue':'10 s Hann 主瓣零点间全宽约 0.40 Hz，0.20 Hz 是单侧半宽；0.05 Hz 不是全宽的四分之一'})

add('REV-AUD-10','unresolved_input_needed','P0076、P0219',
    '区分输入误差与输出改变量',
    {'issue':'完整方法与 LPS 的平均差不等于锚轨迹相对目标的常值偏差；尚未给出锚轨迹真值偏差分布',
     'fix':'删除把常值偏差明显小于幅度界作为已检验事实的表述，或补已有仿真轨迹与真值的偏差分布'})
add('REV-AUD-11','not_assessable','端到端复现、物理目标身份、开发时点',
    '本次为源码与保存结果的只读复核，不重跑估计器或真实背景注入',
    {'not_established':['全部链路端到端运行一致性','目标分量真值','参数规则运行前锁定的独立时间证据',
                        '稿件 P0241 的对外代码获取路径']})

assert all(sha(Path(p))==h for p,h in before.items())
result={'review_date':'2026-10-06','input_version':'修订稿_20261005',
        'status_counts':dict(Counter(r['status'] for r in checks)),
        'checks':checks,'protected_input_sha256':before,'protected_inputs_unchanged':True}
(OUT/'修订稿数值与证据核查.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'status_counts':result['status_counts'],'frontend':frontend,
                  'confirmation':cs,'protected_inputs_unchanged':True},ensure_ascii=False,indent=2))
